import os
import time
import logging
import datetime
import threading
from dotenv import load_dotenv
from blockchain_fetcher import BlockchainFetcher
from tweet_analytics import TweetAnalytics
from web_dashboard import WebDashboard
from twitter_poster import TwitterPoster

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

# Load environment variables
load_dotenv()

async def main():
    """Main function to run the Twitter bot"""
    logger.info("Starting MultiversX Community Management AI Twitter Bot")
    
    # Initialize components
    blockchain_fetcher = BlockchainFetcher(network="devnet")
    analytics = TweetAnalytics()
    
    # Initialize the Twitter poster
    twitter_poster = TwitterPoster()
    
    # Start web dashboard
    dashboard = WebDashboard(port=5000)
    dashboard_thread = dashboard.start()
    logger.info(f"Web dashboard running at http://localhost:5000")
    
    # Main loop - just keep the dashboard running and collect blockchain data
    try:
        while True:
            logger.info("Bot running in blockchain monitoring and dashboard mode")
            
            try:
                # Get current EGLD price from blockchain
                price = blockchain_fetcher.get_egld_price()
                if price:
                    logger.info(f"Current EGLD price: ${price}")
                
                # Get network stats
                stats = blockchain_fetcher.get_network_stats()
                if stats:
                    logger.info(f"Network stats: Transactions={stats.get('transactions', 0)}, Accounts={stats.get('accounts', 0)}")
                
                # Example of posting a tweet
                tweet_id = await twitter_poster.post_tweet("Your tweet content here")
                
                # Wait before checking again
                logger.info("Waiting 60 seconds before next data check...")
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a bit longer if there was an error
                
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())