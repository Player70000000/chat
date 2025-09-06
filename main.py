#!/usr/bin/env python3
"""
Punto de entrada principal para el backend unificado de empresa-limpieza-chat
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar variables de entorno primero
load_dotenv()

from backend.app import create_app
from backend.config import get_config
from backend.config.logging import setup_logging, log_system_info

# Configurar logging según el entorno
config = get_config()
logger = setup_logging(config)
logger = logging.getLogger(__name__)

def main():
    """Función principal del servidor"""
    try:
        # Log información del sistema
        log_system_info()
        
        # Crear aplicación Flask
        logger.info("Creando aplicación Flask...")
        app = create_app()
        
        # Configuración del servidor
        host = config.HOST
        port = config.PORT
        debug = config.DEBUG
        
        logger.info(f"Configuración del servidor:")
        logger.info(f"  Host: {host}")
        logger.info(f"  Puerto: {port}")
        logger.info(f"  Debug: {debug}")
        logger.info(f"  Entorno: {os.getenv('FLASK_ENV', 'development')}")
        
        if debug:
            logger.warning("EJECUTANDO EN MODO DEBUG - NO USAR EN PRODUCCIÓN")
        
        # Ejecutar servidor
        logger.info("Iniciando servidor Flask...")
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Servidor detenido por usuario")
    except Exception as e:
        logger.error(f"Error crítico iniciando servidor: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()