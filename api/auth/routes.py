import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from ...config.database import get_db, get_db_status

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/status', methods=['GET'])
def verificar_conexion():
    """Verificación de estado del servidor y base de datos"""
    try:
        info = {
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }
        info.update(get_db_status())
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error verificar: {e}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/info', methods=['GET'])
def pagina_inicio():
    """Información del servidor y endpoints disponibles"""
    try:
        return jsonify({
            "servicio": "Chat API Backend",
            "version": "2.0.0",
            "status": "activo",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "auth": {
                    "GET /api/auth/info": "Información del servidor",
                    "GET /api/auth/status": "Estado del servidor",
                    "POST /api/auth/validate": "Validar usuario"
                },
                "channels": {
                    "GET /api/channels/": "Listar canales",
                    "POST /api/channels/": "Crear canal",
                    "GET /api/channels/<nombre>": "Info de canal",
                    "PUT /api/channels/<nombre>": "Editar canal",
                    "DELETE /api/channels/<nombre>": "Eliminar canal"
                },
                "messages": {
                    "POST /api/messages/": "Enviar mensaje",
                    "GET /api/messages/canal/<canal>": "Obtener mensajes",
                    "PUT /api/messages/<id>": "Editar mensaje propio",
                    "DELETE /api/messages/<id>": "Eliminar mensaje propio",
                    "PUT /api/messages/<id>/estado": "Actualizar estado de mensaje"
                },
                "personnel": {
                    "GET /api/personnel/cuadrillas/": "Listar cuadrillas",
                    "POST /api/personnel/cuadrillas/": "Crear cuadrilla",
                    "GET /api/personnel/cuadrillas/<numero>": "Info de cuadrilla",
                    "PUT /api/personnel/cuadrillas/<numero>": "Editar cuadrilla",
                    "DELETE /api/personnel/cuadrillas/<numero>": "Eliminar cuadrilla",
                    "GET /api/personnel/obreros/": "Listar obreros",
                    "POST /api/personnel/obreros/": "Registrar obrero",
                    "GET /api/personnel/obreros/<cedula>": "Info de obrero",
                    "DELETE /api/personnel/obreros/<cedula>": "Eliminar obrero"
                },
                "reports": {
                    "GET /api/reports/personal/resumen": "Resumen de personal",
                    "GET /api/reports/personal/cuadrillas-por-actividad": "Cuadrillas por actividad",
                    "GET /api/reports/chat/resumen": "Resumen de chat",
                    "GET /api/reports/chat/actividad-por-canal": "Actividad por canal",
                    "POST /api/reports/personalizado/rango-fechas": "Reporte personalizado",
                    "GET /api/reports/exportar/<tipo>": "Exportar datos (cuadrillas|obreros|canales)"
                }
            },
            "database": get_db_status()
        })
    except Exception as e:
        logger.error(f"Error inicio: {e}")
        return jsonify({"error": "Error interno"}), 500

# Endpoint para futuras funcionalidades de autenticación
@auth_bp.route('/validate', methods=['POST'])
def validate_user():
    """Validar usuario - placeholder para futuras mejoras"""
    try:
        datos = request.get_json()
        if not datos or not datos.get('usuario'):
            return jsonify({"error": "Usuario requerido"}), 400
        
        usuario = datos.get('usuario', '').strip()
        if not usuario:
            return jsonify({"error": "Usuario no puede estar vacío"}), 400
        
        if len(usuario) > 50:
            return jsonify({"error": "Usuario demasiado largo"}), 400
        
        return jsonify({
            "valid": True,
            "usuario": usuario,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error validar usuario: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500