from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitterScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-notifications')
        self.service = Service(ChromeDriverManager().install())
        
    def get_tweets(self, search_term="MultiversX", limit=10):
        """
        Scrape tweets mentioning the search_term
        
        Args:
            search_term (str): The term to search for
            limit (int): Maximum number of tweets to return
            
        Returns:
            list: List of dictionaries containing tweet data (id, text, username)
        """
        logger.info(f"Starting to scrape tweets for: {search_term}")
        driver = webdriver.Chrome(service=self.service, options=self.options)
        
        try:
            # Twitter's search URL
            url = f"https://twitter.com/search?q={search_term}&src=typed_query&f=live"
            driver.get(url)
            
            # Wait for the page to load
            time.sleep(5)
            
            # Wait for tweets to be visible
            tweet_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//article[@data-testid="tweet"]'))
            )
            
            tweets = []
            processed = 0
            
            for element in tweet_elements:
                if processed >= limit:
                    break
                
                try:
                    # Extract tweet text
                    tweet_text_element = element.find_element(By.XPATH, './/div[@data-testid="tweetText"]')
                    tweet_text = tweet_text_element.text
                    
                    # Extract tweet ID from the link
                    links = element.find_elements(By.XPATH, './/a[contains(@href, "/status/")]')
                    for link in links:
                        href = link.get_attribute('href')
                        if '/status/' in href:
                            tweet_id = href.split('/status/')[1].split('?')[0]
                            break
                    
                    # Extract username
                    username_element = element.find_element(By.XPATH, './/span[contains(text(), "@")]')
                    username = username_element.text
                    
                    tweets.append({
                        'id': tweet_id,
                        'text': tweet_text,
                        'username': username
                    })
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing tweet: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(tweets)} tweets")
            return tweets
            
        except Exception as e:
            logger.error(f"Error scraping tweets: {e}")
            return []
            
        finally:
            driver.quit()