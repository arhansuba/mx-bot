import os
import json
import time
import logging
import datetime
import threading
from typing import Dict, List, Optional, Any, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TweetScheduler:
    def __init__(self, data_dir="data", callback=None):
        """
        Initialize the tweet scheduler
        
        Args:
            data_dir (str): Directory to store scheduler data
            callback (Callable): Callback function for scheduled tweets
        """
        self.data_dir = data_dir
        self.scheduler_dir = os.path.join(data_dir, "scheduler")
        self.scheduler_file = os.path.join(self.scheduler_dir, "scheduled_tweets.json")
        self.callback = callback
        self.running = False
        self.scheduler_thread = None
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.scheduler_dir, exist_ok=True)
        
        # Load scheduled tweets
        self.scheduled_tweets = self._load_scheduled_tweets()
        
        logger.info(f"Tweet scheduler initialized with {len(self.scheduled_tweets)} scheduled tweets")
    
    def _load_scheduled_tweets(self) -> List[Dict]:
        """
        Load scheduled tweets from file
        
        Returns:
            List[Dict]: List of scheduled tweets
        """
        if os.path.exists(self.scheduler_file):
            try:
                with open(self.scheduler_file, 'r') as f:
                    scheduled_tweets = json.load(f)
                logger.info(f"Loaded {len(scheduled_tweets)} scheduled tweets")
                return scheduled_tweets
            except Exception as e:
                logger.error(f"Error loading scheduled tweets: {e}")
                return []
        return []
    
    def _save_scheduled_tweets(self):
        """Save scheduled tweets to file"""
        try:
            with open(self.scheduler_file, 'w') as f:
                json.dump(self.scheduled_tweets, f, indent=2)
            logger.debug("Scheduled tweets saved")
            return True
        except Exception as e:
            logger.error(f"Error saving scheduled tweets: {e}")
            return False
    
    def add_tweet(self, content: str, schedule_type: str = "one-time", 
                schedule_datetime: str = None, schedule_days: List[int] = None, 
                schedule_time: str = None, interval_hours: int = 24, 
                enabled: bool = True) -> Dict:
        """
        Add a new scheduled tweet
        
        Args:
            content (str): Tweet content
            schedule_type (str): Type of schedule (one-time, daily, weekly, interval)
            schedule_datetime (str): ISO datetime for one-time tweets
            schedule_days (List[int]): Days of week for weekly tweets (0-6, where 0 is Sunday)
            schedule_time (str): Time of day for daily/weekly tweets (HH:MM format)
            interval_hours (int): Hours between tweets for interval type
            enabled (bool): Whether the tweet is enabled
            
        Returns:
            Dict: The added tweet
        """
        tweet_id = str(datetime.datetime.now().timestamp())
        
        tweet = {
            "id": tweet_id,
            "content": content,
            "schedule": {
                "type": schedule_type,
                "datetime": schedule_datetime,
                "days": schedule_days or [],
                "time": schedule_time,
                "interval_hours": interval_hours,
                "last_sent": None
            },
            "enabled": enabled,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        self.scheduled_tweets.append(tweet)
        self._save_scheduled_tweets()
        
        logger.info(f"Added new scheduled tweet: {content[:30]}...")
        return tweet
    
    def update_tweet(self, tweet_id: str, content: str = None, schedule_type: str = None,
                    schedule_datetime: str = None, schedule_days: List[int] = None,
                    schedule_time: str = None, interval_hours: int = None,
                    enabled: bool = None) -> bool:
        """
        Update an existing scheduled tweet
        
        Args:
            tweet_id (str): ID of the tweet to update
            content (str): New tweet content
            schedule_type (str): New schedule type
            schedule_datetime (str): New datetime for one-time tweets
            schedule_days (List[int]): New days of week for weekly tweets
            schedule_time (str): New time of day for daily/weekly tweets
            interval_hours (int): New interval hours
            enabled (bool): New enabled status
            
        Returns:
            bool: Success status
        """
        for tweet in self.scheduled_tweets:
            if tweet["id"] == tweet_id:
                if content is not None:
                    tweet["content"] = content
                
                if schedule_type is not None:
                    tweet["schedule"]["type"] = schedule_type
                
                if schedule_datetime is not None:
                    tweet["schedule"]["datetime"] = schedule_datetime
                
                if schedule_days is not None:
                    tweet["schedule"]["days"] = schedule_days
                
                if schedule_time is not None:
                    tweet["schedule"]["time"] = schedule_time
                
                if interval_hours is not None:
                    tweet["schedule"]["interval_hours"] = interval_hours
                
                if enabled is not None:
                    tweet["enabled"] = enabled
                
                self._save_scheduled_tweets()
                logger.info(f"Updated scheduled tweet: {tweet_id}")
                return True
        
        logger.warning(f"Tweet not found for update: {tweet_id}")
        return False
    
    def delete_tweet(self, tweet_id: str) -> bool:
        """
        Delete a scheduled tweet
        
        Args:
            tweet_id (str): ID of the tweet to delete
            
        Returns:
            bool: Success status
        """
        initial_count = len(self.scheduled_tweets)
        self.scheduled_tweets = [t for t in self.scheduled_tweets if t["id"] != tweet_id]
        
        if len(self.scheduled_tweets) < initial_count:
            self._save_scheduled_tweets()
            logger.info(f"Deleted scheduled tweet: {tweet_id}")
            return True
        
        logger.warning(f"Tweet not found for deletion: {tweet_id}")
        return False
    
    def get_tweets(self) -> List[Dict]:
        """
        Get all scheduled tweets
        
        Returns:
            List[Dict]: List of scheduled tweets
        """
        return self.scheduled_tweets
    
    def get_tweet(self, tweet_id: str) -> Optional[Dict]:
        """
        Get a specific scheduled tweet
        
        Args:
            tweet_id (str): ID of the tweet
            
        Returns:
            Dict or None: The scheduled tweet if found
        """
        for tweet in self.scheduled_tweets:
            if tweet["id"] == tweet_id:
                return tweet
        return None
    
    def _should_send_tweet(self, tweet: Dict) -> bool:
        """
        Check if a tweet should be sent now
        
        Args:
            tweet (Dict): The scheduled tweet
            
        Returns:
            bool: Whether the tweet should be sent
        """
        if not tweet.get("enabled", False):
            return False
        
        schedule = tweet.get("schedule", {})
        schedule_type = schedule.get("type", "")
        
        now = datetime.datetime.now()
        
        if schedule_type == "one-time":
            # One-time scheduled tweet
            schedule_datetime = schedule.get("datetime", "")
            if not schedule_datetime:
                return False
            
            try:
                scheduled_time = datetime.datetime.fromisoformat(schedule_datetime)
                return now >= scheduled_time
            except ValueError:
                logger.error(f"Invalid datetime format: {schedule_datetime}")
                return False
        
        elif schedule_type == "daily":
            # Daily scheduled tweet
            schedule_time = schedule.get("time", "")
            if not schedule_time:
                return False
            
            try:
                # Parse time like "14:30"
                hour, minute = map(int, schedule_time.split(":"))
                scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Check if it's time to send and hasn't been sent today
                last_sent = schedule.get("last_sent")
                if last_sent:
                    try:
                        last_sent_dt = datetime.datetime.fromisoformat(last_sent)
                        # If already sent today, don't send again
                        if last_sent_dt.date() == now.date():
                            return False
                    except ValueError:
                        pass
                
                # Send if current time is past the scheduled time for today
                return now.time() >= scheduled_time.time()
            except (ValueError, IndexError):
                logger.error(f"Invalid time format: {schedule_time}")
                return False
        
        elif schedule_type == "weekly":
            # Weekly scheduled tweet
            schedule_days = schedule.get("days", [])
            schedule_time = schedule.get("time", "")
            
            if not schedule_days or not schedule_time:
                return False
            
            try:
                # Check if today is a scheduled day
                today_weekday = str(now.weekday() + 1 % 7)  # 0 = Monday in datetime, but we want 0 = Sunday
                if today_weekday not in schedule_days:
                    return False
                
                # Parse time like "14:30"
                hour, minute = map(int, schedule_time.split(":"))
                scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Check if it's time to send and hasn't been sent today
                last_sent = schedule.get("last_sent")
                if last_sent:
                    try:
                        last_sent_dt = datetime.datetime.fromisoformat(last_sent)
                        # If already sent today, don't send again
                        if last_sent_dt.date() == now.date():
                            return False
                    except ValueError:
                        pass
                
                # Send if current time is past the scheduled time for today
                return now.time() >= scheduled_time.time()
            except (ValueError, IndexError):
                logger.error(f"Invalid format for weekly tweet: {schedule}")
                return False
        
        elif schedule_type == "interval":
            # Interval-based tweet
            interval_hours = schedule.get("interval_hours", 24)
            last_sent = schedule.get("last_sent")
            
            if not last_sent:
                return True  # Never sent before, send it now
            
            try:
                last_sent_dt = datetime.datetime.fromisoformat(last_sent)
                next_send_time = last_sent_dt + datetime.timedelta(hours=interval_hours)
                return now >= next_send_time
            except ValueError:
                logger.error(f"Invalid last_sent format: {last_sent}")
                return False
        
        return False
    
    def _mark_tweet_sent(self, tweet: Dict):
        """
        Mark a tweet as sent
        
        Args:
            tweet (Dict): The scheduled tweet
        """
        tweet["schedule"]["last_sent"] = datetime.datetime.now().isoformat()
        
        # For one-time tweets, disable them after sending
        if tweet["schedule"]["type"] == "one-time":
            tweet["enabled"] = False
        
        self._save_scheduled_tweets()
    
    def _scheduler_loop(self):
        """Background scheduler loop"""
        logger.info("Starting tweet scheduler loop")
        
        while self.running:
            try:
                # Reload scheduled tweets to get any updates
                self.scheduled_tweets = self._load_scheduled_tweets()
                
                for tweet in self.scheduled_tweets:
                    if self._should_send_tweet(tweet):
                        content = tweet.get("content", "")
                        
                        # Call the callback function if set
                        if self.callback and content:
                            logger.info(f"Sending scheduled tweet: {content[:30]}...")
                            self.callback(content)
                            
                            # Mark as sent
                            self._mark_tweet_sent(tweet)
                
                # Check every minute
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a bit longer if there was an error
    
    def set_callback(self, callback: Callable):
        """
        Set the callback function for scheduled tweets
        
        Args:
            callback (Callable): Callback function
        """
        self.callback = callback
    
    def start(self):
        """Start the tweet scheduler"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            logger.info("Tweet scheduler started")
    
    def stop(self):
        """Stop the tweet scheduler"""
        if self.running:
            self.running = False
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            logger.info("Tweet scheduler stopped")
    
    def is_running(self):
        """Check if the scheduler is running"""
        return self.running and (self.scheduler_thread is not None) and self.scheduler_thread.is_alive()