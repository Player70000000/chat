import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from backend.config.database import get_db
from backend.utils.validators import (
    validate_message_data, 
    validate_object_id, 
    validate_message_estado
)

logger = logging.getLogger(__name__)
messages_bp = Blueprint('messages', __name__, url_prefix='/api/messages')

@messages_bp.route('/', methods=['POST'])
def enviar_mensaje():
    """Enviar mensaje con estados"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        datos = request.get_json()
        if not datos or not datos.get('canal') or not datos.get('mensaje'):
            return jsonify({"error": "Canal y mensaje son obligatorios"}), 400
        
        # Validar contenido del mensaje
        datos_mensaje, error = validate_message_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        # Estructura mejorada con estados
        documento_mensaje = {
            "canal": datos['canal'],
            "mensaje": datos_mensaje['mensaje'],
            "usuario": datos.get('usuario', 'Anónimo'),
            "timestamp": datetime.now(),
            "estado": "enviado",
            "editado": False,
            "fecha_edicion": None
        }
        
        resultado = db.mensajes.insert_one(documento_mensaje)
        
        return jsonify({
            "mensaje": "Mensaje enviado exitosamente",
            "mensaje_id": str(resultado.inserted_id),
            "estado": "enviado",
            "timestamp": documento_mensaje["timestamp"].isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error enviar mensaje: {e}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/canal/<canal>', methods=['GET'])
def obtener_mensajes(canal):
    """Obtener mensajes de canal con estados"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Incluir _id para permitir edición/eliminación
        mensajes = list(db.mensajes.find(
            {"canal": canal}, 
            {"_id": 1, "canal": 1, "mensaje": 1, "usuario": 1, 
             "timestamp": 1, "estado": 1, "editado": 1, "fecha_edicion": 1}
        ).sort("timestamp", 1))
        
        # Convertir ObjectId a string y asegurar campos por defecto
        for mensaje in mensajes:
            mensaje["_id"] = str(mensaje["_id"])
            mensaje["estado"] = mensaje.get("estado", "enviado")
            mensaje["editado"] = mensaje.get("editado", False)
            mensaje["fecha_edicion"] = mensaje.get("fecha_edicion")
        
        return jsonify({"mensajes": mensajes})
        
    except Exception as e:
        logger.error(f"Error obtener mensajes: {e}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/<mensaje_id>', methods=['PUT'])
def editar_mensaje(mensaje_id):
    """Editar mensaje propio"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Validar ObjectId
        obj_id = validate_object_id(mensaje_id)
        if not obj_id:
            return jsonify({"error": "ID de mensaje inválido"}), 400
        
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
        
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        # Validar usuario (debe ser el autor del mensaje)
        usuario_actual = datos.get('usuario')
        if not usuario_actual:
            return jsonify({"error": "Usuario requerido"}), 400
        
        # Buscar mensaje
        mensaje_original = db.mensajes.find_one({"_id": obj_id})
        if not mensaje_original:
            return jsonify({"error": "Mensaje no encontrado"}), 404
        
        # Verificar que sea el autor
        if mensaje_original.get('usuario') != usuario_actual:
            return jsonify({"error": "Solo puedes editar tus propios mensajes"}), 403
        
        # Validar nuevo contenido
        datos_mensaje, error = validate_message_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        nuevo_mensaje = datos_mensaje['mensaje']
        
        # No editar si el contenido es igual
        if mensaje_original.get('mensaje') == nuevo_mensaje:
            return jsonify({"error": "El mensaje no ha cambiado"}), 400
        
        # Actualizar mensaje
        resultado = db.mensajes.update_one(
            {"_id": obj_id},
            {"$set": {
                "mensaje": nuevo_mensaje,
                "editado": True,
                "fecha_edicion": datetime.now(),
                "estado": "editado"
            }}
        )
        
        if resultado.modified_count == 0:
            return jsonify({"error": "No se pudo actualizar el mensaje"}), 500
        
        return jsonify({
            "mensaje": "Mensaje editado exitosamente",
            "mensaje_id": mensaje_id,
            "nuevo_contenido": nuevo_mensaje,
            "editado": True,
            "fecha_edicion": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error editar mensaje {mensaje_id}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@messages_bp.route('/<mensaje_id>', methods=['DELETE'])
def eliminar_mensaje(mensaje_id):
    """Eliminar mensaje propio"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Validar ObjectId
        obj_id = validate_object_id(mensaje_id)
        if not obj_id:
            return jsonify({"error": "ID de mensaje inválido"}), 400
        
        # Obtener usuario del query parameter o body
        usuario_actual = request.args.get('usuario')
        if not usuario_actual and request.is_json:
            datos = request.get_json()
            usuario_actual = datos.get('usuario') if datos else None
        
        if not usuario_actual:
            return jsonify({"error": "Usuario requerido"}), 400
        
        # Buscar mensaje
        mensaje = db.mensajes.find_one({"_id": obj_id})
        if not mensaje:
            return jsonify({"error": "Mensaje no encontrado"}), 404
        
        # Verificar que sea el autor
        if mensaje.get('usuario') != usuario_actual:
            return jsonify({"error": "Solo puedes eliminar tus propios mensajes"}), 403
        
        # Eliminar mensaje
        resultado = db.mensajes.delete_one({"_id": obj_id})
        
        if resultado.deleted_count == 0:
            return jsonify({"error": "No se pudo eliminar el mensaje"}), 500
        
        return jsonify({
            "mensaje": "Mensaje eliminado exitosamente",
            "mensaje_id": mensaje_id,
            "canal": mensaje.get('canal'),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error eliminar mensaje {mensaje_id}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@messages_bp.route('/<mensaje_id>/estado', methods=['PUT'])
def actualizar_estado_mensaje(mensaje_id):
    """Actualizar estado de mensaje (entregado, leído)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Validar ObjectId
        obj_id = validate_object_id(mensaje_id)
        if not obj_id:
            return jsonify({"error": "ID de mensaje inválido"}), 400
        
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
        
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        nuevo_estado, error = validate_message_estado(datos.get('estado', ''))
        if error:
            return jsonify({"error": error}), 400
        
        # Buscar mensaje
        mensaje = db.mensajes.find_one({"_id": obj_id})
        if not mensaje:
            return jsonify({"error": "Mensaje no encontrado"}), 404
        
        # Actualizar estado
        resultado = db.mensajes.update_one(
            {"_id": obj_id},
            {"$set": {
                "estado": nuevo_estado,
                "fecha_actualizacion_estado": datetime.now()
            }}
        )
        
        if resultado.modified_count == 0:
            return jsonify({"error": "No se pudo actualizar el estado"}), 500
        
        return jsonify({
            "mensaje": "Estado actualizado exitosamente",
            "mensaje_id": mensaje_id,
            "estado_anterior": mensaje.get('estado', 'enviado'),
            "estado_nuevo": nuevo_estado,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error actualizar estado {mensaje_id}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500