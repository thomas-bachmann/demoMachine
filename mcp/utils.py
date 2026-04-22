import os
import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


async def api_get(path: str) -> dict:
    """Effectue une requête GET sur le backend"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"{BACKEND_URL}{path}")
        r.raise_for_status()
        return r.json()


async def api_post(path: str) -> dict:
    """Effectue une requête POST sur le backend sans payload"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(f"{BACKEND_URL}{path}")
        r.raise_for_status()
        return r.json()


async def api_post_json(path: str, payload: dict) -> dict:
    """Effectue une requête POST JSON sur le backend"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(f"{BACKEND_URL}{path}", json=payload)
        r.raise_for_status()
        return r.json()


async def get_backend_motor_ids() -> list[int]:
    """Découvre les IDs des moteurs depuis l'état du backend"""
    try:
        state = await api_get("/state")
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


def normalize_motor_id(value) -> int:
    """Accepte les IDs moteur en tant qu'int ou strings comme 'motor_1' ou '1'"""
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned.startswith("motor_"):
            cleaned = cleaned.split("motor_", 1)[1]
        if cleaned.isdigit():
            return int(cleaned)

    raise ValueError("Invalid motor_id format")