import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DummyTwitterPoster:
    """A dummy implementation of TwitterPoster that doesn't use Selenium"""
    
    def __init__(self):
        logger.info("Initialized dummy Twitter poster (no browser automation)")
        self.dummy_mode = True
    
    def login_to_twitter(self, username, password):
        """Mock Twitter login that always succeeds"""
        logger.info("Dummy Twitter login (no actual login performed)")
        return True
    
    def post_reply(self, tweet_id, reply_text):
        """Mock posting a reply"""
        logger.info(f"Would reply to tweet {tweet_id} with: {reply_text[:30]}...")
        return True
    
    def post_tweet(self, content):
        """Mock posting a tweet"""
        logger.info(f"Would post tweet: {content[:30]}...")
        return True
