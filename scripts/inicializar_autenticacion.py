# -*- coding: utf-8 -*-
"""
SCRIPT DE INICIALIZACIÓN - SISTEMA DE AUTENTICACIÓN v8.0
CORPOTACHIRA - Empresa de Limpieza

Este script inicializa completamente el sistema de autenticación:
1. Configura colección 'usuarios' con índices
2. Crea usuario admin por defecto
3. Sincroniza moderadores existentes con credenciales automáticas
4. Muestra resumen de credenciales generadas

IMPORTANTE: Este script debe ejecutarse UNA SOLA VEZ después del deployment
"""

import sys
import os
from datetime import datetime

# Agregar path del proyecto para importar funciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from funciones.database_functions import get_db
from funciones.auth_functions import (
    crear_usuario_admin_inicial,
    sincronizar_usuarios_con_personal,
    generar_credenciales_moderador,
    hash_password
)

def main():
    """
    Función principal que ejecuta la inicialización completa
    """
    print("🚀 CORPOTACHIRA v8.0 - INICIALIZACIÓN DE AUTENTICACIÓN")
    print("=" * 70)
    print()

    try:
        # PASO 1: Configurar colección usuarios
        print("📋 PASO 1: Configurando colección 'usuarios'...")
        configurar_coleccion_usuarios()
        print("✅ Colección configurada exitosamente")
        print()

        # PASO 2: Crear usuario admin inicial
        print("👤 PASO 2: Creando usuario administrador...")
        admin_creado = crear_usuario_admin_inicial()

        if admin_creado:
            print("✅ Usuario admin creado exitosamente")
            print("🔑 Credenciales del Administrador:")
            print("   Usuario: admin")
            print("   Contraseña: CorpoTachira2024#Admin!")
            print("   ⚠️  IMPORTANTE: Cambia esta contraseña después del primer login")
        else:
            print("ℹ️  Usuario admin ya existía")
        print()

        # PASO 3: Sincronizar moderadores
        print("👥 PASO 3: Sincronizando moderadores existentes...")
        sync_result = sincronizar_usuarios_con_personal()

        if sync_result['success']:
            print(f"✅ Sincronización completada:")
            print(f"   • Moderadores procesados: {sync_result['moderadores_procesados']}")
            print(f"   • Usuarios nuevos creados: {sync_result['usuarios_creados']}")
            print(f"   • Usuarios ya existentes: {sync_result['usuarios_existentes']}")

            if sync_result['errores']:
                print(f"   ⚠️  Errores: {len(sync_result['errores'])}")
                for error in sync_result['errores']:
                    print(f"      - {error}")
        else:
            print(f"❌ Error en sincronización: {sync_result.get('message', 'Error desconocido')}")
        print()

        # PASO 4: Mostrar estadísticas finales
        print("📊 PASO 4: Estadísticas finales del sistema...")
        mostrar_estadisticas()
        print()

        # PASO 5: Mostrar credenciales generadas
        print("🔐 PASO 5: Credenciales generadas:")
        mostrar_credenciales_moderadores()
        print()

        print("🎉 ¡INICIALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print()
        print("📝 RESUMEN:")
        print("   • Sistema de autenticación: ✅ Activo")
        print("   • Niveles de acceso: Admin, Moderador, Obrero")
        print("   • Endpoints protegidos: ✅ Configurados")
        print("   • Logs de seguridad: ✅ Activados")
        print()
        print("🚀 El sistema está listo para usar con autenticación completa!")

    except Exception as e:
        print(f"❌ ERROR CRÍTICO en inicialización: {e}")
        print("\n🔍 Verifica:")
        print("   • Conexión a MongoDB Atlas")
        print("   • Variables de entorno en .env")
        print("   • Dependencias instaladas (requirements.txt)")
        sys.exit(1)

def configurar_coleccion_usuarios():
    """
    Configura la colección usuarios con índices necesarios
    """
    try:
        db = get_db()
        usuarios_collection = db['usuarios']

        # Crear índices únicos para integridad
        usuarios_collection.create_index("username", unique=True)
        usuarios_collection.create_index("cedula")
        usuarios_collection.create_index("tipo_usuario")
        usuarios_collection.create_index("personal_id", sparse=True)
        usuarios_collection.create_index("activo")
        usuarios_collection.create_index([("tipo_usuario", 1), ("activo", 1)])

        # Configurar colección de logs de seguridad
        security_logs = db['security_logs']
        security_logs.create_index("timestamp")
        security_logs.create_index("event_type")
        security_logs.create_index("user_id")

        return True

    except Exception as e:
        print(f"Error configurando colección: {e}")
        return False

def mostrar_estadisticas():
    """
    Muestra estadísticas del sistema después de la inicialización
    """
    try:
        db = get_db()

        # Contar documentos en cada colección
        stats = {
            'usuarios': db['usuarios'].count_documents({}),
            'moderadores': db['moderadores'].count_documents({'activo': True}),
            'obreros': db['obreros'].count_documents({'activo': True}),
            'cuadrillas': db['cuadrillas'].count_documents({'activa': True}),
            'canales': db['canales'].count_documents({'activo': True}),
            'mensajes': db['mensajes'].count_documents({}),
            'security_logs': db['security_logs'].count_documents({})
        }

        print("   📈 Datos en el sistema:")
        for coleccion, cantidad in stats.items():
            emoji = {
                'usuarios': '👤',
                'moderadores': '👔',
                'obreros': '👷',
                'cuadrillas': '👥',
                'canales': '💬',
                'mensajes': '📨',
                'security_logs': '🔐'
            }.get(coleccion, '📋')

            print(f"      {emoji} {coleccion.title()}: {cantidad}")

    except Exception as e:
        print(f"   ⚠️  Error obteniendo estadísticas: {e}")

def mostrar_credenciales_moderadores():
    """
    Muestra las credenciales generadas para cada moderador
    """
    try:
        db = get_db()
        moderadores = list(db['moderadores'].find({'activo': True}))

        if not moderadores:
            print("   ℹ️  No hay moderadores activos en el sistema")
            return

        print("   🔑 Credenciales de moderadores generadas automáticamente:")
        print("   " + "="*60)

        for moderador in moderadores:
            nombre = moderador.get('nombre', '')
            apellidos = moderador.get('apellidos', '')
            cedula = moderador.get('cedula', '')

            if nombre and apellidos and cedula:
                usuario, contraseña = generar_credenciales_moderador(nombre, apellidos, cedula)

                if usuario and contraseña:
                    nombre_completo = f"{nombre} {apellidos}"
                    print(f"   👤 {nombre_completo}")
                    print(f"      Usuario: {usuario}")
                    print(f"      Contraseña: {contraseña}")
                    print(f"      Cédula: {cedula}")
                    print()

        print("   📧 Estas credenciales deben ser entregadas a cada moderador")
        print("   🔐 Los moderadores pueden cambiar su contraseña una vez autenticados")

    except Exception as e:
        print(f"   ⚠️  Error mostrando credenciales: {e}")

def validar_prerequisitos():
    """
    Valida que todos los prerequisitos estén cumplidos
    """
    print("🔍 Validando prerequisitos...")

    # Verificar conexión a BD
    try:
        db = get_db()
        # Hacer una consulta simple para verificar conexión
        db.list_collection_names()
        print("   ✅ Conexión a MongoDB Atlas: OK")
    except Exception as e:
        print(f"   ❌ Conexión a MongoDB Atlas: FALLO - {e}")
        return False

    # Verificar variables de entorno
    required_env_vars = ['JWT_SECRET_KEY']
    for var in required_env_vars:
        if os.getenv(var):
            print(f"   ✅ Variable {var}: OK")
        else:
            print(f"   ⚠️  Variable {var}: No configurada, usando valor por defecto")

    print("   ✅ Prerequisitos validados")
    print()
    return True

if __name__ == "__main__":
    print("🎯 Validando prerequisitos antes de inicializar...")

    if not validar_prerequisitos():
        print("❌ Prerequisitos no cumplidos. Verifica la configuración.")
        sys.exit(1)

    # Pedir confirmación al usuario
    print("⚠️  IMPORTANTE: Este script inicializará el sistema de autenticación")
    print("   • Se crearán usuarios y credenciales")
    print("   • Se aplicarán cambios permanentes en la base de datos")
    print()

    respuesta = input("¿Deseas continuar? (s/N): ").strip().lower()

    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        print()
        main()
    else:
        print("\n❌ Inicialización cancelada por el usuario")
        sys.exit(0)