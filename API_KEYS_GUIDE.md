# CHATTY API Keys Configuration Guide

## 🎯 Quick Start - Run Interactive Setup

```bash
python3 API_KEY_PROMPT.py
```

This will guide you through entering all API keys interactively.

---

## 📋 Required API Keys

### 🔴 CRITICAL (Blocks Revenue)

| Key | Purpose | Where to Get |
|-----|---------|--------------|
| `STRIPE_SECRET_KEY` | Payment processing | https://dashboard.stripe.com/apikeys |
| `STRIPE_PUBLISHABLE_KEY` | Frontend payments | https://dashboard.stripe.com/apikeys |

**How to get:**
1. Sign up at https://stripe.com
2. Go to Developers → API Keys
3. Copy Publishable key (starts with `pk_live_`)
4. Reveal and copy Secret key (starts with `sk_live_`)

---

### 🟡 HIGH PRIORITY (AI Failover)

| Key | Purpose | Where to Get |
|-----|---------|--------------|
| `ANTHROPIC_API_KEY` | Claude 3.5 Sonnet/Opus | https://console.anthropic.com |
| `GOOGLE_API_KEY` | Gemini Pro/Flash | https://makersuite.google.com/app/apikey |

**Already Configured:**
- ✅ `XAI_API_KEY` - Grok-3 (xAI)
- ✅ `OPENAI_API_KEY` - GPT-4 (OpenAI)
- ✅ `NVIDIA_API_KEY` - Kimi K2.5 (NVIDIA)
- ✅ `SENDGRID_API_KEY` - Email (SendGrid)
- ✅ `HUGGINGFACE_TOKEN` - Models (HuggingFace)

---

### 🟢 MEDIUM PRIORITY (Enhanced Features)

#### MCP Tools

| Key | Purpose | Where to Get |
|-----|---------|--------------|
| `BRAVE_API_KEY` | Web search MCP | https://api.search.brave.com/app/keys |
| `GITHUB_TOKEN` | Git operations | https://github.com/settings/tokens |

#### Social Media Automation

| Key | Purpose | Where to Get |
|-----|---------|--------------|
| `X_BEARER_TOKEN` | Twitter/X API | https://developer.twitter.com/en/portal/dashboard |
| `X_CONSUMER_KEY` | Twitter/X App | Same as above |
| `X_CONSUMER_SECRET` | Twitter/X App | Same as above |
| `X_ACCESS_TOKEN` | Twitter/X User | Same as above |
| `X_ACCESS_SECRET` | Twitter/X User | Same as above |
| `LINKEDIN_CLIENT_ID` | LinkedIn API | https://www.linkedin.com/developers/apps |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn API | Same as above |

#### Communication

| Key | Purpose | Where to Get |
|-----|---------|--------------|
| `TWILIO_ACCOUNT_SID` | SMS | https://console.twilio.com |
| `TWILIO_AUTH_TOKEN` | SMS | Same as above |

#### Search & Research

| Key | Purpose | Where to Get |
|-----|---------|--------------|
| `SERP_API_KEY` | Google Search API | https://serpapi.com |
| `TAVILY_API_KEY` | AI Search | https://tavily.com |

---

## 📝 Manual Configuration

### Option 1: Edit .env File Directly

```bash
# Open .env file
nano /home/coden809/Projects/chatty/.env
```

Add your keys:
```bash
# Payment Processing (CRITICAL)
STRIPE_SECRET_KEY=sk_live_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_live_your_key_here

# AI Providers (HIGH PRIORITY)
ANTHROPIC_API_KEY=sk-ant-your_key_here
GOOGLE_API_KEY=AIza-your_key_here

# MCP Tools (MEDIUM PRIORITY)
BRAVE_API_KEY=BSA-your_key_here
GITHUB_TOKEN=ghp_your_token_here

# Social Media (MEDIUM PRIORITY)
X_BEARER_TOKEN=AAAA...
X_CONSUMER_KEY=your_key_here
X_CONSUMER_SECRET=your_secret_here
X_ACCESS_TOKEN=your_token_here
X_ACCESS_SECRET=your_secret_here

# Communication (MEDIUM PRIORITY)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=your_token_here

# Search (MEDIUM PRIORITY)
SERP_API_KEY=your_key_here
TAVILY_API_KEY=tvly-your_key_here
```

### Option 2: Set Environment Variables

```bash
export STRIPE_SECRET_KEY="sk_live_..."
export ANTHROPIC_API_KEY="sk-ant-..."
# etc.
```

---

## 🔗 Getting Each API Key

### Stripe (Payment Processing)
1. Go to https://dashboard.stripe.com/register
2. Complete verification
3. Developers → API Keys
4. Copy keys

### Anthropic (Claude AI)
1. Go to https://console.anthropic.com
2. Sign up with Google account
3. Billing → Add credits ($5 minimum)
4. API Keys → Create Key

### Google AI (Gemini)
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy key (starts with `AIza`)

### Brave Search (MCP Tool)
1. Go to https://api.search.brave.com/app/keys
2. Create free account
3. Generate API key
4. Copy key (starts with `BSA`)

### GitHub Token (MCP Git)
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:user`
4. Generate and copy

### Twitter/X API
1. Go to https://developer.twitter.com/en/apply-for-access
2. Apply for Elevated access (free)
3. Create app
4. Keys and Tokens → Generate all

### SendGrid (Already Configured)
- Your SendGrid key is: `SG.5SMFFuGgTuuhJdWRKfP5vg...`
- Status: ✅ Valid and working

### NVIDIA Build (Already Configured)
- Your key is: `nvapi-heNDJHT9v_E_VG9pg24N4IYcGYB8ObvP...`
- Status: ✅ Valid and working

---

## ✅ Verify Configuration

After adding keys, verify with:

```bash
# Test all integrations
cd /home/coden809/Projects/chatty
python3 check_automation_status.py

# Test specific integration
python3 MCP_INTEGRATION.py
python3 A2A_PROTOCOL.py
```

---

## 🎓 Priority Recommendations

### Phase 1: Essential (Do First)
- [ ] Stripe keys (for revenue)
- [ ] Anthropic key (AI failover)

### Phase 2: Enhanced (Do Next)
- [ ] Google API key (another AI option)
- [ ] Brave API key (web search MCP)
- [ ] GitHub token (git operations)

### Phase 3: Full Power (When Ready)
- [ ] Twitter/X keys (social automation)
- [ ] LinkedIn keys (B2B outreach)
- [ ] Twilio keys (SMS)
- [ ] SerpAPI/Tavily (enhanced search)

---

## 🔒 Security Notes

1. **Never commit API keys to git**
   - Keys are in `.env` (already in `.gitignore`)
   
2. **Use environment-specific keys**
   - Development: Use test/sandbox keys
   - Production: Use live keys

3. **Rotate keys regularly**
   - Set calendar reminders monthly
   
4. **Monitor usage**
   - Check dashboards for unexpected usage
   - Set up spending alerts

---

## 📊 Current Status

| Service | Status | Action |
|---------|--------|--------|
| Stripe | ❌ Missing | **ADD FIRST** |
| Anthropic Claude | ❌ Missing | **ADD SECOND** |
| xAI Grok | ✅ Working | None needed |
| OpenAI | ✅ Working | None needed |
| NVIDIA Kimi | ✅ Working | None needed |
| SendGrid | ✅ Working | None needed |
| HuggingFace | ✅ Working | None needed |
| Google Gemini | ❌ Missing | Optional |
| Twitter/X | ❌ Missing | Optional |
| LinkedIn | ❌ Missing | Optional |
| Brave Search | ❌ Missing | Optional |
| GitHub | ❌ Missing | Optional |

---

## 🚀 After Configuration

Once you've added your keys:

```bash
# 1. Restart CHATTY
./launch_chatty.sh

# 2. Check status
python3 check_automation_status.py

# 3. Test new features
python3 CHATTY_MASTER_ORCHESTRATOR_v2.py
```

---

**Ready to configure?** Run `python3 API_KEY_PROMPT.py` or edit `.env` directly.
