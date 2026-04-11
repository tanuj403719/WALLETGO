"""Forecast model for storing predictions"""

class Forecast:
    """Forecast model template"""
    def __init__(self, user_id: str, forecast_data: list, confidence: float):
        self.user_id = user_id
        self.forecast_data = forecast_data
        self.confidence = confidence
    
    # TODO: Add SQLAlchemy model
