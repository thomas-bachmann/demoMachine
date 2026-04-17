"""
API Bus - Interface REST pour communiquer avec le PLC
Expose les actions possibles au monde extérieur (Frontend, n8n, etc.)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx

from plc import MachineController
from models import (
    SetMotorSpeedPayload,
    EmergencyStopButtonPayload,
    EmergencyStopAcknowledgePayload,
    ErrorAcknowledgePayload,
)

# Configuration
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Initialisation
app = FastAPI(title="Demo Machine API")
plc = MachineController()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== UTILITAIRES ==========

def notify_webhook():
    """Envoie l'état courant au webhook n8n si l'URL est définie."""
    if WEBHOOK_URL:
        try:
            state = plc.get_state()
            httpx.post(WEBHOOK_URL, json=state.model_dump())
        except Exception as e:
            print(f"Erreur lors de l'appel du webhook n8n: {e}")


# ========== ENDPOINTS INFO ==========

@app.get("/")
def root():
    """Endpoint de base"""
    return {"status": "ok", "message": "Demo Machine API"}


@app.get("/state")
def get_state():
    """Retourne l'état courant de la machine"""
    return plc.get_state()


# ========== ENDPOINTS PUISSANCE ==========

@app.post("/toggle")
def toggle_power():
    """Toggle la puissance ON/OFF"""
    plc.toggle_power()
    state = plc.get_state()
    notify_webhook()
    return state


@app.post("/power-on")
def power_on():
    """Demande l'allumage de la machine"""
    plc.request_power_on()
    state = plc.get_state()
    notify_webhook()
    return state


@app.post("/power-off")
def power_off():
    """Demande l'extinction de la machine"""
    plc.request_power_off()
    state = plc.get_state()
    notify_webhook()
    return state


# ========== ENDPOINTS MOTEURS ==========

@app.post("/speed-target")
def set_speed_target(payload: SetMotorSpeedPayload):
    """Défini la vitesse cible d'un moteur"""
    plc.set_motor_speed(payload.motor_id, payload.target_speed)
    state = plc.get_state()
    notify_webhook()
    return state


# ========== ENDPOINTS DIAGNOSTIC ==========

@app.post("/warning")
def toggle_warning():
    """Toggle l'alerte (simulation)"""
    # Récupérer l'état actuel
    current_state = plc.state
    # Toggle
    plc.set_warning(not current_state.has_warning)
    state = plc.get_state()
    notify_webhook()
    return state


@app.post("/error")
def toggle_error():
    """Toggle la condition d'erreur (simulation)"""
    # Récupérer l'état actuel
    current_state = plc.state
    # Toggle la condition d'erreur
    plc.set_error_condition(not current_state.error_condition)
    state = plc.get_state()
    notify_webhook()
    return state


@app.post("/error-acknowledge")
def error_acknowledge(payload: ErrorAcknowledgePayload):
    """
    Gère le bouton de quittance (acknowledge) de l'erreur.
    
    acknowledged = true : quittance activée → désactive l'erreur
    acknowledged = false: quittance désactivée
    """
    plc.set_error_acknowledge(payload.acknowledged)
    state = plc.get_state()
    notify_webhook()
    return state


# ========== ENDPOINTS ARRÊT D'URGENCE ==========

@app.post("/emergency-stop")
def emergency_stop_button(payload: EmergencyStopButtonPayload):
    """
    Gère le bouton d'arrêt d'urgence à crantage.
    
    button_pressed = true : le bouton est enfoncé → active l'e-stop
    button_pressed = false: le bouton est relâché → permet la quittance
    
    WORKFLOW:
    1. Appuyer sur E-stop (button_pressed=true) → machine s'arrête
    2. Relâcher le bouton (button_pressed=false) → e-stop reste actif
    3. Appuyer sur Acknowledge → e-stop se désactive
    """
    plc.set_emergency_stop_button(payload.button_pressed)
    state = plc.get_state()
    notify_webhook()
    return state


@app.post("/emergency-stop-acknowledge")
def emergency_stop_acknowledge(payload: EmergencyStopAcknowledgePayload):
    """
    Gère le bouton de quittance (acknowledge) de l'arrêt d'urgence.
    
    acknowledged = true : quittance activée → désactive l'e-stop (si bouton relâché)
    acknowledged = false: quittance désactivée
    
    IMPORTANT: La quittance ne fonctionne que si le bouton est relâché!
    """
    plc.set_emergency_stop_acknowledge(payload.acknowledged)
    state = plc.get_state()
    notify_webhook()
    return state