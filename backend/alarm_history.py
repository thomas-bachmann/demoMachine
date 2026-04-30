"""
Historique des alarmes et erreurs.
Logs tous les événements (warnings, errors) dans un fichier de log.
"""
import os
from datetime import datetime
from pathlib import Path
from threading import Lock


class AlarmHistory:
    """Gère l'historique des alarmes et erreurs"""
    
    def __init__(self, log_file: str = "alarm_history.log"):
        self.log_file = Path(log_file)
        self.lock = Lock()
        # Créer le fichier s'il n'existe pas
        if not self.log_file.exists():
            self.log_file.touch()
    
    def log_alarm(self, alarm_type: str, message: str):
        """
        Enregistre une alarme ou erreur dans l'historique.
        
        Args:
            alarm_type: Type d'alarme ('warning' ou 'error')
            message: Description de l'événement
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{alarm_type.upper()}] {message}\n"
        
        with self.lock:
            try:
                with open(self.log_file, "a") as f:
                    f.write(log_entry)
            except Exception as e:
                print(f"Error writing to alarm log: {e}")
    
    def get_alarms(self) -> list[dict]:
        """
        Récupère tous les enregistrements d'alarmes.
        
        Returns:
            Liste de dictionnaires contenant timestamp, type et message
        """
        alarms = []
        
        try:
            with self.lock:
                if self.log_file.exists():
                    with open(self.log_file, "r") as f:
                        for line in f:
                            alarm = self._parse_log_line(line)
                            if alarm:
                                alarms.append(alarm)
        except Exception as e:
            print(f"Error reading alarm log: {e}")
        
        # Retourner dans l'ordre inverse (les plus récents en premier)
        return list(reversed(alarms))
    
    def _parse_log_line(self, line: str) -> dict | None:
        """
        Parse une ligne de log.
        Format: [YYYY-MM-DD HH:MM:SS] [TYPE] message
        """
        line = line.strip()
        if not line:
            return None
        
        try:
            # Extraire le timestamp
            timestamp_end = line.find("]")
            if timestamp_end == -1:
                return None
            timestamp = line[1:timestamp_end]
            
            # Extraire le type
            rest = line[timestamp_end + 2:]
            type_end = rest.find("]")
            if type_end == -1:
                return None
            alarm_type = rest[1:type_end].lower()
            
            # Extraire le message
            message = rest[type_end + 2:]
            
            return {
                "timestamp": timestamp,
                "type": alarm_type,
                "message": message
            }
        except Exception:
            return None
    
    def clear_alarms(self):
        """Efface l'historique des alarmes"""
        with self.lock:
            try:
                self.log_file.write_text("")
            except Exception as e:
                print(f"Error clearing alarm log: {e}")


# Instance globale
_alarm_history = None


def get_alarm_history() -> AlarmHistory:
    """Récupère l'instance globale de AlarmHistory"""
    global _alarm_history
    if _alarm_history is None:
        _alarm_history = AlarmHistory()
    return _alarm_history
