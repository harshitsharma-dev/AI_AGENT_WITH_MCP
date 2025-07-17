# syntax=docker/dockerfile:1

# --- Build Stage ---
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files and install all dependencies
COPY package*.json ./
COPY tsconfig.json ./
RUN npm install

# Copy source code and build
COPY src/ ./src/
RUN npm run build

# --- Production Stage ---
FROM node:20-slim

# Create non-root user and install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appgroup \
    && useradd -r -g appgroup -d /app appuser

WORKDIR /app

# Install only production dependencies
COPY package*.json ./
RUN npm install --omit=dev --ignore-scripts && \
    chown -R appuser:appgroup /app

# Copy built files from builder stage
COPY --from=builder --chown=appuser:appgroup /app/build ./build

# Switch to non-root user
USER appuser

# Set production environment
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=4096" \
    HTTP_PORT=3000 \
    HTTP_HOST=0.0.0.0

# Expose the HTTP port
EXPOSE 3000

CMD ["node", "build/index.js"]