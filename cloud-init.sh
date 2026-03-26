#!/bin/bash
# =============================================================================
# CHATTY Cloud-Init Script
# Run this on any fresh VPS/cloud instance to set up CHATTY automatically
# Works on: Ubuntu, Debian, CentOS, RHEL, Oracle Linux, Amazon Linux
# =============================================================================

set -e

LOG_FILE="/var/log/chatty-setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================="
echo "CHATTY Cloud-Init Setup"
echo "Started: $(date)"
echo "=========================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo "Cannot detect OS"
    exit 1
fi

echo "Detected OS: $OS $VERSION"

# Update system
echo "Updating system packages..."
if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    apt-get update && apt-get upgrade -y
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]] || [[ "$OS" == "ol" ]] || [[ "$OS" == "amzn" ]]; then
    yum update -y || dnf update -y
fi

# Install essential packages
echo "Installing essential packages..."
if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    apt-get install -y \
        git curl wget vim htop \
        python3 python3-pip python3-venv \
        build-essential libpq-dev \
        ffmpeg libsm6 libxext6 \
        software-properties-common
        
    # Add deadsnakes PPA for Python 3.11
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update
    apt-get install -y python3.11 python3.11-venv python3.11-dev
    
elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]] || [[ "$OS" == "ol" ]] || [[ "$OS" == "amzn" ]]; then
    yum install -y \
        git curl wget vim htop \
        python3 python3-pip \
        gcc gcc-c++ make \
        postgresql-devel \
        ffmpeg || true
fi

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    usermod -aG docker $(whoami) || true
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
fi

# Create CHATTY directory
mkdir -p /opt/chatty
cd /opt/chatty

# Create systemd service for CHATTY
cat > /etc/systemd/system/chatty.service << 'EOF'
[Unit]
Description=CHATTY Continuous Automation
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/chatty
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable service
systemctl daemon-reload
systemctl enable chatty.service

# Create swap if less than 4GB RAM
RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
if [ "$RAM_MB" -lt 4096 ]; then
    echo "Creating swap space..."
    SWAP_SIZE=$((4096 - RAM_MB))
    fallocate -l ${SWAP_SIZE}M /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=$SWAP_SIZE
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Setup firewall (if ufw or firewalld available)
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 8000/tcp
    ufw --force enable || true
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=22/tcp
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --reload || true
fi

# Create setup completion marker
touch /opt/chatty/.cloud-init-complete

echo ""
echo "=========================================="
echo "CHATTY Base Setup Complete!"
echo "Finished: $(date)"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Copy your CHATTY code to /opt/chatty"
echo "  2. Copy your .env file to /opt/chatty/.env"
echo "  3. Run: docker-compose up -d"
echo "  4. Or use: systemctl start chatty"
echo ""
echo "To check status: docker-compose ps"
echo "To view logs: docker-compose logs -f"
