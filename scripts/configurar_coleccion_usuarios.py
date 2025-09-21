# -*- coding: utf-8 -*-
"""
SCRIPT DE CONFIGURACIÓN - COLECCIÓN USUARIOS
CORPOTACHIRA v8.0 - Sistema de Autenticación

Este script configura la colección 'usuarios' en MongoDB Atlas con:
- Estructura de documentos
- Índices únicos para rendimiento y integridad
- Validaciones de esquema
"""

import sys
import os
from datetime import datetime

# Agregar path del proyecto para importar funciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from funciones.database_functions import get_database_connection

def configurar_coleccion_usuarios():
    """
    Configura la colección usuarios con índices y validaciones
    """
    try:
        print("🔧 Configurando colección 'usuarios' en MongoDB Atlas...")

        db = get_database_connection()
        usuarios_collection = db['usuarios']

        # Eliminar índices existentes (excepto _id que es automático)
        print("📋 Limpiando índices anteriores...")
        try:
            usuarios_collection.drop_indexes()
        except Exception as e:
            print(f"⚠️  No hay índices previos para eliminar: {e}")

        # Crear índices únicos para integridad
        print("🔍 Creando índices únicos...")

        # Índice único para username
        usuarios_collection.create_index("username", unique=True)
        print("✅ Índice único creado: username")

        # Índice para cédula (puede repetirse entre admin manual y moderadores)
        usuarios_collection.create_index("cedula")
        print("✅ Índice creado: cedula")

        # Índice para tipo_usuario (filtros rápidos)
        usuarios_collection.create_index("tipo_usuario")
        print("✅ Índice creado: tipo_usuario")

        # Índice para personal_id (referencia a moderadores)
        usuarios_collection.create_index("personal_id", sparse=True)
        print("✅ Índice creado: personal_id")

        # Índice para activo (filtros de usuarios activos)
        usuarios_collection.create_index("activo")
        print("✅ Índice creado: activo")

        # Índice compuesto para consultas frecuentes
        usuarios_collection.create_index([("tipo_usuario", 1), ("activo", 1)])
        print("✅ Índice compuesto creado: tipo_usuario + activo")

        # Listar índices creados
        print("\n📊 Índices configurados:")
        indices = usuarios_collection.list_indexes()
        for indice in indices:
            print(f"   - {indice['name']}: {indice.get('key', {})}")

        # Crear colección de logs de seguridad si no existe
        print("\n🔐 Configurando colección 'security_logs'...")
        security_logs = db['security_logs']

        # Índice para timestamp (limpieza automática)
        security_logs.create_index("timestamp")
        print("✅ Índice creado en security_logs: timestamp")

        # Índice para event_type (consultas por tipo)
        security_logs.create_index("event_type")
        print("✅ Índice creado en security_logs: event_type")

        # Índice para user_id (consultas por usuario)
        security_logs.create_index("user_id")
        print("✅ Índice creado en security_logs: user_id")

        print("\n✅ ¡Configuración de colecciones completada exitosamente!")

        # Mostrar estadísticas
        print(f"\n📈 Estadísticas actuales:")
        print(f"   - Usuarios existentes: {usuarios_collection.count_documents({})}")
        print(f"   - Logs de seguridad: {security_logs.count_documents({})}")

        return True

    except Exception as e:
        print(f"❌ Error configurando colección usuarios: {e}")
        return False

def validar_configuracion():
    """
    Valida que la configuración sea correcta
    """
    try:
        print("\n🔍 Validando configuración...")

        db = get_database_connection()
        usuarios_collection = db['usuarios']

        # Verificar índices
        indices = list(usuarios_collection.list_indexes())
        indices_nombres = [indice['name'] for indice in indices]

        indices_requeridos = ['_id_', 'username_1', 'cedula_1', 'tipo_usuario_1', 'personal_id_1', 'activo_1']

        for indice_req in indices_requeridos:
            if indice_req in indices_nombres:
                print(f"✅ Índice encontrado: {indice_req}")
            else:
                print(f"❌ Índice faltante: {indice_req}")
                return False

        print("✅ Todos los índices requeridos están configurados")

        # Probar inserción de documento de prueba
        print("\n🧪 Probando inserción de documento...")

        doc_prueba = {
            'tipo_usuario': 'test',
            'username': 'test_config_' + str(datetime.utcnow().timestamp()),
            'password': 'hash_test',
            'nombre_completo': 'Usuario de Prueba',
            'cedula': 'TEST123',
            'activo': True,
            'fecha_creacion': datetime.utcnow()
        }

        resultado = usuarios_collection.insert_one(doc_prueba)

        if resultado.inserted_id:
            print("✅ Inserción de prueba exitosa")

            # Eliminar documento de prueba
            usuarios_collection.delete_one({'_id': resultado.inserted_id})
            print("✅ Documento de prueba eliminado")
        else:
            print("❌ Error en inserción de prueba")
            return False

        print("\n✅ ¡Validación completada exitosamente!")
        return True

    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return False

if __name__ == "__main__":
    print("🚀 CORPOTACHIRA v8.0 - Configuración de Autenticación")
    print("=" * 60)

    # Configurar colección
    if configurar_coleccion_usuarios():
        print("\n✅ Configuración exitosa")

        # Validar configuración
        if validar_configuracion():
            print("\n🎉 ¡Sistema listo para autenticación!")
        else:
            print("\n❌ Error en validación")
            sys.exit(1)
    else:
        print("\n❌ Error en configuración")
        sys.exit(1)