import os
import json
from litellm import completion
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def generate_llm_response(
    prompt: str,
    model: str | None = None,
    mcp_server_url: str | None = None
) -> str:
    if model is None:
        model = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")
    messages = [{"role": "user", "content": prompt}]

    if not mcp_server_url:
        response = completion(model=model, messages=messages)
        return response.choices[0].message.content

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
                response = completion(model=model, messages=messages, tools=tools)
                choice = response.choices[0]

                if choice.finish_reason == "stop":
                    return choice.message.content

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