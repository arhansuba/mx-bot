import logging
import tweepy
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TwitterAPIPoster:
    def __init__(self):
        """Initialize the Twitter API poster with credentials from .env"""
        try:
            # Get Twitter API credentials from environment variables
            self.consumer_key = os.getenv("TWITTER_API_KEY")
            self.consumer_secret = os.getenv("TWITTER_API_SECRET")
            self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            self.access_token_secret = os.getenv("TWITTER_ACCESS_SECRET")
            
            if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
                logger.warning("Twitter API credentials not fully configured in .env file")
                self.api_available = False
                return
                
            # Initialize the Tweepy API
            auth = tweepy.OAuth1UserHandler(
                self.consumer_key, self.consumer_secret,
                self.access_token, self.access_token_secret
            )
            self.api = tweepy.API(auth)
            
            # Verify credentials
            self.api.verify_credentials()
            self.api_available = True
            logger.info("Twitter API initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Twitter API: {e}")
            self.api_available = False
    
    def is_available(self):
        """Check if Twitter API is available"""
        return self.api_available
    
    def post_tweet(self, content):
        """
        Post a tweet using the Twitter API
        
        Args:
            content (str): Tweet content
            
        Returns:
            bool: Success status
        """
        if not self.api_available:
            logger.warning("Twitter API not available for posting")
            return False
            
        try:
            self.api.update_status(content)
            logger.info(f"Successfully posted tweet via API: {content[:30]}...")
            return True
        except Exception as e:
            logger.error(f"Error posting tweet via API: {e}")
            return False
    
    def post_reply(self, tweet_id, content):
        """
        Post a reply to a tweet using the Twitter API
        
        Args:
            tweet_id (str): ID of the tweet to reply to
            content (str): Reply content
            
        Returns:
            bool: Success status
        """
        if not self.api_available:
            logger.warning("Twitter API not available for posting replies")
            return False
            
        try:
            self.api.update_status(
                status=content,
                in_reply_to_status_id=tweet_id,
                auto_populate_reply_metadata=True
            )
            logger.info(f"Successfully posted reply via API to tweet {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Error posting reply via API: {e}")
            return False
