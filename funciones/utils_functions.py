"""
Funciones de Utilidades
Funciones auxiliares, helpers y endpoints de información del sistema
"""

import logging
from datetime import datetime
from flask import jsonify
from funciones.database_functions import get_db_status

# Logger para este módulo
logger = logging.getLogger(__name__)

# ==================== FUNCIONES AUXILIARES ====================

def format_date(fecha):
    """Formatear fecha de forma consistente"""
    if isinstance(fecha, datetime):
        return fecha.strftime('%d/%m/%Y %H:%M')
    if isinstance(fecha, str):
        try:
            fecha_obj = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
            return fecha_obj.strftime('%d/%m/%Y %H:%M')
        except:
            pass
    return 'Fecha no disponible'

# ==================== ENDPOINTS DEL SISTEMA ====================

def pagina_inicio():
    """Información del servidor"""
    try:
        return jsonify({
            "servicio": "Chat API Backend",
            "version": "2.0.0",  # ACTUALIZADA
            "status": "activo",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "GET /": "Información del servidor",
                "GET /verificar": "Estado del servidor",
                "GET /canales": "Listar canales",
                "POST /crear_canal": "Crear canal",
                "GET /canal/<nombre>": "Info de canal",
                "PUT /canal/<nombre>": "Editar canal",
                "DELETE /canal/<nombre>": "Eliminar canal",
                "POST /enviar": "Enviar mensaje",
                "GET /mensajes/<canal>": "Obtener mensajes",
                # NUEVOS ENDPOINTS
                "PUT /mensaje/<id>": "Editar mensaje propio",
                "DELETE /mensaje/<id>": "Eliminar mensaje propio",
                "PUT /mensaje/<id>/estado": "Actualizar estado de mensaje"
            },
            "database": get_db_status()
        })
    except Exception as e:
        logger.error(f"Error inicio: {e}")
        return jsonify({"error": "Error interno"}), 500

def verificar_conexion():
    """Verificación de estado"""
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

def api_auth_status():
    """Authentication status"""
    return jsonify({
        "authenticated": True,
        "user": "sistema",
        "timestamp": datetime.now().isoformat()
    })

def api_channels_list():
    """List channels - modern endpoint"""
    try:
        from funciones.database_functions import get_db
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        canales = list(db.canales.find({}, {"_id": 0}))
        return jsonify({
            "success": True,
            "channels": canales,
            "count": len(canales)
        })
    except Exception as e:
        logger.error(f"Error api_channels: {e}")
        return jsonify({"error": str(e)}), 500