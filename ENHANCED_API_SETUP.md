# 🔐 ENHANCED API KEY SETUP - WITH LANGCHAIN, CREWAI & N8N

## ✅ What's New

Your automation setup now includes **priority support** for:

1. **LangChain (LangSmith)** - Essential for AI tracing and monitoring
2. **CrewAI** - Required for multi-agent orchestration  
3. **n8n** - Workflow automation integration

Plus **automatic encrypted backups** of all your API keys!

---

## 🚀 Quick Start (Just Press ENTER!)

```bash
./AUTOMATE_EVERYTHING.sh
```

The script will now guide you through getting **all** API keys in priority order:

### Priority 1 (Essential - Asked First):
- ✅ **LangChain** - AI tracing & monitoring
- ✅ **CrewAI** - Agent orchestration
- ✅ **n8n** - Workflow automation

### Priority 2 (Important):
- ✅ **xAI (Grok)** - Primary AI brain
- ✅ **OpenRouter** - AI fallback
- ✅ **Cohere** - Secondary AI
- ✅ **Twitter/X** - Social media
- ✅ **Hugging Face** - Model access

### Priority 3 (Optional):
- ⚪ **Anthropic** - Claude models (paid)

---

## 🔑 Comprehensive API Key Support

Your automation setup now supports **ALL major AI providers** with direct signup links:

### Priority 1: Infrastructure & Tools
| Service | URL | Why You Need It |
|---------|-----|-----------------|
| **LangChain** | https://smith.langchain.com/settings | AI tracing & debugging |
| **CrewAI** | https://app.crewai.com/settings/api-keys | Multi-agent orchestration |
| **n8n** | https://app.n8n.cloud/settings/api | Workflow automation |

### Priority 2: Major Model Providers
| Service | URL | Note |
|---------|-----|------|
| **OpenAI** | https://platform.openai.com/api-keys | Industry standard (GPT-4o) |
| **Google Gemini** | https://aistudio.google.com/app/apikey | Generous free tier |
| **DeepSeek** | https://platform.deepseek.com/api_keys | Top-tier coding (V3/R1) |
| **Anthropic** | https://console.anthropic.com/settings/keys | Complex reasoning (Claude) |

### Priority 3: Aggregators & Platforms
| Service | URL | Note |
|---------|-----|------|
| **OpenRouter** | https://openrouter.ai/keys | Access to all models |
| **xAI (Grok)** | https://console.x.ai/ | Real-time knowledge |
| **Hugging Face** | https://huggingface.co/settings/tokens | Open source models |

### Priority 4: Specialized Models
| Service | URL | Note |
|---------|-----|------|
| **Mistral AI** | https://console.mistral.ai/api-keys/ | Efficient European models |
| **Perplexity** | https://www.perplexity.ai/settings/api | Live web search API |
| **Together AI** | https://api.together.xyz/settings/api-keys | Fast inference |
| **Replicate** | https://replicate.com/account/api-tokens | Image generation models |
| **Cohere** | https://dashboard.cohere.com/api-keys | RAG & Embeddings |

---

## 🔐 Automatic Secure Backups

Every time you save an API key, the system now:

1. ✅ **Creates encrypted backup** of existing keys
2. ✅ **Stores in** `~/.config/chatty/backups/`
3. ✅ **Sets secure permissions** (owner read-only)
4. ✅ **Never overwrites** without backup

### Backup Commands

**Create manual backup:**
```bash
python3 secure_key_backup.py backup
```

**List all backups:**
```bash
python3 secure_key_backup.py list
```

**Restore from backup:**
```bash
python3 secure_key_backup.py restore
```

**Automatic backup (on change):**
```bash
python3 secure_key_backup.py auto
```

---

## 📁 Where Keys Are Stored

### Primary Location (Active Keys):
```
~/.config/chatty/secrets.env
```
- Permissions: `600` (owner read/write only)
- Format: Standard `.env` file
- Auto-loaded by all automation scripts

### Backup Location (Encrypted):
```
~/.config/chatty/backups/
```
- Encrypted with Fernet (symmetric encryption)
- Timestamped backups
- Metadata files for tracking

### Encryption Key:
```
~/.config/chatty/.backup_key
```
- Permissions: `600` (owner read-only)
- Auto-generated on first backup
- **Keep this safe!** Without it, backups can't be restored

---

## 🎯 Setup Process (Enhanced)

When you run `./AUTOMATE_EVERYTHING.sh`:

### Step 1: System Check ✅
- Verifies Python & dependencies
- Checks required files

### Step 2: API Key Setup (Priority Order) 🔑

**First, the essentials:**
```
[1/9] LangChain
ℹ️  Essential for LangChain tracing and monitoring
Press ENTER to open in browser...
```

**Then, the important ones:**
```
[4/9] xAI (Grok)
Press ENTER to open in browser...
```

**Finally, optional:**
```
[9/9] Anthropic
⚠️  Note: Optional - requires payment
Skip this service? (y/N):
```

### Step 3: Automatic Backup 💾
- Before saving each key
- Encrypted backup created
- Secure permissions set

### Step 4: Verification ✅
- Confirms all keys saved
- Shows configuration status

### Step 5: Launch 🚀
- Starts automation
- Begins generating content

---

## 🔍 Check Your Status

```bash
python3 check_automation_status.py
```

**You'll see:**
```
🔑 API Keys Status:
   ✅ LangChain (LangSmith): Configured
   ✅ CrewAI: Configured
   ✅ n8n Cloud: Configured
   ✅ xAI (Grok): Configured
   ✅ OpenRouter: Configured
   ✅ Cohere: Configured
   ✅ Twitter/X: Configured
   ✅ Hugging Face: Configured

   📊 8/8 keys configured
```

---

## 🛡️ Security Features

### 1. Encrypted Backups
- Fernet symmetric encryption
- Unique key per installation
- Timestamped for versioning

### 2. Secure Permissions
- `600` on secrets file (owner only)
- `600` on backup key (owner only)
- `600` on backup files (owner only)

### 3. Automatic Backups
- Before any key modification
- Hourly limit (max 1 per hour)
- No accidental overwrites

### 4. Safe Storage Location
- Hidden in `~/.config/chatty/`
- Not in project directory
- Not committed to git

---

## 💡 Common Tasks

### Add a new API key
```bash
python3 auto_setup_api_keys.py
```
- Auto-detects missing keys
- Shows only what you need
- Creates backup before saving

### Update an existing key
```bash
python3 auto_setup_api_keys.py
```
- Same process
- Automatically backs up old key
- Replaces with new value

### Restore lost keys
```bash
python3 secure_key_backup.py restore
```
- Lists all backups
- Choose which to restore
- Backs up current before restoring

### View all backups
```bash
python3 secure_key_backup.py list
```

---

## 🎉 Summary

**Enhanced Features:**
1. ✅ **3 new priority API keys** (LangChain, CrewAI, n8n)
2. ✅ **Automatic encrypted backups** before every change
3. ✅ **Secure permissions** on all key files
4. ✅ **Priority-based setup** (essential keys first)
5. ✅ **Easy restore** from any backup
6. ✅ **Never lose keys** again!

**To get started:**
```bash
./AUTOMATE_EVERYTHING.sh
```

Then just press ENTER and paste keys when prompted! 🚀

**Your keys are:**
- ✅ Stored securely in `~/.config/chatty/secrets.env`
- ✅ Backed up automatically (encrypted)
- ✅ Protected with proper permissions
- ✅ Never forgotten
- ✅ Always safe

---

**Created:** 2026-01-24
**Status:** ✅ ENHANCED & SECURE
**Backup System:** 🔐 ACTIVE
