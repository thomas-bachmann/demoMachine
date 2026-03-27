# ── Stage 1 : build (Vue + Vite) ─────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2 : serve (Caddy) ─────────────────────────────────
FROM caddy:alpine AS runner

# Copie du build
COPY --from=builder /app/dist /usr/share/nginx/html

# Copie la config Caddy
COPY Caddyfile /etc/caddy/Caddyfile

EXPOSE 80

# Caddy utilise déjà le bon CMD par défaut