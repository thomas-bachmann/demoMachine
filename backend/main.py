# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import math, time

app = FastAPI(title="Demo Machine API")

# CORS (utile pour le dev local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# État de la machine
class MachineState(BaseModel):
    is_on: bool = False
    has_warning: bool = False
    has_error: bool = False
    current_speed: float = 0.0
    target_speed: float = 0.0
    tau_s: float = 1.5

class SpeedTargetIn(BaseModel):
    target_speed: float = Field(ge=0, le=100)

last_update = time.monotonic()

state = MachineState()

def update_speed():
    global last_update
    now = time.monotonic()
    dt = now - last_update
    last_update = now
    desired = state.target_speed if state.is_on else 0.0
    alpha = 1.0 - math.exp(-dt / max(state.tau_s, 1e-3))
    state.current_speed += alpha * (desired - state.current_speed)

@app.get("/")
def root():
    return {"status": "ok", "message": "Demo Machine API"}

@app.get("/state")
def get_state():
    update_speed()
    return state

@app.post("/toggle")
def toggle_power():
    state.is_on = not state.is_on
    if not state.is_on:
        state.has_warning = False
        state.has_error = False
    return state

@app.post("/warning")
def toggle_warning():
    if state.is_on:
        state.has_warning = not state.has_warning
    return state

@app.post("/error")
def toggle_error():
    if state.is_on:
        state.has_error = not state.has_error
    return state

@app.post("/speed-target")
def set_speed_target(payload: SpeedTargetIn):
    update_speed()
    state.target_speed = payload.target_speed
    return state