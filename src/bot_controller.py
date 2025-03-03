import os
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Any

from twitter_scraper import TwitterScraper
from ai_analyzer import TweetAnalyzer
from blockchain_fetcher import BlockchainFetcher
from response_generator import ResponseGenerator
from twitter_poster import TwitterPoster
from tweet_analytics import TweetAnalytics
from sentiment_analyzer import SentimentAnalyzer
from blockchain_monitor import BlockchainMonitor
from tweet_scheduler import TweetScheduler
from twitter_api_poster import TwitterAPIPoster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotController:
    def __init__(self, data_dir="data"):
        """
        Main controller for the Twitter bot
        
        Args:
            data_dir (str): Directory to store bot data
        """
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "bot_config.json")
        
        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load or create config
        self.config = self._load_config()
        
        # Initialize components
        self.twitter_scraper = TwitterScraper()
        self.tweet_analyzer = TweetAnalyzer()
        self.blockchain_fetcher = BlockchainFetcher(network=self.config.get("network", "devnet"))
        self.response_generator = ResponseGenerator()
        self.twitter_poster = TwitterPoster()
        self.analytics = TweetAnalytics(data_dir=data_dir)
        self.twitter_api_poster = TwitterAPIPoster()
        
        # New features
        self.sentiment_analyzer = SentimentAnalyzer()
        self.blockchain_monitor = BlockchainMonitor(
            data_dir=data_dir,
            network=self.config.get("network", "devnet"), 
            callback=self._handle_blockchain_event
        )
        self.tweet_scheduler = TweetScheduler(
            data_dir=data_dir,
            callback=self._handle_scheduled_tweet
        )
        
        # State
        self.running = False
        self.main_thread = None
        self.processed_tweets = set()
        
        logger.info("Bot controller initialized")
    
    def _load_config(self) -> Dict:
        """
        Load bot configuration
        
        Returns:
            Dict: Bot configuration
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        config = {
            "bot_enabled": True,
            "check_interval": 60,  # seconds
            "tweet_limit": 10,
            "search_terms": ["MultiversX"],
            "network": "devnet",
            "scheduled_tweets": [],
            "blacklisted_users": [],
            "auto_retweet_keywords": [],
            "sentiment_analysis_enabled": False,
            "proactive_monitoring": {
                "enabled": False,
                "price_change_threshold": 5.0,  # percentage
                "transaction_volume_threshold": 1000000,  # in USD
            }
        }
        
        # Save default config
        self._save_config(config)
        return config
    
    def _save_config(self, config: Dict) -> bool:
        """
        Save bot configuration
        
        Args:
            config (Dict): Bot configuration
            
        Returns:
            bool: Success status
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Bot configuration saved")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def apply_config(self, config: Dict) -> bool:
        """
        Apply a new configuration
        
        Args:
            config (Dict): New configuration
            
        Returns:
            bool: Success status
        """
        # Update the configuration
        self.config.update(config)
        
        # Apply network change if needed
        if "network" in config and config["network"] != self.blockchain_fetcher.network:
            self.blockchain_fetcher = BlockchainFetcher(network=config["network"])
            self.blockchain_monitor.stop()
            self.blockchain_monitor = BlockchainMonitor(
                data_dir=self.data_dir,
                network=config["network"], 
                callback=self._handle_blockchain_event
            )
            
            # Restart blockchain monitor if it was running
            if config["proactive_monitoring"]["enabled"]:
                self.blockchain_monitor.start()
        
        # Apply monitoring settings
        if "proactive_monitoring" in config:
            monitoring_config = config["proactive_monitoring"]
            
            # Set monitoring thresholds
            thresholds = {
                "price_change_percent": monitoring_config.get("price_change_threshold", 5.0),
                "transaction_volume_usd": monitoring_config.get("transaction_volume_threshold", 1000000)
            }
            self.blockchain_monitor.set_thresholds(thresholds)
            
            # Start/stop monitoring based on config
            if monitoring_config.get("enabled", False):
                if not self.blockchain_monitor.is_running():
                    self.blockchain_monitor.start()
            else:
                if self.blockchain_monitor.is_running():
                    self.blockchain_monitor.stop()
        
        # Save the updated config
        success = self._save_config(self.config)
        
        return success
    
    def _handle_blockchain_event(self, event: Dict):
        """
        Handle a blockchain event
        
        Args:
            event (Dict): Event data
        """
        logger.info(f"Handling blockchain event: {event['type']}")
        
        try:
            # Generate message for the event
            message = self.blockchain_monitor.generate_event_message(event)
            
            # Post to Twitter
            if message:
                success = self.twitter_poster.post_tweet(message)
                if success:
                    logger.info(f"Posted blockchain event tweet: {message}")
                else:
                    logger.error(f"Failed to post blockchain event tweet")
        except Exception as e:
            logger.error(f"Error handling blockchain event: {e}")
    
    def _handle_scheduled_tweet(self, content: str):
        """
        Handle a scheduled tweet
        
        Args:
            content (str): Tweet content
        """
        logger.info(f"Handling scheduled tweet: {content[:30]}...")
        
        try:
            # Post to Twitter
            success = self.twitter_poster.post_tweet(content)
            if success:
                logger.info(f"Posted scheduled tweet")
            else:
                logger.error(f"Failed to post scheduled tweet")
        except Exception as e:
            logger.error(f"Error handling scheduled tweet: {e}")
    
    def process_tweet(self, tweet: Dict):
        """
        Process a single tweet
        
        Args:
            tweet (Dict): Tweet data
            
        Returns:
            bool: Success status
        """
        tweet_id = tweet.get('id')
        tweet_text = tweet.get('text')
        username = tweet.get('username')
        
        try:
            # Classify the tweet
            classification = self.tweet_analyzer.classify_tweet(tweet_text)
            
            # Perform sentiment analysis if enabled
            sentiment_data = None
            if self.config.get("sentiment_analysis_enabled", False):
                sentiment_data = self.sentiment_analyzer.analyze_sentiment(tweet_text)
                logger.info(f"Sentiment analysis: {sentiment_data['sentiment']} ({sentiment_data['sentiment_score']})")
            
            # Fetch blockchain data based on classification
            blockchain_data = {}
            
            if classification == "price inquiry":
                # Get EGLD price
                price = self.blockchain_fetcher.get_egld_price()
                blockchain_data["price"] = price
                
                # Get additional network stats
                stats = self.blockchain_fetcher.get_network_stats()
                if stats:
                    blockchain_data["network_stats"] = stats
            
            elif classification == "nft mention":
                # Extract and get NFT details
                nft_id = self.tweet_analyzer.extract_nft_identifier(tweet_text)
                if nft_id:
                    nft_data = self.blockchain_fetcher.get_nft_details(nft_id)
                    blockchain_data["nft"] = nft_data
                    
                    # Get collection details if NFT found
                    if nft_data and "collection" in nft_data:
                        collection_data = self.blockchain_fetcher.get_collection_details(nft_data["collection"])
                        blockchain_data["collection"] = collection_data
            
            elif classification == "balance inquiry":
                # Extract and get address balance
                address = self.tweet_analyzer.extract_address(tweet_text)
                if address:
                    balance = self.blockchain_fetcher.get_balance(address)
                    blockchain_data["balance"] = balance
                    
                    # Get tokens and NFTs for richer response
                    tokens = self.blockchain_fetcher.get_account_tokens(address)
                    if tokens:
                        blockchain_data["tokens"] = tokens
                    
                    nfts = self.blockchain_fetcher.get_account_nfts(address, limit=5)
                    if nfts:
                        blockchain_data["nfts"] = nfts
            
            # Generate response based on sentiment if available
            if sentiment_data:
                response = self.sentiment_analyzer.create_targeted_response(
                    tweet_text,
                    classification,
                    blockchain_data,
                    sentiment_data
                )
            else:
                # Use standard response generator
                response = self.response_generator.generate_response(
                    classification, 
                    blockchain_data,
                    username
                )
            
            # Try to post using the API first, fall back to Selenium if needed
            success = False
            if self.twitter_api_poster.is_available():
                success = self.twitter_api_poster.post_reply(tweet_id, response)
            
            # Fall back to Selenium if API posting fails
            if not success:
                success = self.twitter_poster.post_reply(tweet_id, response)
            
            if success:
                logger.info(f"Successfully replied to tweet {tweet_id}")
                
                # Record interaction in analytics
                self.analytics.record_interaction(
                    tweet, 
                    classification, 
                    response, 
                    blockchain_data,
                    sentiment_data=sentiment_data if sentiment_data else None
                )
                
                return True
            else:
                logger.error(f"Failed to reply to tweet {tweet_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing tweet {tweet_id}: {e}")
            return False
    
    def send_manual_tweet(self, content: str) -> bool:
        """
        Send a manual tweet
        
        Args:
            content (str): Tweet content
            
        Returns:
            bool: Success status
        """
        try:
            success = self.twitter_poster.post_tweet(content)
            if success:
                logger.info(f"Successfully sent manual tweet")
                return True
            else:
                logger.error(f"Failed to send manual tweet")
                return False
        except Exception as e:
            logger.error(f"Error sending manual tweet: {e}")
            return False
    
    def _main_loop(self):
        """Main bot loop"""
        logger.info("Starting main bot loop")
        
        # Log in to Twitter
        twitter_username = os.getenv("TWITTER_USERNAME")
        twitter_password = os.getenv("TWITTER_PASSWORD")
        
        logged_in = self.twitter_poster.login_to_twitter(twitter_username, twitter_password)
        if not logged_in:
            logger.error("Failed to log in to Twitter. Exiting main loop.")
            self.running = False
            return
        
        while self.running:
            try:
                if not self.config.get("bot_enabled", True):
                    logger.info("Bot is disabled, skipping check cycle")
                    time.sleep(10)
                    continue
                
                logger.info("Checking for new tweets...")
                
                # Get tweets mentioning MultiversX
                search_terms = self.config.get("search_terms", ["MultiversX"])
                tweet_limit = self.config.get("tweet_limit", 10)
                
                for term in search_terms:
                    tweets = self.twitter_scraper.get_tweets(search_term=term, limit=tweet_limit)
                    
                    for tweet in tweets:
                        tweet_id = tweet.get('id')
                        username = tweet.get('username')
                        
                        # Skip if we've already processed this tweet or if the user is blacklisted
                        if tweet_id in self.processed_tweets:
                            continue
                        
                        if username in self.config.get("blacklisted_users", []):
                            logger.info(f"Skipping blacklisted user: {username}")
                            self.processed_tweets.add(tweet_id)
                            continue
                        
                        logger.info(f"Processing tweet {tweet_id} from {username}")
                        
                        # Process the tweet
                        success = self.process_tweet(tweet)
                        
                        if success:
                            self.processed_tweets.add(tweet_id)
                
                # Wait before checking for new tweets again
                check_interval = self.config.get("check_interval", 60)
                logger.info(f"Waiting for {check_interval} seconds before checking for new tweets...")
                
                # Use smaller sleep intervals to allow for quicker shutdown
                for _ in range(check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait a bit longer if there was an error
    
    def start(self):
        """Start the Twitter bot"""
        if not self.running:
            self.running = True
            
            # Start the main thread
            self.main_thread = threading.Thread(target=self._main_loop)
            self.main_thread.daemon = True
            self.main_thread.start()
            
            # Start the blockchain monitor if enabled
            if self.config.get("proactive_monitoring", {}).get("enabled", False):
                self.blockchain_monitor.start()
            
            # Start the tweet scheduler
            self.tweet_scheduler.start()
            
            logger.info("Bot started")
            return True
        return False
    
    def stop(self):
        """Stop the Twitter bot"""
        if self.running:
            self.running = False
            
            # Stop the main thread
            if self.main_thread:
                self.main_thread.join(timeout=5)
            
            # Stop the blockchain monitor
            if self.blockchain_monitor.is_running():
                self.blockchain_monitor.stop()
            
            # Stop the tweet scheduler
            if self.tweet_scheduler.is_running():
                self.tweet_scheduler.stop()
            
            logger.info("Bot stopped")
            return True
        return False
    
    def restart(self):
        """Restart the Twitter bot"""
        logger.info("Restarting bot...")
        self.stop()
        time.sleep(1)
        return self.start()
    
    def is_running(self):
        """Check if the bot is running"""
        return self.running and (self.main_thread is not None) and self.main_thread.is_alive()