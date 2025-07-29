import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, WriteConcernError
from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

# Configuración básica de logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Variables globales para conexión
db = None
client = None

def init_db():
    """Inicializa la conexión a MongoDB"""
    global db, client
    try:
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            logger.error("MONGO_URI no encontrada en variables de entorno")
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
        
        # Crear índices
        try:
            db.canales.create_index("nombre", unique=True)
            db.mensajes.create_index([("canal", 1), ("timestamp", -1)])
        except Exception:
            pass  # Índices pueden ya existir
            
        return True
        
    except ConnectionFailure as e:
        logger.error(f"Error de conexión a MongoDB: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado en init_db: {e}")
        return False

def initialize():
    """Inicializa la aplicación"""
    if not init_db():
        logger.error("Fallo en inicialización de BD")

# Inicializar la base de datos al arrancar
initialize()

@app.route('/', methods=['GET'])
def pagina_inicio():
    """Página de inicio de la API"""
    try:
        info = {
            "servicio": "Chat API Backend",
            "version": "1.0.0",
            "status": "activo",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "GET /": "Esta página de información",
                "GET /verificar": "Verificar estado del servidor",
                "GET /canales": "Listar canales disponibles",
                "POST /crear_canal": "Crear nuevo canal",
                "POST /enviar": "Enviar mensaje",
                "GET /mensajes/<canal>": "Obtener mensajes de canal",
                "GET /canal/<nombre>": "Obtener información específica de un canal",
                "DELETE /canal/<nombre>": "Eliminar canal y todos sus mensajes"
            }
        }
        
        if db is not None:
            try:
                client.admin.command('ping')
                canales_count = db.canales.count_documents({})
                mensajes_count = db.mensajes.count_documents({})
                info["database"] = {"status": "conectada", "canales": canales_count, "mensajes": mensajes_count}
            except Exception:
                info["database"] = {"status": "error"}
        else:
            info["database"] = {"status": "no_disponible"}
        
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Error en página de inicio: {e}")
        return jsonify({"error": "Error interno"}), 500

@app.route('/verificar', methods=['GET'])
def verificar_conexion():
    """Endpoint de verificación"""
    try:
        info = {
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }
        
        if db is None:
            info["database"] = "no_inicializada"
        else:
            try:
                client.admin.command('ping')
                canales_count = db.canales.count_documents({})
                mensajes_count = db.mensajes.count_documents({})
                info["database"] = "conectada"
                info["canales_count"] = canales_count
                info["mensajes_count"] = mensajes_count
            except Exception as e:
                info["database"] = f"error: {str(e)}"
        
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Error en verificar_conexion: {e}")
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
            
        nombre_canal = datos.get('nombre', '').strip()
        if not nombre_canal:
            return jsonify({"error": "El nombre del canal es obligatorio"}), 400
        
        # Verificar si canal existe
        canal_existente = db.canales.find_one({"nombre": nombre_canal})
        if canal_existente:
            return jsonify({"error": f"El canal '{nombre_canal}' ya existe"}), 400
        
        # Crear canal
        nuevo_canal = {
            "nombre": nombre_canal,
            "creado": datetime.now(),
            "descripcion": datos.get('descripcion', ''),
            "activo": True
        }
        
        resultado = db.canales.insert_one(nuevo_canal)
        
        respuesta = {
            "mensaje": f"Canal '{nombre_canal}' creado exitosamente",
            "canal_id": str(resultado.inserted_id),
            "nombre": nombre_canal,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(respuesta), 201
        
    except (WriteConcernError, OperationFailure) as e:
        logger.error(f"Error de base de datos en crear_canal: {e}")
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as e:
        logger.error(f"Error crítico en crear_canal: {e}")
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
        logger.error(f"Error listando canales: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/canal/<nombre>', methods=['GET'])
def obtener_canal(nombre):
    """Obtener información específica de un canal por su nombre"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Buscar el canal en la base de datos
        canal = db.canales.find_one({"nombre": nombre})
        
        if not canal:
            return jsonify({
                "error": "Canal no encontrado",
                "mensaje": f"El canal '{nombre}' no existe"
            }), 404
        
        # Formatear la fecha de creación
        fecha_creacion = canal.get('creado', '')
        if isinstance(fecha_creacion, datetime):
            fecha_creacion = fecha_creacion.strftime('%d/%m/%Y %H:%M')
        elif isinstance(fecha_creacion, str):
            try:
                # Intentar parsear fecha ISO y convertir
                fecha_obj = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                fecha_creacion = fecha_obj.strftime('%d/%m/%Y %H:%M')
            except:
                fecha_creacion = 'Fecha no disponible'
        else:
            fecha_creacion = 'Fecha no disponible'
        
        # Preparar respuesta con datos básicos del canal
        respuesta = {
            "nombre": canal.get('nombre', ''),
            "descripcion": canal.get('descripcion', 'Sin descripción'),
            "fecha_creacion": fecha_creacion,
            "activo": canal.get('activo', True)
        }
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo canal '{nombre}': {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "mensaje": str(e)
        }), 500

@app.route('/canal/<nombre>', methods=['DELETE'])
def eliminar_canal(nombre):
    """Eliminar un canal y todos sus mensajes"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        nombre_canal = nombre.strip()
        if not nombre_canal:
            return jsonify({"error": "Nombre de canal inválido"}), 400
        
        # Verificar si el canal existe
        canal_existente = db.canales.find_one({"nombre": nombre_canal})
        if not canal_existente:
            return jsonify({
                "error": "Canal no encontrado",
                "mensaje": f"El canal '{nombre_canal}' no existe"
            }), 404
        
        # Contar mensajes antes de eliminar (para estadísticas)
        mensajes_count = db.mensajes.count_documents({"canal": nombre_canal})
        
        # Eliminar todos los mensajes del canal
        resultado_mensajes = db.mensajes.delete_many({"canal": nombre_canal})
        
        # Eliminar el canal
        resultado_canal = db.canales.delete_one({"nombre": nombre_canal})
        
        if resultado_canal.deleted_count == 0:
            return jsonify({
                "error": "No se pudo eliminar el canal",
                "mensaje": "Error en la operación de eliminación"
            }), 500
        
        # Respuesta exitosa con estadísticas
        respuesta = {
            "mensaje": f"Canal '{nombre_canal}' eliminado exitosamente",
            "canal_eliminado": nombre_canal,
            "mensajes_eliminados": resultado_mensajes.deleted_count,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(respuesta), 200
        
    except (WriteConcernError, OperationFailure) as e:
        logger.error(f"Error de base de datos eliminando canal '{nombre}': {e}")
        return jsonify({
            "error": "Error de base de datos",
            "mensaje": "No se pudo completar la eliminación"
        }), 500
    except Exception as e:
        logger.error(f"Error crítico eliminando canal '{nombre}': {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "mensaje": str(e)
        }), 500

@app.route('/enviar', methods=['POST'])
def enviar_mensaje():
    """Enviar mensaje a un canal"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        datos = request.get_json()
        
        if not datos or not datos.get('canal') or not datos.get('mensaje'):
            return jsonify({"error": "Canal y mensaje son obligatorios"}), 400
            
        nuevo_mensaje = {
            "canal": datos['canal'],
            "mensaje": datos['mensaje'],
            "usuario": datos.get('usuario', 'Anónimo'),
            "timestamp": datetime.now()
        }
        
        resultado = db.mensajes.insert_one(nuevo_mensaje)
        
        return jsonify({
            "mensaje": "Mensaje enviado exitosamente",
            "mensaje_id": str(resultado.inserted_id)
        }), 201
        
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/mensajes/<canal>', methods=['GET'])
def obtener_mensajes(canal):
    """Obtener mensajes de un canal"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        mensajes = list(db.mensajes.find(
            {"canal": canal}, 
            {"_id": 0}
        ).sort("timestamp", 1))
        
        return jsonify({"mensajes": mensajes})
        
    except Exception as e:
        logger.error(f"Error obteniendo mensajes: {e}")
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