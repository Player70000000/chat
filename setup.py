#!/usr/bin/env python3
"""
Script de configuración para el backend unificado
"""

import os
import sys
from dotenv import load_dotenv

def setup_environment():
    """Configurar entorno de desarrollo"""
    
    print("🚀 Configuración del Backend Unificado - Empresa Limpieza Chat")
    print("=" * 60)
    
    # Verificar si existe .env
    env_path = ".env"
    env_example_path = ".env.example"
    
    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            print("📄 Creando archivo .env desde .env.example...")
            with open(env_example_path, 'r') as example:
                content = example.read()
            with open(env_path, 'w') as env_file:
                env_file.write(content)
            print("✅ Archivo .env creado exitosamente")
        else:
            print("❌ No se encontró .env.example")
            return False
    else:
        print("✅ Archivo .env ya existe")
    
    # Cargar variables de entorno
    load_dotenv()
    
    print("\n🔧 Configuración actual:")
    print(f"HOST: {os.getenv('HOST', '0.0.0.0')}")
    print(f"PORT: {os.getenv('PORT', '5000')}")
    print(f"DEBUG: {os.getenv('DEBUG', 'False')}")
    print(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'development')}")
    
    mongo_uri = os.getenv('MONGO_URI', '')
    if mongo_uri:
        # Ocultar password en el output
        if '@' in mongo_uri and 'mongodb+srv://' in mongo_uri:
            safe_uri = mongo_uri.split('@')[1]
            print(f"MONGO_URI: mongodb+srv://***:***@{safe_uri}")
        else:
            print(f"MONGO_URI: {mongo_uri}")
    else:
        print("⚠️  MONGO_URI no configurada")
    
    print("\n📋 Instrucciones:")
    print("1. Edita el archivo .env con tu configuración de MongoDB")
    print("2. Para MongoDB Atlas:")
    print("   - Crea una cuenta en https://www.mongodb.com/cloud/atlas")
    print("   - Configura un cluster")
    print("   - Crea un usuario de base de datos")
    print("   - Configura Network Access")
    print("   - Copia el connection string al archivo .env")
    print("3. Ejecuta: python main.py")
    
    return True

def check_dependencies():
    """Verificar dependencias"""
    print("\n📦 Verificando dependencias...")
    
    required_packages = [
        'flask',
        'flask_cors', 
        'pymongo',
        'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print(f"\n⚠️  Instala las dependencias faltantes:")
        print(f"pip install {' '.join(missing)}")
        print("o ejecuta: pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def test_connection():
    """Probar conexión a MongoDB"""
    print("\n🔍 Probando conexión a MongoDB...")
    
    try:
        from config.database import init_db, get_db_status
        
        if init_db():
            status = get_db_status()
            if status["status"] == "conectada":
                print("✅ Conexión a MongoDB exitosa")
                print(f"Base de datos: chat_app")
                print(f"Colecciones inicializadas correctamente")
                return True
            else:
                print(f"❌ Error de conexión: {status}")
        else:
            print("❌ No se pudo inicializar la base de datos")
            
    except Exception as e:
        print(f"❌ Error al probar conexión: {e}")
    
    return False

def main():
    """Función principal"""
    print("Iniciando configuración...")
    
    # Cambiar al directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Configurar entorno
    if not setup_environment():
        print("❌ Error en configuración del entorno")
        sys.exit(1)
    
    # Verificar dependencias
    if not check_dependencies():
        print("❌ Dependencias faltantes")
        sys.exit(1)
    
    # Probar conexión (opcional)
    answer = input("\n¿Probar conexión a MongoDB? (y/n): ").lower()
    if answer in ['y', 'yes', 'sí', 's']:
        test_connection()
    
    print("\n🎉 Configuración completada!")
    print("Ejecuta 'python main.py' para iniciar el servidor")

if __name__ == "__main__":
    main()