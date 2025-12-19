"""Configuration module for WingBot Python apps"""
import os
from typing import List

class Config:
    """Application configuration"""
    
    PORT = int(os.getenv('PORT', '443'))
    DEBUG_LEVEL = os.getenv('DEBUG_LEVEL', 'normal')
    SERVER_IP = os.getenv('SERVER_IP', 'your_server_ip')
    
    SIMPLEFX_API_KEY = os.getenv('SIMPLEFX_API_KEY', '')
    SIMPLEFX_API_SECRET = os.getenv('SIMPLEFX_API_SECRET', '')
    SIMPLEFX_API_KEY2 = os.getenv('SIMPLEFX_API_KEY2', '')
    SIMPLEFX_API_SECRET2 = os.getenv('SIMPLEFX_API_SECRET2', '') 
    
    @staticmethod
    def validate_api_keys():
        """Validate that SimpleFX API keys are configured"""
        pass
    
    @staticmethod
    def get_api_key_info():
        """Get masked API key info for debugging"""
        def mask_key(key: str) -> str:
            if not key:
                return "NOT SET"
            if len(key) <= 8:
                return "***"
            return f"{key[:4]}...{key[-4:]}"
        
        return {
            'SIMPLEFX_API_KEY': mask_key(Config.SIMPLEFX_API_KEY),
            'SIMPLEFX_API_SECRET': mask_key(Config.SIMPLEFX_API_SECRET),
            'SIMPLEFX_API_KEY2': mask_key(Config.SIMPLEFX_API_KEY2),
            'SIMPLEFX_API_SECRET2': mask_key(Config.SIMPLEFX_API_SECRET2),
            'source': 'shared/config.py'
        }
    SIMPLEFX_API_URL = 'https://rest.simplefx.com/api/v3'
    SIMPLEFX_QUOTES_URL = 'https://web-quotes-core.simplefx.com'
    
    DEFAULT_ACCOUNT_NUMBER = os.getenv('DEFAULT_ACCOUNT_NUMBER', '3028761')
    DEFAULT_ACCOUNT_NUMBER2 = os.getenv('DEFAULT_ACCOUNT_NUMBER2', '3979937')
    
    SECONDARY_API_ACCOUNTS: List[str] = [DEFAULT_ACCOUNT_NUMBER2] if DEFAULT_ACCOUNT_NUMBER2 else []
    ALL_MONITORED_ACCOUNTS: List[str] = [DEFAULT_ACCOUNT_NUMBER] if DEFAULT_ACCOUNT_NUMBER else []
    
    EXTENDED_ACCOUNTS: List[str] = [
        '174225', '3028177', '3028235', '3028450', '3028761', 
        '3037813', '3037814', '3044621', '3047423', '3048221', 
        '3048222', '3048699', '3049696'
    ]
    
    STATUS_AUTH_USERNAME = os.getenv('STATUS_AUTH_USERNAME', 'admin')
    STATUS_AUTH_PASSWORD = os.getenv('STATUS_AUTH_PASSWORD', '')
    STATUS_AUTH2_USERNAME = os.getenv('STATUS_AUTH2_USERNAME', 'admin')
    STATUS_AUTH2_PASSWORD = os.getenv('STATUS_AUTH2_PASSWORD', '')
    
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH = os.path.join(_project_root, 'sfx_historical_orders.db')
    
    if not os.path.exists(DATABASE_PATH):
        _alt_path = os.path.join(os.getcwd(), 'sfx_historical_orders.db')
        if os.path.exists(_alt_path):
            DATABASE_PATH = _alt_path
    
    @staticmethod
    def is_live_account(login_number: str) -> bool:
        """Check if account is a LIVE account"""
        live_accounts = ["3979960", "247341", "3979937"]
        return str(login_number) in live_accounts
    
    @staticmethod
    def should_use_secondary_api(login_number: str) -> bool:
        """Check if account should use secondary API"""
        return str(login_number) in Config.SECONDARY_API_ACCOUNTS or str(login_number) == "3979937"

