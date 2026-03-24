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
      "url": "http://localhost:8001/sse"
    },
    "demo-machine": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8001/sse"
      ]
    }
  }
}
```

## Outils MCP disponibles

| Outil         | Description                                      |
|---------------|--------------------------------------------------|
| get_status    | Retourne le health check de l'API                |
| get_state     | Retourne l'état (is_on, has_warning, has_error)  |
| toggle_power  | Allume ou éteint la machine                      |
| toggle_warning| Active/désactive le warning                      |
| toggle_error  | Active/désactive l'erreur                        |

## Déploiement serveur (Hetzner) pas à pas

Ce guide décrit une configuration simple et sécurisée : SSH par clé, port SSH custom, firewall strict, reverse proxy HTTPS en `443`.

### 1) Créer le serveur

- Image : Ubuntu 24.04
- Type : CX23
- Ajouter votre clé SSH publique lors de la création du serveur
- Volume additionnel : non nécessaire pour cette démo

### 2) Configurer le firewall Hetzner

Règles entrantes minimales :

- `TCP 2222` (SSH) depuis votre IP uniquement (`x.x.x.x/32`)
- `TCP 80` depuis `0.0.0.0/0` et `::/0` (certificat)
- `TCP 443` depuis `0.0.0.0/0` et `::/0`

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
apt -y install git make docker.io nginx certbot python3-certbot-nginx
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

### 7) Mettre en place le reverse proxy Nginx (HTTPS)

Créer `/etc/nginx/sites-available/demo-machine` :

```nginx
server {
  listen 80;
  listen [::]:80;
  server_name votre-domaine.tld;

  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /mcp/sse {
    proxy_pass http://127.0.0.1:8001/sse;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_cache off;
    add_header Cache-Control no-cache;
  }

  location /mcp/messages {
    proxy_pass http://127.0.0.1:8001/messages;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

Activer le site :

```bash
ln -s /etc/nginx/sites-available/demo-machine /etc/nginx/sites-enabled/demo-machine
nginx -t && systemctl reload nginx
```

### 8) Générer le certificat TLS

```bash
certbot --nginx -d votre-domaine.tld
```

Puis vérifier :

- Frontend : `https://votre-domaine.tld/`
- MCP SSE : `https://votre-domaine.tld/mcp/sse`

### 9) Configurer le client MCP

Exemple d'URL à utiliser côté client MCP :

```text
https://votre-domaine.tld/mcp/sse
```

### 10) Checklist sécurité finale

- `22` fermé dans le firewall Hetzner
- SSH uniquement sur `2222`
- Authentification par clé uniquement (`PasswordAuthentication no`)
- Ports `3000`, `8000`, `8001` non exposés publiquement
- Accès public uniquement via `443` (et `80` pour challenge/redirect)

## Structure

```
.
├── docker-compose.yml
├── Makefile
├── backend/          # API FastAPI
├── frontend/         # App Vue.js
└── mcp/              # Serveur MCP SSE
```