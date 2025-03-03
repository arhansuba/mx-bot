import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.blockchain_fetcher import BlockchainFetcher

class TestBlockchainFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = BlockchainFetcher(network="devnet")
    
    @patch('requests.get')
    def test_get_egld_price(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"price": 42.5}
        mock_get.return_value = mock_response
        
        # Test the method
        price = self.fetcher.get_egld_price()
        
        # Assertions
        self.assertEqual(price, 42.5)
        mock_get.assert_called_once_with("https://devnet-api.multiversx.com/economics")
    
    @patch('requests.get')
    def test_get_egld_price_error(self, mock_get):
        # Setup mock response for error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        # Test the method
        price = self.fetcher.get_egld_price()
        
        # Assertions
        self.assertIsNone(price)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_network_stats(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "shards": 3,
            "blocks": 12345,
            "accounts": 5000,
            "transactions": 100000
        }
        mock_get.return_value = mock_response
        
        # Test the method
        stats = self.fetcher.get_network_stats()
        
        # Assertions
        self.assertEqual(stats["shards"], 3)
        self.assertEqual(stats["blocks"], 12345)
        mock_get.assert_called_once_with("https://devnet-api.multiversx.com/stats")
    
    @patch('requests.get')
    def test_get_nft_details(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "identifier": "TEST-123",
            "name": "Test NFT",
            "collection": "TEST"
        }
        mock_get.return_value = mock_response
        
        # Test the method
        nft = self.fetcher.get_nft_details("TEST-123")
        
        # Assertions
        self.assertEqual(nft["name"], "Test NFT")
        self.assertEqual(nft["collection"], "TEST")
        mock_get.assert_called_once_with("https://devnet-api.multiversx.com/nfts/TEST-123")
    
    @patch('requests.get')
    def test_get_balance(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "address": "erd1test",
            "balance": "1000000000000000000"  # 1 EGLD in denomination
        }
        mock_get.return_value = mock_response
        
        # Test the method
        balance = self.fetcher.get_balance("erd1test")
        
        # Assertions
        self.assertEqual(balance, 1.0)  # Should be converted to EGLD
        mock_get.assert_called_once_with("https://devnet-api.multiversx.com/accounts/erd1test")
    
    def test_handle_empty_inputs(self):
        # Test with empty NFT ID
        self.assertIsNone(self.fetcher.get_nft_details(""))
        self.assertIsNone(self.fetcher.get_nft_details(None))
        
        # Test with empty address
        self.assertIsNone(self.fetcher.get_balance(""))
        self.assertIsNone(self.fetcher.get_balance(None))

if __name__ == '__main__':
    unittest.main()