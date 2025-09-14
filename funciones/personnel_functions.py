"""
Funciones de Personal
Maneja todas las operaciones relacionadas con moderadores y personal
"""

import logging
from datetime import datetime
from flask import request, jsonify
from funciones.database_functions import get_db

# Logger para este módulo
logger = logging.getLogger(__name__)

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
        
        # Validar campos requeridos - MEJORADO para detectar diferentes nombres de campo
        nombre = datos.get('nombre', datos.get('name', datos.get('nombres', ''))).strip()
        email = datos.get('email', datos.get('correo', datos.get('mail', ''))).strip()
        cedula_raw = datos.get('cedula', datos.get('ci', datos.get('documento', '')))
        
        logger.info(f"Nombre extraído: '{nombre}', Email extraído: '{email}', Cédula: '{cedula_raw}'")
        
        if not nombre:
            nombre_original = datos.get('nombre', datos.get('name', ''))
            if nombre_original and not nombre_original.strip():
                error_msg = "El nombre no puede estar vacío o contener solo espacios en blanco"
            else:
                error_msg = "El nombre es obligatorio"
            
            return jsonify({
                "error": error_msg,
                "ayuda": "Asegúrate de ingresar un nombre válido sin solo espacios",
                "debug": {
                    "datos_recibidos": datos,
                    "nombre_original": nombre_original,
                    "nombre_despues_strip": nombre,
                    "claves_disponibles": list(datos.keys())
                }
            }), 400
        if not email:
            return jsonify({
                "error": "El email es obligatorio",
                "debug": {
                    "datos_recibidos": datos,
                    "email_valor": email,
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
        
        # Verificar que no exista el email
        if db.moderadores.find_one({"email": email}):
            return jsonify({"error": f"Ya existe un moderador con el email '{email}'"}), 400
        
        # Verificar que no exista la cédula
        if db.moderadores.find_one({"cedula": cedula_valida}):
            return jsonify({"error": f"Ya existe un moderador con la cédula '{cedula_valida}'"}), 400
        
        # Obtener campos adicionales
        apellidos = datos.get('apellidos', '').strip()
        telefono = datos.get('telefono', '').strip()
        
        # NUEVO: Verificar que no exista el teléfono
        if telefono and db.moderadores.find_one({"telefono": telefono}):
            return jsonify({"error": f"Ya existe un moderador con el teléfono '{telefono}'"}), 400
        
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
            "fecha_creacion": datetime.now(),
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