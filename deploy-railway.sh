#!/bin/bash
# =============================================================================
# CHATTY Railway Deployment Script
# Railway offers $5/month free credit (approximately 500 hours runtime)
# Good for testing and smaller deployments
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  CHATTY Railway Deployment${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}Railway CLI not found. Installing...${NC}"
    
    # Install Railway CLI
    npm install -g @railway/cli
    
    echo -e "${GREEN}Railway CLI installed.${NC}"
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}Please login to Railway:${NC}"
    railway login
fi

echo -e "${GREEN}✓ Railway CLI authenticated${NC}"

# Initialize project if needed
if [ ! -f .railway/config.json ]; then
    echo -e "${YELLOW}Initializing Railway project...${NC}"
    railway init --name "chatty-automation"
fi

# Create railway.json config
cat > railway.json <<'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python3 CHATTY_CONTINUOUS_MODE.py",
    "restartPolicyType": "ALWAYS",
    "restartPolicyMaxRetries": 10
  }
}
EOF

echo -e "${GREEN}✓ Railway config created${NC}"

# Create nixpacks.toml for build configuration
cat > nixpacks.toml <<'EOF'
[phases.build]
cmds = ["pip install -r requirements.txt"]

[phases.setup]
nixPkgs = ["python311", "gcc", "libffi", "openssl", "git", "ffmpeg"]

[start]
cmd = "python3 CHATTY_CONTINUOUS_MODE.py"
EOF

echo -e "${YELLOW}Setting environment variables...${NC}"

# Read .env file and set variables in Railway
if [ -f .env ]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        
        # Extract key and value
        key=$(echo "$line" | cut -d= -f1)
        value=$(echo "$line" | cut -d= -f2-)
        
        # Skip if key is empty
        [[ -z "$key" ]] && continue
        
        # Set in Railway
        echo -e "  Setting ${BLUE}$key${NC}"
        railway variables set "$key=$value" 2>/dev/null || true
    done < .env
fi

echo -e "${GREEN}✓ Environment variables set${NC}"

# Deploy
echo -e "${YELLOW}Deploying to Railway...${NC}"
railway up --detach

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  CHATTY Deployed to Railway!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# Get domain
DOMAIN=$(railway domain 2>/dev/null || echo "Not yet available")
echo -e "  Domain: ${YELLOW}$DOMAIN${NC}"
echo ""
echo -e "  View logs: ${BLUE}railway logs${NC}"
echo -e "  View status: ${BLUE}railway status${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} Railway free tier includes $5 credit/month (~500 hours)"
echo -e "For 24/7 operation, consider upgrading to Hobby plan ($5/month)"
echo ""
