"""
Funciones de Cuadrillas
Maneja todas las operaciones relacionadas con la gestión de cuadrillas
"""

import logging
from datetime import datetime, timezone, timedelta
from flask import request, jsonify
from bson import ObjectId
from funciones.database_functions import get_db

# Logger para este módulo
logger = logging.getLogger(__name__)

def get_venezuela_time():
    """Obtener la hora actual de Venezuela (GMT-4)"""
    # Venezuela está en GMT-4 (4 horas atrás de UTC)
    venezuela_tz = timezone(timedelta(hours=-4))
    return datetime.now(venezuela_tz)

def get_next_cuadrilla_number():
    """Obtener el próximo número de cuadrilla disponible"""
    try:
        db = get_db()
        cuadrillas_collection = db.cuadrillas

        # Buscar la cuadrilla con el número más alto
        last_cuadrilla = cuadrillas_collection.find().sort("numero_cuadrilla", -1).limit(1)
        last_cuadrilla = list(last_cuadrilla)

        if not last_cuadrilla:
            # Primera cuadrilla
            return "Cuadrilla-N°1"

        # Extraer el número de la última cuadrilla
        last_number_str = last_cuadrilla[0]["numero_cuadrilla"]
        # Formato: "Cuadrilla-N°X" -> extraer X
        last_number = int(last_number_str.split("°")[1])
        next_number = last_number + 1

        return f"Cuadrilla-N°{next_number}"

    except Exception as e:
        logger.error(f"Error obteniendo próximo número de cuadrilla: {str(e)}")
        return "Cuadrilla-N°1"  # Fallback seguro

def get_persona_snapshot(collection_name, persona_id):
    """Obtener snapshot de una persona (moderador o obrero) por ID"""
    try:
        db = get_db()
        collection = db[collection_name]

        # Buscar la persona por ID
        persona = collection.find_one({"_id": ObjectId(persona_id)})

        if not persona:
            return None, f"No se encontró la persona con ID {persona_id} en {collection_name}"

        # Crear snapshot con datos esenciales
        snapshot = {
            "id": persona["_id"],
            "nombre": persona.get("nombre", ""),
            "apellidos": persona.get("apellidos", ""),
            "cedula": persona.get("cedula", "")
        }

        return snapshot, None

    except Exception as e:
        logger.error(f"Error obteniendo snapshot de persona: {str(e)}")
        return None, f"Error interno obteniendo datos de la persona"

def check_obreros_disponibles(obreros_ids):
    """Verificar que los obreros no estén ya asignados a cuadrillas activas"""
    try:
        db = get_db()
        cuadrillas_collection = db.cuadrillas

        # Buscar cuadrillas activas que contengan alguno de estos obreros
        cuadrillas_activas = cuadrillas_collection.find({"activo": True})

        obreros_ya_asignados = []

        for cuadrilla in cuadrillas_activas:
            for obrero in cuadrilla.get("obreros", []):
                obrero_id = str(obrero.get("id"))
                if obrero_id in obreros_ids:
                    obrero_info = f"{obrero.get('nombre')} {obrero.get('apellidos')} (CI: {obrero.get('cedula')})"
                    cuadrilla_info = cuadrilla.get('numero_cuadrilla', 'N/A')
                    obreros_ya_asignados.append(f"{obrero_info} en {cuadrilla_info}")

        if obreros_ya_asignados:
            error_msg = "Los siguientes obreros ya están asignados a cuadrillas activas:\n"
            error_msg += "\n".join([f"• {info}" for info in obreros_ya_asignados])
            return False, error_msg

        return True, None

    except Exception as e:
        logger.error(f"Error verificando obreros disponibles: {str(e)}")
        return False, "Error interno verificando disponibilidad de obreros"

def validate_cuadrilla_data(data):
    """Validar datos de cuadrilla antes de guardar"""

    # Validar actividad
    if not data.get("actividad") or not data.get("actividad").strip():
        return False, "Debe especificar la actividad de la cuadrilla"

    # Validar moderador
    if not data.get("moderador_id"):
        return False, "Debe seleccionar un moderador"

    # Validar obreros
    if not data.get("obreros_ids") or len(data.get("obreros_ids")) == 0:
        return False, "Debe seleccionar al menos un obrero"

    # Validar rango de obreros (4-40)
    num_obreros = len(data.get("obreros_ids"))
    if num_obreros < 4:
        return False, "Una cuadrilla debe tener mínimo 4 obreros"

    if num_obreros > 40:
        return False, "Una cuadrilla debe tener máximo 40 obreros"

    # Validar obreros únicos
    obreros_ids = data.get("obreros_ids")
    if len(set(obreros_ids)) != len(obreros_ids):
        return False, "No se pueden repetir obreros en la misma cuadrilla"

    # Validar creado_por
    if not data.get("creado_por"):
        return False, "Debe especificar quién crea la cuadrilla"

    # VALIDACIÓN CRÍTICA: Verificar que los obreros no estén ya asignados
    obreros_ids = [str(oid) for oid in data.get("obreros_ids")]
    disponibles, error_msg = check_obreros_disponibles(obreros_ids)
    if not disponibles:
        return False, error_msg

    return True, None

def create_cuadrilla():
    """Crear una nueva cuadrilla"""
    try:
        # Obtener datos del request
        data = request.get_json()

        # Validar datos
        is_valid, error_msg = validate_cuadrilla_data(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        db = get_db()

        # Obtener próximo número de cuadrilla
        numero_cuadrilla = get_next_cuadrilla_number()

        # Obtener snapshot del moderador
        moderador_snapshot, error = get_persona_snapshot("moderadores", data["moderador_id"])
        if error:
            return jsonify({"error": f"Error con moderador: {error}"}), 400

        # Obtener snapshots de los obreros
        obreros_snapshots = []
        for obrero_id in data["obreros_ids"]:
            obrero_snapshot, error = get_persona_snapshot("obreros", obrero_id)
            if error:
                return jsonify({"error": f"Error con obrero: {error}"}), 400
            obreros_snapshots.append(obrero_snapshot)

        # Crear documento de cuadrilla
        cuadrilla_doc = {
            "numero_cuadrilla": numero_cuadrilla,
            "actividad": data["actividad"].strip(),
            "activo": True,
            "moderador": moderador_snapshot,
            "obreros": obreros_snapshots,
            "numero_obreros": len(obreros_snapshots),
            "fecha_creacion": get_venezuela_time(),
            "creado_por": data["creado_por"],
            "fecha_modificacion": get_venezuela_time(),
            "modificado_por": data["creado_por"]
        }

        # Insertar en base de datos
        cuadrillas_collection = db.cuadrillas
        result = cuadrillas_collection.insert_one(cuadrilla_doc)

        if result.inserted_id:
            logger.info(f"Cuadrilla creada exitosamente: {numero_cuadrilla}")

            # Preparar respuesta con el documento creado
            cuadrilla_doc["_id"] = str(result.inserted_id)
            cuadrilla_doc["moderador"]["id"] = str(cuadrilla_doc["moderador"]["id"])

            for obrero in cuadrilla_doc["obreros"]:
                obrero["id"] = str(obrero["id"])

            return jsonify({
                "success": True,
                "message": f"Cuadrilla {numero_cuadrilla} creada exitosamente",
                "cuadrilla": cuadrilla_doc
            }), 201
        else:
            return jsonify({"error": "Error al insertar cuadrilla en base de datos"}), 500

    except Exception as e:
        logger.error(f"Error creando cuadrilla: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

def get_cuadrillas():
    """Obtener lista de todas las cuadrillas"""
    try:
        db = get_db()
        cuadrillas_collection = db.cuadrillas

        # Obtener solo cuadrillas activas ordenadas por número
        cuadrillas = list(cuadrillas_collection.find({"activo": True}).sort("numero_cuadrilla", 1))

        # Convertir ObjectIds a strings para JSON
        for cuadrilla in cuadrillas:
            cuadrilla["_id"] = str(cuadrilla["_id"])
            cuadrilla["moderador"]["id"] = str(cuadrilla["moderador"]["id"])

            for obrero in cuadrilla["obreros"]:
                obrero["id"] = str(obrero["id"])

        return jsonify({
            "success": True,
            "cuadrillas": cuadrillas,
            "total": len(cuadrillas)
        }), 200

    except Exception as e:
        logger.error(f"Error obteniendo cuadrillas: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

def get_cuadrilla_by_id(cuadrilla_id):
    """Obtener una cuadrilla específica por ID"""
    try:
        db = get_db()
        cuadrillas_collection = db.cuadrillas

        # Buscar cuadrilla por ID
        cuadrilla = cuadrillas_collection.find_one({"_id": ObjectId(cuadrilla_id)})

        if not cuadrilla:
            return jsonify({"error": "Cuadrilla no encontrada"}), 404

        # Convertir ObjectIds a strings
        cuadrilla["_id"] = str(cuadrilla["_id"])
        cuadrilla["moderador"]["id"] = str(cuadrilla["moderador"]["id"])

        for obrero in cuadrilla["obreros"]:
            obrero["id"] = str(obrero["id"])

        return jsonify({
            "success": True,
            "cuadrilla": cuadrilla
        }), 200

    except Exception as e:
        logger.error(f"Error obteniendo cuadrilla por ID: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

def update_cuadrilla(cuadrilla_id):
    """Actualizar una cuadrilla existente"""
    try:
        # Obtener datos del request
        data = request.get_json()

        # Validar datos
        is_valid, error_msg = validate_cuadrilla_data(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        db = get_db()
        cuadrillas_collection = db.cuadrillas

        # Verificar que la cuadrilla existe
        existing_cuadrilla = cuadrillas_collection.find_one({"_id": ObjectId(cuadrilla_id)})
        if not existing_cuadrilla:
            return jsonify({"error": "Cuadrilla no encontrada"}), 404

        # Obtener snapshot del moderador
        moderador_snapshot, error = get_persona_snapshot("moderadores", data["moderador_id"])
        if error:
            return jsonify({"error": f"Error con moderador: {error}"}), 400

        # Obtener snapshots de los obreros
        obreros_snapshots = []
        for obrero_id in data["obreros_ids"]:
            obrero_snapshot, error = get_persona_snapshot("obreros", obrero_id)
            if error:
                return jsonify({"error": f"Error con obrero: {error}"}), 400
            obreros_snapshots.append(obrero_snapshot)

        # Preparar actualización
        update_data = {
            "moderador": moderador_snapshot,
            "obreros": obreros_snapshots,
            "numero_obreros": len(obreros_snapshots),
            "fecha_modificacion": get_venezuela_time(),
            "modificado_por": data.get("creado_por", "sistema")  # Usar creado_por como modificado_por
        }

        # Actualizar en base de datos
        result = cuadrillas_collection.update_one(
            {"_id": ObjectId(cuadrilla_id)},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            logger.info(f"Cuadrilla {cuadrilla_id} actualizada exitosamente")
            return jsonify({
                "success": True,
                "message": "Cuadrilla actualizada exitosamente"
            }), 200
        else:
            return jsonify({"error": "No se realizaron cambios en la cuadrilla"}), 400

    except Exception as e:
        logger.error(f"Error actualizando cuadrilla: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

def delete_cuadrilla(cuadrilla_id):
    """Eliminar una cuadrilla (marcar como inactiva)"""
    try:
        db = get_db()
        cuadrillas_collection = db.cuadrillas

        # Verificar que la cuadrilla existe
        existing_cuadrilla = cuadrillas_collection.find_one({"_id": ObjectId(cuadrilla_id)})
        if not existing_cuadrilla:
            return jsonify({"error": "Cuadrilla no encontrada"}), 404

        # Marcar como inactiva (soft delete)
        result = cuadrillas_collection.update_one(
            {"_id": ObjectId(cuadrilla_id)},
            {
                "$set": {
                    "activo": False,
                    "fecha_modificacion": get_venezuela_time(),
                    "modificado_por": "sistema"
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Cuadrilla {cuadrilla_id} marcada como inactiva")
            return jsonify({
                "success": True,
                "message": "Cuadrilla eliminada exitosamente"
            }), 200
        else:
            return jsonify({"error": "No se pudo eliminar la cuadrilla"}), 400

    except Exception as e:
        logger.error(f"Error eliminando cuadrilla: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

def get_next_cuadrilla_number_api():
    """Endpoint API para obtener el próximo número de cuadrilla"""
    try:
        numero = get_next_cuadrilla_number()
        return jsonify({
            "success": True,
            "numero_cuadrilla": numero
        }), 200

    except Exception as e:
        logger.error(f"Error en API próximo número: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

def get_obreros_disponibles():
    """Obtener lista de obreros que NO están asignados a cuadrillas activas"""
    try:
        db = get_db()
        obreros_collection = db.obreros
        cuadrillas_collection = db.cuadrillas

        # Obtener todos los obreros
        todos_obreros = list(obreros_collection.find())

        # Obtener obreros asignados a cuadrillas activas
        cuadrillas_activas = cuadrillas_collection.find({"activo": True})
        obreros_asignados_ids = set()

        for cuadrilla in cuadrillas_activas:
            for obrero in cuadrilla.get("obreros", []):
                # Usar el ObjectId del obrero asignado
                obrero_id = obrero.get("id")
                if obrero_id:
                    obreros_asignados_ids.add(str(obrero_id))

        # Filtrar obreros disponibles (no asignados)
        obreros_disponibles = []
        for obrero in todos_obreros:
            obrero_id_str = str(obrero["_id"])
            if obrero_id_str not in obreros_asignados_ids:
                # Convertir ObjectId a string para JSON
                obrero["_id"] = obrero_id_str
                obreros_disponibles.append(obrero)

        logger.info(f"Obreros disponibles: {len(obreros_disponibles)} de {len(todos_obreros)} totales")

        return jsonify({
            "success": True,
            "obreros": obreros_disponibles,
            "count": len(obreros_disponibles),
            "total_obreros": len(todos_obreros),
            "asignados": len(obreros_asignados_ids)
        }), 200

    except Exception as e:
        logger.error(f"Error obteniendo obreros disponibles: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500