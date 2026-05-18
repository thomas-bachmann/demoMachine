import os
import json
import re
import uuid
from litellm import completion
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

_conversation_store: dict[str, list] = {}
MAX_STORED_MESSAGES = 40

SYSTEM_PROMPT = """Tu es un assistant IA pour une machine industrielle de démonstration. Tu peux consulter l'état de la machine et déclencher des actions via les outils disponibles.

Lorsqu'une demande utilisateur est ambiguë et que tu ne peux pas agir sans précision (exemple: le numéro de moteur n'est pas spécifié, la valeur cible est manquante), réponds UNIQUEMENT avec le bloc suivant, sans aucun autre texte :
<clarification>
{
  "question": "Question courte et claire pour l'utilisateur",
  "options": [
    {"id": "opt1", "label": "Libellé option 1"},
    {"id": "opt2", "label": "Libellé option 2"},
    {"id": "other", "label": "Autre (préciser)"}
  ]
}
</clarification>

N'utilise ce format QUE si la demande est vraiment ambiguë. Si la demande est suffisamment précise, utilise directement les outils disponibles sans demander de confirmation."""


def _save_session(session_id: str, messages: list) -> None:
    _conversation_store[session_id] = messages[-MAX_STORED_MESSAGES:]


def _parse_clarification(response: str) -> tuple[str, dict | None]:
    """Extract <clarification> JSON block from response if present."""
    match = re.search(r'<clarification>\s*(.*?)\s*</clarification>', response, re.DOTALL)
    if not match:
        return response, None
    try:
        clarification = json.loads(match.group(1))
        clean = (response[:match.start()] + response[match.end():]).strip()
        return clean, clarification
    except (json.JSONDecodeError, KeyError):
        return response, None


async def generate_llm_response(
    prompt: str,
    session_id: str | None = None,
    model: str | None = None,
    api_base_url: str | None = None,
    mcp_server_url: str | None = None,
) -> dict:
    if model is None:
        model = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")

    if session_id is None:
        session_id = str(uuid.uuid4())

    history = _conversation_store.get(session_id, [])
    messages = history + [{"role": "user", "content": prompt}]
    system = [{"role": "system", "content": SYSTEM_PROMPT}]

    if not mcp_server_url:
        response = completion(model=model, messages=system + messages, api_base=api_base_url)
        raw = response.choices[0].message.content
        clean_response, clarification = _parse_clarification(raw)
        history_content = clarification.get('question', clean_response) if clarification else clean_response
        messages.append({"role": "assistant", "content": history_content})
        _save_session(session_id, messages)
        return {"response": clean_response, "session_id": session_id, "clarification": clarification}

    async with streamablehttp_client(mcp_server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            mcp_tools = await session.list_tools()
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                }
                for t in mcp_tools.tools
            ]

            while True:
                response = completion(model=model, messages=system + messages, tools=tools, api_base=api_base_url)
                choice = response.choices[0]

                if choice.finish_reason == "stop":
                    raw = choice.message.content
                    clean_response, clarification = _parse_clarification(raw)
                    history_content = clarification.get('question', clean_response) if clarification else clean_response
                    messages.append({"role": "assistant", "content": history_content})
                    _save_session(session_id, messages)
                    return {"response": clean_response, "session_id": session_id, "clarification": clarification}

                if choice.finish_reason == "tool_calls":
                    messages.append(choice.message)

                    for tool_call in choice.message.tool_calls:
                        result = await session.call_tool(
                            tool_call.function.name,
                            json.loads(tool_call.function.arguments)
                        )
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result.content)
                        })
