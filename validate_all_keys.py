import os
import requests
from dotenv import load_dotenv

_secrets_file = os.getenv("CHATTY_SECRETS_FILE", ".env")
load_dotenv(_secrets_file)

def _collect_keys(prefix: str, count: int = 6):
    keys = []
    for i in range(count):
        name = f"{prefix}_API_KEY" if i == 0 else f"{prefix}_API_KEY_{i+1}"
        value = os.getenv(name)
        if value:
            keys.append(value)
    return keys

def test_openai(key):
    if not key: return "MISSING"
    try:
        headers = {"Authorization": f"Bearer {key}"}
        response = requests.post("https://api.openai.com/v1/chat/completions", 
                                headers=headers, 
                                json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
                                timeout=10)
        if response.status_code == 200: return "GOOD"
        try:
            data = response.json()
            if "insufficient_quota" in str(data): return "NO FUNDS"
            return f"BAD ({response.status_code}): {data.get('error', {}).get('message', 'Unknown error')}"
        except: return f"BAD ({response.status_code})"
    except Exception as e: return f"FAILED: {str(e)}"

def test_anthropic(key):
    if not key: return "MISSING"
    try:
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        response = requests.post("https://api.anthropic.com/v1/messages", 
                                headers=headers, 
                                json={"model": "claude-3-haiku-20240307", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]},
                                timeout=10)
        if response.status_code == 200: return "GOOD"
        try:
            data = response.json()
            if "credit balance is too low" in str(data): return "NO FUNDS"
            return f"BAD ({response.status_code}): {data.get('error', {}).get('message', 'Unknown error')}"
        except: return f"BAD ({response.status_code})"
    except Exception as e: return f"FAILED: {str(e)}"

def test_gemini(key):
    if not key: return "MISSING"
    try:
        # Try different versions/models
        for version in ["v1beta", "v1"]:
            for model in ["gemini-1.5-flash", "gemini-1.5-pro"]:
                url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={key}"
                response = requests.post(url, json={"contents": [{"parts": [{"text": "hi"}]}]}, timeout=10)
                if response.status_code == 200: return f"GOOD ({version}/{model})"
        return f"BAD ({response.status_code})"
    except Exception as e: return f"FAILED: {str(e)}"

def test_xai(key):
    if not key: return "MISSING"
    try:
        headers = {"Authorization": f"Bearer {key}"}
        response = requests.post("https://api.x.ai/v1/chat/completions", 
                                headers=headers, 
                                json={"model": "grok-3", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
                                timeout=10)
        if response.status_code == 200: return "GOOD"
        return f"BAD ({response.status_code})"
    except Exception as e: return f"FAILED: {str(e)}"

def test_groq(key):
    if not key: return "MISSING"
    try:
        headers = {"Authorization": f"Bearer {key}"}
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                headers=headers, 
                                json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
                                timeout=10)
        if response.status_code == 200: return "GOOD"
        return f"BAD ({response.status_code})"
    except Exception as e: return f"FAILED: {str(e)}"

def test_openrouter(key):
    if not key: return "MISSING"
    try:
        headers = {"Authorization": f"Bearer {key}", "HTTP-Referer": "https://narcoguard.com", "X-Title": "NarcoGuard AI"}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=headers, 
                                json={"model": "openai/gpt-3.5-turbo", "messages": [{"role": "user", "content": "hi"}]},
                                timeout=10)
        if response.status_code == 200: return "GOOD"
        return f"BAD ({response.status_code})"
    except Exception as e: return f"FAILED: {str(e)}"

def test_cohere(key):
    if not key: return "MISSING"
    try:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        response = requests.post("https://api.cohere.ai/v1/chat", 
                                headers=headers, 
                                json={"message": "hi", "model": "command-r"},
                                timeout=10)
        if response.status_code == 200: return "GOOD"
        return f"BAD ({response.status_code})"
    except Exception as e: return f"FAILED: {str(e)}"


print("--- Extensive API Key Validation ---")

openai_keys = _collect_keys("OPENAI")
anthropic_keys = _collect_keys("ANTHROPIC", count=4)
xai_keys = _collect_keys("XAI", count=4)
gemini_keys = _collect_keys("GEMINI", count=4) or _collect_keys("GOOGLE", count=4)
groq_keys = _collect_keys("GROQ", count=4)
openrouter_keys = _collect_keys("OPENROUTER", count=6)

print("\n--- Testing OpenAI ---")
if openai_keys:
    for i, key in enumerate(openai_keys):
        print(f"OpenAI {i+1} ({key[:10]}...): {test_openai(key)}")
else:
    print("OpenAI: MISSING")

print("\n--- Testing Anthropic ---")
if anthropic_keys:
    for i, key in enumerate(anthropic_keys):
        print(f"Anthropic {i+1} ({key[:10]}...): {test_anthropic(key)}")
else:
    print("Anthropic: MISSING")

print("\n--- Testing xAI ---")
if xai_keys:
    for i, key in enumerate(xai_keys):
        print(f"xAI {i+1} ({key[:10]}...): {test_xai(key)}")
else:
    print("xAI: MISSING")

print("\n--- Testing Gemini ---")
if gemini_keys:
    for i, key in enumerate(gemini_keys):
        print(f"Gemini {i+1} ({key[:10]}...): {test_gemini(key)}")
else:
    print("Gemini: MISSING")

print("\n--- Testing Groq ---")
if groq_keys:
    for i, key in enumerate(groq_keys):
        print(f"Groq {i+1} ({key[:10]}...): {test_groq(key)}")
else:
    print("Groq: MISSING")

print("\n--- Testing OpenRouter ---")
if openrouter_keys:
    for i, key in enumerate(openrouter_keys):
        print(f"OpenRouter {i+1} ({key[:10]}...): {test_openrouter(key)}")
else:
    print("OpenRouter: MISSING")

print("\n--- Testing Cohere ---")
cohere_key = os.getenv("COHERE_API_KEY")
print(f"Cohere: {test_cohere(cohere_key)}")
