import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class TweetAnalyzer:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def classify_tweet(self, tweet_text):
        """
        Classify a tweet into categories using Gemini AI
        
        Args:
            tweet_text (str): The text of the tweet to analyze
            
        Returns:
            str: The classification of the tweet (price inquiry, NFT mention, balance inquiry, general comment)
        """
        logger.info(f"Classifying tweet: {tweet_text[:50]}...")
        
        try:
            prompt = f"""
            Classify this tweet about MultiversX blockchain: '{tweet_text}'
            
            Classify it into exactly ONE of these categories:
            1. price inquiry - if the tweet is asking about EGLD price or token prices
            2. NFT mention - if the tweet is talking about NFTs on MultiversX
            3. balance inquiry - if the tweet is asking about account balance or includes an address
            4. general comment - for any other MultiversX-related comments
            
            Return ONLY the category name without any explanation, punctuation, or additional text.
            """
            
            response = self.model.generate_content(prompt)
            classification = response.text.strip().lower()
            
            # Validate that the response is one of the expected categories
            valid_categories = [
                "price inquiry", 
                "nft mention", 
                "balance inquiry", 
                "general comment"
            ]
            
            # Normalize response
            for category in valid_categories:
                if category in classification:
                    logger.info(f"Tweet classified as: {category}")
                    return category
            
            # Default to general comment if the classification doesn't match any category
            logger.warning(f"Classification not recognized: {classification}, defaulting to 'general comment'")
            return "general comment"
            
        except Exception as e:
            logger.error(f"Error classifying tweet: {e}")
            return "general comment"
    
    def extract_nft_identifier(self, tweet_text):
        """
        Extract NFT identifier from a tweet if present
        
        Args:
            tweet_text (str): The text of the tweet
            
        Returns:
            str or None: The NFT identifier if found, None otherwise
        """
        try:
            prompt = f"""
            Extract the MultiversX NFT identifier from this tweet: '{tweet_text}'
            
            MultiversX NFT identifiers look like 'COLLECTION-123abc'. They usually have a collection name in capital 
            letters, followed by a hyphen and alphanumeric characters.
            
            If you find an NFT identifier, return ONLY the identifier without any additional text.
            If no clear NFT identifier is present, return 'None'.
            """
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            if result.lower() == 'none':
                return None
            return result
            
        except Exception as e:
            logger.error(f"Error extracting NFT identifier: {e}")
            return None
    
    def extract_address(self, tweet_text):
        """
        Extract MultiversX address from a tweet if present
        
        Args:
            tweet_text (str): The text of the tweet
            
        Returns:
            str or None: The address if found, None otherwise
        """
        try:
            prompt = f"""
            Extract the MultiversX wallet address from this tweet: '{tweet_text}'
            
            MultiversX addresses start with 'erd1' followed by a string of alphanumeric characters, 
            typically 58 characters after 'erd1'.
            
            If you find a MultiversX address, return ONLY the address without any additional text.
            If no MultiversX address is present, return 'None'.
            """
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            if result.lower() == 'none':
                return None
                
            # Basic validation - addresses start with erd1
            if result.startswith('erd1'):
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error extracting address: {e}")
            return None