#!/usr/bin/env python3
"""
Test Cole Medin Learning System
"""

import asyncio
import json
import sys
from COLE_MEDIN_LEARNER import ColeMedinChannelLearner

async def test_cole_medin_learning():
    """Test the Cole Medin learning system"""
    print("🧠 Testing Cole Medin Channel Learning")
    print("=" * 50)
    
    learner = ColeMedinChannelLearner()
    
    # Test with a real Cole Medin video about Agent Zero
    cole_videos = [
        "https://www.youtube.com/watch?v=L_G0m2h2Jq8",  # Agent Zero
        "https://www.youtube.com/watch?v=7Xqz_4a3c9k",  # Archon 2
        "https://www.youtube.com/watch?v=9Yr8n5p3d7f"   # BMAD
    ]
    
    for video_url in cole_videos[:1]:  # Test one video
        print(f"\n🎥 Learning from Cole Medin: {video_url}")
        result = await learner.learn_from_cole_medin_video(video_url)
        
        print(f"\n📊 Results:")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"Title: {result['metadata'].get('title', 'N/A')}")
            print(f"Cole's Relevance: {result['cole_analysis'].get('cole_relevance_score', 0)}")
            print(f"Frameworks: {result['cole_analysis'].get('agent_frameworks_mentioned', [])}")
            print(f"Techniques: {result['cole_analysis'].get('key_techniques', [])}")
            print(f"Chatty Applications: {result['cole_analysis'].get('chatty_applications', [])}")
            print(f"Improvements Applied: {len(result['applied_changes'])}")
            
            # Show applied changes
            for change in result['applied_changes']:
                print(f"\n🔧 {change.get('improvement', 'N/A')}")
                print(f"File: {change.get('file', 'N/A')}")
                print(f"Success: {change.get('success', False)}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Show final stats
    stats = learner.get_cole_learning_stats()
    print(f"\n📈 Cole Medin Learning Stats:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(test_cole_medin_learning())
