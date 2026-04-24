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

def generate_llm_response(message: str, machine_state: dict) -> str:
    """
    Génère une réponse du LLM basée sur le message et l'état machine.
    Utilise une approche par keywords pour identifier les intentions et recommander des actions.
    
    Args:
        message: Message de l'utilisateur
        machine_state: État courant de la machine
    
    Returns:
        Réponse textuelle du LLM avec guidance
    """
    msg_lower = message.lower()
    
    # === RECONNAISSANCE D'INTENTIONS ===
    
    # Moteurs - vitesse et tau
    if any(word in msg_lower for word in ["motor", "moteur", "vitesse", "speed", "tau", "accélération"]):
        motor_guidance = "Pour contrôler les moteurs:\n"
        motor_guidance += "🎚️ **Réglage de la vitesse**: Utilisez le panneau Monitoring pour ajuster la vitesse des moteurs avec les sliders\n"
        motor_guidance += "⚙️ **Configuration du Tau**: Allez dans Settings pour modifier la constante de temps (tau) qui contrôle l'accélération/décélération\n"
        motor_guidance += f"📊 État actuel:\n"
        
        if machine_state.get('motors'):
            for motor in machine_state['motors']:
                motor_guidance += f"  - Motor {motor['id']}: Vitesse={motor['current_speed']:.1f}%, Tau={motor['tau_s']:.2f}s\n"
        
        if not machine_state.get('isOn'):
            motor_guidance += "\n⚠️ La machine est éteinte. Allumez-la d'abord pour contrôler les moteurs."
        
        return motor_guidance
    
    # Aide générale et menus
    if any(word in msg_lower for word in ["aide", "help", "guide", "menu", "comment", "quoi", "que faire"]):
        return """👋 **Bienvenue au Guide DemoMachine!**

Voici ce que vous pouvez faire:

🔍 **Monitoring** - Visualisez l'état en temps réel:
   • Vitesse actuelle et cible des moteurs
   • Historique des vitesses (10 dernières minutes)
   • État de la machine (puissance, erreurs, e-stop)

⚙️ **Settings** - Configurez la machine:
   • Ajustez le Tau (constante de temps) de chaque moteur
   • Valeurs recommandées: 0.1s (rapide) à 10s (lent)

🎚️ **Contrôles** - Interagissez directement:
   • Allumez/éteignez la machine (bouton toggle)
   • Réglez les vitesses cibles avec les sliders
   • Gestion de l'arrêt d'urgence et des erreurs

💬 **Chatbot** (Vous êtes ici!) - Obtenir de l'aide
   • Posez des questions sur les moteurs, l'état, les menus...

**Besoin d'aide avec un élément spécifique?** Posez votre question!"""
    
    # État et diagnostique
    if any(word in msg_lower for word in ["état", "state", "status", "diagnostic", "santé"]):
        state_msg = "📊 **État de la Machine**\n"
        
        is_on = machine_state.get('isOn', False)
        state_msg += f"🔌 Alimentation: {'✅ ON' if is_on else '❌ OFF'}\n"
        
        has_warning = machine_state.get('hasWarning', False)
        state_msg += f"⚠️ Alerte: {'🟡 ACTIVE' if has_warning else '✅ Aucune'}\n"
        
        door_open = machine_state.get('doorOpen', False)
        state_msg += f"🚪 Porte: {'❌ OUVERTE' if door_open else '✅ Fermée'}\n"
        
        error_active = machine_state.get('errorActive', False)
        state_msg += f"❌ Erreur: {'🔴 ACTIVE' if error_active else '✅ Aucune'}\n"
        
        if machine_state.get('motors'):
            state_msg += "\n🎚️ **Moteurs**\n"
            for motor in machine_state['motors']:
                state_msg += f"  Motor {motor['id']}: {motor['current_speed']:.1f}% → {motor['target_speed']:.1f}% (τ={motor['tau_s']:.2f}s)\n"
        
        if not is_on:
            state_msg += "\n💡 **Suggestion**: La machine est éteinte. Allez au Monitoring pour l'allumer."
        
        return state_msg
    
    # Arrêt d'urgence
    if any(word in msg_lower for word in ["emergency", "arrêt", "e-stop", "urgence", "stop"]):
        return """🛑 **Arrêt d'Urgence - Guide d'Utilisation**

L'arrêt d'urgence est un mécanisme de sécurité avec 2 étapes:

1️⃣ **Activation**:
   • Appuyez sur le bouton E-STOP (rouge) dans le Monitoring
   • La machine s'arrête immédiatement
   • Le bouton se bloque en position enfoncée

2️⃣ **Quittance (Acknowledge)**:
   • Relâchez le bouton E-STOP
   • Appuyez sur le bouton "Acknowledge" pour déverrouiller
   • La machine peut alors redémarrer

⚠️ **Important**: 
   • Ne pas utiliser pour un arrêt normal - utilisez plutôt le toggle Power
   • L'E-stop doit être relâché AVANT d'utiliser Acknowledge
   • Vérifiez la cause de l'urgence avant de réactiver"""
    
    # Porte
    if any(word in msg_lower for word in ["porte", "door", "fermer", "ouvrir"]):
        door_status = machine_state.get('doorOpen', False)
        return f"""🚪 **État de la Porte**

État actuel: {'❌ OUVERTE' if door_status else '✅ Fermée'}

La porte contrôle l'état de sécurité de la machine:
• Porte fermée → Machine peut fonctionner
• Porte ouverte → Machine s'arrête immédiatement pour sécurité

Pour simuler l'ouverture/fermeture: allez dans **Monitoring** et utilisez le bouton "Simulate Door"."""
    
    # Erreur
    if any(word in msg_lower for word in ["erreur", "error", "erreur", "problème", "problèmes"]):
        error_active = machine_state.get('errorActive', False)
        return f"""❌ **Gestion des Erreurs**

État actuel: {'🔴 ERREUR ACTIVE' if error_active else '✅ Pas d\'erreur'}

Les erreurs déclenchent un arrêt de sécurité:
• La machine s'arrête immédiatement
• Vous devez appuyer sur "Error Acknowledge" pour reprendre

Pour quittancer une erreur:
1. Allez au **Monitoring**
2. Appuyez sur le bouton "Error Acknowledge" (maintenu)
3. La machine redémarrera après quittance

Les erreurs sont automatiquement simulables via les boutons du Monitoring."""
    
    # Allumer/Éteindre
    if any(word in msg_lower for word in ["allumer", "éteindre", "on", "off", "power", "puissance"]):
        is_on = machine_state.get('isOn', False)
        return f"""🔌 **Contrôle de l'Alimentation**

État actuel: {'✅ Machine ON' if is_on else '❌ Machine OFF'}

Pour allumer/éteindre la machine:
1. Allez au **Monitoring**
2. Cliquez sur le bouton **"Power On/Off"** (bouton toggle en haut à droite)

**Conditions de démarrage**:
La machine ne peut démarrer que si:
✅ E-Stop n'est pas actif
✅ Pas d'erreur active
✅ Porte fermée

Si la machine refuse de démarrer, vérifiez ces conditions!"""
    
    # Par défaut - suggestion générale
    return """Désolé, je n'ai pas bien compris votre question.

Essayez de demander:
• **"Aide"** - Guide complet
• **"État"** - État actuel de la machine
• **"Moteurs"** - Contrôle des moteurs
• **"E-Stop"** - Arrêt d'urgence
• **"Porte"** - État de la porte
• **"Erreur"** - Gestion des erreurs
• **"Power"** - Allumer/éteindre

Ou posez simplement votre question en français! 🤖"""


@app.post("/llm-chat")
def llm_chat(payload: LLMChatPayload):
    """Endpoint de chat LLM avec accès au contexte machine"""
    try:
        response = generate_llm_response(payload.message, payload.machine_state)
        return {
            "status": "ok",
            "response": response
        }
    except Exception as e:
        return {
            "status": "error",
            "response": f"Erreur lors du traitement: {str(e)}"
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