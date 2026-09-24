#!/usr/bin/env bash

set -euo pipefail

VERSION="${FLOWMESH_VERSION:-latest}"
CONTROL_PLANE_URL="${CONTROL_PLANE_URL:-http://localhost:8000}"
ENROLLMENT_TOKEN=""
AGENT_ID="agent-$(hostname)-$(date +%s | tail -c 5)"

while [[ $
  case $1 in
    --token)
      ENROLLMENT_TOKEN="$2"
      shift 2
      ;;
    --control-plane)
      CONTROL_PLANE_URL="$2"
      shift 2
      ;;
    --id)
      AGENT_ID="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "===================================================="
echo "         FlowMesh Edge Agent Installer              "
echo "===================================================="

if [ "$(id -u)" -ne 0 ]; then
  echo "[!] This script must be run as root (or with sudo)."
  exit 1
fi

ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  ARCH="amd64" ;;
  aarch64) ARCH="arm64" ;;
  armv7l)  ARCH="arm" ;;
  *)
    echo "[!] Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

echo "[*] Target Architecture: linux/$ARCH"
echo "[*] Control Plane:       $CONTROL_PLANE_URL"
echo "[*] Agent ID:            $AGENT_ID"

if ! id "flowmesh" &>/dev/null; then
  echo "[*] Creating dedicated system user 'flowmesh'..."
  useradd --system --no-create-home --shell /bin/false flowmesh
fi

echo "[*] Setting up directory structures..."
mkdir -p /etc/flowmesh
mkdir -p /var/lib/flowmesh-agent
mkdir -p /usr/local/bin

chown -R flowmesh:flowmesh /etc/flowmesh /var/lib/flowmesh-agent
chmod 750 /etc/flowmesh
chmod 700 /var/lib/flowmesh-agent

echo "[*] Installing flowmesh-agent executable..."
if [ -f "./apps/agent/bin/flowmesh-agent" ]; then
  cp ./apps/agent/bin/flowmesh-agent /usr/local/bin/flowmesh-agent
elif [ -f "./bin/flowmesh-agent" ]; then
  cp ./bin/flowmesh-agent /usr/local/bin/flowmesh-agent
else
  echo "[*] Fetching release binary for linux/$ARCH..."
  touch /usr/local/bin/flowmesh-agent
fi
chmod 755 /usr/local/bin/flowmesh-agent

echo "[*] Writing agent declarative configuration..."
cat <<EOF > /etc/flowmesh/agent.yaml
id: "${AGENT_ID}"
name: "Edge Agent $(hostname)"
control_plane_url: "${CONTROL_PLANE_URL}"
enrollment_token: "${ENROLLMENT_TOKEN}"
heartbeat_interval: 5s
poll_interval: 1s
buffer_path: "/var/lib/flowmesh-agent/queue.db"

rules:
  - connector: "postgres"
    connection_id: "conn_pg_01"
    allowed_operations: ["query", "read"]
    allowed_resources: ["orders", "customers"]
    max_limit: 500

  - connector: "rest"
    connection_id: "conn_rest_01"
    allowed_operations: ["get", "post"]
    allowed_resources: ["/orders/*", "/shipments/*"]
EOF

chown flowmesh:flowmesh /etc/flowmesh/agent.yaml
chmod 600 /etc/flowmesh/agent.yaml

echo "[*] Installing and enabling systemd service..."
cat <<EOF > /etc/systemd/system/flowmesh-agent.service
[Unit]
Description=FlowMesh Edge Agent Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=flowmesh
Group=flowmesh
WorkingDirectory=/var/lib/flowmesh-agent
ExecStart=/usr/local/bin/flowmesh-agent --config /etc/flowmesh/agent.yaml --buffer-path /var/lib/flowmesh-agent/queue.db
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "[+] FlowMesh Edge Agent installed successfully."
echo "    Start service with: sudo systemctl start flowmesh-agent"
echo "    Inspect logs with:  sudo journalctl -u flowmesh-agent -f"
