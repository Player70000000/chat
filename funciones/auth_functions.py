# -*- coding: utf-8 -*-
"""
SISTEMA DE AUTENTICACIÓN Y NIVELES DE ACCESO v8.0
CORPOTACHIRA - Empresa de Limpieza

FUNCIONES DE AUTENTICACIÓN:
- Gestión de usuarios con 3 niveles: Admin, Moderador, Obrero
- Generación automática de credenciales para moderadores
- Autenticación con JWT y control de sesiones
- Middleware de verificación de permisos
"""

import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from bson import ObjectId
from funciones.database_functions import get_db

# Configuración JWT desde variables de entorno
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'CorpoTachira_Secret_Key_Ultra_Segura_2024_!@#$%^&*()')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '8'))
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
LOCKOUT_DURATION_MINUTES = int(os.getenv('LOCKOUT_DURATION_MINUTES', '5'))

def generar_credenciales_moderador(nombre, apellidos, cedula):
    """
    Genera automáticamente credenciales para un moderador según las reglas:
    - Usuario: Primera letra nombre (mayúscula) + cédula completa
    - Contraseña: Primera letra nombre (mayúscula) + primera letra apellido (minúscula) + cédula + "#"

    Args:
        nombre (str): Nombre del moderador
        apellidos (str): Apellidos del moderador
        cedula (str): Cédula del moderador

    Returns:
        tuple: (usuario, contraseña)
    """
    try:
        # Limpiar espacios y obtener primeras letras
        nombre_limpio = nombre.strip()
        apellidos_limpio = apellidos.strip()
        cedula_limpia = str(cedula).strip()

        # Generar usuario: D31510033
        usuario = f"{nombre_limpio[0].upper()}{cedula_limpia}"

        # Generar contraseña: Dm31510033#
        contraseña = f"{nombre_limpio[0].upper()}{apellidos_limpio[0].lower()}{cedula_limpia}#"

        return usuario, contraseña

    except Exception as e:
        print(f"Error generando credenciales: {e}")
        return None, None

def hash_password(password):
    """
    Hashea una contraseña usando bcrypt

    Args:
        password (str): Contraseña en texto plano

    Returns:
        str: Hash de la contraseña
    """
    try:
        # Generar salt y hashear
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    except Exception as e:
        print(f"Error hasheando contraseña: {e}")
        return None

def verificar_password(password, hash_almacenado):
    """
    Verifica si una contraseña coincide con su hash

    Args:
        password (str): Contraseña en texto plano
        hash_almacenado (str): Hash almacenado en BD

    Returns:
        bool: True si coinciden, False si no
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hash_almacenado.encode('utf-8'))

    except Exception as e:
        print(f"Error verificando contraseña: {e}")
        return False

def generar_token_jwt(user_data):
    """
    Genera un token JWT con información del usuario

    Args:
        user_data (dict): Datos del usuario

    Returns:
        str: Token JWT o None si error
    """
    try:
        # Debug: imprimir datos del usuario para diagnosticar
# Debug removido: token JWT generado correctamente

        # Verificar que user_data no sea None
        if not user_data:
            print("❌ ERROR: user_data es None")
            return None

        # Extraer ID de manera segura
        user_id = user_data.get('_id')
        if user_id:
            user_id_str = str(user_id)
        else:
            print("❌ ERROR: user_data no tiene '_id'")
            return None

        payload = {
            'user_id': user_id_str,
            'username': user_data.get('username', ''),
            'tipo_usuario': user_data.get('tipo_usuario', ''),
            'nombre_completo': user_data.get('nombre_completo', ''),
            'cedula': user_data.get('cedula', ''),
            'activo': user_data.get('activo', True),
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }

# Debug removido: payload creado correctamente

        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        print(f"✅ Token generado exitosamente: {len(token)} caracteres")
        return token

    except Exception as e:
        print(f"❌ Error generando token JWT: {e}")
        print(f"❌ Tipo de error: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return None

def verificar_token_jwt(token):
    """
    Verifica y decodifica un token JWT

    Args:
        token (str): Token JWT

    Returns:
        dict: Datos del usuario o None si inválido
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        print("Token expirado")
        return None
    except jwt.InvalidTokenError:
        print("Token inválido")
        return None
    except Exception as e:
        print(f"Error verificando token: {e}")
        return None

def login_admin_moderador(username, password):
    """
    Autentica admin o moderador con username y contraseña

    Args:
        username (str): Nombre de usuario
        password (str): Contraseña

    Returns:
        dict: Resultado del login con token y datos del usuario
    """
    try:
        db = get_db()
        usuarios_collection = db['usuarios']

        # Buscar usuario en BD
        usuario = usuarios_collection.find_one({
            'username': username,
            'activo': True
        })

        if not usuario:
            return {
                'success': False,
                'message': 'Usuario no encontrado o inactivo',
                'code': 'USER_NOT_FOUND'
            }

        # Verificar si está bloqueado
        if usuario.get('bloqueado_hasta'):
            bloqueo_hasta = usuario['bloqueado_hasta']
            if datetime.utcnow() < bloqueo_hasta:
                tiempo_restante = bloqueo_hasta - datetime.utcnow()
                minutos_restantes = int(tiempo_restante.total_seconds() / 60)
                return {
                    'success': False,
                    'message': f'Cuenta bloqueada. Intenta en {minutos_restantes} minutos',
                    'code': 'ACCOUNT_LOCKED'
                }
            else:
                # Desbloquear cuenta
                usuarios_collection.update_one(
                    {'_id': usuario['_id']},
                    {'$unset': {'bloqueado_hasta': ''}, '$set': {'intentos_fallidos': 0}}
                )

        # Verificar contraseña
        if not verificar_password(password, usuario['password']):
            # Incrementar intentos fallidos
            intentos = usuario.get('intentos_fallidos', 0) + 1
            update_data = {'intentos_fallidos': intentos}

            if intentos >= MAX_LOGIN_ATTEMPTS:
                # Bloquear cuenta
                update_data['bloqueado_hasta'] = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

            usuarios_collection.update_one(
                {'_id': usuario['_id']},
                {'$set': update_data}
            )

            if intentos >= MAX_LOGIN_ATTEMPTS:
                return {
                    'success': False,
                    'message': f'Cuenta bloqueada por {LOCKOUT_DURATION_MINUTES} minutos debido a múltiples intentos fallidos',
                    'code': 'ACCOUNT_LOCKED'
                }
            else:
                intentos_restantes = MAX_LOGIN_ATTEMPTS - intentos
                return {
                    'success': False,
                    'message': f'Contraseña incorrecta. {intentos_restantes} intentos restantes',
                    'code': 'INVALID_PASSWORD'
                }

        # Login exitoso - resetear intentos fallidos y actualizar último acceso
        usuarios_collection.update_one(
            {'_id': usuario['_id']},
            {
                '$set': {'ultimo_acceso': datetime.utcnow()},
                '$unset': {'intentos_fallidos': '', 'bloqueado_hasta': ''}
            }
        )

        # Generar token
        token = generar_token_jwt(usuario)
        if not token:
            return {
                'success': False,
                'message': 'Error generando token de sesión',
                'code': 'TOKEN_ERROR',
                'debug_info': {
                    'usuario_keys': list(usuario.keys()) if usuario else 'usuario_is_none',
                    'usuario_id': str(usuario.get('_id')) if usuario and usuario.get('_id') else 'no_id',
                    'usuario_username': usuario.get('username') if usuario else 'no_username'
                }
            }

        return {
            'success': True,
            'message': 'Login exitoso',
            'token': token,
            'user_data': {
                'id': str(usuario['_id']),
                'username': usuario['username'],
                'tipo_usuario': usuario['tipo_usuario'],
                'nombre_completo': usuario['nombre_completo'],
                'cedula': usuario['cedula'],
                'email': usuario.get('email'),
                'ultimo_acceso': usuario.get('ultimo_acceso')
            }
        }

    except Exception as e:
        print(f"Error en login admin/moderador: {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"Traceback completo: {error_trace}")
        return {
            'success': False,
            'message': 'Error interno del servidor',
            'code': 'SERVER_ERROR',
            'debug_error': str(e),
            'debug_type': str(type(e))
        }

def login_obrero(cedula):
    """
    Autentica obrero SOLO con cédula (sin contraseña)
    Busca ÚNICAMENTE en colección 'obreros', NO en moderadores

    Args:
        cedula (str): Cédula del obrero

    Returns:
        dict: Resultado del login con token y datos del obrero
    """
    try:
        db = get_db()
        obreros_collection = db['obreros']

        # Buscar SOLO en obreros activos
        obrero = obreros_collection.find_one({
            'cedula': str(cedula).strip(),
            'activo': True
        })

        if not obrero:
            return {
                'success': False,
                'message': 'Cédula no encontrada o trabajador inactivo',
                'code': 'WORKER_NOT_FOUND'
            }

        # Crear datos especiales para token de obrero
        obrero_data = {
            '_id': obrero['_id'],
            'username': f"obrero_{cedula}",
            'tipo_usuario': 'obrero',
            'nombre_completo': f"{obrero['nombre']} {obrero['apellidos']}",
            'cedula': obrero['cedula'],
            'activo': True
        }

        # Generar token especial para obrero
        token = generar_token_jwt(obrero_data)
        if not token:
            return {
                'success': False,
                'message': 'Error generando token de sesión',
                'code': 'TOKEN_ERROR'
            }

        return {
            'success': True,
            'message': 'Acceso concedido',
            'token': token,
            'user_data': {
                'id': str(obrero['_id']),
                'tipo_usuario': 'obrero',
                'nombre_completo': obrero_data['nombre_completo'],
                'cedula': obrero['cedula'],
                'nivel': 'obrero'
            }
        }

    except Exception as e:
        print(f"Error en login obrero: {e}")
        return {
            'success': False,
            'message': 'Error interno del servidor',
            'code': 'SERVER_ERROR'
        }

def crear_usuario_admin_inicial():
    """
    Crea el usuario administrador inicial si no existe

    Returns:
        bool: True si se creó exitosamente, False si ya existía o hubo error
    """
    try:
        db = get_db()
        usuarios_collection = db['usuarios']

        # Verificar si ya existe admin
        admin_existente = usuarios_collection.find_one({'username': 'admin'})
        if admin_existente:
            print("Usuario admin ya existe")
            return False

        # Crear usuario admin
        password_hash = hash_password("CorpoTachira2024#Admin!")
        if not password_hash:
            print("Error hasheando contraseña del admin")
            return False

        admin_data = {
            'tipo_usuario': 'admin',
            'username': 'admin',
            'password': password_hash,
            'nombre_completo': 'Administrador Sistema',
            'cedula': 'ADMIN',
            'email': 'admin@corpotachira.com',
            'personal_id': None,
            'activo': True,
            'fecha_creacion': datetime.utcnow(),
            'ultimo_acceso': None,
            'intentos_fallidos': 0
        }

        resultado = usuarios_collection.insert_one(admin_data)
        if resultado.inserted_id:
            print("Usuario admin creado exitosamente")
            print("Username: admin")
            print("Password: CorpoTachira2024#Admin!")
            return True
        else:
            print("Error insertando usuario admin")
            return False

    except Exception as e:
        print(f"Error creando usuario admin: {e}")
        return False

def sincronizar_usuarios_con_personal():
    """
    Sincroniza moderadores activos con la colección usuarios
    Genera credenciales automáticas para cada moderador
    NO crea usuarios para obreros (ellos usan solo cédula)

    Returns:
        dict: Resultado de la sincronización
    """
    try:
        db = get_db()
        usuarios_collection = db['usuarios']
        moderadores_collection = db['moderadores']

        # Obtener todos los moderadores activos
        moderadores = list(moderadores_collection.find({'activo': True}))

        usuarios_creados = 0
        usuarios_existentes = 0
        errores = []

        for moderador in moderadores:
            try:
                # Verificar si ya existe usuario para este moderador
                usuario_existente = usuarios_collection.find_one({
                    'personal_id': moderador['_id']
                })

                if usuario_existente:
                    usuarios_existentes += 1
                    continue

                # Generar credenciales automáticas
                usuario, contraseña = generar_credenciales_moderador(
                    moderador['nombre'],
                    moderador['apellidos'],
                    moderador['cedula']
                )

                if not usuario or not contraseña:
                    errores.append(f"Error generando credenciales para {moderador['nombre']}")
                    continue

                # Hashear contraseña
                password_hash = hash_password(contraseña)
                if not password_hash:
                    errores.append(f"Error hasheando contraseña para {moderador['nombre']}")
                    continue

                # Crear usuario
                usuario_data = {
                    'tipo_usuario': 'moderador',
                    'username': usuario,
                    'password': password_hash,
                    'nombre_completo': f"{moderador['nombre']} {moderador['apellidos']}",
                    'cedula': moderador['cedula'],
                    'email': moderador.get('email'),
                    'personal_id': moderador['_id'],
                    'activo': True,
                    'fecha_creacion': datetime.utcnow(),
                    'ultimo_acceso': None,
                    'intentos_fallidos': 0
                }

                resultado = usuarios_collection.insert_one(usuario_data)
                if resultado.inserted_id:
                    usuarios_creados += 1
                    print(f"Usuario creado - {moderador['nombre']}: {usuario} / {contraseña}")
                else:
                    errores.append(f"Error insertando usuario para {moderador['nombre']}")

            except Exception as e:
                errores.append(f"Error procesando {moderador.get('nombre', 'Desconocido')}: {e}")

        return {
            'success': True,
            'moderadores_procesados': len(moderadores),
            'usuarios_creados': usuarios_creados,
            'usuarios_existentes': usuarios_existentes,
            'errores': errores
        }

    except Exception as e:
        print(f"Error en sincronización: {e}")
        return {
            'success': False,
            'message': f'Error en sincronización: {e}'
        }

def middleware_verificar_autenticacion():
    """
    Decorator para verificar autenticación en endpoints
    Extrae token del header Authorization y valida
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
# Obtener token del header
                auth_header = request.headers.get('Authorization')

                if not auth_header:
                    return jsonify({
                        'success': False,
                        'message': 'Token de autorización requerido',
                        'code': 'NO_TOKEN'
                    }), 401

                # Extraer token (formato: "Bearer TOKEN")
                try:
                    token = auth_header.split(' ')[1]
                except IndexError:
                    return jsonify({
                        'success': False,
                        'message': 'Formato de token inválido',
                        'code': 'INVALID_TOKEN_FORMAT'
                    }), 401

                # Verificar token
                user_data = verificar_token_jwt(token)

                if not user_data:
                    return jsonify({
                        'success': False,
                        'message': 'Token inválido o expirado',
                        'code': 'INVALID_TOKEN'
                    }), 401

                # Adjuntar datos del usuario al request
                request.user_data = user_data

                return f(*args, **kwargs)

            except Exception as e:
                print(f"Error en middleware de autenticación: {e}")
                return jsonify({
                    'success': False,
                    'message': 'Error verificando autenticación',
                    'code': 'AUTH_ERROR'
                }), 500

        return wrapper
    return decorator

def middleware_verificar_permisos(niveles_permitidos):
    """
    Decorator para verificar permisos específicos

    Args:
        niveles_permitidos (list): Lista de niveles permitidos ['admin', 'moderador', 'obrero']
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Verificar que existe user_data (debe aplicarse después de verificar_autenticacion)
                if not hasattr(request, 'user_data'):
                    return jsonify({
                        'success': False,
                        'message': 'Autenticación requerida',
                        'code': 'AUTH_REQUIRED'
                    }), 401

                user_tipo = request.user_data.get('tipo_usuario')

# Verificar permisos del usuario

                # Verificar permisos
                if user_tipo not in niveles_permitidos:
                    return jsonify({
                        'success': False,
                        'message': 'No tienes permisos para realizar esta acción',
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'required_levels': niveles_permitidos,
                        'your_level': user_tipo
                    }), 403

                return f(*args, **kwargs)

            except Exception as e:
                print(f"Error en middleware de permisos: {e}")
                return jsonify({
                    'success': False,
                    'message': 'Error verificando permisos',
                    'code': 'PERMISSIONS_ERROR'
                }), 500

        return wrapper
    return decorator

def verificar_sesion_activa(token):
    """
    Verifica si una sesión está activa y es válida

    Args:
        token (str): Token JWT

    Returns:
        dict: Resultado de la verificación
    """
    try:
        user_data = verificar_token_jwt(token)
        if not user_data:
            return {
                'success': False,
                'message': 'Sesión expirada o inválida',
                'code': 'SESSION_INVALID'
            }

        # Verificar que el usuario sigue activo en BD
        db = get_db()

        if user_data['tipo_usuario'] == 'obrero':
            # Para obreros, verificar en colección obreros
            obreros_collection = db['obreros']
            obrero = obreros_collection.find_one({
                '_id': ObjectId(user_data['user_id']),
                'activo': True
            })
            if not obrero:
                return {
                    'success': False,
                    'message': 'Usuario inactivo',
                    'code': 'USER_INACTIVE'
                }
        else:
            # Para admin y moderadores, verificar en colección usuarios
            usuarios_collection = db['usuarios']
            usuario = usuarios_collection.find_one({
                '_id': ObjectId(user_data['user_id']),
                'activo': True
            })
            if not usuario:
                return {
                    'success': False,
                    'message': 'Usuario inactivo',
                    'code': 'USER_INACTIVE'
                }

        return {
            'success': True,
            'user_data': user_data
        }

    except Exception as e:
        print(f"Error verificando sesión: {e}")
        return {
            'success': False,
            'message': 'Error verificando sesión',
            'code': 'SESSION_ERROR'
        }

def cambiar_password(user_id, password_actual, password_nueva):
    """
    Cambia la contraseña de un usuario admin o moderador

    Args:
        user_id (str): ID del usuario
        password_actual (str): Contraseña actual
        password_nueva (str): Nueva contraseña

    Returns:
        dict: Resultado del cambio
    """
    try:
        db = get_db()
        usuarios_collection = db['usuarios']

        # Buscar usuario
        usuario = usuarios_collection.find_one({'_id': ObjectId(user_id)})
        if not usuario:
            return {
                'success': False,
                'message': 'Usuario no encontrado',
                'code': 'USER_NOT_FOUND'
            }

        # Verificar contraseña actual
        if not verificar_password(password_actual, usuario['password']):
            return {
                'success': False,
                'message': 'Contraseña actual incorrecta',
                'code': 'CURRENT_PASSWORD_INVALID'
            }

        # Validar nueva contraseña
        if len(password_nueva) < 6:
            return {
                'success': False,
                'message': 'La nueva contraseña debe tener al menos 6 caracteres',
                'code': 'PASSWORD_TOO_SHORT'
            }

        # Hashear nueva contraseña
        nuevo_hash = hash_password(password_nueva)
        if not nuevo_hash:
            return {
                'success': False,
                'message': 'Error procesando nueva contraseña',
                'code': 'PASSWORD_HASH_ERROR'
            }

        # Actualizar contraseña
        resultado = usuarios_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'password': nuevo_hash}}
        )

        if resultado.modified_count > 0:
            return {
                'success': True,
                'message': 'Contraseña cambiada exitosamente'
            }
        else:
            return {
                'success': False,
                'message': 'Error actualizando contraseña',
                'code': 'UPDATE_ERROR'
            }

    except Exception as e:
        print(f"Error cambiando contraseña: {e}")
        return {
            'success': False,
            'message': 'Error interno del servidor',
            'code': 'SERVER_ERROR'
        }

# Logs de seguridad
def log_security_event(event_type, user_data, details=None):
    """
    Registra eventos de seguridad

    Args:
        event_type (str): Tipo de evento (login, logout, failed_login, etc.)
        user_data (dict): Datos del usuario
        details (dict): Detalles adicionales
    """
    try:
        db = get_db()
        security_logs = db['security_logs']

        log_entry = {
            'event_type': event_type,
            'timestamp': datetime.utcnow(),
            'user_id': user_data.get('user_id'),
            'username': user_data.get('username'),
            'tipo_usuario': user_data.get('tipo_usuario'),
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details or {}
        }

        security_logs.insert_one(log_entry)

    except Exception as e:
        print(f"Error registrando evento de seguridad: {e}")

# Función para limpiar tokens expirados (opcional, para mantenimiento)
def limpiar_tokens_expirados():
    """
    Limpia logs de seguridad antiguos y realiza mantenimiento
    """
    try:
        db = get_db()

        # Limpiar logs de seguridad mayores a 30 días
        fecha_limite = datetime.utcnow() - timedelta(days=30)
        security_logs = db['security_logs']
        resultado = security_logs.delete_many({'timestamp': {'$lt': fecha_limite}})

        print(f"Logs de seguridad limpiados: {resultado.deleted_count}")

        # Desbloquear cuentas con bloqueo expirado
        usuarios_collection = db['usuarios']
        resultado_usuarios = usuarios_collection.update_many(
            {'bloqueado_hasta': {'$lt': datetime.utcnow()}},
            {'$unset': {'bloqueado_hasta': ''}, '$set': {'intentos_fallidos': 0}}
        )

        print(f"Cuentas desbloqueadas: {resultado_usuarios.modified_count}")

        return True

    except Exception as e:
        print(f"Error en limpieza: {e}")
        return False


def get_user_from_token():
    """
    Extrae y valida el token JWT desde la request actual
    Devuelve los datos del usuario si el token es válido

    Returns:
        dict: Datos del usuario o None si token inválido/faltante
    """
    try:
        from flask import request

        # Obtener token del header Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        # Extraer token (formato: "Bearer TOKEN")
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return None

        # Verificar y decodificar token
        user_data = verificar_token_jwt(token)
        return user_data

    except Exception as e:
        logger.error(f"Error obteniendo usuario desde token: {e}")
        return None