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
from funciones.cuadrilla_functions import (
    create_cuadrilla, get_cuadrillas, get_cuadrilla_by_id, update_cuadrilla, delete_cuadrilla, get_next_cuadrilla_number_api, get_obreros_disponibles
)
from funciones.chat_functions import (
    crear_canal, listar_canales, obtener_canal, editar_canal, eliminar_canal,
    enviar_mensaje, obtener_mensajes, editar_mensaje, eliminar_mensaje, actualizar_estado_mensaje
)
from funciones.utils_functions import (
    format_date, pagina_inicio, verificar_conexion, api_auth_status, api_channels_list
)
from funciones.reports_functions import (
    generar_reporte_moderadores, listar_reportes_moderadores,
    generar_reporte_obreros, listar_reportes_obreros,
    generar_reporte_general, listar_reportes_generales, eliminar_reporte_general
)

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')
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

# Cuadrillas routes - gestión de cuadrillas
app.route('/api/personnel/cuadrillas/', methods=['GET'])(get_cuadrillas)
app.route('/api/personnel/cuadrillas/', methods=['POST'])(create_cuadrilla)
app.route('/api/personnel/cuadrillas/<cuadrilla_id>', methods=['GET'])(get_cuadrilla_by_id)
app.route('/api/personnel/cuadrillas/<cuadrilla_id>', methods=['PUT'])(update_cuadrilla)
app.route('/api/personnel/cuadrillas/<cuadrilla_id>', methods=['DELETE'])(delete_cuadrilla)
app.route('/api/personnel/cuadrillas/next-number/', methods=['GET'])(get_next_cuadrilla_number_api)
app.route('/api/personnel/obreros/disponibles/', methods=['GET'])(get_obreros_disponibles)

# Reports routes - gestión de reportes
app.route('/api/reports/moderadores/generar', methods=['POST'])(generar_reporte_moderadores)
app.route('/api/reports/moderadores/listar', methods=['GET'])(listar_reportes_moderadores)
app.route('/api/reports/obreros/generar', methods=['POST'])(generar_reporte_obreros)
app.route('/api/reports/obreros/listar', methods=['GET'])(listar_reportes_obreros)

# Endpoints de reportes generales
@app.route('/api/reports/generales/generar', methods=['POST'])
def api_generar_reporte_general():
    """Endpoint para generar reportes generales de cuadrillas"""
    try:
        reporte_data = request.get_json()
        if not reporte_data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos del reporte"
            }), 400

        return generar_reporte_general(reporte_data)

    except Exception as e:
        logger.error(f"❌ Error en endpoint generar reporte general: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno del servidor: {str(e)}"
        }), 500

app.route('/api/reports/generales/listar', methods=['GET'])(listar_reportes_generales)

@app.route('/api/reports/generales/<reporte_id>', methods=['DELETE'])
def api_eliminar_reporte_general(reporte_id):
    """Endpoint para eliminar reportes generales por ID"""
    try:
        if not reporte_id:
            return jsonify({
                "success": False,
                "error": "ID de reporte requerido"
            }), 400

        return eliminar_reporte_general(reporte_id)

    except Exception as e:
        logger.error(f"❌ Error en endpoint eliminar reporte general: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno del servidor: {str(e)}"
        }), 500

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