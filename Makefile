ENV_FILE := .env
NGINX_TEMPLATE := deploy/nginx/demo-machine.conf.template
NGINX_SITE := /etc/nginx/sites-available/demo-machine

.PHONY: up down build restart logs frontend backend mcp n8n n8n-up stack-up stack-build nginx-apply check clean

COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; fi)

ifeq ($(strip $(COMPOSE)),)
$(error Neither 'docker compose' nor 'docker-compose' is available. Please install Docker Compose)
endif

# Cibles internes (stack brute)
stack-up:
	$(COMPOSE) up -d

stack-build:
	$(COMPOSE) up -d --build

# Lance toute la stack + n8n + applique nginx host + vérifications
up: stack-up n8n-up nginx-apply check

# Build + relance + applique nginx host + vérifications
build: stack-build n8n-up nginx-apply check

# Arrête tout
down:
	$(COMPOSE) down -v

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

# Déploie la conf nginx host depuis le template versionné
nginx-apply:
	@test -f $(ENV_FILE) || (echo "Missing $(ENV_FILE)" && exit 1)
	@test -f $(NGINX_TEMPLATE) || (echo "Missing $(NGINX_TEMPLATE)" && exit 1)
	@set -a; . ./$(ENV_FILE); set +a; \
	: "$$SERVER_IP"; \
	envsubst '$$SERVER_IP' < $(NGINX_TEMPLATE) | sudo tee $(NGINX_SITE) >/dev/null; \
	sudo nginx -t && sudo systemctl reload nginx

# Vérifs rapides locales serveur
check:
	@curl -fsS -I http://127.0.0.1:5678 >/dev/null && echo "OK n8n direct (127.0.0.1:5678)"
	@curl -fsS -I http://127.0.0.1/n8n/ >/dev/null && echo "OK nginx /n8n/"

# Nettoie tout (containers + images + volumes)
clean:
	$(COMPOSE) down --rmi local -v