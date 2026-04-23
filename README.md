# demoMachine

## But
Démonstrateur de communication entre un simulateur Web de machine et un LLM via MCP.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│    Backend      │◀───│      MCP        │
│   (Vue.js)      │     │   (FastAPI)     │     │   (Python)      │
│   :3000         │     │    :8000        │     │    :8001        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        ▲
                                                        │
                                                ┌───────┴───────┐
                                                │ Claude Desktop│
                                                └───────────────┘
```

## Prérequis
- Docker & Docker Compose
- (Optionnel) Claude Desktop pour utiliser le MCP localement

## Démarrage rapide

```bash
# Lancer tous les services
make up

# Ou avec rebuild
make build

# Arrêter
make down

# Voir les logs
make logs
```

## Accès local
- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000
- **Swagger** : http://localhost:8000/docs
- **MCP** : http://localhost:8001/sse

**Note** : En développement, tous les services sont accessibles sur localhost. En production sur serveur, ils sont accessibles via le reverse proxy Caddy uniquement via le port 80 (HTTP).


## API Backend

### Endpoints Info
| Méthode | Endpoint   | Description                          |
|---------|------------|--------------------------------------|
| GET     | /          | Health check                         |
| GET     | /state     | État complet de la machine           |
| GET     | /logs      | Logs des conteneurs Docker           |

### Endpoints Puissance
| Méthode | Endpoint   | Description                          |
|---------|------------|--------------------------------------|
| POST    | /toggle    | Allumer/éteindre la machine          |
| POST    | /power-on  | Allumer la machine                   |
| POST    | /power-off | Éteindre la machine                  |

### Endpoints Moteurs
| Méthode | Endpoint      | Description                          |
|---------|---------------|--------------------------------------|
| POST    | /speed-target | Définir la vitesse cible d'un moteur |

### Endpoints Diagnostic
| Méthode | Endpoint   | Description                          |
|---------|------------|--------------------------------------|
| POST    | /warning   | Toggle warning (simulation)          |
| POST    | /door      | Toggle état porte (ouvert/fermé)    |
| POST    | /error     | Toggle condition d'erreur            |
| POST    | /destroy   | Détruire la machine (sécurisé par clé) |

### Endpoints Arrêt d'Urgence
| Méthode | Endpoint                    | Description                          |
|---------|----------------------------|--------------------------------------|
| POST    | /error-acknowledge         | Acquitter l'erreur                   |
| POST    | /emergency-stop            | Contrôler le bouton e-stop           |
| POST    | /emergency-stop-acknowledge| Acquitter l'e-stop                   |

## Configuration Claude Desktop (Optionnel)

### Développement local
Ajouter dans `%AppData%\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "demo-machine": {
      "url": "http://localhost:8001/sse"
    }
  }
}
```

### Production (serveur distant)
```json
{
  "mcpServers": {
    "demo-machine": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://YOUR_SERVER_IP:8001/sse",
        "--allow-http"
      ]
    }
  }
}
```

**Note** : Le flag `--allow-http` est nécessaire pour l'accès HTTP non-local. Pour HTTPS, remplacer `http://` par `https://` avec un domaine.


## Outils MCP disponibles

### Info et État
| Outil      | Description                                      |
|------------|--------------------------------------------------|
| get_status | Retourne le health check de l'API                |
| get_state  | Retourne l'état complet (is_on, has_warning, etc)|
| get_logs   | Retourne les logs des conteneurs Docker          |

### Contrôle Puissance
| Outil        | Description                                      |
|--------------|--------------------------------------------------|
| toggle_power | Allume ou éteint la machine                      |

### État Machine (Lecture)
| Outil       | Description                                      |
|-------------|--------------------------------------------------|
| get_warning | Retourne l'état du warning (read-only)           |
| get_error   | Retourne l'état d'erreur (read-only)             |

### Contrôle Moteurs
| Outil           | Description                                      |
|-----------------|--------------------------------------------------|
| set_speed_target| Définit la vitesse cible d'un moteur (0-100)    |

### Diagnostic et Sécurité
| Outil                      | Description                                      |
|----------------------------|--------------------------------------------------|
| error_acknowledge          | Acquitter une condition d'erreur                 |
| emergency_stop             | Contrôler le bouton d'arrêt d'urgence            |
| emergency_stop_acknowledge | Acquitter l'arrêt d'urgence                      |
| destroy_machine            | Détruire la machine (nécessite clé de sécurité)  |

## Déploiement serveur (Hetzner) pas à pas

Ce guide décrit une configuration simple et sécurisée : SSH par clé, port SSH custom, firewall strict, reverse proxy HTTP sur IP (HTTPS optionnel, via Caddy).

### 1) Créer le serveur

- Image : Ubuntu 24.04
- Type : CX23
- Ajouter votre clé SSH publique lors de la création du serveur
- Volume additionnel : non nécessaire pour cette démo

### 2) Configurer le firewall Hetzner

Règles entrantes minimales :

- `TCP 2222` (SSH) depuis votre IP uniquement (`x.x.x.x/32`)
- `TCP 80` (HTTP) depuis `0.0.0.0/0` et `::/0`

Règles sortantes :

- Démarrage : tout autoriser
- Durcissement ultérieur possible (`53`, `123`, `80`, `443`)

### 3) Vérifier et durcir SSH

Se connecter :

```bash
ssh -p 2222 root@IP_SERVEUR
```

Vérifier l'écoute :

```bash
ss -ltnp | grep ssh
```

Vous devez voir uniquement le port `2222` une fois la migration terminée.

### 4) Installer les dépendances système

```bash
apt update && apt -y upgrade
apt -y install git make docker.io caddy
systemctl enable --now docker
```

### 5) Cloner le projet et lancer la stack

```bash
git clone <URL_DU_REPO>
cd demoMachine
make build
make logs
```

### 6) Vérifier les services Docker

```bash
docker compose ps
curl http://127.0.0.1:3000
curl http://127.0.0.1:8000
curl http://127.0.0.1:8001/sse
```


### 7) Configuration reverse proxy Caddy

Créer le fichier `.env` avec:

```bash
DOMAIN=example.com
SERVER_IP=YOUR_SERVER_IP
N8N_WEBHOOK_URL=https://example.com/n8n/webhook
N8N_BASIC_AUTH_PW=your_password
DESTROY_KEY=your_secret_key
```

Générer et recharger Caddy:

```bash
make caddy-apply
```

Cela génère le `caddy_config/Caddyfile` depuis le template et recharge le service Caddy.

### 8) Accès public

Depuis votre PC/téléphone, vérifier:

```bash
curl http://YOUR_SERVER_IP/n8n/
```

Ou navigateur:
- n8n : `http://YOUR_SERVER_IP/n8n/`
- Frontend : `http://YOUR_SERVER_IP:3000/` (non proxy)
- Backend : `http://YOUR_SERVER_IP:8000/` (non proxy)
- MCP : `http://YOUR_SERVER_IP:8001/sse` (non proxy)

### 9) Configurer le client MCP pour le serveur distant

Dans Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "demo-machine": {
      "command": "npx",
      "args": ["mcp-remote", "http://YOUR_SERVER_IP:8001/sse", "--allow-http"]
    }
  }
}
```

### 10) Configuration du démarrage automatique

Pour que la stack démarre automatiquement au reboot du serveur:

```bash
sudo cp demomachine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable demomachine.service
```

Vérifier le statut:

```bash
sudo systemctl status demomachine.service
sudo journalctl -u demomachine.service -f  # Voir les logs
```

### 11) Checklist sécurité finale

- `22` fermé dans le firewall Hetzner
- SSH uniquement sur `2222`
- Authentification par clé uniquement (`PasswordAuthentication no`)
- Ports `3000`, `8000`, `8001` non exposés au public (localhost-bound)
- Accès public uniquement via port `80` (HTTP) via Caddy reverse proxy
- ⚠️ **À faire ultérieurement** : Migrer vers HTTPS avec Certbot + domaine pour enlever le flag `--allow-http`

### 11) Configurer le démarrage automatique (optionnel)

Pour que la stack démarre automatiquement au reboot du serveur :

```bash
sudo cp demomachine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable demomachine.service
```

Vérifier le statut :

```bash
sudo systemctl status demomachine.service
sudo journalctl -u demomachine.service -f  # Voir les logs
```

## Nettoyage de l'ancien reverse proxy Nginx

- Le dossier `deploy/nginx/` et ses fichiers peuvent être supprimés.
- Les volumes ou scripts liés à Nginx ne sont plus nécessaires.
- Toute la configuration de reverse proxy est désormais gérée par Caddy.

## Structure du projet

```
.
├── docker-compose.yml          # Configuration des services
├── Makefile                    # Commandes d'administration
├── demomachine.service         # Service systemd pour démarrage automatique
├── README.md
├── backend/                    # API FastAPI + PLC
│   ├── main.py                # Routes API + logs Docker
│   ├── plc.py                 # Logique machine (PLC)
│   ├── models.py              # Modèles Pydantic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Application Vue.js
│   ├── src/
│   │   ├── App.vue            # Interface principale
│   │   ├── main.js
│   │   └── components/        # Composants Vue
│   │       ├── MotorSlider.vue
│   │       └── MotorSummaryCard.vue
│   ├── package.json
│   ├── Dockerfile
│   └── Caddyfile
├── mcp/                        # Serveur MCP (Model Context Protocol)
│   ├── main.py                # Outils MCP
│   ├── utils.py               # Utilitaires HTTP
│   ├── requirements.txt
│   └── Dockerfile
├── caddy_config/              # Configuration reverse proxy
│   └── Caddyfile.template
└── n8n_data/                  # Données persistantes n8n
```

## Notes importantes

- **Services internes** : Frontend (3000), Backend (8000), MCP (8001) écoutent uniquement sur `127.0.0.1` en production
- **Accès public** : Via reverse proxy Caddy sur le port 80/443
- **Docker socket** : Monté dans le backend pour accéder aux logs des conteneurs via `get_logs`
- **Stockage n8n** : Utilise un volume Docker persistant `n8n_data`
