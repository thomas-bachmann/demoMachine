.PHONY: up down build restart logs frontend backend mcp clean

# Lance tout
up:
	docker compose up -d

# Arrête tout
down:
	docker compose down

# Build et lance
build:
	docker compose up -d --build

# Redémarre tout
restart: down up

# Logs en temps réel
logs:
	docker compose logs -f

# Services individuels
frontend:
	docker compose up frontend -d --build

backend:
	docker compose up backend -d --build

mcp:
	docker compose up mcp -d --build

# Nettoie tout (containers + images)
clean:
	docker compose down --rmi local -v