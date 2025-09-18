"""
Configuración de la aplicación móvil
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# URL del backend API
API_BASE_URL = os.getenv('API_URL', 'https://chat-cv1i.onrender.com')

# Configuración del usuario por defecto
DEFAULT_USERNAME = os.getenv('USUARIO', 'UsuarioMovil')

# Configuración de timeouts
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

# Configuración de UI
MOBILE_WINDOW_WIDTH = 360
MOBILE_WINDOW_HEIGHT = 640

# Configuración de colores (Material Design)
THEME_COLORS = {
    'primary': 'Blue',
    'accent': 'Orange',
    'style': 'Light'
}