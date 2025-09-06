import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

from backend.config.database import init_db
from backend.api.channels.routes import channels_bp
from backend.api.messages.routes import messages_bp
from backend.api.auth.routes import auth_bp
from backend.api.personnel.routes import personnel_bp
from backend.api.reports.routes import reports_bp

# Configuración básica de logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    CORS(app)
    
    # Inicializar base de datos
    if not init_db():
        logger.error("No se pudo inicializar la base de datos")
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(channels_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(personnel_bp)
    app.register_blueprint(reports_bp)
    
    # Mantener compatibilidad con rutas legacy
    setup_legacy_routes(app)
    
    # Manejadores de errores globales
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint no encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Error 500: {error}")
        return jsonify({"error": "Error interno del servidor"}), 500
    
    return app

def setup_legacy_routes(app):
    """Configurar rutas de compatibilidad con el sistema anterior"""
    from backend.api.auth.routes import pagina_inicio, verificar_conexion
    from backend.api.channels.routes import (
        crear_canal as crear_canal_legacy,
        listar_canales as listar_canales_legacy,
        obtener_canal as obtener_canal_legacy,
        editar_canal as editar_canal_legacy,
        eliminar_canal as eliminar_canal_legacy
    )
    from backend.api.messages.routes import (
        enviar_mensaje as enviar_mensaje_legacy,
        obtener_mensajes as obtener_mensajes_legacy,
        editar_mensaje as editar_mensaje_legacy,
        eliminar_mensaje as eliminar_mensaje_legacy,
        actualizar_estado_mensaje as actualizar_estado_mensaje_legacy
    )
    
    # Rutas de compatibilidad
    app.add_url_rule('/', 'pagina_inicio', pagina_inicio, methods=['GET'])
    app.add_url_rule('/verificar', 'verificar_conexion', verificar_conexion, methods=['GET'])
    app.add_url_rule('/crear_canal', 'crear_canal', crear_canal_legacy, methods=['POST'])
    app.add_url_rule('/canales', 'listar_canales', listar_canales_legacy, methods=['GET'])
    app.add_url_rule('/canal/<nombre>', 'obtener_canal', obtener_canal_legacy, methods=['GET'])
    app.add_url_rule('/canal/<nombre>', 'editar_canal', editar_canal_legacy, methods=['PUT'])
    app.add_url_rule('/canal/<nombre>', 'eliminar_canal', eliminar_canal_legacy, methods=['DELETE'])
    app.add_url_rule('/enviar', 'enviar_mensaje', enviar_mensaje_legacy, methods=['POST'])
    app.add_url_rule('/mensajes/<canal>', 'obtener_mensajes', obtener_mensajes_legacy, methods=['GET'])
    app.add_url_rule('/mensaje/<mensaje_id>', 'editar_mensaje', editar_mensaje_legacy, methods=['PUT'])
    app.add_url_rule('/mensaje/<mensaje_id>', 'eliminar_mensaje', eliminar_mensaje_legacy, methods=['DELETE'])
    app.add_url_rule('/mensaje/<mensaje_id>/estado', 'actualizar_estado_mensaje', actualizar_estado_mensaje_legacy, methods=['PUT'])

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)