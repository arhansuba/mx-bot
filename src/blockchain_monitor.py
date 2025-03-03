import os
import json
import time
import logging
import datetime
import threading
from typing import Dict, List, Optional, Any, Callable
import requests
from utils.retry_utils import retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlockchainMonitor:
    def __init__(self, data_dir="data", network="devnet", callback=None):
        """
        Initialize the blockchain monitor
        
        Args:
            data_dir (str): Directory to store monitoring data
            network (str): MultiversX network to monitor
            callback (Callable): Callback function for detected events
        """
        self.data_dir = data_dir
        self.monitor_dir = os.path.join(data_dir, "monitor")
        
        networks = {
            "devnet": "https://devnet-api.multiversx.com",
            "testnet": "https://testnet-api.multiversx.com",
            "mainnet": "https://api.multiversx.com"
        }
        
        self.api_url = networks.get(network.lower(), networks["devnet"])
        self.network = network
        self.callback = callback
        self.running = False
        self.monitor_thread = None
        self.history_file = os.path.join(self.monitor_dir, "monitor_history.json")
        self.last_check = {
            "price": 0,
            "transactions": 0,
            "blocks": 0
        }
        
        # Thresholds for alerts
        self.thresholds = {
            "price_change_percent": 5.0,  # 5% price change
            "transaction_volume_usd": 1000000,  # $1M transaction volume
            "high_value_transaction": 100000,  # 100K EGLD 
            "block_time": 60  # seconds
        }
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.monitor_dir, exist_ok=True)
        
        # Load monitoring history
        self._load_history()
        
        logger.info(f"Blockchain monitor initialized for network: {network}")
    
    def _load_history(self):
        """Load monitoring history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                    
                # Update last check with values from history
                if "last_check" in history:
                    self.last_check = history["last_check"]
                    
                # Update thresholds if defined in history
                if "thresholds" in history:
                    self.thresholds = history["thresholds"]
                    
                logger.info(f"Loaded monitoring history with {len(history.get('events', []))} events")
                return history
            except Exception as e:
                logger.error(f"Error loading monitoring history: {e}")
        
        # Create default history structure
        history = {
            "last_check": self.last_check,
            "thresholds": self.thresholds,
            "events": [],
            "known_transactions": {}
        }
        
        self._save_history(history)
        return history
    
    def _save_history(self, history):
        """Save monitoring history to file"""
        try:
            # Update last check times
            history["last_check"] = self.last_check
            history["thresholds"] = self.thresholds
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            logger.debug("Monitoring history saved")
            return True
        except Exception as e:
            logger.error(f"Error saving monitoring history: {e}")
            return False
    
    def set_thresholds(self, thresholds):
        """
        Set monitoring thresholds
        
        Args:
            thresholds (Dict): Threshold values
        """
        if isinstance(thresholds, dict):
            for key, value in thresholds.items():
                if key in self.thresholds:
                    self.thresholds[key] = value
            
            logger.info(f"Updated monitoring thresholds: {self.thresholds}")
            
            # Update in history file
            history = self._load_history()
            history["thresholds"] = self.thresholds
            self._save_history(history)
    
    def set_callback(self, callback):
        """
        Set the callback function for detected events
        
        Args:
            callback (Callable): Callback function
        """
        self.callback = callback
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2, exceptions=(requests.RequestException,))
    def _fetch_data(self, endpoint):
        """
        Fetch data from the API
        
        Args:
            endpoint (str): API endpoint
            
        Returns:
            Dict: API response
        """
        url = f"{self.api_url}/{endpoint}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _check_price_changes(self):
        """
        Check for significant price changes
        
        Returns:
            List: Detected events
        """
        try:
            # Get current price
            economics = self._fetch_data("economics")
            current_price = economics.get("price", 0)
            
            if current_price == 0:
                logger.warning("Retrieved zero price from API, skipping price check")
                return []
            
            events = []
            history = self._load_history()
            
            # Get last known price
            last_known_price = history.get("last_known_price", None)
            
            if last_known_price is not None:
                # Calculate price change
                price_change = current_price - last_known_price
                price_change_percent = (price_change / last_known_price) * 100
                
                # Check if price change exceeds threshold
                if abs(price_change_percent) >= self.thresholds["price_change_percent"]:
                    # Price change detected
                    event = {
                        "type": "price_change",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "data": {
                            "old_price": last_known_price,
                            "new_price": current_price,
                            "change": price_change,
                            "change_percent": price_change_percent,
                            "direction": "up" if price_change > 0 else "down"
                        }
                    }
                    
                    events.append(event)
                    
                    # Add to history
                    history.setdefault("events", []).append(event)
                    logger.info(f"Detected price change event: {price_change_percent:.2f}% ({price_change:.2f} USD)")
            
            # Update last known price
            history["last_known_price"] = current_price
            self._save_history(history)
            
            # Update last check time
            self.last_check["price"] = time.time()
            
            return events
            
        except Exception as e:
            logger.error(f"Error checking price changes: {e}")
            return []
    
    def _check_high_value_transactions(self):
        """
        Check for high-value transactions
        
        Returns:
            List: Detected events
        """
        try:
            # Get recent transactions
            transactions = self._fetch_data("transactions?size=50&order=desc")
            
            events = []
            history = self._load_history()
            known_txs = history.get("known_transactions", {})
            
            # Get current EGLD price
            economics = self._fetch_data("economics")
            egld_price = economics.get("price", 0)
            
            for tx in transactions:
                tx_hash = tx.get("txHash")
                
                # Skip if we've already processed this transaction
                if tx_hash in known_txs:
                    continue
                
                # Check transaction value
                tx_value = float(tx.get("value", "0")) / 10**18  # Convert from denomination to EGLD
                tx_value_usd = tx_value * egld_price
                
                if tx_value >= self.thresholds["high_value_transaction"]:
                    # High value transaction detected
                    event = {
                        "type": "high_value_transaction",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "data": {
                            "tx_hash": tx_hash,
                            "sender": tx.get("sender"),
                            "receiver": tx.get("receiver"),
                            "value_egld": tx_value,
                            "value_usd": tx_value_usd
                        }
                    }
                    
                    events.append(event)
                    
                    # Add to history
                    history.setdefault("events", []).append(event)
                    logger.info(f"Detected high value transaction: {tx_value:.2f} EGLD (${tx_value_usd:.2f})")
                
                # Mark transaction as processed
                known_txs[tx_hash] = {
                    "value": tx_value,
                    "timestamp": tx.get("timestamp")
                }
            
            # Keep only the 1000 most recent transactions in history
            if len(known_txs) > 1000:
                oldest_txs = sorted(known_txs.items(), key=lambda x: x[1]["timestamp"])
                known_txs = dict(oldest_txs[-1000:])
            
            # Update history
            history["known_transactions"] = known_txs
            self._save_history(history)
            
            # Update last check time
            self.last_check["transactions"] = time.time()
            
            return events
            
        except Exception as e:
            logger.error(f"Error checking high value transactions: {e}")
            return []
    
    def _check_network_status(self):
        """
        Check network status and performance
        
        Returns:
            List: Detected events
        """
        try:
            # Get network stats
            stats = self._fetch_data("stats")
            
            events = []
            history = self._load_history()
            
            # Check for interesting network events
            
            # 1. Block time anomalies
            current_block_time = stats.get("roundTime", 0)
            last_known_block_time = history.get("last_known_block_time", None)
            
            if last_known_block_time is not None and current_block_time > self.thresholds["block_time"]:
                # Block time increase detected
                event = {
                    "type": "block_time_increase",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "data": {
                        "old_block_time": last_known_block_time,
                        "new_block_time": current_block_time,
                        "change": current_block_time - last_known_block_time
                    }
                }
                
                events.append(event)
                
                # Add to history
                history.setdefault("events", []).append(event)
                logger.info(f"Detected block time increase: {current_block_time} seconds")
            
            # 2. Transaction volume anomalies
            current_tx_count = stats.get("transactions", 0)
            last_known_tx_count = history.get("last_known_tx_count", None)
            
            if last_known_tx_count is not None:
                tx_count_change = current_tx_count - last_known_tx_count
                
                if tx_count_change > 10000:  # Arbitrary threshold for demonstration
                    # Transaction volume spike detected
                    event = {
                        "type": "transaction_volume_spike",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "data": {
                            "old_tx_count": last_known_tx_count,
                            "new_tx_count": current_tx_count,
                            "change": tx_count_change
                        }
                    }
                    
                    events.append(event)
                    
                    # Add to history
                    history.setdefault("events", []).append(event)
                    logger.info(f"Detected transaction volume spike: +{tx_count_change} transactions")
            
            # Update last known values
            history["last_known_block_time"] = current_block_time
            history["last_known_tx_count"] = current_tx_count
            self._save_history(history)
            
            # Update last check time
            self.last_check["blocks"] = time.time()
            
            return events
            
        except Exception as e:
            logger.error(f"Error checking network status: {e}")
            return []
    
    def run_checks(self):
        """
        Run all monitoring checks
        
        Returns:
            List: All detected events
        """
        all_events = []
        
        # Check price changes
        price_events = self._check_price_changes()
        all_events.extend(price_events)
        
        # Check high value transactions
        tx_events = self._check_high_value_transactions()
        all_events.extend(tx_events)
        
        # Check network status
        network_events = self._check_network_status()
        all_events.extend(network_events)
        
        # Process detected events
        if all_events and self.callback:
            for event in all_events:
                self.callback(event)
        
        return all_events
    
    def generate_event_message(self, event):
        """
        Generate a Twitter message for a blockchain event
        
        Args:
            event (Dict): Event data
            
        Returns:
            str: Formatted message for Twitter
        """
        try:
            event_type = event.get("type", "")
            event_data = event.get("data", {})
            
            if event_type == "price_change":
                direction = "📈" if event_data.get("direction") == "up" else "📉"
                percent = abs(event_data.get("change_percent", 0))
                new_price = event_data.get("new_price", 0)
                
                return f"{direction} #EGLD price has changed by {percent:.2f}%! Current price: ${new_price:.2f} USD. #MultiversX #Crypto"
            
            elif event_type == "high_value_transaction":
                value_egld = event_data.get("value_egld", 0)
                value_usd = event_data.get("value_usd", 0)
                tx_hash = event_data.get("tx_hash", "")
                
                return f"🔥 Large transaction detected! {value_egld:.2f} #EGLD (${value_usd:.2f}) has been moved. Check tx: https://explorer.multiversx.com/transactions/{tx_hash} #MultiversX"
            
            elif event_type == "block_time_increase":
                new_time = event_data.get("new_block_time", 0)
                
                return f"⚠️ #MultiversX network status update: Block time has increased to {new_time} seconds. Network may be experiencing congestion."
            
            elif event_type == "transaction_volume_spike":
                change = event_data.get("change", 0)
                
                return f"📊 Network activity on #MultiversX has spiked with +{change} transactions recently! The ecosystem is buzzing with activity. #MultiversXNetwork"
            
            # Default message for unknown event types
            return f"📢 Notable event detected on the #MultiversX blockchain. Stay updated with our AI bot! #Crypto #Blockchain"
            
        except Exception as e:
            logger.error(f"Error generating event message: {e}")
            return "📢 Interesting activity detected on the #MultiversX blockchain! #Crypto #Blockchain"
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        logger.info("Starting blockchain monitoring loop")
        
        while self.running:
            try:
                # Run monitoring checks
                events = self.run_checks()
                
                # Log detection results
                if events:
                    logger.info(f"Detected {len(events)} blockchain events")
                else:
                    logger.debug("No significant blockchain events detected")
                
                # Sleep for a while before next check
                for _ in range(60):  # Check every minute
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a bit longer if there was an error
    
    def start(self):
        """Start the blockchain monitor"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("Blockchain monitor started")
    
    def stop(self):
        """Stop the blockchain monitor"""
        if self.running:
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            logger.info("Blockchain monitor stopped")
    
    def is_running(self):
        """Check if the monitor is running"""
        return self.running and (self.monitor_thread is not None) and self.monitor_thread.is_alive()
    
    def get_recent_events(self, limit=10):
        """
        Get the most recent detected events
        
        Args:
            limit (int): Maximum number of events to return
            
        Returns:
            List: Recent events
        """
        history = self._load_history()
        events = history.get("events", [])
        
        # Sort by timestamp (newest first) and limit
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""), reverse=True)
        return sorted_events[:limit]