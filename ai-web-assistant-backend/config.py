import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR}/storage.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Default models for each provider
    OPENAI_MODEL = "gpt-3.5-turbo"
    CLAUDE_MODEL = "claude-3-sonnet-20240229"
    
    # Common AI settings
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
    
    # Provider settings
    SUPPORTED_PROVIDERS = {
        "openai": ["gpt-4", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-sonnet-20240229"]
    }
