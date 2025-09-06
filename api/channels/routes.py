import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from pymongo.errors import WriteConcernError, OperationFailure

from ...config.database import get_db
from ...utils.validators import validate_canal_data, format_date

logger = logging.getLogger(__name__)
channels_bp = Blueprint('channels', __name__, url_prefix='/api/channels')

@channels_bp.route('/', methods=['GET'])
def listar_canales():
    """Listar todos los canales"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        canales = list(db.canales.find({}, {"_id": 0}))
        return jsonify({"canales": canales})
        
    except Exception as e:
        logger.error(f"Error listar canales: {e}")
        return jsonify({"error": str(e)}), 500

@channels_bp.route('/', methods=['POST'])
def crear_canal():
    """Crear nuevo canal"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
            
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        datos_validados, error = validate_canal_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        # Verificar existencia
        if db.canales.find_one({"nombre": datos_validados["nombre"]}):
            return jsonify({"error": f"El canal '{datos_validados['nombre']}' ya existe"}), 400
        
        # Crear canal
        resultado = db.canales.insert_one({
            "nombre": datos_validados["nombre"],
            "descripcion": datos_validados["descripcion"],
            "creado": datetime.now(),
            "activo": True
        })
        
        return jsonify({
            "mensaje": f"Canal '{datos_validados['nombre']}' creado exitosamente",
            "canal_id": str(resultado.inserted_id),
            "nombre": datos_validados["nombre"],
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except (WriteConcernError, OperationFailure) as e:
        logger.error(f"Error BD crear_canal: {e}")
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as e:
        logger.error(f"Error crear_canal: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@channels_bp.route('/<nombre>', methods=['GET'])
def obtener_canal(nombre):
    """Obtener información de un canal"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        canal = db.canales.find_one({"nombre": nombre})
        if not canal:
            return jsonify({
                "error": "Canal no encontrado",
                "mensaje": f"El canal '{nombre}' no existe"
            }), 404
        
        return jsonify({
            "nombre": canal.get('nombre', ''),
            "descripcion": canal.get('descripcion', 'Sin descripción'),
            "fecha_creacion": format_date(canal.get('creado', '')),
            "activo": canal.get('activo', True)
        }), 200
        
    except Exception as e:
        logger.error(f"Error obtener canal '{nombre}': {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@channels_bp.route('/<nombre>', methods=['PUT'])
def editar_canal(nombre):
    """Editar canal"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
        
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        nombre_actual = nombre.strip()
        if not nombre_actual:
            return jsonify({"error": "Nombre de canal inválido"}), 400
        
        # Verificar existencia del canal
        if not db.canales.find_one({"nombre": nombre_actual}):
            return jsonify({
                "error": "Canal no encontrado",
                "mensaje": f"El canal '{nombre_actual}' no existe"
            }), 404
        
        # Validar datos
        datos_validados, error = validate_canal_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        nuevo_nombre = datos_validados["nombre"]
        nueva_descripcion = datos_validados["descripcion"]
        nombre_cambio = nuevo_nombre != nombre_actual
        
        # Verificar duplicado si se cambia nombre
        if nombre_cambio and db.canales.find_one({"nombre": nuevo_nombre}):
            return jsonify({
                "error": "Nombre ya utilizado",
                "mensaje": f"Ya existe un canal con el nombre '{nuevo_nombre}'"
            }), 400
        
        # Actualizar canal
        resultado_canal = db.canales.update_one(
            {"nombre": nombre_actual},
            {"$set": {
                "nombre": nuevo_nombre,
                "descripcion": nueva_descripcion,
                "modificado": datetime.now()
            }}
        )
        
        if resultado_canal.modified_count == 0:
            return jsonify({"error": "No se pudo actualizar el canal"}), 500
        
        # Actualizar mensajes si cambió el nombre
        mensajes_actualizados = 0
        if nombre_cambio:
            resultado_mensajes = db.mensajes.update_many(
                {"canal": nombre_actual},
                {"$set": {"canal": nuevo_nombre}}
            )
            mensajes_actualizados = resultado_mensajes.modified_count
        
        return jsonify({
            "mensaje": "Canal actualizado exitosamente",
            "canal_anterior": nombre_actual,
            "canal_nuevo": nuevo_nombre,
            "descripcion": nueva_descripcion,
            "nombre_cambio": nombre_cambio,
            "mensajes_actualizados": mensajes_actualizados,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except (WriteConcernError, OperationFailure) as e:
        logger.error(f"Error BD editar canal '{nombre}': {e}")
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as e:
        logger.error(f"Error editar canal '{nombre}': {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@channels_bp.route('/<nombre>', methods=['DELETE'])
def eliminar_canal(nombre):
    """Eliminar canal y mensajes"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        nombre_canal = nombre.strip()
        if not nombre_canal:
            return jsonify({"error": "Nombre de canal inválido"}), 400
        
        # Verificar existencia
        if not db.canales.find_one({"nombre": nombre_canal}):
            return jsonify({
                "error": "Canal no encontrado",
                "mensaje": f"El canal '{nombre_canal}' no existe"
            }), 404
        
        # Eliminar mensajes y canal
        resultado_mensajes = db.mensajes.delete_many({"canal": nombre_canal})
        resultado_canal = db.canales.delete_one({"nombre": nombre_canal})
        
        if resultado_canal.deleted_count == 0:
            return jsonify({"error": "No se pudo eliminar el canal"}), 500
        
        return jsonify({
            "mensaje": f"Canal '{nombre_canal}' eliminado exitosamente",
            "canal_eliminado": nombre_canal,
            "mensajes_eliminados": resultado_mensajes.deleted_count,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except (WriteConcernError, OperationFailure) as e:
        logger.error(f"Error BD eliminar canal '{nombre}': {e}")
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as e:
        logger.error(f"Error eliminar canal '{nombre}': {e}")
        return jsonify({"error": "Error interno del servidor"}), 500