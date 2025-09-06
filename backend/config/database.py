import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)

# Variables globales para conexión
db = None
client = None

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
            db.mensajes.create_index([("usuario", 1), ("_id", 1)])
        except:
            pass
            
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
    """Obtener instancia de base de datos"""
    return db