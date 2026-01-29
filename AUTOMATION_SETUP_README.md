# 🚀 CHATTY - ONE-CLICK AUTOMATION

## Super Simple Setup - Just Press ENTER!

### Quick Start (Easiest Way)

```bash
cd /home/coden809/CHATTY
./AUTOMATE_EVERYTHING.sh
```

Then just **press ENTER** at each prompt! That's it! 🎉

---

## What Gets Automated

✅ **AI-Powered Content Generation**
- Automatic blog posts, social media content
- Grant proposals and investor pitches
- Marketing materials and press releases

✅ **Lead Acquisition & Conversion**
- Automatic lead finding and scoring
- AI-powered outreach and follow-up
- Conversion tracking and optimization

✅ **Grant Writing & Submission**
- Finds relevant grant opportunities
- Writes compelling proposals
- Tracks submissions and deadlines

✅ **Social Media Automation**
- Scheduled posting to Twitter/X
- Engagement tracking
- Viral content generation

✅ **Revenue Generation**
- 24/7 automated operations
- Multiple revenue streams
- Performance tracking

---

## Setup Process

The script will guide you through:

1. **System Check** (automatic)
   - Verifies Python and dependencies
   - Checks required files

2. **API Key Setup** (semi-automatic)
   - Opens signup pages in your browser
   - You paste the keys (takes ~5 minutes)
   - Keys needed:
     - xAI (Grok) - Free tier available
     - OpenRouter - $1 free credit
     - Cohere - Free tier available
     - Twitter/X - Free tier available

3. **Configuration Verification** (automatic)
   - Validates all settings
   - Ensures everything is ready

4. **Launch Automation** (automatic)
   - Starts all automation systems
   - Begins generating revenue

---

## Alternative Setup Methods

### Method 1: One-Click Setup (Recommended)
```bash
python3 ONE_CLICK_SETUP.py
```

### Method 2: API Keys Only
```bash
python3 auto_setup_api_keys.py
```

### Method 3: Manual Setup
1. Get API keys from:
   - xAI: https://console.x.ai/
   - OpenRouter: https://openrouter.ai/keys
   - Cohere: https://dashboard.cohere.com/api-keys
   - Twitter: https://developer.twitter.com/en/portal/dashboard

2. Add keys to `~/.config/chatty/secrets.env`

3. Launch automation:
```bash
python3 START_COMPLETE_AUTOMATION.py
```

---

## Monitoring Your Automation

### Dashboard
```bash
# Open in browser
http://localhost:5000
```

### Leads Dashboard
```bash
# View acquired leads
http://localhost:5000/leads
```

### Status Files
```bash
# Check earnings status
cat generated_content/earnings_status.md

# View action feed
cat generated_content/action_feed.md

# Check logs
tail -f logs/automation.log
```

---

## What Happens After Setup

The system runs **continuously in the background** and:

- ⏰ Generates content every hour
- 📊 Finds and converts leads daily
- 📝 Writes grant proposals automatically
- 🐦 Posts to social media on schedule
- 💰 Generates revenue 24/7

---

## Useful Commands

### Check if automation is running
```bash
ps aux | grep START_COMPLETE_AUTOMATION
```

### View recent activity
```bash
tail -f logs/automation.log
```

### Stop automation
```bash
pkill -f START_COMPLETE_AUTOMATION
```

### Restart automation
```bash
python3 START_COMPLETE_AUTOMATION.py
```

---

## Troubleshooting

### "No API keys configured"
Run the setup again:
```bash
python3 auto_setup_api_keys.py
```

### "Port already in use"
Stop existing processes:
```bash
pkill -f AUTOMATION_API_SERVER
python3 AUTOMATION_API_SERVER.py
```

### "Module not found"
Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Getting API Keys (Detailed)

### xAI (Grok) - Primary AI Brain
1. Visit: https://console.x.ai/
2. Sign in with X/Twitter
3. Click "API Keys"
4. Click "Create API Key"
5. Copy the key (starts with `xai-`)

**Free Tier:** Yes ✅

### OpenRouter - Fallback AI
1. Visit: https://openrouter.ai/keys
2. Sign in or create account
3. Click "Create Key"
4. Copy the key (starts with `sk-or-v1-`)

**Free Tier:** $1 free credit ✅

### Cohere - Secondary Fallback
1. Visit: https://dashboard.cohere.com/api-keys
2. Sign in or create account
3. Click "Create API Key"
4. Copy the key

**Free Tier:** Yes ✅

### Twitter/X - Social Media
1. Visit: https://developer.twitter.com/en/portal/dashboard
2. Sign in
3. Create a project/app
4. Go to "Keys and tokens"
5. Generate "Bearer Token"
6. Copy the token

**Free Tier:** Yes ✅

---

## Support

### Files Location
- **Project:** `/home/coden809/CHATTY`
- **Secrets:** `~/.config/chatty/secrets.env`
- **Generated Content:** `/home/coden809/CHATTY/generated_content`
- **Logs:** `/home/coden809/CHATTY/logs`

### Need Help?
Check the logs for detailed error messages:
```bash
tail -100 logs/automation.log
```

---

## Summary

**To get started:**
1. Run `./AUTOMATE_EVERYTHING.sh`
2. Press ENTER at each prompt
3. Paste API keys when asked (takes ~5 min)
4. Done! 🎉

Your automation will be running 24/7, generating content, finding leads, and making money automatically!
