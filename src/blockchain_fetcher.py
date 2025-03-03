import requests
import logging
import time
from typing import Dict, List, Optional, Union, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlockchainFetcher:
    def __init__(self, network="devnet"):
        """
        Initialize blockchain fetcher
        
        Args:
            network (str): The MultiversX network to use (devnet, testnet, mainnet)
        """
        networks = {
            "devnet": "https://devnet-api.multiversx.com",
            "testnet": "https://testnet-api.multiversx.com",
            "mainnet": "https://api.multiversx.com"
        }
        
        self.api_url = networks.get(network.lower(), networks["devnet"])
        self.network = network
        self.cache = {}
        self.cache_expiry = {}
        logger.info(f"Blockchain fetcher initialized with API URL: {self.api_url}")
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get data from cache if it exists and is not expired
        
        Args:
            key (str): Cache key
            
        Returns:
            Any: Cached data or None if not in cache or expired
        """
        if key in self.cache and self.cache_expiry.get(key, 0) > time.time():
            logger.debug(f"Retrieved {key} from cache")
            return self.cache[key]
        return None
    
    def _set_in_cache(self, key: str, data: Any, ttl_seconds: int = 60) -> None:
        """
        Store data in cache with expiry
        
        Args:
            key (str): Cache key
            data (Any): Data to cache
            ttl_seconds (int): Time to live in seconds
        """
        self.cache[key] = data
        self.cache_expiry[key] = time.time() + ttl_seconds
        logger.debug(f"Stored {key} in cache with {ttl_seconds}s TTL")
    
    def get_egld_price(self) -> Optional[float]:
        """
        Get the current EGLD price in USD
        
        Returns:
            float or None: The EGLD price if successful, None otherwise
        """
        cache_key = "egld_price"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            endpoint = f"{self.api_url}/economics"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                price = data.get("price", None)
                logger.info(f"Current EGLD price: ${price}")
                
                # Cache for 5 minutes
                self._set_in_cache(cache_key, price, 300)
                
                return price
            else:
                logger.error(f"Failed to get EGLD price. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching EGLD price: {e}")
            return None
    
    def get_network_stats(self) -> Optional[Dict]:
        """
        Get current network statistics
        
        Returns:
            Dict or None: Network statistics if successful, None otherwise
        """
        cache_key = "network_stats"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            endpoint = f"{self.api_url}/stats"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Successfully retrieved network stats")
                
                # Cache for 5 minutes
                self._set_in_cache(cache_key, data, 300)
                
                return data
            else:
                logger.error(f"Failed to get network stats. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching network stats: {e}")
            return None
    
    def get_nft_details(self, identifier: str) -> Optional[Dict]:
        """
        Get details about an NFT
        
        Args:
            identifier (str): The NFT identifier
            
        Returns:
            dict or None: NFT details if successful, None otherwise
        """
        if not identifier:
            return None
            
        cache_key = f"nft_{identifier}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            endpoint = f"{self.api_url}/nfts/{identifier}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved NFT details for {identifier}")
                
                # Cache for 10 minutes
                self._set_in_cache(cache_key, data, 600)
                
                return data
            else:
                logger.error(f"Failed to get NFT details. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching NFT details: {e}")
            return None
    
    def get_collection_details(self, collection_id: str) -> Optional[Dict]:
        """
        Get details about an NFT collection
        
        Args:
            collection_id (str): The collection identifier
            
        Returns:
            dict or None: Collection details if successful, None otherwise
        """
        if not collection_id:
            return None
            
        cache_key = f"collection_{collection_id}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            endpoint = f"{self.api_url}/collections/{collection_id}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved collection details for {collection_id}")
                
                # Cache for 30 minutes
                self._set_in_cache(cache_key, data, 1800)
                
                return data
            else:
                logger.error(f"Failed to get collection details. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching collection details: {e}")
            return None
    
    def get_balance(self, address_str: str) -> Optional[float]:
        """
        Get the balance of a MultiversX address
        
        Args:
            address_str (str): The address to check
            
        Returns:
            float or None: The balance in EGLD if successful, None otherwise
        """
        if not address_str:
            return None
            
        cache_key = f"balance_{address_str}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            endpoint = f"{self.api_url}/accounts/{address_str}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                # Balance is in denominated units (10^18), convert to EGLD
                balance_string = data.get("balance", "0")
                balance = float(balance_string) / 10**18
                logger.info(f"Balance for {address_str}: {balance} EGLD")
                
                # Cache for 2 minutes
                self._set_in_cache(cache_key, balance, 120)
                
                return balance
            else:
                logger.error(f"Failed to get balance. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
            
    def get_account_tokens(self, address_str: str) -> Optional[List[Dict]]:
        """
        Get the tokens owned by a MultiversX address
        
        Args:
            address_str (str): The address to check
            
        Returns:
            List[Dict] or None: List of tokens if successful, None otherwise
        """
        if not address_str:
            return None
            
        cache_key = f"tokens_{address_str}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            endpoint = f"{self.api_url}/accounts/{address_str}/tokens"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved {len(data)} tokens for {address_str}")
                
                # Cache for 5 minutes
                self._set_in_cache(cache_key, data, 300)
                
                return data
            else:
                logger.error(f"Failed to get tokens. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching tokens: {e}")
            return None
    
    def get_account_nfts(self, address_str: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get the NFTs owned by a MultiversX address
        
        Args:
            address_str (str): The address to check
            limit (int): Maximum number of NFTs to return
            
        Returns:
            List[Dict] or None: List of NFTs if successful, None otherwise
        """
        if not address_str:
            return None
            
        cache_key = f"nfts_{address_str}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            endpoint = f"{self.api_url}/accounts/{address_str}/nfts?size={limit}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved {len(data)} NFTs for {address_str}")
                
                # Cache for 5 minutes
                self._set_in_cache(cache_key, data, 300)
                
                return data
            else:
                logger.error(f"Failed to get NFTs. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching NFTs: {e}")
            return None
    
    def get_token_price(self, token_id: str) -> Optional[float]:
        """
        Get the price of a token
        
        Args:
            token_id (str): The token identifier
            
        Returns:
            float or None: The token price in USD if successful, None otherwise
        """
        if not token_id:
            return None
            
        cache_key = f"token_price_{token_id}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        try:
            # For EGLD, use the economics endpoint
            if token_id.lower() == "egld":
                return self.get_egld_price()
                
            # For other tokens, try the xExchange API
            endpoint = f"{self.api_url}/mex/tokens/{token_id}"
            response = requests.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                price = data.get("price", None)
                logger.info(f"Price for {token_id}: ${price}")
                
                # Cache for 5 minutes
                self._set_in_cache(cache_key, price, 300)
                
                return price
            else:
                logger.error(f"Failed to get token price. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching token price: {e}")
            return None