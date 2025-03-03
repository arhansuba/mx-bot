import os
import json
import logging
import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLAnalytics:
    def __init__(self, data_dir="data"):
        """
        Initialize the ML analytics module
        
        Args:
            data_dir (str): Directory with interaction data
        """
        self.data_dir = data_dir
        self.analytics_dir = os.path.join(data_dir, "analytics")
        self.ml_dir = os.path.join(self.analytics_dir, "ml")
        self.interactions_file = os.path.join(data_dir, "interactions.json")
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.analytics_dir, exist_ok=True)
        os.makedirs(self.ml_dir, exist_ok=True)
        
        logger.info("ML analytics module initialized")
    
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
    
    def _create_dataframe(self) -> pd.DataFrame:
        """
        Create a pandas DataFrame from interactions
        
        Returns:
            pd.DataFrame: Interaction data
        """
        interactions = self._load_interactions()
        
        if not interactions:
            logger.warning("No interactions found")
            return pd.DataFrame()
        
        # Extract main features
        data = []
        for interaction in interactions:
            record = {
                'timestamp': interaction.get('timestamp', ''),
                'username': interaction.get('username', ''),
                'classification': interaction.get('classification', ''),
                'tweet_length': len(interaction.get('tweet_text', '')),
                'response_length': len(interaction.get('response', '')),
            }
            
            # Add sentiment data if available
            sentiment_data = interaction.get('sentiment_data', {})
            if sentiment_data:
                record['sentiment'] = sentiment_data.get('sentiment', 'neutral')
                record['sentiment_score'] = sentiment_data.get('sentiment_score', 0.5)
                record['emotional_tone'] = sentiment_data.get('emotional_tone', 'unknown')
                record['requires_attention'] = sentiment_data.get('requires_attention', False)
            
            # Add blockchain data features
            blockchain_data = interaction.get('blockchain_data', {})
            if 'price' in blockchain_data:
                record['price_query'] = True
                record['price_value'] = blockchain_data.get('price', 0)
            else:
                record['price_query'] = False
                record['price_value'] = 0
                
            if 'nft' in blockchain_data:
                record['nft_query'] = True
            else:
                record['nft_query'] = False
                
            if 'balance' in blockchain_data:
                record['balance_query'] = True
                record['balance_value'] = blockchain_data.get('balance', 0)
            else:
                record['balance_query'] = False
                record['balance_value'] = 0
            
            data.append(record)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Extract time components
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
        
        return df
    
    def analyze_user_segments(self) -> Dict:
        """
        Segment users based on their interactions
        
        Returns:
            Dict: User segment analysis
        """
        try:
            df = self._create_dataframe()
            
            if df.empty:
                return {"error": "No data available for analysis"}
            
            # Group by username
            user_interactions = df.groupby('username').agg({
                'timestamp': 'count',  # Count of interactions
                'classification': lambda x: list(x),  # List of classifications
                'sentiment': lambda x: list(x) if 'sentiment' in df.columns else [],
                'sentiment_score': 'mean' if 'sentiment_score' in df.columns else None,
                'tweet_length': 'mean',
                'price_query': 'sum',
                'nft_query': 'sum',
                'balance_query': 'sum'
            }).reset_index()
            
            # Rename columns
            user_interactions = user_interactions.rename(columns={'timestamp': 'interaction_count'})
            
            # Calculate most common classification for each user
            user_interactions['primary_interest'] = user_interactions['classification'].apply(
                lambda x: Counter(x).most_common(1)[0][0] if x else "unknown"
            )
            
            # Calculate sentiment distribution if available
            if 'sentiment' in user_interactions.columns:
                user_interactions['primary_sentiment'] = user_interactions['sentiment'].apply(
                    lambda x: Counter(x).most_common(1)[0][0] if x else "neutral"
                )
            
            # Create feature matrix for clustering
            features = ['interaction_count', 'tweet_length', 'price_query', 'nft_query', 'balance_query']
            if 'sentiment_score' in user_interactions.columns:
                features.append('sentiment_score')
                
            X = user_interactions[features].values
            
            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Determine optimal number of clusters (simplified)
            n_clusters = min(4, len(user_interactions))
            
            # Apply KMeans clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            user_interactions['cluster'] = kmeans.fit_predict(X_scaled)
            
            # Analyze clusters
            cluster_analysis = {}
            for cluster_id in range(n_clusters):
                cluster_users = user_interactions[user_interactions['cluster'] == cluster_id]
                
                # Calculate key metrics for this cluster
                interests = Counter([item for sublist in cluster_users['classification'] for item in sublist])
                primary_interest = interests.most_common(1)[0][0] if interests else "unknown"
                
                cluster_analysis[f"Cluster {cluster_id}"] = {
                    "size": len(cluster_users),
                    "avg_interactions": cluster_users['interaction_count'].mean(),
                    "primary_interest": primary_interest,
                    "interest_distribution": {k: v / sum(interests.values()) for k, v in interests.items()},
                    "price_queries_pct": cluster_users['price_query'].sum() / cluster_users['interaction_count'].sum(),
                    "nft_queries_pct": cluster_users['nft_query'].sum() / cluster_users['interaction_count'].sum(),
                    "balance_queries_pct": cluster_users['balance_query'].sum() / cluster_users['interaction_count'].sum(),
                }
                
                if 'primary_sentiment' in cluster_users.columns:
                    sentiments = Counter(cluster_users['primary_sentiment'])
                    cluster_analysis[f"Cluster {cluster_id}"]["sentiment_distribution"] = {
                        k: v / len(cluster_users) for k, v in sentiments.items()
                    }
            
            # Generate visualization
            if len(X_scaled) > 1:  # Need at least 2 users for PCA
                self._visualize_clusters(X_scaled, user_interactions['cluster'], user_interactions['username'])
            
            return {
                "user_segments": cluster_analysis,
                "total_users": len(user_interactions),
                "avg_interactions_per_user": user_interactions['interaction_count'].mean(),
                "interest_distribution": {
                    k: v / len(user_interactions) 
                    for k, v in Counter(user_interactions['primary_interest']).items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user segments: {e}")
            return {"error": str(e)}
    
    def _visualize_clusters(self, X_scaled, clusters, usernames):
        """
        Create a visualization of user clusters
        
        Args:
            X_scaled: Scaled feature matrix
            clusters: Cluster assignments
            usernames: User identifiers
        """
        try:
            # Apply PCA for dimensionality reduction
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # Create scatter plot
            plt.figure(figsize=(10, 8))
            
            # Plot each cluster
            for cluster_id in np.unique(clusters):
                # Get indices for this cluster
                indices = np.where(clusters == cluster_id)
                
                # Plot points
                plt.scatter(
                    X_pca[indices, 0], 
                    X_pca[indices, 1], 
                    label=f'Cluster {cluster_id}',
                    alpha=0.7
                )
            
            plt.title('User Segments - PCA Visualization')
            plt.xlabel('Principal Component 1')
            plt.ylabel('Principal Component 2')
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Save the plot
            plot_file = os.path.join(self.ml_dir, f"user_clusters_{datetime.datetime.now().strftime('%Y%m%d')}.png")
            plt.savefig(plot_file)
            plt.close()
            
            logger.info(f"Saved user clusters visualization to {plot_file}")
            
        except Exception as e:
            logger.error(f"Error creating cluster visualization: {e}")
    
    def analyze_content_effectiveness(self) -> Dict:
        """
        Analyze the effectiveness of different content types and approaches
        
        Returns:
            Dict: Content effectiveness analysis
        """
        try:
            df = self._create_dataframe()
            
            if df.empty:
                return {"error": "No data available for analysis"}
            
            # Analyze response length vs. sentiment
            effectiveness_by_length = {}
            if 'sentiment_score' in df.columns:
                # Create bins for response length
                df['response_length_bin'] = pd.cut(
                    df['response_length'], 
                    bins=[0, 100, 150, 200, 280],
                    labels=['Very Short', 'Short', 'Medium', 'Long']
                )
                
                # Calculate average sentiment score by response length
                effectiveness_by_length = df.groupby('response_length_bin')['sentiment_score'].mean().to_dict()
            
            # Analyze effectiveness by classification
            classification_stats = df.groupby('classification').agg({
                'timestamp': 'count',
                'sentiment_score': 'mean' if 'sentiment_score' in df.columns else lambda x: None
            }).rename(columns={'timestamp': 'count'}).to_dict('index')
            
            # Analyze time patterns
            time_patterns = {}
            if 'hour' in df.columns:
                # Group interactions by hour of day
                hourly_counts = df.groupby('hour').size()
                peak_hour = hourly_counts.idxmax()
                
                # Group interactions by day of week
                day_counts = df.groupby('day_of_week').size()
                peak_day = day_counts.idxmax()
                
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                most_active_day = days[peak_day]
                
                time_patterns = {
                    "peak_hour": int(peak_hour),
                    "peak_day_of_week": most_active_day,
                    "hourly_distribution": hourly_counts.to_dict(),
                    "daily_distribution": {days[k]: v for k, v in day_counts.to_dict().items()}
                }
            
            # Create visualizations
            self._visualize_content_effectiveness(df)
            
            return {
                "effectiveness_by_response_length": effectiveness_by_length,
                "effectiveness_by_classification": classification_stats,
                "time_patterns": time_patterns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content effectiveness: {e}")
            return {"error": str(e)}
    
    def _visualize_content_effectiveness(self, df):
        """
        Create visualizations for content effectiveness
        
        Args:
            df: DataFrame with interaction data
        """
        try:
            # Plot interactions by classification
            plt.figure(figsize=(10, 6))
            classification_counts = df['classification'].value_counts()
            classification_counts.plot(kind='bar', color='skyblue')
            plt.title('Interactions by Classification')
            plt.xlabel('Classification')
            plt.ylabel('Count')
            plt.tight_layout()
            
            # Save the plot
            class_file = os.path.join(self.ml_dir, f"classification_counts_{datetime.datetime.now().strftime('%Y%m%d')}.png")
            plt.savefig(class_file)
            plt.close()
            
            # Plot hourly distribution if available
            if 'hour' in df.columns:
                plt.figure(figsize=(12, 6))
                df.groupby('hour').size().plot(kind='line', marker='o')
                plt.title('Interactions by Hour of Day')
                plt.xlabel('Hour')
                plt.ylabel('Number of Interactions')
                plt.xticks(range(0, 24))
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                # Save the plot
                hourly_file = os.path.join(self.ml_dir, f"hourly_activity_{datetime.datetime.now().strftime('%Y%m%d')}.png")
                plt.savefig(hourly_file)
                plt.close()
            
            logger.info(f"Saved content effectiveness visualizations")
            
        except Exception as e:
            logger.error(f"Error creating effectiveness visualizations: {e}")
    
    def generate_insights(self) -> Dict:
        """
        Generate actionable insights from the analytics
        
        Returns:
            Dict: Data insights and recommendations
        """
        try:
            # Combine different analyses
            user_segments = self.analyze_user_segments()
            content_effectiveness = self.analyze_content_effectiveness()
            
            # Extract key insights
            insights = []
            recommendations = []
            
            # Check for errors in analyses
            if "error" in user_segments or "error" in content_effectiveness:
                return {
                    "insights": ["Not enough data to generate meaningful insights."],
                    "recommendations": ["Continue collecting more interaction data."]
                }
            
            # User segment insights
            if "user_segments" in user_segments:
                segments = user_segments["user_segments"]
                for cluster_id, data in segments.items():
                    primary_interest = data.get("primary_interest")
                    insights.append(
                        f"User segment {cluster_id} ({data['size']} users) primarily interested in {primary_interest} "
                        f"with {data['avg_interactions']:.1f} average interactions per user."
                    )
                
                # Recommendations based on largest segments
                largest_segment = max(segments.items(), key=lambda x: x[1]['size'])[0]
                largest_interest = segments[largest_segment]['primary_interest']
                recommendations.append(
                    f"Create more content focused on {largest_interest} to engage your largest user segment."
                )
            
            # Content effectiveness insights
            if "effectiveness_by_classification" in content_effectiveness:
                class_stats = content_effectiveness["effectiveness_by_classification"]
                
                # Most common query type
                if class_stats:
                    most_common = max(class_stats.items(), key=lambda x: x[1]['count'])[0]
                    insights.append(f"The most common query type is '{most_common}' with {class_stats[most_common]['count']} interactions.")
                
                # Sentiment analysis if available
                highest_sentiment = None
                highest_score = -1
                
                for class_type, stats in class_stats.items():
                    if 'sentiment_score' in stats and stats['sentiment_score'] is not None:
                        if stats['sentiment_score'] > highest_score:
                            highest_score = stats['sentiment_score']
                            highest_sentiment = class_type
                
                if highest_sentiment:
                    insights.append(f"'{highest_sentiment}' queries generate the most positive sentiment (score: {highest_score:.2f}).")
                    recommendations.append(f"Prioritize '{highest_sentiment}' content to maximize positive engagement.")
            
            # Time-based insights
            if "time_patterns" in content_effectiveness:
                time_data = content_effectiveness["time_patterns"]
                if "peak_hour" in time_data and "peak_day_of_week" in time_data:
                    insights.append(
                        f"User activity peaks at {time_data['peak_hour']}:00 and is highest on {time_data['peak_day_of_week']}."
                    )
                    recommendations.append(
                        f"Schedule important announcements and content around {time_data['peak_hour']}:00 on {time_data['peak_day_of_week']} for maximum visibility."
                    )
            
            # Response length insights
            if "effectiveness_by_response_length" in content_effectiveness:
                length_data = content_effectiveness["effectiveness_by_response_length"]
                if length_data:
                    best_length = max(length_data.items(), key=lambda x: x[1] if x[1] is not None else -1)[0]
                    insights.append(f"'{best_length}' responses tend to generate the most positive sentiment.")
                    recommendations.append(f"Optimize response length to the '{best_length}' category for better engagement.")
            
            # Add general insights if we don't have many
            if len(insights) < 2:
                insights.append("Initial data shows varied user interests in MultiversX ecosystem topics.")
            if len(recommendations) < 2:
                recommendations.append("Diversify content to cover price information, NFTs, and technology updates.")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "user_segments": user_segments,
                "content_effectiveness": content_effectiveness,
                "charts": {
                    "user_clusters": f"user_clusters_{datetime.datetime.now().strftime('%Y%m%d')}.png",
                    "classification_counts": f"classification_counts_{datetime.datetime.now().strftime('%Y%m%d')}.png",
                    "hourly_activity": f"hourly_activity_{datetime.datetime.now().strftime('%Y%m%d')}.png"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "error": str(e),
                "insights": ["Error generating insights. Please check the logs."],
                "recommendations": ["Ensure you have sufficient interaction data."]
            }
    
    def generate_report(self) -> str:
        """
        Generate a complete ML analytics report and save it
        
        Returns:
            str: Path to the generated report
        """
        try:
            # Get insights and data
            report_data = self.generate_insights()
            
            # Create report file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.ml_dir, f"ml_report_{timestamp}.json")
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"Generated ML analytics report: {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            return ""