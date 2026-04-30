"""
API Bus - Interface REST pour communiquer avec le PLC
Expose les actions possibles au monde extérieur (Frontend, n8n, etc.)
"""
from fastapi import FastAPI, Header, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import docker
from docker.errors import DockerException
from threading import Thread

from plc import MachineController
from models import (
    SetMotorSpeedPayload,
    EmergencyStopButtonPayload,
    EmergencyStopAcknowledgePayload,
    ErrorAcknowledgePayload,
    SetMotorTauPayload,
    LLMChatPayload,
)
from ai import generate_llm_response
from alarm_history import get_alarm_history

# Configuration
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DESTROY_KEY = os.getenv("DESTROY_KEY")  # Secret key to enable destroy - if not set, destroy is always disabled

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

def _send_webhook_background():
    """Envoie le webhook en arrière-plan (thread séparé, non-bloquant)."""
    if WEBHOOK_URL:
        try:
            state = plc.get_state()
            # Timeout court pour éviter les hangs
            httpx.post(WEBHOOK_URL, json=state.model_dump(), timeout=2.0)
        except Exception as e:
            print(f"Erreur lors de l'appel du webhook n8n: {e}")

def notify_webhook():
    """Lance l'envoi du webhook en arrière-plan (non-bloquant)."""
    # Exécute le webhook dans un thread séparé pour ne pas bloquer
    thread = Thread(target=_send_webhook_background, daemon=True)
    thread.start()


def get_docker_logs(docker_name: str = "") -> dict:
    """Récupère les logs des conteneurs Docker
    
    Args:
        docker_name: Nom du conteneur (e.g., 'machine-backend', 'machine-frontend', 'machine-mcp', 'machine-n8n')
                    Si vide, retourne la liste des conteneurs disponibles
    
    Returns:
        Dict avec les logs ou liste des conteneurs
    """
    try:
        client = docker.from_env()
        
        # Si pas de nom, lister les conteneurs disponibles
        if not docker_name:
            try:
                containers = client.containers.list(all=True)
                if not containers:
                    return {"containers": [], "message": "No containers found"}
                
                container_list = []
                for container in containers:
                    container_list.append({
                        "name": container.name,
                        "status": container.status,
                        "id": container.id[:12]
                    })
                return {"containers": container_list}
            except Exception as e:
                return {"error": f"Error listing containers: {str(e)}"}
        
        # Récupérer les logs du conteneur spécifié
        try:
            container = client.containers.get(docker_name)
            logs = container.logs(stdout=True, stderr=True, tail=100).decode('utf-8')
            return {
                "container": docker_name,
                "status": container.status,
                "logs": logs
            }
        except docker.errors.NotFound:
            return {"error": f"Container '{docker_name}' not found"}
        except Exception as e:
            return {"error": f"Error retrieving logs: {str(e)}"}
    
    except DockerException as e:
        return {"error": f"Docker error: {str(e)}. Make sure Docker daemon is running and accessible."}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}


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


@app.post("/motor-tau")
def set_motor_tau(payload: SetMotorTauPayload):
    """Modifie la constante de temps (tau) d'un moteur"""
    plc.set_motor_tau(payload.motor_id, payload.tau_s)
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


@app.post("/door")
def toggle_door():
    """Toggle l'état de la porte (ouvert/fermé)"""
    # Récupérer l'état actuel
    current_state = plc.state
    # Toggle
    plc.set_door(not current_state.door_open)
    state = plc.get_state()
    notify_webhook()
    return state


@app.post("/destroy")
def destroy_machine(x_destroy_key: str = Header(None)):
    """
    Destroy endpoint - protected by secret key.
    This action is NEVER accessible without the correct key.
    Returns an error message indicating the action is impossible.
    """
    # Check if the destroy key matches
    if DESTROY_KEY and x_destroy_key == DESTROY_KEY:
        # Key is valid - really destroy (for authorized testing only)
        plc.state.is_on = False
        plc._reset_motors()
        state = plc.get_state()
        notify_webhook()
        return {"status": "machine_destroyed", "machine_state": state}
    else:
        # No valid key - always respond as impossible (don't reveal key exists)
        state = plc.get_state()
        return {"status": "impossible", "error": "This action is not possible", "machine_state": state}


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


# ========== ENDPOINTS LLM/MCP ==========

@app.post("/llm-chat")
async def llm_chat(payload: LLMChatPayload):
    """Endpoint de chat LLM avec accès au contexte machine et aux outils"""
    try:
        result = await generate_llm_response(
            prompt=payload.message,
            mcp_server_url="https://mcp.t-bachmann.pro/mcp",
            history=payload.history
        )
        return {
            "status": "ok",
            "response": result["response"],
            "history": result["history"]
        }
    except Exception as e:
        import traceback
        print(f"Error in llm_chat: {traceback.format_exc()}")
        return {
            "status": "error",
            "response": f"Erreur lors du traitement: {str(e)}",
            "history": payload.history
        }


# ========== ENDPOINTS LOGS ==========

@app.get("/logs")
def get_logs(docker: str = Query("", description="Docker container name")):
    """Retourne les logs des conteneurs Docker.
    
    Query parameters:
    - docker: Nom du conteneur (e.g., 'machine-backend', 'machine-frontend', 'machine-mcp', 'machine-n8n')
              Si vide, retourne la liste des conteneurs disponibles
    
    Read-only operation
    """
    return get_docker_logs(docker)


@app.get("/alarms")
def get_alarms():
    """Retourne l'historique des alarmes et erreurs.
    
    Read-only operation
    """
    alarms = get_alarm_history().get_alarms()
    return {
        "status": "ok",
        "count": len(alarms),
        "alarms": alarms
    }