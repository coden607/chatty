import os
import requests
from dotenv import load_dotenv

# Load root .env
load_dotenv(".env", override=True)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=True)

or_keys = [
    os.getenv('OPENROUTER_API_KEY'), 
    os.getenv('OPENROUTER_API_KEY_2'), 
    os.getenv('OPENROUTER_API_KEY_3'), 
    os.getenv('OPENROUTER_API_KEY_4'),
    os.getenv('OPENROUTER_API_KEY_5')
]

for i, key in enumerate(or_keys):
    if not key:
        print(f"OR Key #{i+1}: Missing")
        continue
        
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {key}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"OR Key #{i+1}: {data.get('data', {}).get('total_credits', 0)} credits")
        else:
            print(f"OR Key #{i+1}: Failed ({response.status_code}) - {response.text}")
    except Exception as e:
        print(f"OR Key #{i+1}: Error - {e}")
