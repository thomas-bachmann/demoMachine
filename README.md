# demoMachine

## 📋 Description

Démonstrateur d'une machine industrielle virtuelle avec interface web et intégration LLM via MCP (Model Context Protocol). Le projet permettre aux LLMs de contrôler et d'interagir avec une machine simulée et de consulter son état en temps réel.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue.js)                        │
│                 :3000 (localhost/production)                    │
└────────────────────┬────────────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────────────┐
│                  Backend (FastAPI + Docker)                     │
│                    :8000 (localhost)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ BUS (main.py) → PLC (plc.py) → MachineState (models.py) │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Contrôle machines (PowerOn/Off, Motors, E-Stop, etc.)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │ Webhook
┌────────────────────▼────────────────────────────────────────────┐
│                     n8n (Automation)                            │
│                  :5678 (localhost)                              │
└─────────────────────────────────────────────────────────────────┘

                        ┌──────────────────┐
                        │  MCP Server      │
                        │  :8001           │
                        │  ┌────────────┐  │
                        │  │ RAG Indexer│  │
                        │  │ Codebase   │  │
                        │  │ Context    │  │
                        │  └────────────┘  │
                        └────────┬─────────┘
                                 │
                        ┌────────▼────────┐
                        │ Claude Desktop  │
                        │ Claude Web      │
                        └─────────────────┘
```

## 🎯 Objectifs

- **Simulateur machine** : Interface web pour contrôler une machine virtuelle
- **Intégration LLM** : Permet aux LLMs d'accéder à l'état de la machine et d'exécuter des commandes
- **RAG (Retrieval Augmented Generation)** : Indexation du codebase pour fournir du contexte aux LLMs
- **Automatisation** : Intégration n8n pour créer des workflows automatisés
- **Architecture modulaire** : Séparation claire Frontend/Backend/MCP

## 📦 Services

| Service      | Port  | Description                                    |
|--------------|-------|------------------------------------------------|
| **Frontend** | 3000  | Interface Vue.js pour contrôler la machine    |
| **Backend**  | 8000  | API FastAPI - Logique métier et PLC           |
| **MCP**      | 8001  | Serveur MCP - Outils pour Claude             |
| **n8n**      | 5678  | Plateforme d'automatisation                   |
| **Ollama**   | 11434 | LLM local (optionnel)                         |

## 🚀 Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Fichier `.env` configuré (voir [Configuration](#configuration))

### Installation

```bash
# Cloner et entrer dans le répertoire
cd demoMachine

# Créer le fichier .env
cp .env.example .env  # À adapter selon votre configuration

# Lancer tous les services
make up

# Ou avec rebuild (développement)
make build

# Voir les logs
make logs

# Arrêter tout
make down
```

## 🔧 Commandes Makefile

```bash
make up              # Lancer tous les services
make build           # Rebuild + relancer (développement)
make down            # Arrêter tous les services
make restart         # Redémarrer tous les services
make logs            # Logs en temps réel
make clean           # Nettoyer les conteneurs et volumes
make prune           # Nettoyer les images inutilisées
make prune-all       # Nettoyer complètement Docker

# Services spécifiques
make frontend        # Rebuild et lancer Frontend uniquement
make backend         # Rebuild et lancer Backend uniquement
make mcp             # Rebuild et lancer MCP uniquement

# Ollama (LLM local)
make ollama-pull     # Télécharger le modèle configuré
make ollama-list     # Lister les modèles disponibles
make ollama-test     # Tester Ollama
```

## 🌐 Accès local

```
Frontend:          http://localhost:3000
Backend API:       http://localhost:8000
Swagger API Docs:  http://localhost:8000/docs
MCP Server:        http://localhost:8001/sse
n8n Interface:     http://localhost:5678
```

## ⚙️ Configuration

### Fichier `.env`

Créer un fichier `.env` à la racine avec :

```bash
# LLM Configuration
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_API_BASE=                    # Laisser vide pour Anthropic
ANTHROPIC_API_KEY=your_api_key

# n8n Configuration
N8N_BASIC_AUTH_PW=your_password
N8N_WEBHOOK_URL=https://n8n.your-domain/n8n/

# Backend Configuration
DESTROY_KEY=your_secret_key      # Clé pour sécuriser l'endpoint /destroy

# Production (Caddy reverse proxy)
DOMAIN=your-domain.com           # ex: demo.example.com
```

## 📡 API Backend

### Endpoints Info

| Méthode | Endpoint | Description              |
|---------|----------|--------------------------|
| GET     | /        | Health check             |
| GET     | /state   | État complet de la machine |
| GET     | /logs    | Logs des conteneurs Docker |

### Endpoints Puissance

| Méthode | Endpoint    | Description           |
|---------|-------------|-----------------------|
| POST    | /toggle     | Allumer/éteindre      |
| POST    | /power-on   | Allumer la machine    |
| POST    | /power-off  | Éteindre la machine   |

### Endpoints Moteurs

| Méthode | Endpoint      | Description                  |
|---------|---------------|------------------------------|
| POST    | /speed-target | Définir vitesse d'un moteur |

### Endpoints Diagnostic

| Méthode | Endpoint   | Description                  |
|---------|------------|------------------------------|
| POST    | /warning   | Toggle warning (simulation) |
| POST    | /door      | Toggle porte (ouvert/fermé) |
| POST    | /error     | Toggle erreur                |
| POST    | /destroy   | Détruire la machine (sécurisé) |

### Endpoints Arrêt d'Urgence

| Méthode | Endpoint                     | Description              |
|---------|------------------------------|--------------------------|
| POST    | /error-acknowledge           | Acquitter l'erreur       |
| POST    | /emergency-stop              | Contrôler l'e-stop       |
| POST    | /emergency-stop-acknowledge  | Acquitter l'e-stop       |

### Endpoints LLM

| Méthode | Endpoint   | Description                      |
|---------|------------|----------------------------------|
| POST    | /llm-chat  | Chat avec le LLM (via MCP)      |

## 🤖 Configuration Claude Desktop (Optionnel)

Pour utiliser le MCP localement avec Claude Desktop :

**Windows**: `%AppData%\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "demo-machine": {
      "url": "http://localhost:8001/sse"
    }
  }
}
```

Une fois configuré, Claude Desktop aura accès aux outils MCP pour contrôler et interroger la machine.

## 📁 Structure du projet

```
demoMachine/
├── backend/              # API FastAPI + PLC
│   ├── main.py          # Endpoints REST
│   ├── plc.py           # Logique machine (Safety Critical)
│   ├── models.py        # Modèles Pydantic
│   ├── ai.py            # Intégration LLM
│   ├── alarm_history.py # Historique des alarmes
│   ├── ARCHITECTURE.md  # Documentation architecture
│   └── requirements.txt
├── frontend/            # Interface Vue.js
│   ├── src/
│   │   ├── components/  # Composants Vue
│   │   ├── router/      # Routeur Vue
│   │   └── stores/      # Pinia stores
│   ├── vite.config.js
│   └── package.json
├── mcp/                 # Serveur MCP
│   ├── main.py         # Point d'entrée MCP
│   ├── indexer.py      # Indexation du codebase
│   ├── rag.py          # Retrieval Augmented Generation
│   ├── utils.py        # Utilitaires
│   └── requirements.txt
├── caddy_config/        # Configuration reverse proxy
│   └── Caddyfile.template
├── n8n_data/           # Données n8n
├── docker-compose.yml  # Configuration des services
├── Makefile            # Automatisation
└── README.md           # Ce fichier
```

## 🔐 Sécurité

- **E-Stop** : Arrêt d'urgence prioritaire sur tous les autres commandes
- **Destroy Key** : Endpoint `/destroy` protégé par une clé secrète
- **CORS** : Tous les domaines autorisés en développement (adapter en production)
- **État machine** : Validation stricte des transitions d'état dans le PLC

## 🐛 Troubleshooting

### Les services ne démarrent pas
```bash
# Vérifier les logs
make logs

# Nettoyer et redémarrer
make down
docker system prune -f
make build
```

### Port déjà utilisé
```bash
# Trouver le processus utilisant le port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :8001  # MCP

# Ou dans docker-compose.yml, modifier les ports
```

### Modèle LLM non disponible
```bash
# Si en local avec Ollama
make ollama-pull

# Ou utiliser Anthropic (Claude) via API_KEY
```

## 📚 Documentation complémentaire

- [Architecture Backend](backend/ARCHITECTURE.md) - Détails du modèle PLC
- [Makefile](Makefile) - Toutes les commandes disponibles
- [docker-compose.yml](docker-compose.yml) - Configuration des services

## 🚢 Déploiement Production

En production, les services sont exposés via Caddy (reverse proxy) sur le port 80 :

```
https://your-domain.com  → Frontend (port 3000)
https://your-domain.com/api  → Backend (port 8000)
https://your-domain.com/mcp  → MCP (port 8001)
https://your-domain.com/n8n  → n8n (port 5678)
```

Voir `caddy_config/Caddyfile.template` pour la configuration exacte.

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
