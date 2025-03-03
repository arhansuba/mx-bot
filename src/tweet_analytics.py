import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TweetAnalytics:
    def __init__(self, data_dir="data"):
        """
        Initialize the tweet analytics module
        
        Args:
            data_dir (str): Directory to store analytics data
        """
        self.data_dir = data_dir
        self.interactions_file = os.path.join(data_dir, "interactions.json")
        self.analytics_dir = os.path.join(data_dir, "analytics")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.analytics_dir, exist_ok=True)
        
        # Load existing interactions or create empty list
        self.interactions = self._load_interactions()
        logger.info(f"Tweet analytics initialized with {len(self.interactions)} existing interactions")
    
    def _load_interactions(self) -> List[Dict]:
        """
        Load interaction data from file
        
        Returns:
            List[Dict]: List of interaction records
        """
        if os.path.exists(self.interactions_file):
            try:
                with open(self.interactions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading interactions: {e}")
                return []
        return []
    
    def _save_interactions(self) -> None:
        """Save interaction data to file"""
        try:
            with open(self.interactions_file, 'w') as f:
                json.dump(self.interactions, f, indent=2)
            logger.debug("Interactions saved successfully")
        except Exception as e:
            logger.error(f"Error saving interactions: {e}")
    
    def record_interaction(self, tweet_data: Dict, classification: str, 
                           response: str, blockchain_data: Dict) -> None:
        """
        Record a new bot interaction
        
        Args:
            tweet_data (Dict): Data about the tweet
            classification (str): Classification of the tweet
            response (str): The bot's response
            blockchain_data (Dict): Data fetched from the blockchain
        """
        interaction = {
            "timestamp": datetime.datetime.now().isoformat(),
            "tweet_id": tweet_data.get("id"),
            "username": tweet_data.get("username"),
            "tweet_text": tweet_data.get("text"),
            "classification": classification,
            "response": response,
            "blockchain_data": blockchain_data
        }
        
        self.interactions.append(interaction)
        self._save_interactions()
        logger.info(f"Recorded new interaction with tweet {tweet_data.get('id')}")
    
    def generate_daily_report(self) -> Dict:
        """
        Generate a report of today's interactions
        
        Returns:
            Dict: Report data
        """
        today = datetime.datetime.now().date()
        
        # Filter interactions from today
        today_interactions = [
            interaction for interaction in self.interactions
            if datetime.datetime.fromisoformat(interaction["timestamp"]).date() == today
        ]
        
        # Count by classification
        classification_counts = {}
        for interaction in today_interactions:
            classification = interaction["classification"]
            classification_counts[classification] = classification_counts.get(classification, 0) + 1
        
        # Basic stats
        report = {
            "date": today.isoformat(),
            "total_interactions": len(today_interactions),
            "classification_breakdown": classification_counts,
            "users_reached": len(set(interaction["username"] for interaction in today_interactions))
        }
        
        logger.info(f"Generated daily report: {len(today_interactions)} interactions today")
        return report
    
    def save_daily_report(self) -> None:
        """Generate and save a daily report file"""
        report = self.generate_daily_report()
        today = datetime.datetime.now().date().isoformat()
        
        try:
            report_file = os.path.join(self.analytics_dir, f"report_{today}.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Generate charts
            self._generate_charts(report, today)
            
            logger.info(f"Daily report saved to {report_file}")
        except Exception as e:
            logger.error(f"Error saving daily report: {e}")
    
    def _generate_charts(self, report: Dict, date_str: str) -> None:
        """
        Generate charts for the report
        
        Args:
            report (Dict): Report data
            date_str (str): Date string for file naming
        """
        try:
            # Classification breakdown pie chart
            classifications = report["classification_breakdown"]
            if classifications:
                plt.figure(figsize=(10, 6))
                plt.pie(
                    classifications.values(), 
                    labels=classifications.keys(),
                    autopct='%1.1f%%',
                    startangle=90
                )
                plt.axis('equal')
                plt.title('Tweet Classifications')
                
                chart_file = os.path.join(self.analytics_dir, f"classifications_{date_str}.png")
                plt.savefig(chart_file)
                plt.close()
                
                logger.info(f"Classification chart saved to {chart_file}")
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def get_historical_stats(self, days: int = 7) -> Dict:
        """
        Get stats for the past N days
        
        Args:
            days (int): Number of days to include
            
        Returns:
            Dict: Historical statistics
        """
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).date()
        
        # Group interactions by date
        interactions_by_date = {}
        classification_by_date = {}
        
        for interaction in self.interactions:
            date = datetime.datetime.fromisoformat(interaction["timestamp"]).date()
            
            if date >= cutoff_date:
                date_str = date.isoformat()
                
                # Count interactions by date
                if date_str not in interactions_by_date:
                    interactions_by_date[date_str] = 0
                interactions_by_date[date_str] += 1
                
                # Count classifications by date
                if date_str not in classification_by_date:
                    classification_by_date[date_str] = {}
                
                classification = interaction["classification"]
                classification_by_date[date_str][classification] = \
                    classification_by_date[date_str].get(classification, 0) + 1
        
        return {
            "interactions_by_date": interactions_by_date,
            "classification_by_date": classification_by_date,
            "total_interactions": sum(interactions_by_date.values()),
            "unique_users": len(set(
                interaction["username"] for interaction in self.interactions
                if datetime.datetime.fromisoformat(interaction["timestamp"]).date() >= cutoff_date
            ))
        }
    
    def export_to_csv(self, output_file: str = None) -> str:
        """
        Export interaction data to CSV
        
        Args:
            output_file (str, optional): Output file path
            
        Returns:
            str: Path to the generated CSV file
        """
        if not output_file:
            output_file = os.path.join(self.analytics_dir, f"interactions_{datetime.datetime.now().strftime('%Y%m%d')}.csv")
        
        try:
            # Convert interactions to pandas DataFrame
            df = pd.DataFrame(self.interactions)
            
            # Handle nested blockchain_data
            if 'blockchain_data' in df.columns:
                df = df.drop('blockchain_data', axis=1)
            
            # Save to CSV
            df.to_csv(output_file, index=False)
            logger.info(f"Exported interactions to {output_file}")
            
            return output_file
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return ""