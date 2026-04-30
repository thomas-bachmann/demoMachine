"""
PLC (Programmable Logic Controller) - Contrôle bas niveau de la machine
Gère la logique de sécurité, les règles de transition d'état et la simulation.
Ce module encapsule la vraie logique de la machine.
"""
import time
from models import MachineState
from alarm_history import get_alarm_history


class MachineController:
    """
    PLC - Contrôleur logique programmable
    
    Responsabilités:
    - État de la machine
    - Règles de sécurité et transitions d'état valides
    - Simulation des moteurs
    - Gestion de l'arrêt d'urgence au niveau bas niveau
    """

    def __init__(self):
        self.state = MachineState()
        self._is_power_on_requested = False

    def update(self):
        """
        Mise à jour cyclique du PLC.
        À appeler régulièrement (ex: 500ms) pour mettre à jour la simulation.
        C'est ici que les règles de sécurité en temps réel sont appliquées.
        """
        # Mise à jour du timing
        now = time.monotonic()
        dt = now - self.state.last_update
        self.state.last_update = now

        # LOGIQUE DE SÉCURITÉ NIVEAU PLC:
        # Si emergency stop est actif, forcer l'arrêt de la machine
        if self.state.emergency_stop_active:
            self.state.is_on = False
            self._is_power_on_requested = False

        # Si une erreur est active, forcer l'arrêt de la machine
        if self.state.error_active:
            self.state.is_on = False
            self._is_power_on_requested = False

        # Si la porte est ouverte, forcer l'arrêt de la machine
        if self.state.door_open:
            self.state.is_on = False
            self._is_power_on_requested = False

        # Gérer la demande d'allumage (après vérification des conditions)
        if self._is_power_on_requested and not self.state.is_on:
            # Vérifier les conditions de sécurité
            if not self.state.emergency_stop_active and not self.state.error_active:
                self.state.is_on = True
            self._is_power_on_requested = False

        # Mise à jour de la simulation des moteurs
        for motor in self.state.motors:
            motor.update_speed(self.state.is_on, dt)

    def get_state(self) -> MachineState:
        """Retourne l'état courant de la machine"""
        self.update()
        return self.state

    # ========== COMMANDES DE PUISSANCE ==========

    def request_power_on(self) -> bool:
        """
        Demande l'allumage de la machine.
        Le PLC vérifie les conditions de sécurité.
        Retourne True si la demande a été acceptée.
        """
        if self.state.is_on:
            return True  # Déjà allumé

        # Vérifier les conditions de sécurité
        if self.state.emergency_stop_active:
            return False  # E-stop actif
        if self.state.error_active:
            return False  # Erreur présente
        if self.state.door_open:
            return False  # Porte ouverte

        # Demande acceptée
        self._is_power_on_requested = True
        return True

    def request_power_off(self) -> bool:
        """Demande l'extinction de la machine"""
        if not self.state.is_on:
            return True  # Déjà éteint

        self.state.is_on = False
        self._reset_motors()
        return True

    def toggle_power(self) -> bool:
        """Toggle la puissance (on/off)"""
        if self.state.is_on:
            return self.request_power_off()
        else:
            return self.request_power_on()

    # ========== CONTRÔLE DES MOTEURS ==========

    def set_motor_speed(self, motor_id: int, target_speed: float) -> bool:
        """
        Défini la vitesse cible d'un moteur.
        La vitesse n'est appliquée que si la machine est en marche.
        """
        if motor_id < 1 or motor_id > len(self.state.motors):
            return False

        motor = self.state.motors[motor_id - 1]
        motor.target_speed = target_speed
        return True

    def set_motor_tau(self, motor_id: int, tau_s: float) -> bool:
        """
        Modifie la constante de temps (tau) d'un moteur.
        Le tau contrôle la vitesse d'accélération/décélération du moteur.
        """
        if motor_id < 1 or motor_id > len(self.state.motors):
            return False

        motor = self.state.motors[motor_id - 1]
        motor.tau_s = max(0.1, min(10.0, tau_s))  # Clamp entre 0.1 et 10
        return True

    def _reset_motors(self):
        """Réinitialise les moteurs (vitesse à 0)"""
        for motor in self.state.motors:
            motor.target_speed = 0

    # ========== DIAGNOSTIC ==========

    def set_warning(self, active: bool):
        """Défini l'état d'alerte (simulation) - peut être toggleé à tout moment"""
        # Si le statut change, logger l'événement
        if active != self.state.has_warning:
            if active:
                get_alarm_history().log_alarm("warning", "Warning activated")
            else:
                get_alarm_history().log_alarm("warning", "Warning deactivated")
        
        self.state.has_warning = active

    def set_door(self, open: bool):
        """Défini l'état de la porte (simulation)"""
        self.state.door_open = open

    def set_error_condition(self, error_present: bool):
        """
        Gère la condition d'erreur (automatique, pas de bouton humain).
        
        Logique:
        - Si erreur passe de False → True: activer l'error_active de la machine
        - Une erreur reste active jusqu'à acknowledge même après disparition de la condition
        """
        was_error = self.state.error_condition
        self.state.error_condition = error_present
        
        # Transition: condition d'erreur se déclenche → activer l'error_active
        if error_present and not was_error:
            self.state.error_active = True
            self.state.error_acknowledged = False
            # SÉCURITÉ: arrêt immédiat
            self.state.is_on = False
            self._reset_motors()
            # Log l'erreur
            get_alarm_history().log_alarm("error", "Error condition triggered - machine stopped")
        
        return True

    def set_error_acknowledge(self, acknowledged: bool):
        """
        Gère le bouton de quittance (acknowledge) de l'erreur.
        
        Logique:
        - Quand acknowledged=true: désactive l'error_active ET réinitialise la condition
        - Quand acknowledged=false: rien
        """
        self.state.error_acknowledged = acknowledged
        
        # L'acknowledge réinitialise complètement l'erreur
        if acknowledged:
            self.state.error_active = False
            self.state.error_condition = False
        
        return True

    # ========== ARRÊT D'URGENCE (Safety Critical) ==========

    def set_emergency_stop_button(self, button_pressed: bool) -> bool:
        """
        Gère le bouton d'arrêt d'urgence à crantage.
        
        Logique:
        - Si bouton passe de False → True: activer l'e-stop de la machine
        - L'e-stop reste actif même après relâchement du bouton
        - Seul acknowledge peut le désactiver (si bouton est relâché)
        """
        was_pressed = self.state.emergency_stop_button_pressed
        self.state.emergency_stop_button_pressed = button_pressed
        
        # Transition: bouton enfoncé → activer l'e-stop
        if button_pressed and not was_pressed:
            self.state.emergency_stop_active = True
            self.state.emergency_stop_acknowledged = False
            # SÉCURITÉ: arrêt immédiat
            self.state.is_on = False
            self._reset_motors()
            # Log l'arrêt d'urgence
            get_alarm_history().log_alarm("error", "EMERGENCY STOP triggered - machine stopped")
        
        return True

    def set_emergency_stop_acknowledge(self, acknowledged: bool) -> bool:
        """
        Gère le bouton de quittance (acknowledge).
        
        Logique:
        - Ne fonctionne que si le bouton d'e-stop est RELÂCHÉ
        - Quand acknowledged=true: désactive l'e-stop si bouton est relâché
        - Quand acknowledged=false: rien
        """
        self.state.emergency_stop_acknowledged = acknowledged
        
        # La quittance ne peut désactiver l'e-stop que si le bouton est relâché
        if acknowledged and not self.state.emergency_stop_button_pressed:
            self.state.emergency_stop_active = False
        
        return True
