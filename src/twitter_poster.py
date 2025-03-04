# src/twitter/twitter_poster.py
import os
import logging
import tweepy
import random
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List

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
        
        # Import other components
        self.ai_analyzer = self._import_component('src.ai_analyzer', 'AIAnalyzer')
        self.tweet_generator = self._import_component('src.nlp_tweet_generator', 'NLPTweetGenerator')
        self.blockchain_monitor = self._import_component('src.blockchain_monitor', 'BlockchainMonitor')
        
        # Validate Twitter credentials
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            self.logger.error("Missing Twitter API credentials")
            raise ValueError("Missing Twitter API credentials")
            
        # Initialize Twitter client
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
        
        # Template patterns for variety when AI generation fails
        self.tweet_templates = [
            "📊 #MultiversX Network Update | {time}\n\n💰 EGLD: ${price}\n🔢 Transactions: {txs}\n👥 Accounts: {accounts}\n\n#EGLD",
            "🚀 #MultiversX Ecosystem Report\n\n$EGLD: ${price}\n📈 {txs} transactions\n👨‍💻 {accounts} accounts\n\n#Web3 #Blockchain",
            "#MultiversX Stats | {time}\n\nEGLD Price: ${price}\nTotal Transactions: {txs}\nTotal Accounts: {accounts}\n\n#EGLD #Crypto",
            "⚡ MultiversX Network Pulse ⚡\n\nEGLD: ${price}\nTransactions: {txs}\nAccounts: {accounts}\n\n#MultiversX #EGLD"
        ]
        self.last_template_index = -1

    def _import_component(self, module_path, class_name):
        """Dynamically import a component if it exists"""
        try:
            module = __import__(module_path, fromlist=[class_name])
            component_class = getattr(module, class_name)
            return component_class()
        except (ImportError, AttributeError):
            self.logger.warning(f"Could not import {class_name} from {module_path}")
            return None
        except Exception as e:
            self.logger.warning(f"Error initializing {class_name}: {str(e)}")
            return None
        
    async def verify_connection(self) -> bool:
        """Async wrapper for verifying Twitter connection"""
        return self.client.verify_connection()
    
    async def generate_tweet_content(self, price=None, stats=None, events=None) -> str:
        """Generate tweet content based on blockchain data using NLP Generator if available"""
        try:
            # Try using the NLP Tweet Generator component if available
            if self.tweet_generator:
                content = await self.tweet_generator.generate_tweet({
                    'price': price,
                    'transactions': stats.get('transactions') if stats else None,
                    'accounts': stats.get('accounts') if stats else None,
                    'events': events
                })
                
                if content:
                    self.logger.info("Generated tweet content using NLP Tweet Generator")
                    return content
                    
            # If no content was generated or no generator available, use templates
            # Get new template (different from the last one used)
            template_index = random.randint(0, len(self.tweet_templates) - 1)
            while template_index == self.last_template_index and len(self.tweet_templates) > 1:
                template_index = random.randint(0, len(self.tweet_templates) - 1)
                
            self.last_template_index = template_index
            template = self.tweet_templates[template_index]
            
            # Format the template with data
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add commas to large numbers for readability
            txs_formatted = f"{stats.get('transactions', 0):,}" if stats and 'transactions' in stats else "N/A"
            accounts_formatted = f"{stats.get('accounts', 0):,}" if stats and 'accounts' in stats else "N/A"
            
            content = template.format(
                time=current_time,
                price=price if price else "N/A",
                txs=txs_formatted,
                accounts=accounts_formatted
            )
            
            self.logger.info(f"Generated tweet content using template #{template_index+1}")
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating tweet content: {str(e)}")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"#MultiversX Update | {current_time}\n\nEGLD: ${price if price else 'N/A'}\nTransactions: {stats.get('transactions', 'N/A') if stats else 'N/A'}\nAccounts: {stats.get('accounts', 'N/A') if stats else 'N/A'}\n\n#EGLD"
        
    async def post_tweet(self, content=None, price=None, stats=None, events=None) -> Optional[str]:
        """Post a tweet to Twitter using API"""
        try:
            # Generate tweet content if not provided
            if not content:
                content = await self.generate_tweet_content(price, stats, events)
                
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
        except Exception as e:
            self.logger.error(f"Error in post_tweet: {str(e)}")
            return None
        
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