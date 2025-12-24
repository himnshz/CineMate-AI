"""
CineMate Care - Configuration Loader

Centralized configuration management for all Azure services.
Validates that all required environment variables are present at startup.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigurationError(ValueError):
    """Raised when required configuration is missing."""
    pass


class Config:
    """
    Centralized configuration for CineMate Care.
    
    Loads Azure credentials from environment variables and validates
    that all required values are present.
    """
    
    # Azure AI Vision (Computer Vision 4.0)
    AZURE_VISION_ENDPOINT: str = ""
    AZURE_VISION_KEY: str = ""
    
    # Azure OpenAI Service (GPT-4o)
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = ""
    
    # Azure Speech Service
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""
    
    # Application Settings
    TTS_VOICE: str = "en-US-DavisNeural"
    WAKE_WORD: str = "CineMate"
    CARE_MODE: str = "active"
    
    _loaded: bool = False
    
    @classmethod
    def load(cls, validate: bool = True) -> None:
        """
        Load configuration from environment variables.
        
        Args:
            validate: If True, raise error for missing required vars
        """
        # Azure AI Vision
        cls.AZURE_VISION_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT", "")
        cls.AZURE_VISION_KEY = os.getenv("AZURE_VISION_KEY", "")
        
        # Azure OpenAI
        cls.AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        cls.AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
        cls.AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv(
            "AZURE_OPENAI_DEPLOYMENT", 
            os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        )
        
        # Azure Speech
        cls.AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
        cls.AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "eastus")
        
        # Application Settings
        cls.TTS_VOICE = os.getenv("TTS_VOICE", "en-US-DavisNeural")
        cls.WAKE_WORD = os.getenv("WAKE_WORD", "CineMate")
        cls.CARE_MODE = os.getenv("CARE_MODE", "active")
        
        cls._loaded = True
        
        if validate:
            cls.validate()
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.
        Raises ConfigurationError with details of missing values.
        """
        missing = []
        
        # Check Azure AI Vision
        if not cls.AZURE_VISION_ENDPOINT:
            missing.append("AZURE_VISION_ENDPOINT")
        if not cls.AZURE_VISION_KEY:
            missing.append("AZURE_VISION_KEY")
        
        # Check Azure OpenAI
        if not cls.AZURE_OPENAI_ENDPOINT:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not cls.AZURE_OPENAI_KEY:
            missing.append("AZURE_OPENAI_KEY")
        
        # Check Azure Speech
        if not cls.AZURE_SPEECH_KEY:
            missing.append("AZURE_SPEECH_KEY")
        
        if missing:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Please copy .env.example to .env and fill in your Azure credentials."
            )
    
    @classmethod
    def validate_vision(cls) -> None:
        """Validate only Vision service credentials."""
        if not cls._loaded:
            cls.load(validate=False)
        
        if not cls.AZURE_VISION_ENDPOINT or not cls.AZURE_VISION_KEY:
            raise ConfigurationError(
                "Azure Vision credentials not configured. "
                "Set AZURE_VISION_ENDPOINT and AZURE_VISION_KEY."
            )
    
    @classmethod
    def validate_openai(cls) -> None:
        """Validate only OpenAI service credentials."""
        if not cls._loaded:
            cls.load(validate=False)
        
        if not cls.AZURE_OPENAI_ENDPOINT or not cls.AZURE_OPENAI_KEY:
            raise ConfigurationError(
                "Azure OpenAI credentials not configured. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY."
            )
    
    @classmethod
    def validate_speech(cls) -> None:
        """Validate only Speech service credentials."""
        if not cls._loaded:
            cls.load(validate=False)
        
        if not cls.AZURE_SPEECH_KEY:
            raise ConfigurationError(
                "Azure Speech credentials not configured. "
                "Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION."
            )
    
    @classmethod
    def get_status(cls) -> dict:
        """Get status of all service configurations."""
        if not cls._loaded:
            cls.load(validate=False)
        
        return {
            "vision": bool(cls.AZURE_VISION_ENDPOINT and cls.AZURE_VISION_KEY),
            "openai": bool(cls.AZURE_OPENAI_ENDPOINT and cls.AZURE_OPENAI_KEY),
            "speech": bool(cls.AZURE_SPEECH_KEY),
        }
    
    @classmethod
    def print_status(cls) -> None:
        """Print configuration status to console."""
        status = cls.get_status()
        print("\n🔧 CineMate Care Configuration Status:")
        print(f"   Azure Vision:  {'✅ Configured' if status['vision'] else '❌ Missing'}")
        print(f"   Azure OpenAI:  {'✅ Configured' if status['openai'] else '❌ Missing'}")
        print(f"   Azure Speech:  {'✅ Configured' if status['speech'] else '❌ Missing'}")
        print()


# Auto-load on import (but don't validate - let caller decide)
Config.load(validate=False)


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("CineMate Care - Configuration Test")
    print("=" * 60)
    
    Config.print_status()
    
    try:
        Config.validate()
        print("✅ All required configuration is present!")
    except ConfigurationError as e:
        print(f"❌ {e}")
