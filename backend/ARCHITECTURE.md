# Architecture Backend - Modèle PLC/Bus

## Vue d'ensemble

L'architecture du backend suit le modèle classique d'une machine industrielle avec séparation des responsabilités:

```
┌─────────────────────────────────────────────┐
│           Frontend (IPC)                    │
│    Logique de programmation métier          │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│         BUS (main.py)                       │
│    Exposition des actions - Endpoints REST  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         PLC (plc.py)                        │
│    Contrôle bas niveau - Logique sécurité   │
│    Gestion des transitions d'état           │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      État Machine (models.py)               │
│    Modèles de données - MachineState        │
└─────────────────────────────────────────────┘
```

## Composants

### 1. **models.py** - Modèles de données
Contient les définitions Pydantic pour:
- `Motor` - État d'un moteur (vitesse actuelle, vitesse cible, etc.)
- `MachineState` - État complet de la machine
- Payloads d'entrée pour l'API

**Responsabilité**: Définir la structure des données

### 2. **plc.py** - PLC (Programmable Logic Controller)
Le cœur de la logique machine. Contient `MachineController` qui gère:

**Logique de sécurité (Safety Critical)**:
- ✓ Arrêt d'urgence à priorité absolue
- ✓ Arrêt de la machine en cas d'erreur
- ✓ Vérification des conditions avant démarrage
- ✓ Réinitialisation en cas de défaut

**Gestion des états**:
- Puissance: `request_power_on()`, `request_power_off()`, `toggle_power()`
- Moteurs: `set_motor_speed()`
- Diagnostic: `set_warning()`, `set_error()`
- E-Stop: `trigger_emergency_stop()`, `acknowledge_emergency_stop()`

**Simulation**:
- Mise à jour cyclique des moteurs via `update()`

**Responsabilité**: Implémenter la vraie logique machine, garantir la sécurité

### 3. **main.py** - Bus (API REST)
Expose les capacités du PLC via une API REST. Pour chaque action:
1. Appelle le PLC
2. Récupère l'état mis à jour
3. Notifie les webhooks (n8n)
4. Retourne l'état au client

**Endpoints**:
- `GET /state` - Récupère l'état courant
- `POST /toggle` - Toggle power
- `POST /power-on` - Demande allumage
- `POST /power-off` - Demande extinction
- `POST /speed-target` - Défini vitesse moteur
- `POST /warning` - Toggle alerte
- `POST /error` - Toggle erreur
- `POST /emergency-stop` - Toggle e-stop
- `POST /emergency-stop-acknowledge` - Hold-to-confirm

**Responsabilité**: Exposer les capacités du PLC, pas de logique métier

## Flux de commande exemple: Allumage de la machine

```
1. Frontend → POST /toggle
        ↓
2. Bus (main.py) appelle plc.toggle_power()
        ↓
3. PLC vérifie:
   - E-stop actif? → NON
   - Erreur présente? → NON
   - → Allumage AUTORISÉ
        ↓
4. PLC met machine ON
        ↓
5. Webhook n8n notifié
        ↓
6. État retourné au frontend
```

## Cas de sécurité: Démarrage avec E-stop actif

```
1. Frontend → POST /toggle (pendant e-stop)
        ↓
2. Bus appelle plc.toggle_power()
        ↓
3. PLC vérifie:
   - E-stop actif? → OUI
   - → Allumage REFUSÉ (machine reste OFF)
        ↓
4. État retourné (is_on: false)
```

## Mise à jour cyclique

Le PLC applique les règles de sécurité à chaque appel à `update()`:

```python
plc.update()
# Appelée automatiquement par:
# - plc.get_state()
# - Chaque endpoint API
```

**Garantit que**:
- E-stop arrête toujours la machine (même si pas de commande)
- Erreur arrête toujours la machine
- Moteurs tournent seulement si machine est ON
- Transitions d'état sont cohérentes

## Avantages de cette architecture

1. **Sécurité**: Règles de sécurité au niveau PLC, impossible à contourner par le bus
2. **Maintenabilité**: Logique métier séparée du bus d'exposition
3. **Testabilité**: Le PLC peut être testé indépendamment de l'API
4. **Extensibilité**: Ajouter un nouveau transport (MQTT, etc.) ne demande que de dupliquer le bus
5. **Réalisme**: Correspond au modèle réel des machines industrielles

## Évolution future

- Ajouter un bus MQTT en plus de REST
- Localiser la logique métier dans le PLC au lieu du frontend
- Ajouter un historique d'événements
- Implémenter des modes opératoires (Automatique, Manuel, Diagnostic)
