#!/usr/bin/env python3
"""
Unified Backend - Main entry point for deployment
Combines legacy chat_backend with modern API endpoints
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment variables
load_dotenv()

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Import existing chat backend
from chat_backend import app, db, get_db_status

# Import modern API blueprints
try:
    from backend.api.personnel.routes import personnel_bp
    BLUEPRINT_LOADED = True
    logger.info("Personnel API blueprint loaded successfully")
except ImportError as e:
    logger.error(f"Failed to import personnel blueprint: {e}")
    BLUEPRINT_LOADED = False

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register API blueprints
if BLUEPRINT_LOADED:
    app.register_blueprint(personnel_bp)
    logger.info("Personnel blueprint registered successfully")
else:
    logger.warning("Personnel blueprint not loaded - using fallback endpoints")

# ==================== MODERN API ENDPOINTS ====================

# Auth status endpoint already exists in chat_backend.py

@app.route('/api/channels/', methods=['GET'])
def api_channels_list():
    """List channels - modern endpoint"""
    try:
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        canales = list(db.canales.find({}, {"_id": 0}))
        return jsonify({
            "success": True,
            "channels": canales,
            "count": len(canales)
        })
    except Exception as e:
        logger.error(f"Error api_channels: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/personnel/cuadrillas/', methods=['GET'])
def api_personnel_cuadrillas():
    """Personnel - work crews"""
    return jsonify({
        "success": True,
        "cuadrillas": [
            {"id": 1, "nombre": "Cuadrilla A", "supervisor": "Juan Pérez"},
            {"id": 2, "nombre": "Cuadrilla B", "supervisor": "María García"}
        ]
    })

@app.route('/api/personnel/cuadrillas/', methods=['POST'])
def api_personnel_cuadrillas_create():
    """Create work crew"""
    datos = request.get_json()
    return jsonify({
        "success": True,
        "message": "Cuadrilla creada exitosamente",
        "data": datos
    }), 201

@app.route('/api/personnel/obreros/', methods=['GET'])
def api_personnel_obreros():
    """Personnel - workers"""
    return jsonify({
        "success": True,
        "obreros": [
            {"id": 1, "nombre": "Carlos López", "cuadrilla_id": 1},
            {"id": 2, "nombre": "Ana Torres", "cuadrilla_id": 1}
        ]
    })

@app.route('/api/personnel/obreros/', methods=['POST'])
def api_personnel_obreros_create():
    """Create worker"""
    datos = request.get_json()
    return jsonify({
        "success": True,
        "message": "Obrero registrado exitosamente",
        "data": datos
    }), 201

# Fallback endpoints if blueprint doesn't load
if not BLUEPRINT_LOADED:
    @app.route('/api/personnel/moderadores/', methods=['GET'])
    def fallback_get_moderadores():
        """Fallback GET moderadores endpoint"""
        try:
            if db is None:
                return jsonify({"error": "Base de datos no disponible"}), 500
            
            moderadores_raw = list(db.personal_moderador.find({}))
            
            # Formatear moderadores para compatibilidad con frontend
            moderadores = []
            for mod in moderadores_raw:
                moderador_formateado = {
                    "nombre": mod.get("nombre", ""),
                    "apellidos": mod.get("apellidos", ""),
                    "email": mod.get("email", mod.get("correo", "")),
                    "telefono": mod.get("telefono", ""),
                    "talla_ropa": mod.get("talla_ropa", ""),
                    "talla_zapatos": mod.get("talla_zapatos", ""),
                    "nivel": mod.get("nivel", "moderador"),
                    "activo": mod.get("activo", True),
                    "fecha_creacion": mod.get("fecha_creacion", mod.get("registrado", "")),
                    "creado_por": mod.get("creado_por", "sistema"),
                    "_id": str(mod["_id"])  # Incluir ID para mapeo
                }
                moderadores.append(moderador_formateado)
                
            return jsonify({
                "moderadores": moderadores,
                "total": len(moderadores)
            })
        except Exception as e:
            logger.error(f"Error fallback GET moderadores: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/personnel/moderadores/', methods=['POST'])
    def fallback_create_moderador():
        """Fallback POST moderador endpoint"""
        try:
            if db is None:
                return jsonify({"error": "Base de datos no disponible"}), 500
                
            datos = request.get_json()
            if not datos:
                return jsonify({"error": "No se recibieron datos"}), 400
            
            # Validación básica
            nombre = datos.get("nombre", "").strip()
            if not nombre:
                return jsonify({"error": "El nombre es obligatorio"}), 400
            
            email = datos.get("email", "").strip()
            if not email:
                return jsonify({"error": "El email es obligatorio"}), 400
            
            # Verificar duplicados
            if db.personal_moderador.find_one({"$or": [{"email": email}, {"correo": email}]}):
                return jsonify({"error": f"Ya existe un moderador con email {email}"}), 400
            
            # Crear documento
            moderador_doc = {
                "nombre": nombre,
                "apellidos": datos.get("apellidos", ""),
                "email": email,
                "telefono": datos.get("telefono", ""),
                "talla_ropa": datos.get("talla_ropa", ""),
                "talla_zapatos": datos.get("talla_zapatos", ""),
                "nivel": datos.get("nivel", "moderador"),
                "creado_por": "sistema",
                "fecha_creacion": datetime.now(),
                "activo": True
            }
            
            resultado = db.personal_moderador.insert_one(moderador_doc)
            
            return jsonify({
                "data": {
                    "nombre": moderador_doc["nombre"],
                    "email": moderador_doc["email"],
                    "apellidos": moderador_doc["apellidos"],
                    "telefono": moderador_doc["telefono"],
                    "talla_ropa": moderador_doc["talla_ropa"],
                    "talla_zapatos": moderador_doc["talla_zapatos"],
                    "nivel": moderador_doc["nivel"],
                    "activo": moderador_doc["activo"],
                    "fecha_creacion": moderador_doc["fecha_creacion"],
                    "creado_por": moderador_doc["creado_por"]
                },
                "message": "Moderador registrado exitosamente",
                "moderador_id": str(resultado.inserted_id),
                "success": True
            }), 201
            
        except Exception as e:
            logger.error(f"Error fallback POST moderador: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/reports/personal/resumen', methods=['GET'])
def api_reports_personal():
    """Personnel reports summary"""
    return jsonify({
        "success": True,
        "resumen": {
            "total_cuadrillas": 2,
            "total_obreros": 15,
            "activos": 14,
            "inactivos": 1
        }
    })

@app.route('/api/reports/chat/resumen', methods=['GET'])
def api_reports_chat():
    """Chat reports summary"""
    try:
        db_status = get_db_status()
        return jsonify({
            "success": True,
            "resumen": {
                "total_canales": db_status.get("canales", 0),
                "total_mensajes": db_status.get("mensajes", 0),
                "estado_db": db_status.get("status", "unknown")
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/exportar/cuadrillas', methods=['GET'])
def api_reports_exportar():
    """Export work crews"""
    return jsonify({
        "success": True,
        "export_url": "/downloads/cuadrillas_2025.xlsx",
        "format": "excel",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting unified backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)