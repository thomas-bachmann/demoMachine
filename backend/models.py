"""
Modèles de données pour la machine
"""
from pydantic import BaseModel, Field
from typing import List
import math
import time


class Motor(BaseModel):
    """Modèle d'un moteur"""
    id: int = 0
    current_speed: float = 0.0
    target_speed: float = 0.0
    tau_s: float = 1.5  # Constante de temps pour la simulation

    def update_speed(self, is_running: bool, dt: float):
        """Simule la mise à jour de la vitesse du moteur"""
        desired = self.target_speed if is_running else 0.0
        alpha = 1.0 - math.exp(-dt / max(self.tau_s, 1e-3))
        self.current_speed += alpha * (desired - self.current_speed)


class MachineState(BaseModel):
    """État complet de la machine exposé par le PLC"""
    # État d'alimentation
    is_on: bool = False
    
    # États de diagnostic
    has_warning: bool = False
    door_open: bool = False  # True = porte ouverte, False = porte fermée
    
    # État d'erreur (3 niveaux distincts - même logique que e-stop mais automatique)
    error_condition: bool = False        # La condition d'erreur existe (capteur, etc.)
    error_active: bool = False           # L'état verrouillé de la machine
    error_acknowledged: bool = False     # Le bouton acknowledge a été pressé
    
    # État d'arrêt d'urgence (3 niveaux distincts)
    emergency_stop_button_pressed: bool = False  # Le bouton physique à crantage
    emergency_stop_active: bool = False          # L'état verrouillé de la machine
    emergency_stop_acknowledged: bool = False    # Le bouton acknowledge a été pressé
    
    # Moteurs
    motors: List[Motor] = Field(
        default_factory=lambda: [
            Motor(id=1, tau_s=1.5),
            Motor(id=2, tau_s=3.0)
        ]
    )
    
    # Timing (interne)
    last_update: float = Field(default_factory=time.monotonic)


# Payloads d'entrée pour l'API
class SetMotorSpeedPayload(BaseModel):
    """Payload pour définir la vitesse d'un moteur"""
    target_speed: float = Field(ge=0, le=100, description="Vitesse cible 0-100")
    motor_id: int = Field(ge=1, le=2, description="ID du moteur (1-2)")


class EmergencyStopButtonPayload(BaseModel):
    """Payload pour le bouton d'arrêt d'urgence à crantage"""
    button_pressed: bool = Field(description="État du bouton: true=enfoncé, false=relâché")


class EmergencyStopAcknowledgePayload(BaseModel):
    """Payload pour le bouton de quittance (acknowledge)"""
    acknowledged: bool = Field(description="true=appuyé sur quittance, false=relâché")


class ErrorAcknowledgePayload(BaseModel):
    """Payload pour le bouton de quittance (acknowledge) de l'erreur"""
    acknowledged: bool = Field(description="true=appuyé sur quittance, false=relâché")


class SetMotorTauPayload(BaseModel):
    """Payload pour modifier le tau d'un moteur"""
    motor_id: int = Field(ge=1, le=2, description="ID du moteur (1-2)")
    tau_s: float = Field(ge=0.1, le=10.0, description="Constante de temps en secondes")
