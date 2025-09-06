import os
import logging
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, WriteConcernError

# ConfiguraciÃ³n bÃ¡sica de logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Variables globales para conexiÃ³n
db = None
client = None

def init_db():
    """Inicializa la conexiÃ³n a MongoDB"""
    global db, client
    try:
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            logger.error("MONGO_URI no encontrada")
            return False
            
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            retryWrites=True,
            w='majority'
        )
        
        client.admin.command('ping')
        db = client.chat_db
        
        # Crear Ã­ndices si no existen
        try:
            db.canales.create_index("nombre", unique=True)
            db.mensajes.create_index([("canal", 1), ("timestamp", -1)])
        except:
            pass
            
        return True
        
    except Exception as e:
        logger.error(f"Error init_db: {e}")
        return False

# Inicializar BD
init_db()

def get_db_status():
    """Obtener estado de la BD de forma optimizada"""
    if db is None:
        return {"status": "no_disponible"}
    try:
        client.admin.command('ping')
        return {
            "status": "conectada",
            "canales": db.canales.count_documents({}),
            "mensajes": db.mensajes.count_documents({})
        }
    except:
        return {"status": "error"}

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

def validate_canal_data(datos):
    """Validar datos de canal de forma centralizada"""
    nombre = datos.get('nombre', '').strip()
    descripcion = datos.get('descripcion', '').strip()
    
    if not nombre:
        return None, "El nombre del canal es obligatorio"
    
    if len(nombre) > 50:
        return None, "El nombre no puede exceder 50 caracteres"
    
    if len(descripcion) > 300:
        return None, "La descripciÃ³n no puede exceder 300 caracteres"
    
    if not re.match(r'^[a-zA-Z0-9\s\-_#]+$', nombre):
        return None, "El nombre contiene caracteres no permitidos"
    
    return {"nombre": nombre, "descripcion": descripcion}, None

@app.route('/', methods=['GET'])
def pagina_inicio():
    """InformaciÃ³n del servidor"""
    try:
        return jsonify({
            "servicio": "Chat API Backend",
            "version": "1.0.0",
            "status": "activo",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "GET /": "InformaciÃ³n del servidor",
                "GET /verificar": "Estado del servidor",
                "GET /canales": "Listar canales",
                "POST /crear_canal": "Crear canal",
                "GET /canal/<nombre>": "Info de canal",
                "PUT /canal/<nombre>": "Editar canal",
                "DELETE /canal/<nombre>": "Eliminar canal",
                "POST /enviar": "Enviar mensaje",
                "GET /mensajes/<canal>": "Obtener mensajes"
            },
            "database": get_db_status()
        })
    except Exception as e:
        logger.error(f"Error inicio: {e}")
        return jsonify({"error": "Error interno"}), 500

@app.route('/verificar', methods=['GET'])
def verificar_conexion():
    """VerificaciÃ³n de estado"""
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

@app.route('/crear_canal', methods=['POST'])
def crear_canal():
    """Crear nuevo canal"""
    try:
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

@app.route('/canales', methods=['GET'])
def listar_canales():
    """Listar todos los canales"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        canales = list(db.canales.find({}, {"_id": 0}))
        return jsonify({"canales": canales})
        
    except Exception as e:
        logger.error(f"Error listar canales: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/canal/<nombre>', methods=['GET'])
def obtener_canal(nombre):
    """Obtener informaciÃ³n de un canal"""
    try:
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
            "descripcion": canal.get('descripcion', 'Sin descripciÃ³n'),
            "fecha_creacion": format_date(canal.get('creado', '')),
            "activo": canal.get('activo', True)
        }), 200
        
    except Exception as e:
        logger.error(f"Error obtener canal '{nombre}': {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/canal/<nombre>', methods=['PUT'])
def editar_canal(nombre):
    """Editar canal"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
        
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        nombre_actual = nombre.strip()
        if not nombre_actual:
            return jsonify({"error": "Nombre de canal invÃ¡lido"}), 400
        
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
        
        # Actualizar mensajes si cambiÃ³ el nombre
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

@app.route('/canal/<nombre>', methods=['DELETE'])
def eliminar_canal(nombre):
    """Eliminar canal y mensajes"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        nombre_canal = nombre.strip()
        if not nombre_canal:
            return jsonify({"error": "Nombre de canal invÃ¡lido"}), 400
        
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

@app.route('/enviar', methods=['POST'])
def enviar_mensaje():
    """Enviar mensaje"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        datos = request.get_json()
        if not datos or not datos.get('canal') or not datos.get('mensaje'):
            return jsonify({"error": "Canal y mensaje son obligatorios"}), 400
        
        resultado = db.mensajes.insert_one({
            "canal": datos['canal'],
            "mensaje": datos['mensaje'],
            "usuario": datos.get('usuario', 'AnÃ³nimo'),
            "timestamp": datetime.now()
        })
        
        return jsonify({
            "mensaje": "Mensaje enviado exitosamente",
            "mensaje_id": str(resultado.inserted_id)
        }), 201
        
    except Exception as e:
        logger.error(f"Error enviar mensaje: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/mensajes/<canal>', methods=['GET'])
def obtener_mensajes(canal):
    """Obtener mensajes de canal"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        mensajes = list(db.mensajes.find(
            {"canal": canal}, 
            {"_id": 0}
        ).sort("timestamp", 1))
        
        return jsonify({"mensajes": mensajes})
        
    except Exception as e:
        logger.error(f"Error obtener mensajes: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error 500: {error}")
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)