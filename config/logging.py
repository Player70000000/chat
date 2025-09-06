"""
Configuración de logging optimizada para producción
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

def setup_logging(config):
    """
    Configurar sistema de logging según el entorno
    """
    
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configuración base
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para consola
    if config.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Handler para archivo (rotativo)
    if config.LOG_FILE or not config.DEBUG:
        log_file = config.LOG_FILE or str(log_dir / "app.log")
        
        # Asegurar que el directorio del archivo existe
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=parse_size(config.MAX_LOG_SIZE),
            backupCount=config.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Handler específico para errores críticos
    error_log_file = str(log_dir / "error.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=parse_size("5MB"),
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Handler para acceso (requests)
    access_log_file = str(log_dir / "access.log")
    access_handler = logging.handlers.RotatingFileHandler(
        access_log_file,
        maxBytes=parse_size("20MB"),
        backupCount=10
    )
    access_handler.setLevel(logging.INFO)
    access_formatter = logging.Formatter(
        '%(asctime)s - %(remote_addr)s - "%(method)s %(url)s" %(status_code)s - %(response_time)sms'
    )
    access_handler.setFormatter(access_formatter)
    
    # Logger específico para acceso
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_logger.addHandler(access_handler)
    access_logger.propagate = False
    
    # Configurar loggers de terceros
    configure_third_party_loggers(config)
    
    return root_logger

def configure_third_party_loggers(config):
    """Configurar logging de librerías de terceros"""
    
    # Werkzeug (Flask development server)
    werkzeug_logger = logging.getLogger('werkzeug')
    if config.DEBUG:
        werkzeug_logger.setLevel(logging.INFO)
    else:
        werkzeug_logger.setLevel(logging.WARNING)
    
    # PyMongo
    pymongo_logger = logging.getLogger('pymongo')
    pymongo_logger.setLevel(logging.WARNING)
    
    # urllib3
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.WARNING)

def parse_size(size_str):
    """Convertir string de tamaño a bytes"""
    if isinstance(size_str, int):
        return size_str
    
    size_str = size_str.upper().strip()
    
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3
    }
    
    for unit, multiplier in multipliers.items():
        if size_str.endswith(unit):
            size_num = size_str[:-len(unit)].strip()
            return int(float(size_num) * multiplier)
    
    # Si no tiene unidad, asumir bytes
    return int(size_str)

class RequestLogger:
    """Middleware para logging de requests"""
    
    def __init__(self, app):
        self.app = app
        self.access_logger = logging.getLogger('access')
    
    def __call__(self, environ, start_response):
        start_time = datetime.now()
        
        def new_start_response(status, response_headers, exc_info=None):
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log de request
            self.access_logger.info(
                '',
                extra={
                    'remote_addr': environ.get('REMOTE_ADDR', '-'),
                    'method': environ.get('REQUEST_METHOD', '-'),
                    'url': environ.get('PATH_INFO', '-') + 
                           ('?' + environ.get('QUERY_STRING', '') if environ.get('QUERY_STRING') else ''),
                    'status_code': status.split()[0] if status else '-',
                    'response_time': f"{response_time:.2f}"
                }
            )
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, new_start_response)

def log_system_info():
    """Log información del sistema al inicio"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("INICIANDO EMPRESA LIMPIEZA CHAT BACKEND")
    logger.info("=" * 50)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Python: {os.sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info("=" * 50)

def log_database_connection(status, details=None):
    """Log estado de conexión a base de datos"""
    logger = logging.getLogger('database')
    
    if status == 'success':
        logger.info("Conexión a MongoDB establecida exitosamente")
        if details:
            logger.info(f"Base de datos: {details.get('database', 'N/A')}")
            logger.info(f"Colecciones inicializadas: {details.get('collections', 0)}")
    elif status == 'error':
        logger.error(f"Error conectando a MongoDB: {details}")
    elif status == 'retry':
        logger.warning(f"Reintentando conexión a MongoDB... Intento {details}")

def log_security_event(event_type, details):
    """Log eventos de seguridad"""
    security_logger = logging.getLogger('security')
    security_logger.warning(f"EVENTO DE SEGURIDAD - {event_type}: {details}")

def setup_gunicorn_logging():
    """Configuración específica para Gunicorn"""
    # Configurar formato compatible con Gunicorn
    gunicorn_logger = logging.getLogger('gunicorn.error')
    gunicorn_access = logging.getLogger('gunicorn.access')
    
    # Usar los handlers configurados
    app_logger = logging.getLogger()
    gunicorn_logger.handlers = app_logger.handlers
    gunicorn_access.handlers = app_logger.handlers
    
    return gunicorn_logger