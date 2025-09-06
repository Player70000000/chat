#!/usr/bin/env python3
"""
Script simple para probar la conexión a MongoDB
"""

import os
import sys

def load_env_file():
    """Cargar variables del archivo .env manualmente"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        print("❌ No se encontró archivo .env")
        return None
    
    return env_vars

def test_mongodb_connection():
    """Probar conexión a MongoDB"""
    print("🔍 Probando conexión a MongoDB...")
    
    # Cargar variables de entorno
    env_vars = load_env_file()
    if not env_vars:
        return False
    
    mongo_uri = env_vars.get('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI no encontrada en .env")
        return False
    
    print(f"📡 Intentando conectar a: {mongo_uri}")
    
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure
        
        # Crear cliente
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Probar conexión
        client.admin.command('ping')
        
        # Obtener base de datos
        db = client.chat_app
        
        print("✅ Conexión exitosa a MongoDB")
        print(f"📊 Base de datos: {db.name}")
        
        # Probar operaciones básicas
        print("\n🔧 Probando operaciones básicas...")
        
        # Crear una colección de prueba
        test_collection = db.test_connection
        
        # Insertar documento de prueba
        test_doc = {"test": True, "message": "Prueba de conexión exitosa"}
        result = test_collection.insert_one(test_doc)
        print(f"✅ Inserción exitosa - ID: {result.inserted_id}")
        
        # Leer documento
        found_doc = test_collection.find_one({"_id": result.inserted_id})
        if found_doc:
            print(f"✅ Lectura exitosa - Documento: {found_doc['message']}")
        
        # Limpiar documento de prueba
        test_collection.delete_one({"_id": result.inserted_id})
        print("✅ Limpieza completada")
        
        # Mostrar información del servidor
        server_info = client.server_info()
        print(f"\n📋 Información del servidor:")
        print(f"   Versión MongoDB: {server_info.get('version', 'N/A')}")
        print(f"   Conexión activa: ✅")
        
        client.close()
        return True
        
    except ImportError:
        print("❌ pymongo no está instalado")
        print("   Instala con: pip install pymongo")
        return False
        
    except ConnectionFailure as e:
        print(f"❌ Error de conexión: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def show_configuration():
    """Mostrar configuración actual"""
    print("🚀 Backend Unificado - Empresa Limpieza Chat")
    print("=" * 50)
    
    env_vars = load_env_file()
    if not env_vars:
        return
    
    print("🔧 Configuración actual:")
    print(f"   HOST: {env_vars.get('HOST', 'N/A')}")
    print(f"   PORT: {env_vars.get('PORT', 'N/A')}")
    print(f"   DEBUG: {env_vars.get('DEBUG', 'N/A')}")
    print(f"   FLASK_ENV: {env_vars.get('FLASK_ENV', 'N/A')}")
    
    mongo_uri = env_vars.get('MONGO_URI', '')
    if mongo_uri:
        # Ocultar credenciales si es Atlas
        if '@' in mongo_uri and 'mongodb+srv://' in mongo_uri:
            parts = mongo_uri.split('@')
            safe_uri = f"mongodb+srv://***:***@{parts[1]}"
            print(f"   MONGO_URI: {safe_uri}")
        else:
            print(f"   MONGO_URI: {mongo_uri}")
    else:
        print("   ⚠️ MONGO_URI no configurada")

def show_atlas_instructions():
    """Mostrar instrucciones para MongoDB Atlas"""
    print("\n📖 Para configurar MongoDB Atlas:")
    print("=" * 40)
    print("1. Ve a https://www.mongodb.com/cloud/atlas")
    print("2. Crea una cuenta gratuita")
    print("3. Crea un nuevo cluster (M0 Sandbox - gratis)")
    print("4. Crea un usuario de base de datos:")
    print("   Username: empresalimpieza")
    print("   Password: [tu password seguro]")
    print("5. Configura Network Access:")
    print("   - Permite tu IP actual")
    print("   - O permite 0.0.0.0/0 para desarrollo")
    print("6. Obtén el connection string y actualiza .env:")
    print("   MONGO_URI=mongodb+srv://empresalimpieza:PASSWORD@cluster0.xxxxx.mongodb.net/chat_app?retryWrites=true&w=majority")
    print("\n🔄 Luego ejecuta este script nuevamente para probar")

def main():
    """Función principal"""
    show_configuration()
    
    print("\n" + "="*50)
    
    if test_mongodb_connection():
        print("\n🎉 ¡Configuración correcta! El backend está listo.")
    else:
        print("\n⚠️ Problema de conexión a MongoDB")
        show_atlas_instructions()

if __name__ == "__main__":
    main()