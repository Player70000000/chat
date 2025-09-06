#!/usr/bin/env python3
"""
Nuevo backend modular para el sistema de chat
Punto de entrada principal que mantiene compatibilidad con la versión anterior
"""

import sys
import os

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"Iniciando servidor modular en puerto {port}")
    print("Endpoints disponibles:")
    print("- Nuevos endpoints RESTful: /api/*")
    print("- Endpoints legacy (compatibilidad): /*")
    app.run(host='0.0.0.0', port=port, debug=False)