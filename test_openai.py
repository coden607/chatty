#!/usr/bin/env python3
"""
Debug OpenAI Integration for YouTube Learning
"""

import os
from dotenv import load_dotenv
import openai

load_dotenv()

def test_openai_integration():
    """Test OpenAI integration directly"""
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"OpenAI Key: {api_key[:20] if api_key else 'NOT FOUND'}...")
    
    if not api_key:
        print("❌ OpenAI key not found")
        return
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Test with simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OpenAI is working!'"}],
            max_tokens=10
        )
        
        print(f"✅ OpenAI Response: {response.choices[0].message.content}")
        
        # Test with transcript analysis
        test_transcript = """
        This video is about multi-agent systems and automation. 
        We discuss how to implement agent coordination and communication protocols.
        The key insights are about using message passing and event-driven architectures.
        """
        
        prompt = f"""
        Analyze this transcript for automation insights:
        
        {test_transcript}
        
        Return JSON with:
        {{
            "relevance_score": 0.8,
            "key_topics": ["multi-agent", "automation"],
            "automation_techniques": ["agent coordination"],
            "code_improvements": ["implement message passing"],
            "actionable_insights": ["use event-driven architecture"]
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        
        print(f"✅ Analysis Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")

if __name__ == "__main__":
    test_openai_integration()
