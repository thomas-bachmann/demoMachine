"""
PLC (Programmable Logic Controller) - Contrôle bas niveau de la machine
Gère la logique de sécurité, les règles de transition d'état et la simulation.
Ce module encapsule la vraie logique de la machine.
"""
import time
from models import MachineState


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

        # Si une erreur est présente, forcer l'arrêt de la machine
        if self.state.has_error:
            self.state.is_on = False
            self._is_power_on_requested = False

        # Gérer la demande d'allumage (après vérification des conditions)
        if self._is_power_on_requested and not self.state.is_on:
            # Vérifier les conditions de sécurité
            if not self.state.emergency_stop_active and not self.state.has_error:
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
        if self.state.has_error:
            return False  # Erreur présente

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

    def _reset_motors(self):
        """Réinitialise les moteurs (vitesse à 0)"""
        for motor in self.state.motors:
            motor.target_speed = 0

    # ========== DIAGNOSTIC ==========

    def set_warning(self, active: bool):
        """Défini l'état d'alerte (simulation)"""
        if self.state.is_on:
            self.state.has_warning = active

    def set_error(self, active: bool):
        """Défini l'état d'erreur (simulation)"""
        if active and not self.state.has_error:
            # L'erreur s'active
            self.state.has_error = True
            # SÉCURITÉ: arrêter la machine en cas d'erreur
            self.state.is_on = False
            self._reset_motors()
        elif not active:
            # L'erreur se désactive
            self.state.has_error = False

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
