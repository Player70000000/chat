"""
Funciones para generación de reportes PDF
Sistema de reportes de moderadores y obreros
"""

import os
import logging
from datetime import datetime
from flask import jsonify, make_response, send_file
from bson import ObjectId
from io import BytesIO

# Importar ReportLab para generación de PDFs (comentado para testing local)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Importar funciones de base de datos
from .database_functions import get_db

# Configurar logging
logger = logging.getLogger(__name__)

# Log de ReportLab después de configurar logger
if not REPORTLAB_AVAILABLE:
    logger.warning("⚠️ ReportLab no disponible - generando archivos de texto en lugar de PDF")

def generar_reporte_moderadores():
    """
    Generar reporte PDF de moderadores
    Retorna: JSON con información del reporte generado
    """
    try:
        logger.info("🔄 Iniciando generación de reporte de moderadores")

        # 1. Obtener datos de moderadores desde la BD
        db = get_db()
        moderadores_collection = db.moderadores
        reportes_collection = db.reportes_moderadores

        # Consultar todos los moderadores activos
        moderadores = list(moderadores_collection.find({"activo": True}))
        total_moderadores = len(moderadores)

        logger.info(f"📊 Encontrados {total_moderadores} moderadores activos")

        if total_moderadores == 0:
            return jsonify({
                "success": False,
                "error": "No hay moderadores activos para generar reporte"
            }), 400

        # 2. Obtener número de reporte (auto-incrementable)
        ultimo_reporte = reportes_collection.find_one(
            {},
            sort=[("numero_reporte", -1)]
        )
        numero_reporte = 1 if not ultimo_reporte else ultimo_reporte["numero_reporte"] + 1

        # 3. Generar PDF
        fecha_actual = datetime.now()
        pdf_filename = f"reporte_moderadores_{numero_reporte}.pdf"
        pdf_path = os.path.join("static", "reportes", pdf_filename)

        # Crear directorio si no existe
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Verificar si ReportLab está disponible
        if not REPORTLAB_AVAILABLE:
            # Modo testing - crear archivo de texto simulando PDF
            pdf_success = _crear_texto_simulado(
                pdf_path.replace('.pdf', '.txt'),
                moderadores,
                numero_reporte,
                fecha_actual,
                total_moderadores
            )
            pdf_filename = pdf_filename.replace('.pdf', '.txt')
        else:
            # Generar contenido del PDF real
            pdf_success = _crear_pdf_moderadores(
                pdf_path,
                moderadores,
                numero_reporte,
                fecha_actual,
                total_moderadores
            )

        if not pdf_success:
            return jsonify({
                "success": False,
                "error": "Error generando reporte"
            }), 500

        # 4. Guardar registro en BD
        reporte_data = {
            "numero_reporte": numero_reporte,
            "fecha_creacion": fecha_actual,
            "total_moderadores": total_moderadores,
            "pdf_path": pdf_path,
            "pdf_filename": pdf_filename,
            "estado": "generado",
            "tipo": "moderadores"
        }

        resultado = reportes_collection.insert_one(reporte_data)
        reporte_id = str(resultado.inserted_id)

        logger.info(f"✅ Reporte generado exitosamente: N°{numero_reporte}")

        # 5. Retornar información del reporte
        return jsonify({
            "success": True,
            "reporte": {
                "id": reporte_id,
                "numero_reporte": numero_reporte,
                "fecha_creacion": fecha_actual.isoformat(),
                "total_moderadores": total_moderadores,
                "pdf_url": f"/static/reportes/{pdf_filename}",
                "estado": "generado"
            }
        })

    except Exception as e:
        logger.error(f"❌ Error generando reporte de moderadores: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500

def _crear_texto_simulado(txt_path, moderadores, numero_reporte, fecha_creacion, total_moderadores):
    """
    Crear archivo de texto simulando PDF para testing local
    """
    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("CORPOTACHIRA Reportes\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Reportes de moderadores N°{numero_reporte}\n\n")
            f.write(f"Moderadores existentes: {total_moderadores}\n\n")
            f.write("Detalles de los moderadores:\n")
            f.write("-" * 30 + "\n\n")

            for i, moderador in enumerate(moderadores, 1):
                fecha_mod = moderador.get('fecha_creacion', '')
                if isinstance(fecha_mod, datetime):
                    fecha_formatted = fecha_mod.strftime("%a, %d/%m/%Y %H:%M")
                else:
                    fecha_formatted = "No disponible"

                f.write(f"{i}.) Nombre: {moderador.get('nombre', 'No ingresado')}\n")
                f.write(f"{i}.) Apellido: {moderador.get('apellidos', 'No ingresado')}\n")
                f.write(f"{i}.) Cedula: {moderador.get('cedula', 'No ingresado')}\n")
                f.write(f"{i}.) Correo: {moderador.get('email', 'No ingresado')}\n")
                f.write(f"{i}.) Telefono: {moderador.get('telefono', 'No ingresado')}\n")
                f.write(f"{i}.) Talla de ropa: {moderador.get('talla_ropa', 'No ingresado')}\n")
                f.write(f"{i}.) Talla de zapatos: {moderador.get('talla_zapatos', 'No ingresado')}\n")
                f.write(f"{i}.) Fecha de creacion: {fecha_formatted}\n\n")

            fecha_reporte = fecha_creacion.strftime("%d/%m/%Y %H:%M")
            f.write(f"\nFecha de creación del reporte: {fecha_reporte}\n")

        logger.info(f"📄 Archivo de texto simulado creado: {txt_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creando archivo simulado: {str(e)}")
        return False

def _crear_pdf_moderadores(pdf_path, moderadores, numero_reporte, fecha_creacion, total_moderadores):
    """
    Crear PDF con formato específico de moderadores
    """
    if not REPORTLAB_AVAILABLE:
        return False

    try:
        # Crear documento PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_LEFT
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT
        )

        # Contenido del PDF
        story = []

        # Título principal
        story.append(Paragraph("CORPOTACHIRA Reportes", title_style))
        story.append(Spacer(1, 12))

        # Subtítulo con número de reporte
        story.append(Paragraph(f"Reportes de moderadores N°{numero_reporte}", subtitle_style))
        story.append(Spacer(1, 12))

        # Resumen
        story.append(Paragraph(f"Moderadores existentes: {total_moderadores}", normal_style))
        story.append(Spacer(1, 12))

        # Detalles de moderadores
        story.append(Paragraph("Detalles de los moderadores:", subtitle_style))
        story.append(Spacer(1, 12))

        # Iterar sobre cada moderador
        for i, moderador in enumerate(moderadores, 1):
            # Formatear fecha de creación
            fecha_mod = moderador.get('fecha_creacion', '')
            if isinstance(fecha_mod, datetime):
                fecha_formatted = fecha_mod.strftime("%a, %d/%m/%Y %H:%M")
            else:
                fecha_formatted = "No disponible"

            # Detalles del moderador
            detalles = [
                f"{i}.) Nombre: {moderador.get('nombre', 'No ingresado')}",
                f"{i}.) Apellido: {moderador.get('apellidos', 'No ingresado')}",
                f"{i}.) Cedula: {moderador.get('cedula', 'No ingresado')}",
                f"{i}.) Correo: {moderador.get('email', 'No ingresado')}",
                f"{i}.) Telefono: {moderador.get('telefono', 'No ingresado')}",
                f"{i}.) Talla de ropa: {moderador.get('talla_ropa', 'No ingresado')}",
                f"{i}.) Talla de zapatos: {moderador.get('talla_zapatos', 'No ingresado')}",
                f"{i}.) Fecha de creacion: {fecha_formatted}"
            ]

            # Agregar cada detalle
            for detalle in detalles:
                story.append(Paragraph(detalle, normal_style))

            # Espacio entre moderadores
            story.append(Spacer(1, 12))

        # Fecha de creación del reporte (esquina inferior derecha)
        story.append(Spacer(1, 50))
        fecha_reporte = fecha_creacion.strftime("%d/%m/%Y %H:%M")
        fecha_style = ParagraphStyle(
            'FechaReporte',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Fecha de creación del reporte: {fecha_reporte}", fecha_style))

        # Construir PDF
        doc.build(story)

        logger.info(f"📄 PDF creado exitosamente: {pdf_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creando PDF: {str(e)}")
        return False

def listar_reportes_moderadores():
    """
    Listar todos los reportes de moderadores generados
    """
    try:
        db = get_db()
        reportes_collection = db.reportes_moderadores

        # Obtener reportes ordenados por fecha (más recientes primero)
        reportes = list(reportes_collection.find(
            {"tipo": "moderadores"},
            sort=[("fecha_creacion", -1)]
        ))

        # Formatear datos para el frontend
        reportes_formateados = []
        for reporte in reportes:
            reportes_formateados.append({
                "id": str(reporte["_id"]),
                "numero_reporte": reporte["numero_reporte"],
                "fecha_creacion": reporte["fecha_creacion"].isoformat(),
                "total_moderadores": reporte["total_moderadores"],
                "pdf_url": f"/static/reportes/{reporte['pdf_filename']}",
                "estado": reporte.get("estado", "generado")
            })

        return jsonify({
            "success": True,
            "reportes": reportes_formateados,
            "total": len(reportes_formateados)
        })

    except Exception as e:
        logger.error(f"❌ Error listando reportes: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500

def generar_reporte_obreros():
    """
    Generar reporte PDF de obreros
    Retorna: JSON con información del reporte generado
    """
    try:
        logger.info("🔄 Iniciando generación de reporte de obreros")

        # 1. Obtener datos de obreros desde la BD
        db = get_db()
        obreros_collection = db.obreros
        reportes_collection = db.reportes_obreros

        # Consultar todos los obreros activos
        obreros = list(obreros_collection.find({"activo": True}))
        total_obreros = len(obreros)

        logger.info(f"📊 Encontrados {total_obreros} obreros activos")

        if total_obreros == 0:
            return jsonify({
                "success": False,
                "error": "No hay obreros activos para generar reporte"
            }), 400

        # 2. Obtener número de reporte (auto-incrementable)
        ultimo_reporte = reportes_collection.find_one(
            {},
            sort=[("numero_reporte", -1)]
        )
        numero_reporte = 1 if not ultimo_reporte else ultimo_reporte["numero_reporte"] + 1

        # 3. Generar PDF
        fecha_actual = datetime.now()
        pdf_filename = f"reporte_obreros_{numero_reporte}.pdf"
        pdf_path = os.path.join("static", "reportes", pdf_filename)

        # Crear directorio si no existe
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Verificar si ReportLab está disponible
        if not REPORTLAB_AVAILABLE:
            # Modo testing - crear archivo de texto simulando PDF
            pdf_success = _crear_texto_simulado_obreros(
                pdf_path.replace('.pdf', '.txt'),
                obreros,
                numero_reporte,
                fecha_actual,
                total_obreros
            )
            pdf_filename = pdf_filename.replace('.pdf', '.txt')
        else:
            # Generar contenido del PDF real
            pdf_success = _crear_pdf_obreros(
                pdf_path,
                obreros,
                numero_reporte,
                fecha_actual,
                total_obreros
            )

        if not pdf_success:
            return jsonify({
                "success": False,
                "error": "Error generando reporte"
            }), 500

        # 4. Guardar registro en BD
        reporte_data = {
            "numero_reporte": numero_reporte,
            "fecha_creacion": fecha_actual,
            "total_obreros": total_obreros,
            "pdf_path": pdf_path,
            "pdf_filename": pdf_filename,
            "estado": "generado",
            "tipo": "obreros"
        }

        resultado = reportes_collection.insert_one(reporte_data)
        reporte_id = str(resultado.inserted_id)

        logger.info(f"✅ Reporte generado exitosamente: N°{numero_reporte}")

        # 5. Retornar información del reporte
        return jsonify({
            "success": True,
            "reporte": {
                "id": reporte_id,
                "numero_reporte": numero_reporte,
                "fecha_creacion": fecha_actual.isoformat(),
                "total_obreros": total_obreros,
                "pdf_url": f"/static/reportes/{pdf_filename}",
                "estado": "generado"
            }
        })

    except Exception as e:
        logger.error(f"❌ Error generando reporte de obreros: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500

def _crear_texto_simulado_obreros(txt_path, obreros, numero_reporte, fecha_creacion, total_obreros):
    """
    Crear archivo de texto simulando PDF para testing local (obreros)
    """
    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("CORPOTACHIRA Reportes\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Reportes de obreros N°{numero_reporte}\n\n")
            f.write(f"Obreros existentes: {total_obreros}\n\n")
            f.write("Detalles de los obreros:\n")
            f.write("-" * 30 + "\n\n")

            for i, obrero in enumerate(obreros, 1):
                fecha_ob = obrero.get('fecha_creacion', '')
                if isinstance(fecha_ob, datetime):
                    fecha_formatted = fecha_ob.strftime("%a, %d/%m/%Y %H:%M")
                else:
                    fecha_formatted = "No disponible"

                f.write(f"{i}.) Nombre: {obrero.get('nombre', 'No ingresado')}\n")
                f.write(f"{i}.) Apellido: {obrero.get('apellidos', 'No ingresado')}\n")
                f.write(f"{i}.) Cedula: {obrero.get('cedula', 'No ingresado')}\n")
                f.write(f"{i}.) Correo: {obrero.get('email', 'No ingresado')}\n")
                f.write(f"{i}.) Telefono: {obrero.get('telefono', 'No ingresado')}\n")
                f.write(f"{i}.) Talla de ropa: {obrero.get('talla_ropa', 'No ingresado')}\n")
                f.write(f"{i}.) Talla de zapatos: {obrero.get('talla_zapatos', 'No ingresado')}\n")
                f.write(f"{i}.) Fecha de creacion: {fecha_formatted}\n\n")

            fecha_reporte = fecha_creacion.strftime("%d/%m/%Y %H:%M")
            f.write(f"\nFecha de creación del reporte: {fecha_reporte}\n")

        logger.info(f"📄 Archivo de texto simulado creado: {txt_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creando archivo simulado: {str(e)}")
        return False

def _crear_pdf_obreros(pdf_path, obreros, numero_reporte, fecha_creacion, total_obreros):
    """
    Crear PDF con formato específico de obreros
    """
    if not REPORTLAB_AVAILABLE:
        return False

    try:
        # Crear documento PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_LEFT
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT
        )

        # Contenido del PDF
        story = []

        # Título principal
        story.append(Paragraph("CORPOTACHIRA Reportes", title_style))
        story.append(Spacer(1, 12))

        # Subtítulo con número de reporte
        story.append(Paragraph(f"Reportes de obreros N°{numero_reporte}", subtitle_style))
        story.append(Spacer(1, 12))

        # Resumen
        story.append(Paragraph(f"Obreros existentes: {total_obreros}", normal_style))
        story.append(Spacer(1, 12))

        # Detalles de obreros
        story.append(Paragraph("Detalles de los obreros:", subtitle_style))
        story.append(Spacer(1, 12))

        # Iterar sobre cada obrero
        for i, obrero in enumerate(obreros, 1):
            # Formatear fecha de creación
            fecha_ob = obrero.get('fecha_creacion', '')
            if isinstance(fecha_ob, datetime):
                fecha_formatted = fecha_ob.strftime("%a, %d/%m/%Y %H:%M")
            else:
                fecha_formatted = "No disponible"

            # Detalles del obrero
            detalles = [
                f"{i}.) Nombre: {obrero.get('nombre', 'No ingresado')}",
                f"{i}.) Apellido: {obrero.get('apellidos', 'No ingresado')}",
                f"{i}.) Cedula: {obrero.get('cedula', 'No ingresado')}",
                f"{i}.) Correo: {obrero.get('email', 'No ingresado')}",
                f"{i}.) Telefono: {obrero.get('telefono', 'No ingresado')}",
                f"{i}.) Talla de ropa: {obrero.get('talla_ropa', 'No ingresado')}",
                f"{i}.) Talla de zapatos: {obrero.get('talla_zapatos', 'No ingresado')}",
                f"{i}.) Fecha de creacion: {fecha_formatted}"
            ]

            # Agregar cada detalle
            for detalle in detalles:
                story.append(Paragraph(detalle, normal_style))

            # Espacio entre obreros
            story.append(Spacer(1, 12))

        # Fecha de creación del reporte (esquina inferior derecha)
        story.append(Spacer(1, 50))
        fecha_reporte = fecha_creacion.strftime("%d/%m/%Y %H:%M")
        fecha_style = ParagraphStyle(
            'FechaReporte',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Fecha de creación del reporte: {fecha_reporte}", fecha_style))

        # Construir PDF
        doc.build(story)

        logger.info(f"📄 PDF creado exitosamente: {pdf_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creando PDF: {str(e)}")
        return False

def listar_reportes_obreros():
    """
    Listar todos los reportes de obreros generados
    """
    try:
        db = get_db()
        reportes_collection = db.reportes_obreros

        # Obtener reportes ordenados por fecha (más recientes primero)
        reportes = list(reportes_collection.find(
            {"tipo": "obreros"},
            sort=[("fecha_creacion", -1)]
        ))

        # Formatear datos para el frontend
        reportes_formateados = []
        for reporte in reportes:
            reportes_formateados.append({
                "id": str(reporte["_id"]),
                "numero_reporte": reporte["numero_reporte"],
                "fecha_creacion": reporte["fecha_creacion"].isoformat(),
                "total_obreros": reporte["total_obreros"],
                "pdf_url": f"/static/reportes/{reporte['pdf_filename']}",
                "estado": reporte.get("estado", "generado")
            })

        return jsonify({
            "success": True,
            "reportes": reportes_formateados,
            "total": len(reportes_formateados)
        })

    except Exception as e:
        logger.error(f"❌ Error listando reportes: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500