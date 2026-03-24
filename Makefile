.PHONY: up down build restart logs frontend backend mcp clean

COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; fi)

ifeq ($(strip $(COMPOSE)),)
$(error Neither 'docker compose' nor 'docker-compose' is available. Please install Docker Compose)
endif

# Lance tout
up:
	$(COMPOSE) up -d

# Arrête tout
down:
	$(COMPOSE) down

# Build et lance
build:
	$(COMPOSE) up -d --build

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

# Nettoie tout (containers + images)
clean:
	$(COMPOSE) down --rmi local -v