import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from pymongo.errors import WriteConcernError, OperationFailure

from ...config.database import get_db
from ...utils.validators import format_date

logger = logging.getLogger(__name__)
reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

# =============================================================================
# REPORTES DE PERSONAL
# =============================================================================

@reports_bp.route('/personal/resumen', methods=['GET'])
def resumen_personal():
    """Resumen general del personal"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Contar cuadrillas activas
        total_cuadrillas = db.cuadrillas.count_documents({"activa": True})
        
        # Contar obreros activos
        total_obreros = db.personal_obrero.count_documents({"activo": True})
        
        # Obtener actividades más comunes
        pipeline_actividades = [
            {"$match": {"activa": True}},
            {"$group": {"_id": "$actividad", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        actividades_comunes = list(db.cuadrillas.aggregate(pipeline_actividades))
        
        return jsonify({
            "resumen": {
                "total_cuadrillas": total_cuadrillas,
                "total_obreros": total_obreros,
                "actividades_comunes": [
                    {"actividad": a["_id"], "cantidad": a["count"]} 
                    for a in actividades_comunes
                ]
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error resumen personal: {e}")
        return jsonify({"error": str(e)}), 500

@reports_bp.route('/personal/cuadrillas-por-actividad', methods=['GET'])
def cuadrillas_por_actividad():
    """Reporte de cuadrillas agrupadas por actividad"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        pipeline = [
            {"$match": {"activa": True}},
            {"$group": {
                "_id": "$actividad",
                "cuadrillas": {
                    "$push": {
                        "numero": "$numero_cuadrilla",
                        "fecha_creada": "$creada"
                    }
                },
                "cantidad": {"$sum": 1}
            }},
            {"$sort": {"cantidad": -1}}
        ]
        
        resultado = list(db.cuadrillas.aggregate(pipeline))
        
        # Formatear fechas
        for actividad in resultado:
            for cuadrilla in actividad["cuadrillas"]:
                cuadrilla["fecha_creada"] = format_date(cuadrilla.get("fecha_creada"))
        
        return jsonify({
            "reporte": "Cuadrillas por Actividad",
            "actividades": resultado,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error reporte cuadrillas por actividad: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================
# REPORTES DE CHAT
# =============================================================================

@reports_bp.route('/chat/resumen', methods=['GET'])
def resumen_chat():
    """Resumen general del sistema de chat"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Contar canales activos
        total_canales = db.canales.count_documents({"activo": True})
        
        # Contar mensajes totales
        total_mensajes = db.mensajes.count_documents({})
        
        # Mensajes del último mes
        hace_mes = datetime.now() - timedelta(days=30)
        mensajes_mes = db.mensajes.count_documents({
            "timestamp": {"$gte": hace_mes}
        })
        
        # Usuarios más activos
        pipeline_usuarios = [
            {"$group": {"_id": "$usuario", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        usuarios_activos = list(db.mensajes.aggregate(pipeline_usuarios))
        
        return jsonify({
            "resumen": {
                "total_canales": total_canales,
                "total_mensajes": total_mensajes,
                "mensajes_ultimo_mes": mensajes_mes,
                "usuarios_activos": [
                    {"usuario": u["_id"], "mensajes": u["count"]} 
                    for u in usuarios_activos
                ]
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error resumen chat: {e}")
        return jsonify({"error": str(e)}), 500

@reports_bp.route('/chat/actividad-por-canal', methods=['GET'])
def actividad_por_canal():
    """Reporte de actividad de mensajes por canal"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        # Parámetros opcionales
        dias = request.args.get('dias', 30, type=int)
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": fecha_limite}}},
            {"$group": {
                "_id": "$canal",
                "total_mensajes": {"$sum": 1},
                "usuarios_unicos": {"$addToSet": "$usuario"},
                "ultimo_mensaje": {"$max": "$timestamp"}
            }},
            {"$addFields": {
                "usuarios_count": {"$size": "$usuarios_unicos"}
            }},
            {"$sort": {"total_mensajes": -1}}
        ]
        
        resultado = list(db.mensajes.aggregate(pipeline))
        
        # Formatear fechas y limpiar datos
        for canal in resultado:
            canal["ultimo_mensaje"] = format_date(canal["ultimo_mensaje"])
            canal["usuarios_unicos"] = canal["usuarios_count"]
            del canal["usuarios_count"]
        
        return jsonify({
            "reporte": f"Actividad por Canal (últimos {dias} días)",
            "canales": resultado,
            "periodo_dias": dias,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error reporte actividad por canal: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================
# REPORTES PERSONALIZADOS
# =============================================================================

@reports_bp.route('/personalizado/rango-fechas', methods=['POST'])
def reporte_rango_fechas():
    """Reporte personalizado por rango de fechas"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 400
        
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        # Validar fechas
        try:
            fecha_inicio = datetime.fromisoformat(datos.get('fecha_inicio', ''))
            fecha_fin = datetime.fromisoformat(datos.get('fecha_fin', ''))
        except (ValueError, TypeError):
            return jsonify({"error": "Formato de fecha inválido. Use ISO format (YYYY-MM-DD)"}), 400
        
        if fecha_inicio >= fecha_fin:
            return jsonify({"error": "La fecha de inicio debe ser anterior a la fecha de fin"}), 400
        
        # Tipo de reporte
        tipo = datos.get('tipo', 'mensajes')  # mensajes, cuadrillas, obreros
        
        if tipo == 'mensajes':
            resultado = db.mensajes.count_documents({
                "timestamp": {"$gte": fecha_inicio, "$lte": fecha_fin}
            })
            detalle = "mensajes enviados"
            
        elif tipo == 'cuadrillas':
            resultado = db.cuadrillas.count_documents({
                "creada": {"$gte": fecha_inicio, "$lte": fecha_fin}
            })
            detalle = "cuadrillas creadas"
            
        elif tipo == 'obreros':
            resultado = db.personal_obrero.count_documents({
                "registrado": {"$gte": fecha_inicio, "$lte": fecha_fin}
            })
            detalle = "obreros registrados"
            
        else:
            return jsonify({"error": "Tipo de reporte inválido"}), 400
        
        return jsonify({
            "reporte": f"Reporte personalizado - {detalle}",
            "tipo": tipo,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
            "resultado": resultado,
            "detalle": detalle,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error reporte personalizado: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================
# EXPORTACIÓN DE DATOS
# =============================================================================

@reports_bp.route('/exportar/<tipo>', methods=['GET'])
def exportar_datos(tipo):
    """Exportar datos en formato JSON"""
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Base de datos no disponible"}), 500
        
        if tipo == 'cuadrillas':
            datos = list(db.cuadrillas.find({}, {"_id": 0}))
            # Formatear fechas
            for item in datos:
                if 'creada' in item:
                    item['creada'] = format_date(item['creada'])
                if 'modificada' in item:
                    item['modificada'] = format_date(item['modificada'])
                    
        elif tipo == 'obreros':
            datos = list(db.personal_obrero.find({}, {"_id": 0}))
            # Formatear fechas
            for item in datos:
                if 'registrado' in item:
                    item['registrado'] = format_date(item['registrado'])
                    
        elif tipo == 'canales':
            datos = list(db.canales.find({}, {"_id": 0}))
            # Formatear fechas
            for item in datos:
                if 'creado' in item:
                    item['creado'] = format_date(item['creado'])
                if 'modificado' in item:
                    item['modificado'] = format_date(item['modificado'])
                    
        else:
            return jsonify({"error": "Tipo de exportación inválido"}), 400
        
        return jsonify({
            "tipo_exportacion": tipo,
            "total_registros": len(datos),
            "fecha_exportacion": datetime.now().isoformat(),
            "datos": datos
        })
        
    except Exception as e:
        logger.error(f"Error exportar {tipo}: {e}")
        return jsonify({"error": str(e)}), 500