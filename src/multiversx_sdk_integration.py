import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Any, Union
from utils.retry_utils import retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiversXSDKIntegration:
    def __init__(self, network="devnet"):
        """
        Initialize MultiversX SDK integration
        
        Args:
            network (str): Network to use (devnet, testnet, mainnet)
        """
        self.network = network
        
        # Network configurations
        self.networks = {
            "devnet": {
                "api_url": "https://devnet-api.multiversx.com",
                "gateway_url": "https://devnet-gateway.multiversx.com",
                "explorer_url": "https://devnet-explorer.multiversx.com"
            },
            "testnet": {
                "api_url": "https://testnet-api.multiversx.com",
                "gateway_url": "https://testnet-gateway.multiversx.com",
                "explorer_url": "https://testnet-explorer.multiversx.com"
            },
            "mainnet": {
                "api_url": "https://api.multiversx.com",
                "gateway_url": "https://gateway.multiversx.com",
                "explorer_url": "https://explorer.multiversx.com"
            }
        }
        
        # Set current network URLs
        network_config = self.networks.get(network.lower(), self.networks["devnet"])
        self.api_url = network_config["api_url"]
        self.gateway_url = network_config["gateway_url"]
        self.explorer_url = network_config["explorer_url"]
        
        # Import MultiversX SDK components - using try/except to handle potential import errors
        try:
            # Import the minimal components we need from the SDK
            from multiversx_sdk import Address
            from multiversx_sdk import ApiNetwork
            
            # Store imported modules
            self.Address = Address
            self.ApiNetwork = ApiNetwork
            
            self.sdk_available = True
            logger.info(f"MultiversX SDK integration initialized for network: {network}")
            
        except ImportError as e:
            self.sdk_available = False
            logger.warning(f"MultiversX SDK not available: {e}")
            logger.warning("Falling back to REST API calls for blockchain interaction")
    
    def is_sdk_available(self) -> bool:
        """
        Check if MultiversX SDK is available
        
        Returns:
            bool: Whether SDK is available
        """
        return self.sdk_available
    
    def get_address_object(self, address_str: str):
        """
        Create an Address object from string
        
        Args:
            address_str (str): Bech32 address
            
        Returns:
            Address: MultiversX SDK Address object or None
        """
        if not self.sdk_available:
            logger.warning("SDK not available, cannot create Address object")
            return None
        
        try:
            if not address_str.startswith("erd1"):
                logger.error(f"Invalid MultiversX address format: {address_str}")
                return None
            
            return self.Address.from_bech32(address_str)
        except Exception as e:
            logger.error(f"Error creating Address object: {e}")
            return None
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2)
    def get_account_details(self, address_str: str) -> Optional[Dict]:
        """
        Get detailed account information
        
        Args:
            address_str (str): Account address
            
        Returns:
            Dict or None: Account details
        """
        if not address_str:
            return None
        
        try:
            # If SDK is available, use it
            if self.sdk_available:
                address = self.get_address_object(address_str)
                if not address:
                    return None
                
                # Create network provider
                network = self.ApiNetwork(self.gateway_url)
                
                # Get account information
                account = network.get_account(address)
                
                # Format account details
                return {
                    "address": address_str,
                    "nonce": account.nonce,
                    "balance": str(account.balance),
                    "balance_egld": float(account.balance) / 10**18,
                    "shard": account.shard
                }
            
            # Otherwise, use REST API
            import requests
            endpoint = f"{self.api_url}/accounts/{address_str}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "address": address_str,
                    "nonce": data.get("nonce", 0),
                    "balance": data.get("balance", "0"),
                    "balance_egld": float(data.get("balance", "0")) / 10**18,
                    "shard": data.get("shard", 0)
                }
            else:
                logger.error(f"Error fetching account details: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting account details: {e}")
            return None
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2)
    def get_account_transactions(self, address_str: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get account transactions
        
        Args:
            address_str (str): Account address
            limit (int): Maximum number of transactions
            
        Returns:
            List[Dict] or None: Transactions
        """
        if not address_str:
            return None
        
        try:
            import requests
            endpoint = f"{self.api_url}/accounts/{address_str}/transactions?size={limit}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching account transactions: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting account transactions: {e}")
            return None
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2)
    def get_account_tokens(self, address_str: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get account tokens
        
        Args:
            address_str (str): Account address
            limit (int): Maximum number of tokens
            
        Returns:
            List[Dict] or None: Tokens
        """
        if not address_str:
            return None
        
        try:
            import requests
            endpoint = f"{self.api_url}/accounts/{address_str}/tokens?size={limit}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching account tokens: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting account tokens: {e}")
            return None
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2)
    def get_account_nfts(self, address_str: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get account NFTs
        
        Args:
            address_str (str): Account address
            limit (int): Maximum number of NFTs
            
        Returns:
            List[Dict] or None: NFTs
        """
        if not address_str:
            return None
        
        try:
            import requests
            endpoint = f"{self.api_url}/accounts/{address_str}/nfts?size={limit}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching account NFTs: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting account NFTs: {e}")
            return None
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2)
    def get_token_details(self, token_id: str) -> Optional[Dict]:
        """
        Get detailed token information
        
        Args:
            token_id (str): Token identifier
            
        Returns:
            Dict or None: Token details
        """
        if not token_id:
            return None
        
        try:
            import requests
            endpoint = f"{self.api_url}/tokens/{token_id}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching token details: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting token details: {e}")
            return None
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2)
    def get_nft_details(self, nft_id: str) -> Optional[Dict]:
        """
        Get detailed NFT information
        
        Args:
            nft_id (str): NFT identifier
            
        Returns:
            Dict or None: NFT details
        """
        if not nft_id:
            return None
        
        try:
            import requests
            endpoint = f"{self.api_url}/nfts/{nft_id}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching NFT details: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting NFT details: {e}")
            return None
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2)
    def get_network_stats(self) -> Optional[Dict]:
        """
        Get network statistics
        
        Returns:
            Dict or None: Network statistics
        """
        try:
            import requests
            endpoint = f"{self.api_url}/stats"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching network stats: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
            return None
    
    @retry(max_tries=3, delay_seconds=1, backoff_factor=2)
    def get_economics(self) -> Optional[Dict]:
        """
        Get network economics
        
        Returns:
            Dict or None: Network economics
        """
        try:
            import requests
            endpoint = f"{self.api_url}/economics"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching economics: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting economics: {e}")
            return None
    
    def get_explorer_url(self, item_type: str, item_id: str) -> str:
        """
        Generate an explorer URL for a blockchain item
        
        Args:
            item_type (str): Type of item (address, transaction, token, nft)
            item_id (str): Item identifier
            
        Returns:
            str: Explorer URL
        """
        base_url = self.explorer_url
        
        if item_type == "address":
            return f"{base_url}/accounts/{item_id}"
        elif item_type == "transaction":
            return f"{base_url}/transactions/{item_id}"
        elif item_type == "token":
            return f"{base_url}/tokens/{item_id}"
        elif item_type == "nft":
            return f"{base_url}/nfts/{item_id}"
        else:
            return base_url
    
    def format_token_balance(self, raw_balance: str, decimals: int) -> str:
        """
        Format a token balance with proper decimals
        
        Args:
            raw_balance (str): Raw balance string
            decimals (int): Number of decimals
            
        Returns:
            str: Formatted balance
        """
        try:
            balance = float(raw_balance) / (10 ** decimals)
            
            # Format with appropriate number of decimal places
            if balance == int(balance):
                return str(int(balance))
            else:
                # Remove trailing zeros
                return str(balance).rstrip('0').rstrip('.') if '.' in str(balance) else str(balance)
                
        except Exception as e:
            logger.error(f"Error formatting token balance: {e}")
            return raw_balance
    
    def format_address(self, address_str: str, truncate: bool = False) -> str:
        """
        Format an address for display
        
        Args:
            address_str (str): MultiversX address
            truncate (bool): Whether to truncate the address
            
        Returns:
            str: Formatted address
        """
        if not address_str or not address_str.startswith("erd1"):
            return address_str
        
        if truncate:
            return address_str[:8] + "..." + address_str[-4:]
        
        return address_str
    
    def get_comprehensive_account_info(self, address_str: str) -> Dict:
        """
        Get comprehensive account information including balances, tokens, NFTs
        
        Args:
            address_str (str): Account address
            
        Returns:
            Dict: Comprehensive account information
        """
        result = {
            "address": address_str,
            "explorer_url": self.get_explorer_url("address", address_str)
        }
        
        # Get basic account details
        account_details = self.get_account_details(address_str)
        if account_details:
            result.update(account_details)
        
        # Get tokens
        tokens = self.get_account_tokens(address_str, limit=5)
        if tokens:
            result["tokens"] = []
            for token in tokens:
                token_info = {
                    "identifier": token.get("identifier", ""),
                    "name": token.get("name", ""),
                    "ticker": token.get("ticker", ""),
                    "balance": self.format_token_balance(
                        token.get("balance", "0"), 
                        token.get("decimals", 18)
                    ),
                    "explorer_url": self.get_explorer_url("token", token.get("identifier", ""))
                }
                result["tokens"].append(token_info)
        
        # Get NFTs
        nfts = self.get_account_nfts(address_str, limit=5)
        if nfts:
            result["nfts"] = []
            for nft in nfts:
                nft_info = {
                    "identifier": nft.get("identifier", ""),
                    "name": nft.get("name", ""),
                    "collection": nft.get("collection", ""),
                    "explorer_url": self.get_explorer_url("nft", nft.get("identifier", ""))
                }
                result["nfts"].append(nft_info)
        
        # Get recent transactions
        transactions = self.get_account_transactions(address_str, limit=3)
        if transactions:
            result["recent_transactions"] = []
            for tx in transactions:
                tx_info = {
                    "hash": tx.get("txHash", ""),
                    "sender": self.format_address(tx.get("sender", ""), truncate=True),
                    "receiver": self.format_address(tx.get("receiver", ""), truncate=True),
                    "value": self.format_token_balance(tx.get("value", "0"), 18),
                    "status": tx.get("status", ""),
                    "timestamp": tx.get("timestamp", 0),
                    "explorer_url": self.get_explorer_url("transaction", tx.get("txHash", ""))
                }
                result["recent_transactions"].append(tx_info)
        
        return result
    
    def get_comprehensive_nft_info(self, nft_id: str) -> Dict:
        """
        Get comprehensive NFT information
        
        Args:
            nft_id (str): NFT identifier
            
        Returns:
            Dict: Comprehensive NFT information
        """
        result = {
            "identifier": nft_id,
            "explorer_url": self.get_explorer_url("nft", nft_id)
        }
        
        # Get NFT details
        nft_details = self.get_nft_details(nft_id)
        if nft_details:
            result.update({
                "name": nft_details.get("name", ""),
                "collection": nft_details.get("collection", ""),
                "creator": self.format_address(nft_details.get("creator", ""), truncate=True),
                "royalties": nft_details.get("royalties", 0),
                "attributes": nft_details.get("attributes", ""),
                "media": nft_details.get("media", {}),
                "rarity": nft_details.get("rarity", "")
            })
        
        return result
    
    def get_blockchain_metrics(self) -> Dict:
        """
        Get key blockchain metrics (price, transactions, etc.)
        
        Returns:
            Dict: Blockchain metrics
        """
        result = {
            "network": self.network
        }
        
        # Get economics
        economics = self.get_economics()
        if economics:
            result.update({
                "price": economics.get("price", 0),
                "market_cap": economics.get("marketCap", 0),
                "circulating_supply": economics.get("circulatingSupply", 0),
                "total_supply": economics.get("totalSupply", 0),
                "staked": economics.get("staked", 0)
            })
        
        # Get network stats
        stats = self.get_network_stats()
        if stats:
            result.update({
                "transactions": stats.get("transactions", 0),
                "accounts": stats.get("accounts", 0),
                "blocks": stats.get("blocks", 0),
                "round_time": stats.get("roundTime", 0),
                "epoch": stats.get("epoch", 0),
                "shards": stats.get("shards", 0)
            })
        
        return result