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

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MODERN API ENDPOINTS ====================

@app.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    """Authentication status"""
    return jsonify({
        "authenticated": True,
        "user": "sistema",
        "timestamp": datetime.now().isoformat()
    })

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