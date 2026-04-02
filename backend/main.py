# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, AliasChoices, computed_field
from typing import List
import math, time
import os
import httpx


WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI(title="Demo Machine API")

def update_webhook():
    """Envoie l'état courant au webhook n8n si l'URL est définie."""
    if WEBHOOK_URL:
        try:
            httpx.post(WEBHOOK_URL, json=state.model_dump())
        except Exception as e:
            print(f"Erreur lors de l'appel du webhook n8n: {e}")
    return state

# CORS (utile pour le dev local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MotorSlide(BaseModel):
    id: int = 0
    current_speed: float = 0.0
    target_speed: float = 0.0
    tau_s: float = 1.5

    def updateSpeed(self, is_on: bool, dt: float):
        desired = self.target_speed if is_on else 0.0
        alpha = 1.0 - math.exp(-dt / max(self.tau_s, 1e-3))
        self.current_speed += alpha * (desired - self.current_speed)

# État de la machine
class MachineState(BaseModel):
    is_on: bool = False
    has_warning: bool = False
    has_error: bool = False
    motors: List[MotorSlide] = Field(
        default_factory=lambda: [
            MotorSlide(id=1, tau_s=1.5),
            MotorSlide(id=2, tau_s=3.0)
        ]
    )
    last_update: float = Field(default_factory=time.monotonic)

    @computed_field
    @property
    def motor_1(self) -> MotorSlide:
        return self.motors[0]

    @computed_field
    @property
    def motor_2(self) -> MotorSlide:
        return self.motors[1]

    def reset(self):
        for motor in self.motors:
            motor.target_speed = 0
        self.has_warning = False
        self.has_error = False

    def updateSpeed(self):
        now = time.monotonic()
        dt = now - self.last_update
        self.last_update = now
        for motor in self.motors:
            motor.updateSpeed(self.is_on, dt)

class SpeedTargetIn(BaseModel):
    target_speed: float = Field(ge=0, le=100)
    motor_id: int = Field(ge=1, le=2)

state = MachineState()

@app.get("/")
def root():
    return {"status": "ok", "message": "Demo Machine API"}

@app.get("/state")
def get_state():
    state.updateSpeed()
    return update_webhook().model_dump()

@app.post("/toggle")
def toggle_power():
    state.is_on = not state.is_on
    if not state.is_on:
        state.reset()
    return update_webhook()

@app.post("/warning")
def toggle_warning():
    if state.is_on:
        state.has_warning = not state.has_warning
    return update_webhook()

@app.post("/error")
def toggle_error():
    if state.is_on:
        state.has_error = not state.has_error
    return update_webhook()

@app.post("/speed-target")
def set_speed_target(payload: SpeedTargetIn):
    state.updateSpeed()
    for motor in state.motors:
        if motor.id == payload.motor_id:
            motor.target_speed = payload.target_speed
            break
    return update_webhook()