"""
LEX - Lender Eligibility X
Configuration Module

This module handles all configuration loading from environment variables
and provides safe defaults. It uses python-dotenv to load .env files.
"""

import os
from pathlib import Path
from typing import Optional

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    # Load from .env file in the project root
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    ENV_FILE_LOADED = env_path.exists()
except ImportError:
    # python-dotenv not installed, will rely on system environment variables
    ENV_FILE_LOADED = False


class Config:
    """Configuration class that loads from environment variables."""
    
    # ==================================================
    # GEMINI API CONFIGURATION
    # ==================================================
    
    @staticmethod
    def get_gemini_api_key() -> Optional[str]:
        """
        Get Gemini API key from environment variables.
        Priority: GEMINI_API_KEY > None
        
        Returns:
            API key string or None if not configured
        """
        return os.getenv("GEMINI_API_KEY")
    
    @staticmethod
    def get_model_name() -> str:
        """
        Get the Gemini model name to use.
        
        Returns:
            Model name string with default fallback
        """
        return os.getenv("GEMINI_MODEL_NAME", "models/gemini-1.5-pro-latest")
    
    # ==================================================
    # APPLICATION CONFIGURATION
    # ==================================================
    
    @staticmethod
    def get_app_password() -> str:
        """
        Get application password for user authentication.
        
        Returns:
            Password string with default fallback
        """
        return os.getenv("APP_PASSWORD", "lex444")
    
    @staticmethod
    def get_admin_email_domain() -> str:
        """
        Get admin email domain suffix for admin access.
        
        Returns:
            Domain string (e.g., '@admin.lex')
        """
        return os.getenv("ADMIN_EMAIL_DOMAIN", "@admin.lex")
    
    # ==================================================
    # FILE PATHS
    # ==================================================
    
    @staticmethod
    def get_pdf_directory() -> str:
        """
        Get path to directory containing lender PDF files.
        
        Returns:
            Path string (absolute or relative)
        """
        default_path = str(Path(__file__).parent / "lender_pdf_database")
        return os.getenv("LENDER_PDF_DIR", default_path)
    
    @staticmethod
    def get_logo_path() -> str:
        """
        Get path to logo file.
        
        Returns:
            Path string (absolute or relative)
        """
        return os.getenv("LOGO_PATH", "logo.png")
    
    # ==================================================
    # VALIDATION & HELPERS
    # ==================================================
    
    @staticmethod
    def is_configured() -> bool:
        """
        Check if the application is properly configured with required values.
        
        Returns:
            True if API key is configured, False otherwise
        """
        return Config.get_gemini_api_key() is not None
    
    @staticmethod
    def get_config_status() -> dict:
        """
        Get current configuration status for debugging.
        
        Returns:
            Dictionary with configuration status
        """
        api_key = Config.get_gemini_api_key()
        return {
            "env_file_loaded": ENV_FILE_LOADED,
            "api_key_configured": api_key is not None,
            "api_key_length": len(api_key) if api_key else 0,
            "model_name": Config.get_model_name(),
            "pdf_directory": Config.get_pdf_directory(),
            "password_configured": bool(Config.get_app_password()),
        }
    
    @staticmethod
    def validate_and_get_errors() -> list[str]:
        """
        Validate configuration and return any errors.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not Config.get_gemini_api_key():
            errors.append(
                "❌ GEMINI_API_KEY not configured. "
                "Please set it in .env file or environment variables."
            )
        
        pdf_dir = Path(Config.get_pdf_directory())
        if not pdf_dir.exists():
            errors.append(
                f"❌ PDF directory not found: {pdf_dir}\n"
                "Please update LENDER_PDF_DIR in .env file."
            )
        
        return errors


# Create a singleton instance for easy importing
config = Config()


# For backwards compatibility and convenience
def get_api_key() -> Optional[str]:
    """Get Gemini API key."""
    return config.get_gemini_api_key()


def get_model_name() -> str:
    """Get model name."""
    return config.get_model_name()


def get_app_password() -> str:
    """Get application password."""
    return config.get_app_password()


def get_pdf_directory() -> str:
    """Get PDF directory path."""
    return config.get_pdf_directory()

