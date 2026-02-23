#!/bin/bash
set -euo pipefail

# ============================================================
# Interview Pilot — EC2 Backend Deployment Script
# Target: Amazon Linux 2023
# Usage: sudo bash setup.sh
# Frontend is deployed separately on Vercel.
# ============================================================

APP_DIR="/opt/interview-pilot"
DEPLOY_DIR="$APP_DIR/deploy"

echo "=========================================="
echo "  Interview Pilot — Backend Setup"
echo "=========================================="

# ── 1. System packages ──
echo "[1/6] Installing system packages..."
dnf update -y -q
dnf install -y -q git nginx python3.12 python3.12-pip

# ── 2. Install uv (Python package manager) ──
echo "[2/6] Installing uv..."
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    cp "$HOME/.local/bin/uv" /usr/local/bin/uv 2>/dev/null || true
fi

# ── 3. Clone or update repo ──
echo "[3/6] Setting up repository..."
if [ -d "$APP_DIR/.git" ]; then
    echo "  Repository exists, pulling latest..."
    cd "$APP_DIR" && git pull origin main
else
    echo "  Cloning repository..."
    git clone https://github.com/sleepy-wook/interview-pilot.git "$APP_DIR"
fi

# ── 4. Backend setup ──
echo "[4/6] Setting up backend..."
cd "$APP_DIR/backend"
uv sync
mkdir -p uploads

if [ ! -f .env ]; then
    cp "$APP_DIR/.env.example" .env
    echo ""
    echo "  *** IMPORTANT: Edit backend/.env with production values! ***"
    echo "    nano $APP_DIR/backend/.env"
    echo ""
fi

# ── 5. Nginx config ──
echo "[5/6] Configuring nginx..."
cp "$DEPLOY_DIR/nginx.conf" /etc/nginx/conf.d/interview-pilot.conf

if [ -f /etc/nginx/conf.d/default.conf ]; then
    mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak
fi

nginx -t

# ── 6. Systemd service ──
echo "[6/6] Setting up systemd service..."
cp "$DEPLOY_DIR/interview-backend.service" /etc/systemd/system/
systemctl daemon-reload

chown -R ec2-user:ec2-user "$APP_DIR"

systemctl enable --now nginx
systemctl enable --now interview-backend

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "<your-ip>")

sleep 3
echo ""
echo "=========================================="
echo "  Backend Deployment Complete!"
echo "=========================================="
echo ""
echo "  API: http://$PUBLIC_IP/api/"
echo "  Health: http://$PUBLIC_IP/health"
echo ""
echo "  Service status:"
systemctl is-active --quiet nginx && echo "    nginx:   running" || echo "    nginx:   FAILED"
systemctl is-active --quiet interview-backend && echo "    backend: running" || echo "    backend: FAILED"
echo ""
echo "  Next steps:"
echo "    1. Edit backend/.env with production DATABASE_URL etc."
echo "    2. sudo systemctl restart interview-backend"
echo "    3. Deploy frontend on Vercel with:"
echo "       NEXT_PUBLIC_API_URL=http://$PUBLIC_IP"
echo ""
echo "  Useful commands:"
echo "    sudo journalctl -u interview-backend -f   # View logs"
echo "    sudo systemctl restart interview-backend   # Restart"
echo "=========================================="
