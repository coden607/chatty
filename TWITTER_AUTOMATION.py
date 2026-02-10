#!/usr/bin/env python3
"""
TWITTER/X AUTOMATION MODULE
Fully automated Twitter/X posting and engagement
Transparent logging to logs/twitter_automation.log
"""

import asyncio
import os
import json
import logging
import random
from datetime import datetime
from pathlib import Path
import tweepy
from transparency_log import log_transparency

# Setup logging
LOG_DIR = Path("/home/coden809/CHATTY/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'twitter_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('twitter_automation')

class TwitterAutomation:
    """Fully automated Twitter/X posting system"""
    
    def __init__(self):
        self.is_running = False
        self.client = None
        self.api = None
        self.total_posts = 0
        self.total_engagements = 0
        self.log_file = LOG_DIR / 'twitter_automation.log'
        self.action_log_file = Path("/home/coden809/CHATTY/generated_content") / "twitter_actions.jsonl"
        
    def _load_secrets(self):
        """Load Twitter/X credentials from secrets file and export as env vars"""
        secrets_path = os.environ.get('CHATTY_SECRETS_FILE', '/home/coden809/.config/chatty/secrets.env')
        secrets_path = os.path.expanduser(secrets_path)
        secrets = {}
        if os.path.exists(secrets_path):
            with open(secrets_path) as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        secrets[key] = value
                        # Export as environment variable for tweepy
                        os.environ[key] = value
        return secrets
    
    def _get_twitter_credentials(self):
        """Get Twitter credentials with fallback to alternative names"""
        secrets = self._load_secrets()
        
        # Try X_* keys first, then fall back to TWITTER_* aliases
        bearer_token = secrets.get('X_BEARER_TOKEN') or os.environ.get('TWITTER_BEARER_TOKEN') or os.environ.get('X_BEARER_TOKEN')
        consumer_key = secrets.get('X_CONSUMER_KEY') or os.environ.get('TWITTER_API_KEY') or os.environ.get('X_CONSUMER_KEY')
        consumer_secret = secrets.get('X_CONSUMER_SECRET') or os.environ.get('TWITTER_API_SECRET') or os.environ.get('X_CONSUMER_SECRET')
        access_token = secrets.get('X_ACCESS_TOKEN') or os.environ.get('TWITTER_ACCESS_TOKEN') or os.environ.get('X_ACCESS_TOKEN')
        access_secret = secrets.get('X_ACCESS_SECRET') or os.environ.get('TWITTER_ACCESS_SECRET') or os.environ.get('X_ACCESS_SECRET')
        
        return bearer_token, consumer_key, consumer_secret, access_token, access_secret
    
    async def initialize(self):
        """Initialize Twitter API client"""
        logger.info("="*60)
        logger.info("🐦 TWITTER/X AUTOMATION INITIALIZING")
        logger.info("="*60)
        
        # Load secrets and export as env vars
        self._load_secrets()
        
        # Get credentials from environment (now set by _load_secrets)
        bearer_token = os.environ.get('X_BEARER_TOKEN') or os.environ.get('TWITTER_BEARER_TOKEN')
        consumer_key = os.environ.get('X_CONSUMER_KEY') or os.environ.get('TWITTER_API_KEY')
        consumer_secret = os.environ.get('X_CONSUMER_SECRET') or os.environ.get('TWITTER_API_SECRET')
        access_token = os.environ.get('X_ACCESS_TOKEN') or os.environ.get('TWITTER_ACCESS_TOKEN')
        access_secret = os.environ.get('X_ACCESS_SECRET') or os.environ.get('TWITTER_ACCESS_SECRET')
        
        # Verify all credentials are present
        missing = []
        if not bearer_token: missing.append('X_BEARER_TOKEN')
        if not consumer_key: missing.append('X_CONSUMER_KEY')
        if not consumer_secret: missing.append('X_CONSUMER_SECRET')
        if not access_token: missing.append('X_ACCESS_TOKEN')
        if not access_secret: missing.append('X_ACCESS_SECRET')
        
        if missing:
            logger.error(f"❌ Missing Twitter credentials: {', '.join(missing)}")
            return False
            
        # Check for placeholder/identical keys which cause 401
        if consumer_key == consumer_secret or access_token == access_secret:
            logger.error("❌ Twitter credentials appear to be placeholders (key matches secret). Initialization aborted.")
            return False
        
        try:
            # Initialize v2 client
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_secret,
                wait_on_rate_limit=True
            )
            
            # Initialize v1.1 API for media uploads
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_secret)
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Verify credentials
            me = self.client.get_me()
            if me.data:
                logger.info(f"✅ Twitter API initialized as: @{me.data.username}")
                self._log_action("initialize", "success", {"username": me.data.username})
            else:
                logger.warning("⚠️ Could not verify Twitter credentials")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Twitter API: {e}")
            self._log_action("initialize", "failed", {"error": str(e)})
            return False
    
    def _log_action(self, action: str, status: str, details: dict = None):
        """Log action to transparent JSONL file"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "status": status,
            "details": details or {}
        }
        self.action_log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.action_log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    async def post_tweet(self, content: str) -> dict:
        """Post a single tweet"""
        try:
            response = self.client.create_tweet(text=content[:280])
            if response.data:
                tweet_id = response.data['id']
                logger.info(f"🐦 Posted tweet: {content[:50]}...")
                self.total_posts += 1
                self._log_action("post_tweet", "success", {
                    "tweet_id": tweet_id,
                    "content_preview": content[:50]
                })
                log_transparency(
                    "twitter_post",
                    "sent",
                    {"tweet_id": tweet_id, "content_preview": content[:50]},
                )
                return {"status": "success", "tweet_id": tweet_id}
            else:
                logger.error("❌ Failed to get tweet ID from response")
                return {"status": "failed", "error": "No tweet ID"}
        except Exception as e:
            logger.error(f"❌ Tweet failed: {e}")
            self._log_action("post_tweet", "failed", {"error": str(e)})
            log_transparency("twitter_post", "failed", {"error": str(e)})
            return {"status": "failed", "error": str(e)}
    
    async def post_thread(self, tweets: list) -> dict:
        """Post a thread of tweets"""
        results = []
        previous_tweet_id = None
        
        for i, tweet in enumerate(tweets):
            try:
                if i == 0:
                    response = self.client.create_tweet(text=tweet[:280])
                else:
                    response = self.client.create_tweet(
                        text=tweet[:280],
                        in_reply_to_tweet_id=previous_tweet_id
                    )
                
                if response.data:
                    previous_tweet_id = response.data['id']
                    results.append({"status": "success", "tweet_id": previous_tweet_id})
                    logger.info(f"🐦 Thread tweet {i+1}/{len(tweets)}: {tweet[:30]}...")
                    self.total_posts += 1
                    await asyncio.sleep(2)  # Rate limit protection
                    
            except Exception as e:
                logger.error(f"❌ Thread tweet {i+1} failed: {e}")
                results.append({"status": "failed", "error": str(e)})
                break
        
        self._log_action("post_thread", "completed", {"total_tweets": len(tweets), "successes": sum(1 for r in results if r['status'] == 'success')})
        return {"results": results}
    
    async def get_timeline(self, max_results: int = 10):
        """Get home timeline"""
        try:
            tweets = self.client.get_home_tweet_count()
            logger.info(f"📖 Retrieved timeline with {tweets} tweets")
            return tweets
        except Exception as e:
            logger.error(f"❌ Failed to get timeline: {e}")
            return []
    
    async def get_my_tweets(self, max_results: int = 20):
        """Get user's recent tweets"""
        try:
            tweets = self.client.get_users_tweets(
                id=me.data.id if (me := self.client.get_me()) else None,
                max_results=max_results
            )
            return tweets
        except Exception as e:
            logger.error(f"❌ Failed to get my tweets: {e}")
            return []
    
    async def auto_post_loop(self):
        """Automated posting loop - posts content periodically"""
        content_themes = [
            "NarcoGuard AI life-saving technology",
            "Automated overdose prevention",
            "Harm reduction innovation",
            "AI for good",
            "Community impact stories"
        ]
        
        sample_content = {
            "NarcoGuard AI life-saving technology": [
                "🕐 Every second counts in an overdose. NarcoGuard's AI detects overdoses in SECONDS, not minutes. https://v0-narcoguard-pwa-build.vercel.app",
                "The opioid crisis needs solutions, not just awareness. NarcoGuard provides automated naloxone delivery when seconds matter most.",
                "AI isn't just for chatbots. It's saving lives in Broome County. NarcoGuard: Where technology meets humanity. https://gofund.me/e1a0b3f2"
            ],
            "Automated overdose prevention": [
                "What if a watch could save your life? NarcoGuard's AI-powered watch detects overdose signs and delivers naloxone automatically.",
                "80 units deployed in Broome County. 80 chances to save a life. The future of harm reduction is here.",
                "From detection to delivery in seconds. That's the NarcoGuard promise. 🕐➡️💉"
            ],
            "Harm reduction innovation": [
                "Harm reduction meets high-tech. NarcoGuard combines AI, wearables, and automated response to combat the opioid crisis.",
                "We're not waiting for change. We're building it. NarcoGuard: Automated harm reduction for the 21st century.",
                "Technology should serve humanity. NarcoGuard serves those who need it most."
            ],
            "AI for good": [
                "This is what AI for good looks like. NarcoGuard: Saving lives one detection at a time.",
                "When we asked 'how can AI help?', the answer was clear: save lives. NarcoGuard is the answer.",
                "AI won't solve every problem, but it can solve this one. Automated overdose detection and response."
            ],
            "Community impact stories": [
                "Behind every NarcoGuard unit is a story of hope. Behind every deployment is a community that cares.",
                "Broome County is leading the way. 80 units. 80 lives potentially saved. This is what progress looks like.",
                "From prototype to deployment to impact. NarcoGuard's journey is just beginning, but the results are already visible."
            ]
        }
        
        post_count = 0
        while self.is_running:
            try:
                # Pick a random theme and tweet
                theme = random.choice(content_themes)
                tweet_text = random.choice(sample_content.get(theme, sample_content["NarcoGuard AI life-saving technology"]))
                
                result = await self.post_tweet(tweet_text)
                post_count += 1
                
                # Log to main automation log
                logger.info(f"📊 Auto-post #{post_count}: {theme}")
                
                # Wait 2-4 hours between posts
                wait_time = random.randint(7200, 14400)
                logger.info(f"💤 Next post in {wait_time//3600} hours...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"❌ Auto-post error: {e}")
                await asyncio.sleep(300)  # 5 min retry
    
    async def engagement_loop(self):
        """Automated engagement loop - like and reply to relevant tweets"""
        # Search queries for engagement
        search_queries = [
            "overdose prevention",
            "harm reduction",
            "opioid crisis solutions",
            "AI healthcare",
            "wearable technology health"
        ]
        
        while self.is_running:
            try:
                query = random.choice(search_queries)
                
                # Search for relevant tweets
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=10
                )
                
                if tweets.data:
                    for tweet in tweets.data[:3]:  # Engage with top 3
                        try:
                            # Like the tweet
                            self.client.like(tweet.id)
                            self.total_engagements += 1
                            
                            # Small delay between actions
                            await asyncio.sleep(5)
                            
                        except Exception as e:
                            logger.debug(f"Engagement skipped: {e}")
                    
                    logger.info(f"👍 Engaged with {len(tweets.data[:3])} tweets about '{query}'")
                
                # Wait before next engagement round
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"❌ Engagement loop error: {e}")
                await asyncio.sleep(600)
    
    async def start(self):
        """Start the Twitter automation system"""
        self.is_running = True
        while self.is_running:
            try:
                if not await self.initialize():
                    logger.error("❌ Cannot start Twitter automation - initialization failed (retrying)")
                    await asyncio.sleep(300)
                    continue

                logger.info("="*60)
                logger.info("🐦 TWITTER/X AUTOMATION RUNNING")
                logger.info("="*60)
                logger.info("🔄 Auto-posting: ACTIVE")
                logger.info("🔄 Auto-engagement: ACTIVE")
                logger.info("📊 Logging to: logs/twitter_automation.log")

                post_task = asyncio.create_task(self.auto_post_loop())
                engagement_task = asyncio.create_task(self.engagement_loop())

                while self.is_running:
                    await asyncio.sleep(60)

                post_task.cancel()
                engagement_task.cancel()
                await asyncio.gather(post_task, engagement_task, return_exceptions=True)
            except Exception as e:
                logger.error(f"❌ Twitter automation loop failed: {e}")
                await asyncio.sleep(120)
    
    async def stop(self):
        """Stop the Twitter automation system"""
        self.is_running = False
        logger.info("🐦 Twitter automation stopped")
        logger.info(f"📊 Session stats: {self.total_posts} posts, {self.total_engagements} engagements")
        self._log_action("session_end", "stopped", {
            "total_posts": self.total_posts,
            "total_engagements": self.total_engagements
        })
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            "status": "running" if self.is_running else "stopped",
            "total_posts": self.total_posts,
            "total_engagements": self.total_engagements,
            "log_file": str(self.log_file),
            "action_log": str(self.action_log_file)
        }


# Global instance
twitter_automation = TwitterAutomation()


async def main():
    """Test run"""
    await twitter_automation.start()

if __name__ == "__main__":
    print("🐦 TWITTER/X AUTOMATION MODULE")
    print("="*60)
    print("Automated posting and engagement")
    print("Transparent logging to logs/twitter_automation.log")
    print("="*60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        asyncio.run(twitter_automation.stop())
