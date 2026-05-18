import os
import json
import uuid
from litellm import completion
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# In-memory conversation store: session_id -> messages
_conversation_store: dict[str, list] = {}
MAX_STORED_MESSAGES = 40


def _save_session(session_id: str, messages: list) -> None:
    _conversation_store[session_id] = messages[-MAX_STORED_MESSAGES:]


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

    if not mcp_server_url:
        response = completion(model=model, messages=messages, api_base=api_base_url)
        assistant_message = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_message})
        _save_session(session_id, messages)
        return {"response": assistant_message, "session_id": session_id}

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
                    _save_session(session_id, messages)
                    return {"response": response_content, "session_id": session_id}

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