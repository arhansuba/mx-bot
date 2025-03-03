import logging
import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import Dict, Tuple, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SentimentAnalyzer:
    def __init__(self):
        """Initialize the sentiment analyzer with Gemini AI"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logger.info("Sentiment analyzer initialized with Gemini AI")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of a text
        
        Args:
            text (str): The text to analyze
            
        Returns:
            Dict: Sentiment analysis results
        """
        try:
            prompt = f"""
            Analyze the sentiment of this tweet about MultiversX cryptocurrency ecosystem:
            
            "{text}"
            
            Analyze it in the following aspects:
            1. Overall sentiment (positive, negative, or neutral) with a confidence score (0-1)
            2. Emotional tone (enthusiastic, frustrated, curious, etc.)
            3. Key topics mentioned (price, technology, community, etc.)
            4. Any specific feedback or questions
            
            Provide your analysis as valid JSON with these keys:
            {{
                "sentiment": "positive/negative/neutral",
                "sentiment_score": 0.x,
                "emotional_tone": "primary emotion",
                "topics": ["topic1", "topic2", ...],
                "feedback": "any specific feedback",
                "questions": ["question1", "question2", ...],
                "requires_attention": true/false (if negative or contains a question that needs addressing)
            }}
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response
            import json
            import re
            
            # Find JSON pattern in the response
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                try:
                    sentiment_data = json.loads(json_match.group(1))
                    logger.info(f"Sentiment analysis completed: {sentiment_data['sentiment']} with score {sentiment_data['sentiment_score']}")
                    return sentiment_data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decoding error: {e}")
            
            # If JSON extraction fails, return basic sentiment analysis
            logger.warning("Failed to extract JSON from response, returning basic sentiment")
            if "positive" in response_text.lower():
                sentiment = "positive"
                score = 0.7
            elif "negative" in response_text.lower():
                sentiment = "negative"
                score = 0.7
            else:
                sentiment = "neutral"
                score = 0.5
                
            return {
                "sentiment": sentiment,
                "sentiment_score": score,
                "emotional_tone": "unknown",
                "topics": [],
                "feedback": "",
                "questions": [],
                "requires_attention": "negative" in sentiment
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "emotional_tone": "unknown",
                "topics": [],
                "feedback": "",
                "questions": [],
                "requires_attention": False
            }
    
    def get_response_strategy(self, sentiment_data: Dict[str, Any]) -> str:
        """
        Determine response strategy based on sentiment analysis
        
        Args:
            sentiment_data (Dict): Sentiment analysis results
            
        Returns:
            str: Response strategy
        """
        sentiment = sentiment_data.get("sentiment", "neutral")
        score = sentiment_data.get("sentiment_score", 0.5)
        requires_attention = sentiment_data.get("requires_attention", False)
        questions = sentiment_data.get("questions", [])
        
        if sentiment == "negative" and score > 0.7:
            return "address_concern"
        elif sentiment == "negative":
            return "empathize"
        elif questions and len(questions) > 0:
            return "answer_question"
        elif sentiment == "positive" and score > 0.7:
            return "enthusiastic"
        else:
            return "informative"
    
    def create_targeted_response(self, tweet_text: str, classification: str, 
                                blockchain_data: Dict, sentiment_data: Dict[str, Any]) -> str:
        """
        Create a response targeted to the sentiment and content
        
        Args:
            tweet_text (str): Original tweet text
            classification (str): Tweet classification
            blockchain_data (Dict): Blockchain data
            sentiment_data (Dict): Sentiment analysis results
            
        Returns:
            str: Generated response
        """
        try:
            strategy = self.get_response_strategy(sentiment_data)
            sentiment = sentiment_data.get("sentiment", "neutral")
            emotional_tone = sentiment_data.get("emotional_tone", "unknown")
            topics = sentiment_data.get("topics", [])
            
            # Create contextual data for the prompt
            context = {
                "tweet": tweet_text,
                "classification": classification,
                "sentiment": sentiment,
                "emotional_tone": emotional_tone,
                "topics": topics,
                "strategy": strategy
            }
            
            # Add blockchain data based on classification
            if classification == "price inquiry" and "price" in blockchain_data:
                context["price"] = blockchain_data["price"]
            elif classification == "nft mention" and "nft" in blockchain_data:
                nft_data = blockchain_data["nft"]
                context["nft_name"] = nft_data.get("name", "the NFT")
                context["nft_collection"] = nft_data.get("collection", "")
            elif classification == "balance inquiry" and "balance" in blockchain_data:
                context["balance"] = blockchain_data["balance"]
            
            # Build prompt based on response strategy
            if strategy == "address_concern":
                prompt = f"""
                This user has expressed a negative sentiment about MultiversX. Address their concern with empathy, 
                provide accurate information to correct any misconceptions, and offer help if appropriate.
                
                Tweet: "{tweet_text}"
                
                Classification: {classification}
                Sentiment: {sentiment} (Score: {sentiment_data.get('sentiment_score')})
                Emotional tone: {emotional_tone}
                Topics mentioned: {', '.join(topics)}
                
                Please craft a thoughtful, helpful response that:
                1. Acknowledges their concern
                2. Provides accurate information
                3. Offers assistance or resources if appropriate
                4. Maintains a professional, supportive tone
                
                Keep the response under 240 characters for Twitter.
                """
            
            elif strategy == "empathize":
                prompt = f"""
                This user has expressed some concern or frustration about MultiversX. Respond with empathy and helpful information.
                
                Tweet: "{tweet_text}"
                
                Classification: {classification}
                Sentiment: {sentiment} (Score: {sentiment_data.get('sentiment_score')})
                Emotional tone: {emotional_tone}
                Topics mentioned: {', '.join(topics)}
                
                Craft a response that:
                1. Shows you understand their perspective
                2. Provides helpful information
                3. Maintains a respectful, patient tone
                
                Keep the response under 240 characters for Twitter.
                """
            
            elif strategy == "answer_question":
                prompt = f"""
                This user has asked a question about MultiversX. Provide a clear, helpful answer based on the blockchain data.
                
                Tweet: "{tweet_text}"
                
                Classification: {classification}
                Questions: {sentiment_data.get('questions', [])}
                
                Additional context:
                {str(context)}
                
                Craft a response that:
                1. Directly answers their question(s)
                2. Provides accurate blockchain data
                3. Is helpful and informative
                
                Keep the response under 240 characters for Twitter.
                """
            
            elif strategy == "enthusiastic":
                prompt = f"""
                This user has expressed positive sentiment about MultiversX. Respond with matching enthusiasm while providing valuable information.
                
                Tweet: "{tweet_text}"
                
                Classification: {classification}
                Sentiment: {sentiment} (Score: {sentiment_data.get('sentiment_score')})
                Emotional tone: {emotional_tone}
                Topics mentioned: {', '.join(topics)}
                
                Additional context:
                {str(context)}
                
                Craft a response that:
                1. Matches their enthusiasm
                2. Provides relevant blockchain data
                3. Encourages further engagement
                
                Keep the response under 240 characters for Twitter.
                """
            
            else:  # informative
                prompt = f"""
                Provide an informative response to this user's tweet about MultiversX.
                
                Tweet: "{tweet_text}"
                
                Classification: {classification}
                Sentiment: {sentiment}
                Topics mentioned: {', '.join(topics)}
                
                Additional context:
                {str(context)}
                
                Craft a response that:
                1. Is relevant to their tweet
                2. Provides accurate blockchain data
                3. Is helpful and engaging
                
                Keep the response under 240 characters for Twitter.
                """
            
            # Generate response
            response = self.model.generate_content(prompt)
            generated_text = response.text.strip()
            
            # Ensure the response is not too long for Twitter
            if len(generated_text) > 280:
                generated_text = generated_text[:277] + "..."
                
            logger.info(f"Generated sentiment-targeted response using strategy: {strategy}")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error creating targeted response: {e}")
            return f"Thanks for your interest in MultiversX! We appreciate your feedback and will continue to improve our ecosystem. 🌐 #MultiversX"