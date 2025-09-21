import os
import logging
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.errors import ConnectionFailure, OperationFailure, WriteConcernError
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# NUEVO: Importar funciones modulares
from funciones.database_functions import init_db, get_db_status, get_db, get_client
from funciones.personnel_functions import api_personnel_moderadores, api_personnel_moderadores_create, api_personnel_moderadores_update, api_personnel_moderadores_delete, api_personnel_moderadores_debug, api_personnel_obreros, api_personnel_obreros_create, api_personnel_obreros_update, api_personnel_obreros_delete, api_personnel_obreros_debug
from funciones.cuadrilla_functions import (
    create_cuadrilla, get_cuadrillas, get_cuadrilla_by_id, update_cuadrilla, delete_cuadrilla, get_next_cuadrilla_number_api, get_obreros_disponibles
)
from funciones.chat_functions import (
    crear_canal, listar_canales, obtener_canal, editar_canal, eliminar_canal,
    enviar_mensaje, obtener_mensajes, editar_mensaje, eliminar_mensaje, actualizar_estado_mensaje
)
from funciones.utils_functions import (
    format_date, pagina_inicio, verificar_conexion, api_auth_status, api_channels_list
)
from funciones.reports_functions import (
    generar_reporte_moderadores, listar_reportes_moderadores, eliminar_reporte_moderadores,
    generar_reporte_obreros, listar_reportes_obreros, eliminar_reporte_obreros,
    generar_reporte_general, listar_reportes_generales, eliminar_reporte_general
)
# NUEVO v8.0: Sistema de Autenticación y Niveles de Acceso
from funciones.auth_functions import (
    login_admin_moderador, login_obrero, verificar_sesion_activa, cambiar_password,
    middleware_verificar_autenticacion, middleware_verificar_permisos,
    crear_usuario_admin_inicial, sincronizar_usuarios_con_personal, log_security_event
)

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# NUEVO: Obtener referencias de BD desde el módulo
def get_db_refs():
    """Obtener referencias actualizadas de BD"""
    return get_db(), get_client()

# Variables globales para mantener compatibilidad
db = None
client = None

# Inicializar BD y obtener referencias
init_db()
db, client = get_db_refs()

# ==================== RUTAS MODULARIZADAS ====================
# Todas las rutas ahora usan funciones de módulos externos

# Utility routes - información del sistema
app.route('/', methods=['GET'])(pagina_inicio)
app.route('/verificar', methods=['GET'])(verificar_conexion)
app.route('/api/auth/status', methods=['GET'])(api_auth_status)
app.route('/api/channels/', methods=['GET'])(api_channels_list)

# ==================== ENDPOINTS DE AUTENTICACIÓN v8.0 ====================

@app.route('/api/auth/login/admin-moderador', methods=['POST'])
def api_login_admin_moderador():
    """
    Endpoint para login de Admin y Moderadores
    Requiere: username y password
    """
    try:
        datos_login = request.get_json()
        if not datos_login:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos de login',
                'code': 'NO_DATA'
            }), 400

        username = datos_login.get('username', '').strip()
        password = datos_login.get('password', '').strip()

        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Usuario y contraseña son requeridos',
                'code': 'MISSING_CREDENTIALS'
            }), 400

        # Procesar login
        resultado = login_admin_moderador(username, password)

        if resultado['success']:
            # Log evento de seguridad exitoso
            log_security_event('login_success', {
                'username': username,
                'tipo_usuario': resultado.get('user_data', {}).get('tipo_usuario', 'unknown')
            })
            return jsonify(resultado), 200
        else:
            # Log evento de seguridad fallido
            log_security_event('login_failed', {
                'username': username,
                'error_code': resultado.get('code', 'UNKNOWN'),
                'error_message': resultado.get('message', 'Error desconocido')
            })
            return jsonify(resultado), 401

    except Exception as e:
        logger.error(f"❌ Error en login admin/moderador: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'code': 'SERVER_ERROR'
        }), 500

@app.route('/api/auth/login/obrero', methods=['POST'])
def api_login_obrero():
    """
    Endpoint para login de Obreros
    Solo requiere: cedula (sin contraseña)
    """
    try:
        datos_login = request.get_json()
        if not datos_login:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos de login',
                'code': 'NO_DATA'
            }), 400

        cedula = datos_login.get('cedula', '').strip()

        if not cedula:
            return jsonify({
                'success': False,
                'message': 'Cédula es requerida',
                'code': 'MISSING_CEDULA'
            }), 400

        # Validar formato de cédula
        if not cedula.isdigit() or len(cedula) < 6 or len(cedula) > 10:
            return jsonify({
                'success': False,
                'message': 'Cédula debe tener entre 6 y 10 dígitos',
                'code': 'INVALID_CEDULA_FORMAT'
            }), 400

        # Procesar login
        resultado = login_obrero(cedula)

        if resultado['success']:
            # Log evento de seguridad exitoso
            log_security_event('login_success', {
                'cedula': cedula,
                'tipo_usuario': 'obrero'
            })

        return jsonify(resultado), 200 if resultado['success'] else 401

    except Exception as e:
        logger.error(f"❌ Error en login obrero: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'code': 'SERVER_ERROR'
        }), 500

@app.route('/api/auth/initialize-system', methods=['POST'])
def api_initialize_system():
    """
    Endpoint temporal para inicializar el sistema de autenticación
    Crea usuario admin inicial y sincroniza moderadores
    SOLO PARA SETUP INICIAL - SERÁ REMOVIDO DESPUÉS
    """
    try:
        resultado_inicializacion = {
            'admin_creado': False,
            'sync_resultado': None,
            'errores': []
        }

        # Verificar si ya existe usuario admin
        db = get_db()
        usuarios_collection = db['usuarios']

        admin_existente = usuarios_collection.find_one({'username': 'admin'})
        if admin_existente:
            resultado_inicializacion['admin_creado'] = True
            resultado_inicializacion['mensaje_admin'] = 'Usuario admin ya existía'
        else:
            # Crear usuario admin inicial
            admin_creado = crear_usuario_admin_inicial()
            resultado_inicializacion['admin_creado'] = admin_creado
            resultado_inicializacion['mensaje_admin'] = 'Usuario admin creado exitosamente' if admin_creado else 'Error creando admin'

        # Sincronizar moderadores existentes
        try:
            sync_result = sincronizar_usuarios_con_personal()
            resultado_inicializacion['sync_resultado'] = sync_result
        except Exception as e:
            resultado_inicializacion['errores'].append(f"Error en sincronización: {str(e)}")

        return jsonify({
            'success': True,
            'message': 'Sistema inicializado correctamente',
            'resultado': resultado_inicializacion
        }), 200

    except Exception as e:
        logger.error(f"❌ Error inicializando sistema: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error inicializando sistema: {str(e)}',
            'code': 'INIT_ERROR'
        }), 500

@app.route('/api/auth/verificar-sesion', methods=['GET'])
@middleware_verificar_autenticacion()
def api_verificar_sesion():
    """
    Endpoint para verificar si la sesión actual es válida
    Requiere token JWT en header Authorization
    """
    try:
        # El middleware ya verificó el token, user_data está disponible
        user_data = request.user_data

        return jsonify({
            'success': True,
            'message': 'Sesión válida',
            'user_data': {
                'id': user_data.get('user_id'),
                'username': user_data.get('username'),
                'tipo_usuario': user_data.get('tipo_usuario'),
                'nombre_completo': user_data.get('nombre_completo'),
                'cedula': user_data.get('cedula'),
                'activo': user_data.get('activo')
            }
        }), 200

    except Exception as e:
        logger.error(f"❌ Error verificando sesión: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error verificando sesión',
            'code': 'SESSION_ERROR'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
@middleware_verificar_autenticacion()
def api_logout():
    """
    Endpoint para cerrar sesión
    Invalida el token actual y registra el evento
    """
    try:
        user_data = request.user_data

        # Log evento de logout
        log_security_event('logout', {
            'user_id': user_data.get('user_id'),
            'username': user_data.get('username'),
            'tipo_usuario': user_data.get('tipo_usuario')
        })

        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        }), 200

    except Exception as e:
        logger.error(f"❌ Error en logout: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error cerrando sesión',
            'code': 'LOGOUT_ERROR'
        }), 500

@app.route('/api/auth/cambiar-password', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def api_cambiar_password():
    """
    Endpoint para cambiar contraseña
    Solo para admin y moderadores (obreros no tienen contraseña)
    """
    try:
        user_data = request.user_data
        datos_cambio = request.get_json()

        if not datos_cambio:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos',
                'code': 'NO_DATA'
            }), 400

        password_actual = datos_cambio.get('password_actual', '').strip()
        password_nueva = datos_cambio.get('password_nueva', '').strip()

        if not password_actual or not password_nueva:
            return jsonify({
                'success': False,
                'message': 'Contraseña actual y nueva son requeridas',
                'code': 'MISSING_PASSWORDS'
            }), 400

        # Procesar cambio de contraseña
        resultado = cambiar_password(
            user_data['user_id'],
            password_actual,
            password_nueva
        )

        if resultado['success']:
            # Log evento de seguridad
            log_security_event('password_change', {
                'user_id': user_data['user_id'],
                'username': user_data.get('username')
            })

        return jsonify(resultado), 200 if resultado['success'] else 400

    except Exception as e:
        logger.error(f"❌ Error cambiando contraseña: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'code': 'SERVER_ERROR'
        }), 500

@app.route('/api/auth/inicializar-sistema', methods=['POST'])
def api_inicializar_sistema():
    """
    Endpoint para inicializar el sistema de autenticación
    Crea admin inicial y sincroniza moderadores
    SOLO SE USA UNA VEZ AL INSTALAR
    """
    try:
        # Crear admin inicial
        admin_creado = crear_usuario_admin_inicial()

        # Sincronizar moderadores
        sync_result = sincronizar_usuarios_con_personal()

        return jsonify({
            'success': True,
            'message': 'Sistema de autenticación inicializado',
            'admin_creado': admin_creado,
            'sincronizacion': sync_result
        }), 200

    except Exception as e:
        logger.error(f"❌ Error inicializando sistema: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error inicializando sistema de autenticación',
            'code': 'INIT_ERROR'
        }), 500

# Chat routes - gestión de canales y mensajes CON AUTENTICACIÓN v8.0
# Obreros pueden LEER, Admin/Moderador pueden TODO

@app.route('/crear_canal', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_crear_canal():
    return crear_canal()

@app.route('/canales', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador', 'obrero'])
def secured_listar_canales():
    return listar_canales()

@app.route('/canal/<nombre>', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador', 'obrero'])
def secured_obtener_canal(nombre):
    return obtener_canal(nombre)

@app.route('/canal/<nombre>', methods=['PUT'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_editar_canal(nombre):
    return editar_canal(nombre)

@app.route('/canal/<nombre>', methods=['DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_eliminar_canal(nombre):
    return eliminar_canal(nombre)

@app.route('/enviar', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_enviar_mensaje():
    return enviar_mensaje()

@app.route('/mensajes/<canal>', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador', 'obrero'])
def secured_obtener_mensajes(canal):
    return obtener_mensajes(canal)

@app.route('/mensaje/<mensaje_id>', methods=['PUT'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_editar_mensaje(mensaje_id):
    return editar_mensaje(mensaje_id)

@app.route('/mensaje/<mensaje_id>', methods=['DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_eliminar_mensaje(mensaje_id):
    return eliminar_mensaje(mensaje_id)

@app.route('/mensaje/<mensaje_id>/estado', methods=['PUT'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_actualizar_estado_mensaje(mensaje_id):
    return actualizar_estado_mensaje(mensaje_id)

# Personnel routes - gestión de personal CON AUTENTICACIÓN v8.0
# Moderadores - Solo ADMIN puede gestionar moderadores
@app.route('/api/personnel/moderadores/', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin'])
def secured_api_personnel_moderadores():
    return api_personnel_moderadores()

@app.route('/api/personnel/moderadores/', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin'])
def secured_api_personnel_moderadores_create():
    return api_personnel_moderadores_create()

@app.route('/api/personnel/moderadores/', methods=['PUT'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin'])
def secured_api_personnel_moderadores_update():
    return api_personnel_moderadores_update()

@app.route('/api/personnel/moderadores/', methods=['DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin'])
def secured_api_personnel_moderadores_delete():
    return api_personnel_moderadores_delete()

@app.route('/api/personnel/moderadores/debug', methods=['GET', 'POST', 'PUT', 'DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin'])
def secured_api_personnel_moderadores_debug():
    return api_personnel_moderadores_debug()

# Obreros routes - gestión de obreros (Admin + Moderador)
@app.route('/api/personnel/obreros/', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_api_personnel_obreros():
    return api_personnel_obreros()

@app.route('/api/personnel/obreros/', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_api_personnel_obreros_create():
    return api_personnel_obreros_create()

@app.route('/api/personnel/obreros/', methods=['PUT'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_api_personnel_obreros_update():
    return api_personnel_obreros_update()

@app.route('/api/personnel/obreros/', methods=['DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_api_personnel_obreros_delete():
    return api_personnel_obreros_delete()

@app.route('/api/personnel/obreros/debug', methods=['GET', 'POST', 'PUT', 'DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_api_personnel_obreros_debug():
    return api_personnel_obreros_debug()

# Cuadrillas routes - gestión de cuadrillas (Admin + Moderador)
@app.route('/api/personnel/cuadrillas/', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_get_cuadrillas():
    return get_cuadrillas()

@app.route('/api/personnel/cuadrillas/', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_create_cuadrilla():
    return create_cuadrilla()

@app.route('/api/personnel/cuadrillas/<cuadrilla_id>', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_get_cuadrilla_by_id(cuadrilla_id):
    return get_cuadrilla_by_id(cuadrilla_id)

@app.route('/api/personnel/cuadrillas/<cuadrilla_id>', methods=['PUT'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_update_cuadrilla(cuadrilla_id):
    return update_cuadrilla(cuadrilla_id)

@app.route('/api/personnel/cuadrillas/<cuadrilla_id>', methods=['DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_delete_cuadrilla(cuadrilla_id):
    return delete_cuadrilla(cuadrilla_id)

@app.route('/api/personnel/cuadrillas/next-number/', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_get_next_cuadrilla_number_api():
    return get_next_cuadrilla_number_api()

@app.route('/api/personnel/obreros/disponibles/', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_get_obreros_disponibles():
    return get_obreros_disponibles()

# Reports routes - gestión de reportes (Admin + Moderador)
@app.route('/api/reports/moderadores/generar', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_generar_reporte_moderadores():
    return generar_reporte_moderadores()

@app.route('/api/reports/moderadores/listar', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_listar_reportes_moderadores():
    return listar_reportes_moderadores()

@app.route('/api/reports/obreros/generar', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_generar_reporte_obreros():
    return generar_reporte_obreros()

@app.route('/api/reports/obreros/listar', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_listar_reportes_obreros():
    return listar_reportes_obreros()

@app.route('/api/reports/moderadores/<reporte_id>', methods=['DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def api_eliminar_reporte_moderadores(reporte_id):
    """Endpoint para eliminar reportes de moderadores por ID"""
    try:
        if not reporte_id:
            return jsonify({
                "success": False,
                "error": "ID de reporte requerido"
            }), 400

        return eliminar_reporte_moderadores(reporte_id)

    except Exception as e:
        logger.error(f"❌ Error en endpoint eliminar reporte moderadores: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/api/reports/obreros/<reporte_id>', methods=['DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def api_eliminar_reporte_obreros(reporte_id):
    """Endpoint para eliminar reportes de obreros por ID"""
    try:
        if not reporte_id:
            return jsonify({
                "success": False,
                "error": "ID de reporte requerido"
            }), 400

        return eliminar_reporte_obreros(reporte_id)

    except Exception as e:
        logger.error(f"❌ Error en endpoint eliminar reporte obreros: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno del servidor: {str(e)}"
        }), 500

# Endpoints de reportes generales (Admin + Moderador)
@app.route('/api/reports/generales/generar', methods=['POST'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def api_generar_reporte_general():
    """Endpoint para generar reportes generales de cuadrillas"""
    try:
        reporte_data = request.get_json()
        if not reporte_data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos del reporte"
            }), 400

        return generar_reporte_general(reporte_data)

    except Exception as e:
        logger.error(f"❌ Error en endpoint generar reporte general: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/api/reports/generales/listar', methods=['GET'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def secured_listar_reportes_generales():
    return listar_reportes_generales()

@app.route('/api/reports/generales/<reporte_id>', methods=['DELETE'])
@middleware_verificar_autenticacion()
@middleware_verificar_permisos(['admin', 'moderador'])
def api_eliminar_reporte_general(reporte_id):
    """Endpoint para eliminar reportes generales por ID"""
    try:
        if not reporte_id:
            return jsonify({
                "success": False,
                "error": "ID de reporte requerido"
            }), 400

        return eliminar_reporte_general(reporte_id)

    except Exception as e:
        logger.error(f"❌ Error en endpoint eliminar reporte general: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno del servidor: {str(e)}"
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error 500: {error}")
    return jsonify({"error": "Error interno del servidor"}), 500

# ==================== PUNTO DE ENTRADA ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting modular backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)