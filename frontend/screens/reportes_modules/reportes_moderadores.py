from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivy.clock import Clock

from .api_client import ReportesAPIClient
from .report_components import (
    StatsCard,
    LoadingIndicator,
    ErrorDisplay,
    SummarySection,
    DataTable,
    ChartCard,
    ExportDialog
)

# Importar componentes de lista
from kivymd.uix.list import ThreeLineListItem


class ReporteListItem(ThreeLineListItem):
    """Item de lista para mostrar reportes generados"""

    def __init__(self, reporte_data, on_click_callback, **kwargs):
        super().__init__(**kwargs)

        # Datos del reporte
        self.reporte_data = reporte_data
        self.on_click_callback = on_click_callback

        # Formatear información del reporte
        numero_reporte = reporte_data.get('numero_reporte', 'N/A')
        total_moderadores = reporte_data.get('total_moderadores', 0)
        fecha_creacion = reporte_data.get('fecha_creacion', '')

        # Formatear fecha para mostrar
        try:
            from datetime import datetime
            if fecha_creacion:
                # Parsear fecha ISO format
                fecha_obj = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                fecha_formatted = fecha_obj.strftime("%d/%m/%Y %H:%M")
            else:
                fecha_formatted = "Fecha no disponible"
        except:
            fecha_formatted = "Fecha no disponible"

        # Configurar textos del item
        self.text = f"📄 Reporte (Moderadores) N°{numero_reporte}"
        self.secondary_text = f"Creado: {fecha_formatted}"
        self.tertiary_text = f"📊 {total_moderadores} moderadores incluidos"

        # Configurar callback de click
        self.on_release = self.abrir_reporte

    def abrir_reporte(self):
        """Abrir el reporte al hacer clic"""
        if self.on_click_callback:
            self.on_click_callback(self.reporte_data)


class ReportesModeradoresManager:
    """Gestor de reportes específicos para moderadores"""

    def __init__(self, parent_layout):
        self.parent_layout = parent_layout
        self.api_client = ReportesAPIClient()
        self.current_layout = None

    def mostrar_reportes_moderadores(self):
        """Mostrar pantalla principal de reportes de moderadores"""
        self.current_layout = MDBoxLayout(orientation="vertical", spacing="10dp")

        # Top bar
        top_bar = MDTopAppBar(
            title="👤 Reportes de Moderadores",
            left_action_items=[["arrow-left", lambda x: self._volver_menu_principal()]],
            right_action_items=[["refresh", lambda x: self._refrescar_datos()]]
        )

        # Scroll para el contenido
        self.content_scroll = MDScrollView()
        self.content_layout = MDBoxLayout(
            orientation="vertical",
            spacing="15dp",
            adaptive_height=True,
            padding="10dp"
        )

        self.content_scroll.add_widget(self.content_layout)
        self.current_layout.add_widget(top_bar)
        self.current_layout.add_widget(self.content_scroll)

        # Cargar datos iniciales
        self._cargar_resumen_moderadores()

        # Mostrar en el layout principal
        self.parent_layout.clear_widgets()
        self.parent_layout.add_widget(self.current_layout)

    def _cargar_resumen_moderadores(self):
        """Cargar resumen estadístico de moderadores"""
        self.content_layout.clear_widgets()

        # Ejecutar directamente sin Clock para debug
        self._procesar_datos_moderadores()

    def _procesar_datos_moderadores(self):
        """Procesar y mostrar datos de moderadores"""
        self.content_layout.clear_widgets()

        # Botón para generar nuevo reporte
        generar_button = MDRaisedButton(
            text="📊 GENERAR NUEVO REPORTE",
            md_bg_color=[0.2, 0.7, 0.3, 1],
            size_hint_y=None,
            height="50dp",
            on_release=lambda x: self._generar_nuevo_reporte()
        )

        # Título de lista
        lista_title = MDLabel(
            text="Lista de Reportes (Moderadores)",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )

        # Scroll y lista para reportes
        self.reportes_scroll = MDScrollView(
            size_hint_y=None,
            height="300dp"
        )
        self.reportes_list = MDList(adaptive_height=True)
        self.reportes_scroll.add_widget(self.reportes_list)

        # Agregar elementos al layout
        self.content_layout.add_widget(generar_button)
        self.content_layout.add_widget(lista_title)
        self.content_layout.add_widget(self.reportes_scroll)

        # Cargar reportes existentes
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)

    def _mostrar_resumen_principal(self, datos):
        """Mostrar resumen principal de moderadores"""
        resumen = datos.get('resumen', {})

        stats_principales = {
            "👤 Total de moderadores": resumen.get('total_moderadores', 0),
            "✅ Moderadores activos": resumen.get('moderadores_activos', 0),
            "❌ Moderadores inactivos": resumen.get('moderadores_inactivos', 0),
            "📅 Registrados este mes": resumen.get('registrados_mes', 0)
        }

        stats_card = StatsCard(
            titulo="📊 Resumen General de Moderadores",
            datos=stats_principales,
            color=(0.95, 0.95, 1, 1)
        )
        self.content_layout.add_widget(stats_card)

    def _mostrar_distribucion_tallas(self):
        """Mostrar distribución de tallas de ropa y zapatos"""
        # Tallas de ropa
        tallas_ropa_response = self.api_client.get_moderadores_por_talla_ropa()
        if tallas_ropa_response['success']:
            tallas_ropa = tallas_ropa_response['data'].get('tallas', [])
            if tallas_ropa:
                datos_grafico = [
                    {
                        'label': item.get('_id', 'Sin talla'),
                        'valor': item.get('cantidad', 0),
                        'porcentaje': (item.get('cantidad', 0) / sum(t.get('cantidad', 0) for t in tallas_ropa)) * 100
                    }
                    for item in tallas_ropa
                ]

                chart_ropa = ChartCard(
                    titulo="👕 Distribución por Talla de Ropa",
                    datos_grafico=datos_grafico
                )
                self.content_layout.add_widget(chart_ropa)

        # Tallas de zapatos
        tallas_zapatos_response = self.api_client.get_moderadores_por_talla_zapatos()
        if tallas_zapatos_response['success']:
            tallas_zapatos = tallas_zapatos_response['data'].get('tallas', [])
            if tallas_zapatos:
                datos_grafico = [
                    {
                        'label': f"Talla {item.get('_id', 'N/A')}",
                        'valor': item.get('cantidad', 0),
                        'porcentaje': (item.get('cantidad', 0) / sum(t.get('cantidad', 0) for t in tallas_zapatos)) * 100
                    }
                    for item in tallas_zapatos
                ]

                chart_zapatos = ChartCard(
                    titulo="👟 Distribución por Talla de Zapatos",
                    datos_grafico=datos_grafico
                )
                self.content_layout.add_widget(chart_zapatos)

    def _mostrar_estado_activacion(self):
        """Mostrar estadísticas de activación"""
        activacion_response = self.api_client.get_moderadores_activos_inactivos()
        if activacion_response['success']:
            datos = activacion_response['data'].get('estadisticas', {})

            stats_activacion = {
                "✅ Activos": datos.get('activos', 0),
                "❌ Inactivos": datos.get('inactivos', 0),
                "📊 Total": datos.get('total', 0),
                "📈 % Activos": f"{datos.get('porcentaje_activos', 0):.1f}%"
            }

            activacion_card = StatsCard(
                titulo="🔄 Estado de Activación",
                datos=stats_activacion,
                color=(1, 1, 0.95, 1)
            )
            self.content_layout.add_widget(activacion_card)

    def _mostrar_registros_recientes(self):
        """Mostrar moderadores registrados recientemente"""
        recientes_response = self.api_client.get_moderadores_recientes(30)
        if recientes_response['success']:
            moderadores_recientes = recientes_response['data'].get('moderadores_recientes', [])

            if moderadores_recientes:
                # Preparar datos para la tabla
                datos_tabla = []
                for moderador in moderadores_recientes[:10]:  # Mostrar solo los 10 más recientes
                    datos_tabla.append({
                        'nombre': moderador.get('nombre', 'N/A'),
                        'apellidos': moderador.get('apellidos', 'N/A'),
                        'cedula': moderador.get('cedula', 'N/A'),
                        'fecha_registro': moderador.get('fecha_creacion', 'N/A')[:10] if moderador.get('fecha_creacion') else 'N/A'
                    })

                tabla_recientes = DataTable(
                    titulo="📅 Moderadores Registrados Recientemente (últimos 30 días)",
                    headers=['Nombre', 'Apellidos', 'Cédula', 'Fecha Registro'],
                    datos=datos_tabla
                )
                self.content_layout.add_widget(tabla_recientes)

    def _mostrar_comparacion_con_obreros(self):
        """Mostrar comparación estadística con obreros"""
        try:
            # Obtener datos de obreros para comparar
            obreros_response = self.api_client.get_resumen_obreros()
            moderadores_response = self.api_client.get_resumen_moderadores()

            if obreros_response['success'] and moderadores_response['success']:
                obreros_data = obreros_response['data'].get('resumen', {})
                moderadores_data = moderadores_response['data'].get('resumen', {})

                total_obreros = obreros_data.get('total_obreros', 0)
                total_moderadores = moderadores_data.get('total_moderadores', 0)
                total_personal = total_obreros + total_moderadores

                if total_personal > 0:
                    porcentaje_obreros = (total_obreros / total_personal) * 100
                    porcentaje_moderadores = (total_moderadores / total_personal) * 100

                    stats_comparacion = {
                        "👷‍♂️ Total Obreros": f"{total_obreros} ({porcentaje_obreros:.1f}%)",
                        "👤 Total Moderadores": f"{total_moderadores} ({porcentaje_moderadores:.1f}%)",
                        "👥 Total Personal": total_personal,
                        "📊 Ratio M:O": f"1:{(total_obreros/total_moderadores):.1f}" if total_moderadores > 0 else "1:0"
                    }

                    comparacion_card = StatsCard(
                        titulo="⚖️ Comparación Moderadores vs Obreros",
                        datos=stats_comparacion,
                        color=(1, 0.95, 1, 1)
                    )
                    self.content_layout.add_widget(comparacion_card)

        except Exception as e:
            pass  # No mostrar error si falla la comparación

    def _mostrar_opciones_exportacion(self):
        """Mostrar botones de exportación"""
        export_layout = MDBoxLayout(orientation="vertical", spacing="10dp", adaptive_height=True)

        export_btn = MDRaisedButton(
            text="📋 Exportar Datos de Moderadores",
            size_hint_y=None,
            height="50dp",
            md_bg_color=(0.3, 0.3, 0.7, 1),
            on_release=lambda x: self._exportar_datos_moderadores()
        )
        export_layout.add_widget(export_btn)

        self.content_layout.add_widget(export_layout)

    def _exportar_datos_moderadores(self):
        """Manejar exportación de datos de moderadores"""
        try:
            response = self.api_client.exportar_moderadores()

            if response['success']:
                data = response['data']
                total_registros = data.get('total_registros', 0)

                dialog = MDDialog(
                    title="✅ Exportación Exitosa",
                    text=f"Se exportaron {total_registros} registros de moderadores.\n\nDatos disponibles en formato JSON.",
                    buttons=[
                        MDRaisedButton(
                            text="OK",
                            on_release=lambda x: dialog.dismiss()
                        )
                    ]
                )
                dialog.open()
            else:
                self._mostrar_error_dialog(f"Error en la exportación: {response['error']}")

        except Exception as e:
            self._mostrar_error_dialog(f"Error al exportar: {str(e)}")

    def _mostrar_error_api(self, mensaje):
        """Mostrar error de API sin borrar botón y lista"""
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel

        error_card = MDCard(
            elevation=1,
            padding="15dp",
            size_hint_y=None,
            height="100dp",
            md_bg_color=(1, 0.9, 0.9, 1)
        )

        error_layout = MDBoxLayout(orientation="vertical", spacing="10dp")

        error_label = MDLabel(
            text=f"⚠️ {mensaje}",
            theme_text_color="Error",
            font_size="14sp",
            size_hint_y=None,
            height="30dp"
        )

        retry_btn = MDRaisedButton(
            text="🔄 Reintentar Datos",
            size_hint_y=None,
            height="40dp",
            on_release=lambda x: self._refrescar_datos()
        )

        error_layout.add_widget(error_label)
        error_layout.add_widget(retry_btn)
        error_card.add_widget(error_layout)
        self.content_layout.add_widget(error_card)

    def _mostrar_error(self, mensaje):
        """Mostrar error en el layout principal (legacy)"""
        self.content_layout.clear_widgets()
        error_display = ErrorDisplay(
            mensaje=mensaje,
            on_retry=self._refrescar_datos
        )
        self.content_layout.add_widget(error_display)

    def _mostrar_error_dialog(self, mensaje):
        """Mostrar error en dialog"""
        dialog = MDDialog(
            title="❌ Error",
            text=mensaje,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def _refrescar_datos(self):
        """Refrescar todos los datos"""
        self._cargar_resumen_moderadores()


    def _generar_nuevo_reporte(self):
        """Generar nuevo reporte de moderadores consultando la API"""
        # Mostrar dialog de confirmación primero
        self.confirmation_dialog = MDDialog(
            title="📊 Generar Nuevo Reporte",
            text="¿Deseas generar un nuevo reporte de moderadores?\n\nEsto consultará todos los moderadores activos en la base de datos.",
            buttons=[
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: self.confirmation_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Generar",
                    md_bg_color=(0.2, 0.7, 0.3, 1),
                    on_release=lambda x: self._confirmar_generar_reporte()
                )
            ]
        )
        self.confirmation_dialog.open()

    def _confirmar_generar_reporte(self):
        """Confirmar y proceder con la generación del reporte"""
        self.confirmation_dialog.dismiss()

        # Mostrar dialog de progreso
        self.progress_dialog = MDDialog(
            title="🔄 Generando Reporte",
            text="Consultando base de datos y generando PDF...\nPor favor espera un momento.",
            auto_dismiss=False
        )
        self.progress_dialog.open()

        # Llamar a la API en segundo plano
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._llamar_api_generar(), 0.5)

    def _llamar_api_generar(self):
        """Llamar a la API para generar el reporte"""
        try:
            import requests
            response = requests.post(
                f"{self.api_client.base_url}/api/reports/moderadores/generar",
                timeout=30
            )

            self.progress_dialog.dismiss()

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    reporte_info = data.get('reporte', {})
                    self._mostrar_exito_generacion(reporte_info)
                    # Actualizar la lista de reportes
                    self._cargar_lista_reportes()
                else:
                    self._mostrar_error_generacion(data.get('error', 'Error desconocido'))
            else:
                self._mostrar_error_generacion(f"Error del servidor: {response.status_code}")

        except requests.exceptions.Timeout:
            self.progress_dialog.dismiss()
            self._mostrar_error_generacion("Tiempo de espera agotado. El reporte puede tardar unos minutos en generarse.")
        except Exception as e:
            self.progress_dialog.dismiss()
            self._mostrar_error_generacion(f"Error de conexión: {str(e)}")

    def _mostrar_exito_generacion(self, reporte_info):
        """Mostrar dialog de éxito con información del reporte"""
        numero_reporte = reporte_info.get('numero_reporte', 'N/A')
        total_moderadores = reporte_info.get('total_moderadores', 0)
        pdf_url = reporte_info.get('pdf_url', '')

        success_dialog = MDDialog(
            title="✅ Reporte Generado Exitosamente",
            text=f"Reporte N°{numero_reporte} creado con éxito\n\n📊 Moderadores incluidos: {total_moderadores}\n📄 PDF disponible para descargar\n\nEl reporte aparecerá en la lista a continuación.",
            buttons=[
                MDRaisedButton(
                    text="Ver PDF",
                    md_bg_color=(0.2, 0.6, 0.8, 1),
                    on_release=lambda x: self._abrir_pdf_reporte(pdf_url, success_dialog)
                ),
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: success_dialog.dismiss()
                )
            ]
        )
        success_dialog.open()

    def _mostrar_error_generacion(self, mensaje):
        """Mostrar dialog de error"""
        error_dialog = MDDialog(
            title="❌ Error Generando Reporte",
            text=f"No se pudo generar el reporte:\n\n{mensaje}\n\nPor favor intenta nuevamente.",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: error_dialog.dismiss()
                )
            ]
        )
        error_dialog.open()

    def _abrir_pdf_reporte(self, pdf_url, dialog):
        """Abrir PDF en el navegador"""
        dialog.dismiss()
        if pdf_url:
            import webbrowser
            full_url = f"{self.api_client.base_url}{pdf_url}"
            webbrowser.open(full_url)

    def _cargar_lista_reportes(self):
        """Cargar lista de reportes existentes desde la API"""
        try:
            import requests
            url = f"{self.api_client.base_url}/api/reports/moderadores/listar"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    reportes = data.get('reportes', [])
                    self._actualizar_lista_reportes(reportes)
                else:
                    self._mostrar_mensaje_lista("❌ Error cargando reportes")
            else:
                self._mostrar_mensaje_lista("❌ Error de conexión")

        except Exception as e:
            self._mostrar_mensaje_lista("⚠️ Sin conexión a servidor")

    def _actualizar_lista_reportes(self, reportes):
        """Actualizar la lista visual con los reportes"""
        from kivymd.uix.list import OneLineListItem

        # Limpiar lista actual
        self.reportes_list.clear_widgets()

        if not reportes:
            # Mostrar mensaje si no hay reportes
            simple_item = OneLineListItem(text="📝 No hay reportes generados")
            self.reportes_list.add_widget(simple_item)
            return

        # Invertir lista para mostrar más antiguos primero (orden ascendente)
        reportes_ordenados = list(reversed(reportes))

        # Agregar reportes a la lista
        for reporte in reportes_ordenados:
            numero = reporte.get('numero_reporte', 'N/A')
            fecha_creacion = reporte.get('fecha_creacion', '')

            # Formatear fecha para mostrar (solo fecha, sin hora)
            try:
                from datetime import datetime
                if fecha_creacion:
                    fecha_obj = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                    fecha_formatted = fecha_obj.strftime("%d/%m/%Y")
                else:
                    fecha_formatted = "Sin fecha"
            except:
                fecha_formatted = "Sin fecha"

            # Crear item con formato simplificado y limpio
            item_text = f"Reporte N°{numero} - {fecha_formatted}"
            simple_item = OneLineListItem(text=item_text)

            # Configurar callback para abrir PDF
            simple_item.on_release = lambda x=reporte: self._abrir_reporte_desde_lista(x)
            self.reportes_list.add_widget(simple_item)

    def _mostrar_mensaje_lista(self, mensaje):
        """Mostrar mensaje informativo en la lista"""
        from kivymd.uix.list import OneLineListItem

        mensaje_item = OneLineListItem(
            text=mensaje,
            theme_text_color="Secondary"
        )
        self.reportes_list.clear_widgets()
        self.reportes_list.add_widget(mensaje_item)

    def _abrir_reporte_desde_lista(self, reporte_data):
        """Abrir PDF del reporte seleccionado desde la lista"""
        pdf_url = reporte_data.get('pdf_url', '')
        if pdf_url:
            import webbrowser
            full_url = f"{self.api_client.base_url}{pdf_url}"
            webbrowser.open(full_url)

    def _volver_menu_principal(self):
        """Volver al menú principal de reportes"""
        if hasattr(self.parent_layout, 'mostrar_menu_reportes'):
            self.parent_layout.mostrar_menu_reportes()
        elif hasattr(self.parent_layout, 'parent') and hasattr(self.parent_layout.parent, 'mostrar_menu_reportes'):
            self.parent_layout.parent.mostrar_menu_reportes()