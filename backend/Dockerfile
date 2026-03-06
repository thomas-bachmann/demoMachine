# ── Stage 1 : dépendances ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Installer les dépendances dans un venv isolé
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2 : runtime ────────────────────────────────────────
FROM python:3.12-slim AS runner

WORKDIR /app

# Récupérer le venv du stage précédent
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]