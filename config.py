"""
Configuración centralizada para el backend unificado
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base"""
    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/chat_app')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Servidor
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', None)
    MAX_LOG_SIZE = os.getenv('MAX_LOG_SIZE', '10MB')
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Seguridad
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', 'False').lower() == 'true'
    RATE_LIMIT = int(os.getenv('RATE_LIMIT', 100))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 1800))
    
    # Rendimiento
    WORKERS = int(os.getenv('WORKERS', 4))
    WORKER_TIMEOUT = int(os.getenv('WORKER_TIMEOUT', 30))
    MAX_REQUESTS = int(os.getenv('MAX_REQUESTS', 1000))
    MAX_REQUESTS_JITTER = int(os.getenv('MAX_REQUESTS_JITTER', 50))
    
    # Monitoreo
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'False').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', 9090))
    
    # Notificaciones
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', None)
    SMTP_SERVER = os.getenv('SMTP_SERVER', None)
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', None)
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', None)

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True
    MONGO_URI = os.getenv('MONGO_URI_TEST', 'mongodb://localhost:27017/chat_app_test')

# Mapeo de configuraciones por entorno
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env_name=None):
    """Obtener configuración según el entorno"""
    if env_name is None:
        env_name = os.getenv('FLASK_ENV', 'default')
    
    return config_map.get(env_name, DevelopmentConfig)