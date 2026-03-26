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
- Node.js (pour Claude Desktop MCP)

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

## Accès
- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000
- **Swagger** : http://localhost:8000/docs
- **MCP SSE** : http://localhost:8001/sse

## API Backend

| Méthode | Endpoint   | Description                          |
|---------|------------|--------------------------------------|
| GET     | /          | Health check                         |
| GET     | /state     | État de la machine                   |
| POST    | /toggle    | Allumer/éteindre                     |
| POST    | /warning   | Activer/désactiver warning           |
| POST    | /error     | Activer/désactiver erreur            |

## Configuration Claude Desktop

Ajouter dans `%AppData%\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "demo-machine": {
      "url": "http://localhost:8001/sse" # URL locale pour développement
    },
    "demo-machine": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://IP/mcp/sse", # URL publique après déploiement
        "--allow-http"
      ]
    }
  }
}
```

**Note** : Le flag `--allow-http` est nécessaire pour l'accès HTTP non-local. Pour HTTPS, remplacer `http://` par `https://`.

## Outils MCP disponibles

| Outil         | Description                                      |
|---------------|--------------------------------------------------|
| get_status    | Retourne le health check de l'API                |
| get_state     | Retourne l'état (is_on, has_warning, has_error)  |
| toggle_power  | Allume ou éteint la machine                      |
| toggle_warning| Active/désactive le warning                      |
| toggle_error  | Active/désactive l'erreur                        |

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


### 7) Mettre en place le reverse proxy Caddy

Créer le template `caddy_config/Caddyfile.template` :

```caddyfile
http://$SERVER_IP {
    handle_path /n8n/* {
        reverse_proxy n8n:5678
    }
    encode gzip
}
```

Générer le Caddyfile et recharger Caddy :

```bash
make caddy-apply
```

Cela va générer le fichier `caddy_config/Caddyfile` à partir du template et recharger le service Caddy.


### 8) Vérifier l'accès public

Depuis votre PC/téléphone, vérifier :

```bash
curl http://IP/n8n/
```

Ou accéder via navigateur :

- n8n : `http://IP/n8n/`
- Frontend : `http://IP:3000/`
- MCP SSE : `http://IP:8001/sse`

### 9) Configurer le client MCP

Dans Claude Desktop (`claude_desktop_config.json`) :

```json
{
  "mcpServers": {
    "demo-machine": {
      "command": "npx",
      "args": ["mcp-remote", "http://IP/mcp/sse", "--allow-http"]
    }
  }
}
```

### 10) Checklist sécurité finale

- `22` fermé dans le firewall Hetzner
- SSH uniquement sur `2222`
- Authentification par clé uniquement (`PasswordAuthentication no`)
- Ports `3000`, `8000`, `8001` non exposés au public (localhost-bound)
- Accès public uniquement via port `80` (HTTP) via Caddy reverse proxy
- ⚠️ **À faire ultérieurement** : Migrer vers HTTPS avec Certbot + domaine pour enlever le flag `--allow-http`

## Nettoyage de l'ancien reverse proxy Nginx

- Le dossier `deploy/nginx/` et ses fichiers peuvent être supprimés.
- Les volumes ou scripts liés à Nginx ne sont plus nécessaires.
- Toute la configuration de reverse proxy est désormais gérée par Caddy.

## Structure

```
.
├── docker-compose.yml
├── Makefile
├── backend/          # API FastAPI
├── frontend/         # App Vue.js
└── mcp/              # Serveur MCP SSE
```