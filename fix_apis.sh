#!/bin/bash
# Fix API issues for CHATTY system

echo "🔧 CHATTY API Fix Script"
echo "========================"

# Check SendGrid API key
echo ""
echo "1. Testing SendGrid API..."
SENDGRID_KEY=$(grep SENDGRID_API_KEY .env | head -1 | cut -d= -f2)
if [ -n "$SENDGRID_KEY" ]; then
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
        https://api.sendgrid.com/v3/user/profile \
        -H "Authorization: Bearer $SENDGRID_KEY" 2>/dev/null)
    if [ "$RESPONSE" = "200" ]; then
        echo "   ✅ SendGrid API key is VALID"
    else
        echo "   ❌ SendGrid API key returned HTTP $RESPONSE"
        echo "   💡 Get a new key at: https://app.sendgrid.com/settings/api_keys"
    fi
else
    echo "   ❌ No SendGrid API key found in .env"
fi

# Check Model Router
echo ""
echo "2. Testing Model Router..."
python3 -c "
from CHATTY_MODEL_ROUTER import router
result = router.health_check()
active = sum(1 for p in result['providers'].values() if p['available'])
print(f'   ✅ {active}/8 AI providers available')
for name, status in result['providers'].items():
    if status['available'] and status.get('api_keys_configured'):
        print(f'      ✅ {name}')
" 2>/dev/null

# Check for missing keys
echo ""
echo "3. Missing API Keys (for full functionality):"
for key in STRIPE_SECRET_KEY X_BEARER_TOKEN ANTHROPIC_API_KEY GOOGLE_API_KEY; do
    if ! grep -q "^$key=" .env 2>/dev/null || grep -q "^$key=$" .env 2>/dev/null; then
        echo "   ❌ $key"
    fi
done

echo ""
echo "========================"
echo "📊 Current System Status:"
echo "========================"

# Count leads
if [ -f leads.json ]; then
    LEADS=$(python3 -c "import json; print(len(json.load(open('leads.json'))))" 2>/dev/null || echo "0")
    echo "   Leads discovered: $LEADS"
fi

# Count actions
if [ -f generated_content/action_history.jsonl ]; then
    ACTIONS=$(wc -l < generated_content/action_history.jsonl)
    echo "   Actions logged: $ACTIONS"
fi

# Check processes
echo "   Running processes:"
ps aux | grep -E "START_COMPLETE|AUTOMATION_API" | grep -v grep | grep python3 | awk '{print "      PID " $2}'

echo ""
echo "✅ Fix script complete!"
echo "📖 Full status: SYSTEM_STATUS.md"
