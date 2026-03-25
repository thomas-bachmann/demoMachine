import os
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool

server = Server("mcp-machine")
sse = SseServerTransport("/messages")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


async def _api_get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"{BACKEND_URL}{path}")
        r.raise_for_status()
        return r.json()


async def _api_post(path: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(f"{BACKEND_URL}{path}")
        r.raise_for_status()
        return r.json()
    
async def _api_post_json(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(f"{BACKEND_URL}{path}", json=payload)
        r.raise_for_status()
        return r.json()


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_status",
            description="Returns basic API information (health check)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_state",
            description="Returns the current machine state (is_on, has_warning, has_error)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="toggle_power",
            description="Turns the machine on or off. If the machine turns off, warning and error are reset.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="toggle_warning",
            description="Toggles the warning state. Only works if the machine is on.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="toggle_error",
            description="Toggles the error state. Only works if the machine is on.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="set_speed_target",
            description="Sets motor target speed between 0 and 100.",
            inputSchema={
                "type": "object",
                "properties": {"target_speed": {"type": "number", "minimum": 0, "maximum": 100}},
                "required": ["target_speed"],
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "get_status":
            result = await _api_get("/")
            return [TextContent(type="text", text=str(result))]

        elif name == "get_state":
            result = await _api_get("/state")
            return [TextContent(type="text", text=str(result))]

        elif name == "toggle_power":
            result = await _api_post("/toggle")
            return [TextContent(type="text", text=f"Machine toggled. State: {result}")]

        elif name == "toggle_warning":
            result = await _api_post("/warning")
            return [TextContent(type="text", text=f"Warning toggled. State: {result}")]

        elif name == "toggle_error":
            result = await _api_post("/error")
            return [TextContent(type="text", text=f"Error toggled. State: {result}")]
        
        elif name == "set_speed_target":
            target_speed = float(arguments.get("target_speed"))
            result = await _api_post_json("/speed-target", {"target_speed": target_speed})
            return [TextContent(type="text", text=f"Target speed set to {target_speed}. State: {result}")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"API error: {e.response.status_code}")]
    except httpx.RequestError as e:
        return [TextContent(type="text", text=f"Connection error: {str(e)}")]


async def app(scope, receive, send):
    path = scope.get("path", "")
    method = scope.get("method", "GET")
    
    if scope["type"] == "http":
        if path == "/sse" and method == "GET":
            async with sse.connect_sse(scope, receive, send) as streams:
                await server.run(streams[0], streams[1], server.create_initialization_options())
        elif path.startswith("/messages") and method == "POST":
            await sse.handle_post_message(scope, receive, send)
        else:
            # 404
            await send({
                "type": "http.response.start",
                "status": 404,
                "headers": [[b"content-type", b"text/plain"]],
            })
            await send({
                "type": "http.response.body",
                "body": b"Not Found",
            })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)