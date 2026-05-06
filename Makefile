ENV_FILE := .env

.PHONY: up down build restart logs frontend backend mcp n8n n8n-up stack-up stack-build caddy-apply check clean caddy-fmt docker-df prune prune-all ollama-pull ollama-list ollama-test

COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; fi)

# Lecture du modèle Ollama depuis le .env (ex: ollama/llama3.2:1b → llama3.2:1b)
OLLAMA_MODEL := $(shell grep '^LLM_MODEL=' $(ENV_FILE) 2>/dev/null | cut -d'=' -f2 | sed 's|ollama/||')

ifeq ($(strip $(COMPOSE)),)
$(error Neither 'docker compose' nor 'docker-compose' is available. Please install Docker Compose)
endif

# Cibles internes (stack brute)
stack-up:
	$(COMPOSE) up -d

stack-build:
	$(COMPOSE) down --remove-orphans -v || true
	sleep 2
	$(COMPOSE) up -d --build

# Lance toute la stack + n8n
up: stack-up n8n-up

# Build + relance (local development)
build: stack-build n8n-up ollama-ensure

# Arrête tout
down:
	$(COMPOSE) down

# Redémarre tout
restart: down up

# Logs en temps réel
logs:
	$(COMPOSE) logs -f

# Services individuels
frontend:
	$(COMPOSE) up frontend -d --build

backend:
	$(COMPOSE) up backend -d --build

mcp:
	$(COMPOSE) up mcp -d --build

n8n:
	$(COMPOSE) up n8n -d

# Relance n8n en recréant le conteneur
n8n-up:
	$(COMPOSE) rm -sf n8n || true
	$(COMPOSE) up -d n8n

index:
	$(COMPOSE) exec mcp python indexer.py



# Déploie la conf Caddy host depuis le template versionné
caddy-apply:
	@test -f $(ENV_FILE) || (echo "Missing $(ENV_FILE)" && exit 1)
	@test -f caddy_config/Caddyfile.template || (echo "Missing caddy_config/Caddyfile.template" && exit 1)
	@set -a; . ./$(ENV_FILE); set +a; \
	envsubst '$$SERVER_IP $$DOMAIN' < caddy_config/Caddyfile.template > caddy_config/Caddyfile
	@$(MAKE) caddy-fmt
	@sudo caddy validate --config caddy_config/Caddyfile
	@sudo cp caddy_config/Caddyfile /etc/caddy/Caddyfile
	@sudo systemctl reload caddy

# Formate le Caddyfile généré selon les standards Caddy
caddy-fmt:
	@caddy fmt --overwrite caddy_config/Caddyfile

# Vérifs rapides locales serveur
check:
	@curl -fsS -I http://127.0.0.1:5678 >/dev/null && echo "OK n8n direct (127.0.0.1:5678)"
	@curl -fsS -I http://$${SERVER_IP}/n8n/ >/dev/null && echo "OK caddy /n8n/"

# Affiche l'utilisation disque Docker
docker-df:
	@docker system df

# Supprime images sans tag et conteneurs arrêtés (safe)
prune:
	@echo "Nettoyage des images sans tag..."
	@docker image prune -f
	@echo "Nettoyage des conteneurs arrêtés..."
	@docker container prune -f
	@docker system df

# Supprime tout ce qui n'est pas utilisé, y compris les images non taguées (dangereux)
prune-all:
	@echo "⚠️  Suppression de TOUTES les ressources Docker inutilisées..."
	@read -p "Confirmer? [y/N] " confirm && [ "$$confirm" = "y" ]
	@docker system prune -f
	@docker system df

# Pull le modèle défini dans .env
ollama-pull:
	docker exec machine-ollama ollama pull $(OLLAMA_MODEL)

# Liste les modèles disponibles
ollama-list:
	docker exec machine-ollama ollama list

# Test rapide du modèle
ollama-test:
	docker exec machine-ollama ollama run $(OLLAMA_MODEL) "Réponds en une phrase : quel est ton rôle ?"

# Pull le modèle seulement s'il n'est pas déjà présent
ollama-ensure:
	@docker exec machine-ollama ollama list | grep -q "$(OLLAMA_MODEL)" \
		&& echo "Ollama: $(OLLAMA_MODEL) déjà présent" \
		|| (echo "Ollama: pull $(OLLAMA_MODEL)..." && docker exec machine-ollama ollama pull $(OLLAMA_MODEL))

# Nettoie tout (containers + images), mais conserve le volume n8n_data
clean:
	$(COMPOSE) down --rmi local