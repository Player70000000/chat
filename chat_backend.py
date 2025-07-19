from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import logging
import sys

# Configurar logging más detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuración MongoDB con logs detallados
MONGO_URI = os.getenv('MONGO_URI')
if MONGO_URI:
    MONGO_URI = MONGO_URI.strip()
    logger.info(f"🔗 MONGO_URI cargada (primeros 20 chars): {MONGO_URI[:20]}...")
else:
    logger.error("❌ MONGO_URI no encontrada en variables de entorno")

try:
    # Intentar conexión con diferentes configuraciones
    logger.info("🔄 Intentando conectar a MongoDB...")
    
    # Configuración 1: Con write concern explícito
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
        retryWrites=True,
        w=1,
        wtimeout=5000
    )
    
    # Probar la conexión
    client.admin.command('ping')
    logger.info("✅ Conexión a MongoDB exitosa con w=1")
    
except Exception as e:
    logger.error(f"❌ Error conectando con w=1: {str(e)}")
    try:
        # Fallback: Sin write concern explícito
        logger.info("🔄 Intentando conexión fallback...")
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            retryWrites=False
        )
        client.admin.command('ping')
        logger.info("✅ Conexión fallback exitosa")
    except Exception as e2:
        logger.error(f"❌ Error en conexión fallback: {str(e2)}")
        client = None

if client:
    db = client.chat_db
    mensajes = db.mensajes
    canales = db.canales
    logger.info("📁 Base de datos y colecciones configuradas")
else:
    logger.error("❌ No se pudo establecer conexión con MongoDB")

@app.route('/verificar', methods=['GET'])
def verificar():
    """Endpoint para verificar estado del servidor y MongoDB"""
    try:
        logger.info("🔍 Verificando estado del servidor...")
        
        # Verificar conexión MongoDB
        if not client:
            return jsonify({
                'status': 'error',
                'message': 'No hay conexión a MongoDB',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
            
        # Ping a MongoDB
        client.admin.command('ping')
        
        # Contar documentos en colecciones
        canales_count = canales.count_documents({})
        mensajes_count = mensajes.count_documents({})
        
        logger.info(f"✅ Servidor funcionando - Canales: {canales_count}, Mensajes: {mensajes_count}")
        
        return jsonify({
            'status': 'ok',
            'message': 'Servidor funcionando correctamente',
            'mongodb': 'conectado',
            'canales_count': canales_count,
            'mensajes_count': mensajes_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error en verificación: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error del servidor: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/crear_canal', methods=['POST'])
def crear_canal():
    """Endpoint para crear un nuevo canal con logging extenso"""
    try:
        logger.info("🆕 === INICIANDO CREACIÓN DE CANAL ===")
        
        # Verificar que hay conexión a MongoDB
        if not client:
            logger.error("❌ No hay conexión a MongoDB")
            return jsonify({
                'error': 'No hay conexión a la base de datos'
            }), 500
        
        # Obtener datos del request
        data = request.get_json()
        logger.info(f"📋 Datos recibidos: {data}")
        
        if not data or 'nombre' not in data:
            logger.error("❌ Datos inválidos - falta 'nombre'")
            return jsonify({
                'error': 'Nombre del canal es requerido'
            }), 400
        
        nombre_canal = data['nombre'].strip()
        if not nombre_canal:
            logger.error("❌ Nombre de canal vacío")
            return jsonify({
                'error': 'Nombre del canal no puede estar vacío'
            }), 400
        
        logger.info(f"📝 Creando canal: '{nombre_canal}'")
        
        # Verificar si el canal ya existe
        logger.info("🔍 Verificando si el canal ya existe...")
        canal_existente = canales.find_one({'nombre': nombre_canal})
        
        if canal_existente:
            logger.warning(f"⚠️ Canal '{nombre_canal}' ya existe")
            return jsonify({
                'error': f'El canal "{nombre_canal}" ya existe'
            }), 409
        
        # Preparar documento del canal
        nuevo_canal = {
            'nombre': nombre_canal,
            'creado': datetime.now(timezone.utc),
            'activo': True
        }
        logger.info(f"📄 Documento del canal: {nuevo_canal}")
        
        # Intentar insertar con diferentes estrategias
        logger.info("💾 Intentando insertar canal...")
        
        try:
            # Estrategia 1: Con write concern explícito
            resultado = canales.insert_one(nuevo_canal)
            logger.info(f"✅ Canal insertado exitosamente - ID: {resultado.inserted_id}")
            
        except Exception as insert_error:
            logger.error(f"❌ Error en inserción con w=1: {str(insert_error)}")
            
            try:
                # Estrategia 2: Sin write concern
                logger.info("🔄 Intentando inserción sin write concern...")
                resultado = canales.with_options(write_concern={'w': 0}).insert_one(nuevo_canal)
                logger.info(f"✅ Canal insertado con w=0 - ID: {resultado.inserted_id}")
                
            except Exception as insert_error2:
                logger.error(f"❌ Error en inserción con w=0: {str(insert_error2)}")
                return jsonify({
                    'error': f'Error al guardar el canal: {str(insert_error2)}'
                }), 500
        
        # Verificar que se guardó correctamente
        logger.info("🔍 Verificando que el canal se guardó...")
        canal_guardado = canales.find_one({'nombre': nombre_canal})
        
        if canal_guardado:
            logger.info(f"✅ Canal verificado en base de datos: {canal_guardado['_id']}")
            return jsonify({
                'mensaje': f'Canal "{nombre_canal}" creado exitosamente',
                'canal_id': str(canal_guardado['_id']),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 201
        else:
            logger.error("❌ Canal no encontrado después de inserción")
            return jsonify({
                'error': 'Canal creado pero no se puede verificar'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ ERROR GENERAL en crear_canal: {str(e)}")
        logger.error(f"❌ Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback completo:\n{traceback.format_exc()}")
        
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/canales', methods=['GET'])
def obtener_canales():
    """Obtener lista de canales con logging"""
    try:
        logger.info("📋 Obteniendo lista de canales...")
        
        if not client:
            return jsonify({'error': 'No hay conexión a MongoDB'}), 500
        
        lista_canales = list(canales.find({'activo': True}))
        
        for canal in lista_canales:
            canal['_id'] = str(canal['_id'])
            if 'creado' in canal:
                canal['creado'] = canal['creado'].isoformat()
        
        logger.info(f"✅ Encontrados {len(lista_canales)} canales")
        return jsonify(lista_canales), 200
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo canales: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/enviar', methods=['POST'])
def enviar_mensaje():
    """Enviar mensaje con logging"""
    try:
        logger.info("💬 Enviando mensaje...")
        
        if not client:
            return jsonify({'error': 'No hay conexión a MongoDB'}), 500
        
        data = request.get_json()
        
        if not data or 'canal' not in data or 'mensaje' not in data:
            return jsonify({'error': 'Canal y mensaje son requeridos'}), 400
        
        nuevo_mensaje = {
            'canal': data['canal'],
            'mensaje': data['mensaje'],
            'usuario': data.get('usuario', 'Anónimo'),
            'timestamp': datetime.now(timezone.utc)
        }
        
        resultado = mensajes.insert_one(nuevo_mensaje)
        logger.info(f"✅ Mensaje enviado - ID: {resultado.inserted_id}")
        
        return jsonify({
            'mensaje': 'Mensaje enviado exitosamente',
            'mensaje_id': str(resultado.inserted_id)
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/mensajes', methods=['GET'])
def obtener_mensajes():
    """Obtener mensajes de un canal"""
    try:
        canal = request.args.get('canal')
        if not canal:
            return jsonify({'error': 'Canal es requerido'}), 400
        
        logger.info(f"📨 Obteniendo mensajes del canal: {canal}")
        
        if not client:
            return jsonify({'error': 'No hay conexión a MongoDB'}), 500
        
        lista_mensajes = list(mensajes.find({'canal': canal}).sort('timestamp', 1))
        
        for mensaje in lista_mensajes:
            mensaje['_id'] = str(mensaje['_id'])
            if 'timestamp' in mensaje:
                mensaje['timestamp'] = mensaje['timestamp'].isoformat()
        
        logger.info(f"✅ Encontrados {len(lista_mensajes)} mensajes")
        return jsonify(lista_mensajes), 200
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo mensajes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Error 500: {str(error)}")
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    logger.info("🚀 Iniciando servidor Flask...")
    logger.info(f"🌐 Modo debug: {os.getenv('FLASK_DEBUG', 'False')}")
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🔧 Puerto: {port}, Debug: {debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)