"""
Funciones de Base de Datos
Maneja toda la conexión y operaciones con MongoDB Atlas
"""

import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, WriteConcernError

# Variables globales para conexión
db = None
client = None

# Logger para este módulo
logger = logging.getLogger(__name__)

def init_db():
    """Inicializa la conexión a MongoDB"""
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
        
        # Crear índices si no existen
        try:
            db.canales.create_index("nombre", unique=True)
            db.mensajes.create_index([("canal", 1), ("timestamp", -1)])
            # NUEVO: Índice para buscar mensajes por usuario y estado
            db.mensajes.create_index([("usuario", 1), ("_id", 1)])
            # NUEVO: Índice para moderadores por email (único)
            db.moderadores.create_index("email", unique=True)
            # NUEVO: Índice para obreros por email (único)
            db.obreros.create_index("email", unique=True)
        except:
            pass
            
        logger.info("Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error init_db: {e}")
        return False

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

def get_db():
    """Obtener referencia a la base de datos"""
    return db

def get_client():
    """Obtener referencia al cliente MongoDB"""
    return client