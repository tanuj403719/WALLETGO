"""NatWest API integration service"""
import os
import requests
from typing import List, Dict
from datetime import datetime, timedelta

class NatWestService:
    """Service for NatWest API integration"""
    
    def __init__(self):
        self.api_key = os.getenv('NATWEST_API_KEY')
        self.api_secret = os.getenv('NATWEST_API_SECRET')
        self.sandbox_url = os.getenv('NATWEST_SANDBOX_URL', 'https://api-sandbox.openbanking.natwest.com')
    
    def get_transactions(self, account_id: str, days: int = 90) -> List[Dict]:
        """
        Fetch transactions from NatWest API
        
        Args:
            account_id: NatWest account ID
            days: Number of days of history to fetch
        
        Returns:
            List of transaction dictionaries
        """
        # TODO: Implement NatWest API call
        pass
    
    def get_demo_transactions(self) -> List[Dict]:
        """
        Generate demo transaction data for testing
        
        Returns:
            List of demo transactions
        """
        demo_data = [
            {"date": "2024-03-01", "amount": -1500, "category": "rent", "description": "Rent"},
            {"date": "2024-03-05", "amount": 4000, "category": "income", "description": "Salary"},
            {"date": "2024-03-08", "amount": -85, "category": "groceries", "description": "Weekly shopping"},
            {"date": "2024-03-10", "amount": -15, "category": "subscription", "description": "Netflix"},
            {"date": "2024-03-15", "amount": -120, "category": "dining", "description": "Restaurant"},
            {"date": "2024-03-20", "amount": -50, "category": "transport", "description": "Uber"},
        ]
        return demo_data
    
    def get_recurring_bills(self, account_id: str) -> List[Dict]:
        """
        Identify recurring bills from transaction history
        
        Returns:
            List of recurring bill dictionaries
        """
        # TODO: Implement recurring bill detection
        pass
