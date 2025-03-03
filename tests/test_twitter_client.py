#!/usr/bin/env python
# test_twitter_api.py

import asyncio
import logging
import sys
from dotenv import load_dotenv

# Add the src directory to the system path
sys.path.append('c:/Users/subas/multiversx-ai-bot/src')

# Adjust the import statement to correctly reference the module
from twitter_poster import TwitterPoster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('twitter_test')

async def main():
    """Test Twitter poster functionality"""
    try:
        # Load environment variables
        load_dotenv()
        
        logger.info("Creating Twitter poster with environment variables")
        
        # Create Twitter poster
        poster = TwitterPoster()
        
        # Verify connection
        logger.info("Verifying Twitter connection...")
        connection_result = await poster.verify_connection()
        
        if not connection_result:
            logger.error("Twitter connection verification failed")
            return
            
        logger.info("Twitter connection verified successfully!")
        
        # Test posting a simple tweet
        test_content = f"MultiversX AI Bot test tweet - API testing at {asyncio.get_event_loop().time():.0f}"
        
        logger.info(f"Testing tweet posting with content: {test_content}")
        
        tweet_id = await poster.post_tweet(test_content)
        
        if tweet_id:
            logger.info(f"Test tweet posted successfully! Tweet ID: {tweet_id}")
            logger.info(f"View at: https://twitter.com/anyuser/status/{tweet_id}")
            
            # Get metrics (will be mostly zeros for a new tweet)
            metrics = await poster.get_tweet_metrics(tweet_id)
            logger.info(f"Initial metrics: {metrics}")
        else:
            logger.error("Failed to post test tweet")
            
    except Exception as e:
        logger.error(f"Error in test script: {str(e)}", exc_info=True)
    finally:
        # Clean up
        if 'poster' in locals():
            await poster.close()
        logger.info("Test script completed")

if __name__ == "__main__":
    asyncio.run(main())