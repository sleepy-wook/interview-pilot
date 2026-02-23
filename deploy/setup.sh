#!/bin/bash
set -euo pipefail

# ============================================================
# Interview Pilot — EC2 Deployment Script
# Target: Amazon Linux 2023
# Usage: sudo bash setup.sh
# ============================================================

APP_DIR="/opt/interview-pilot"
DEPLOY_DIR="$APP_DIR/deploy"

echo "=========================================="
echo "  Interview Pilot — EC2 Setup"
echo "=========================================="

# ── 1. System packages ──
echo "[1/8] Installing system packages..."
dnf update -y -q
dnf install -y -q git nginx python3.12 python3.12-pip nodejs npm

# ── 2. Install uv (Python package manager) ──
echo "[2/8] Installing uv..."
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    # Also make it available for ec2-user
    cp "$HOME/.local/bin/uv" /usr/local/bin/uv 2>/dev/null || true
fi

# ── 3. Clone or update repo ──
echo "[3/8] Setting up repository..."
if [ -d "$APP_DIR/.git" ]; then
    echo "  Repository exists, pulling latest..."
    cd "$APP_DIR" && git pull origin main
else
    echo "  Cloning repository..."
    git clone https://github.com/sleepy-wook/interview-pilot.git "$APP_DIR"
fi

# ── 4. Backend setup ──
echo "[4/8] Setting up backend..."
cd "$APP_DIR/backend"
uv sync
mkdir -p uploads

if [ ! -f .env ]; then
    echo ""
    echo "  *** IMPORTANT: Create backend/.env before starting! ***"
    echo "  Copy from .env.example and fill in production values:"
    echo "    cp $APP_DIR/.env.example $APP_DIR/backend/.env"
    echo "    nano $APP_DIR/backend/.env"
    echo ""
fi

# ── 5. Frontend setup ──
echo "[5/8] Setting up frontend..."
cd "$APP_DIR/frontend"
npm install --production=false

# Get public IP for API URL
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
echo "  Detected public IP: $PUBLIC_IP"

# Build with production API URL
NEXT_PUBLIC_API_URL="http://$PUBLIC_IP" npm run build

# Save env for frontend service
echo "NEXT_PUBLIC_API_URL=http://$PUBLIC_IP" > .env.local

# ── 6. Nginx config ──
echo "[6/8] Configuring nginx..."
cp "$DEPLOY_DIR/nginx.conf" /etc/nginx/conf.d/interview-pilot.conf

# Remove default server block if it conflicts
if [ -f /etc/nginx/conf.d/default.conf ]; then
    mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak
fi

nginx -t

# ── 7. Systemd services ──
echo "[7/8] Setting up systemd services..."
cp "$DEPLOY_DIR/interview-backend.service" /etc/systemd/system/
cp "$DEPLOY_DIR/interview-frontend.service" /etc/systemd/system/
systemctl daemon-reload

# ── 8. Set ownership and start ──
echo "[8/8] Starting services..."
chown -R ec2-user:ec2-user "$APP_DIR"

systemctl enable --now nginx
systemctl enable --now interview-backend
systemctl enable --now interview-frontend

# Wait and check
sleep 3
echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "  URL: http://$PUBLIC_IP"
echo ""
echo "  Service status:"
systemctl is-active --quiet nginx && echo "    nginx:    running" || echo "    nginx:    FAILED"
systemctl is-active --quiet interview-backend && echo "    backend:  running" || echo "    backend:  FAILED"
systemctl is-active --quiet interview-frontend && echo "    frontend: running" || echo "    frontend: FAILED"
echo ""
echo "  Useful commands:"
echo "    sudo journalctl -u interview-backend -f   # Backend logs"
echo "    sudo journalctl -u interview-frontend -f  # Frontend logs"
echo "    sudo systemctl restart interview-backend   # Restart backend"
echo "    sudo systemctl restart interview-frontend  # Restart frontend"
echo ""
echo "  Don't forget to configure backend/.env!"
echo "=========================================="
