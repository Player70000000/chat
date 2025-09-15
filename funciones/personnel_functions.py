"""
Funciones de Personal
Maneja todas las operaciones relacionadas con moderadores y personal
"""

import logging
from datetime import datetime, timezone, timedelta
from flask import request, jsonify
from funciones.database_functions import get_db

# Logger para este módulo
logger = logging.getLogger(__name__)

def get_venezuela_time():
    """Obtener la hora actual de Venezuela (GMT-4)"""
    # Venezuela está en GMT-4 (4 horas atrás de UTC)
    venezuela_tz = timezone(timedelta(hours=-4))
    return datetime.now(venezuela_tz)

def validate_cedula(cedula):
    """Validar cédula con reglas específicas"""
    if not cedula:
        return None, "La cédula es obligatoria"
    
    # Convertir a string y limpiar espacios
    cedula_str = str(cedula).strip()
    
    # Validar que solo contenga números
    if not cedula_str.isdigit():
        return None, "La cédula solo puede contener números"
    
    # Validar longitud mínima y máxima
    if len(cedula_str) < 6:
        return None, "La cédula debe tener mínimo 6 dígitos"
    
    if len(cedula_str) > 10:
        return None, "La cédula debe tener máximo 10 dígitos"
    
    return cedula_str, None

def validate_nombre_apellido(texto, campo_nombre):
    """Validar que nombres y apellidos no contengan números"""
    if not texto:
        return None, f"El {campo_nombre} es obligatorio"
    
    # Convertir a string y limpiar espacios
    texto_str = str(texto).strip()
    
    # Validar que no esté vacío después de limpiar
    if not texto_str:
        return None, f"El {campo_nombre} no puede estar vacío"
    
    # Validar que no contenga números
    if any(char.isdigit() for char in texto_str):
        return None, f"El {campo_nombre} no puede contener números"
    
    # Validar longitud mínima
    if len(texto_str) < 2:
        return None, f"El {campo_nombre} debe tener al menos 2 caracteres"
    
    # Validar longitud máxima
    if len(texto_str) > 50:
        return None, f"El {campo_nombre} debe tener máximo 50 caracteres"
    
    # Aplicar capitalización
    return texto_str.strip().title(), None

def validate_email(email):
    """Validar formato de email"""
    if not email:
        return None, "El email es obligatorio"
    
    # Convertir a string y limpiar espacios
    email_str = str(email).strip().lower()
    
    # Validar que no esté vacío después de limpiar
    if not email_str:
        return None, "El email no puede estar vacío"
    
    # Validar formato básico de email
    if '@' not in email_str:
        return None, "El email debe contener el símbolo '@' (ejemplo: usuario@gmail.com)"
    
    # Dividir en partes local y dominio
    parts = email_str.split('@')
    if len(parts) != 2:
        return None, "El email debe tener exactamente un símbolo '@'"
    
    local_part, domain_part = parts
    
    # Validar parte local (antes del @)
    if not local_part:
        return None, "El email debe tener un usuario antes del '@'"
    
    if len(local_part) < 1:
        return None, "La parte del usuario debe tener al menos 1 carácter"
    
    # Validar parte del dominio (después del @)
    if not domain_part:
        return None, "El email debe tener un dominio después del '@'"
    
    if '.' not in domain_part:
        return None, "El dominio debe contener al menos un punto (ejemplo: @gmail.com)"
    
    # Validar que el dominio tenga al menos un punto y caracteres
    domain_parts = domain_part.split('.')
    if len(domain_parts) < 2:
        return None, "El dominio debe tener al menos una extensión (ejemplo: .com, .es)"
    
    # Validar que no haya partes vacías en el dominio
    for part in domain_parts:
        if not part:
            return None, "El dominio no puede tener puntos consecutivos"
        if len(part) < 1:
            return None, "Cada parte del dominio debe tener al menos 1 carácter"
    
    # Validar longitud total
    if len(email_str) > 100:
        return None, "El email no puede tener más de 100 caracteres"
    
    return email_str, None

def api_personnel_moderadores():
    """Personnel - moderators - lista desde base de datos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Buscar todos los moderadores en la colección
        moderadores = list(db.moderadores.find({}, {"_id": 0}))
        
        logger.info(f"Moderadores encontrados: {len(moderadores)}")
        
        return jsonify({
            "success": True,
            "moderadores": moderadores,
            "count": len(moderadores),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obtener moderadores: {e}")
        return jsonify({"error": str(e)}), 500

def api_personnel_moderadores_create():
    """Create moderator - guarda en base de datos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # DEBUG: Log completo del request
        logger.info("=== MODERADOR CREATE REQUEST DEBUG ===")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Raw data: {request.get_data()}")
        logger.info(f"Is JSON: {request.is_json}")
        
        # Intentar obtener datos en diferentes formatos
        datos = None
        
        if request.is_json:
            datos = request.get_json()
            logger.info("Datos recibidos como JSON")
        elif request.form:
            # Convertir form data a diccionario
            datos = request.form.to_dict()
            logger.info("Datos recibidos como form data")
        else:
            # Intentar parsear raw data como JSON
            try:
                import json
                raw_data = request.get_data().decode('utf-8')
                datos = json.loads(raw_data)
                logger.info("Datos parseados desde raw data como JSON")
            except:
                logger.error("No se pudieron parsear los datos")
                return jsonify({
                    "error": "Formato de datos no soportado. Use JSON o form data.",
                    "debug": {
                        "content_type": request.content_type,
                        "raw_data": request.get_data().decode('utf-8', errors='ignore')[:200],
                        "is_json": request.is_json,
                        "has_form": bool(request.form)
                    }
                }), 400
        
        if not datos:
            logger.error("Datos vacíos después del parsing")
            return jsonify({
                "error": "No se recibieron datos válidos",
                "debug": {
                    "content_type": request.content_type,
                    "parsed_data": datos
                }
            }), 400
        
        # DEBUG: Log datos recibidos
        logger.info(f"Datos JSON parseados: {datos}")
        logger.info(f"Claves disponibles: {list(datos.keys())}")
        logger.info("=== FIN DEBUG REQUEST ===")
        
        # Validar y formatear campos requeridos - CON VALIDACIONES COMPLETAS
        nombre_raw = datos.get('nombre', datos.get('name', datos.get('nombres', '')))
        email_raw = datos.get('email', datos.get('correo', datos.get('mail', '')))
        cedula_raw = datos.get('cedula', datos.get('ci', datos.get('documento', '')))
        apellidos_raw = datos.get('apellidos', '')
        
        logger.info(f"Nombre extraído: '{nombre_raw}', Email extraído: '{email_raw}', Cédula: '{cedula_raw}', Apellidos: '{apellidos_raw}'")
        
        # Validar nombre (sin números)
        nombre, error_nombre = validate_nombre_apellido(nombre_raw, "nombre")
        if error_nombre:
            return jsonify({
                "error": error_nombre,
                "debug": {
                    "datos_recibidos": datos,
                    "nombre_original": nombre_raw,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400
        
        # Validar apellidos (sin números)
        apellidos, error_apellidos = validate_nombre_apellido(apellidos_raw, "apellido")
        if error_apellidos:
            return jsonify({
                "error": error_apellidos,
                "debug": {
                    "datos_recibidos": datos,
                    "apellidos_original": apellidos_raw,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400
        
        # Validar email (formato correcto)
        email, error_email = validate_email(email_raw)
        if error_email:
            return jsonify({
                "error": error_email,
                "debug": {
                    "datos_recibidos": datos,
                    "email_original": email_raw,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400
        
        # Validar cédula
        logger.info(f"🔍 VALIDANDO CEDULA: cedula_raw='{cedula_raw}', tipo={type(cedula_raw)}")
        cedula_valida, error_cedula = validate_cedula(cedula_raw)
        logger.info(f"🔍 RESULTADO VALIDACION: cedula_valida='{cedula_valida}', error='{error_cedula}'")
        if error_cedula:
            logger.error(f"❌ Error validación cédula: {error_cedula}")
            return jsonify({
                "error": error_cedula,
                "debug": {
                    "cedula_recibida": cedula_raw,
                    "datos_recibidos": datos,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400
        
        # VALIDACIÓN CRUZADA: Verificar que no exista el email en moderadores Y obreros
        if db.moderadores.find_one({"email": email}):
            return jsonify({"error": f"Ya existe un moderador con el email '{email}'"}), 400
        if db.obreros.find_one({"email": email}):
            return jsonify({"error": f"Ya existe un obrero con el email '{email}'"}), 400

        # VALIDACIÓN CRUZADA: Verificar que no exista la cédula en moderadores Y obreros
        if db.moderadores.find_one({"cedula": cedula_valida}):
            return jsonify({"error": f"Ya existe un moderador con la cédula '{cedula_valida}'"}), 400
        if db.obreros.find_one({"cedula": cedula_valida}):
            return jsonify({"error": f"Ya existe un obrero con la cédula '{cedula_valida}'"}), 400

        # Obtener campos adicionales
        telefono = datos.get('telefono', '').strip()

        # VALIDACIÓN CRUZADA: Verificar que no exista el teléfono en moderadores Y obreros
        if telefono and db.moderadores.find_one({"telefono": telefono}):
            return jsonify({"error": f"Ya existe un moderador con el teléfono '{telefono}'"}), 400
        if telefono and db.obreros.find_one({"telefono": telefono}):
            return jsonify({"error": f"Ya existe un obrero con el teléfono '{telefono}'"}), 400
        
        # FIX: Manejar campos opcionales que pueden ser None/null
        talla_ropa_raw = datos.get('talla_ropa')
        talla_zapatos_raw = datos.get('talla_zapatos')
        
        logger.info(f"🔍 DEBUG CAMPOS OPCIONALES: talla_ropa_raw={talla_ropa_raw} (tipo: {type(talla_ropa_raw)})")
        logger.info(f"🔍 DEBUG CAMPOS OPCIONALES: talla_zapatos_raw={talla_zapatos_raw} (tipo: {type(talla_zapatos_raw)})")
        
        # Convertir None a string vacío antes de strip(), luego asignar "No ingresado" si está vacío
        talla_ropa_clean = (talla_ropa_raw or '').strip()
        talla_zapatos_clean = (talla_zapatos_raw or '').strip()
        
        # Asignar "No ingresado" si los campos están vacíos
        talla_ropa = talla_ropa_clean if talla_ropa_clean else "No ingresado"
        talla_zapatos = talla_zapatos_clean if talla_zapatos_clean else "No ingresado"
        
        logger.info(f"✅ CAMPOS OPCIONALES PROCESADOS: talla_ropa='{talla_ropa}', talla_zapatos='{talla_zapatos}'")
        
        # Crear documento del moderador con todos los campos
        documento_moderador = {
            "nombre": nombre,
            "apellidos": apellidos,
            "cedula": cedula_valida,
            "email": email,
            "telefono": telefono,
            "talla_ropa": talla_ropa,
            "talla_zapatos": talla_zapatos,
            "activo": datos.get('activo', True),
            "nivel": datos.get('nivel', 'moderador'),
            "fecha_creacion": get_venezuela_time(),
            "creado_por": "sistema"
        }
        
        logger.info(f"📄 DOCUMENTO A GUARDAR: {documento_moderador}")
        logger.info(f"🔑 CEDULA EN DOCUMENTO: '{documento_moderador.get('cedula')}' (tipo: {type(documento_moderador.get('cedula'))})")
        
        # Guardar en base de datos
        resultado = db.moderadores.insert_one(documento_moderador)
        
        logger.info(f"💾 GUARDADO EXITOSO: ID = {resultado.inserted_id}")
        
        # VERIFICAR QUE SE GUARDÓ CORRECTAMENTE
        moderador_guardado = db.moderadores.find_one({"_id": resultado.inserted_id})
        logger.info(f"✅ VERIFICACION POST-GUARDADO: {moderador_guardado}")
        cedula_guardada = moderador_guardado.get('cedula') if moderador_guardado else None
        logger.info(f"🆔 CEDULA GUARDADA EN DB: '{cedula_guardada}' (tipo: {type(cedula_guardada)})")
        
        logger.info(f"Moderador creado: {nombre} ({email})")
        
        return jsonify({
            "success": True,
            "message": "Moderador registrado exitosamente",
            "moderador_id": str(resultado.inserted_id),
            "data": {
                "nombre": nombre,
                "apellidos": apellidos,
                "cedula": cedula_valida,
                "email": email,
                "telefono": telefono,
                "talla_ropa": talla_ropa,
                "talla_zapatos": talla_zapatos,
                "activo": documento_moderador["activo"],
                "nivel": documento_moderador["nivel"],
                "fecha_creacion": documento_moderador["fecha_creacion"],
                "creado_por": documento_moderador["creado_por"]
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error crear moderador: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

def api_personnel_moderadores_debug():
    """DEBUG endpoint - returns all request info"""
    try:
        return jsonify({
            "method": request.method,
            "url": request.url,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "form": dict(request.form),
            "json": request.get_json(silent=True),
            "data": request.get_data().decode('utf-8', errors='ignore'),
            "content_type": request.content_type,
            "is_json": request.is_json,
            "content_length": request.content_length,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"debug_error": str(e)})

def api_personnel_moderadores_update():
    """Update moderator - actualiza moderador existente en base de datos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # DEBUG: Log completo del request
        logger.info("=== MODERADOR UPDATE REQUEST DEBUG ===")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Method: {request.method}")
        logger.info(f"Raw data: {request.get_data()}")
        
        # Intentar obtener datos en diferentes formatos
        datos = None
        
        if request.is_json:
            datos = request.get_json()
            logger.info("Datos recibidos como JSON")
        elif request.form:
            datos = request.form.to_dict()
            logger.info("Datos recibidos como form data")
        else:
            try:
                import json
                raw_data = request.get_data().decode('utf-8')
                datos = json.loads(raw_data)
                logger.info("Datos parseados desde raw data como JSON")
            except:
                logger.error("No se pudieron parsear los datos")
                return jsonify({
                    "error": "Formato de datos no soportado. Use JSON o form data.",
                    "debug": {
                        "content_type": request.content_type,
                        "method": request.method
                    }
                }), 400
        
        if not datos:
            logger.error("Datos vacíos después del parsing")
            return jsonify({"error": "No se recibieron datos válidos"}), 400
        
        logger.info(f"Datos recibidos para actualización: {datos}")
        
        # Obtener cédula del moderador a actualizar (clave primaria)
        cedula_original = datos.get('cedula_original', datos.get('cedula', ''))
        if not cedula_original:
            return jsonify({"error": "Cédula original es requerida para actualizar"}), 400
        
        # Validar que el moderador existe
        moderador_existente = db.moderadores.find_one({"cedula": cedula_original})
        if not moderador_existente:
            return jsonify({"error": f"No se encontró moderador con cédula '{cedula_original}'"}), 404
        
        logger.info(f"Moderador encontrado para actualizar: {moderador_existente.get('nombre')} ({moderador_existente.get('email')})")
        
        # Validar y formatear campos requeridos - CON VALIDACIONES COMPLETAS
        nombre_raw = datos.get('nombre', '')
        apellidos_raw = datos.get('apellidos', '')
        email_raw = datos.get('email', '')
        cedula_nueva = datos.get('cedula', '').strip()
        
        # Validar nombre (sin números)
        nombre, error_nombre = validate_nombre_apellido(nombre_raw, "nombre")
        if error_nombre:
            return jsonify({"error": error_nombre}), 400
        
        # Validar apellidos (sin números)
        apellidos, error_apellidos = validate_nombre_apellido(apellidos_raw, "apellido")
        if error_apellidos:
            return jsonify({"error": error_apellidos}), 400
        
        # Validar email (formato correcto)
        email, error_email = validate_email(email_raw)
        if error_email:
            return jsonify({"error": error_email}), 400
        
        # Validar nueva cédula
        cedula_valida, error_cedula = validate_cedula(cedula_nueva)
        if error_cedula:
            return jsonify({"error": error_cedula}), 400
        
        # VALIDACIÓN CRUZADA: Verificar unicidad solo si se cambió el email
        if email != moderador_existente.get('email'):
            # Verificar en moderadores (excluyendo el actual)
            if db.moderadores.find_one({"email": email, "cedula": {"$ne": cedula_original}}):
                return jsonify({"error": f"Ya existe otro moderador con el email '{email}'"}), 400
            # Verificar en obreros
            if db.obreros.find_one({"email": email}):
                return jsonify({"error": f"Ya existe un obrero con el email '{email}'"}), 400

        # VALIDACIÓN CRUZADA: Verificar unicidad solo si se cambió la cédula
        if cedula_valida != cedula_original:
            # Verificar en moderadores
            if db.moderadores.find_one({"cedula": cedula_valida}):
                return jsonify({"error": f"Ya existe otro moderador con la cédula '{cedula_valida}'"}), 400
            # Verificar en obreros
            if db.obreros.find_one({"cedula": cedula_valida}):
                return jsonify({"error": f"Ya existe un obrero con la cédula '{cedula_valida}'"}), 400

        # VALIDACIÓN CRUZADA: Verificar unicidad del teléfono solo si se cambió
        telefono = datos.get('telefono', '').strip()
        if telefono and telefono != moderador_existente.get('telefono'):
            # Verificar en moderadores (excluyendo el actual)
            if db.moderadores.find_one({"telefono": telefono, "cedula": {"$ne": cedula_original}}):
                return jsonify({"error": f"Ya existe otro moderador con el teléfono '{telefono}'"}), 400
            # Verificar en obreros
            if db.obreros.find_one({"telefono": telefono}):
                return jsonify({"error": f"Ya existe un obrero con el teléfono '{telefono}'"}), 400
        
        # Manejar campos opcionales
        talla_ropa_raw = datos.get('talla_ropa')
        talla_zapatos_raw = datos.get('talla_zapatos')
        
        talla_ropa_clean = (talla_ropa_raw or '').strip()
        talla_zapatos_clean = (talla_zapatos_raw or '').strip()
        
        talla_ropa = talla_ropa_clean if talla_ropa_clean else "No ingresado"
        talla_zapatos = talla_zapatos_clean if talla_zapatos_clean else "No ingresado"
        
        # Preparar documento actualizado
        documento_actualizado = {
            "nombre": nombre,
            "apellidos": apellidos,
            "cedula": cedula_valida,
            "email": email,
            "telefono": telefono,
            "talla_ropa": talla_ropa,
            "talla_zapatos": talla_zapatos,
            "activo": datos.get('activo', moderador_existente.get('activo', True)),
            "nivel": datos.get('nivel', moderador_existente.get('nivel', 'moderador')),
            # Mantener fecha de creación original
            "fecha_creacion": moderador_existente.get('fecha_creacion'),
            "creado_por": moderador_existente.get('creado_por'),
            # Agregar campos de modificación
            "fecha_modificacion": get_venezuela_time(),
            "modificado_por": "sistema"
        }
        
        logger.info(f"Documento a actualizar: {documento_actualizado}")
        
        # Actualizar en base de datos
        resultado = db.moderadores.update_one(
            {"cedula": cedula_original},
            {"$set": documento_actualizado}
        )
        
        if resultado.modified_count == 0:
            logger.warning("No se modificó ningún documento - posiblemente datos idénticos")
            # Verificar si existe pero no se modificó
            if resultado.matched_count > 0:
                logger.info("Moderador encontrado pero sin cambios")
            else:
                return jsonify({"error": "No se encontró el moderador para actualizar"}), 404
        
        logger.info(f"Moderador actualizado exitosamente: {nombre} ({email})")
        
        # Obtener documento actualizado para respuesta
        moderador_actualizado = db.moderadores.find_one({"cedula": cedula_valida}, {"_id": 0})
        
        return jsonify({
            "success": True,
            "message": "Moderador actualizado exitosamente",
            "data": moderador_actualizado,
            "changes": {
                "matched_count": resultado.matched_count,
                "modified_count": resultado.modified_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error actualizar moderador: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

def api_personnel_moderadores_delete():
    """Delete moderator - elimina moderador existente de la base de datos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # DEBUG: Log completo del request
        logger.info("=== MODERADOR DELETE REQUEST DEBUG ===")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Method: {request.method}")
        logger.info(f"Raw data: {request.get_data()}")
        
        # Intentar obtener datos en diferentes formatos
        datos = None
        
        if request.is_json:
            datos = request.get_json()
            logger.info("Datos recibidos como JSON")
        elif request.form:
            datos = request.form.to_dict()
            logger.info("Datos recibidos como form data")
        else:
            try:
                import json
                raw_data = request.get_data().decode('utf-8')
                datos = json.loads(raw_data)
                logger.info("Datos parseados desde raw data como JSON")
            except:
                logger.error("No se pudieron parsear los datos")
                return jsonify({
                    "error": "Formato de datos no soportado. Use JSON o form data.",
                    "debug": {
                        "content_type": request.content_type,
                        "method": request.method
                    }
                }), 400
        
        if not datos:
            logger.error("Datos vacíos después del parsing")
            return jsonify({"error": "No se recibieron datos válidos"}), 400
        
        logger.info(f"Datos recibidos para eliminación: {datos}")
        
        # Obtener cédula del moderador a eliminar (clave primaria)
        cedula = datos.get('cedula', '').strip()
        if not cedula:
            return jsonify({"error": "Cédula es requerida para eliminar moderador"}), 400
        
        # Validar que el moderador existe
        moderador_existente = db.moderadores.find_one({"cedula": cedula})
        if not moderador_existente:
            return jsonify({"error": f"No se encontró moderador con cédula '{cedula}'"}), 404
        
        logger.info(f"Moderador encontrado para eliminar: {moderador_existente.get('nombre')} {moderador_existente.get('apellidos')} ({moderador_existente.get('email')})")
        
        # Guardar datos del moderador para la respuesta
        moderador_eliminado = {
            "nombre": moderador_existente.get('nombre'),
            "apellidos": moderador_existente.get('apellidos'),
            "cedula": moderador_existente.get('cedula'),
            "email": moderador_existente.get('email'),
            "telefono": moderador_existente.get('telefono'),
            "fecha_creacion": moderador_existente.get('fecha_creacion'),
            "fecha_eliminacion": get_venezuela_time(),
            "eliminado_por": "sistema"
        }
        
        # Eliminar de base de datos
        resultado = db.moderadores.delete_one({"cedula": cedula})
        
        if resultado.deleted_count == 0:
            logger.warning("No se eliminó ningún documento")
            return jsonify({"error": "No se pudo eliminar el moderador"}), 500
        
        logger.info(f"Moderador eliminado exitosamente: {moderador_eliminado['nombre']} {moderador_eliminado['apellidos']}")
        
        return jsonify({
            "success": True,
            "message": "Moderador eliminado exitosamente",
            "moderador_eliminado": moderador_eliminado,
            "deleted_count": resultado.deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error eliminar moderador: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# ==================== FUNCIONES DE OBREROS ====================

def api_personnel_obreros():
    """Personnel - obreros - lista desde base de datos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500

        # Buscar todos los obreros en la colección
        obreros = list(db.obreros.find({}, {"_id": 0}))

        logger.info(f"Obreros encontrados: {len(obreros)}")

        return jsonify({
            "success": True,
            "obreros": obreros,
            "count": len(obreros),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error obtener obreros: {e}")
        return jsonify({"error": str(e)}), 500

def api_personnel_obreros_create():
    """Create obrero - guarda en base de datos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500

        # DEBUG: Log completo del request
        logger.info("=== OBRERO CREATE REQUEST DEBUG ===")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Raw data: {request.get_data()}")
        logger.info(f"Is JSON: {request.is_json}")

        # Intentar obtener datos en diferentes formatos
        datos = None

        if request.is_json:
            datos = request.get_json()
            logger.info("Datos recibidos como JSON")
        elif request.form:
            # Convertir form data a diccionario
            datos = request.form.to_dict()
            logger.info("Datos recibidos como form data")
        else:
            # Intentar parsear raw data como JSON
            try:
                import json
                raw_data = request.get_data().decode('utf-8')
                datos = json.loads(raw_data)
                logger.info("Datos parseados desde raw data como JSON")
            except:
                logger.error("No se pudieron parsear los datos")
                return jsonify({
                    "error": "Formato de datos no soportado. Use JSON o form data.",
                    "debug": {
                        "content_type": request.content_type,
                        "raw_data": request.get_data().decode('utf-8', errors='ignore')[:200],
                        "is_json": request.is_json,
                        "has_form": bool(request.form)
                    }
                }), 400

        if not datos:
            logger.error("Datos vacíos después del parsing")
            return jsonify({
                "error": "No se recibieron datos válidos",
                "debug": {
                    "content_type": request.content_type,
                    "parsed_data": datos
                }
            }), 400

        # DEBUG: Log datos recibidos
        logger.info(f"Datos JSON parseados: {datos}")
        logger.info(f"Claves disponibles: {list(datos.keys())}")
        logger.info("=== FIN DEBUG REQUEST ===")

        # Validar y formatear campos requeridos - CON VALIDACIONES COMPLETAS
        nombre_raw = datos.get('nombre', datos.get('name', datos.get('nombres', '')))
        email_raw = datos.get('email', datos.get('correo', datos.get('mail', '')))
        cedula_raw = datos.get('cedula', datos.get('ci', datos.get('documento', '')))
        apellidos_raw = datos.get('apellidos', '')

        logger.info(f"Nombre extraído: '{nombre_raw}', Email extraído: '{email_raw}', Cédula: '{cedula_raw}', Apellidos: '{apellidos_raw}'")

        # Validar nombre (sin números)
        nombre, error_nombre = validate_nombre_apellido(nombre_raw, "nombre")
        if error_nombre:
            return jsonify({
                "error": error_nombre,
                "debug": {
                    "datos_recibidos": datos,
                    "nombre_original": nombre_raw,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400

        # Validar apellidos (sin números)
        apellidos, error_apellidos = validate_nombre_apellido(apellidos_raw, "apellido")
        if error_apellidos:
            return jsonify({
                "error": error_apellidos,
                "debug": {
                    "datos_recibidos": datos,
                    "apellidos_original": apellidos_raw,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400

        # Validar email (formato correcto)
        email, error_email = validate_email(email_raw)
        if error_email:
            return jsonify({
                "error": error_email,
                "debug": {
                    "datos_recibidos": datos,
                    "email_original": email_raw,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400

        # Validar cédula
        logger.info(f"🔍 VALIDANDO CEDULA: cedula_raw='{cedula_raw}', tipo={type(cedula_raw)}")
        cedula_valida, error_cedula = validate_cedula(cedula_raw)
        logger.info(f"🔍 RESULTADO VALIDACION: cedula_valida='{cedula_valida}', error='{error_cedula}'")
        if error_cedula:
            logger.error(f"❌ Error validación cédula: {error_cedula}")
            return jsonify({
                "error": error_cedula,
                "debug": {
                    "cedula_recibida": cedula_raw,
                    "datos_recibidos": datos,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400

        # VALIDACIÓN CRUZADA: Verificar que no exista el email en obreros Y moderadores
        if db.obreros.find_one({"email": email}):
            return jsonify({"error": f"Ya existe un obrero con el email '{email}'"}), 400
        if db.moderadores.find_one({"email": email}):
            return jsonify({"error": f"Ya existe un moderador con el email '{email}'"}), 400

        # VALIDACIÓN CRUZADA: Verificar que no exista la cédula en obreros Y moderadores
        if db.obreros.find_one({"cedula": cedula_valida}):
            return jsonify({"error": f"Ya existe un obrero con la cédula '{cedula_valida}'"}), 400
        if db.moderadores.find_one({"cedula": cedula_valida}):
            return jsonify({"error": f"Ya existe un moderador con la cédula '{cedula_valida}'"}), 400

        # Obtener campos adicionales
        telefono = datos.get('telefono', '').strip()

        # VALIDACIÓN CRUZADA: Verificar que no exista el teléfono en obreros Y moderadores
        if telefono and db.obreros.find_one({"telefono": telefono}):
            return jsonify({"error": f"Ya existe un obrero con el teléfono '{telefono}'"}), 400
        if telefono and db.moderadores.find_one({"telefono": telefono}):
            return jsonify({"error": f"Ya existe un moderador con el teléfono '{telefono}'"}), 400

        # Manejar campos opcionales que pueden ser None/null
        talla_ropa_raw = datos.get('talla_ropa')
        talla_zapatos_raw = datos.get('talla_zapatos')

        logger.info(f"🔍 DEBUG CAMPOS OPCIONALES: talla_ropa_raw={talla_ropa_raw} (tipo: {type(talla_ropa_raw)})")
        logger.info(f"🔍 DEBUG CAMPOS OPCIONALES: talla_zapatos_raw={talla_zapatos_raw} (tipo: {type(talla_zapatos_raw)})")

        # Convertir None a string vacío antes de strip(), luego asignar "No ingresado" si está vacío
        talla_ropa_clean = (talla_ropa_raw or '').strip()
        talla_zapatos_clean = (talla_zapatos_raw or '').strip()

        # Asignar "No ingresado" si los campos están vacíos
        talla_ropa = talla_ropa_clean if talla_ropa_clean else "No ingresado"
        talla_zapatos = talla_zapatos_clean if talla_zapatos_clean else "No ingresado"

        logger.info(f"✅ CAMPOS OPCIONALES PROCESADOS: talla_ropa='{talla_ropa}', talla_zapatos='{talla_zapatos}'")

        # Crear documento del obrero con todos los campos
        documento_obrero = {
            "nombre": nombre,
            "apellidos": apellidos,
            "cedula": cedula_valida,
            "email": email,
            "telefono": telefono,
            "talla_ropa": talla_ropa,
            "talla_zapatos": talla_zapatos,
            "activo": datos.get('activo', True),
            "nivel": datos.get('nivel', 'obrero'),
            "fecha_creacion": get_venezuela_time(),
            "creado_por": "sistema"
        }

        logger.info(f"📄 DOCUMENTO A GUARDAR: {documento_obrero}")
        logger.info(f"🔑 CEDULA EN DOCUMENTO: '{documento_obrero.get('cedula')}' (tipo: {type(documento_obrero.get('cedula'))})")

        # Guardar en base de datos
        resultado = db.obreros.insert_one(documento_obrero)

        logger.info(f"💾 GUARDADO EXITOSO: ID = {resultado.inserted_id}")

        # VERIFICAR QUE SE GUARDÓ CORRECTAMENTE
        obrero_guardado = db.obreros.find_one({"_id": resultado.inserted_id})
        logger.info(f"✅ VERIFICACION POST-GUARDADO: {obrero_guardado}")
        cedula_guardada = obrero_guardado.get('cedula') if obrero_guardado else None
        logger.info(f"🆔 CEDULA GUARDADA EN DB: '{cedula_guardada}' (tipo: {type(cedula_guardada)})")

        logger.info(f"Obrero creado: {nombre} ({email})")

        return jsonify({
            "success": True,
            "message": "Obrero registrado exitosamente",
            "obrero_id": str(resultado.inserted_id),
            "data": {
                "nombre": nombre,
                "apellidos": apellidos,
                "cedula": cedula_valida,
                "email": email,
                "telefono": telefono,
                "talla_ropa": talla_ropa,
                "talla_zapatos": talla_zapatos,
                "activo": documento_obrero["activo"],
                "nivel": documento_obrero["nivel"],
                "fecha_creacion": documento_obrero["fecha_creacion"],
                "creado_por": documento_obrero["creado_por"]
            }
        }), 201

    except Exception as e:
        logger.error(f"Error crear obrero: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

def api_personnel_obreros_update():
    """Update obrero - actualiza obrero existente en base de datos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500

        # DEBUG: Log completo del request
        logger.info("=== OBRERO UPDATE REQUEST DEBUG ===")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Method: {request.method}")
        logger.info(f"Raw data: {request.get_data()}")

        # Intentar obtener datos en diferentes formatos
        datos = None

        if request.is_json:
            datos = request.get_json()
            logger.info("Datos recibidos como JSON")
        elif request.form:
            datos = request.form.to_dict()
            logger.info("Datos recibidos como form data")
        else:
            try:
                import json
                raw_data = request.get_data().decode('utf-8')
                datos = json.loads(raw_data)
                logger.info("Datos parseados desde raw data como JSON")
            except:
                logger.error("No se pudieron parsear los datos")
                return jsonify({
                    "error": "Formato de datos no soportado. Use JSON o form data.",
                    "debug": {
                        "content_type": request.content_type,
                        "method": request.method
                    }
                }), 400

        if not datos:
            logger.error("Datos vacíos después del parsing")
            return jsonify({"error": "No se recibieron datos válidos"}), 400

        logger.info(f"Datos recibidos para actualización: {datos}")

        # Obtener cédula del obrero a actualizar (clave primaria)
        cedula_original = datos.get('cedula_original', datos.get('cedula', ''))
        if not cedula_original:
            return jsonify({"error": "Cédula original es requerida para actualizar"}), 400

        # Validar que el obrero existe
        obrero_existente = db.obreros.find_one({"cedula": cedula_original})
        if not obrero_existente:
            return jsonify({"error": f"No se encontró obrero con cédula '{cedula_original}'"}), 404

        logger.info(f"Obrero encontrado para actualizar: {obrero_existente.get('nombre')} ({obrero_existente.get('email')})")

        # Validar y formatear campos requeridos - CON VALIDACIONES COMPLETAS
        nombre_raw = datos.get('nombre', '')
        apellidos_raw = datos.get('apellidos', '')
        email_raw = datos.get('email', '')
        cedula_nueva = datos.get('cedula', '').strip()

        # Validar nombre (sin números)
        nombre, error_nombre = validate_nombre_apellido(nombre_raw, "nombre")
        if error_nombre:
            return jsonify({"error": error_nombre}), 400

        # Validar apellidos (sin números)
        apellidos, error_apellidos = validate_nombre_apellido(apellidos_raw, "apellido")
        if error_apellidos:
            return jsonify({"error": error_apellidos}), 400

        # Validar email (formato correcto)
        email, error_email = validate_email(email_raw)
        if error_email:
            return jsonify({"error": error_email}), 400

        # Validar nueva cédula
        cedula_valida, error_cedula = validate_cedula(cedula_nueva)
        if error_cedula:
            return jsonify({"error": error_cedula}), 400

        # VALIDACIÓN CRUZADA: Verificar unicidad solo si se cambió el email
        if email != obrero_existente.get('email'):
            # Verificar en obreros (excluyendo el actual)
            if db.obreros.find_one({"email": email, "cedula": {"$ne": cedula_original}}):
                return jsonify({"error": f"Ya existe otro obrero con el email '{email}'"}), 400
            # Verificar en moderadores
            if db.moderadores.find_one({"email": email}):
                return jsonify({"error": f"Ya existe un moderador con el email '{email}'"}), 400

        # VALIDACIÓN CRUZADA: Verificar unicidad solo si se cambió la cédula
        if cedula_valida != cedula_original:
            # Verificar en obreros
            if db.obreros.find_one({"cedula": cedula_valida}):
                return jsonify({"error": f"Ya existe otro obrero con la cédula '{cedula_valida}'"}), 400
            # Verificar en moderadores
            if db.moderadores.find_one({"cedula": cedula_valida}):
                return jsonify({"error": f"Ya existe un moderador con la cédula '{cedula_valida}'"}), 400

        # VALIDACIÓN CRUZADA: Verificar unicidad del teléfono solo si se cambió
        telefono = datos.get('telefono', '').strip()
        if telefono and telefono != obrero_existente.get('telefono'):
            # Verificar en obreros (excluyendo el actual)
            if db.obreros.find_one({"telefono": telefono, "cedula": {"$ne": cedula_original}}):
                return jsonify({"error": f"Ya existe otro obrero con el teléfono '{telefono}'"}), 400
            # Verificar en moderadores
            if db.moderadores.find_one({"telefono": telefono}):
                return jsonify({"error": f"Ya existe un moderador con el teléfono '{telefono}'"}), 400

        # Manejar campos opcionales
        talla_ropa_raw = datos.get('talla_ropa')
        talla_zapatos_raw = datos.get('talla_zapatos')

        talla_ropa_clean = (talla_ropa_raw or '').strip()
        talla_zapatos_clean = (talla_zapatos_raw or '').strip()

        talla_ropa = talla_ropa_clean if talla_ropa_clean else "No ingresado"
        talla_zapatos = talla_zapatos_clean if talla_zapatos_clean else "No ingresado"

        # Preparar documento actualizado
        documento_actualizado = {
            "nombre": nombre,
            "apellidos": apellidos,
            "cedula": cedula_valida,
            "email": email,
            "telefono": telefono,
            "talla_ropa": talla_ropa,
            "talla_zapatos": talla_zapatos,
            "activo": datos.get('activo', obrero_existente.get('activo', True)),
            "nivel": datos.get('nivel', obrero_existente.get('nivel', 'obrero')),
            # Mantener fecha de creación original
            "fecha_creacion": obrero_existente.get('fecha_creacion'),
            "creado_por": obrero_existente.get('creado_por'),
            # Agregar campos de modificación
            "fecha_modificacion": get_venezuela_time(),
            "modificado_por": "sistema"
        }

        logger.info(f"Documento a actualizar: {documento_actualizado}")

        # Actualizar en base de datos
        resultado = db.obreros.update_one(
            {"cedula": cedula_original},
            {"$set": documento_actualizado}
        )

        if resultado.modified_count == 0:
            logger.warning("No se modificó ningún documento - posiblemente datos idénticos")
            # Verificar si existe pero no se modificó
            if resultado.matched_count > 0:
                logger.info("Obrero encontrado pero sin cambios")
            else:
                return jsonify({"error": "No se encontró el obrero para actualizar"}), 404

        logger.info(f"Obrero actualizado exitosamente: {nombre} ({email})")

        # Obtener documento actualizado para respuesta
        obrero_actualizado = db.obreros.find_one({"cedula": cedula_valida}, {"_id": 0})

        return jsonify({
            "success": True,
            "message": "Obrero actualizado exitosamente",
            "data": obrero_actualizado,
            "changes": {
                "matched_count": resultado.matched_count,
                "modified_count": resultado.modified_count
            }
        }), 200

    except Exception as e:
        logger.error(f"Error actualizar obrero: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

def api_personnel_obreros_delete():
    """Delete obrero - elimina obrero existente de la base de datos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500

        # DEBUG: Log completo del request
        logger.info("=== OBRERO DELETE REQUEST DEBUG ===")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Method: {request.method}")
        logger.info(f"Raw data: {request.get_data()}")

        # Intentar obtener datos en diferentes formatos
        datos = None

        if request.is_json:
            datos = request.get_json()
            logger.info("Datos recibidos como JSON")
        elif request.form:
            datos = request.form.to_dict()
            logger.info("Datos recibidos como form data")
        else:
            try:
                import json
                raw_data = request.get_data().decode('utf-8')
                datos = json.loads(raw_data)
                logger.info("Datos parseados desde raw data como JSON")
            except:
                logger.error("No se pudieron parsear los datos")
                return jsonify({
                    "error": "Formato de datos no soportado. Use JSON o form data.",
                    "debug": {
                        "content_type": request.content_type,
                        "method": request.method
                    }
                }), 400

        if not datos:
            logger.error("Datos vacíos después del parsing")
            return jsonify({"error": "No se recibieron datos válidos"}), 400

        logger.info(f"Datos recibidos para eliminación: {datos}")

        # Obtener cédula del obrero a eliminar (clave primaria)
        cedula = datos.get('cedula', '').strip()
        if not cedula:
            return jsonify({"error": "Cédula es requerida para eliminar obrero"}), 400

        # Validar que el obrero existe
        obrero_existente = db.obreros.find_one({"cedula": cedula})
        if not obrero_existente:
            return jsonify({"error": f"No se encontró obrero con cédula '{cedula}'"}), 404

        logger.info(f"Obrero encontrado para eliminar: {obrero_existente.get('nombre')} {obrero_existente.get('apellidos')} ({obrero_existente.get('email')})")

        # Guardar datos del obrero para la respuesta
        obrero_eliminado = {
            "nombre": obrero_existente.get('nombre'),
            "apellidos": obrero_existente.get('apellidos'),
            "cedula": obrero_existente.get('cedula'),
            "email": obrero_existente.get('email'),
            "telefono": obrero_existente.get('telefono'),
            "fecha_creacion": obrero_existente.get('fecha_creacion'),
            "fecha_eliminacion": get_venezuela_time(),
            "eliminado_por": "sistema"
        }

        # Eliminar de base de datos
        resultado = db.obreros.delete_one({"cedula": cedula})

        if resultado.deleted_count == 0:
            logger.warning("No se eliminó ningún documento")
            return jsonify({"error": "No se pudo eliminar el obrero"}), 500

        logger.info(f"Obrero eliminado exitosamente: {obrero_eliminado['nombre']} {obrero_eliminado['apellidos']}")

        return jsonify({
            "success": True,
            "message": "Obrero eliminado exitosamente",
            "obrero_eliminado": obrero_eliminado,
            "deleted_count": resultado.deleted_count
        }), 200

    except Exception as e:
        logger.error(f"Error eliminar obrero: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

def api_personnel_obreros_debug():
    """DEBUG endpoint for obreros - returns all request info"""
    try:
        return jsonify({
            "method": request.method,
            "url": request.url,
            "headers": dict(request.headers),
            "args": dict(request.args),
            "form": dict(request.form),
            "json": request.get_json(silent=True),
            "data": request.get_data().decode('utf-8', errors='ignore'),
            "content_type": request.content_type,
            "is_json": request.is_json,
            "content_length": request.content_length,
            "timestamp": datetime.now().isoformat(),
            "endpoint": "obreros_debug"
        })
    except Exception as e:
        return jsonify({"debug_error": str(e)})