FROM node:22-alpine AS builder
WORKDIR /app

# Copy backend package files (build context = repo root)
COPY apps/backend/package*.json ./
RUN npm install --production=false

# Copy backend source
COPY apps/backend/src ./src
COPY apps/backend/tsconfig.json ./

RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3001
CMD ["node", "dist/server.js"]
