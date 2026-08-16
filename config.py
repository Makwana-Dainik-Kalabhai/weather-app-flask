"""
Configuration file for the Weather App
Now using free wttr.in API - no API key needed!
"""
import os

class Config:
    """Main configuration class"""
    
    # Secret key for Flask - needed for sessions and security
    SECRET_KEY = 'dev-secret-key-12345'  # Change this in production
    
    # Debug mode - shows errors in browser (useful for development)
    DEBUG = True
    
    # Weather API settings - USING FREE API (NO KEY NEEDED!)
    WEATHER_API_URL = 'https://wttr.in'  # Free weather API
    WEATHER_API_FORMAT = 'json'  # Get data in JSON format
    
    # Cache settings
    CACHE_TYPE = 'SimpleCache'  # Simple in-memory cache (easy for beginners)
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes in seconds