"""Configuration settings for ChronoFlow application"""
import os
from datetime import timedelta

class Config:
    """Application configuration"""
    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/chronoflow_db')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # CORS Configuration
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:3000']
    
    # Application Settings
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))

