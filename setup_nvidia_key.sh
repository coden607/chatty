#!/bin/bash
# Setup script for NVIDIA API Key

echo "=========================================="
echo "NVIDIA API Key Setup for CHATTY"
echo "=========================================="
echo ""

# Check if NVIDIA_API_KEY is already set
if [ -n "$NVIDIA_API_KEY" ]; then
    echo "✅ NVIDIA_API_KEY is already set in environment"
    echo "   Key prefix: ${NVIDIA_API_KEY:0:20}..."
    echo ""
fi

# Get the API key from user
read -p "Enter your NVIDIA API Key (starts with 'nvapi-'): " api_key

if [ -z "$api_key" ]; then
    echo "❌ No API key entered. Exiting."
    exit 1
fi

# Validate key format
if [[ ! "$api_key" =~ ^nvapi- ]]; then
    echo "⚠️  Warning: NVIDIA API keys typically start with 'nvapi-'"
    read -p "Continue anyway? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        exit 1
    fi
fi

# Add to .env file
ENV_FILE="/home/coden809/Projects/chatty/.env"

# Remove old NVIDIA_API_KEY if exists
sed -i '/^NVIDIA_API_KEY=/d' "$ENV_FILE"

# Add new key
echo "" >> "$ENV_FILE"
echo "# NVIDIA Build API Key for Kimi K2.5" >> "$ENV_FILE"
echo "NVIDIA_API_KEY=$api_key" >> "$ENV_FILE"

echo ""
echo "✅ API Key added to $ENV_FILE"

# Export for current session
export NVIDIA_API_KEY="$api_key"
echo "✅ API Key exported for current session"

# Add to .bashrc for persistence
BASHRC="/home/coden809/.bashrc"
if ! grep -q "NVIDIA_API_KEY=" "$BASHRC"; then
    echo "" >> "$BASHRC"
    echo "# NVIDIA Build API Key" >> "$BASHRC"
    echo "export NVIDIA_API_KEY='$api_key'" >> "$BASHRC"
    echo "✅ API Key added to $BASHRC for persistence"
else
    # Update existing key
    sed -i "/^export NVIDIA_API_KEY=/c\export NVIDIA_API_KEY='$api_key'" "$BASHRC"
    echo "✅ API Key updated in $BASHRC"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "You can now run:"
echo "  python3 test_nvidia_real.py"
echo ""
echo "To get your free API key:"
echo "  https://build.nvidia.com/moonshotai/kimi-k2.5"
echo ""

# Test the key
echo "🔄 Testing API connection..."
python3 -c "
import os
import asyncio
import aiohttp

async def test():
    api_key = os.getenv('NVIDIA_API_KEY')
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://integrate.api.nvidia.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': 'moonshotai/kimi-k2.5', 'messages': [{'role': 'user', 'content': 'Hello'}], 'max_tokens': 10}
        ) as resp:
            if resp.status == 200:
                print('✅ API connection successful!')
            else:
                print(f'❌ API error: {resp.status}')
                data = await resp.text()
                print(f'   {data[:200]}')

asyncio.run(test())
" 2>&1
