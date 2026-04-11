"""User model for database"""
from datetime import datetime

class User:
    """User model template"""
    def __init__(self, id: str, email: str, created_at: datetime):
        self.id = id
        self.email = email
        self.created_at = created_at
    
    # TODO: Add SQLAlchemy model
