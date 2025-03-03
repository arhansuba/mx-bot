import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class ResponseGenerator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_response(self, classification, blockchain_data, username=None):
        """
        Generate a response based on tweet classification and blockchain data
        
        Args:
            classification (str): The tweet classification
            blockchain_data (dict): Data fetched from the blockchain
            username (str): Twitter username to personalize response
            
        Returns:
            str: The generated response
        """
        logger.info(f"Generating response for classification: {classification}")
        
        try:
            user_greeting = f"@{username} " if username else ""
            
            if classification == "price inquiry":
                price = blockchain_data.get("price")
                if price:
                    prompt = f"""
                    Generate a friendly Twitter reply about the current EGLD price (${price}).
                    Include the price clearly and add a relevant emoji.
                    Keep it short (under 240 characters) and friendly.
                    Use this format: "{user_greeting}[your response]"
                    """
                else:
                    prompt = f"""
                    Generate a friendly Twitter reply explaining that we couldn't fetch the current EGLD price.
                    Suggest checking the MultiversX Explorer instead.
                    Keep it short (under 240 characters) and friendly.
                    Use this format: "{user_greeting}[your response]"
                    """
            
            elif classification == "nft mention":
                nft_data = blockchain_data.get("nft")
                if nft_data:
                    name = nft_data.get("name", "this NFT")
                    collection = nft_data.get("collection", "")
                    prompt = f"""
                    Generate a friendly Twitter reply about the NFT named "{name}" from collection "{collection}".
                    Include specific details from the NFT data and add a relevant emoji.
                    Keep it short (under 240 characters) and friendly.
                    Use this format: "{user_greeting}[your response]"
                    """
                else:
                    prompt = f"""
                    Generate a friendly Twitter reply explaining that we couldn't find information about the mentioned NFT.
                    Suggest checking the MultiversX Explorer for accurate NFT information.
                    Keep it short (under 240 characters) and friendly.
                    Use this format: "{user_greeting}[your response]"
                    """
            
            elif classification == "balance inquiry":
                balance = blockchain_data.get("balance")
                if balance is not None:
                    prompt = f"""
                    Generate a friendly Twitter reply about the account balance of {balance} EGLD.
                    Include the balance clearly and add a relevant emoji.
                    Keep it short (under 240 characters) and friendly.
                    Use this format: "{user_greeting}[your response]"
                    """
                else:
                    prompt = f"""
                    Generate a friendly Twitter reply explaining that we couldn't fetch the account balance.
                    Suggest checking the MultiversX Explorer for accurate balance information.
                    Keep it short (under 240 characters) and friendly.
                    Use this format: "{user_greeting}[your response]"
                    """
            
            else:  # general comment
                prompt = f"""
                Generate a friendly Twitter reply to a general comment about MultiversX blockchain.
                Include something positive about the MultiversX ecosystem and add a relevant emoji.
                Keep it short (under 240 characters) and friendly.
                Use this format: "{user_greeting}[your response]"
                """
            
            response = self.model.generate_content(prompt)
            generated_text = response.text.strip()
            
            # Ensure the response is not too long for Twitter
            if len(generated_text) > 280:
                generated_text = generated_text[:277] + "..."
                
            logger.info(f"Generated response: {generated_text}")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            if username:
                return f"@{username} Thanks for your interest in MultiversX! Our AI is currently experiencing issues, but we'll get back to you soon. 🌐"
            else:
                return "Thanks for your interest in MultiversX! Our AI is currently experiencing issues, but we'll get back to you soon. 🌐"