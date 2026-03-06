# ── Stage 1 : build (Vue + Vite) ─────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2 : serve ──────────────────────────────────────────
FROM nginx:alpine AS runner

# Config nginx pour SPA (react-router friendly)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copie du build
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]