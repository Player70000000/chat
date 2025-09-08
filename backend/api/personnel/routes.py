import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from pymongo.errors import WriteConcernError, OperationFailure

from ...config.database import get_db
from ...utils.validators import validate_cuadrilla_data, validate_obrero_data

logger = logging.getLogger(__name__)
personnel_bp = Blueprint('personnel', __name__, url_prefix='/api/personnel')

# =============================================================================
# ENDPOINTS DE CUADRILLAS
# =============================================================================

@personnel_bp.route('/cuadrillas/', methods=['GET'])
def listar_cuadrillas():
    """Listar todas las cuadrillas"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        cuadrillas = list(db.cuadrillas.find({}, {"_id": 0}))
        return jsonify({
            "cuadrillas": cuadrillas,
            "total": len(cuadrillas)
        })
        
    except Exception as e:
        logger.error(f"Error listar cuadrillas: {e}")
        return jsonify({"error": str(e)}), 500

@personnel_bp.route('/cuadrillas/', methods=['POST'])
def crear_cuadrilla():
    """Crear nueva cuadrilla"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
            
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        datos_validados, error = validate_cuadrilla_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        # Verificar si ya existe cuadrilla con ese número
        if db.cuadrillas.find_one({"numero_cuadrilla": datos_validados["numero_cuadrilla"]}):
            return jsonify({
                "error": f"La cuadrilla {datos_validados['numero_cuadrilla']} ya existe"
            }), 400
        
        # Crear cuadrilla
        cuadrilla_doc = {
            "numero_cuadrilla": datos_validados["numero_cuadrilla"],
            "actividad": datos_validados["actividad"],
            "creada": datetime.now(),
            "activa": True
        }
        
        resultado = db.cuadrillas.insert_one(cuadrilla_doc)
        
        return jsonify({
            "mensaje": f"Cuadrilla {datos_validados['numero_cuadrilla']} creada exitosamente",
            "cuadrilla_id": str(resultado.inserted_id),
            "numero_cuadrilla": datos_validados["numero_cuadrilla"],
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except (WriteConcernError, OperationFailure) as e:
        logger.error(f"Error BD crear_cuadrilla: {e}")
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as e:
        logger.error(f"Error crear_cuadrilla: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@personnel_bp.route('/cuadrillas/<numero>', methods=['GET'])
def obtener_cuadrilla(numero):
    """Obtener información de una cuadrilla"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        cuadrilla = db.cuadrillas.find_one({"numero_cuadrilla": numero}, {"_id": 0})
        if not cuadrilla:
            return jsonify({
                "error": "Cuadrilla no encontrada",
                "mensaje": f"La cuadrilla {numero} no existe"
            }), 404
        
        return jsonify(cuadrilla), 200
        
    except Exception as e:
        logger.error(f"Error obtener cuadrilla {numero}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@personnel_bp.route('/cuadrillas/<numero>', methods=['PUT'])
def editar_cuadrilla(numero):
    """Editar información de cuadrilla"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
        
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        # Verificar existencia
        if not db.cuadrillas.find_one({"numero_cuadrilla": numero}):
            return jsonify({
                "error": "Cuadrilla no encontrada",
                "mensaje": f"La cuadrilla {numero} no existe"
            }), 404
        
        datos_validados, error = validate_cuadrilla_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        # Actualizar cuadrilla
        resultado = db.cuadrillas.update_one(
            {"numero_cuadrilla": numero},
            {"$set": {
                "actividad": datos_validados["actividad"],
                "modificada": datetime.now()
            }}
        )
        
        if resultado.modified_count == 0:
            return jsonify({"error": "No se pudo actualizar la cuadrilla"}), 500
        
        return jsonify({
            "mensaje": "Cuadrilla actualizada exitosamente",
            "numero_cuadrilla": numero,
            "actividad": datos_validados["actividad"],
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error editar cuadrilla {numero}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@personnel_bp.route('/cuadrillas/<numero>', methods=['DELETE'])
def eliminar_cuadrilla(numero):
    """Eliminar cuadrilla"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Verificar existencia
        if not db.cuadrillas.find_one({"numero_cuadrilla": numero}):
            return jsonify({
                "error": "Cuadrilla no encontrada",
                "mensaje": f"La cuadrilla {numero} no existe"
            }), 404
        
        # Eliminar cuadrilla
        resultado = db.cuadrillas.delete_one({"numero_cuadrilla": numero})
        
        if resultado.deleted_count == 0:
            return jsonify({"error": "No se pudo eliminar la cuadrilla"}), 500
        
        return jsonify({
            "mensaje": f"Cuadrilla {numero} eliminada exitosamente",
            "numero_cuadrilla": numero,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error eliminar cuadrilla {numero}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# =============================================================================
# ENDPOINTS DE OBREROS
# =============================================================================

@personnel_bp.route('/obreros/', methods=['GET'])
def listar_obreros():
    """Listar todos los obreros"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        obreros = list(db.personal_obrero.find({}, {"_id": 0}))
        return jsonify({
            "obreros": obreros,
            "total": len(obreros)
        })
        
    except Exception as e:
        logger.error(f"Error listar obreros: {e}")
        return jsonify({"error": str(e)}), 500

@personnel_bp.route('/obreros/', methods=['POST'])
def crear_obrero():
    """Registrar nuevo obrero"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
            
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        datos_validados, error = validate_obrero_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        # Verificar si ya existe obrero con esa cédula
        if db.personal_obrero.find_one({"cedula": datos_validados["cedula"]}):
            return jsonify({
                "error": f"Ya existe un obrero con cédula {datos_validados['cedula']}"
            }), 400
        
        # Crear obrero
        obrero_doc = {
            "nombre": datos_validados["nombre"],
            "apellido": datos_validados["apellido"],
            "cedula": datos_validados["cedula"],
            "registrado": datetime.now(),
            "activo": True
        }
        
        resultado = db.personal_obrero.insert_one(obrero_doc)
        
        return jsonify({
            "mensaje": "Obrero registrado exitosamente",
            "obrero_id": str(resultado.inserted_id),
            "cedula": datos_validados["cedula"],
            "nombre_completo": f"{datos_validados['nombre']} {datos_validados['apellido']}",
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except (WriteConcernError, OperationFailure) as e:
        logger.error(f"Error BD crear_obrero: {e}")
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as e:
        logger.error(f"Error crear_obrero: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@personnel_bp.route('/obreros/<cedula>', methods=['GET'])
def obtener_obrero(cedula):
    """Obtener información de un obrero por cédula"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        obrero = db.personal_obrero.find_one({"cedula": cedula}, {"_id": 0})
        if not obrero:
            return jsonify({
                "error": "Obrero no encontrado",
                "mensaje": f"No existe obrero con cédula {cedula}"
            }), 404
        
        return jsonify(obrero), 200
        
    except Exception as e:
        logger.error(f"Error obtener obrero {cedula}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@personnel_bp.route('/obreros/<cedula>', methods=['DELETE'])
def eliminar_obrero(cedula):
    """Eliminar obrero"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Verificar existencia
        if not db.personal_obrero.find_one({"cedula": cedula}):
            return jsonify({
                "error": "Obrero no encontrado",
                "mensaje": f"No existe obrero con cédula {cedula}"
            }), 404
        
        # Eliminar obrero
        resultado = db.personal_obrero.delete_one({"cedula": cedula})
        
        if resultado.deleted_count == 0:
            return jsonify({"error": "No se pudo eliminar el obrero"}), 500
        
        return jsonify({
            "mensaje": "Obrero eliminado exitosamente",
            "cedula": cedula,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error eliminar obrero {cedula}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# =============================================================================
# ENDPOINTS DE MODERADORES
# =============================================================================

@personnel_bp.route('/moderadores/', methods=['GET'])
def listar_moderadores():
    """Listar todos los moderadores"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        moderadores = list(db.personal_moderador.find({}, {"_id": 0}))
        return jsonify({
            "moderadores": moderadores,
            "total": len(moderadores)
        })
        
    except Exception as e:
        logger.error(f"Error listar moderadores: {e}")
        return jsonify({"error": str(e)}), 500

@personnel_bp.route('/moderadores/', methods=['POST'])
def crear_moderador():
    """Registrar nuevo moderador"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
            
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
            
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        # Validar datos requeridos
        error = validate_moderador_data(datos)
        if error:
            return jsonify({"error": error}), 400
        
        # Verificar si ya existe moderador con ese correo
        if db.personal_moderador.find_one({"correo": datos["correo"]}):
            return jsonify({
                "error": f"Ya existe un moderador con correo {datos['correo']}"
            }), 400
        
        # Crear moderador
        moderador_doc = {
            "nombres": datos["nombres"],
            "apellidos": datos["apellidos"],
            "correo": datos["correo"],
            "telefono": datos["telefono"],
            "talla_ropa": datos.get("talla_ropa", ""),
            "talla_zapatos": datos.get("talla_zapatos", ""),
            "registrado": datetime.now(),
            "activo": True
        }
        
        resultado = db.personal_moderador.insert_one(moderador_doc)
        
        return jsonify({
            "mensaje": "Moderador registrado exitosamente",
            "moderador_id": str(resultado.inserted_id),
            "correo": datos["correo"],
            "nombre_completo": f"{datos['nombres']} {datos['apellidos']}",
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except (WriteConcernError, OperationFailure) as e:
        logger.error(f"Error BD crear_moderador: {e}")
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as e:
        logger.error(f"Error crear_moderador: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@personnel_bp.route('/moderadores/<correo>', methods=['GET'])
def obtener_moderador(correo):
    """Obtener información de un moderador por correo"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        moderador = db.personal_moderador.find_one({"correo": correo}, {"_id": 0})
        if not moderador:
            return jsonify({
                "error": "Moderador no encontrado",
                "mensaje": f"No existe moderador con correo {correo}"
            }), 404
        
        return jsonify(moderador), 200
        
    except Exception as e:
        logger.error(f"Error obtener moderador {correo}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@personnel_bp.route('/moderadores/<correo>', methods=['DELETE'])
def eliminar_moderador(correo):
    """Eliminar moderador"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Verificar existencia
        if not db.personal_moderador.find_one({"correo": correo}):
            return jsonify({
                "error": "Moderador no encontrado",
                "mensaje": f"No existe moderador con correo {correo}"
            }), 404
        
        # Eliminar moderador
        resultado = db.personal_moderador.delete_one({"correo": correo})
        
        if resultado.deleted_count == 0:
            return jsonify({"error": "No se pudo eliminar el moderador"}), 500
        
        return jsonify({
            "mensaje": "Moderador eliminado exitosamente",
            "correo": correo,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error eliminar moderador {correo}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

def validate_moderador_data(datos):
    """Validar datos de moderador"""
    if not datos.get("nombres", "").strip():
        return "Los nombres son requeridos"
    
    if not datos.get("apellidos", "").strip():
        return "Los apellidos son requeridos"
    
    if not datos.get("correo", "").strip():
        return "El correo es requerido"
    
    if not datos.get("telefono", "").strip():
        return "El teléfono es requerido"
    
    # Validar formato de correo básico
    correo = datos["correo"].strip()
    if "@" not in correo or "." not in correo:
        return "Formato de correo inválido"
    
    # Validar longitud de teléfono
    telefono = datos["telefono"].strip()
    if len(telefono) < 7:
        return "Teléfono debe tener al menos 7 caracteres"
    
    return None

# =============================================================================
# ENDPOINTS LEGACY (Compatibilidad)
# =============================================================================

def get_data_cuadrilla():
    """Legacy endpoint - crear cuadrilla (compatible con frontend viejo)"""
    return crear_cuadrilla()

def get_data_obrero():
    """Legacy endpoint - crear obrero (compatible con frontend viejo)"""
    return crear_obrero()

def obtener_opciones_backend():
    """Legacy endpoint - obtener números de cuadrillas para selector"""
    try:
        db = get_db()
        if db is None:
            return []
        
        cuadrillas = db.cuadrillas.find({}, {"_id": 0, "numero_cuadrilla": 1})
        return [c["numero_cuadrilla"] for c in cuadrillas]
        
    except Exception as e:
        logger.error(f"Error obtener opciones cuadrillas: {e}")
        return []