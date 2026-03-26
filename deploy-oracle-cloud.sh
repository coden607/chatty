#!/bin/bash
# =============================================================================
# CHATTY Oracle Cloud Free Tier Deployment Script
# Oracle Cloud offers ALWAYS FREE tier with:
# - 2 AMD-based Compute VMs (1/8 OCPU, 1 GB RAM each)
# - 4 ARM-based Ampere A1 VMs (up to 4 OCPUs, 24 GB RAM total)
# - 10 TB/month data transfer
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  CHATTY Oracle Cloud Free Tier Deployment${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Configuration
VM_SHAPE="VM.Standard.A1.Flex"  # ARM-based (always free)
VM_OCPUS=2
VM_MEMORY=12  # GB
VM_NAME="chatty-automation-server"
SSH_KEY_PATH="$HOME/.ssh/oracle_chatty_key"

# Check if OCI CLI is installed
if ! command -v oci &> /dev/null; then
    echo -e "${YELLOW}OCI CLI not found. Installing...${NC}"
    
    # Install OCI CLI
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults
    
    echo -e "${GREEN}OCI CLI installed. Please configure it with:${NC}"
    echo -e "  oci setup config"
    echo -e "Then run this script again."
    exit 0
fi

# Check OCI configuration
if ! oci os ns get &> /dev/null; then
    echo -e "${RED}OCI CLI not configured.${NC}"
    echo -e "${YELLOW}Please run: oci setup config${NC}"
    exit 1
fi

echo -e "${GREEN}✓ OCI CLI configured${NC}"

# Get compartment ID
COMPARTMENT_ID=$(oci iam compartment list --query "data[?name=='root'].id | [0]" --raw-output)
if [ -z "$COMPARTMENT_ID" ]; then
    COMPARTMENT_ID=$(oci iam compartment list --all --query "data[0].id" --raw-output)
fi

echo -e "${BLUE}Using compartment: $COMPARTMENT_ID${NC}"

# Get availability domain
AD=$(oci iam availability-domain list --query "data[0].name" --raw-output)
echo -e "${BLUE}Using availability domain: $AD${NC}"

# Get latest Oracle Linux image
echo -e "${YELLOW}Getting latest Oracle Linux image...${NC}"
IMAGE_ID=$(oci compute image list --compartment-id "$COMPARTMENT_ID" --operating-system "Oracle Linux" --shape "$VM_SHAPE" --sort-by TIMECREATED --sort-order DESC --query "data[?contains('display-name', 'aarch64')].id | [0]" --raw-output)

if [ -z "$IMAGE_ID" ] || [ "$IMAGE_ID" = "null" ]; then
    echo -e "${RED}No ARM-compatible image found. Trying x86...${NC}"
    VM_SHAPE="VM.Standard.E2.1.Micro"
    VM_OCPUS=1
    VM_MEMORY=1
    IMAGE_ID=$(oci compute image list --compartment-id "$COMPARTMENT_ID" --operating-system "Oracle Linux" --shape "$VM_SHAPE" --sort-by TIMECREATED --sort-order DESC --query "data[0].id" --raw-output)
fi

echo -e "${GREEN}✓ Using image: $IMAGE_ID${NC}"
echo -e "${GREEN}✓ VM Shape: $VM_SHAPE${NC}"

# Generate SSH key if doesn't exist
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}Generating SSH key pair...${NC}"
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "chatty-oracle"
    echo -e "${GREEN}✓ SSH key generated at $SSH_KEY_PATH${NC}"
fi

SSH_PUBLIC_KEY=$(cat "${SSH_KEY_PATH}.pub")

# Create cloud-init script
CLOUD_INIT=$(cat <<'EOF'
#!/bin/bash
# CHATTY Cloud Init Script

echo "Starting CHATTY setup..."

# Update system
yum update -y

# Install Docker
dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io
dnf install -y docker-compose-plugin || pip3 install docker-compose

# Start Docker
systemctl start docker
systemctl enable docker
usermod -aG docker opc

# Install additional tools
yum install -y git curl wget htop nano vim

# Install Python 3.11
yum install -y python3.11 python3.11-pip

# Create app directory
mkdir -p /opt/chatty
cd /opt/chatty

# Clone repository (user will need to customize this)
echo "CHATTY base setup complete."
echo "Please copy your .env file and docker-compose.yml to /opt/chatty"
echo "Then run: docker compose up -d"

EOF
)

# Encode cloud-init
CLOUD_INIT_BASE64=$(echo "$CLOUD_INIT" | base64 -w 0)

# Create VM
echo -e "${YELLOW}Creating VM instance...${NC}"
VM_JSON=$(oci compute instance launch \
    --compartment-id "$COMPARTMENT_ID" \
    --availability-domain "$AD" \
    --display-name "$VM_NAME" \
    --shape "$VM_SHAPE" \
    --shape-config "{\"ocpus\": $VM_OCPUS, \"memory_in_gbs\": $VM_MEMORY}" \
    --image-id "$IMAGE_ID" \
    --ssh-authorized-keys-file "${SSH_KEY_PATH}.pub" \
    --user-data-file <(echo "$CLOUD_INIT") \
    --assign-public-ip true \
    --wait-for-state RUNNING \
    --query "data.{id: id, name: \"display-name\"}" 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create VM:${NC}"
    echo "$VM_JSON"
    exit 1
fi

INSTANCE_ID=$(echo "$VM_JSON" | grep -o '"id": "[^"]*"' | cut -d'"' -f4)
echo -e "${GREEN}✓ VM created: $INSTANCE_ID${NC}"

# Get public IP
echo -e "${YELLOW}Getting public IP...${NC}"
sleep 10

VNIC_ID=$(oci compute instance list-vnics --instance-id "$INSTANCE_ID" --query "data[0].id" --raw-output)
PUBLIC_IP=$(oci network vnic get --vnic-id "$VNIC_ID" --query "data.\"public-ip\"" --raw-output)

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  CHATTY Server Deployed Successfully!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  Public IP: ${YELLOW}$PUBLIC_IP${NC}"
echo -e "  SSH Key: ${YELLOW}$SSH_KEY_PATH${NC}"
echo ""
echo -e "  Connect with:"
echo -e "    ${BLUE}ssh -i $SSH_KEY_PATH opc@$PUBLIC_IP${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. SSH into the server"
echo -e "  2. Clone your CHATTY repository:"
echo -e "     git clone <your-repo-url> /opt/chatty"
echo -e "  3. Copy your .env file to /opt/chatty/.env"
echo -e "  4. Start CHATTY:"
echo -e "     cd /opt/chatty && docker compose up -d"
echo ""
echo -e "${GREEN}============================================================${NC}"

# Save deployment info
mkdir -p ~/.chatty
cat > ~/.chatty/oracle_deployment.json <<EOF
{
  "instance_id": "$INSTANCE_ID",
  "public_ip": "$PUBLIC_IP",
  "vm_shape": "$VM_SHAPE",
  "ssh_key": "$SSH_KEY_PATH",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo -e "Deployment info saved to: ${BLUE}~/.chatty/oracle_deployment.json${NC}"
