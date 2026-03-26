#!/bin/bash
# =============================================================================
# CHATTY Render Deployment Script
# Render offers free web services (sleeps after 15 mins inactivity)
# For 24/7 operation, use Background Worker ($7/month minimum)
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  CHATTY Render Deployment${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    echo -e "${YELLOW}Render CLI not found. Installing...${NC}"
    
    # Install Render CLI
    curl -fsSL https://raw.githubusercontent.com/render-oss/render-cli/main/install.sh | bash
    
    echo -e "${GREEN}Render CLI installed. Please restart your terminal and run again.${NC}"
    exit 0
fi

# Check if logged in
if ! render whoami &> /dev/null; then
    echo -e "${YELLOW}Please login to Render:${NC}"
    render login
fi

echo -e "${GREEN}✓ Render CLI authenticated${NC}"

# Create render.yaml for infrastructure as code
cat > render.yaml <<'EOF'
services:
  - type: worker
    name: chatty-continuous
    runtime: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: PYTHONUNBUFFERED
        value: "1"
      - key: CHATTY_REAL_DATA_MODE
        value: "true"
      - key: CHATTY_AUTO_INTEGRATE
        value: "true"
      - fromGroup: chatty-secrets
    disk:
      name: chatty-data
      mountPath: /app/data
      sizeGB: 5

  - type: web
    name: chatty-api
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerCommand: python3 -m uvicorn AUTOMATION_API_SERVER:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHONUNBUFFERED
        value: "1"
      - fromGroup: chatty-secrets
    healthCheckPath: /health

envVarGroups:
  - name: chatty-secrets
    envVars:
      - key: DATABASE_URL
        value: sqlite:///data/chatty.db
EOF

echo -e "${GREEN}✓ Render.yaml created${NC}"

# Create blueprint
echo -e "${YELLOW}Creating Render blueprint...${NC}"
render blueprint apply ./render.yaml

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  CHATTY Blueprint Created on Render!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo -e "  1. Go to https://dashboard.render.com/blueprints"
echo -e "  2. Connect your repository"
echo -e "  3. Add your environment variables to the 'chatty-secrets' group"
echo -e "  4. Deploy the services"
echo ""
echo -e "${YELLOW}Note on Free Tier:${NC}"
echo -e "  - Free web services sleep after 15 minutes of inactivity"
echo -e "  - For true 24/7 operation, use Background Worker ($7/month)"
echo ""
