"""
Funciones de Chat
Maneja todas las operaciones relacionadas con canales, mensajes y validaciones
"""

import re
import logging
from datetime import datetime
from flask import request, jsonify
from pymongo.errors import WriteConcernError, OperationFailure
from bson import ObjectId
from bson.errors import InvalidId
from funciones.database_functions import get_db

# Logger para este módulo
logger = logging.getLogger(__name__)

# ==================== FUNCIONES DE VALIDACIÓN ====================

def validate_canal_data(datos):
    """Validar datos de canal de forma centralizada"""
    nombre = datos.get('nombre', '').strip()
    descripcion = datos.get('descripcion', '').strip()
    
    if not nombre:
        return None, "El nombre del canal es obligatorio"
    
    if len(nombre) > 50:
        return None, "El nombre no puede exceder 50 caracteres"
    
    if len(descripcion) > 300:
        return None, "La descripción no puede exceder 300 caracteres"
    
    if not re.match(r'^[a-zA-Z0-9\s\-_#]+$', nombre):
        return None, "El nombre contiene caracteres no permitidos"
    
    return {"nombre": nombre, "descripcion": descripcion}, None

def validate_message_data(datos):
    """Validar datos de mensaje - NUEVA FUNCIÓN"""
    mensaje = datos.get('mensaje', '').strip()
    
    if not mensaje:
        return None, "El mensaje no puede estar vacío"
    
    if len(mensaje) > 1000:
        return None, "El mensaje no puede exceder 1000 caracteres"
    
    return {"mensaje": mensaje}, None

def validate_object_id(id_string):
    """Validar y convertir string a ObjectId - NUEVA FUNCIÓN"""
    try:
        return ObjectId(id_string)
    except (InvalidId, TypeError):
        return None

# ==================== FUNCIONES DE CANALES ====================

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
        
        return jsonify({
            "nombre": canal.get('nombre', ''),
            "descripcion": canal.get('descripcion', 'Sin descripción'),
            "fecha_creacion": format_date(canal.get('creado', '')),
            "activo": canal.get('activo', True)
        }), 200
        
    except Exception as e:
        logger.error(f"Error obtener canal '{nombre}': {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

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

# ==================== FUNCIONES DE MENSAJES ====================

def enviar_mensaje():
    """Enviar mensaje - MEJORADO CON ESTADOS"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        datos = request.get_json()
        if not datos or not datos.get('canal') or not datos.get('mensaje'):
            return jsonify({"error": "Canal y mensaje son obligatorios"}), 400
        
        # NUEVO: Validar contenido del mensaje
        datos_mensaje, error = validate_message_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        # NUEVO: Estructura mejorada con estados
        documento_mensaje = {
            "canal": datos['canal'],
            "mensaje": datos_mensaje['mensaje'],
            "usuario": datos.get('usuario', 'Anónimo'),
            "timestamp": datetime.now(),
            "estado": "enviado",        # NUEVO: Estado inicial
            "editado": False,           # NUEVO: Flag de edición
            "fecha_edicion": None       # NUEVO: Fecha de última edición
        }
        
        resultado = db.mensajes.insert_one(documento_mensaje)
        
        return jsonify({
            "mensaje": "Mensaje enviado exitosamente",
            "mensaje_id": str(resultado.inserted_id),
            "estado": "enviado",  # NUEVO
            "timestamp": documento_mensaje["timestamp"].isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error enviar mensaje: {e}")
        return jsonify({"error": str(e)}), 500

def obtener_mensajes(canal):
    """Obtener mensajes de canal - MEJORADO CON ESTADOS"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # NUEVO: Incluir _id para permitir edición/eliminación
        mensajes = list(db.mensajes.find(
            {"canal": canal}, 
            {"_id": 1, "canal": 1, "mensaje": 1, "usuario": 1, 
             "timestamp": 1, "estado": 1, "editado": 1, "fecha_edicion": 1}
        ).sort("timestamp", 1))
        
        # NUEVO: Convertir ObjectId a string y asegurar campos por defecto
        for mensaje in mensajes:
            mensaje["_id"] = str(mensaje["_id"])
            mensaje["estado"] = mensaje.get("estado", "enviado")
            mensaje["editado"] = mensaje.get("editado", False)
            mensaje["fecha_edicion"] = mensaje.get("fecha_edicion")
        
        return jsonify({"mensajes": mensajes})
        
    except Exception as e:
        logger.error(f"Error obtener mensajes: {e}")
        return jsonify({"error": str(e)}), 500

def editar_mensaje(mensaje_id):
    """Editar mensaje propio - NUEVO ENDPOINT"""
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
                "estado": "editado"  # Cambiar estado
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

def eliminar_mensaje(mensaje_id):
    """Eliminar mensaje propio - NUEVO ENDPOINT"""
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

def actualizar_estado_mensaje(mensaje_id):
    """Actualizar estado de mensaje (entregado, leído) - NUEVO ENDPOINT"""
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
        
        nuevo_estado = datos.get('estado', '').strip().lower()
        estados_validos = ['enviado', 'entregado', 'leido', 'editado']
        
        if nuevo_estado not in estados_validos:
            return jsonify({
                "error": f"Estado inválido. Estados válidos: {', '.join(estados_validos)}"
            }), 400
        
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