import os
import json
from litellm import completion
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def _filter_history_for_client(messages: list[dict]) -> list[dict]:
    """
    Filtre l'historique pour le client :
    - Supprime les messages de type 'tool' (contenu du RAG)
    - Garde seulement les 5 derniers messages user/assistant
    """
    # Filtrer pour ne garder que user et assistant
    filtered = [msg for msg in messages if msg.get("role") in ("user", "assistant")]
    # Garder les 5 derniers
    return filtered[-5:]


async def generate_llm_response(
    prompt: str,
    model: str | None = None,
    api_base_url: str | None = None,
    mcp_server_url: str | None = None,
    history: list[dict] | None = None
) -> dict:
    if model is None:
        model = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")
    messages = (history or []) + [{"role": "user", "content": prompt}]

    if not mcp_server_url:
        response = completion(model=model, messages=messages, api_base=api_base_url)
        assistant_message = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_message})
        filtered_history = _filter_history_for_client(messages)
        return {"response": assistant_message, "history": filtered_history}

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
                response = completion(model=model, messages=messages, tools=tools, api_base=api_base_url)
                choice = response.choices[0]

                if choice.finish_reason == "stop":
                    response_content = choice.message.content
                    messages.append({"role": "assistant", "content": response_content})
                    filtered_history = _filter_history_for_client(messages)
                    return {"response": response_content, "history": filtered_history}

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