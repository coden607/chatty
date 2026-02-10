#!/usr/bin/env python3
"""
Debug OpenRouter Response
"""

import os
from dotenv import load_dotenv
import openai
import json

load_dotenv()

def debug_openrouter_response():
    """Debug what OpenRouter actually returns"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    
    if not openrouter_key:
        print("❌ OpenRouter key not found")
        return
    
    try:
        client = openai.OpenAI(
            api_key=openrouter_key,
            base_url='https://openrouter.ai/api/v1'
        )
        
        prompt = """
        Analyze this transcript for automation insights:
        
        Transcript: "This video is about multi-agent systems and automation. We discuss how to implement agent coordination and communication protocols."
        
        Return JSON:
        {
            "relevance_score": 0.8,
            "key_topics": ["automation", "ai"],
            "automation_techniques": ["workflow automation"],
            "code_improvements": ["implement message passing"],
            "actionable_insights": ["use event-driven architecture"]
        }
        """
        
        response = client.chat.completions.create(
            model='anthropic/claude-3-haiku',
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3
        )
        
        print("🔍 OpenRouter Response Debug:")
        print(f"Model: {response.model}")
        print(f"Raw Response: {response.choices[0].message.content}")
        print(f"Type: {type(response.choices[0].message.content)}")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.choices[0].message.content)
            print(f"✅ Parsed JSON: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            
            # Try to extract JSON from response
            content = response.choices[0].message.content
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                print(f"🔧 Extracted JSON: {json_str}")
                
                try:
                    parsed = json.loads(json_str)
                    print(f"✅ Extracted Parsed: {parsed}")
                except json.JSONDecodeError as e2:
                    print(f"❌ Extract JSON Error: {e2}")
        
    except Exception as e:
        print(f"❌ OpenRouter Error: {e}")

if __name__ == "__main__":
    debug_openrouter_response()
