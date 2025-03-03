#!/usr/bin/env python
# src/twitter/twitter_api_poster.py

import os
import tweepy
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

class TwitterAPIClient:
    """Twitter API client that handles authentication and posting tweets"""
    
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        """Initialize the Twitter API client with credentials"""
        self.logger = logging.getLogger("twitter_api_client")
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.client = None
        self.api = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Tweepy client and API"""
        try:
            # Initialize v2 client for newer endpoints
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Initialize v1.1 API for some features not available in v2
            auth = tweepy.OAuth1UserHandler(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            self.api = tweepy.API(auth)
            
            # Verify credentials
            self.api.verify_credentials()
            self.logger.info("Twitter API client initialized successfully")
            
        except tweepy.errors.Unauthorized:
            self.logger.error("Twitter authentication failed - check your credentials")
            raise ValueError("Twitter authentication failed")
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter client: {str(e)}")
            raise
            
    def verify_connection(self) -> bool:
        """Verify that the API connection is working"""
        try:
            user = self.client.get_me()
            return user is not None
        except Exception as e:
            self.logger.error(f"Twitter connection verification failed: {str(e)}")
            return False
            
    def post_tweet(self, content: str) -> Optional[str]:
        """Post a tweet and return the tweet ID if successful"""
        try:
            response = self.client.create_tweet(text=content)
            tweet_id = response.data['id']
            self.logger.info(f"Tweet posted successfully. ID: {tweet_id}")
            return tweet_id
        except tweepy.errors.TooManyRequests:
            self.logger.error("Rate limit exceeded when posting tweet")
            return None
        except tweepy.errors.Forbidden as e:
            self.logger.error(f"Tweet rejected by Twitter: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error posting tweet: {str(e)}")
            return None
            
    def post_tweet_with_media(self, content: str, media_path: str) -> Optional[str]:
        """Post a tweet with media attachment"""
        try:
            # Upload media using v1.1 API
            media = self.api.media_upload(media_path)
            media_id = media.media_id
            
            # Post tweet with media using v2 API
            response = self.client.create_tweet(
                text=content,
                media_ids=[media_id]
            )
            
            tweet_id = response.data['id']
            self.logger.info(f"Tweet with media posted successfully. ID: {tweet_id}")
            return tweet_id
            
        except Exception as e:
            self.logger.error(f"Error posting tweet with media: {str(e)}")
            return None
            
    def reply_to_tweet(self, tweet_id: str, content: str) -> Optional[str]:
        """Reply to a specific tweet"""
        try:
            response = self.client.create_tweet(
                text=content,
                in_reply_to_tweet_id=tweet_id
            )
            reply_id = response.data['id']
            self.logger.info(f"Reply posted successfully. ID: {reply_id}")
            return reply_id
        except Exception as e:
            self.logger.error(f"Error posting reply: {str(e)}")
            return None
            
    def get_tweet_metrics(self, tweet_id: str) -> Dict[str, Any]:
        """Get metrics for a specific tweet"""
        try:
            # Get tweet with metrics
            tweet = self.client.get_tweet(
                tweet_id,
                tweet_fields=['public_metrics', 'created_at']
            )
            
            if not tweet or not tweet.data:
                return {}
                
            metrics = tweet.data.public_metrics
            created_at = tweet.data.created_at
            
            return {
                'likes': metrics.get('like_count', 0),
                'retweets': metrics.get('retweet_count', 0),
                'replies': metrics.get('reply_count', 0),
                'quotes': metrics.get('quote_count', 0),
                'impressions': metrics.get('impression_count', 0),
                'created_at': created_at.isoformat() if created_at else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tweet metrics: {str(e)}")
            return {}

class TwitterPoster:
    """Main Twitter poster class for the MultiversX AI Bot"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, 
                 access_token: str = None, access_token_secret: str = None):
        """Initialize the Twitter poster with API credentials"""
        self.logger = logging.getLogger("twitter_poster")
        
        # Load credentials from environment if not provided
        self.api_key = api_key or os.getenv('TWITTER_API_KEY')
        self.api_secret = api_secret or os.getenv('TWITTER_API_SECRET')
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = access_token_secret or os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        # Validate credentials
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            self.logger.error("Missing Twitter API credentials")
            raise ValueError("Missing Twitter API credentials")
            
        # Initialize client
        self.client = TwitterAPIClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
        
        # Track posting rate limits
        self.last_post_time = None
        self.post_count_today = 0
        self.max_posts_per_day = 50  # Default limit
        
    async def verify_connection(self) -> bool:
        """Async wrapper for verifying Twitter connection"""
        return self.client.verify_connection()
        
    async def post_tweet(self, content: str) -> Optional[str]:
        """Post a tweet to Twitter using API"""
        # Check rate limits
        if not self._check_rate_limits():
            self.logger.warning("Rate limit would be exceeded - not posting tweet")
            return None
            
        # Post the tweet
        tweet_id = self.client.post_tweet(content)
        
        # Update rate limit tracking
        if tweet_id:
            self._update_rate_tracking()
            
        return tweet_id
        
    async def post_tweet_with_media(self, content: str, media_path: str) -> Optional[str]:
        """Post a tweet with media attachment"""
        # Check rate limits
        if not self._check_rate_limits():
            self.logger.warning("Rate limit would be exceeded - not posting tweet with media")
            return None
            
        # Post the tweet with media
        tweet_id = self.client.post_tweet_with_media(content, media_path)
        
        # Update rate limit tracking
        if tweet_id:
            self._update_rate_tracking()
            
        return tweet_id
        
    async def reply_to_tweet(self, tweet_id: str, content: str) -> Optional[str]:
        """Reply to a specific tweet"""
        # Check rate limits
        if not self._check_rate_limits():
            self.logger.warning("Rate limit would be exceeded - not posting reply")
            return None
            
        # Post the reply
        reply_id = self.client.reply_to_tweet(tweet_id, content)
        
        # Update rate limit tracking
        if reply_id:
            self._update_rate_tracking()
            
        return reply_id
        
    async def get_tweet_metrics(self, tweet_id: str) -> Dict[str, Any]:
        """Get metrics for a specific tweet"""
        return self.client.get_tweet_metrics(tweet_id)
        
    def _check_rate_limits(self) -> bool:
        """Check if posting would exceed rate limits"""
        current_time = datetime.now()
        
        # Check if we've exceeded daily limit
        today = current_time.date()
        if self.last_post_time:
            last_post_date = self.last_post_time.date()
            if last_post_date == today and self.post_count_today >= self.max_posts_per_day:
                self.logger.warning(f"Daily post limit of {self.max_posts_per_day} would be exceeded")
                return False
            elif last_post_date != today:
                # Reset counter for new day
                self.post_count_today = 0
                
        # Avoid posting too frequently (at least 30 seconds between posts)
        if self.last_post_time and (current_time - self.last_post_time).total_seconds() < 30:
            self.logger.warning("Posting too frequently - minimum 30 second gap required")
            return False
            
        return True
        
    def _update_rate_tracking(self):
        """Update rate limit tracking after successful post"""
        self.last_post_time = datetime.now()
        self.post_count_today += 1
        self.logger.info(f"Rate limit tracking updated: {self.post_count_today} posts today")
        
    async def close(self):
        """Clean up resources"""
        # Nothing to clean up with Twitter API client
        pass

# Debug script
async def test_twitter_poster():
    """Test the Twitter poster functionality"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("twitter_test")
    
    try:
        # Create poster
        poster = TwitterPoster()
        
        # Verify connection
        logger.info("Verifying Twitter connection...")
        if not await poster.verify_connection():
            logger.error("Failed to connect to Twitter API")
            return
            
        # Post test tweet
        test_content = f"MultiversX AI Bot - Test tweet at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(f"Posting test tweet: {test_content}")
        
        tweet_id = await poster.post_tweet(test_content)
        
        if tweet_id:
            logger.info(f"Test tweet posted successfully with ID: {tweet_id}")
            logger.info(f"View at: https://twitter.com/anyuser/status/{tweet_id}")
        else:
            logger.error("Failed to post test tweet")
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)
    finally:
        if 'poster' in locals():
            await poster.close()

if __name__ == "__main__":
    asyncio.run(test_twitter_poster())