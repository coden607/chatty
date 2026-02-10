#!/usr/bin/env python3
"""
REAL SOCIAL MEDIA INTEGRATION SYSTEM
Complete social media API integration for CHATTY
"""

import asyncio
import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os
from urllib.parse import quote
from dotenv import load_dotenv
from transparency_log import log_transparency

# Load environment variables
load_dotenv(".env", override=False)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=False)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealSocialMediaIntegration:
    """Real social media integration system with multiple platform APIs"""
    
    def __init__(self):
        self.is_running = False
        
        # Platform configurations
        self.platforms = {
            "twitter": {
                "enabled": bool(os.getenv("X_CONSUMER_KEY") and os.getenv("X_ACCESS_TOKEN")),
                "api_base": "https://api.twitter.com/2",
                "consumer_key": os.getenv("X_CONSUMER_KEY"),
                "consumer_secret": os.getenv("X_CONSUMER_SECRET"),
                "access_token": os.getenv("X_ACCESS_TOKEN"),
                "access_secret": os.getenv("X_ACCESS_SECRET"),
                "bearer_token": os.getenv("X_BEARER_TOKEN"),
                "post_limit": 1000,  # Daily limit
                "engagement_limit": 500
            },
            "linkedin": {
                "enabled": bool(os.getenv("LINKEDIN_ACCESS_TOKEN") and os.getenv("LINKEDIN_PERSON_ID")),
                "api_base": "https://api.linkedin.com/v2",
                "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN"),
                "person_id": os.getenv("LINKEDIN_PERSON_ID"),
                "organization_id": os.getenv("LINKEDIN_ORG_ID"),
                "post_limit": 25,
                "engagement_limit": 100
            },
            "facebook": {
                "enabled": bool(os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN") and os.getenv("FACEBOOK_PAGE_ID")),
                "api_base": "https://graph.facebook.com/v20.0",
                "page_access_token": os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"),
                "page_id": os.getenv("FACEBOOK_PAGE_ID"),
                "post_limit": 200,
                "engagement_limit": 1000
            },
            "instagram": {
                "enabled": bool(os.getenv("INSTAGRAM_ACCESS_TOKEN") and os.getenv("INSTAGRAM_BUSINESS_ACCOUNT")),
                "api_base": "https://graph.facebook.com/v20.0",
                "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN"),
                "business_account": os.getenv("INSTAGRAM_BUSINESS_ACCOUNT"),
                "post_limit": 25,
                "engagement_limit": 500
            },
            "youtube": {
                "enabled": bool(os.getenv("YOUTUBE_API_KEY")),
                "api_base": "https://www.googleapis.com/youtube/v3",
                "api_key": os.getenv("YOUTUBE_API_KEY"),
                "channel_id": os.getenv("YOUTUBE_CHANNEL_ID"),
                "post_limit": 3,
                "engagement_limit": 100
            }
        }
        
        # Content management
        self.content_queue = []
        self.post_schedule = []
        self.engagement_queue = []
        
        # Analytics tracking
        self.post_analytics = []
        self.engagement_analytics = []
        self.follower_analytics = []
        
        # Rate limiting
        self.rate_limits = {}
        self.daily_usage = {}
        
    async def initialize(self):
        """Initialize social media integration system"""
        logger.info("📱 Initializing Real Social Media Integration System...")
        
        # Validate platform configurations
        for platform_name, config in self.platforms.items():
            if config["enabled"]:
                if await self._validate_platform_credentials(platform_name):
                    logger.info(f"✅ {platform_name.title()} API validated")
                else:
                    logger.error(f"❌ {platform_name.title()} API validation failed")
                    config["enabled"] = False
            else:
                logger.info(f"⚠️ {platform_name.title()} API disabled (missing credentials)")
        
        # Load existing data
        await self._load_social_data()
        
        # Initialize rate limits
        await self._initialize_rate_limits()
        
        logger.info("✅ Social media integration system initialized")
        return True
    
    async def _validate_platform_credentials(self, platform_name: str) -> bool:
        """Validate platform API credentials"""
        try:
            config = self.platforms[platform_name]
            
            if platform_name == "twitter":
                # Test Twitter API access
                headers = {"Authorization": f"Bearer {config['bearer_token']}"}
                response = requests.get(f"{config['api_base']}/users/me", headers=headers, timeout=10)
                return response.status_code == 200
                
            elif platform_name == "linkedin":
                # Test LinkedIn API access
                headers = {"Authorization": f"Bearer {config['access_token']}"}
                response = requests.get(f"{config['api_base']}/me", headers=headers, timeout=10)
                return response.status_code == 200
                
            elif platform_name == "facebook":
                # Test Facebook API access
                params = {"access_token": config["page_access_token"]}
                response = requests.get(f"{config['api_base']}/{config['page_id']}", params=params, timeout=10)
                return response.status_code == 200
                
            elif platform_name == "instagram":
                # Test Instagram API access
                params = {"access_token": config["access_token"]}
                response = requests.get(f"{config['api_base']}/{config['business_account']}", params=params, timeout=10)
                return response.status_code == 200
                
            elif platform_name == "youtube":
                # Test YouTube API access
                params = {"key": config["api_key"], "part": "snippet", "id": config["channel_id"]}
                response = requests.get(f"{config['api_base']}/channels", params=params, timeout=10)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"❌ Credential validation failed for {platform_name}: {e}")
            return False
        
        return False
    
    async def _load_social_data(self):
        """Load existing social media data"""
        data_file = Path("generated_content") / "social_media_data.json"
        if data_file.exists():
            try:
                with open(data_file, "r") as f:
                    data = json.load(f)
                    self.post_analytics = data.get("post_analytics", [])
                    self.engagement_analytics = data.get("engagement_analytics", [])
                    self.follower_analytics = data.get("follower_analytics", [])
                logger.info(f"✅ Loaded social media analytics data")
            except Exception as e:
                logger.error(f"❌ Failed to load social media data: {e}")
    
    async def _initialize_rate_limits(self):
        """Initialize rate limiting tracking"""
        for platform_name in self.platforms:
            self.rate_limits[platform_name] = {
                "post_limit": self.platforms[platform_name]["post_limit"],
                "engagement_limit": self.platforms[platform_name]["engagement_limit"],
                "posts_used": 0,
                "engagements_used": 0,
                "reset_time": datetime.now() + timedelta(days=1)
            }
            self.daily_usage[platform_name] = {
                "posts": 0,
                "engagements": 0,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
    
    async def post_content(self, platform_name: str, content: str, media_urls: List[str] = None, scheduled_time: datetime = None) -> Dict[str, Any]:
        """Post content to a specific platform"""
        try:
            if not self.platforms[platform_name]["enabled"]:
                return {"error": f"{platform_name.title()} API not configured"}
            
            # Check rate limits
            if not await self._check_rate_limit(platform_name, "post"):
                return {"error": f"Rate limit exceeded for {platform_name}"}
            
            config = self.platforms[platform_name]
            
            if platform_name == "twitter":
                result = await self._post_to_twitter(content, media_urls)
            elif platform_name == "linkedin":
                result = await self._post_to_linkedin(content, media_urls)
            elif platform_name == "facebook":
                result = await self._post_to_facebook(content, media_urls)
            elif platform_name == "instagram":
                result = await self._post_to_instagram(content, media_urls)
            elif platform_name == "youtube":
                result = await self._post_to_youtube(content, media_urls)
            else:
                return {"error": "Unsupported platform"}
            
            if result.get("success"):
                await self._track_post_analytics(platform_name, content, result)
                await self._update_rate_limit(platform_name, "post")
                
                logger.info(f"✅ Posted to {platform_name}: {result.get('post_id', 'unknown')}")
            else:
                logger.error(f"❌ Failed to post to {platform_name}: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Post failed for {platform_name}: {e}")
            return {"error": str(e)}
    
    async def _post_to_twitter(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to Twitter/X"""
        try:
            config = self.platforms["twitter"]
            
            # Handle media uploads
            media_ids = []
            if media_urls:
                for url in media_urls[:4]:  # Twitter allows max 4 images
                    media_id = await self._upload_media_to_twitter(url)
                    if media_id:
                        media_ids.append(media_id)
            
            # Post tweet
            headers = {"Authorization": f"Bearer {config['bearer_token']}"}
            payload = {"text": content}
            if media_ids:
                payload["media"] = {"media_ids": media_ids}
            
            response = requests.post(f"{config['api_base']}/tweets", headers=headers, json=payload, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "post_id": data["data"]["id"],
                    "url": f"https://twitter.com/user/status/{data['data']['id']}"
                }
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _upload_media_to_twitter(self, media_url: str) -> Optional[str]:
        """Upload media to Twitter"""
        try:
            config = self.platforms["twitter"]
            headers = {"Authorization": f"Bearer {config['bearer_token']}"}
            
            # Download media
            response = requests.get(media_url, timeout=30)
            if response.status_code != 200:
                return None
            
            # Upload media
            files = {"media": response.content}
            response = requests.post(f"{config['api_base']}/media/upload", headers=headers, files=files, timeout=60)
            
            if response.status_code == 200:
                return response.json()["media_id_string"]
            return None
            
        except Exception as e:
            logger.error(f"❌ Media upload failed: {e}")
            return None
    
    async def _post_to_linkedin(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to LinkedIn"""
        try:
            config = self.platforms["linkedin"]
            headers = {
                "Authorization": f"Bearer {config['access_token']}",
                "Content-Type": "application/json"
            }
            
            # Prepare content
            payload = {
                "author": f"urn:li:person:{config['person_id']}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            
            # Add media if provided
            if media_urls:
                media_assets = []
                for url in media_urls:
                    # Upload media first (simplified)
                    media_assets.append({
                        "status": "READY",
                        "media": url
                    })
                
                payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = media_assets
                payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            
            response = requests.post(f"{config['api_base']}/ugcPosts", headers=headers, json=payload, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "post_id": data["id"],
                    "url": f"https://www.linkedin.com/feed/update/{data['id']}"
                }
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _post_to_facebook(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to Facebook"""
        try:
            config = self.platforms["facebook"]
            
            # Prepare parameters
            params = {
                "access_token": config["page_access_token"],
                "message": content
            }
            
            # Add media if provided
            if media_urls:
                params["attached_media[0]"] = media_urls[0]  # Facebook supports single image per post
            
            response = requests.post(f"{config['api_base']}/{config['page_id']}/feed", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "post_id": data["id"],
                    "url": f"https://www.facebook.com/{config['page_id']}/posts/{data['id']}"
                }
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _post_to_instagram(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to Instagram"""
        try:
            config = self.platforms["instagram"]
            
            if not media_urls:
                return {"success": False, "error": "Instagram requires media"}
            
            # Create media container
            params = {
                "access_token": config["access_token"],
                "image_url": media_urls[0],
                "caption": content
            }
            
            response = requests.post(f"{config['api_base']}/{config['business_account']}/media", params=params, timeout=30)
            
            if response.status_code == 200:
                container_data = response.json()
                
                # Publish media
                publish_params = {
                    "access_token": config["access_token"],
                    "creation_id": container_data["id"]
                }
                
                publish_response = requests.post(f"{config['api_base']}/{config['business_account']}/media_publish", params=publish_params, timeout=30)
                
                if publish_response.status_code == 200:
                    publish_data = publish_response.json()
                    return {
                        "success": True,
                        "post_id": publish_data["id"],
                        "url": f"https://www.instagram.com/p/{publish_data['id']}"
                    }
            
            return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _post_to_youtube(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to YouTube (upload video)"""
        try:
            config = self.platforms["youtube"]
            
            if not media_urls:
                return {"success": False, "error": "YouTube requires video"}
            
            # This is a simplified version - YouTube upload requires multipart upload
            # In production, you'd use the YouTube Data API v3 with proper OAuth2
            
            return {"success": False, "error": "YouTube upload requires OAuth2 implementation"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def engage_with_content(self, platform_name: str, action: str, target_id: str, message: str = None) -> Dict[str, Any]:
        """Engage with content (like, comment, share)"""
        try:
            if not self.platforms[platform_name]["enabled"]:
                return {"error": f"{platform_name.title()} API not configured"}
            
            # Check rate limits
            if not await self._check_rate_limit(platform_name, "engagement"):
                return {"error": f"Rate limit exceeded for {platform_name}"}
            
            config = self.platforms[platform_name]
            
            if action == "like":
                result = await self._like_content(platform_name, target_id)
            elif action == "comment":
                if not message:
                    return {"error": "Comment requires message"}
                result = await self._comment_on_content(platform_name, target_id, message)
            elif action == "share":
                result = await self._share_content(platform_name, target_id)
            else:
                return {"error": "Unsupported engagement action"}
            
            if result.get("success"):
                await self._track_engagement_analytics(platform_name, action, target_id, result)
                await self._update_rate_limit(platform_name, "engagement")
                
                logger.info(f"✅ {action.title()} on {platform_name}: {target_id}")
            else:
                logger.error(f"❌ {action.title()} failed on {platform_name}: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Engagement failed on {platform_name}: {e}")
            return {"error": str(e)}
    
    async def _like_content(self, platform_name: str, target_id: str) -> Dict[str, Any]:
        """Like content on a platform"""
        try:
            config = self.platforms[platform_name]
            
            if platform_name == "twitter":
                headers = {"Authorization": f"Bearer {config['bearer_token']}"}
                payload = {"tweet_id": target_id}
                response = requests.post(f"{config['api_base']}/users/me/likes", headers=headers, json=payload, timeout=10)
                
            elif platform_name == "facebook":
                params = {"access_token": config["page_access_token"]}
                response = requests.post(f"{config['api_base']}/{target_id}/likes", params=params, timeout=10)
                
            elif platform_name == "linkedin":
                # LinkedIn doesn't have a direct like API, would need to use reactions
                return {"success": False, "error": "LinkedIn like API not implemented"}
            
            if response.status_code in [200, 201]:
                return {"success": True, "action_id": f"like_{target_id}"}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _comment_on_content(self, platform_name: str, target_id: str, message: str) -> Dict[str, Any]:
        """Comment on content"""
        try:
            config = self.platforms[platform_name]
            
            if platform_name == "twitter":
                # Twitter doesn't have direct comment API, would need to reply
                return await self._post_to_twitter(f"@{target_id.split(':')[0]} {message}")
                
            elif platform_name == "facebook":
                params = {"access_token": config["page_access_token"], "message": message}
                response = requests.post(f"{config['api_base']}/{target_id}/comments", params=params, timeout=10)
                
            elif platform_name == "linkedin":
                # LinkedIn comment API
                headers = {"Authorization": f"Bearer {config['access_token']}"}
                payload = {
                    "actor": f"urn:li:person:{config['person_id']}",
                    "object": f"urn:li:activity:{target_id}",
                    "message": {"text": message}
                }
                response = requests.post(f"{config['api_base']}/comments", headers=headers, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                return {"success": True, "comment_id": f"comment_{target_id}"}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _share_content(self, platform_name: str, target_id: str) -> Dict[str, Any]:
        """Share content"""
        try:
            config = self.platforms[platform_name]
            
            if platform_name == "twitter":
                # Retweet
                headers = {"Authorization": f"Bearer {config['bearer_token']}"}
                response = requests.post(f"{config['api_base']}/tweets", headers=headers, json={"text": f"RT @{target_id.split(':')[0]}"}, timeout=10)
                
            elif platform_name == "facebook":
                params = {"access_token": config["page_access_token"]}
                response = requests.post(f"{config['api_base']}/{target_id}/sharedposts", params=params, timeout=10)
            
            if response.status_code in [200, 201]:
                return {"success": True, "share_id": f"share_{target_id}"}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_analytics(self, platform_name: str = None) -> Dict[str, Any]:
        """Get social media analytics"""
        try:
            if platform_name:
                if not self.platforms[platform_name]["enabled"]:
                    return {"error": f"{platform_name.title()} API not configured"}
                
                return await self._get_platform_analytics(platform_name)
            else:
                # Get overall analytics
                analytics = {}
                for name, config in self.platforms.items():
                    if config["enabled"]:
                        analytics[name] = await self._get_platform_analytics(name)
                
                return analytics
                
        except Exception as e:
            logger.error(f"❌ Analytics retrieval failed: {e}")
            return {"error": str(e)}
    
    async def _get_platform_analytics(self, platform_name: str) -> Dict[str, Any]:
        """Get analytics for a specific platform"""
        try:
            config = self.platforms[platform_name]
            
            if platform_name == "twitter":
                return await self._get_twitter_analytics()
            elif platform_name == "linkedin":
                return await self._get_linkedin_analytics()
            elif platform_name == "facebook":
                return await self._get_facebook_analytics()
            elif platform_name == "instagram":
                return await self._get_instagram_analytics()
            elif platform_name == "youtube":
                return await self._get_youtube_analytics()
            
        except Exception as e:
            logger.error(f"❌ Platform analytics failed for {platform_name}: {e}")
            return {"error": str(e)}
    
    async def _get_twitter_analytics(self) -> Dict[str, Any]:
        """Get Twitter analytics"""
        try:
            config = self.platforms["twitter"]
            headers = {"Authorization": f"Bearer {config['bearer_token']}"}
            
            # Get user metrics
            response = requests.get(f"{config['api_base']}/users/me", headers=headers, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                
                # Get recent tweets metrics
                tweets_response = requests.get(f"{config['api_base']}/users/me/tweets?max_results=100", headers=headers, timeout=10)
                if tweets_response.status_code == 200:
                    tweets_data = tweets_response.json()
                    
                    # Calculate engagement metrics
                    total_engagement = 0
                    total_impressions = 0
                    for tweet in tweets_data.get("data", []):
                        total_engagement += tweet.get("public_metrics", {}).get("like_count", 0) + \
                                          tweet.get("public_metrics", {}).get("retweet_count", 0) + \
                                          tweet.get("public_metrics", {}).get("reply_count", 0)
                        total_impressions += tweet.get("public_metrics", {}).get("impression_count", 0)
                    
                    return {
                        "followers": user_data.get("public_metrics", {}).get("followers_count", 0),
                        "following": user_data.get("public_metrics", {}).get("following_count", 0),
                        "total_tweets": user_data.get("public_metrics", {}).get("tweet_count", 0),
                        "total_engagement": total_engagement,
                        "total_impressions": total_impressions,
                        "avg_engagement_rate": (total_engagement / total_impressions * 100) if total_impressions > 0 else 0,
                        "platform": "twitter"
                    }
            
            return {"error": "Failed to retrieve Twitter analytics"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_linkedin_analytics(self) -> Dict[str, Any]:
        """Get LinkedIn analytics"""
        try:
            config = self.platforms["linkedin"]
            headers = {"Authorization": f"Bearer {config['access_token']}"}
            
            # Get profile analytics
            response = requests.get(f"{config['api_base']}/me", headers=headers, timeout=10)
            if response.status_code == 200:
                profile_data = response.json()
                
                # Get post analytics
                posts_response = requests.get(f"{config['api_base']}/ugcPosts?q=authors&authors=List(urn:li:person:{config['person_id']})&count=100", headers=headers, timeout=10)
                if posts_response.status_code == 200:
                    posts_data = posts_response.json()
                    
                    # Calculate engagement metrics
                    total_engagement = 0
                    total_impressions = 0
                    for post in posts_data.get("elements", []):
                        # Extract engagement data from post analytics
                        total_engagement += post.get("socialDetail", {}).get("numLikes", 0) + \
                                          post.get("socialDetail", {}).get("numComments", 0)
                        total_impressions += post.get("socialDetail", {}).get("numImpressions", 0)
                    
                    return {
                        "followers": profile_data.get("numFollowers", 0),
                        "connections": profile_data.get("numConnections", 0),
                        "total_posts": len(posts_data.get("elements", [])),
                        "total_engagement": total_engagement,
                        "total_impressions": total_impressions,
                        "avg_engagement_rate": (total_engagement / total_impressions * 100) if total_impressions > 0 else 0,
                        "platform": "linkedin"
                    }
            
            return {"error": "Failed to retrieve LinkedIn analytics"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_facebook_analytics(self) -> Dict[str, Any]:
        """Get Facebook analytics"""
        try:
            config = self.platforms["facebook"]
            params = {"access_token": config["page_access_token"]}
            
            # Get page metrics
            response = requests.get(f"{config['api_base']}/{config['page_id']}?fields=fan_count,posts.limit(100)", params=params, timeout=10)
            if response.status_code == 200:
                page_data = response.json()
                
                # Calculate engagement metrics
                total_engagement = 0
                total_reach = 0
                for post in page_data.get("posts", {}).get("data", []):
                    # Get post insights
                    insights_response = requests.get(f"{config['api_base']}/{post['id']}/insights?metric=post_engaged_users,post_impressions", params=params, timeout=10)
                    if insights_response.status_code == 200:
                        insights_data = insights_response.json()
                        for metric in insights_data.get("data", []):
                            if metric["name"] == "post_engaged_users":
                                total_engagement += metric["values"][0]["value"] if metric["values"] else 0
                            elif metric["name"] == "post_impressions":
                                total_reach += metric["values"][0]["value"] if metric["values"] else 0
                
                return {
                    "followers": page_data.get("fan_count", 0),
                    "total_posts": len(page_data.get("posts", {}).get("data", [])),
                    "total_engagement": total_engagement,
                    "total_reach": total_reach,
                    "avg_engagement_rate": (total_engagement / total_reach * 100) if total_reach > 0 else 0,
                    "platform": "facebook"
                }
            
            return {"error": "Failed to retrieve Facebook analytics"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_instagram_analytics(self) -> Dict[str, Any]:
        """Get Instagram analytics"""
        try:
            config = self.platforms["instagram"]
            params = {"access_token": config["access_token"]}
            
            # Get account metrics
            response = requests.get(f"{config['api_base']}/{config['business_account']}?fields=followers_count,media_count", params=params, timeout=10)
            if response.status_code == 200:
                account_data = response.json()
                
                # Get media analytics
                media_response = requests.get(f"{config['api_base']}/{config['business_account']}/media?fields=like_count,comments_count,impressions", params=params, timeout=10)
                if media_response.status_code == 200:
                    media_data = media_response.json()
                    
                    # Calculate engagement metrics
                    total_engagement = 0
                    total_impressions = 0
                    for media in media_data.get("data", []):
                        total_engagement += media.get("like_count", 0) + media.get("comments_count", 0)
                        total_impressions += media.get("impressions", 0)
                    
                    return {
                        "followers": account_data.get("followers_count", 0),
                        "total_posts": account_data.get("media_count", 0),
                        "total_engagement": total_engagement,
                        "total_impressions": total_impressions,
                        "avg_engagement_rate": (total_engagement / total_impressions * 100) if total_impressions > 0 else 0,
                        "platform": "instagram"
                    }
            
            return {"error": "Failed to retrieve Instagram analytics"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_youtube_analytics(self) -> Dict[str, Any]:
        """Get YouTube analytics"""
        try:
            config = self.platforms["youtube"]
            params = {
                "key": config["api_key"],
                "part": "statistics",
                "id": config["channel_id"]
            }
            
            # Get channel statistics
            response = requests.get(f"{config['api_base']}/channels", params=params, timeout=10)
            if response.status_code == 200:
                channel_data = response.json()
                
                if channel_data.get("items"):
                    stats = channel_data["items"][0]["statistics"]
                    
                    return {
                        "subscribers": int(stats.get("subscriberCount", 0)),
                        "total_views": int(stats.get("viewCount", 0)),
                        "total_videos": int(stats.get("videoCount", 0)),
                        "platform": "youtube"
                    }
            
            return {"error": "Failed to retrieve YouTube analytics"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _check_rate_limit(self, platform_name: str, action_type: str) -> bool:
        """Check if rate limit allows the action"""
        try:
            limits = self.rate_limits[platform_name]
            usage = self.daily_usage[platform_name]
            
            # Reset daily counters if needed
            current_date = datetime.now().strftime("%Y-%m-%d")
            if usage["date"] != current_date:
                usage["date"] = current_date
                usage["posts"] = 0
                usage["engagements"] = 0
                limits["posts_used"] = 0
                limits["engagements_used"] = 0
            
            if action_type == "post":
                return usage["posts"] < limits["post_limit"]
            elif action_type == "engagement":
                return usage["engagements"] < limits["engagement_limit"]
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Rate limit check failed: {e}")
            return False
    
    async def _update_rate_limit(self, platform_name: str, action_type: str):
        """Update rate limit usage"""
        try:
            usage = self.daily_usage[platform_name]
            if action_type == "post":
                usage["posts"] += 1
            elif action_type == "engagement":
                usage["engagements"] += 1
                
        except Exception as e:
            logger.error(f"❌ Rate limit update failed: {e}")
    
    async def _track_post_analytics(self, platform_name: str, content: str, result: Dict[str, Any]):
        """Track post analytics"""
        try:
            analytics = {
                "platform": platform_name,
                "content": content[:100],  # Truncate long content
                "post_id": result.get("post_id"),
                "timestamp": datetime.now().isoformat(),
                "success": result.get("success", False),
                "error": result.get("error")
            }
            
            self.post_analytics.append(analytics)
            
            # Log transparency event
            log_transparency(
                "social_post",
                "tracked",
                {
                    "platform": platform_name,
                    "post_id": result.get("post_id"),
                    "success": result.get("success", False)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Post analytics tracking failed: {e}")
    
    async def _track_engagement_analytics(self, platform_name: str, action: str, target_id: str, result: Dict[str, Any]):
        """Track engagement analytics"""
        try:
            analytics = {
                "platform": platform_name,
                "action": action,
                "target_id": target_id,
                "timestamp": datetime.now().isoformat(),
                "success": result.get("success", False),
                "error": result.get("error")
            }
            
            self.engagement_analytics.append(analytics)
            
        except Exception as e:
            logger.error(f"❌ Engagement analytics tracking failed: {e}")
    
    async def start(self):
        """Start the social media integration system"""
        self.is_running = True
        logger.info("📱 Starting Real Social Media Integration System...")
        
        # Start background tasks
        asyncio.create_task(self._background_analytics_update())
        asyncio.create_task(self._background_rate_limit_reset())
        
        logger.info("✅ Social media integration system running")
        
        # Keep running
        while self.is_running:
            await asyncio.sleep(60)
    
    async def _background_analytics_update(self):
        """Background task to update analytics"""
        while self.is_running:
            try:
                # Update analytics every hour
                for platform_name, config in self.platforms.items():
                    if config["enabled"]:
                        analytics = await self._get_platform_analytics(platform_name)
                        if "error" not in analytics:
                            self.follower_analytics.append({
                                "platform": platform_name,
                                "timestamp": datetime.now().isoformat(),
                                "data": analytics
                            })
                
                await asyncio.sleep(3600)  # Hourly update
                
            except Exception as e:
                logger.error(f"❌ Background analytics update error: {e}")
                await asyncio.sleep(7200)
    
    async def _background_rate_limit_reset(self):
        """Background task to reset rate limits"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Reset daily rate limits at midnight
                for platform_name in self.platforms:
                    limits = self.rate_limits[platform_name]
                    if current_time >= limits["reset_time"]:
                        limits["posts_used"] = 0
                        limits["engagements_used"] = 0
                        limits["reset_time"] = current_time + timedelta(days=1)
                
                await asyncio.sleep(3600)  # Check hourly
                
            except Exception as e:
                logger.error(f"❌ Background rate limit reset error: {e}")
                await asyncio.sleep(3600)
    
    async def stop(self):
        """Stop the social media integration system"""
        self.is_running = False
        logger.info("📱 Stopping Real Social Media Integration System...")
        
        # Save data
        await self._save_social_data()
        
        logger.info("✅ Social media integration system stopped")
    
    async def _save_social_data(self):
        """Save social media data"""
        data = {
            "post_analytics": self.post_analytics,
            "engagement_analytics": self.engagement_analytics,
            "follower_analytics": self.follower_analytics,
            "last_updated": datetime.now().isoformat()
        }
        
        data_file = Path("generated_content") / "social_media_data.json"
        data_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(data_file, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Social media data saved to {data_file}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get social media integration system status"""
        enabled_platforms = sum(1 for config in self.platforms.values() if config["enabled"])
        
        return {
            "status": "running" if self.is_running else "stopped",
            "enabled_platforms": enabled_platforms,
            "total_posts": len(self.post_analytics),
            "total_engagements": len(self.engagement_analytics),
            "total_analytics_updates": len(self.follower_analytics),
            "platforms": {
                name: {
                    "enabled": config["enabled"],
                    "posts_today": self.daily_usage[name]["posts"],
                    "engagements_today": self.daily_usage[name]["engagements"],
                    "post_limit": config["post_limit"],
                    "engagement_limit": config["engagement_limit"]
                }
                for name, config in self.platforms.items()
            }
        }

# Global instance
real_social_media = RealSocialMediaIntegration()

async def main():
    """Test the social media integration system"""
    if await real_social_media.initialize():
        await real_social_media.start()

if __name__ == "__main__":
    print("📱 REAL SOCIAL MEDIA INTEGRATION SYSTEM")
    print("=" * 60)
    print("Complete social media API integration for CHATTY")
    print("Multi-platform support with real posting and analytics")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        asyncio.run(real_social_media.stop())