import os
import json
import logging
import datetime
import random
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class NLPTweetGenerator:
    def __init__(self, data_dir="data"):
        """
        Initialize the NLP tweet generator
        
        Args:
            data_dir (str): Directory to store tweet templates and data
        """
        self.data_dir = data_dir
        self.templates_dir = os.path.join(data_dir, "templates")
        self.templates_file = os.path.join(self.templates_dir, "tweet_templates.json")
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Load or create templates
        self.templates = self._load_templates()
        
        # Initialize Gemini AI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Initialize personality profile
        self.personality = {
            "tone": "friendly and professional",
            "style": "informative with a touch of enthusiasm",
            "expertise": "knowledgeable about MultiversX blockchain",
            "values": "community-focused, educational, helpful",
            "avoids": "excessive jargon, hype, speculation about price"
        }
        
        logger.info("NLP tweet generator initialized")
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """
        Load tweet templates from file
        
        Returns:
            Dict[str, List[str]]: Templates categorized by type
        """
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r') as f:
                    templates = json.load(f)
                logger.info(f"Loaded {sum(len(v) for v in templates.values())} tweet templates")
                return templates
            except Exception as e:
                logger.error(f"Error loading tweet templates: {e}")
        
        # Default templates
        templates = {
            "educational": [
                "Did you know? {fact} #MultiversX #Blockchain",
                "Here's an interesting fact about #MultiversX: {fact}",
                "Learn something new about #MultiversX today: {fact}",
                "💡 MultiversX Insight: {fact} #Blockchain #Tech",
                "Today's #MultiversX knowledge drop: {fact} 🔍"
            ],
            "news": [
                "📢 MultiversX Update: {news} #MultiversX",
                "Breaking news from the MultiversX ecosystem: {news} #Crypto",
                "Just in: {news} #MultiversX #Blockchain",
                "The latest from MultiversX: {news} 🌐",
                "MultiversX News Alert: {news} #EGLD"
            ],
            "stats": [
                "📊 MultiversX Stats: {stats} #EGLD",
                "The numbers are in! {stats} #MultiversX",
                "MultiversX by the numbers: {stats} 📈",
                "Today's MultiversX ecosystem stats: {stats} #Blockchain",
                "Check out these MultiversX metrics: {stats} #Crypto"
            ],
            "community": [
                "Shout out to the amazing MultiversX community! {message} #MultiversXCommunity",
                "We appreciate all of you in the MultiversX ecosystem! {message} 🙏",
                "The strength of MultiversX is its community. {message} #EGLD",
                "To all MultiversX builders and users: {message} 🚀",
                "Community update: {message} #MultiversX #Blockchain"
            ],
            "features": [
                "Spotlight on MultiversX features: {feature} #MultiversX",
                "Have you tried this MultiversX feature? {feature} #Blockchain",
                "MultiversX Highlight: {feature} ✨",
                "Powerful MultiversX functionality: {feature} #EGLD",
                "Feature Focus: {feature} #MultiversX #Technology"
            ]
        }
        
        # Save default templates
        with open(self.templates_file, 'w') as f:
            json.dump(templates, f, indent=2)
        
        logger.info(f"Created default tweet templates")
        return templates
    
    def add_template(self, category: str, template: str) -> bool:
        """
        Add a new tweet template
        
        Args:
            category (str): Category of the template
            template (str): Template text
            
        Returns:
            bool: Success status
        """
        if category not in self.templates:
            self.templates[category] = []
        
        if template not in self.templates[category]:
            self.templates[category].append(template)
            
            # Save templates
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
            
            logger.info(f"Added new template to category {category}")
            return True
        
        return False
    
    def remove_template(self, category: str, template: str) -> bool:
        """
        Remove a tweet template
        
        Args:
            category (str): Category of the template
            template (str): Template text
            
        Returns:
            bool: Success status
        """
        if category in self.templates and template in self.templates[category]:
            self.templates[category].remove(template)
            
            # Save templates
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
            
            logger.info(f"Removed template from category {category}")
            return True
        
        return False
    
    def get_templates(self) -> Dict[str, List[str]]:
        """
        Get all tweet templates
        
        Returns:
            Dict[str, List[str]]: Templates categorized by type
        """
        return self.templates
    
    def generate_tweet_from_template(self, category: str, data: Dict[str, Any]) -> str:
        """
        Generate a tweet from a template
        
        Args:
            category (str): Category of the template
            data (Dict): Data to fill in the template
            
        Returns:
            str: Generated tweet
        """
        try:
            if category not in self.templates or not self.templates[category]:
                logger.warning(f"No templates found for category: {category}")
                return ""
            
            # Select a random template from the category
            template = random.choice(self.templates[category])
            
            # Fill in the template
            tweet = template
            for key, value in data.items():
                placeholder = "{" + key + "}"
                if placeholder in tweet:
                    tweet = tweet.replace(placeholder, str(value))
            
            logger.info(f"Generated tweet from template: {tweet[:30]}...")
            return tweet
            
        except Exception as e:
            logger.error(f"Error generating tweet from template: {e}")
            return ""
    
    def generate_educational_tweet(self, blockchain_data: Optional[Dict] = None) -> str:
        """
        Generate an educational tweet about MultiversX
        
        Args:
            blockchain_data (Dict, optional): Blockchain data to incorporate
            
        Returns:
            str: Generated tweet
        """
        try:
            prompt = f"""
            Generate an interesting, educational fact about the MultiversX blockchain ecosystem.
            
            Make it concise (under 200 characters), accurate, and engaging for a crypto audience.
            Focus on technology, features, or capabilities that make MultiversX unique.
            
            DO NOT mention price predictions or investment advice.
            
            Personality profile to match:
            {json.dumps(self.personality, indent=2)}
            """
            
            # Add blockchain data context if available
            if blockchain_data:
                prompt += f"\n\nYou can incorporate this blockchain data if relevant:\n{json.dumps(blockchain_data, indent=2)}"
            
            response = self.model.generate_content(prompt)
            fact = response.text.strip()
            
            # Generate tweet using template
            return self.generate_tweet_from_template("educational", {"fact": fact})
            
        except Exception as e:
            logger.error(f"Error generating educational tweet: {e}")
            return "Did you know MultiversX uses an adaptive state sharding architecture for improved scalability? #MultiversX #Blockchain"
    
    def generate_news_tweet(self, news_data: Optional[Dict] = None) -> str:
        """
        Generate a news tweet about MultiversX
        
        Args:
            news_data (Dict, optional): News data to incorporate
            
        Returns:
            str: Generated tweet
        """
        try:
            # If news data is provided, use it
            if news_data and "headline" in news_data:
                return self.generate_tweet_from_template("news", {"news": news_data["headline"]})
            
            # Otherwise, generate news-like content
            prompt = f"""
            Generate a brief, newsworthy update about the MultiversX blockchain ecosystem.
            
            Make it concise (under 200 characters), accurate, and with a news-like tone.
            It should sound like a recent development but be generic enough to not appear as false news.
            
            Focus on ecosystem growth, partnerships, tech development, or community milestones.
            
            Personality profile to match:
            {json.dumps(self.personality, indent=2)}
            """
            
            response = self.model.generate_content(prompt)
            news = response.text.strip()
            
            # Generate tweet using template
            return self.generate_tweet_from_template("news", {"news": news})
            
        except Exception as e:
            logger.error(f"Error generating news tweet: {e}")
            return "MultiversX ecosystem continues to grow with new projects and partnerships emerging every week. Stay tuned for more updates! #MultiversX"
    
    def generate_stats_tweet(self, blockchain_data: Dict) -> str:
        """
        Generate a stats tweet about MultiversX
        
        Args:
            blockchain_data (Dict): Blockchain data to incorporate
            
        Returns:
            str: Generated tweet
        """
        try:
            # Extract and format relevant stats
            stats_text = ""
            
            if "price" in blockchain_data:
                stats_text += f"EGLD price: ${blockchain_data['price']}, "
            
            if "network_stats" in blockchain_data:
                network = blockchain_data["network_stats"]
                if "transactions" in network:
                    stats_text += f"Total txs: {network['transactions']:,}, "
                if "accounts" in network:
                    stats_text += f"Accounts: {network['accounts']:,}, "
                if "blocks" in network:
                    stats_text += f"Blocks: {network['blocks']:,}, "
            
            # Remove trailing comma and space
            if stats_text.endswith(", "):
                stats_text = stats_text[:-2]
            
            # If we have stats, use them
            if stats_text:
                return self.generate_tweet_from_template("stats", {"stats": stats_text})
            
            # Otherwise, generate generic stats message
            prompt = f"""
            Generate a brief summary of MultiversX blockchain statistics.
            
            Make it concise (under 200 characters), with a focus on impressive metrics 
            about the network, ecosystem, or community.
            
            Use generic but realistic numbers that would represent a growing blockchain ecosystem.
            
            Personality profile to match:
            {json.dumps(self.personality, indent=2)}
            """
            
            response = self.model.generate_content(prompt)
            stats = response.text.strip()
            
            # Generate tweet using template
            return self.generate_tweet_from_template("stats", {"stats": stats})
            
        except Exception as e:
            logger.error(f"Error generating stats tweet: {e}")
            return "MultiversX network continues to demonstrate strong performance with fast transactions and growing adoption. #MultiversX #Blockchain"
    
    def generate_community_tweet(self) -> str:
        """
        Generate a community-focused tweet
        
        Returns:
            str: Generated tweet
        """
        try:
            prompt = f"""
            Generate a positive, community-focused message for MultiversX blockchain users and developers.
            
            Make it concise (under 200 characters), uplifting, and appreciative of the community.
            Focus on encouragement, thanking the community, or highlighting community achievements.
            
            Personality profile to match:
            {json.dumps(self.personality, indent=2)}
            """
            
            response = self.model.generate_content(prompt)
            message = response.text.strip()
            
            # Generate tweet using template
            return self.generate_tweet_from_template("community", {"message": message})
            
        except Exception as e:
            logger.error(f"Error generating community tweet: {e}")
            return "Thank you to all the developers, validators, and users who make the MultiversX ecosystem thrive! Your support and contributions are what make our network great. #MultiversXCommunity"
    
    def generate_feature_tweet(self) -> str:
        """
        Generate a tweet highlighting a MultiversX feature
        
        Returns:
            str: Generated tweet
        """
        try:
            prompt = f"""
            Generate a brief description of a specific feature or capability of the MultiversX blockchain.
            
            Make it concise (under 200 characters), informative, and focused on a technical advantage
            or unique selling point of MultiversX.
            
            Some examples could be related to:
            - Adaptive State Sharding
            - Secure Proof of Stake
            - WASM VM
            - Smart Contracts
            - Tokenomics
            - Developer Tools
            
            Personality profile to match:
            {json.dumps(self.personality, indent=2)}
            """
            
            response = self.model.generate_content(prompt)
            feature = response.text.strip()
            
            # Generate tweet using template
            return self.generate_tweet_from_template("features", {"feature": feature})
            
        except Exception as e:
            logger.error(f"Error generating feature tweet: {e}")
            return "MultiversX's Adaptive State Sharding combines network, transaction, and data sharding for unmatched scalability while maintaining security and decentralization. #MultiversX #Blockchain"
    
    def generate_creative_tweet(self, prompt_hints: str = "") -> str:
        """
        Generate a completely creative tweet based on AI
        
        Args:
            prompt_hints (str): Hints to guide the AI
            
        Returns:
            str: Generated tweet
        """
        try:
            base_prompt = f"""
            Generate a creative, engaging tweet about MultiversX blockchain.
            
            Make it concise (under 280 characters), informative yet conversational,
            and appropriate for posting from an official account.
            
            Include appropriate hashtags like #MultiversX, #Blockchain, or #EGLD.
            
            Personality profile to match:
            {json.dumps(self.personality, indent=2)}
            """
            
            # Add hints if provided
            if prompt_hints:
                base_prompt += f"\n\nFocus on or incorporate these elements: {prompt_hints}"
            
            response = self.model.generate_content(base_prompt)
            tweet = response.text.strip()
            
            logger.info(f"Generated creative tweet: {tweet[:30]}...")
            return tweet
            
        except Exception as e:
            logger.error(f"Error generating creative tweet: {e}")
            return "The future of blockchain is here with MultiversX - scalable, secure, and built for global adoption. Join us on this journey! #MultiversX #Blockchain #EGLD"
    
    def generate_tweet(self, category: str = "random", blockchain_data: Optional[Dict] = None, hints: str = "") -> str:
        """
        Generate a tweet based on the specified category
        
        Args:
            category (str): Tweet category
            blockchain_data (Dict, optional): Blockchain data to incorporate
            hints (str): Additional hints for tweet generation
            
        Returns:
            str: Generated tweet
        """
        # If category is random, choose one
        if category == "random":
            categories = ["educational", "news", "stats", "community", "features", "creative"]
            category = random.choice(categories)
        
        # Generate tweet based on category
        if category == "educational":
            return self.generate_educational_tweet(blockchain_data)
        elif category == "news":
            return self.generate_news_tweet()
        elif category == "stats":
            return self.generate_stats_tweet(blockchain_data or {})
        elif category == "community":
            return self.generate_community_tweet()
        elif category == "features":
            return self.generate_feature_tweet()
        elif category == "creative":
            return self.generate_creative_tweet(hints)
        else:
            logger.warning(f"Unknown tweet category: {category}")
            return self.generate_creative_tweet(hints)