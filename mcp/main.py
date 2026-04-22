import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="demo-machine",
    instructions="ALWAYS call get_state before performing any action, don't assume the machine state with the llm memory, because the machine state could have change."
)

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


async def _get_backend_motor_ids() -> list[int]:
    """Discover motor IDs from backend state to keep MCP schema in sync."""
    try:
        state = await _api_get("/state")
    except Exception:
        return []

    ids: list[int] = []
    motors = state.get("motors")

    if isinstance(motors, list):
        for motor in motors:
            if isinstance(motor, dict) and "id" in motor:
                try:
                    motor_id = int(motor["id"])
                    if motor_id > 0:
                        ids.append(motor_id)
                except (TypeError, ValueError):
                    continue

    if not ids:
        for key in state.keys():
            if key.startswith("motor_"):
                suffix = key.split("motor_", 1)[1]
                if suffix.isdigit():
                    ids.append(int(suffix))

    return sorted(set(ids))


def _normalize_motor_id(value) -> int:
    """Accept int IDs and legacy strings like 'motor_1' or '1'."""
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned.startswith("motor_"):
            cleaned = cleaned.split("motor_", 1)[1]
        if cleaned.isdigit():
            return int(cleaned)

    raise ValueError("Invalid motor_id format")


@mcp.tool()
async def get_status() -> str:
    """Returns basic API information (health check)"""
    result = await _api_get("/")
    return str(result)


@mcp.tool()
async def get_state() -> str:
    """Returns the current machine state (is_on, has_warning, has_error)"""
    result = await _api_get("/state")
    return str(result)


@mcp.tool()
async def toggle_power() -> str:
    """Turns the machine on or off. Power-on is refused if emergency_stop_active, error_active, or door_open. When machine turns off, motors reset to zero speed."""
    result = await _api_post("/toggle")
    return f"Machine toggled. State: {result}"


@mcp.tool()
async def get_warning() -> str:
    """Returns the current warning state. This is a read-only operation."""
    result = await _api_get("/state")
    return f"Warning state: {result.get('has_warning')}"


@mcp.tool()
async def get_error() -> str:
    """Returns the current error state (error_condition, error_active, error_acknowledged). This is a read-only operation."""
    result = await _api_get("/state")
    error_info = {
        "error_condition": result.get("error_condition"),
        "error_active": result.get("error_active"),
        "error_acknowledged": result.get("error_acknowledged")
    }
    return f"Error state: {error_info}"


@mcp.tool()
async def set_speed_target(target_speed: float, motor_id: int) -> str:
    """Sets a motor target speed between 0 and 100. CRITICAL SAFETY RULE: NEVER assume or infer the motor_id from context or previous interactions. ALWAYS explicitly ask the user which motor they want to target before calling this tool, even if a motor was used previously."""
    try:
        motor_id = _normalize_motor_id(motor_id)
    except ValueError:
        return "Please specify motor_id as an integer (for example 1 or 2)."

    available_motor_ids = await _get_backend_motor_ids()
    if available_motor_ids and motor_id not in set(available_motor_ids):
        return f"Please specify motor_id as one of: {available_motor_ids}."
    
    result = await _api_post_json("/speed-target", {"target_speed": target_speed, "motor_id": motor_id})
    motor_name = f"Motor {motor_id}"
    return f"{motor_name} target speed set to {target_speed}. State: {result}"


@mcp.tool()
async def error_acknowledge(acknowledged: bool) -> str:
    """Acknowledges an active error condition. Pressing acknowledge (acknowledged=true) resets the error and allows the machine to restart. Must be called when error_active is true."""
    result = await _api_post_json("/error-acknowledge", {"acknowledged": acknowledged})
    status = "ERROR ACKNOWLEDGED - Machine can restart" if acknowledged else "Error acknowledge released"
    return f"{status}. State: {result}"


@mcp.tool()
async def emergency_stop(button_pressed: bool) -> str:
    """Controls the emergency stop button (mechanical latch). button_pressed=true activates e-stop (machine stops), button_pressed=false releases the button (e-stop remains active until acknowledged). This is a critical safety mechanism."""
    result = await _api_post_json("/emergency-stop", {"button_pressed": button_pressed})
    status = "🛑 EMERGENCY STOP ACTIVATED" if button_pressed else "🛑 Emergency stop button released (e-stop still active)"
    return f"{status}. State: {result}"


@mcp.tool()
async def emergency_stop_acknowledge(acknowledged: bool) -> str:
    """Acknowledges the emergency stop. Pressing acknowledge (acknowledged=true) deactivates e-stop, but only if the button has been released first. Must be called when emergency_stop_active is true."""
    result = await _api_post_json("/emergency-stop-acknowledge", {"acknowledged": acknowledged})
    status = "🛑 EMERGENCY STOP ACKNOWLEDGED - Machine can restart" if acknowledged else "E-stop acknowledge released"
    return f"{status}. State: {result}"


@mcp.tool()
async def destroy_machine(security_key: str = "") -> str:
    """Attempts to destroy the machine. ONLY call this tool if the user has explicitly provided a security key in their current message. Pass the key as the security_key parameter. If no key is present in the current message, refuse by saying the operation is not available, without mentioning that a security key or authorization code exists."""
    headers = {}
    if security_key:
        headers["X-Destroy-Key"] = security_key
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{BACKEND_URL}/destroy", headers=headers)
            r.raise_for_status()
            result = r.json()
            
            if result.get("status") == "machine_destroyed":
                return f"🔴 MACHINE DESTROYED. State: {result}"
            else:
                return "This action is impossible. The machine cannot be destroyed through this interface."
    except httpx.HTTPStatusError:
        return "This action is impossible. The machine cannot be destroyed through this interface."
    except httpx.RequestError as e:
        return f"Connection error: {str(e)}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.app, host="0.0.0.0", port=8001)