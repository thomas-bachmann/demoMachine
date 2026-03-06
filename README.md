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

## Structure

```
.
├── docker-compose.yml
├── Makefile
├── backend/          # API FastAPI
├── frontend/         # App Vue.js
└── mcp/              # Serveur MCP SSE
```