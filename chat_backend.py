import os
import logging
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.errors import ConnectionFailure, OperationFailure, WriteConcernError
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# NUEVO: Importar funciones modulares
from funciones.database_functions import init_db, get_db_status, get_db, get_client
from funciones.personnel_functions import api_personnel_moderadores, api_personnel_moderadores_create, api_personnel_moderadores_update, api_personnel_moderadores_delete, api_personnel_moderadores_debug, api_personnel_obreros, api_personnel_obreros_create, api_personnel_obreros_update, api_personnel_obreros_delete, api_personnel_obreros_debug
from funciones.chat_functions import (
    crear_canal, listar_canales, obtener_canal, editar_canal, eliminar_canal,
    enviar_mensaje, obtener_mensajes, editar_mensaje, eliminar_mensaje, actualizar_estado_mensaje
)
from funciones.utils_functions import (
    format_date, pagina_inicio, verificar_conexion, api_auth_status, api_channels_list
)

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# NUEVO: Obtener referencias de BD desde el módulo
def get_db_refs():
    """Obtener referencias actualizadas de BD"""
    return get_db(), get_client()

# Variables globales para mantener compatibilidad
db = None
client = None

# Inicializar BD y obtener referencias
init_db()
db, client = get_db_refs()

# ==================== RUTAS MODULARIZADAS ====================
# Todas las rutas ahora usan funciones de módulos externos

# Utility routes - información del sistema
app.route('/', methods=['GET'])(pagina_inicio)
app.route('/verificar', methods=['GET'])(verificar_conexion)
app.route('/api/auth/status', methods=['GET'])(api_auth_status)
app.route('/api/channels/', methods=['GET'])(api_channels_list)

# Chat routes - gestión de canales y mensajes
app.route('/crear_canal', methods=['POST'])(crear_canal)
app.route('/canales', methods=['GET'])(listar_canales)
app.route('/canal/<nombre>', methods=['GET'])(obtener_canal)
app.route('/canal/<nombre>', methods=['PUT'])(editar_canal)
app.route('/canal/<nombre>', methods=['DELETE'])(eliminar_canal)
app.route('/enviar', methods=['POST'])(enviar_mensaje)
app.route('/mensajes/<canal>', methods=['GET'])(obtener_mensajes)
app.route('/mensaje/<mensaje_id>', methods=['PUT'])(editar_mensaje)
app.route('/mensaje/<mensaje_id>', methods=['DELETE'])(eliminar_mensaje)
app.route('/mensaje/<mensaje_id>/estado', methods=['PUT'])(actualizar_estado_mensaje)

# Personnel routes - gestión de personal
app.route('/api/personnel/moderadores/', methods=['GET'])(api_personnel_moderadores)
app.route('/api/personnel/moderadores/', methods=['POST'])(api_personnel_moderadores_create)
app.route('/api/personnel/moderadores/', methods=['PUT'])(api_personnel_moderadores_update)
app.route('/api/personnel/moderadores/', methods=['DELETE'])(api_personnel_moderadores_delete)
app.route('/api/personnel/moderadores/debug', methods=['GET', 'POST', 'PUT', 'DELETE'])(api_personnel_moderadores_debug)

# Obreros routes - gestión de obreros
app.route('/api/personnel/obreros/', methods=['GET'])(api_personnel_obreros)
app.route('/api/personnel/obreros/', methods=['POST'])(api_personnel_obreros_create)
app.route('/api/personnel/obreros/', methods=['PUT'])(api_personnel_obreros_update)
app.route('/api/personnel/obreros/', methods=['DELETE'])(api_personnel_obreros_delete)
app.route('/api/personnel/obreros/debug', methods=['GET', 'POST', 'PUT', 'DELETE'])(api_personnel_obreros_debug)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error 500: {error}")
    return jsonify({"error": "Error interno del servidor"}), 500

# ==================== PUNTO DE ENTRADA ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting modular backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)