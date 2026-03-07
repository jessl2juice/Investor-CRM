# ============================================================
# BetterMind CRM - Multi-stage Dockerfile
# Stage 1: Build React frontend with Vite
# Stage 2: Run FastAPI backend serving API + static frontend
# ============================================================

# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Backend ---
FROM python:3.12-slim
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from Stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Copy docs for in-app help
COPY docs/ ./docs/

# Cloud Run sets PORT env var
ENV PORT=8080

EXPOSE 8080

CMD ["python", "backend/main.py"]
