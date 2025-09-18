"""
Módulo de Reportes Generales de Cuadrillas
Gestor modular para reportes de trabajo de cuadrillas con herramientas
"""

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.menu import MDDropdownMenu
from kivy.clock import Clock
from kivy.metrics import dp
import requests

from .api_client import ReportesAPIClient


class ReportesGeneralesManager:
    """Gestor de reportes generales de cuadrillas y trabajo"""

    def __init__(self, parent_layout):
        self.parent_layout = parent_layout
        self.api_client = ReportesAPIClient()
        self.current_layout = None

        # Data para la creación de reportes
        self.cuadrillas_data = []
        self.herramientas_utilizadas = []
        self.screen_stack = []  # Para navegación entre pantallas

        # Variables para cuadrilla seleccionada
        self.selected_cuadrilla_data = None

    def mostrar_reportes_generales(self):
        """Mostrar pantalla principal de reportes generales"""
        self.current_layout = MDBoxLayout(orientation="vertical", spacing="10dp")

        # Top bar
        top_bar = MDTopAppBar(
            title="📋 Reportes Generales",
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
        self._cargar_pantalla_principal()

        # Mostrar en el layout principal
        self.parent_layout.clear_widgets()
        self.parent_layout.add_widget(self.current_layout)

    def _cargar_pantalla_principal(self):
        """Cargar pantalla principal con botón generar y lista de reportes"""
        self.content_layout.clear_widgets()

        # Botón para generar nuevo reporte
        generar_button = MDRaisedButton(
            text="📊 GENERAR NUEVO REPORTE",
            md_bg_color=[0.2, 0.7, 0.3, 1],
            size_hint_y=None,
            height="50dp",
            on_release=lambda x: self._abrir_pantalla_creacion()
        )

        # Título de lista
        lista_title = MDLabel(
            text="Lista de Reportes Generales",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )

        # Scroll y lista para reportes (patrón exitoso)
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
        Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)

    def _cargar_lista_reportes(self):
        """Cargar lista de reportes generales existentes"""
        try:
            response = requests.get(
                f"{self.api_client.base_url}/api/reports/generales/listar",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    reportes = data.get('reportes', [])
                    self._mostrar_lista_reportes(reportes)
                else:
                    self._mostrar_error_lista(f"Error: {data.get('error', 'Error desconocido')}")
            else:
                self._mostrar_error_lista(f"Error HTTP {response.status_code}")
        except Exception as e:
            self._mostrar_error_lista(f"Error de conexión: {str(e)}")

    def _mostrar_lista_reportes(self, reportes):
        """Mostrar lista de reportes usando patrón exitoso (OneLineListItem)"""
        self.reportes_list.clear_widgets()

        if not reportes:
            no_data_label = MDLabel(
                text="No hay reportes generales disponibles",
                theme_text_color="Hint",
                halign="center",
                size_hint_y=None,
                height="50dp"
            )
            self.reportes_list.add_widget(no_data_label)
            return

        # Ordenar por número de reporte ascendente (patrón exitoso)
        reportes_ordenados = list(reversed(reportes))

        for reporte in reportes_ordenados:
            # Formatear fecha
            fecha_creacion = reporte.get('fecha_creacion', '')
            try:
                from datetime import datetime
                if fecha_creacion:
                    fecha_obj = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                    fecha_formatted = fecha_obj.strftime("%d/%m/%Y")
                else:
                    fecha_formatted = "Sin fecha"
            except:
                fecha_formatted = "Sin fecha"

            # Usar OneLineListItem simple (patrón exitoso)
            numero_reporte = reporte.get('numero_reporte', 'N/A')
            item_text = f"Reporte N°{numero_reporte} - {fecha_formatted}"

            simple_item = OneLineListItem(
                text=item_text,
                on_release=lambda x, r=reporte: self._abrir_reporte_desde_lista(r)
            )
            self.reportes_list.add_widget(simple_item)

    def _mostrar_error_lista(self, mensaje):
        """Mostrar error en la lista de reportes"""
        self.reportes_list.clear_widgets()
        error_label = MDLabel(
            text=f"❌ {mensaje}",
            theme_text_color="Error",
            halign="center",
            size_hint_y=None,
            height="50dp"
        )
        self.reportes_list.add_widget(error_label)

    def _abrir_reporte_desde_lista(self, reporte_data):
        """Abrir reporte desde la lista (abrir PDF)"""
        try:
            pdf_url = reporte_data.get('pdf_url', '')
            if pdf_url:
                # Abrir PDF en navegador
                import webbrowser
                full_url = f"{self.api_client.base_url}{pdf_url}"
                webbrowser.open(full_url)
            else:
                self._mostrar_error_dialog("No se encontró el archivo PDF del reporte")
        except Exception as e:
            self._mostrar_error_dialog(f"Error al abrir reporte: {str(e)}")

    def _abrir_pantalla_creacion(self):
        """Abrir pantalla completa de creación de reporte"""
        # Guardar pantalla actual en stack
        self.screen_stack.append(self.current_layout)

        # Crear nueva pantalla completa
        self._crear_pantalla_creacion()

    def _crear_pantalla_creacion(self):
        """Crear pantalla completa para nuevo reporte"""
        # Layout principal de la pantalla
        self.creation_layout = MDBoxLayout(orientation="vertical", spacing="10dp")

        # Top bar para pantalla de creación
        creation_top_bar = MDTopAppBar(
            title="📝 Crear Reporte General",
            left_action_items=[["arrow-left", lambda x: self._volver_pantalla_principal()]],
            right_action_items=[["check", lambda x: self._validar_y_guardar_reporte()]]
        )

        # Scroll para formulario
        form_scroll = MDScrollView()
        self.form_layout = MDBoxLayout(
            orientation="vertical",
            spacing="20dp",
            adaptive_height=True,
            padding="15dp"
        )

        form_scroll.add_widget(self.form_layout)
        self.creation_layout.add_widget(creation_top_bar)
        self.creation_layout.add_widget(form_scroll)

        # Resetear variables de selección
        self.selected_cuadrilla_data = None

        # Crear campos del formulario
        self._crear_campos_formulario()

        # Cargar datos de cuadrillas
        self._cargar_cuadrillas_data()

        # Mostrar pantalla de creación
        self.parent_layout.clear_widgets()
        self.parent_layout.add_widget(self.creation_layout)

    def _crear_campos_formulario(self):
        """Crear todos los campos del formulario"""
        self.form_layout.clear_widgets()

        # 1. DROPDOWN DE CUADRILLA
        cuadrilla_label = MDLabel(
            text="🏗️ Cuadrilla:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(cuadrilla_label)

        self.cuadrilla_field = MDRaisedButton(
            text="Seleccionar Cuadrilla *",
            md_bg_color=[0.95, 0.95, 0.95, 1],  # Gris claro como campo
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp",
            on_release=self._mostrar_selector_cuadrilla
        )
        self.form_layout.add_widget(self.cuadrilla_field)

        # 2. CAMPO ACTIVIDAD (Solo lectura)
        actividad_label = MDLabel(
            text="⚡ Actividad:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(actividad_label)

        self.actividad_field = MDTextField(
            hint_text="Actividad se carga automáticamente...",
            readonly=True,
            size_hint_y=None,
            height="50dp"
        )
        self.form_layout.add_widget(self.actividad_field)

        # 3. MUNICIPIO
        municipio_label = MDLabel(
            text="🏘️ Municipio:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(municipio_label)

        self.municipio_field = MDTextField(
            hint_text="Escribir municipio...",
            size_hint_y=None,
            height="50dp",
            on_text=self._validar_municipio
        )
        self.form_layout.add_widget(self.municipio_field)

        # 4. DISTANCIA
        distancia_label = MDLabel(
            text="📏 Distancia (metros):",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(distancia_label)

        self.distancia_field = MDTextField(
            hint_text="Distancia en metros...",
            input_filter="int",
            size_hint_y=None,
            height="50dp",
            on_text=self._validar_distancia
        )
        self.form_layout.add_widget(self.distancia_field)

        # 5. HERRAMIENTAS UTILIZADAS (Dinámico)
        herramientas_label = MDLabel(
            text="🔨 Herramientas Utilizadas:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(herramientas_label)

        # Container para herramientas dinámicas
        self.herramientas_container = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            adaptive_height=True
        )
        self.form_layout.add_widget(self.herramientas_container)

        # Inicializar con una herramienta
        self.herramientas_utilizadas = []
        self._agregar_herramienta_inicial()

        # Botón agregar herramienta
        add_herramienta_btn = MDRaisedButton(
            text="➕ Agregar Herramienta",
            size_hint_y=None,
            height="40dp",
            md_bg_color=(0.3, 0.7, 0.3, 1),
            on_release=self._agregar_nueva_herramienta
        )
        self.form_layout.add_widget(add_herramienta_btn)

        # 6. DETALLES ADICIONALES
        detalles_label = MDLabel(
            text="📝 Detalles Adicionales:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(detalles_label)

        self.detalles_field = MDTextField(
            hint_text="Información adicional del trabajo...",
            multiline=True,
            size_hint_y=None,
            height="100dp"
        )
        self.form_layout.add_widget(self.detalles_field)

    def _cargar_cuadrillas_data(self):
        """Cargar datos de cuadrillas desde la API"""
        try:
            url = f"{self.api_client.base_url}/api/personnel/cuadrillas/"
            print(f"🔗 Cargando cuadrillas desde: {url}")

            response = requests.get(url, timeout=10)
            print(f"📡 Status code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📊 Data recibida: {data}")
                if data.get('success'):
                    cuadrillas = data.get('cuadrillas', [])
                    print(f"✅ Cuadrillas encontradas: {len(cuadrillas)}")
                    for i, c in enumerate(cuadrillas):
                        print(f"  {i+1}. {c.get('numero_cuadrilla', 'N/A')}")
                    self.cuadrillas_data = cuadrillas
                else:
                    print(f"❌ API retornó success=False: {data.get('error', 'Sin error')}")
                    self.cuadrillas_data = []
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                self.cuadrillas_data = []
        except Exception as e:
            self.cuadrillas_data = []
            print(f"💥 Error cargando cuadrillas: {str(e)}")

    def _mostrar_selector_cuadrilla(self, instance):
        """Mostrar dropdown de cuadrillas cuando se hace clic en el botón"""
        print(f"🎯 Selector cuadrilla clicked - Cuadrillas disponibles: {len(self.cuadrillas_data)}")

        # Si no hay cuadrillas cargadas, cargar antes de mostrar
        if not self.cuadrillas_data:
            print(f"⏳ Cuadrillas no cargadas, cargando ahora...")
            self._cargar_cuadrillas_data()

        if self.cuadrillas_data:
            print(f"📋 Listando cuadrillas disponibles:")
            for i, c in enumerate(self.cuadrillas_data):
                print(f"  {i+1}. {c.get('numero_cuadrilla', 'N/A')} - {c.get('actividad', 'Sin actividad')}")

            # Crear lista de items para el dropdown
            menu_items = []
            for cuadrilla in self.cuadrillas_data:
                numero = cuadrilla.get('numero_cuadrilla', 'N/A')
                menu_items.append({
                    "text": numero,
                    "on_release": lambda x=None, cuad=cuadrilla, menu=None: self._on_cuadrilla_selected_with_close(cuad, menu)
                })

            print(f"📝 Items del dropdown: {len(menu_items)}")

            # Crear y mostrar dropdown
            self.cuadrilla_dropdown = MDDropdownMenu(
                caller=instance,
                items=menu_items,
                width_mult=2,  # Reducir ancho para que no se salga
                max_height="200dp",
                position="auto"  # Posición automática mejor
            )

            # Actualizar referencias del menu en los items
            for i, item in enumerate(menu_items):
                item["on_release"] = lambda x=None, cuad=self.cuadrillas_data[i]: self._on_cuadrilla_selected_with_close(cuad, self.cuadrilla_dropdown)

            self.cuadrilla_dropdown.open()
        else:
            print(f"❌ Aún no hay cuadrillas después de recargar")
            self._mostrar_error_dialog("Error cargando cuadrillas. Verifica tu conexión.")


    def _on_cuadrilla_selected_with_close(self, cuadrilla_data, dropdown_menu):
        """Callback cuando se selecciona una cuadrilla del dropdown con cierre automático"""
        print(f"✅ Cuadrilla seleccionada: {cuadrilla_data.get('numero_cuadrilla', 'N/A')}")

        # Cerrar dropdown primero
        if dropdown_menu:
            dropdown_menu.dismiss()

        numero = cuadrilla_data.get('numero_cuadrilla', 'N/A')
        actividad = cuadrilla_data.get('actividad', 'Sin actividad')

        # Guardar data de cuadrilla seleccionada
        self.selected_cuadrilla_data = cuadrilla_data

        # Actualizar botón de cuadrilla
        self.cuadrilla_field.text = f"Cuadrilla: {numero}"

        # Actualizar campo de actividad
        self.actividad_field.text = actividad

        # Limpiar herramientas para nuevas
        self._actualizar_herramientas_perdidas_dañadas()

    def _on_cuadrilla_selected(self, cuadrilla_data):
        """Callback cuando se selecciona una cuadrilla del dropdown (legacy)"""
        numero = cuadrilla_data.get('numero_cuadrilla', 'N/A')
        actividad = cuadrilla_data.get('actividad', 'Sin actividad')

        # Guardar data de cuadrilla seleccionada
        self.selected_cuadrilla_data = cuadrilla_data

        # Actualizar botón de cuadrilla
        self.cuadrilla_field.text = f"Cuadrilla: {numero}"

        # Actualizar campo de actividad
        self.actividad_field.text = actividad

        # Limpiar herramientas para nuevas
        self._actualizar_herramientas_perdidas_dañadas()

    def _validar_municipio(self, instance, text):
        """Validar que el municipio solo contenga letras y espacios"""
        # Permitir solo letras, espacios y acentos
        import re
        patron = re.compile(r'^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]*$')

        if not patron.match(text):
            # Remover caracteres inválidos
            texto_limpio = re.sub(r'[^a-zA-ZñÑáéíóúÁÉÍÓÚ\s]', '', text)
            instance.text = texto_limpio

    def _validar_distancia(self, instance, text):
        """Validar que la distancia sea solo números positivos"""
        if text and not text.isdigit():
            # Remover caracteres no numéricos
            texto_limpio = ''.join(filter(str.isdigit, text))
            instance.text = texto_limpio

    def _agregar_herramienta_inicial(self):
        """Agregar la primera herramienta (mínimo 1 obligatoria)"""
        self._agregar_herramienta_widget()

    def _agregar_nueva_herramienta(self, instance):
        """Agregar nueva herramienta al formulario"""
        self._agregar_herramienta_widget()

    def _agregar_herramienta_widget(self):
        """Crear widget para una herramienta"""
        herramienta_id = len(self.herramientas_utilizadas)

        # Container principal de la herramienta
        herramienta_container = MDBoxLayout(
            orientation="vertical",
            spacing="5dp",
            adaptive_height=True,
            size_hint_y=None
        )

        # Header con título y botón eliminar
        header_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="30dp",
            spacing="10dp"
        )

        herramienta_title = MDLabel(
            text=f"Herramienta #{herramienta_id + 1}:",
            theme_text_color="Primary",
            font_style="Subtitle2",
            size_hint_x=0.8
        )

        # Botón eliminar (solo si hay más de 1)
        if len(self.herramientas_utilizadas) > 0:  # Permitir eliminar si hay más de 1
            eliminar_btn = MDIconButton(
                icon="close",
                size_hint_x=0.2,
                on_release=lambda x, idx=herramienta_id: self._eliminar_herramienta(idx)
            )
            header_layout.add_widget(herramienta_title)
            header_layout.add_widget(eliminar_btn)
        else:
            header_layout.add_widget(herramienta_title)

        # Campo nombre de herramienta
        nombre_field = MDTextField(
            hint_text="Nombre de la herramienta...",
            size_hint_y=None,
            height="40dp"
        )

        # Layout horizontal para cantidad con botones
        cantidad_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="40dp",
            spacing="5dp"
        )

        cantidad_menos_btn = MDIconButton(
            icon="minus",
            size_hint_x=0.2,
            on_release=lambda x, idx=herramienta_id: self._cambiar_cantidad(idx, -1)
        )

        cantidad_field = MDTextField(
            text="1",
            input_filter="int",
            size_hint_x=0.6,
            halign="center"
        )

        cantidad_mas_btn = MDIconButton(
            icon="plus",
            size_hint_x=0.2,
            on_release=lambda x, idx=herramienta_id: self._cambiar_cantidad(idx, 1)
        )

        cantidad_layout.add_widget(cantidad_menos_btn)
        cantidad_layout.add_widget(cantidad_field)
        cantidad_layout.add_widget(cantidad_mas_btn)

        # Layout para perdidas/dañadas
        validacion_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="40dp",
            spacing="10dp"
        )

        perdidas_field = MDTextField(
            hint_text="Perdidas",
            text="0",
            input_filter="int",
            size_hint_x=0.5,
            on_text=lambda instance, text, idx=herramienta_id: self._validar_herramienta_cruzada(idx)
        )

        dañadas_field = MDTextField(
            hint_text="Dañadas",
            text="0",
            input_filter="int",
            size_hint_x=0.5,
            on_text=lambda instance, text, idx=herramienta_id: self._validar_herramienta_cruzada(idx)
        )

        validacion_layout.add_widget(perdidas_field)
        validacion_layout.add_widget(dañadas_field)

        # Agregar todo al container
        herramienta_container.add_widget(header_layout)
        herramienta_container.add_widget(nombre_field)
        herramienta_container.add_widget(cantidad_layout)
        herramienta_container.add_widget(validacion_layout)

        # Calcular altura total
        herramienta_container.height = "155dp"

        # Guardar referencias
        herramienta_data = {
            'container': herramienta_container,
            'nombre_field': nombre_field,
            'cantidad_field': cantidad_field,
            'perdidas_field': perdidas_field,
            'dañadas_field': dañadas_field,
            'id': herramienta_id
        }

        self.herramientas_utilizadas.append(herramienta_data)
        self.herramientas_container.add_widget(herramienta_container)

    def _cambiar_cantidad(self, herramienta_idx, delta):
        """Cambiar cantidad de herramienta con botones +/-"""
        if herramienta_idx < len(self.herramientas_utilizadas):
            herramienta = self.herramientas_utilizadas[herramienta_idx]
            cantidad_actual = int(herramienta['cantidad_field'].text or "1")
            nueva_cantidad = max(1, cantidad_actual + delta)  # Mínimo 1
            herramienta['cantidad_field'].text = str(nueva_cantidad)

            # Revalidar campos cruzados
            self._validar_herramienta_cruzada(herramienta_idx)

    def _eliminar_herramienta(self, herramienta_idx):
        """Eliminar herramienta del formulario"""
        if len(self.herramientas_utilizadas) <= 1:
            self._mostrar_error_dialog("Debe mantener al menos una herramienta")
            return

        if herramienta_idx < len(self.herramientas_utilizadas):
            herramienta_data = self.herramientas_utilizadas[herramienta_idx]

            # Remover del layout
            self.herramientas_container.remove_widget(herramienta_data['container'])

            # Remover de la lista
            self.herramientas_utilizadas.pop(herramienta_idx)

            # Reindexar títulos
            self._reindexar_herramientas()

    def _reindexar_herramientas(self):
        """Reindexar títulos de herramientas después de eliminar"""
        for idx, herramienta in enumerate(self.herramientas_utilizadas):
            # Actualizar ID
            herramienta['id'] = idx

            # Actualizar título en header
            header_layout = herramienta['container'].children[-1]  # Primer widget agregado
            if header_layout.children:
                title_label = header_layout.children[-1]  # Primer child del header
                if hasattr(title_label, 'text'):
                    title_label.text = f"Herramienta #{idx + 1}:"

    def _validar_herramienta_cruzada(self, herramienta_idx):
        """Validar regla: perdidas + dañadas ≤ total_utilizadas"""
        if herramienta_idx >= len(self.herramientas_utilizadas):
            return

        herramienta = self.herramientas_utilizadas[herramienta_idx]

        try:
            total = int(herramienta['cantidad_field'].text or "1")
            perdidas = int(herramienta['perdidas_field'].text or "0")
            dañadas = int(herramienta['dañadas_field'].text or "0")

            # Validar regla fundamental
            if (perdidas + dañadas) > total:
                # Ajustar automáticamente
                if perdidas > total:
                    herramienta['perdidas_field'].text = str(total)
                    herramienta['dañadas_field'].text = "0"
                elif dañadas > (total - perdidas):
                    herramienta['dañadas_field'].text = str(total - perdidas)

        except ValueError:
            # Si hay error en conversión, resetear a valores seguros
            herramienta['perdidas_field'].text = "0"
            herramienta['dañadas_field'].text = "0"

    def _actualizar_herramientas_perdidas_dañadas(self):
        """Actualizar campos de perdidas/dañadas cuando cambia cuadrilla"""
        # Resetear validaciones
        for herramienta in self.herramientas_utilizadas:
            herramienta['perdidas_field'].text = "0"
            herramienta['dañadas_field'].text = "0"

    def _validar_y_guardar_reporte(self):
        """Validar todos los campos y guardar reporte"""
        # Validaciones básicas
        if not self.selected_cuadrilla_data or self.cuadrilla_field.text == "Seleccionar Cuadrilla *":
            self._mostrar_error_dialog("Debe seleccionar una cuadrilla")
            return

        if not self.municipio_field.text.strip():
            self._mostrar_error_dialog("Debe ingresar el municipio")
            return

        if not self.distancia_field.text.strip():
            self._mostrar_error_dialog("Debe ingresar la distancia")
            return

        # Validar herramientas
        herramientas_validas = []
        for idx, herramienta in enumerate(self.herramientas_utilizadas):
            nombre = herramienta['nombre_field'].text.strip()
            if not nombre:
                self._mostrar_error_dialog(f"Debe ingresar el nombre de la herramienta #{idx + 1}")
                return

            try:
                cantidad = int(herramienta['cantidad_field'].text or "1")
                perdidas = int(herramienta['perdidas_field'].text or "0")
                dañadas = int(herramienta['dañadas_field'].text or "0")

                if cantidad < 1:
                    self._mostrar_error_dialog(f"La cantidad de {nombre} debe ser al menos 1")
                    return

                if (perdidas + dañadas) > cantidad:
                    self._mostrar_error_dialog(f"Herramienta {nombre}: Perdidas + Dañadas no puede exceder el total")
                    return

                herramientas_validas.append({
                    'nombre': nombre,
                    'cantidad_utilizada': cantidad,
                    'perdidas': perdidas,
                    'dañadas': dañadas
                })

            except ValueError:
                self._mostrar_error_dialog(f"Error en los números de la herramienta #{idx + 1}")
                return

        # Si llegamos aquí, todo está válido
        self._procesar_reporte(herramientas_validas)

    def _procesar_reporte(self, herramientas_validas):
        """Procesar y enviar reporte a la API"""
        # Preparar datos del reporte
        reporte_data = {
            'cuadrilla': self.selected_cuadrilla_data.get('numero_cuadrilla', 'N/A'),
            'actividad': self.actividad_field.text,
            'municipio': self.municipio_field.text.strip(),
            'distancia_metros': int(self.distancia_field.text),
            'herramientas': herramientas_validas,
            'detalles_adicionales': self.detalles_field.text.strip()
        }

        # Mostrar dialog de progreso
        self.progress_dialog = MDDialog(
            title="🔄 Generando Reporte",
            text="Procesando datos y generando PDF...\nPor favor espera un momento.",
            auto_dismiss=False
        )
        self.progress_dialog.open()

        # Enviar a la API en segundo plano
        Clock.schedule_once(lambda dt: self._enviar_reporte_api(reporte_data), 0.5)

    def _enviar_reporte_api(self, reporte_data):
        """Enviar reporte a la API"""
        try:
            response = requests.post(
                f"{self.api_client.base_url}/api/reports/generales/generar",
                json=reporte_data,
                timeout=30
            )

            self.progress_dialog.dismiss()

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    reporte_info = data.get('reporte', {})
                    self._mostrar_exito_generacion(reporte_info)
                    # Volver a pantalla principal y actualizar lista
                    self._volver_pantalla_principal()
                    Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)
                else:
                    self._mostrar_error_dialog(f"Error: {data.get('error', 'Error desconocido')}")
            else:
                self._mostrar_error_dialog(f"Error HTTP {response.status_code}")

        except Exception as e:
            self.progress_dialog.dismiss()
            self._mostrar_error_dialog(f"Error de conexión: {str(e)}")

    def _mostrar_exito_generacion(self, reporte_info):
        """Mostrar mensaje de éxito al generar reporte"""
        numero_reporte = reporte_info.get('numero_reporte', 'N/A')
        cuadrilla = reporte_info.get('cuadrilla', 'N/A')

        success_dialog = MDDialog(
            title="✅ Reporte Generado",
            text=f"Reporte N°{numero_reporte} generado exitosamente.\n\nCuadrilla: {cuadrilla}\nPDF disponible en la lista.",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: success_dialog.dismiss()
                )
            ]
        )
        success_dialog.open()

    def _volver_pantalla_principal(self):
        """Volver a la pantalla principal de reportes"""
        if self.screen_stack:
            # Restaurar pantalla anterior
            previous_layout = self.screen_stack.pop()
            self.parent_layout.clear_widgets()
            self.parent_layout.add_widget(previous_layout)
            self.current_layout = previous_layout

            # Actualizar lista si estamos en la principal
            Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)
        else:
            # Fallback: recrear pantalla principal
            self.mostrar_reportes_generales()

    def _mostrar_error_dialog(self, mensaje):
        """Mostrar dialog de error"""
        error_dialog = MDDialog(
            title="❌ Error",
            text=mensaje,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: error_dialog.dismiss()
                )
            ]
        )
        error_dialog.open()

    def _refrescar_datos(self):
        """Refrescar datos de la pantalla actual"""
        if hasattr(self, 'creation_layout') and self.creation_layout in self.parent_layout.children:
            # Estamos en pantalla de creación, recargar cuadrillas
            self._cargar_cuadrillas_data()
        else:
            # Estamos en pantalla principal, recargar lista
            self._cargar_pantalla_principal()

    def _volver_menu_principal(self):
        """Volver al menú principal de reportes"""
        if hasattr(self.parent_layout, 'mostrar_menu_reportes'):
            self.parent_layout.mostrar_menu_reportes()
        elif hasattr(self.parent_layout, 'parent') and hasattr(self.parent_layout.parent, 'mostrar_menu_reportes'):
            self.parent_layout.parent.mostrar_menu_reportes()