#!/bin/bash
# Add NVIDIA API Key to your secrets file

SECRETS_FILE="/home/coden809/.config/chatty/secrets.env"

echo "=========================================="
echo "Add NVIDIA API Key to CHATTY"
echo "=========================================="
echo ""
echo "Your secrets file: $SECRETS_FILE"
echo ""

# Check if key already exists
current_key=$(grep "^NVIDIA_API_KEY=" "$SECRETS_FILE" | cut -d'=' -f2)

if [ -n "$current_key" ] && [ "$current_key" != "nvapi-YOUR-KEY-HERE" ]; then
    echo "Current key found: ${current_key:0:20}..."
    read -p "Do you want to replace it? (y/n): " replace
    if [ "$replace" != "y" ]; then
        echo "Keeping existing key."
        exit 0
    fi
fi

echo ""
echo "Get your free API key at:"
echo "  https://build.nvidia.com/moonshotai/kimi-k2.5"
echo ""
read -p "Paste your NVIDIA API Key (starts with 'nvapi-'): " api_key

if [ -z "$api_key" ]; then
    echo "❌ No key entered. Exiting."
    exit 1
fi

# Update the secrets file
sed -i "s/^NVIDIA_API_KEY=.*/NVIDIA_API_KEY=$api_key/" "$SECRETS_FILE"

echo ""
echo "✅ NVIDIA_API_KEY updated in $SECRETS_FILE"
echo ""

# Export for current session
export NVIDIA_API_KEY="$api_key"
echo "✅ Key exported for current session"

# Test the key
echo ""
echo "🔄 Testing API connection..."
cd /home/coden809/Projects/chatty
source .venv/bin/activate

python3 -c "
import os
import asyncio
import aiohttp

async def test():
    api_key = os.getenv('NVIDIA_API_KEY')
    if not api_key or api_key == 'nvapi-YOUR-KEY-HERE':
        print('❌ API key not set correctly')
        return
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'https://integrate.api.nvidia.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'moonshotai/kimi-k2.5',
                    'messages': [{'role': 'user', 'content': 'Say hello'}],
                    'max_tokens': 20
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data['choices'][0]['message']['content']
                    print(f'✅ API connected successfully!')
                    print(f'   Model: {data[\"model\"]}')
                    print(f'   Response: {content[:50]}...')
                else:
                    text = await resp.text()
                    print(f'❌ API error: {resp.status}')
                    print(f'   {text[:200]}')
        except Exception as e:
            print(f'❌ Error: {e}')

asyncio.run(test())
"

echo ""
echo "=========================================="
echo "Done! You can now run:"
echo "  python3 test_nvidia_real.py"
echo "=========================================="
