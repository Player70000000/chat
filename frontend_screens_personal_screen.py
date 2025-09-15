import requests
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineListItem, ThreeLineListItem, OneLineListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.widget import MDWidget
from kivymd.uix.menu import MDDropdownMenu
from kivy.clock import Clock
from kivy.metrics import dp
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import API_BASE_URL


class CuadrillaListItem(ThreeLineListItem):
    def __init__(self, numero_cuadrilla, moderador_nombre, numero_obreros, estado, cuadrilla_data, on_select_callback, **kwargs):
        super().__init__(**kwargs)
        actividad = cuadrilla_data.get('actividad', 'Sin actividad')
        self.text = f"👷‍♂️ {numero_cuadrilla} - {estado}"
        self.secondary_text = f"🎯 Actividad: {actividad}"
        self.tertiary_text = f"Moderador: {moderador_nombre} | Obreros: {numero_obreros}"
        self.numero_cuadrilla = numero_cuadrilla
        self.moderador_nombre = moderador_nombre
        self.numero_obreros = numero_obreros
        self.estado = estado
        self.cuadrilla_data = cuadrilla_data
        self.on_select_callback = on_select_callback
        self.on_release = self.select_cuadrilla

    def select_cuadrilla(self):
        self.on_select_callback(self.cuadrilla_data)


class EmpleadoListItem(TwoLineListItem):
    def __init__(self, nombre, apellido, cedula, on_select_callback, **kwargs):
        super().__init__(**kwargs)
        self.text = f"👤 {nombre} {apellido}"
        self.secondary_text = f"Cédula: {cedula}"
        self.nombre = nombre
        self.apellido = apellido
        self.cedula = cedula
        self.on_select_callback = on_select_callback
        self.on_release = self.select_empleado
        
    def select_empleado(self):
        self.on_select_callback(self.nombre, self.apellido, self.cedula)


class CuadrillasManagementScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "cuadrillas_management"
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # Top bar
        self.top_bar = MDTopAppBar(
            title="Gestión de Cuadrillas",
            left_action_items=[["arrow-left", lambda x: self.go_back()]]
        )
        
        # Card principal con botón y lista juntos
        self.cuadrillas_card = MDCard(
            elevation=1,
            padding="15dp"
        )

        card_content = MDBoxLayout(orientation="vertical", spacing="15dp")

        # Botón crear cuadrilla
        cuadrillas_button = MDRaisedButton(
            text="➕ CREAR CUADRILLA",
            md_bg_color=[0.6, 0.3, 0.8, 1],  # Morado
            size_hint_y=None,
            height="50dp",
            on_release=self.show_cuadrillas_placeholder
        )

        # Título para la lista
        lista_title = MDLabel(
            text="Lista de Cuadrillas",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )

        # Lista de cuadrillas
        self.cuadrillas_scroll = MDScrollView()
        self.cuadrillas_list = MDList()
        self.cuadrillas_scroll.add_widget(self.cuadrillas_list)

        card_content.add_widget(cuadrillas_button)
        card_content.add_widget(lista_title)
        card_content.add_widget(self.cuadrillas_scroll)
        self.cuadrillas_card.add_widget(card_content)

        layout.add_widget(self.top_bar)
        layout.add_widget(self.cuadrillas_card)
        
        self.add_widget(layout)
        
        # Cargar cuadrillas al entrar a la pantalla
        Clock.schedule_once(lambda dt: self.load_cuadrillas(), 0.5)
        
    def load_cuadrillas(self):
        self.cuadrillas_list.clear_widgets()
        
        # Indicador de carga
        loading_item = OneLineListItem(text="🔄 Cargando cuadrillas...")
        self.cuadrillas_list.add_widget(loading_item)
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/personnel/cuadrillas/", timeout=10)
            self.cuadrillas_list.clear_widgets()
            
            if response.status_code == 200:
                data = response.json()
                cuadrillas = data.get('cuadrillas', [])
                
                if not cuadrillas:
                    no_cuadrillas_item = OneLineListItem(
                        text="📝 No hay cuadrillas registradas. Crea una usando el botón +"
                    )
                    self.cuadrillas_list.add_widget(no_cuadrillas_item)
                else:
                    for cuadrilla in cuadrillas:
                        numero = cuadrilla.get('numero_cuadrilla', 'N/A')

                        # Obtener información del moderador y obreros
                        moderador = cuadrilla.get('moderador', {})
                        moderador_nombre = f"{moderador.get('nombre', '')} {moderador.get('apellidos', '')}".strip()
                        if not moderador_nombre:
                            moderador_nombre = "Sin moderador"

                        num_obreros = cuadrilla.get('numero_obreros', 0)

                        # Información de estado
                        activo = cuadrilla.get('activo', True)
                        estado_text = "✅ Activa" if activo else "❌ Inactiva"

                        cuadrilla_item = CuadrillaListItem(
                            numero_cuadrilla=numero,
                            moderador_nombre=moderador_nombre,
                            numero_obreros=num_obreros,
                            estado=estado_text,
                            cuadrilla_data=cuadrilla,
                            on_select_callback=self.view_cuadrilla_details
                        )
                        self.cuadrillas_list.add_widget(cuadrilla_item)
            else:
                no_cuadrillas_item = OneLineListItem(
                    text="📝 No hay cuadrillas registradas. Crea una usando el botón de arriba"
                )
                self.cuadrillas_list.add_widget(no_cuadrillas_item)
                
        except requests.exceptions.Timeout:
            self.show_error("⏱️ Timeout: El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_error("🌐 Error de conexión: Verifica tu conexión a internet")
        except Exception as e:
            self.show_error(f"⚠️ Error inesperado: {str(e)}")
            
    def show_error(self, message):
        self.cuadrillas_list.clear_widgets()
        error_item = OneLineListItem(text=message)
        self.cuadrillas_list.add_widget(error_item)
        
        retry_item = OneLineListItem(
            text="🔄 Reintentar",
            on_release=lambda x: self.load_cuadrillas()
        )
        self.cuadrillas_list.add_widget(retry_item)
        
    def show_create_cuadrilla_dialog(self):
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None, height="200dp")
        
        title_label = MDLabel(
            text="Nueva Cuadrilla de Trabajo",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        
        self.numero_input = MDTextField(
            hint_text="Número de cuadrilla",
            required=True,
            size_hint_y=None,
            height="48dp",
            helper_text="Ej: 001, A01, LIMPIEZA-01"
        )
        
        self.actividad_input = MDTextField(
            hint_text="Actividad principal",
            required=True,
            size_hint_y=None,
            height="48dp",
            helper_text="Ej: Limpieza general, Mantenimiento"
        )
        
        content.add_widget(title_label)
        content.add_widget(self.numero_input)
        content.add_widget(self.actividad_input)
        
        self.create_dialog = MDDialog(
            title="Crear Nueva Cuadrilla",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.create_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="CREAR",
                    on_release=self.create_cuadrilla
                )
            ]
        )
        self.create_dialog.open()
        
    def create_cuadrilla(self, instance):
        numero = self.numero_input.text.strip()
        actividad = self.actividad_input.text.strip()
        
        if not numero or not actividad:
            self.show_dialog("Error", "Todos los campos son obligatorios")
            return
            
        try:
            data = {
                "numero_cuadrilla": numero,
                "actividad": actividad
            }
            
            response = requests.post(f"{API_BASE_URL}/api/personnel/cuadrillas/", json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                self.create_dialog.dismiss()
                self.show_dialog("¡Éxito!", f"Cuadrilla {numero} creada exitosamente")
                self.load_cuadrillas()
            elif response.status_code == 400:
                error_data = response.json()
                self.show_dialog("Error", error_data.get("error", "Error al crear cuadrilla"))
            else:
                self.show_dialog("Error", f"Error del servidor: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.show_dialog("Error", "El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "No se pudo conectar al servidor")
        except Exception as e:
            self.show_dialog("Error", "Error inesperado al crear cuadrilla")
            
    def show_cuadrilla_options(self, cuadrilla_data):
        numero = cuadrilla_data.get('numero_cuadrilla', 'N/A')
        moderador = cuadrilla_data.get('moderador', {})
        moderador_nombre = f"{moderador.get('nombre', '')} {moderador.get('apellidos', '')}".strip()
        num_obreros = cuadrilla_data.get('numero_obreros', 0)
        activo = cuadrilla_data.get('activo', True)

        self.selected_cuadrilla = cuadrilla_data

        info_text = f"Moderador: {moderador_nombre}\n"
        info_text += f"Número de obreros: {num_obreros}\n"
        info_text += f"Estado: {'Activa' if activo else 'Inactiva'}\n\n"
        info_text += "¿Qué deseas hacer?"

        self.options_dialog = MDDialog(
            title=f"👷‍♂️ {numero}",
            text=info_text,
            buttons=[
                MDRaisedButton(
                    text="VER DETALLES",
                    on_release=lambda x: self.view_cuadrilla_details(cuadrilla_data)
                ),
                # MDRaisedButton(
                #     text="EDITAR",
                #     on_release=lambda x: self.edit_cuadrilla(cuadrilla_data)
                # ),
                MDRaisedButton(
                    text="ELIMINAR",
                    on_release=lambda x: self.confirm_delete_cuadrilla(cuadrilla_data)
                ),
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.options_dialog.dismiss()
                )
            ]
        )
        self.options_dialog.open()

    def view_cuadrilla_details(self, cuadrilla_data):
        """Mostrar detalles completos de la cuadrilla"""
        # No hay dialog de opciones que cerrar, vamos directo a detalles

        numero = cuadrilla_data.get('numero_cuadrilla', 'N/A')
        actividad = cuadrilla_data.get('actividad', 'Sin actividad especificada')
        moderador = cuadrilla_data.get('moderador', {})
        obreros = cuadrilla_data.get('obreros', [])

        # Crear contenido detallado
        content_layout = MDBoxLayout(orientation="vertical", spacing="10dp", adaptive_height=True)

        # Información de la actividad
        actividad_info = f"🎯 Actividad:\n   {actividad}"

        actividad_label = MDLabel(
            text=actividad_info,
            theme_text_color="Primary",
            font_style="H6",
            adaptive_height=True
        )

        # Información del moderador
        moderador_info = f"👤 Moderador:\n"
        moderador_info += f"   Nombre: {moderador.get('nombre', 'N/A')} {moderador.get('apellidos', 'N/A')}\n"
        moderador_info += f"   Cédula: {moderador.get('cedula', 'N/A')}"

        moderador_label = MDLabel(
            text=moderador_info,
            theme_text_color="Primary",
            adaptive_height=True
        )

        # Lista de obreros
        obreros_info = f"👷‍♂️ Obreros ({len(obreros)}):\n"
        for i, obrero in enumerate(obreros, 1):
            obreros_info += f"   {i}. {obrero.get('nombre', 'N/A')} {obrero.get('apellidos', 'N/A')} (CI: {obrero.get('cedula', 'N/A')})\n"

        obreros_label = MDLabel(
            text=obreros_info,
            theme_text_color="Primary",
            adaptive_height=True
        )

        # Metadatos
        fecha_creacion = cuadrilla_data.get('fecha_creacion', 'N/A')
        creado_por = cuadrilla_data.get('creado_por', 'N/A')

        meta_info = f"📅 Información adicional:\n"
        meta_info += f"   Creada: {fecha_creacion}\n"
        meta_info += f"   Creado por: {creado_por}"

        meta_label = MDLabel(
            text=meta_info,
            theme_text_color="Secondary",
            adaptive_height=True
        )

        content_layout.add_widget(actividad_label)
        content_layout.add_widget(moderador_label)
        content_layout.add_widget(obreros_label)
        content_layout.add_widget(meta_label)

        # Crear scroll para el contenido
        scroll_content = MDScrollView(size_hint_y=None, height="400dp")
        scroll_content.add_widget(content_layout)

        self.details_dialog = MDDialog(
            title=f"👷‍♂️ {numero}",
            type="custom",
            content_cls=scroll_content,
            buttons=[
                MDRaisedButton(
                    text="ELIMINAR",
                    md_bg_color=[0.8, 0.2, 0.2, 1],  # Rojo
                    on_release=lambda x: [self.details_dialog.dismiss(), self.confirm_delete_cuadrilla(cuadrilla_data)]
                ),
                MDRaisedButton(
                    text="CERRAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],  # Gris
                    on_release=lambda x: self.details_dialog.dismiss()
                )
            ],
            size_hint=(0.9, 0.8)
        )
        self.details_dialog.open()

    def edit_cuadrilla(self, numero, actividad_actual):
        self.options_dialog.dismiss()
        
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None, height="150dp")
        
        info_label = MDLabel(
            text=f"Editando Cuadrilla {numero}",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        
        self.edit_actividad_input = MDTextField(
            text=actividad_actual,
            hint_text="Nueva actividad",
            required=True,
            size_hint_y=None,
            height="48dp"
        )
        
        content.add_widget(info_label)
        content.add_widget(self.edit_actividad_input)
        
        self.edit_dialog = MDDialog(
            title="Editar Cuadrilla",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.edit_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="GUARDAR",
                    on_release=lambda x: self.save_cuadrilla_edit(numero)
                )
            ]
        )
        self.edit_dialog.open()
        
    def save_cuadrilla_edit(self, numero):
        nueva_actividad = self.edit_actividad_input.text.strip()
        
        if not nueva_actividad:
            self.show_dialog("Error", "La actividad no puede estar vacía")
            return
            
        try:
            data = {
                "numero_cuadrilla": numero,
                "actividad": nueva_actividad
            }
            
            response = requests.put(f"{API_BASE_URL}/api/personnel/cuadrillas/{numero}", json=data, timeout=10)
            
            if response.status_code == 200:
                self.edit_dialog.dismiss()
                self.show_dialog("¡Éxito!", f"Cuadrilla {numero} actualizada exitosamente")
                self.load_cuadrillas()
            else:
                error_data = response.json()
                self.show_dialog("Error", error_data.get("error", "Error al actualizar cuadrilla"))
                
        except Exception as e:
            self.show_dialog("Error", "Error inesperado al actualizar cuadrilla")
            
    def confirm_delete_cuadrilla(self, cuadrilla_data):
        self.options_dialog.dismiss()

        numero = cuadrilla_data.get('numero_cuadrilla', 'N/A')
        cuadrilla_id = cuadrilla_data.get('_id')

        self.delete_dialog = MDDialog(
            title="⚠️ Confirmar Eliminación",
            text=f"¿Estás seguro de que deseas eliminar la {numero}?\n\nEsta acción no se puede deshacer.",
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.delete_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="ELIMINAR",
                    on_release=lambda x: self.delete_cuadrilla(cuadrilla_id, numero)
                )
            ]
        )
        self.delete_dialog.open()
        
    def delete_cuadrilla(self, cuadrilla_id, numero):
        try:
            response = requests.delete(f"{API_BASE_URL}/api/personnel/cuadrillas/{cuadrilla_id}", timeout=10)
            
            if response.status_code == 200:
                self.delete_dialog.dismiss()
                self.show_dialog("¡Éxito!", f"Cuadrilla {numero} eliminada exitosamente")
                self.load_cuadrillas()
            else:
                error_data = response.json()
                self.show_dialog("Error", error_data.get("error", "Error al eliminar cuadrilla"))
                
        except Exception as e:
            self.show_dialog("Error", "Error inesperado al eliminar cuadrilla")

    def show_cuadrillas_placeholder(self, instance=None):
        """Mostrar ventana flotante para crear cuadrilla"""
        self.show_create_cuadrilla_dialog()

    def get_next_cuadrilla_number(self):
        """Obtener el próximo número de cuadrilla automáticamente"""
        try:
            # Usar el endpoint específico del backend
            response = requests.get(f"{API_BASE_URL}/api/personnel/cuadrillas/next-number/", timeout=5)

            if response.status_code == 200:
                data = response.json()
                return data.get('numero_cuadrilla', 'Cuadrilla-N°1')
            else:
                # Si hay error en la API, usar fallback
                return "Cuadrilla-N°1"

        except Exception as e:
            # En caso de error, usar número por defecto
            print(f"Error obteniendo próximo número: {e}")
            return "Cuadrilla-N°1"

    def show_create_cuadrilla_dialog(self):
        """Mostrar ventana flotante para crear cuadrilla"""
        # Scroll para contenido extenso
        scroll_content = MDScrollView(size_hint_y=None, height="450dp")
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp", adaptive_height=True, padding="10dp")

        # Título
        title_label = MDLabel(
            text="Crear Cuadrilla",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp",
            halign="center"
        )

        # Campo Número de Cuadrilla (automático, readonly)
        self.cuadrilla_numero_field = MDTextField(
            hint_text="Número de Cuadrilla (Automático)",
            helper_text="Número asignado automáticamente",
            helper_text_mode="on_focus",
            readonly=True,
            size_hint_y=None,
            height="60dp"
        )

        # Campo Actividad (obligatorio)
        self.cuadrilla_actividad_field = MDTextField(
            hint_text="Actividad de la Cuadrilla *",
            required=True,
            helper_text="Descripción de la actividad principal",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )

        # Campo Moderador Asignado (obligatorio) - BOTÓN SELECTOR
        self.cuadrilla_moderador_field = MDRaisedButton(
            text="Seleccionar Moderador *",
            md_bg_color=[0.95, 0.95, 0.95, 1],  # Gris claro como campo
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp",
            on_release=self.open_moderador_dropdown
        )

        # Variables para guardar el moderador seleccionado
        self.selected_moderador_text = ""
        self.selected_moderador_data = None

        # Lista para guardar campos dinámicos de obreros
        self.campos_obreros = []
        self.obreros_seleccionados = []

        # Campo Número de Obreros (obligatorio, 4-40)
        self.cuadrilla_obreros_field = MDTextField(
            hint_text="Número de Obreros (4-40) *",
            required=True,
            helper_text="Ingrese entre 4 y 40 obreros - Se crearán campos automáticamente",
            helper_text_mode="on_focus",
            input_filter="int",
            max_text_length=2,
            size_hint_y=None,
            height="60dp"
        )

        # Bind para detectar cambios en el campo
        self.cuadrilla_obreros_field.bind(text=self.on_obreros_number_change)

        # Container para campos dinámicos de obreros
        self.obreros_dinamicos_container = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            adaptive_height=True
        )

        # Agregar campos al layout
        content_layout.add_widget(title_label)
        content_layout.add_widget(self.cuadrilla_numero_field)
        content_layout.add_widget(self.cuadrilla_actividad_field)
        content_layout.add_widget(self.cuadrilla_moderador_field)
        content_layout.add_widget(self.cuadrilla_obreros_field)
        content_layout.add_widget(self.obreros_dinamicos_container)

        scroll_content.add_widget(content_layout)

        # Crear el dialog
        self.cuadrilla_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=scroll_content,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],
                    on_release=self.cancel_cuadrilla_dialog
                ),
                MDRaisedButton(
                    text="GUARDAR",
                    md_bg_color=[0.6, 0.3, 0.8, 1],  # Morado
                    on_release=self.save_cuadrilla
                )
            ],
            size_hint=(0.9, 0.8)
        )

        # Asignar automáticamente el próximo número de cuadrilla
        next_number = self.get_next_cuadrilla_number()
        self.cuadrilla_numero_field.text = next_number

        self.cuadrilla_dialog.open()

    def cancel_cuadrilla_dialog(self, instance=None):
        """Cancelar y cerrar ventana de crear cuadrilla"""
        # Limpiar campos
        self.clear_cuadrilla_fields()
        # Cerrar dialog
        if hasattr(self, 'cuadrilla_dialog'):
            self.cuadrilla_dialog.dismiss()

    def clear_cuadrilla_fields(self):
        """Limpiar todos los campos del formulario de cuadrilla"""
        if hasattr(self, 'cuadrilla_numero_field'):
            self.cuadrilla_numero_field.text = ""
        if hasattr(self, 'cuadrilla_actividad_field'):
            self.cuadrilla_actividad_field.text = ""
        if hasattr(self, 'cuadrilla_obreros_field'):
            self.cuadrilla_obreros_field.text = ""
        if hasattr(self, 'cuadrilla_moderador_field'):
            self.cuadrilla_moderador_field.text = "Seleccionar Moderador *"
        # Limpiar variables de moderador seleccionado
        self.selected_moderador_text = ""
        self.selected_moderador_data = None

        # Limpiar campos dinámicos de obreros
        if hasattr(self, 'obreros_dinamicos_container'):
            self.obreros_dinamicos_container.clear_widgets()
        self.campos_obreros = []
        self.obreros_seleccionados = []

    def open_moderador_dropdown(self, instance=None):
        """Abrir dropdown para seleccionar moderador de la lista existente"""
        # Cargar moderadores desde API
        try:
            response = requests.get(f"{API_BASE_URL}/api/personnel/moderadores/", timeout=5)

            if response.status_code == 200:
                data = response.json()
                moderadores = data.get('moderadores', [])

                if not moderadores:
                    # No hay moderadores disponibles
                    dialog = MDDialog(
                        title="Sin Moderadores",
                        text="No hay moderadores registrados.\nPrimero debe crear moderadores para asignar a las cuadrillas.",
                        buttons=[
                            MDRaisedButton(
                                text="ENTENDIDO",
                                on_release=lambda x: dialog.dismiss()
                            )
                        ]
                    )
                    dialog.open()
                    return

                # Crear items del menú
                menu_items = []
                for moderador in moderadores:
                    nombre = moderador.get('nombre', '')
                    apellidos = moderador.get('apellidos', '')
                    cedula = moderador.get('cedula', '')
                    nombre_completo = f"{nombre} {apellidos} (CI: {cedula})"

                    menu_items.append({
                        "text": f"   {nombre_completo}   ",
                        "viewclass": "OneLineListItem",
                        "height": 50,
                        "on_release": lambda x=moderador: self.select_moderador(x),
                    })


                caller = instance or self.cuadrilla_moderador_field

                self.moderador_dropdown = MDDropdownMenu(
                    caller=caller,
                    items=menu_items,
                    width_mult=4,
                    max_height=300,
                    position="bottom",
                )

                self.moderador_dropdown.open()

            else:
                # Error en API
                dialog = MDDialog(
                    title="Error",
                    text="No se pudo cargar la lista de moderadores.\nVerifique la conexión e intente nuevamente.",
                    buttons=[
                        MDRaisedButton(
                            text="ENTENDIDO",
                            on_release=lambda x: dialog.dismiss()
                        )
                    ]
                )
                dialog.open()

        except Exception as e:
            # Error de conexión
            dialog = MDDialog(
                title="Error de Conexión",
                text="No se pudo conectar al servidor.\nVerifique su conexión e intente nuevamente.",
                buttons=[
                    MDRaisedButton(
                        text="ENTENDIDO",
                        on_release=lambda x: dialog.dismiss()
                    )
                ]
            )
            dialog.open()

    def select_moderador(self, moderador):
        """Seleccionar moderador para la cuadrilla"""
        nombre = moderador.get('nombre', '')
        apellidos = moderador.get('apellidos', '')
        cedula = moderador.get('cedula', '')

        # Guardar datos del moderador seleccionado
        self.selected_moderador_data = moderador
        self.selected_moderador_text = f"{nombre} {apellidos}"

        # Actualizar texto del botón
        self.cuadrilla_moderador_field.text = f"Moderador: {nombre} {apellidos}"

        # Cerrar dropdown
        if hasattr(self, 'moderador_dropdown'):
            self.moderador_dropdown.dismiss()

    def on_obreros_number_change(self, instance, value):
        """Función que se ejecuta cuando cambia el número de obreros"""
        try:
            # Limpiar campos existentes
            self.obreros_dinamicos_container.clear_widgets()

            # Validar que sea un número
            if not value.isdigit():
                return

            num_obreros = int(value)

            # Validar rango 4-40
            if num_obreros < 4 or num_obreros > 40:
                if num_obreros != 0:  # No mostrar error para campo vacío
                    # Mostrar mensaje de error en el helper text
                    self.cuadrilla_obreros_field.helper_text = "❌ Debe ser entre 4 y 40 obreros"
                    self.cuadrilla_obreros_field.helper_text_mode = "persistent"
                return
            else:
                # Restablecer helper text normal
                self.cuadrilla_obreros_field.helper_text = "Ingrese entre 4 y 40 obreros - Se crearán campos automáticamente"
                self.cuadrilla_obreros_field.helper_text_mode = "on_focus"

            # Crear título para la sección de obreros
            titulo_obreros = MDLabel(
                text=f"Datos de los {num_obreros} Obreros:",
                theme_text_color="Primary",
                font_style="Subtitle1",
                size_hint_y=None,
                height="30dp"
            )
            self.obreros_dinamicos_container.add_widget(titulo_obreros)

            # Crear campos de búsqueda para cada obrero
            self.campos_obreros = []
            self.obreros_seleccionados = []  # Lista para trackear obreros ya seleccionados

            for i in range(num_obreros):
                # Campo de búsqueda por cédula
                busqueda_field = MDTextField(
                    hint_text=f"Buscar Obrero {i+1} por Cédula *",
                    helper_text="Ingrese cédula para buscar obrero automáticamente",
                    helper_text_mode="on_focus",
                    required=True,
                    size_hint_y=None,
                    height="60dp",
                    input_filter="int"
                )

                # Bind para búsqueda en tiempo real
                busqueda_field.bind(text=lambda instance, value, index=i: self.on_obrero_search(instance, value, index))

                # Label para mostrar información del obrero seleccionado
                info_label = MDLabel(
                    text="Ingrese cédula para buscar...",
                    theme_text_color="Secondary",
                    font_size="12sp",
                    size_hint_y=None,
                    height="25dp"
                )

                # Guardar referencia a los campos
                self.campos_obreros.append({
                    'busqueda_field': busqueda_field,
                    'info_label': info_label,
                    'obrero_data': None,  # Datos del obrero seleccionado
                    'dropdown': None,  # Referencia al dropdown activo
                    'selecting': False  # Bandera para evitar búsquedas durante selección
                })

                # Agregar campos al container
                self.obreros_dinamicos_container.add_widget(busqueda_field)
                self.obreros_dinamicos_container.add_widget(info_label)

        except Exception as e:
            print(f"Error generando campos de obreros: {e}")

    def on_obrero_search(self, instance, value, index):
        """Búsqueda inteligente de obreros por cédula en tiempo real"""
        try:
            # Obtener el campo de información correspondiente
            if index >= len(self.campos_obreros):
                return

            # VERIFICAR SI ESTÁ EN PROCESO DE SELECCIÓN - NO BUSCAR
            if self.campos_obreros[index].get('selecting', False):
                return

            info_label = self.campos_obreros[index]['info_label']

            # Si está vacío, restablecer
            if not value:
                info_label.text = "Ingrese cédula para buscar..."
                info_label.theme_text_color = "Secondary"
                self.campos_obreros[index]['obrero_data'] = None
                return

            # Mínimo 1 dígito para buscar
            if len(value) < 1:
                info_label.text = "Ingrese cédula para buscar..."
                info_label.theme_text_color = "Secondary"
                self.campos_obreros[index]['obrero_data'] = None
                return

            # Buscar obreros que coincidan con la cédula
            self.search_obreros_by_cedula(value, index)

        except Exception as e:
            print(f"Error en búsqueda de obreros: {e}")

    def search_obreros_by_cedula(self, cedula_partial, index):
        """Buscar obreros disponibles en la API que coincidan con la cédula parcial"""
        try:
            # Llamar a la API de obreros disponibles (no asignados a cuadrillas)
            response = requests.get(f"{API_BASE_URL}/api/personnel/obreros/disponibles/", timeout=5)

            if response.status_code == 200:
                data = response.json()
                obreros = data.get('obreros', [])

                # Filtrar obreros que empiecen con la cédula parcial Y que no estén ya seleccionados
                matches = []
                for obrero in obreros:
                    cedula = obrero.get('cedula', '')
                    if cedula.startswith(cedula_partial):
                        # Verificar que no esté ya seleccionado en otro campo
                        if not self.is_obrero_already_selected(cedula, index):
                            matches.append(obrero)

                self.handle_search_results(matches, cedula_partial, index)

            else:
                info_label = self.campos_obreros[index]['info_label']
                info_label.text = "❌ Error al buscar obreros"
                info_label.theme_text_color = "Error"

        except Exception as e:
            info_label = self.campos_obreros[index]['info_label']
            info_label.text = "❌ Error de conexión"
            info_label.theme_text_color = "Error"

    def handle_search_results(self, matches, cedula_partial, index):
        """Manejar los resultados de la búsqueda"""
        info_label = self.campos_obreros[index]['info_label']

        if not matches:
            # No se encontraron coincidencias disponibles
            info_label.text = f"❌ No hay obreros disponibles con cédula que empiece por {cedula_partial}"
            info_label.theme_text_color = "Error"
            self.campos_obreros[index]['obrero_data'] = None
            return

        # Siempre mostrar dropdown para que el usuario seleccione manualmente
        if len(matches) == 1:
            info_label.text = f"📝 1 obrero encontrado - Seleccione para confirmar:"
        else:
            info_label.text = f"📝 {len(matches)} obreros encontrados - Seleccione uno:"

        info_label.theme_text_color = "Secondary"
        self.campos_obreros[index]['obrero_data'] = None

        # Mostrar dropdown con opciones (tanto para 1 como para múltiples)
        self.show_obreros_dropdown(matches, index)

    def show_obreros_dropdown(self, matches, index):
        """Mostrar dropdown con lista de obreros disponibles para seleccionar"""
        try:
            # Crear items del menú (solo obreros disponibles)
            menu_items = []
            for obrero in matches:
                nombre = obrero.get('nombre', '')
                apellidos = obrero.get('apellidos', '')
                cedula = obrero.get('cedula', '')

                # Todos los obreros en matches ya están pre-filtrados como disponibles
                menu_items.append({
                    "text": f"   👤 {nombre} {apellidos} (CI: {cedula})   ",
                    "viewclass": "OneLineListItem",
                    "height": 50,
                    "on_release": lambda x=obrero, i=index: self.select_obrero_from_dropdown(x, i),
                })

            if not menu_items:
                return

            # Obtener el campo de búsqueda como caller
            caller = self.campos_obreros[index]['busqueda_field']

            # Crear dropdown con nombre único por campo
            dropdown_name = f"obreros_dropdown_{index}"
            dropdown = MDDropdownMenu(
                caller=caller,
                items=menu_items,
                width_mult=4,
                max_height=200,
                position="bottom",
            )

            # Guardar referencia al dropdown en el campo
            self.campos_obreros[index]['dropdown'] = dropdown
            dropdown.open()

        except Exception as e:
            print(f"Error mostrando dropdown de obreros: {e}")

    def select_obrero_from_dropdown(self, obrero, index):
        """Seleccionar obrero desde el dropdown"""
        try:
            cedula = obrero.get('cedula', '')
            nombre = obrero.get('nombre', '')
            apellidos = obrero.get('apellidos', '')

            # ACTIVAR BANDERA DE SELECCIÓN para prevenir búsquedas
            self.campos_obreros[index]['selecting'] = True

            # Cerrar dropdown PRIMERO
            if 'dropdown' in self.campos_obreros[index] and self.campos_obreros[index]['dropdown']:
                dropdown_ref = self.campos_obreros[index]['dropdown']
                self.campos_obreros[index]['dropdown'] = None

                # Forzar cierre inmediato
                try:
                    dropdown_ref.dismiss()
                except:
                    pass

            # Actualizar campo de búsqueda con la cédula (ahora protegido por bandera)
            busqueda_field = self.campos_obreros[index]['busqueda_field']
            busqueda_field.text = cedula

            # Actualizar información
            info_label = self.campos_obreros[index]['info_label']
            info_label.text = f"✅ {nombre} {apellidos} (CI: {cedula})"
            info_label.theme_text_color = "Primary"

            # Guardar datos del obrero
            self.campos_obreros[index]['obrero_data'] = obrero

            # DESACTIVAR BANDERA después de un delay
            Clock.schedule_once(lambda dt: self.finish_selection(index), 0.2)

        except Exception as e:
            print(f"Error seleccionando obrero: {e}")
            # Asegurarse de desactivar bandera en caso de error
            if index < len(self.campos_obreros):
                self.campos_obreros[index]['selecting'] = False

    def force_close_dropdown(self, dropdown_ref):
        """Función auxiliar para forzar el cierre del dropdown"""
        try:
            if dropdown_ref:
                dropdown_ref.dismiss()
        except Exception as e:
            pass

    def finish_selection(self, index):
        """Finalizar proceso de selección y reactivar búsqueda"""
        try:
            if index < len(self.campos_obreros):
                self.campos_obreros[index]['selecting'] = False
        except Exception as e:
            pass

    def reactivate_search_bind(self, index):
        """Reactivar el bind de búsqueda después de seleccionar obrero"""
        try:
            if index < len(self.campos_obreros):
                busqueda_field = self.campos_obreros[index]['busqueda_field']
                # Reactivar el bind
                busqueda_field.bind(text=lambda instance, value, idx=index: self.on_obrero_search(instance, value, idx))
        except Exception as e:
            pass

    def is_obrero_already_selected(self, cedula, current_index):
        """Verificar si un obrero ya está seleccionado en otro campo"""
        for i, campo in enumerate(self.campos_obreros):
            if i != current_index and campo['obrero_data']:
                if campo['obrero_data'].get('cedula', '') == cedula:
                    return True
        return False

    def save_cuadrilla(self, instance=None):
        """Guardar nueva cuadrilla conectada con API real"""
        try:
            # Validar campos obligatorios
            if not self.cuadrilla_actividad_field.text.strip():
                self.show_dialog("Error", "La actividad es obligatoria")
                return

            if not self.selected_moderador_data:
                self.show_dialog("Error", "Debe seleccionar un moderador")
                return

            if not self.cuadrilla_obreros_field.text.strip():
                self.show_dialog("Error", "Debe especificar el número de obreros")
                return

            # Validar rango de obreros
            try:
                num_obreros = int(self.cuadrilla_obreros_field.text)
                if num_obreros < 4 or num_obreros > 40:
                    self.show_dialog("Error", "El número de obreros debe estar entre 4 y 40")
                    return
            except ValueError:
                self.show_dialog("Error", "El número de obreros debe ser un número válido")
                return

            # Validar que todos los obreros estén seleccionados
            obreros_ids = []
            obreros_faltantes = []

            for i, campo in enumerate(self.campos_obreros):
                obrero_data = campo.get('obrero_data')
                if obrero_data and obrero_data.get('_id'):
                    obreros_ids.append(obrero_data['_id'])
                else:
                    obreros_faltantes.append(i + 1)

            if len(obreros_ids) != num_obreros:
                if obreros_faltantes:
                    faltantes_str = ", ".join(map(str, obreros_faltantes))
                    self.show_dialog("Error", f"Debe seleccionar obreros para las posiciones: {faltantes_str}")
                else:
                    self.show_dialog("Error", f"Debe seleccionar exactamente {num_obreros} obreros")
                return

            # Deshabilitar botón mientras se guarda
            if instance:
                instance.disabled = True
                instance.text = "GUARDANDO..."

            # Preparar datos para enviar
            cuadrilla_data = {
                "actividad": self.cuadrilla_actividad_field.text.strip(),
                "moderador_id": self.selected_moderador_data['_id'],
                "obreros_ids": obreros_ids,
                "creado_por": "sistema"  # Aquí podrías usar el usuario actual
            }

            # Enviar a la API
            response = requests.post(
                f"{API_BASE_URL}/api/personnel/cuadrillas/",
                json=cuadrilla_data,
                timeout=15
            )

            if response.status_code == 201:
                # Éxito
                data = response.json()
                numero_cuadrilla = data.get('cuadrilla', {}).get('numero_cuadrilla', 'N/A')

                self.cuadrilla_dialog.dismiss()
                self.show_dialog("¡Éxito!", f"Cuadrilla {numero_cuadrilla} creada exitosamente")
                self.load_cuadrillas()  # Recargar lista
            else:
                # Error del servidor
                error_data = response.json()
                error_msg = error_data.get('error', 'Error desconocido del servidor')
                self.show_dialog("Error", f"Error al crear cuadrilla: {error_msg}")

        except requests.exceptions.Timeout:
            self.show_dialog("Error", "⏱️ Timeout: El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "🌐 Error de conexión: Verifica tu conexión a internet")
        except Exception as e:
            self.show_dialog("Error", f"⚠️ Error inesperado: {str(e)}")
        finally:
            # Rehabilitar botón
            if instance:
                instance.disabled = False
                instance.text = "GUARDAR"

    def go_back(self):
        # Buscar el layout principal navegando hacia arriba
        current = self.parent
        while current:
            if hasattr(current, 'show_main_menu'):
                current.show_main_menu()
                return
            elif hasattr(current, 'main_layout') and current.main_layout:
                if hasattr(current.main_layout, 'go_back_to_main'):
                    current.main_layout.go_back_to_main('personal')
                return
            current = current.parent
        
    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class EmpleadosManagementScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "empleados_management"
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # Top bar
        self.top_bar = MDTopAppBar(
            title="Gestión de Empleados",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["plus", lambda x: self.show_create_empleado_dialog()]]
        )
        
        # Empleados list
        self.empleados_card = MDCard(
            elevation=1,
            padding="10dp"
        )
        
        self.empleados_scroll = MDScrollView()
        self.empleados_list = MDList()
        self.empleados_scroll.add_widget(self.empleados_list)
        self.empleados_card.add_widget(self.empleados_scroll)
        
        layout.add_widget(self.top_bar)
        layout.add_widget(self.empleados_card)
        
        self.add_widget(layout)
        
        # Cargar empleados al entrar a la pantalla
        Clock.schedule_once(lambda dt: self.load_empleados(), 0.5)
        
    def load_empleados(self):
        self.empleados_list.clear_widgets()
        
        # Indicador de carga
        loading_item = OneLineListItem(text="🔄 Cargando empleados...")
        self.empleados_list.add_widget(loading_item)
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/personnel/obreros/", timeout=10)
            self.empleados_list.clear_widgets()
            
            if response.status_code == 200:
                data = response.json()
                empleados = data.get('obreros', [])
                
                if not empleados:
                    no_empleados_item = OneLineListItem(
                        text="📝 No hay empleados registrados. Registra uno usando el botón +"
                    )
                    self.empleados_list.add_widget(no_empleados_item)
                else:
                    for empleado in empleados:
                        nombre = empleado.get('nombre', 'N/A')
                        apellido = empleado.get('apellido', 'N/A')
                        cedula = empleado.get('cedula', 'N/A')
                        
                        empleado_item = EmpleadoListItem(
                            nombre=nombre,
                            apellido=apellido,
                            cedula=cedula,
                            on_select_callback=self.show_empleado_options
                        )
                        self.empleados_list.add_widget(empleado_item)
            else:
                error_item = OneLineListItem(text=f"❌ Error del servidor: {response.status_code}")
                self.empleados_list.add_widget(error_item)
                
        except requests.exceptions.Timeout:
            self.show_error("⏱️ Timeout: El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_error("🌐 Error de conexión: Verifica tu conexión a internet")
        except Exception as e:
            self.show_error(f"⚠️ Error inesperado: {str(e)}")
            
    def show_error(self, message):
        self.empleados_list.clear_widgets()
        error_item = OneLineListItem(text=message)
        self.empleados_list.add_widget(error_item)
        
        retry_item = OneLineListItem(
            text="🔄 Reintentar",
            on_release=lambda x: self.load_empleados()
        )
        self.empleados_list.add_widget(retry_item)
        
    def show_create_empleado_dialog(self):
        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None, height="280dp")
        
        title_label = MDLabel(
            text="Registrar Nuevo Empleado",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        
        self.nombre_input = MDTextField(
            hint_text="Nombre",
            required=True,
            size_hint_y=None,
            height="48dp"
        )
        
        self.apellido_input = MDTextField(
            hint_text="Apellido",
            required=True,
            size_hint_y=None,
            height="48dp"
        )
        
        self.cedula_input = MDTextField(
            hint_text="Cédula de identidad",
            required=True,
            size_hint_y=None,
            height="48dp",
            helper_text="Ej: 12345678, V-12345678"
        )
        
        content.add_widget(title_label)
        content.add_widget(self.nombre_input)
        content.add_widget(self.apellido_input)
        content.add_widget(self.cedula_input)
        
        self.create_empleado_dialog = MDDialog(
            title="Nuevo Empleado",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.create_empleado_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="REGISTRAR",
                    on_release=self.create_empleado
                )
            ]
        )
        self.create_empleado_dialog.open()
        
    def create_empleado(self, instance):
        nombre = self.nombre_input.text.strip()
        apellido = self.apellido_input.text.strip()
        cedula = self.cedula_input.text.strip()
        
        if not nombre or not apellido or not cedula:
            self.show_dialog("Error", "Todos los campos son obligatorios")
            return
            
        try:
            data = {
                "nombre": nombre,
                "apellido": apellido,
                "cedula": cedula
            }
            
            response = requests.post(f"{API_BASE_URL}/api/personnel/obreros/", json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                self.create_empleado_dialog.dismiss()
                self.show_dialog("¡Éxito!", f"Empleado {nombre} {apellido} registrado exitosamente")
                self.load_empleados()
            elif response.status_code == 400:
                error_data = response.json()
                self.show_dialog("Error", error_data.get("error", "Error al registrar empleado"))
            else:
                self.show_dialog("Error", f"Error del servidor: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.show_dialog("Error", "El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "No se pudo conectar al servidor")
        except Exception as e:
            self.show_dialog("Error", "Error inesperado al registrar empleado")
            
    def show_empleado_options(self, nombre, apellido, cedula):
        self.selected_cedula = cedula
        
        self.options_dialog = MDDialog(
            title=f"{nombre} {apellido}",
            text=f"Cédula: {cedula}\n\n¿Qué deseas hacer?",
            buttons=[
                MDRaisedButton(
                    text="ELIMINAR",
                    on_release=lambda x: self.confirm_delete_empleado(nombre, apellido, cedula)
                ),
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.options_dialog.dismiss()
                )
            ]
        )
        self.options_dialog.open()
        
    def confirm_delete_empleado(self, nombre, apellido, cedula):
        self.options_dialog.dismiss()
        
        self.delete_dialog = MDDialog(
            title="⚠️ Confirmar Eliminación",
            text=f"¿Estás seguro de que deseas eliminar al empleado {nombre} {apellido}?\n\nEsta acción no se puede deshacer.",
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.delete_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="ELIMINAR",
                    on_release=lambda x: self.delete_empleado(nombre, apellido, cedula)
                )
            ]
        )
        self.delete_dialog.open()
        
    def delete_empleado(self, nombre, apellido, cedula):
        try:
            response = requests.delete(f"{API_BASE_URL}/api/personnel/obreros/{cedula}", timeout=10)
            
            if response.status_code == 200:
                self.delete_dialog.dismiss()
                self.show_dialog("¡Éxito!", f"Empleado {nombre} {apellido} eliminado exitosamente")
                self.load_empleados()
            else:
                error_data = response.json()
                self.show_dialog("Error", error_data.get("error", "Error al eliminar empleado"))
                
        except Exception as e:
            self.show_dialog("Error", "Error inesperado al eliminar empleado")
            
    def go_back(self):
        # Buscar el layout principal navegando hacia arriba
        current = self.parent
        while current:
            if hasattr(current, 'show_main_menu'):
                current.show_main_menu()
                return
            elif hasattr(current, 'main_layout') and current.main_layout:
                if hasattr(current.main_layout, 'go_back_to_main'):
                    current.main_layout.go_back_to_main('personal')
                return
            current = current.parent
        
    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class PersonalScreen(MDBoxLayout):
    # Opciones de tallas de ropa disponibles
    TALLAS_ROPA = ["XS", "S", "M", "L", "XL", "XXL"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.main_layout = None  # Referencia al layout principal
        # Variables para controlar los dropdowns
        self.selected_talla_ropa = ""
        self.selected_talla_ropa_edit = ""
        self.setup_ui()
        
    def show_dialog(self, title, text):
        """Mostrar diálogo con título y texto"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
        
    def setup_ui(self):
        # Screen manager para diferentes vistas
        self.screen_manager = MDScreenManager()
        
        # Pantalla del menú principal
        self.main_screen = MDScreen(name="main_menu")
        self.setup_main_menu()
        
        # Pantallas de gestión
        self.cuadrillas_screen = CuadrillasManagementScreen()
        self.empleados_screen = EmpleadosManagementScreen()
        
        # Nueva pantalla de opciones de empleados
        self.empleados_options_screen = MDScreen(name="empleados_options")
        self.setup_empleados_options()
        
        # Pantallas de listas
        self.lista_moderadores_screen = MDScreen(name="lista_moderadores")
        self.setup_lista_moderadores()
        
        self.lista_obreros_screen = MDScreen(name="lista_obreros") 
        self.setup_lista_obreros()
        
        # Nueva pantalla para opciones de listas específicas
        self.empleados_lists_screen = MDScreen(name="empleados_lists")
        self.setup_empleados_lists()
        
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.cuadrillas_screen)
        self.screen_manager.add_widget(self.empleados_screen)
        self.screen_manager.add_widget(self.empleados_options_screen)
        self.screen_manager.add_widget(self.empleados_lists_screen)
        self.screen_manager.add_widget(self.lista_moderadores_screen)
        self.screen_manager.add_widget(self.lista_obreros_screen)
        
        self.add_widget(self.screen_manager)
        
    def setup_main_menu(self):
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Gestión de Personal",
            right_action_items=[["account-multiple", lambda x: None]]
        )
        
        # Contenido del menú
        content_layout = MDBoxLayout(orientation="vertical", spacing="20dp")
        
        # Card de Cuadrillas
        cuadrillas_card = MDCard(
            elevation=3,
            padding="20dp",
            size_hint_y=None,
            height="140dp",
            on_release=self.show_cuadrillas_management,
            md_bg_color=(0.95, 0.95, 1, 1)  # Ligero tinte azul
        )
        
        cuadrillas_content = MDBoxLayout(orientation="vertical", spacing="10dp")
        
        cuadrillas_title = MDLabel(
            text="👷‍♂️ Gestión de Cuadrillas",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )
        
        cuadrillas_desc = MDLabel(
            text="Crear, editar y administrar cuadrillas de trabajo.\nOrganiza los equipos por actividades.",
            theme_text_color="Secondary",
            font_size="14sp",
            text_size=(None, None)
        )
        
        cuadrillas_content.add_widget(cuadrillas_title)
        cuadrillas_content.add_widget(cuadrillas_desc)
        cuadrillas_card.add_widget(cuadrillas_content)
        
        # Card de Empleados
        empleados_card = MDCard(
            elevation=3,
            padding="20dp",
            size_hint_y=None,
            height="140dp",
            on_release=self.show_empleados_management,
            md_bg_color=(0.95, 1, 0.95, 1)  # Ligero tinte verde
        )
        
        empleados_content = MDBoxLayout(orientation="vertical", spacing="10dp")
        
        empleados_title = MDLabel(
            text="👥 Gestión de Empleados",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )
        
        empleados_desc = MDLabel(
            text="Registrar, listar y administrar empleados.\nMantén el directorio de personal actualizado.",
            theme_text_color="Secondary",
            font_size="14sp",
            text_size=(None, None)
        )
        
        empleados_content.add_widget(empleados_title)
        empleados_content.add_widget(empleados_desc)
        empleados_card.add_widget(empleados_content)
        
        # Información adicional
        info_card = MDCard(
            elevation=1,
            padding="15dp",
            size_hint_y=None,
            height="80dp",
            md_bg_color=(1, 1, 0.95, 1)  # Ligero tinte amarillo
        )
        
        info_label = MDLabel(
            text="💡 Tip: Toca las tarjetas para acceder a cada módulo de gestión",
            theme_text_color="Secondary",
            font_size="12sp",
            halign="center"
        )
        info_card.add_widget(info_label)
        
        content_layout.add_widget(cuadrillas_card)
        content_layout.add_widget(empleados_card)
        content_layout.add_widget(info_card)
        
        layout.add_widget(top_bar)
        layout.add_widget(content_layout)
        
        self.main_screen.add_widget(layout)
        
    def show_add_moderador(self, instance=None):
        """Mostrar ventana flotante para añadir moderador"""
        self.show_add_moderador_dialog()
        
    def show_add_obrero(self, instance=None):
        """Mostrar dialog para añadir obrero"""
        self.show_create_obrero_dialog()
        
    def show_cuadrillas_management(self, instance=None):
        """Mostrar gestión de cuadrillas (funcionalidad original)"""
        self.screen_manager.current = "cuadrillas_management"
        
    def show_empleados_management(self, instance=None):
        """Mostrar gestión de empleados (nueva funcionalidad)"""
        self.screen_manager.current = "empleados_options"
        
    def show_main_menu(self):
        self.screen_manager.current = "main_menu"
        
    def show_main_screen(self):
        """Mostrar la pantalla principal de personal"""
        self.show_main_menu()
    
    def setup_empleados_options(self):
        """Configurar pantalla principal de gestión de empleados"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Gestión de Empleados",
            left_action_items=[["arrow-left", lambda x: self.show_main_menu()]]
        )
        
        # Scroll para el contenido
        scroll = MDScrollView()
        content_layout = MDBoxLayout(orientation="vertical", spacing="20dp", adaptive_height=True, padding="20dp")
        
        # Título principal
        title_label = MDLabel(
            text="Gestión de Empleados",
            theme_text_color="Primary",
            font_style="H4",
            size_hint_y=None,
            height="60dp",
            halign="center"
        )
        
        # Sección: Añadir Empleados
        add_section_label = MDLabel(
            text="Agregar Personal",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp",
            halign="left"
        )
        
        # Botones de agregar (horizontal)
        add_buttons_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="15dp",
            size_hint_y=None,
            height="80dp",
            adaptive_width=True
        )
        
        # Botón Añadir Moderador
        moderador_button = MDRaisedButton(
            text="➕ AÑADIR MODERADOR",
            md_bg_color=[0.2, 0.6, 1, 1],  # Azul
            size_hint=(0.48, 1),
            on_release=self.show_add_moderador
        )
        
        # Botón Añadir Obrero
        obrero_button = MDRaisedButton(
            text="➕ AÑADIR OBRERO", 
            md_bg_color=[0.4, 0.8, 0.4, 1],  # Verde
            size_hint=(0.48, 1),
            on_release=self.show_add_obrero
        )
        
        add_buttons_layout.add_widget(moderador_button)
        add_buttons_layout.add_widget(obrero_button)
        
        # Espaciador
        spacer1 = MDLabel(size_hint_y=None, height="20dp")
        
        # Sección: Lista de Empleados
        list_section_label = MDLabel(
            text="Ver Empleados",
            theme_text_color="Primary", 
            font_style="H6",
            size_hint_y=None,
            height="40dp",
            halign="left"
        )
        
        # Botón Lista de Empleados
        empleados_list_button = MDRaisedButton(
            text="👥 LISTA DE EMPLEADOS",
            md_bg_color=[0.8, 0.6, 0.2, 1],  # Naranja
            size_hint_y=None,
            height="60dp",
            on_release=self.show_empleados_lists_options
        )
        
        # Agregar elementos al layout
        content_layout.add_widget(title_label)
        content_layout.add_widget(add_section_label)
        content_layout.add_widget(add_buttons_layout)
        content_layout.add_widget(spacer1)
        content_layout.add_widget(list_section_label)
        content_layout.add_widget(empleados_list_button)
        
        scroll.add_widget(content_layout)
        layout.add_widget(top_bar)
        layout.add_widget(scroll)
        
        self.empleados_options_screen.add_widget(layout)
    
    def setup_lista_moderadores(self):
        """Configurar pantalla de lista de moderadores"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Lista de Moderadores",
            left_action_items=[["arrow-left", lambda x: setattr(self.screen_manager, 'current', 'empleados_lists')]],
            right_action_items=[["refresh", lambda x: self.load_moderadores_data()]]
        )
        
        # Scroll para la lista
        self.moderadores_scroll = MDScrollView()
        self.moderadores_list = MDList()
        self.moderadores_scroll.add_widget(self.moderadores_list)
        
        layout.add_widget(top_bar)
        layout.add_widget(self.moderadores_scroll)
        
        self.lista_moderadores_screen.add_widget(layout)
        
        # Cargar datos inicialmente
        Clock.schedule_once(lambda dt: self.load_moderadores_data(), 0.5)
    
    def setup_lista_obreros(self):
        """Configurar pantalla de lista de obreros"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")

        # Top bar
        top_bar = MDTopAppBar(
            title="Lista de Obreros",
            left_action_items=[["arrow-left", lambda x: setattr(self.screen_manager, 'current', 'empleados_lists')]],
            right_action_items=[["refresh", lambda x: self.load_obreros_data()]]
        )

        # Scroll para la lista
        self.obreros_scroll = MDScrollView()
        self.obreros_list = MDList()
        self.obreros_scroll.add_widget(self.obreros_list)

        layout.add_widget(top_bar)
        layout.add_widget(self.obreros_scroll)

        self.lista_obreros_screen.add_widget(layout)

        # Cargar datos inicialmente
        Clock.schedule_once(lambda dt: self.load_obreros_data(), 0.5)
    
    def open_talla_ropa_dropdown(self, instance=None):
        """Abrir dropdown para seleccionar talla de ropa (formulario crear)"""
        menu_items = []
        for talla in self.TALLAS_ROPA:
            menu_items.append({
                "text": f"   {talla}   ",
                "viewclass": "OneLineListItem", 
                "height": 40,
                "on_release": lambda x=talla: self.select_talla_ropa(x),
            })
        
        # Agregar opción para dejar vacío al final
        menu_items.append({
            "text": "   (Ninguna)   ",
            "viewclass": "OneLineListItem", 
            "height": 40,
            "on_release": lambda: self.select_talla_ropa_vacia(),
        })
        
        caller = instance or self.moderador_talla_ropa_field
        
        self.talla_ropa_dropdown = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=2,
            max_height=200,
            position="bottom",
        )
        
        self.talla_ropa_dropdown.open()
    
    def select_talla_ropa(self, talla):
        """Seleccionar talla de ropa (formulario crear)"""
        self.selected_talla_ropa = talla
        self.selected_talla_text = talla
        self.moderador_talla_ropa_field.text = f"Talla Seleccionada: {talla}"
        
        if hasattr(self, 'talla_ropa_dropdown'):
            self.talla_ropa_dropdown.dismiss()
    
    def select_talla_ropa_vacia(self):
        """Dejar talla de ropa vacía (formulario crear)"""
        self.selected_talla_ropa = ""
        self.selected_talla_text = ""
        self.moderador_talla_ropa_field.text = "Seleccionar Talla de Ropa (opcional)"
        
        if hasattr(self, 'talla_ropa_dropdown'):
            self.talla_ropa_dropdown.dismiss()
    
    def open_talla_ropa_dropdown_edit(self, instance=None):
        """Abrir dropdown para seleccionar talla de ropa (formulario editar)"""
        menu_items = []
        for talla in self.TALLAS_ROPA:
            menu_items.append({
                "text": f"   {talla}   ",
                "viewclass": "OneLineListItem", 
                "height": 40,
                "on_release": lambda x=talla: self.select_talla_ropa_edit(x),
            })
        
        # Agregar opción para dejar vacío al final
        menu_items.append({
            "text": "   (Ninguna)   ",
            "viewclass": "OneLineListItem", 
            "height": 40,
            "on_release": lambda: self.select_talla_ropa_edit_vacia(),
        })
        
        caller = instance or self.edit_moderador_talla_ropa_field
        
        self.talla_ropa_dropdown_edit = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=2,
            max_height=200,
            position="bottom",
        )
        
        self.talla_ropa_dropdown_edit.open()
    
    def select_talla_ropa_edit(self, talla):
        """Seleccionar talla de ropa (formulario editar)"""
        self.selected_talla_ropa_edit = talla
        self.selected_talla_text_edit = talla
        self.edit_moderador_talla_ropa_field.text = f"Talla Seleccionada: {talla}"
        
        if hasattr(self, 'talla_ropa_dropdown_edit'):
            self.talla_ropa_dropdown_edit.dismiss()
    
    def select_talla_ropa_edit_vacia(self):
        """Dejar talla de ropa vacía (formulario editar)"""
        self.selected_talla_ropa_edit = ""
        self.selected_talla_text_edit = ""
        self.edit_moderador_talla_ropa_field.text = "Seleccionar Talla de Ropa (opcional)"
        
        if hasattr(self, 'talla_ropa_dropdown_edit'):
            self.talla_ropa_dropdown_edit.dismiss()
    
    def show_lista_moderadores(self, instance=None):
        """Mostrar lista de moderadores"""
        self.screen_manager.current = "lista_moderadores"
        
    def show_lista_obreros(self, instance=None):
        """Mostrar lista de obreros"""
        self.screen_manager.current = "lista_obreros"
    
    def show_empleados_lists_options(self, instance=None):
        """Mostrar opciones de listas específicas de empleados"""
        self.screen_manager.current = "empleados_lists"
    
    def setup_empleados_lists(self):
        """Configurar pantalla de opciones de listas de empleados"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Lista de Empleados",
            left_action_items=[["arrow-left", lambda x: setattr(self.screen_manager, 'current', 'empleados_options')]]
        )
        
        # Scroll para el contenido
        scroll = MDScrollView()
        content_layout = MDBoxLayout(orientation="vertical", spacing="20dp", adaptive_height=True, padding="20dp")
        
        # Título
        title_label = MDLabel(
            text="Seleccionar Lista",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None,
            height="50dp",
            halign="center"
        )
        
        # Botón Lista de Moderadores
        moderadores_button = MDRaisedButton(
            text="👤 LISTA DE MODERADORES",
            md_bg_color=[0.2, 0.6, 1, 1],  # Azul
            size_hint_y=None,
            height="70dp",
            on_release=self.show_lista_moderadores
        )
        
        # Espaciador
        spacer = MDLabel(size_hint_y=None, height="20dp")
        
        # Botón Lista de Obreros
        obreros_button = MDRaisedButton(
            text="👷 LISTA DE OBREROS",
            md_bg_color=[0.4, 0.8, 0.4, 1],  # Verde
            size_hint_y=None,
            height="70dp",
            on_release=self.show_lista_obreros
        )
        
        content_layout.add_widget(title_label)
        content_layout.add_widget(moderadores_button)
        content_layout.add_widget(spacer)
        content_layout.add_widget(obreros_button)
        
        scroll.add_widget(content_layout)
        layout.add_widget(top_bar)
        layout.add_widget(scroll)
        
        self.empleados_lists_screen.add_widget(layout)
    
    def show_add_moderador_dialog(self):
        """Mostrar ventana flotante para añadir moderador"""
        # Scroll para contenido extenso
        scroll_content = MDScrollView(size_hint_y=None, height="400dp")
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp", adaptive_height=True, padding="10dp")
        
        # Título
        title_label = MDLabel(
            text="Añadir Moderador",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp",
            halign="center"
        )
        
        # Campo Nombres (obligatorio, sin números)
        self.moderador_nombres_field = MDTextField(
            hint_text="Nombres *",
            required=True,
            helper_text="Solo letras, sin números",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter=lambda text, from_undo: ''.join([c for c in text if not c.isdigit()])
        )
        
        # Campo Apellidos (obligatorio, sin números)
        self.moderador_apellidos_field = MDTextField(
            hint_text="Apellidos *",
            required=True,
            helper_text="Solo letras, sin números",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter=lambda text, from_undo: ''.join([c for c in text if not c.isdigit()])
        )
        
        # Campo Cédula (obligatorio)
        self.moderador_cedula_field = MDTextField(
            hint_text="Cédula de Identidad *",
            required=True,
            helper_text="Solo números, mín. 6, máx. 10 dígitos",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter="int",
            max_text_length=10
        )
        
        # Campo Correo (obligatorio, formato email)
        self.moderador_correo_field = MDTextField(
            hint_text="Correo Electrónico *",
            required=True,
            helper_text="Debe contener @ y dominio (ej: usuario@gmail.com)",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )
        
        # Campo Teléfono (obligatorio)
        self.moderador_telefono_field = MDTextField(
            hint_text="Número de Teléfono *",
            required=True,
            helper_text="Ingrese el número de teléfono",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )
        
        # Campos opcionales
        opcional_label = MDLabel(
            text="Campos Opcionales:",
            theme_text_color="Secondary",
            font_size="14sp",
            size_hint_y=None,
            height="30dp"
        )
        
        # Campo Talla de Ropa (opcional) - BOTÓN SELECTOR
        self.moderador_talla_ropa_field = MDRaisedButton(
            text="Seleccionar Talla de Ropa (opcional)",
            md_bg_color=[0.95, 0.95, 0.95, 1],  # Gris claro como campo
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp",
            on_release=self.open_talla_ropa_dropdown
        )
        
        # Variable para guardar la talla seleccionada (ya que no es un TextField)
        self.selected_talla_text = ""
        
        # Campo Talla de Zapatos (opcional) con validación 30-50
        self.moderador_talla_zapatos_field = MDTextField(
            hint_text="Talla de Zapatos (opcional)",
            helper_text="Solo números del 30 al 50",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )
        
        # Agregar campos al layout
        content_layout.add_widget(title_label)
        content_layout.add_widget(self.moderador_nombres_field)
        content_layout.add_widget(self.moderador_apellidos_field)
        content_layout.add_widget(self.moderador_cedula_field)
        content_layout.add_widget(self.moderador_correo_field)
        content_layout.add_widget(self.moderador_telefono_field)
        content_layout.add_widget(opcional_label)
        content_layout.add_widget(self.moderador_talla_ropa_field)
        content_layout.add_widget(self.moderador_talla_zapatos_field)
        
        scroll_content.add_widget(content_layout)
        
        # Crear el dialog
        self.moderador_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=scroll_content,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],
                    on_release=self.cancel_moderador_dialog
                ),
                MDRaisedButton(
                    text="GUARDAR",
                    md_bg_color=[0.2, 0.6, 1, 1],
                    on_release=self.save_moderador
                )
            ],
            size_hint=(0.9, 0.8)
        )
        
        self.moderador_dialog.open()
    
    def cancel_moderador_dialog(self, instance=None):
        """Cancelar y cerrar ventana de añadir moderador"""
        # Limpiar campos
        self.clear_moderador_fields()
        # Cerrar dialog
        if hasattr(self, 'moderador_dialog'):
            self.moderador_dialog.dismiss()
    
    def clear_moderador_fields(self):
        """Limpiar todos los campos del formulario de moderador"""
        if hasattr(self, 'moderador_nombres_field'):
            self.moderador_nombres_field.text = ""
        if hasattr(self, 'moderador_apellidos_field'):
            self.moderador_apellidos_field.text = ""
        if hasattr(self, 'moderador_cedula_field'):
            self.moderador_cedula_field.text = ""
        if hasattr(self, 'moderador_correo_field'):
            self.moderador_correo_field.text = ""
        if hasattr(self, 'moderador_telefono_field'):
            self.moderador_telefono_field.text = ""
        if hasattr(self, 'moderador_talla_ropa_field'):
            self.moderador_talla_ropa_field.text = "Seleccionar Talla de Ropa (opcional)"
        if hasattr(self, 'moderador_talla_zapatos_field'):
            self.moderador_talla_zapatos_field.text = ""
        # Limpiar variables de selección
        self.selected_talla_ropa = ""
        self.selected_talla_ropa_edit = ""
        self.selected_talla_text = ""
        self.selected_talla_text_edit = ""
    
    def save_moderador(self, instance=None):
        """Guardar moderador con validaciones"""
        # Validar campos obligatorios
        validation_result = self.validate_moderador_fields()
        
        if not validation_result:
            return
        
        # Preparar datos
        talla_zapatos_raw = self.moderador_talla_zapatos_field.text.strip()
        
        # Validar talla de zapatos si se ingresó
        if talla_zapatos_raw:
            try:
                talla_zapatos_num = int(talla_zapatos_raw)
                if not (30 <= talla_zapatos_num <= 50):
                    self.show_dialog("Error", "La talla de zapatos debe estar entre 30 y 50")
                    return
            except ValueError:
                self.show_dialog("Error", "La talla de zapatos debe ser un número válido")
                return
        
        moderador_data = {
            "nombre": self.moderador_nombres_field.text.strip().title(),
            "apellidos": self.moderador_apellidos_field.text.strip().title(),
            "cedula": self.moderador_cedula_field.text.strip(),
            "email": self.moderador_correo_field.text.strip().lower(),  # Cambio: correo -> email
            "telefono": self.moderador_telefono_field.text.strip(),
            "talla_ropa": self.selected_talla_text.upper() or None,
            "talla_zapatos": talla_zapatos_raw or None,
            "nivel": "moderador",  # Cambio: tipo -> nivel
            "activo": True  # Añadido campo que el servidor espera
        }
        
        # Deshabilitar botón mientras se procesa
        if instance:
            instance.disabled = True
            instance.text = "GUARDANDO..."
        
        try:
            # Llamada al API para guardar
            api_url = f"{API_BASE_URL}/api/personnel/moderadores/"
            print(f"🌐 Enviando POST a: {api_url}")
            print(f"📡 Datos a enviar: {moderador_data}")
            
            response = requests.post(api_url, json=moderador_data, timeout=10)
            
            print(f"📨 Respuesta del servidor:")
            print(f"  Status code: {response.status_code}")
            print(f"  Response text: {response.text}")
            print(f"  Response headers: {dict(response.headers)}")
            
            if response.status_code == 201:
                print("✅ Guardado exitoso - status 201")
                
                # Debug: Ver qué devuelve el servidor después de crear
                try:
                    created_data = response.json()
                    print(f"🔍 DEBUG - Datos devueltos después de crear moderador: {created_data}")
                    
                    # Obtener el ID del moderador creado
                    moderador_id = created_data.get('moderador_id', '')
                    if moderador_id:
                        # Guardar campos adicionales localmente usando el ID del servidor
                        self.save_additional_moderador_fields(moderador_id, moderador_data)
                        
                except:
                    print("⚠️ No se pudo parsear la respuesta como JSON")
                
                # Éxito - mostrar mensaje y limpiar formulario
                self.show_success_message("Moderador guardado exitosamente")
                self.clear_moderador_fields()
                self.moderador_dialog.dismiss()
                
                # Actualizar lista de moderadores si está visible
                self.refresh_moderadores_list()
                
            else:
                print(f"❌ Error del servidor - status {response.status_code}")
                # Error del servidor
                try:
                    error_data = response.json()
                    print(f"📋 Error data: {error_data}")
                    error_message = error_data.get('error', 'Error desconocido')
                    print(f"🚫 Error message: {error_message}")
                    
                    if 'correo' in error_message.lower() or 'email' in error_message.lower():
                        self.moderador_correo_field.error = True
                        error_message = "Este correo ya está registrado"
                    elif 'telefono' in error_message.lower():
                        self.moderador_telefono_field.error = True
                        error_message = "Este teléfono ya está registrado"
                except Exception as parse_error:
                    print(f"⚠️ Error parseando respuesta JSON: {parse_error}")
                    error_message = f"Error del servidor: {response.status_code}"
                
                print(f"💬 Mostrando diálogo de error: {error_message}")
                self.show_dialog("Error al Guardar", error_message)
                
        except requests.exceptions.ConnectionError as conn_error:
            print(f"🔌 Error de conexión: {conn_error}")
            # Fallback a almacenamiento local si no hay conexión
            if not hasattr(self, 'moderadores_locales'):
                self.moderadores_locales = []
            
            # Verificar duplicados por email
            for moderador in self.moderadores_locales:
                if moderador.get('email', moderador.get('correo', '')) == moderador_data['email']:
                    self.moderador_correo_field.error = True
                    self.show_dialog("Error al Guardar", "Este correo ya está registrado")
                    return
            
            # Guardar localmente
            self.moderadores_locales.append(moderador_data)
            
            # Éxito - mostrar mensaje y limpiar formulario
            self.show_success_message("Moderador guardado exitosamente (modo offline)")
            self.clear_moderador_fields()
            self.moderador_dialog.dismiss()
            
            # Actualizar lista de moderadores si está visible
            self.refresh_moderadores_list()
            
        except Exception as e:
            print(f"💥 Error inesperado: {e}")
            import traceback
            print(f"📍 Traceback: {traceback.format_exc()}")
            self.show_dialog("Error Inesperado", f"Ocurrió un error inesperado: {str(e)}")
        finally:
            print("🔄 Rehabilitando botón...")
            # Rehabilitar botón
            if instance:
                instance.disabled = False
                instance.text = "GUARDAR"
                print("✅ Botón rehabilitado")
    
    def validate_moderador_fields(self):
        """Validar campos obligatorios del moderador"""
        print("🔍 INICIANDO VALIDACIÓN DE CAMPOS")
        valid = True
        
        # Validar nombres
        nombres_text = self.moderador_nombres_field.text.strip()
        print(f"Validando nombres: '{nombres_text}' (length: {len(nombres_text)})")
        
        if not nombres_text:
            print("❌ Nombres vacíos - marcando error")
            self.moderador_nombres_field.error = True
            self.moderador_nombres_field.helper_text = "Los nombres son obligatorios"
            valid = False
        else:
            print("✅ Nombres válidos")
            self.moderador_nombres_field.error = False
            self.moderador_nombres_field.helper_text = "Ingrese los nombres del moderador"
        
        # Validar apellidos
        if not self.moderador_apellidos_field.text.strip():
            self.moderador_apellidos_field.error = True
            self.moderador_apellidos_field.helper_text = "Los apellidos son obligatorios"
            valid = False
        else:
            self.moderador_apellidos_field.error = False
            self.moderador_apellidos_field.helper_text = "Ingrese los apellidos del moderador"
        
        # Validar cédula
        cedula_text = self.moderador_cedula_field.text.strip()
        print(f"Validando cédula: '{cedula_text}' (length: {len(cedula_text)})")
        
        if not cedula_text:
            print("❌ Cédula vacía - marcando error")
            self.moderador_cedula_field.error = True
            self.moderador_cedula_field.helper_text = "La cédula es obligatoria"
            valid = False
        elif not cedula_text.isdigit():
            print("❌ Cédula contiene caracteres no numéricos")
            self.moderador_cedula_field.error = True
            self.moderador_cedula_field.helper_text = "Solo se permiten números"
            valid = False
        elif len(cedula_text) < 6:
            print("❌ Cédula muy corta")
            self.moderador_cedula_field.error = True
            self.moderador_cedula_field.helper_text = "Mínimo 6 dígitos"
            valid = False
        elif len(cedula_text) > 10:
            print("❌ Cédula muy larga")
            self.moderador_cedula_field.error = True
            self.moderador_cedula_field.helper_text = "Máximo 10 dígitos"
            valid = False
        else:
            print("✅ Cédula válida")
            self.moderador_cedula_field.error = False
            self.moderador_cedula_field.helper_text = "Solo números, mín. 6, máx. 10 dígitos"
        
        # Validar correo (formato completo)
        correo = self.moderador_correo_field.text.strip()
        if not correo:
            self.moderador_correo_field.error = True
            self.moderador_correo_field.helper_text = "El correo es obligatorio"
            valid = False
        elif '@' not in correo:
            self.moderador_correo_field.error = True
            self.moderador_correo_field.helper_text = "Debe contener el símbolo @"
            valid = False
        else:
            # Validación más detallada
            email_parts = correo.split('@')
            if len(email_parts) != 2 or not email_parts[0] or not email_parts[1]:
                self.moderador_correo_field.error = True
                self.moderador_correo_field.helper_text = "Formato incorrecto (usuario@dominio.com)"
                valid = False
            elif '.' not in email_parts[1]:
                self.moderador_correo_field.error = True
                self.moderador_correo_field.helper_text = "El dominio debe contener un punto (.com, .es)"
                valid = False
            else:
                self.moderador_correo_field.error = False
                self.moderador_correo_field.helper_text = "Debe contener @ y dominio (ej: usuario@gmail.com)"
        
        # Validar teléfono
        telefono = self.moderador_telefono_field.text.strip()
        if not telefono:
            self.moderador_telefono_field.error = True
            self.moderador_telefono_field.helper_text = "El teléfono es obligatorio"
            valid = False
        elif len(telefono) < 10:
            self.moderador_telefono_field.error = True
            self.moderador_telefono_field.helper_text = "Ingrese un teléfono válido (mín. 10 dígitos)"
            valid = False
        else:
            self.moderador_telefono_field.error = False
            self.moderador_telefono_field.helper_text = "Ingrese el número de teléfono"
        
        return valid
    
    def show_success_message(self, message):
        """Mostrar mensaje de éxito"""
        from kivymd.toast import toast
        toast(message)
    
    def refresh_moderadores_list(self):
        """Actualizar la lista de moderadores"""
        # Si la pantalla de lista de moderadores está configurada, actualizarla
        if hasattr(self, 'lista_moderadores_screen'):
            # Programar actualización después de un breve delay para asegurar que el servidor procese
            Clock.schedule_once(lambda dt: self.load_moderadores_data(), 0.5)
    
    def load_moderadores_data(self):
        """Cargar lista de moderadores desde API o almacenamiento local"""
        try:
            # Intentar cargar desde API primero
            response = requests.get(f"{API_BASE_URL}/api/personnel/moderadores/", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                moderadores = data.get('moderadores', []) if isinstance(data, dict) else data
                
                
                # Limpiar lista actual
                if hasattr(self, 'moderadores_list'):
                    self.moderadores_list.clear_widgets()
                
                if not moderadores:
                    # Mostrar mensaje cuando no hay moderadores
                    no_data_item = OneLineListItem(
                        text="No hay moderadores registrados",
                    )
                    no_data_item.theme_text_color = "Secondary"
                    self.moderadores_list.add_widget(no_data_item)
                else:
                    # Mostrar lista de moderadores desde API
                    for moderador in moderadores:
                        # El servidor ahora devuelve todos los campos directamente
                        nombre = moderador.get('nombre', 'Sin nombre')
                        apellidos = moderador.get('apellidos', '')
                        nombre_completo = f"{nombre} {apellidos}".strip() if apellidos else nombre
                        
                        correo = moderador.get('email', 'Sin email')
                        telefono = moderador.get('telefono', 'No disponible')
                        
                        # Crear item de lista con información completa del servidor
                        item = self.create_moderador_list_item(
                            nombre_completo=nombre_completo,
                            correo=correo,
                            telefono=telefono,
                            moderador_data=moderador
                        )
                        self.moderadores_list.add_widget(item)
            else:
                # API falló, usar datos locales como fallback
                self._load_local_moderadores()
                
        except requests.exceptions.ConnectionError:
            # Sin conexión, usar datos locales
            self._load_local_moderadores()
            
        except Exception as e:
            # Error inesperado
            print(f"Error cargando moderadores: {e}")
            self._load_local_moderadores()
    
    def _load_local_moderadores(self):
        """Cargar moderadores desde almacenamiento local"""
        try:
            # Obtener moderadores locales
            moderadores = getattr(self, 'moderadores_locales', [])
            
            # Limpiar lista actual
            if hasattr(self, 'moderadores_list'):
                self.moderadores_list.clear_widgets()
            
            if not moderadores:
                # Mostrar mensaje cuando no hay moderadores
                no_data_item = OneLineListItem(
                    text="No hay moderadores registrados",
                )
                no_data_item.theme_text_color = "Secondary"
                self.moderadores_list.add_widget(no_data_item)
            else:
                # Mostrar lista de moderadores locales
                for moderador in moderadores:
                    # Para datos locales, usar la estructura consistente con API
                    nombre_completo = f"{moderador.get('nombre', '')} {moderador.get('apellidos', '')}".strip()
                    # Priorizar email sobre correo para consistencia
                    correo = moderador.get('email', moderador.get('correo', 'Sin email'))
                    telefono = moderador.get('telefono', 'No disponible')
                    
                    # Crear item de lista con información del moderador
                    item = self.create_moderador_list_item(
                        nombre_completo=nombre_completo,
                        correo=correo,
                        telefono=telefono,
                        moderador_data=moderador
                    )
                    self.moderadores_list.add_widget(item)
                    
        except Exception as e:
            # Error inesperado
            print(f"Error cargando moderadores locales: {e}")
            if hasattr(self, 'moderadores_list'):
                self.moderadores_list.clear_widgets()
            error_item = OneLineListItem(
                text="Error inesperado al cargar datos",
            )
            error_item.theme_text_color = "Error"
            self.moderadores_list.add_widget(error_item)
    
    def create_moderador_list_item(self, nombre_completo, correo, telefono, moderador_data):
        """Crear item de lista para un moderador"""
        # Obtener cédula del moderador
        cedula = moderador_data.get('cedula', 'No registrada')
        
        # Separar nombre y apellidos para mostrar como campos individuales
        nombre = moderador_data.get('nombre', 'Sin nombre')
        apellidos = moderador_data.get('apellidos', 'Sin apellidos')
        
        # Usar TwoLineListItem con formato profesional sin emojis
        item = TwoLineListItem(
            text=f"Moderador - Cédula: {cedula}",
            secondary_text=f"Nombre: {nombre} | Apellidos: {apellidos} | Email: {correo} | Teléfono: {telefono}"
        )
        
        # CRÍTICO: Agregar datos del moderador al item para poder eliminarlo después
        item.moderador_data = moderador_data
        
        # Opcional: agregar callback para mostrar detalles
        item.on_release = lambda: self.show_moderador_details(moderador_data)
        
        return item
    
    def show_moderador_details(self, moderador_data):
        """Mostrar detalles del moderador"""
        # Obtener campos individuales en lugar de concatenar
        nombre = moderador_data.get('nombre', 'Sin nombre')
        apellidos = moderador_data.get('apellidos', 'Sin apellidos')
        
        # Email (servidor devuelve 'email')
        correo = moderador_data.get('email', 'Sin email')
        
        # Información de contacto y personal
        cedula = moderador_data.get('cedula', 'No registrada')
        telefono = moderador_data.get('telefono', 'No ingresado')
        talla_ropa = moderador_data.get('talla_ropa', 'No ingresado')
        talla_zapatos = moderador_data.get('talla_zapatos', 'No ingresado')
        
        # Información del sistema
        nivel = moderador_data.get('nivel', 'No especificado')
        activo = "Sí" if moderador_data.get('activo', False) else "No"
        fecha_creacion_raw = moderador_data.get('fecha_creacion', 'No especificada')
        creado_por = moderador_data.get('creado_por', 'No especificado')
        
        # Formatear fecha en español
        fecha_creacion = self.format_date_spanish(fecha_creacion_raw)
        
        # Formato profesional sin emojis (Estado omitido de la vista)
        detalles = f"Nombre: {nombre}\n"
        detalles += f"Apellidos: {apellidos}\n"
        detalles += f"Cédula: {cedula}\n"
        detalles += f"Email: {correo}\n"
        detalles += f"Teléfono: {telefono}\n\n"
        detalles += f"Talla de ropa: {talla_ropa}\n"
        detalles += f"Talla de zapatos: {talla_zapatos}\n\n"
        detalles += f"Nivel: {nivel}\n"
        detalles += f"Creado: {fecha_creacion}\n"
        detalles += f"Creado por: {creado_por}"
        
        # Crear diálogo personalizado con botón de editar
        self.show_moderador_details_dialog(moderador_data, detalles)
    
    def show_moderador_details_dialog(self, moderador_data, detalles_text):
        """Mostrar diálogo de detalles con botón de editar"""
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton
        from kivymd.uix.label import MDLabel
        
        # Crear contenedor principal que incluye el título personalizado
        main_content = MDBoxLayout(
            orientation="vertical", 
            spacing="8dp", 
            size_hint_y=None,
            padding=["0dp", "0dp", "0dp", "0dp"]  # Sin padding superior
        )
        main_content.bind(minimum_height=main_content.setter('height'))
        
        # Crear header personalizado con título y botón de editar
        header_layout = MDBoxLayout(
            orientation="horizontal", 
            size_hint_y=None, 
            height="60dp",  # Más alto para mejor alineación
            spacing="5dp",
            padding=["8dp", "8dp", "8dp", "8dp"]  # Padding uniforme
        )
        
        # Título del diálogo
        title_label = MDLabel(
            text="Detalles del Moderador",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_x=0.8,
            halign="left",
            valign="center",
            text_size=(None, None)
        )
        
        # Botón de editar
        edit_button = MDIconButton(
            icon="pencil",
            theme_icon_color="Primary",
            size_hint=(None, None),
            size=("28dp", "28dp"),
            pos_hint={"center_y": 0.5, "right": 1},
            on_release=lambda x: self.edit_moderador(moderador_data)
        )
        
        # Agregar título y botón al header
        header_layout.add_widget(title_label)
        header_layout.add_widget(edit_button)
        
        # Contenido de detalles
        details_label = MDLabel(
            text=detalles_text,
            theme_text_color="Primary",
            size_hint_y=None,
            halign="left",
            valign="top"
        )
        details_label.bind(texture_size=details_label.setter('size'))
        
        # Agregar header y contenido al contenedor principal
        main_content.add_widget(header_layout)
        main_content.add_widget(details_label)
        
        # Espaciador entre texto y botones
        spacer_vertical = MDWidget(size_hint_y=None, height="15dp")
        main_content.add_widget(spacer_vertical)
        
        # Crear layout personalizado para botones separados
        buttons_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="50dp",
            spacing="10dp",
            padding="10dp"
        )
        
        # Botón eliminar a la IZQUIERDA
        delete_button = MDIconButton(
            icon="delete",
            md_bg_color=[0.8, 0.2, 0.2, 1],  # Rojo para indicar peligro
            icon_color=[1, 1, 1, 1],  # Ícono blanco
            size_hint=(None, None),
            size=("40dp", "40dp"),
            on_release=lambda x: self.delete_moderador_confirmation(moderador_data)
        )
        
        # Espaciador que se expande para separar los botones
        spacer = MDWidget(size_hint=(1, 1))
        
        # Botón cerrar a la DERECHA
        close_button = MDRaisedButton(
            text="Cerrar",
            md_bg_color=[0.5, 0.5, 0.5, 1],  # Color gris
            size_hint=(None, None),
            width="80dp",
            height="36dp",
            on_release=lambda x: self.details_dialog.dismiss()
        )
        
        # Agregar botones al layout
        buttons_layout.add_widget(delete_button)
        buttons_layout.add_widget(spacer)
        buttons_layout.add_widget(close_button)
        
        # Agregar el layout de botones al contenido principal
        main_content.add_widget(buttons_layout)
        
        # Crear el diálogo SIN botones predefinidos (los agregamos al contenido)
        self.details_dialog = MDDialog(
            type="custom",
            content_cls=main_content
        )
        self.details_dialog.open()
    
    def edit_moderador(self, moderador_data):
        """Función llamada cuando se presiona el botón de editar"""
        print(f"✏️ Editando moderador: {moderador_data.get('nombre', 'Sin nombre')}")
        
        # Cerrar diálogo actual
        if hasattr(self, 'details_dialog'):
            self.details_dialog.dismiss()
        
        # Crear interfaz de edición con datos prellenados
        self.show_edit_moderador_dialog(moderador_data)
    
    def delete_moderador_confirmation(self, moderador_data):
        """Función llamada cuando se presiona el botón de eliminar - PASO 2: Primer confirmación"""
        print(f"🗑️ Iniciando eliminación de moderador: {moderador_data.get('nombre', 'Sin nombre')}")
        
        # Cerrar dialog de detalles primero
        if hasattr(self, 'details_dialog'):
            self.details_dialog.dismiss()
        
        # Obtener datos del moderador para el mensaje
        nombre = moderador_data.get('nombre', '')
        apellidos = moderador_data.get('apellidos', '')
        cedula = moderador_data.get('cedula', '')
        
        # Mensaje de confirmación personalizado
        mensaje_confirmacion = f"¿Seguro desea eliminar al moderador:\n\n{nombre} {apellidos}\nCédula: {cedula}"
        
        print(f"📋 Mostrando primer mensaje de confirmación para: {nombre} {apellidos}")
        
        # Crear primer dialog de confirmación
        self.first_delete_dialog = MDDialog(
            title="Confirmar Eliminación",
            text=mensaje_confirmacion,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],  # Gris
                    on_release=lambda x: self.cancel_delete_moderador()
                ),
                MDRaisedButton(
                    text="ELIMINAR",
                    md_bg_color=[0.8, 0.2, 0.2, 1],  # Rojo
                    on_release=lambda x: self.show_second_delete_confirmation(moderador_data)
                )
            ]
        )
        self.first_delete_dialog.open()
    
    def cancel_delete_moderador(self):
        """Cancelar eliminación de moderador y volver a lista"""
        print("❌ Eliminación cancelada por el usuario")
        
        # Cerrar dialog de confirmación
        if hasattr(self, 'first_delete_dialog'):
            self.first_delete_dialog.dismiss()
        if hasattr(self, 'second_delete_dialog'):
            self.second_delete_dialog.dismiss()
        
        print("🔙 Permaneciendo en la lista de moderadores")
        # Ya estamos en la lista de moderadores, no necesitamos navegar
    
    def show_second_delete_confirmation(self, moderador_data):
        """Mostrar segundo mensaje de confirmación - PASO 3: Confirmación irreversible"""
        print(f"⚠️ Mostrando segunda confirmación para: {moderador_data.get('nombre', '')} {moderador_data.get('apellidos', '')}")
        
        # Cerrar primer dialog
        if hasattr(self, 'first_delete_dialog'):
            self.first_delete_dialog.dismiss()
        
        # Obtener datos del moderador para el mensaje
        nombre = moderador_data.get('nombre', '')
        apellidos = moderador_data.get('apellidos', '')
        
        # Mensaje de advertencia irreversible
        mensaje_irreversible = f"⚠️ ADVERTENCIA ⚠️\n\nEsta acción es IRREVERSIBLE.\n\nEl moderador {nombre} {apellidos} será eliminado permanentemente del sistema.\n\n¿Está completamente seguro?"
        
        print(f"🚨 Mostrando mensaje irreversible para: {nombre} {apellidos}")
        
        # Crear segundo dialog de confirmación (más severo)
        self.second_delete_dialog = MDDialog(
            title="⚠️ ACCIÓN IRREVERSIBLE",
            text=mensaje_irreversible,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],  # Gris
                    on_release=lambda x: self.cancel_delete_moderador()
                ),
                MDRaisedButton(
                    text="CONFIRMAR",
                    md_bg_color=[0.9, 0.1, 0.1, 1],  # Rojo más intenso
                    on_release=lambda x: self.execute_delete_moderador(moderador_data)
                )
            ]
        )
        self.second_delete_dialog.open()
    
    def execute_delete_moderador(self, moderador_data):
        """Ejecutar eliminación definitiva del moderador - PASOS 5-7"""
        print(f"💀 Ejecutando eliminación definitiva de: {moderador_data.get('nombre', '')} {moderador_data.get('apellidos', '')}")
        
        # Cerrar segundo dialog
        if hasattr(self, 'second_delete_dialog'):
            self.second_delete_dialog.dismiss()
        
        try:
            # Verificar que tenemos los datos del moderador
            if not moderador_data:
                print("❌ ERROR: No se recibieron datos del moderador")
                self.show_dialog("Error", "No se pudieron obtener los datos del moderador")
                return
            
            # Obtener cédula para identificar el moderador
            cedula = moderador_data.get('cedula', '')
            nombre = moderador_data.get('nombre', '')
            apellidos = moderador_data.get('apellidos', '')
            
            if not cedula:
                print("❌ ERROR: No se encontró la cédula del moderador")
                self.show_dialog("Error", "No se pudo identificar el moderador a eliminar")
                return
            
            print(f"🔑 DEBUG: Eliminando moderador con cédula: '{cedula}'")
            print(f"👤 DEBUG: Moderador: {nombre} {apellidos}")
            
            # Preparar datos para enviar al backend
            datos_eliminacion = {
                "cedula": cedula
            }
            
            print(f"📡 DEBUG: Datos a enviar al backend: {datos_eliminacion}")
            
            # Importar requests para hacer la llamada HTTP
            import requests
            import json
            
            # URL del endpoint DELETE (PRODUCCIÓN)
            url = f"{API_BASE_URL}/api/personnel/moderadores/"
            
            print(f"🌐 DEBUG: Enviando DELETE request a: {url}")
            
            # Enviar solicitud DELETE al backend
            response = requests.delete(
                url,
                json=datos_eliminacion,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📡 DEBUG: Respuesta del servidor:")
            print(f"  - Status Code: {response.status_code}")
            print(f"  - Headers: {dict(response.headers)}")
            print(f"  - Text: {response.text}")
            
            if response.status_code == 200:
                # Éxito - parsear respuesta
                try:
                    response_data = response.json()
                    print(f"✅ DEBUG: Respuesta JSON parseada: {response_data}")
                    
                    if response_data.get('success'):
                        print("✅ Moderador eliminado exitosamente del servidor")
                        
                        # PASO 6: Eliminar de vista instantáneamente
                        self.remove_moderador_from_view(cedula)
                        
                        # PASO 7: Mostrar mensaje de éxito y direccionar
                        self.show_delete_success_message(nombre, apellidos)
                        
                    else:
                        error_msg = response_data.get('error', 'Error desconocido del servidor')
                        print(f"❌ Error del servidor: {error_msg}")
                        self.show_dialog("Error", error_msg)
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Error parseando JSON: {e}")
                    self.show_dialog("Error", "Respuesta del servidor no válida")
                    
            else:
                # Error HTTP
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f'Error HTTP {response.status_code}')
                except:
                    error_msg = f'Error HTTP {response.status_code}: {response.text}'
                
                print(f"❌ Error HTTP: {error_msg}")
                self.show_dialog("Error", error_msg)
                
        except requests.exceptions.Timeout:
            print("❌ Timeout conectando al servidor")
            self.show_dialog("Error", "Timeout: El servidor tardó demasiado en responder")
            
        except requests.exceptions.ConnectionError:
            print("❌ Error de conexión al servidor")
            self.show_dialog("Error", "No se pudo conectar al servidor. Verifique su conexión a internet.")
            
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            self.show_dialog("Error", f"Error inesperado: {str(e)}")
    
    def show_edit_moderador_dialog(self, moderador_data):
        """Mostrar ventana flotante para editar moderador - BASADA EN show_add_moderador_dialog()"""
        print(f"📝 DEBUG: Abriendo dialog de edición usando plantilla de añadir moderador")
        
        # Verificar que tenemos los datos del moderador
        if not moderador_data:
            print("❌ ERROR: No se recibieron datos del moderador")
            return
        
        # ESTRUCTURA IDÉNTICA A show_add_moderador_dialog() PERO CON CAMPOS PRELLENADOS
        
        # Scroll para contenido extenso (IGUAL QUE AÑADIR)
        scroll_content = MDScrollView(size_hint_y=None, height="400dp")
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp", adaptive_height=True, padding="10dp")
        
        # Título (ADAPTADO PARA EDITAR)
        title_label = MDLabel(
            text="Editar Moderador",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp",
            halign="center"
        )
        
        # Campo Nombres (obligatorio, PRELLENADO, sin números)
        self.edit_moderador_nombres_field = MDTextField(
            text=str(moderador_data.get('nombre', '')),
            hint_text="Nombres *",
            required=True,
            helper_text="Solo letras, sin números",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter=lambda text, from_undo: ''.join([c for c in text if not c.isdigit()])
        )
        
        # Campo Apellidos (obligatorio, PRELLENADO, sin números)
        self.edit_moderador_apellidos_field = MDTextField(
            text=str(moderador_data.get('apellidos', '')),
            hint_text="Apellidos *",
            required=True,
            helper_text="Solo letras, sin números",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter=lambda text, from_undo: ''.join([c for c in text if not c.isdigit()])
        )
        
        # Campo Cédula (obligatorio, PRELLENADO)
        self.edit_moderador_cedula_field = MDTextField(
            text=str(moderador_data.get('cedula', '')),
            hint_text="Cédula de Identidad *",
            required=True,
            helper_text="Solo números, mín. 6, máx. 10 dígitos",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter="int",
            max_text_length=10
        )
        
        # Campo Correo (obligatorio, PRELLENADO, formato email)
        self.edit_moderador_correo_field = MDTextField(
            text=str(moderador_data.get('email', '')),
            hint_text="Correo Electrónico *",
            required=True,
            helper_text="Debe contener @ y dominio (ej: usuario@gmail.com)",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )
        
        # Campo Teléfono (obligatorio, PRELLENADO)
        self.edit_moderador_telefono_field = MDTextField(
            text=str(moderador_data.get('telefono', '')),
            hint_text="Número de Teléfono *",
            required=True,
            helper_text="Ingrese el número de teléfono",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )
        
        # Campos opcionales (IGUAL QUE AÑADIR)
        opcional_label = MDLabel(
            text="Campos Opcionales:",
            theme_text_color="Secondary",
            font_size="14sp",
            size_hint_y=None,
            height="30dp"
        )
        
        # Campo Talla de Ropa (opcional, PRELLENADO) - BOTÓN SELECTOR
        talla_ropa_valor = moderador_data.get('talla_ropa', '')
        if talla_ropa_valor == 'No ingresado':
            talla_ropa_valor = ''
        
        # Determinar texto inicial del botón
        if talla_ropa_valor and talla_ropa_valor.strip():
            texto_inicial = f"Talla Seleccionada: {talla_ropa_valor}"
            self.selected_talla_ropa_edit = talla_ropa_valor
            self.selected_talla_text_edit = talla_ropa_valor
        else:
            texto_inicial = "Seleccionar Talla de Ropa (opcional)"
            self.selected_talla_ropa_edit = ""
            self.selected_talla_text_edit = ""
            
        self.edit_moderador_talla_ropa_field = MDRaisedButton(
            text=texto_inicial,
            md_bg_color=[0.95, 0.95, 0.95, 1],  # Gris claro como campo
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp",
            on_release=self.open_talla_ropa_dropdown_edit
        )
        
        # Campo Talla de Zapatos (opcional, PRELLENADO)
        talla_zapatos_valor = moderador_data.get('talla_zapatos', '')
        if talla_zapatos_valor == 'No ingresado':
            talla_zapatos_valor = ''
        self.edit_moderador_talla_zapatos_field = MDTextField(
            text=str(talla_zapatos_valor),
            hint_text="Talla de Zapatos (opcional)",
            helper_text="Solo números del 30 al 50",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )
        
        # Agregar campos al layout (EXACTO ORDEN QUE LA VENTANA AÑADIR)
        content_layout.add_widget(title_label)
        content_layout.add_widget(self.edit_moderador_nombres_field)
        content_layout.add_widget(self.edit_moderador_apellidos_field)
        content_layout.add_widget(self.edit_moderador_cedula_field)
        content_layout.add_widget(self.edit_moderador_correo_field)
        content_layout.add_widget(self.edit_moderador_telefono_field)
        content_layout.add_widget(opcional_label)
        content_layout.add_widget(self.edit_moderador_talla_ropa_field)
        content_layout.add_widget(self.edit_moderador_talla_zapatos_field)
        
        scroll_content.add_widget(content_layout)
        
        # Guardar referencia al moderador que estamos editando
        self.editing_moderador_data = moderador_data
        
        # Crear el dialog (EXACTAMENTE IGUAL QUE LA VENTANA AÑADIR)
        self.edit_moderador_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=scroll_content,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],
                    on_release=self.cancel_edit_moderador_dialog
                ),
                MDRaisedButton(
                    text="GUARDAR",
                    md_bg_color=[0.2, 0.6, 1, 1],
                    on_release=self.save_edit_moderador
                )
            ],
            size_hint=(0.9, 0.8)
        )
        
        self.edit_moderador_dialog.open()
    
    def cancel_edit_moderador_dialog(self, instance=None):
        """Cancelar edición y cerrar dialog - IGUAL QUE LA VENTANA AÑADIR"""
        if hasattr(self, 'edit_moderador_dialog'):
            self.edit_moderador_dialog.dismiss()
    
    def cancel_edit_moderador(self):
        """Función antigua - mantener por compatibilidad"""
        if hasattr(self, 'edit_dialog'):
            self.edit_dialog.dismiss()
        print("✗ Edición cancelada")
        # Volver a mostrar la lista de moderadores
        # (ya estamos en la pestaña correcta)
    
    def save_edit_moderador(self, instance=None):
        """Guardar cambios del moderador editado - CONECTAR CON BACKEND PUT"""
        print("💾 DEBUG: Iniciando proceso de guardado...")
        
        try:
            # Verificar que tenemos los campos y datos originales
            if not hasattr(self, 'editing_moderador_data'):
                print("❌ ERROR: No se encontraron datos del moderador original")
                self.show_dialog("Error", "No se pudieron obtener los datos originales del moderador")
                return
            
            # Obtener y formatear valores actuales de los campos (IGUAL QUE LA FUNCIÓN save_moderador)
            nombre = self.edit_moderador_nombres_field.text.strip().title()      # Primera letra mayúscula
            apellidos = self.edit_moderador_apellidos_field.text.strip().title() # Primera letra mayúscula
            cedula = self.edit_moderador_cedula_field.text.strip()
            email = self.edit_moderador_correo_field.text.strip().lower()        # Email en minúsculas
            telefono = self.edit_moderador_telefono_field.text.strip()
            talla_ropa = self.selected_talla_text_edit
            talla_zapatos = self.edit_moderador_talla_zapatos_field.text.strip()
            
            # Validar talla de zapatos si se ingresó
            if talla_zapatos:
                try:
                    talla_zapatos_num = int(talla_zapatos)
                    if not (30 <= talla_zapatos_num <= 50):
                        self.show_dialog("Error", "La talla de zapatos debe estar entre 30 y 50")
                        return
                except ValueError:
                    self.show_dialog("Error", "La talla de zapatos debe ser un número válido")
                    return
            
            print(f"📋 DEBUG: Datos recolectados del formulario:")
            print(f"  - Nombre: '{nombre}'")
            print(f"  - Apellidos: '{apellidos}'")
            print(f"  - Cédula: '{cedula}'")
            print(f"  - Email: '{email}'")
            print(f"  - Teléfono: '{telefono}'")
            print(f"  - Talla ropa: '{talla_ropa}'")
            print(f"  - Talla zapatos: '{talla_zapatos}'")
            
            # Validaciones básicas (IGUAL QUE save_moderador + validación email)
            if not nombre:
                self.show_dialog("Error", "El nombre es obligatorio")
                return
            if not apellidos:
                self.show_dialog("Error", "Los apellidos son obligatorios")
                return
            if not cedula:
                self.show_dialog("Error", "La cédula es obligatoria")
                return
            if not email:
                self.show_dialog("Error", "El email es obligatorio")
                return
            
            # Validación básica de formato de email
            if '@' not in email:
                self.show_dialog("Error", "El email debe contener el símbolo '@'\nEjemplo: usuario@gmail.com")
                return
            
            email_parts = email.split('@')
            if len(email_parts) != 2 or not email_parts[0] or not email_parts[1]:
                self.show_dialog("Error", "Formato de email incorrecto\nEjemplo: usuario@gmail.com")
                return
            
            if '.' not in email_parts[1]:
                self.show_dialog("Error", "El dominio del email debe contener un punto\nEjemplo: usuario@gmail.com")
                return
            
            if not telefono:
                self.show_dialog("Error", "El teléfono es obligatorio")
                return
            
            # Preparar datos para enviar al backend
            datos_actualizados = {
                "cedula_original": self.editing_moderador_data.get('cedula', ''),  # Clave para identificar el moderador
                "nombre": nombre,
                "apellidos": apellidos,
                "cedula": cedula,
                "email": email,
                "telefono": telefono,
                "talla_ropa": talla_ropa if talla_ropa else "",
                "talla_zapatos": talla_zapatos if talla_zapatos else ""
            }
            
            print(f"📡 DEBUG: Datos a enviar al backend: {datos_actualizados}")
            print(f"🔑 DEBUG: Cédula original para identificar: '{datos_actualizados['cedula_original']}'")
            
            # Importar requests para hacer la llamada HTTP
            import requests
            import json
            
            # URL del endpoint PUT (PRODUCCIÓN)
            url = f"{API_BASE_URL}/api/personnel/moderadores/"
            
            print(f"🌐 DEBUG: Enviando PUT request a: {url}")
            
            # Enviar solicitud PUT al backend
            response = requests.put(
                url,
                json=datos_actualizados,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📡 DEBUG: Respuesta del servidor:")
            print(f"  - Status Code: {response.status_code}")
            print(f"  - Headers: {dict(response.headers)}")
            print(f"  - Text: {response.text}")
            
            if response.status_code == 200:
                # Éxito - parsear respuesta
                try:
                    response_data = response.json()
                    print(f"✅ DEBUG: Respuesta JSON parseada: {response_data}")
                    
                    if response_data.get('success'):
                        print("✅ Moderador actualizado exitosamente")
                        
                        # Cerrar dialog de edición
                        if hasattr(self, 'edit_moderador_dialog'):
                            self.edit_moderador_dialog.dismiss()
                        
                        # Mostrar mensaje de éxito
                        self.show_dialog("Éxito", f"Moderador '{nombre} {apellidos}' actualizado correctamente")
                        
                        # Recargar lista de moderadores
                        print("🔄 Recargando lista de moderadores...")
                        self.load_moderadores_data()
                        
                    else:
                        error_msg = response_data.get('error', 'Error desconocido del servidor')
                        print(f"❌ Error del servidor: {error_msg}")
                        self.show_dialog("Error", error_msg)
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Error parseando JSON: {e}")
                    self.show_dialog("Error", "Respuesta del servidor no válida")
                    
            else:
                # Error HTTP
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f'Error HTTP {response.status_code}')
                except:
                    error_msg = f'Error HTTP {response.status_code}: {response.text}'
                
                print(f"❌ Error HTTP: {error_msg}")
                self.show_dialog("Error", error_msg)
                
        except requests.exceptions.Timeout:
            print("❌ Timeout conectando al servidor")
            self.show_dialog("Error", "Timeout: El servidor tardó demasiado en responder")
            
        except requests.exceptions.ConnectionError:
            print("❌ Error de conexión al servidor")
            self.show_dialog("Error", "No se pudo conectar al servidor. Verifique su conexión a internet.")
            
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            self.show_dialog("Error", f"Error inesperado: {str(e)}")
    
    def save_additional_moderador_fields(self, moderador_id, moderador_data):
        """Guardar campos adicionales que el servidor ignora"""
        print(f"💾 Guardando campos adicionales para moderador ID: {moderador_id}")
        
        # Inicializar almacenamiento local si no existe
        if not hasattr(self, 'moderadores_additional_data'):
            self.moderadores_additional_data = {}
        
        # Extraer solo los campos que el servidor ignora
        additional_fields = {
            'apellidos': moderador_data.get('apellidos', ''),
            'telefono': moderador_data.get('telefono', ''),
            'talla_ropa': moderador_data.get('talla_ropa', ''),
            'talla_zapatos': moderador_data.get('talla_zapatos', ''),
            'moderador_id': moderador_id  # Guardar el ID también
        }
        
        # Guardar usando tanto el ID como el email como claves (para mapeo)
        email = moderador_data.get('email', '').lower().strip()
        self.moderadores_additional_data[moderador_id] = additional_fields
        if email:  # También mapear por email para cuando no tengamos ID
            self.moderadores_additional_data[f"email:{email}"] = additional_fields
        
        print(f"💾 Campos adicionales guardados: {additional_fields}")
        print(f"💾 Mapeado por ID: {moderador_id} y email: {email}")
    
    def get_additional_moderador_fields(self, moderador_id=None, email=None):
        """Obtener campos adicionales guardados localmente"""
        if not hasattr(self, 'moderadores_additional_data'):
            return {}
        
        # Intentar primero con ID si está disponible
        if moderador_id and moderador_id in self.moderadores_additional_data:
            return self.moderadores_additional_data[moderador_id]
        
        # Si no hay ID, intentar con email
        if email:
            email_key = f"email:{email.lower().strip()}"
            if email_key in self.moderadores_additional_data:
                return self.moderadores_additional_data[email_key]
        
        return {}
    
    def format_date_spanish(self, fecha_raw):
        """Formatear fecha en español con formato Dom, 14/07/2025 13:20:32"""
        if not fecha_raw or fecha_raw == 'No especificada':
            return 'No especificada'
        
        try:
            # Diccionario de días en español
            dias_espanol = {
                'Monday': 'Lun',
                'Tuesday': 'Mar', 
                'Wednesday': 'Mié',
                'Thursday': 'Jue',
                'Friday': 'Vie',
                'Saturday': 'Sáb',
                'Sunday': 'Dom'
            }
            
            # Si fecha_raw es un diccionario (respuesta de MongoDB), extraer el timestamp
            if isinstance(fecha_raw, dict) and '$date' in fecha_raw:
                timestamp = fecha_raw['$date']
                if isinstance(timestamp, (int, float)):
                    # Timestamp en milisegundos, convertir a segundos
                    fecha = datetime.fromtimestamp(timestamp / 1000)
                else:
                    # Probablemente string ISO
                    fecha = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(fecha_raw, str):
                # Intentar parsear diferentes formatos de string
                try:
                    # Formato GMT: "Sun, 14 Sep 2025 17:20:32 GMT"
                    if fecha_raw.endswith(' GMT'):
                        from datetime import datetime, timedelta
                        fecha_utc = datetime.strptime(fecha_raw, "%a, %d %b %Y %H:%M:%S GMT")
                        # Convertir de UTC a hora de Venezuela (UTC-4)
                        fecha = fecha_utc - timedelta(hours=4)
                    # ISO format with Z
                    elif 'T' in fecha_raw and fecha_raw.endswith('Z'):
                        fecha = datetime.fromisoformat(fecha_raw.replace('Z', '+00:00'))
                    # ISO format standard
                    elif 'T' in fecha_raw:
                        fecha = datetime.fromisoformat(fecha_raw)
                    else:
                        # Fallback genérico
                        fecha = datetime.fromisoformat(fecha_raw)
                except:
                    return fecha_raw  # Si no se puede parsear, devolver como está
            else:
                # Si es datetime object directamente
                fecha = fecha_raw
            
            # Formatear en español: Dom, 14/07/2025 13:20:32
            dia_ingles = fecha.strftime('%A')
            dia_espanol = dias_espanol.get(dia_ingles, dia_ingles[:3])
            fecha_formateada = fecha.strftime(f"{dia_espanol}, %d/%m/%Y %H:%M:%S")
            
            return fecha_formateada
            
        except Exception as e:
            print(f"Error formateando fecha: {e}, fecha_raw: {fecha_raw}")
            return str(fecha_raw)  # En caso de error, devolver como string

    def remove_moderador_from_view(self, cedula):
        """PASO 6: Eliminar moderador de la vista instantáneamente"""
        print(f"🗂️ PASO 6: Eliminando moderador con cédula '{cedula}' de la vista")
        
        try:
            # Verificar que tenemos la lista de moderadores
            if not hasattr(self, 'moderadores_list'):
                print("⚠️ No se encontró la lista de moderadores")
                return
            
            print(f"📋 Total de items en lista: {len(self.moderadores_list.children)}")
            
            # Buscar y eliminar el item de la lista que coincida con la cédula
            items_to_remove = []
            items_checked = 0
            
            for child in self.moderadores_list.children:
                items_checked += 1
                print(f"🔍 Revisando item #{items_checked}: {type(child).__name__}")
                
                # Verificar si el item tiene datos del moderador
                if hasattr(child, 'moderador_data'):
                    child_cedula = child.moderador_data.get('cedula', '')
                    print(f"✅ Item tiene moderador_data - Cédula: '{child_cedula}'")
                    print(f"🔍 Comparando: '{child_cedula}' == '{cedula}'")
                    if str(child_cedula) == str(cedula):
                        items_to_remove.append(child)
                        print(f"🎯 ¡MATCH! Encontrado item a eliminar: {child.text}")
                else:
                    print(f"⚠️ Item no tiene moderador_data: {getattr(child, 'text', 'Sin texto')}")
            
            print(f"📊 Items revisados: {items_checked}, Items a eliminar: {len(items_to_remove)}")
            
            # Remover los items encontrados
            for item in items_to_remove:
                print(f"🗑️ Eliminando item de la vista: {item.text}")
                self.moderadores_list.remove_widget(item)
            
            print(f"📋 Items restantes después de eliminación: {len(self.moderadores_list.children)}")
            
            # Si no hay más moderadores, mostrar mensaje
            if len(self.moderadores_list.children) == 0:
                no_data_item = OneLineListItem(
                    text="No hay moderadores registrados",
                )
                no_data_item.theme_text_color = "Secondary"
                self.moderadores_list.add_widget(no_data_item)
                print("📋 Lista vacía - agregado mensaje 'No hay moderadores'")
            
            if len(items_to_remove) > 0:
                print(f"✅ PASO 6 COMPLETADO: {len(items_to_remove)} moderador(es) eliminado(s) de la vista")
            else:
                print(f"⚠️ PASO 6: No se encontró moderador con cédula '{cedula}' para eliminar de vista")
            
        except Exception as e:
            print(f"❌ Error en remove_moderador_from_view: {e}")
            import traceback
            print(f"📍 Traceback: {traceback.format_exc()}")

    def show_delete_success_message(self, nombre, apellidos):
        """PASO 7: Mostrar mensaje de éxito y direccionar a lista de moderadores"""
        print(f"🎉 PASO 7: Mostrando mensaje de éxito para {nombre} {apellidos}")
        
        try:
            # Cerrar cualquier dialog que esté abierto
            if hasattr(self, 'moderador_details_dialog') and self.moderador_details_dialog:
                self.moderador_details_dialog.dismiss()
            
            # Crear dialog de éxito
            nombre_completo = f"{nombre} {apellidos}".strip()
            mensaje_exito = f"✅ Moderador eliminado exitosamente\n\n👤 {nombre_completo}\n\nHa sido eliminado del sistema"
            
            self.success_delete_dialog = MDDialog(
                title="🗑️ Eliminación Exitosa",
                text=mensaje_exito,
                buttons=[
                    MDRaisedButton(
                        text="ACEPTAR",
                        md_bg_color=[0.2, 0.7, 0.2, 1],  # Verde éxito
                        on_release=lambda x: self.redirect_to_moderadores_list()
                    )
                ]
            )
            self.success_delete_dialog.open()
            print(f"✅ PASO 7 COMPLETADO: Dialog de éxito mostrado")
            
        except Exception as e:
            print(f"❌ Error en show_delete_success_message: {e}")
            import traceback
            print(f"📍 Traceback: {traceback.format_exc()}")
            # Fallback: direccionar directamente a la lista
            self.redirect_to_moderadores_list()

    def redirect_to_moderadores_list(self):
        """Cerrar dialog de éxito y direccionar a lista de moderadores"""
        print(f"🔄 Direccionando a lista de moderadores")
        
        try:
            # Cerrar dialog de éxito
            if hasattr(self, 'success_delete_dialog') and self.success_delete_dialog:
                self.success_delete_dialog.dismiss()
            
            # Direccionar a la pantalla de lista de moderadores
            self.screen_manager.current = "lista_moderadores"
            print(f"✅ Direccionado exitosamente a lista_moderadores")
            
        except Exception as e:
            print(f"❌ Error redirigiendo: {e}")
            import traceback
            print(f"📍 Traceback: {traceback.format_exc()}")

    # ==================== FUNCIONES DE OBREROS ====================

    def load_obreros_data(self):
        """Cargar datos de obreros desde la API"""
        self.obreros_list.clear_widgets()

        # Indicador de carga
        loading_item = OneLineListItem(text="🔄 Cargando obreros...")
        self.obreros_list.add_widget(loading_item)

        try:
            response = requests.get(f"{API_BASE_URL}/api/personnel/obreros/", timeout=10)
            self.obreros_list.clear_widgets()

            if response.status_code == 200:
                data = response.json()
                obreros = data.get('obreros', [])

                if not obreros:
                    no_obreros_item = OneLineListItem(
                        text="📝 No hay obreros registrados. Agrega uno usando el botón +"
                    )
                    self.obreros_list.add_widget(no_obreros_item)
                else:
                    for obrero in obreros:
                        nombre = obrero.get('nombre', 'N/A')
                        apellidos = obrero.get('apellidos', 'N/A')
                        nombre_completo = f"{nombre} {apellidos}"
                        email = obrero.get('email', 'N/A')
                        telefono = obrero.get('telefono', 'N/A')

                        obrero_item = self.create_obrero_list_item(
                            nombre_completo=nombre_completo,
                            correo=email,
                            telefono=telefono,
                            obrero_data=obrero
                        )
                        self.obreros_list.add_widget(obrero_item)
            else:
                error_item = OneLineListItem(text=f"❌ Error del servidor: {response.status_code}")
                self.obreros_list.add_widget(error_item)

        except requests.exceptions.Timeout:
            self.show_error_obreros("⏱️ Timeout: El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_error_obreros("🌐 Error de conexión: Verifica tu conexión a internet")
        except Exception as e:
            self.show_error_obreros(f"⚠️ Error inesperado: {str(e)}")

    def show_error_obreros(self, message):
        """Mostrar error en la lista de obreros"""
        self.obreros_list.clear_widgets()
        error_item = OneLineListItem(text=message)
        self.obreros_list.add_widget(error_item)

        retry_item = OneLineListItem(
            text="🔄 Reintentar",
            on_release=lambda x: self.load_obreros_data()
        )
        self.obreros_list.add_widget(retry_item)

    def create_obrero_list_item(self, nombre_completo, correo, telefono, obrero_data):
        """Crear item de lista para obrero"""
        # Usar TwoLineListItem para mostrar información
        item = TwoLineListItem(
            text=f"👷 {nombre_completo}",
            secondary_text=f"📧 {correo} | 📞 {telefono}",
            on_release=lambda x: self.show_obrero_details(obrero_data)
        )
        return item

    def show_obrero_details(self, obrero_data):
        """Mostrar detalles del obrero"""
        # Obtener campos individuales en lugar de concatenar
        nombre = obrero_data.get('nombre', 'Sin nombre')
        apellidos = obrero_data.get('apellidos', 'Sin apellidos')

        # Email (servidor devuelve 'email')
        correo = obrero_data.get('email', 'Sin email')

        # Información de contacto y personal
        cedula = obrero_data.get('cedula', 'No registrada')
        telefono = obrero_data.get('telefono', 'No ingresado')
        talla_ropa = obrero_data.get('talla_ropa', 'No ingresado')
        talla_zapatos = obrero_data.get('talla_zapatos', 'No ingresado')

        # Información del sistema
        nivel = obrero_data.get('nivel', 'obrero')
        activo = "Sí" if obrero_data.get('activo', False) else "No"
        fecha_creacion_raw = obrero_data.get('fecha_creacion', 'No especificada')
        creado_por = obrero_data.get('creado_por', 'No especificado')

        # Formatear fecha en español
        fecha_creacion = self.format_date_spanish(fecha_creacion_raw)

        # Formato profesional sin emojis (Estado omitido de la vista)
        detalles = f"Nombre: {nombre}\n"
        detalles += f"Apellidos: {apellidos}\n"
        detalles += f"Cédula: {cedula}\n"
        detalles += f"Email: {correo}\n"
        detalles += f"Teléfono: {telefono}\n\n"
        detalles += f"Talla de ropa: {talla_ropa}\n"
        detalles += f"Talla de zapatos: {talla_zapatos}\n\n"
        detalles += f"Nivel: {nivel}\n"
        detalles += f"Creado: {fecha_creacion}\n"
        detalles += f"Creado por: {creado_por}"

        # Crear diálogo personalizado con botón de editar
        self.show_obrero_details_dialog(obrero_data, detalles)

    def show_obrero_details_dialog(self, obrero_data, detalles_text):
        """Mostrar diálogo de detalles con botón de editar"""
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton
        from kivymd.uix.label import MDLabel
        from kivymd.uix.widget import MDWidget

        # Crear contenedor principal que incluye el título personalizado
        main_content = MDBoxLayout(
            orientation="vertical",
            spacing="8dp",
            size_hint_y=None,
            padding=["0dp", "0dp", "0dp", "0dp"]  # Sin padding superior
        )
        main_content.bind(minimum_height=main_content.setter('height'))

        # Crear header personalizado con título y botón de editar
        header_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="60dp",  # Más alto para mejor alineación
            spacing="5dp",
            padding=["8dp", "8dp", "8dp", "8dp"]  # Padding uniforme
        )

        # Título del diálogo
        title_label = MDLabel(
            text="Detalles del Obrero",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_x=0.8,
            halign="left",
            valign="center",
            text_size=(None, None)
        )

        # Botón de editar
        edit_button = MDIconButton(
            icon="pencil",
            theme_icon_color="Primary",
            size_hint=(None, None),
            size=("28dp", "28dp"),
            pos_hint={"center_y": 0.5, "right": 1},
            on_release=lambda x: self.edit_obrero(obrero_data)
        )

        # Agregar título y botón al header
        header_layout.add_widget(title_label)
        header_layout.add_widget(edit_button)

        # Contenido de detalles
        details_label = MDLabel(
            text=detalles_text,
            theme_text_color="Primary",
            size_hint_y=None,
            halign="left",
            valign="top"
        )
        details_label.bind(texture_size=details_label.setter('size'))

        # Agregar header y contenido al contenedor principal
        main_content.add_widget(header_layout)
        main_content.add_widget(details_label)

        # Espaciador entre texto y botones
        spacer_vertical = MDWidget(size_hint_y=None, height="15dp")
        main_content.add_widget(spacer_vertical)

        # Crear layout personalizado para botones separados
        buttons_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="50dp",
            spacing="10dp",
            padding="10dp"
        )

        # Botón eliminar a la IZQUIERDA
        delete_button = MDIconButton(
            icon="delete",
            md_bg_color=[0.8, 0.2, 0.2, 1],  # Rojo para indicar peligro
            icon_color=[1, 1, 1, 1],  # Ícono blanco
            size_hint=(None, None),
            size=("40dp", "40dp"),
            on_release=lambda x: self.delete_obrero_confirmation(obrero_data)
        )

        # Espaciador que se expande para separar los botones
        spacer = MDWidget(size_hint=(1, 1))

        # Botón cerrar a la DERECHA
        close_button = MDRaisedButton(
            text="Cerrar",
            md_bg_color=[0.5, 0.5, 0.5, 1],  # Color gris
            size_hint=(None, None),
            width="80dp",
            height="36dp",
            on_release=lambda x: self.obrero_details_dialog.dismiss()
        )

        # Agregar botones al layout
        buttons_layout.add_widget(delete_button)
        buttons_layout.add_widget(spacer)
        buttons_layout.add_widget(close_button)
        main_content.add_widget(buttons_layout)

        # Crear el diálogo
        self.obrero_details_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=main_content,
            size_hint=(0.9, 0.7)
        )

        self.obrero_details_dialog.open()

    def show_create_obrero_dialog(self):
        """Mostrar dialog para crear nuevo obrero"""
        # Scroll para contenido extenso
        scroll_content = MDScrollView(size_hint_y=None, height="400dp")
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp", adaptive_height=True, padding="10dp")

        # Título
        title_label = MDLabel(
            text="Añadir Obrero",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp",
            halign="center"
        )

        # Campo Nombres (obligatorio, sin números)
        self.obrero_nombre_input = MDTextField(
            hint_text="Nombres *",
            required=True,
            helper_text="Solo letras, sin números",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter=lambda text, from_undo: ''.join([c for c in text if not c.isdigit()])
        )

        # Campo Apellidos (obligatorio, sin números)
        self.obrero_apellidos_input = MDTextField(
            hint_text="Apellidos *",
            required=True,
            helper_text="Solo letras, sin números",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter=lambda text, from_undo: ''.join([c for c in text if not c.isdigit()])
        )

        # Campo Cédula (obligatorio)
        self.obrero_cedula_input = MDTextField(
            hint_text="Cédula de Identidad *",
            required=True,
            helper_text="Solo números, mín. 6, máx. 10 dígitos",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter="int",
            max_text_length=10
        )

        # Campo Correo (obligatorio, formato email)
        self.obrero_email_input = MDTextField(
            hint_text="Correo Electrónico *",
            required=True,
            helper_text="Debe contener @ y dominio (ej: usuario@gmail.com)",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )

        # Campo Teléfono (obligatorio)
        self.obrero_telefono_input = MDTextField(
            hint_text="Número de Teléfono *",
            required=True,
            helper_text="Ingrese un teléfono válido (mín. 10 dígitos)",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )

        # Campos opcionales
        opcional_label = MDLabel(
            text="Campos Opcionales:",
            theme_text_color="Secondary",
            font_size="14sp",
            size_hint_y=None,
            height="30dp"
        )

        # Campo Talla de Ropa (opcional) - BOTÓN SELECTOR
        self.obrero_talla_ropa_field = MDRaisedButton(
            text="Seleccionar Talla de Ropa (opcional)",
            md_bg_color=[0.95, 0.95, 0.95, 1],  # Gris claro como campo
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp",
            on_release=self.open_talla_ropa_dropdown_obrero
        )

        # Variable para guardar la talla seleccionada (ya que no es un TextField)
        self.selected_talla_text_obrero = ""

        # Campo Talla de Zapatos (opcional) con validación 30-50
        self.obrero_talla_zapatos_input = MDTextField(
            hint_text="Talla de Zapatos (opcional)",
            helper_text="Solo números del 30 al 50",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )

        # Agregar campos al layout
        content_layout.add_widget(title_label)
        content_layout.add_widget(self.obrero_nombre_input)
        content_layout.add_widget(self.obrero_apellidos_input)
        content_layout.add_widget(self.obrero_cedula_input)
        content_layout.add_widget(self.obrero_email_input)
        content_layout.add_widget(self.obrero_telefono_input)
        content_layout.add_widget(opcional_label)
        content_layout.add_widget(self.obrero_talla_ropa_field)
        content_layout.add_widget(self.obrero_talla_zapatos_input)

        scroll_content.add_widget(content_layout)

        # Crear el dialog
        self.create_obrero_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=scroll_content,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],
                    on_release=self.cancel_obrero_dialog
                ),
                MDRaisedButton(
                    text="GUARDAR",
                    md_bg_color=[0.2, 0.6, 1, 1],
                    on_release=self.save_obrero
                )
            ],
            size_hint=(0.9, 0.8)
        )

        self.create_obrero_dialog.open()

    def open_talla_ropa_dropdown_obrero(self, instance=None):
        """Abrir dropdown para seleccionar talla de ropa (formulario crear obrero)"""
        menu_items = []
        for talla in self.TALLAS_ROPA:
            menu_items.append({
                "text": f"   {talla}   ",
                "viewclass": "OneLineListItem",
                "height": 40,
                "on_release": lambda x=talla: self.select_talla_ropa_obrero(x),
            })

        # Opción para dejar vacío
        menu_items.append({
            "text": "   (Ninguna)   ",
            "viewclass": "OneLineListItem",
            "height": 40,
            "on_release": lambda: self.select_talla_ropa_obrero_vacia(),
        })

        caller = instance or self.obrero_talla_ropa_field

        self.talla_ropa_dropdown_obrero = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=2,
            max_height=200,
            position="bottom",
        )

        self.talla_ropa_dropdown_obrero.open()

    def select_talla_ropa_obrero(self, talla):
        """Seleccionar talla de ropa (formulario crear obrero)"""
        self.selected_talla_ropa_obrero = talla
        self.obrero_talla_ropa_field.text = f"Talla Seleccionada: {talla}"

        if hasattr(self, 'talla_ropa_dropdown_obrero'):
            self.talla_ropa_dropdown_obrero.dismiss()

    def select_talla_ropa_obrero_vacia(self):
        """Dejar talla de ropa vacía (formulario crear obrero)"""
        self.selected_talla_ropa_obrero = ""
        self.obrero_talla_ropa_field.text = "Seleccionar Talla de Ropa (opcional)"

        if hasattr(self, 'talla_ropa_dropdown_obrero'):
            self.talla_ropa_dropdown_obrero.dismiss()

    def cancel_obrero_dialog(self, instance=None):
        """Cancelar creación de obrero"""
        if hasattr(self, 'create_obrero_dialog'):
            self.create_obrero_dialog.dismiss()
        self.clear_obrero_fields()

    def clear_obrero_fields(self):
        """Limpiar campos del formulario de obrero"""
        if hasattr(self, 'obrero_nombre_input'):
            self.obrero_nombre_input.text = ""
        if hasattr(self, 'obrero_apellidos_input'):
            self.obrero_apellidos_input.text = ""
        if hasattr(self, 'obrero_cedula_input'):
            self.obrero_cedula_input.text = ""
        if hasattr(self, 'obrero_email_input'):
            self.obrero_email_input.text = ""
        if hasattr(self, 'obrero_telefono_input'):
            self.obrero_telefono_input.text = ""
        if hasattr(self, 'obrero_talla_zapatos_input'):
            self.obrero_talla_zapatos_input.text = ""

        # Reset dropdown
        self.selected_talla_ropa_obrero = ""
        if hasattr(self, 'obrero_talla_ropa_field'):
            self.obrero_talla_ropa_field.text = "Seleccionar Talla de Ropa (opcional)"

    def save_obrero(self, instance=None):
        """Guardar nuevo obrero"""
        # Validar campos
        is_valid, error_message = self.validate_obrero_fields()
        if not is_valid:
            self.show_dialog("Error", error_message)
            return

        # Preparar datos
        talla_ropa = getattr(self, 'selected_talla_ropa_obrero', "") or ""
        talla_zapatos_raw = self.obrero_talla_zapatos_input.text.strip()

        # Validar talla de zapatos si se ingresó (igual que moderadores)
        if talla_zapatos_raw:
            try:
                talla_zapatos_num = int(talla_zapatos_raw)
                if not (30 <= talla_zapatos_num <= 50):
                    self.show_dialog("Error", "La talla de zapatos debe estar entre 30 y 50")
                    return
            except ValueError:
                self.show_dialog("Error", "La talla de zapatos debe ser un número válido")
                return

        try:
            data = {
                "nombre": self.obrero_nombre_input.text.strip(),
                "apellidos": self.obrero_apellidos_input.text.strip(),
                "cedula": self.obrero_cedula_input.text.strip(),
                "email": self.obrero_email_input.text.strip(),
                "telefono": self.obrero_telefono_input.text.strip(),
                "talla_ropa": talla_ropa,
                "talla_zapatos": talla_zapatos_raw
            }

            response = requests.post(
                f"{API_BASE_URL}/api/personnel/obreros/",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code in [200, 201]:
                self.create_obrero_dialog.dismiss()
                self.clear_obrero_fields()
                self.show_dialog("¡Éxito!", "Obrero registrado exitosamente")
                self.load_obreros_data()  # Recargar lista
            elif response.status_code == 400:
                error_data = response.json()
                self.show_dialog("Error", error_data.get("error", "Error al registrar obrero"))
            else:
                self.show_dialog("Error", f"Error del servidor: {response.status_code}")

        except requests.exceptions.Timeout:
            self.show_dialog("Error", "El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "No se pudo conectar al servidor")
        except Exception as e:
            self.show_dialog("Error", f"Error inesperado: {str(e)}")

    def validate_obrero_fields(self):
        """Validar campos del obrero"""
        # Validación nombre
        if not self.obrero_nombre_input.text.strip():
            return False, "El nombre es obligatorio"

        if any(char.isdigit() for char in self.obrero_nombre_input.text):
            return False, "El nombre no puede contener números"

        # Validación apellidos
        if not self.obrero_apellidos_input.text.strip():
            return False, "Los apellidos son obligatorios"

        if any(char.isdigit() for char in self.obrero_apellidos_input.text):
            return False, "Los apellidos no pueden contener números"

        # Validación cédula
        cedula = self.obrero_cedula_input.text.strip()
        if not cedula:
            return False, "La cédula es obligatoria"

        if len(cedula) < 6 or len(cedula) > 10:
            return False, "La cédula debe tener entre 6 y 10 dígitos"

        # Validación email
        email = self.obrero_email_input.text.strip()
        if not email:
            return False, "El email es obligatorio"

        if '@' not in email:
            return False, "El email debe contener el símbolo '@' (ejemplo: usuario@gmail.com)"

        if '.' not in email.split('@')[-1]:
            return False, "El dominio debe contener al menos un punto (ejemplo: @gmail.com)"

        # Validación teléfono
        telefono = self.obrero_telefono_input.text.strip()
        if not telefono:
            return False, "El teléfono es obligatorio"

        if len(telefono) < 10:
            return False, "Ingrese un teléfono válido (mín. 10 dígitos)"

        return True, ""


    def edit_obrero(self, obrero_data):
        """Iniciar edición de obrero"""
        if hasattr(self, 'obrero_details_dialog'):
            self.obrero_details_dialog.dismiss()
        self.show_edit_obrero_dialog(obrero_data)

    def delete_obrero_confirmation(self, obrero_data):
        """Función llamada cuando se presiona el botón de eliminar - PASO 2: Primer confirmación"""
        # Cerrar dialog de detalles primero
        if hasattr(self, 'obrero_details_dialog'):
            self.obrero_details_dialog.dismiss()

        # Obtener datos del obrero para el mensaje
        nombre = obrero_data.get('nombre', '')
        apellidos = obrero_data.get('apellidos', '')
        cedula = obrero_data.get('cedula', '')

        # Mensaje de confirmación personalizado
        mensaje_confirmacion = f"¿Seguro desea eliminar al obrero:\n\n{nombre} {apellidos}\nCédula: {cedula}"

        # Crear primer dialog de confirmación
        self.first_delete_dialog_obrero = MDDialog(
            title="Confirmar Eliminación",
            text=mensaje_confirmacion,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],  # Gris
                    on_release=lambda x: self.cancel_delete_obrero()
                ),
                MDRaisedButton(
                    text="ELIMINAR",
                    md_bg_color=[0.8, 0.2, 0.2, 1],  # Rojo
                    on_release=lambda x: self.show_second_delete_confirmation_obrero(obrero_data)
                )
            ]
        )
        self.first_delete_dialog_obrero.open()

    def cancel_delete_obrero(self):
        """Cancelar eliminación de obrero y volver a lista"""
        # Cerrar dialog de confirmación
        if hasattr(self, 'first_delete_dialog_obrero'):
            self.first_delete_dialog_obrero.dismiss()
        if hasattr(self, 'second_delete_dialog_obrero'):
            self.second_delete_dialog_obrero.dismiss()
        # Ya estamos en la lista de obreros, no necesitamos navegar

    def show_second_delete_confirmation_obrero(self, obrero_data):
        """Mostrar segundo mensaje de confirmación - PASO 3: Confirmación irreversible"""
        # Cerrar primer dialog
        if hasattr(self, 'first_delete_dialog_obrero'):
            self.first_delete_dialog_obrero.dismiss()

        # Obtener datos del obrero para el mensaje
        nombre = obrero_data.get('nombre', '')
        apellidos = obrero_data.get('apellidos', '')

        # Mensaje de advertencia irreversible
        mensaje_irreversible = f"⚠️ ADVERTENCIA ⚠️\n\nEsta acción es IRREVERSIBLE.\n\nEl obrero {nombre} {apellidos} será eliminado permanentemente del sistema.\n\n¿Está completamente seguro?"

        # Crear segundo dialog de confirmación (más severo)
        self.second_delete_dialog_obrero = MDDialog(
            title="⚠️ ACCIÓN IRREVERSIBLE",
            text=mensaje_irreversible,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],  # Gris
                    on_release=lambda x: self.cancel_delete_obrero()
                ),
                MDRaisedButton(
                    text="CONFIRMAR",
                    md_bg_color=[0.9, 0.1, 0.1, 1],  # Rojo más intenso
                    on_release=lambda x: self.execute_delete_obrero(obrero_data)
                )
            ]
        )
        self.second_delete_dialog_obrero.open()

    def execute_delete_obrero(self, obrero_data):
        """Ejecutar eliminación definitiva del obrero"""
        # Cerrar segundo dialog
        if hasattr(self, 'second_delete_dialog_obrero'):
            self.second_delete_dialog_obrero.dismiss()

        try:

            delete_data = {"cedula": obrero_data.get('cedula')}

            response = requests.delete(
                f"{API_BASE_URL}/api/personnel/obreros/",
                json=delete_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                self.load_obreros_data()  # Recargar lista
                self.show_delete_success_message_obrero()
            elif response.status_code == 404:
                self.show_dialog("Error", "No se encontró el obrero para eliminar")
            else:
                error_data = response.json()
                self.show_dialog("Error", error_data.get("error", "Error al eliminar obrero"))

        except requests.exceptions.Timeout:
            self.show_dialog("Error", "El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "No se pudo conectar al servidor")
        except Exception as e:
            self.show_dialog("Error", f"Error inesperado: {str(e)}")

    def show_delete_success_message_obrero(self):
        """Mostrar mensaje de éxito al eliminar obrero"""
        self.success_delete_dialog_obrero = MDDialog(
            title="¡Éxito!",
            text="Obrero eliminado exitosamente",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    md_bg_color=[0.2, 0.6, 1, 1],
                    on_release=lambda x: self.success_delete_dialog_obrero.dismiss()
                )
            ]
        )
        self.success_delete_dialog_obrero.open()

    def show_edit_obrero_dialog(self, obrero_data):
        """Mostrar ventana flotante para editar obrero - BASADA EN show_edit_moderador_dialog()"""
        # Guardar referencia del obrero actual
        self.current_obrero_cedula = obrero_data.get('cedula')

        # Verificar que tenemos los datos del obrero
        if not obrero_data:
            return

        # ESTRUCTURA IDÉNTICA A show_edit_moderador_dialog() PERO CON CAMPOS PRELLENADOS

        # Scroll para contenido extenso (IGUAL QUE MODERADORES)
        scroll_content = MDScrollView(size_hint_y=None, height="400dp")
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp", adaptive_height=True, padding="10dp")

        # Título (ADAPTADO PARA EDITAR OBRERO)
        title_label = MDLabel(
            text="Editar Obrero",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp",
            halign="center"
        )

        # Campo Nombres (obligatorio, PRELLENADO, sin números)
        self.edit_obrero_nombre_input = MDTextField(
            text=str(obrero_data.get('nombre', '')),
            hint_text="Nombres *",
            required=True,
            helper_text="Solo letras, sin números",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter=lambda text, from_undo: ''.join([c for c in text if not c.isdigit()])
        )

        # Campo Apellidos (obligatorio, PRELLENADO, sin números)
        self.edit_obrero_apellidos_input = MDTextField(
            text=str(obrero_data.get('apellidos', '')),
            hint_text="Apellidos *",
            required=True,
            helper_text="Solo letras, sin números",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter=lambda text, from_undo: ''.join([c for c in text if not c.isdigit()])
        )

        # Campo Cédula (obligatorio, PRELLENADO)
        self.edit_obrero_cedula_input = MDTextField(
            text=str(obrero_data.get('cedula', '')),
            hint_text="Cédula de Identidad *",
            required=True,
            helper_text="Solo números, mín. 6, máx. 10 dígitos",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp",
            input_filter="int",
            max_text_length=10
        )

        # Campo Correo (obligatorio, PRELLENADO, formato email)
        self.edit_obrero_email_input = MDTextField(
            text=str(obrero_data.get('email', '')),
            hint_text="Correo Electrónico *",
            required=True,
            helper_text="Debe contener @ y dominio (ej: usuario@gmail.com)",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="60dp"
        )

        # Campo Teléfono (obligatorio, PRELLENADO)
        self.edit_obrero_telefono_input = MDTextField(
            text=str(obrero_data.get('telefono', '')),
            hint_text="Número de Teléfono *",
            required=True,
            helper_text="Solo números, mínimo 10 dígitos",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )

        # Campos opcionales
        opcional_label = MDLabel(
            text="Campos Opcionales:",
            theme_text_color="Secondary",
            font_size="14sp",
            size_hint_y=None,
            height="30dp"
        )

        # Campo Talla de Ropa (opcional) - BOTÓN SELECTOR IGUAL QUE MODERADORES
        talla_ropa_actual = obrero_data.get('talla_ropa', '')
        if talla_ropa_actual == 'No ingresado' or not talla_ropa_actual:
            self.selected_talla_ropa_obrero_edit = ""
            button_text = "Seleccionar Talla de Ropa (opcional)"
        else:
            self.selected_talla_ropa_obrero_edit = talla_ropa_actual
            button_text = f"Talla Seleccionada: {talla_ropa_actual}"

        self.edit_obrero_talla_ropa_field = MDRaisedButton(
            text=button_text,
            md_bg_color=[0.95, 0.95, 0.95, 1],
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp",
            on_release=self.open_talla_ropa_dropdown_obrero_edit
        )

        # Campo Talla de Zapatos (opcional) con validación 30-50 IGUAL QUE MODERADORES
        talla_zapatos_actual = obrero_data.get('talla_zapatos', '')
        talla_zapatos_display = talla_zapatos_actual if talla_zapatos_actual != 'No ingresado' else ''

        self.edit_obrero_talla_zapatos_input = MDTextField(
            text=talla_zapatos_display,
            hint_text="Talla de Zapatos (opcional)",
            helper_text="Solo números del 30 al 50",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )

        # Agregar campos al layout IGUAL QUE MODERADORES
        content_layout.add_widget(title_label)
        content_layout.add_widget(self.edit_obrero_nombre_input)
        content_layout.add_widget(self.edit_obrero_apellidos_input)
        content_layout.add_widget(self.edit_obrero_cedula_input)
        content_layout.add_widget(self.edit_obrero_email_input)
        content_layout.add_widget(self.edit_obrero_telefono_input)
        content_layout.add_widget(opcional_label)
        content_layout.add_widget(self.edit_obrero_talla_ropa_field)
        content_layout.add_widget(self.edit_obrero_talla_zapatos_input)

        scroll_content.add_widget(content_layout)

        # Crear el dialog IGUAL QUE MODERADORES
        self.edit_obrero_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=scroll_content,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],
                    on_release=self.cancel_edit_obrero_dialog
                ),
                MDRaisedButton(
                    text="GUARDAR",
                    md_bg_color=[0.2, 0.6, 1, 1],
                    on_release=self.save_edit_obrero
                )
            ],
            size_hint=(0.9, 0.8)
        )

        self.edit_obrero_dialog.open()

    def open_talla_ropa_dropdown_obrero_edit(self, instance=None):
        """Abrir dropdown para seleccionar talla de ropa (formulario editar obrero)"""
        menu_items = []
        for talla in self.TALLAS_ROPA:
            menu_items.append({
                "text": f"   {talla}   ",
                "viewclass": "OneLineListItem",
                "height": 40,
                "on_release": lambda x=talla: self.select_talla_ropa_obrero_edit(x),
            })

        # Opción para dejar vacío
        menu_items.append({
            "text": "   (Ninguna)   ",
            "viewclass": "OneLineListItem",
            "height": 40,
            "on_release": lambda: self.select_talla_ropa_obrero_edit_vacia(),
        })

        caller = instance or self.edit_obrero_talla_ropa_field

        self.talla_ropa_dropdown_obrero_edit = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=2,
            max_height=200,
            position="bottom",
        )

        self.talla_ropa_dropdown_obrero_edit.open()

    def select_talla_ropa_obrero_edit(self, talla):
        """Seleccionar talla de ropa (formulario editar obrero)"""
        self.selected_talla_ropa_obrero_edit = talla
        self.edit_obrero_talla_ropa_field.text = f"Talla Seleccionada: {talla}"

        if hasattr(self, 'talla_ropa_dropdown_obrero_edit'):
            self.talla_ropa_dropdown_obrero_edit.dismiss()

    def select_talla_ropa_obrero_edit_vacia(self):
        """Dejar talla de ropa vacía (formulario editar obrero)"""
        self.selected_talla_ropa_obrero_edit = ""
        self.edit_obrero_talla_ropa_field.text = "Seleccionar Talla de Ropa (opcional)"

        if hasattr(self, 'talla_ropa_dropdown_obrero_edit'):
            self.talla_ropa_dropdown_obrero_edit.dismiss()

    def cancel_edit_obrero_dialog(self, instance=None):
        """Cancelar edición de obrero"""
        if hasattr(self, 'edit_obrero_dialog'):
            self.edit_obrero_dialog.dismiss()

    def save_edit_obrero(self, instance=None):
        """Guardar cambios del obrero"""
        # Validar campos
        is_valid, error_message = self.validate_edit_obrero_fields()
        if not is_valid:
            self.show_dialog("Error", error_message)
            return

        # Preparar datos
        talla_ropa = getattr(self, 'selected_talla_ropa_obrero_edit', "") or ""
        talla_zapatos_raw = self.edit_obrero_talla_zapatos_input.text.strip()

        # Validar talla de zapatos si se ingresó (igual que moderadores)
        if talla_zapatos_raw:
            try:
                talla_zapatos_num = int(talla_zapatos_raw)
                if not (30 <= talla_zapatos_num <= 50):
                    self.show_dialog("Error", "La talla de zapatos debe estar entre 30 y 50")
                    return
            except ValueError:
                self.show_dialog("Error", "La talla de zapatos debe ser un número válido")
                return

        try:
            data = {
                "cedula_original": self.current_obrero_cedula,
                "nombre": self.edit_obrero_nombre_input.text.strip(),
                "apellidos": self.edit_obrero_apellidos_input.text.strip(),
                "cedula": self.edit_obrero_cedula_input.text.strip(),
                "email": self.edit_obrero_email_input.text.strip(),
                "telefono": self.edit_obrero_telefono_input.text.strip(),
                "talla_ropa": talla_ropa,
                "talla_zapatos": talla_zapatos_raw
            }

            response = requests.put(
                f"{API_BASE_URL}/api/personnel/obreros/",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                # Cerrar dialog de edición
                if hasattr(self, 'edit_obrero_dialog'):
                    self.edit_obrero_dialog.dismiss()

                # Cerrar cualquier dialog de detalles que pueda estar abierto
                if hasattr(self, 'obrero_details_dialog'):
                    self.obrero_details_dialog.dismiss()

                # Mostrar mensaje de éxito
                self.show_dialog("Éxito", "Obrero actualizado exitosamente")

                # Navegar a lista de obreros y recargar datos
                self.show_lista_obreros()
                self.load_obreros_data()
            elif response.status_code == 400:
                error_data = response.json()
                self.show_dialog("Error", error_data.get("error", "Error al actualizar obrero"))
            else:
                self.show_dialog("Error", f"Error del servidor: {response.status_code}")

        except requests.exceptions.Timeout:
            self.show_dialog("Error", "El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "No se pudo conectar al servidor")
        except Exception as e:
            self.show_dialog("Error", f"Error inesperado: {str(e)}")

    def validate_edit_obrero_fields(self):
        """Validar campos del obrero en edición"""
        # Validación nombre
        if not self.edit_obrero_nombre_input.text.strip():
            return False, "El nombre es obligatorio"

        if any(char.isdigit() for char in self.edit_obrero_nombre_input.text):
            return False, "El nombre no puede contener números"

        # Validación apellidos
        if not self.edit_obrero_apellidos_input.text.strip():
            return False, "Los apellidos son obligatorios"

        if any(char.isdigit() for char in self.edit_obrero_apellidos_input.text):
            return False, "Los apellidos no pueden contener números"

        # Validación cédula
        cedula = self.edit_obrero_cedula_input.text.strip()
        if not cedula:
            return False, "La cédula es obligatoria"

        if len(cedula) < 6 or len(cedula) > 10:
            return False, "La cédula debe tener entre 6 y 10 dígitos"

        # Validación email
        email = self.edit_obrero_email_input.text.strip()
        if not email:
            return False, "El email es obligatorio"

        if '@' not in email:
            return False, "El email debe contener el símbolo '@' (ejemplo: usuario@gmail.com)"

        if '.' not in email.split('@')[-1]:
            return False, "El dominio debe contener al menos un punto (ejemplo: @gmail.com)"

        # Validación teléfono
        telefono = self.edit_obrero_telefono_input.text.strip()
        if not telefono:
            return False, "El teléfono es obligatorio"

        if len(telefono) < 10:
            return False, "Ingrese un teléfono válido (mín. 10 dígitos)"

        return True, ""

