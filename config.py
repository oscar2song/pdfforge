"""
Configuration Management
"""
import os
import tempfile
from pathlib import Path


class Config:
    """Base configuration"""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or tempfile.mkdtemp()

    # PDF Processing
    LETTER_WIDTH = 612
    LETTER_HEIGHT = 792

    # Standard page sizes (width x height in points)
    PAGE_SIZES = {
        'letter': (612, 792),
        'letter-landscape': (792, 612),
        'legal': (612, 1008),
        'legal-landscape': (1008, 612),
        'A4': (595, 842),
        'a4': (595, 842),
        'a4-landscape': (842, 595),
        'A3': (842, 1191),
        'a3': (842, 1191),
        'a3-landscape': (1191, 842),
        'A5': (420, 595),
        'a5': (420, 595),
    }

    # OCR Settings
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD') or None

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'pdfforge.log'

    # Premium Word (SaaS) Integration
    # Support new generic PREMIUM_* envs with fallback to legacy WORD_PREMIUM_*
    _prem_enabled = os.environ.get('PREMIUM_ENABLED')
    _prem_base = os.environ.get('PREMIUM_BASE_URL')
    _prem_key = os.environ.get('PREMIUM_API_KEY')
    _prem_timeout = os.environ.get('PREMIUM_TIMEOUT_SECONDS')
    _prem_retries = os.environ.get('PREMIUM_RETRIES')
    _prem_proxy = os.environ.get('PREMIUM_DOWNLOAD_PROXY')

    WORD_PREMIUM_ENABLED = (
        (_prem_enabled or os.environ.get('WORD_PREMIUM_ENABLED', 'false')).lower() in {'1', 'true', 'yes', 'on'}
    )
    WORD_PREMIUM_BASE_URL = (_prem_base or os.environ.get('WORD_PREMIUM_BASE_URL') or 'http://localhost:5003')
    WORD_PREMIUM_API_KEY = (_prem_key or os.environ.get('WORD_PREMIUM_API_KEY') or '')
    WORD_PREMIUM_TIMEOUT_SECONDS = int(_prem_timeout or os.environ.get('WORD_PREMIUM_TIMEOUT_SECONDS', '60'))
    WORD_PREMIUM_RETRIES = int(_prem_retries or os.environ.get('WORD_PREMIUM_RETRIES', '0'))  # per user: no retry by default
    WORD_PREMIUM_DOWNLOAD_PROXY = (
        (_prem_proxy or os.environ.get('WORD_PREMIUM_DOWNLOAD_PROXY', 'true')).lower() in {'1', 'true', 'yes', 'on'}
    )


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    def __init__(self):
        """Initialize production config with validation"""
        super().__init__()
        # Only validate SECRET_KEY when actually used, not during import
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY must be set in production")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    UPLOAD_FOLDER = tempfile.mkdtemp()
    SECRET_KEY = 'test-secret-key'


# Use a function to get config to avoid import-time validation issues
def get_config(env=None):
    """Get configuration based on environment"""
    env = env or os.environ.get('FLASK_ENV', 'development')

    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }

    config_class = config_map.get(env, DevelopmentConfig)

    # For production, we need to handle the validation
    if env == 'production':
        try:
            return config_class()
        except ValueError as e:
            print(f"Configuration error: {e}")
            print("Falling back to development configuration")
            return DevelopmentConfig()

    return config_class()


# For backward compatibility
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}