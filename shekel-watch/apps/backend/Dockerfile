# ── Stage 1: TypeScript build ─────────────────────────────────────────────────
FROM node:22-bookworm-slim AS builder
WORKDIR /app

COPY apps/backend/package*.json ./
RUN npm install --production=false

COPY apps/backend/src ./src
COPY apps/backend/tsconfig.json ./
RUN npm run build

# ── Stage 2: Production runner (Node + Python) ────────────────────────────────
FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

# Install Python 3, pip, venv, and supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy Node.js build artifacts
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Create Python venv and install dependencies
COPY apps/python/requirements.txt ./python-requirements.txt
RUN python3 -m venv /app/venv \
    && /app/venv/bin/pip install --no-cache-dir -r python-requirements.txt

# Copy the Python (Streamlit) app
COPY apps/python ./python

# Copy supervisord config
COPY apps/backend/supervisord.conf /etc/supervisord.conf

EXPOSE ${PORT:-3001}
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
