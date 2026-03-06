# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

state = MachineState()

@app.get("/")
def root():
    return {"status": "ok", "message": "Demo Machine API"}

@app.get("/state")
def get_state():
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