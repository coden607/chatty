#!/usr/bin/env python3
"""
Test the Functional YouTube Learner
"""

import asyncio
import sys
from FUNCTIONAL_YOUTUBE_LEARNER import FunctionalYouTubeLearner

async def test_youtube_learner():
    """Test the YouTube learner with a real video"""
    print("🧪 Testing Functional YouTube Learner")
    print("=" * 40)
    
    learner = FunctionalYouTubeLearner()
    
    # Test video ID extraction
    test_urls = [
        "https://www.youtube.com/watch?v=jkrO6OyfGnM",
        "https://youtu.be/si8z_jk7g5c",
        "https://www.youtube.com/embed/wH7vqrz8oOs"
    ]
    
    print("\n🔍 Testing URL extraction:")
    for url in test_urls:
        video_id = learner._extract_video_id(url)
        print(f"URL: {url}")
        print(f"Video ID: {video_id}")
        print()
    
    # Test with one real video (TED talks usually have good transcripts)
    test_video = "https://www.youtube.com/watch?v=8KkKuTCFvZU"  # TED talk on AI
    
    print(f"🎥 Testing full learning with: {test_video}")
    result = await learner.learn_from_video(test_video)
    
    print("\n📊 Results:")
    print(f"Success: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"Title: {result['metadata'].get('title', 'N/A')}")
        print(f"Channel: {result['metadata'].get('channel', 'N/A')}")
        print(f"Transcript length: {result['transcript_length']} chars")
        print(f"Relevance score: {result['analysis'].get('relevance_score', 0)}")
        print(f"Key topics: {result['analysis'].get('key_topics', [])}")
        print(f"Code changes applied: {len(result['code_changes_applied'])}")
        
        # Show applied changes
        for change in result['code_changes_applied']:
            print(f"\n🔧 Change: {change.get('insight', 'N/A')}")
            print(f"File: {change.get('file', 'N/A')}")
            print(f"Success: {change.get('success', False)}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Show final stats
    stats = learner.get_learning_stats()
    print(f"\n📈 Final Stats:")
    print(f"Videos processed: {stats['videos_processed']}")
    print(f"Total code changes: {stats['total_code_changes']}")
    print(f"Topics covered: {stats['topics_covered']}")

if __name__ == "__main__":
    asyncio.run(test_youtube_learner())
