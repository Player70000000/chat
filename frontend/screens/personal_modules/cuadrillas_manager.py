"""
Manager especializado para gestión de cuadrillas
CRUD completo, asignación de personal y FIX del dialog problemático
"""

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, ThreeLineListItem, OneLineListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import dp

from .api_client import api_client
from .validators import validators
from .utils import utils
from .ui_components import ui_components


class CuadrillaListItem(ThreeLineListItem):
    """Item de lista para mostrar cuadrillas"""

    def __init__(self, cuadrilla_data, on_select_callback, **kwargs):
        super().__init__(**kwargs)

        # Datos de la cuadrilla
        self.cuadrilla_data = cuadrilla_data
        self.on_select_callback = on_select_callback

        # Configurar textos
        numero_cuadrilla = cuadrilla_data.get('numero_cuadrilla', 'Sin número')
        actividad = cuadrilla_data.get('actividad', 'Sin actividad')
        moderador = cuadrilla_data.get('moderador', {})
        moderador_nombre = f"{moderador.get('nombre', '')} {moderador.get('apellidos', '')}"
        num_obreros = len(cuadrilla_data.get('obreros', []))
        estado = 'Activa' if cuadrilla_data.get('activa', True) else 'Inactiva'

        self.text = f"🚧 {numero_cuadrilla} - {estado}"
        self.secondary_text = f"Actividad: {actividad}"
        self.tertiary_text = f"Moderador: {moderador_nombre} | Obreros: {num_obreros}"

        # Configurar callback
        self.on_release = self.select_cuadrilla

    def select_cuadrilla(self):
        """Seleccionar cuadrilla"""
        if self.on_select_callback:
            self.on_select_callback(self.cuadrilla_data)


class CuadrillasManager:
    """Manager para gestión completa de cuadrillas"""

    def __init__(self, main_screen=None):
        self.main_screen = main_screen
        self.cuadrillas_data = []
        self.moderadores_disponibles = []
        self.obreros_disponibles = []
        self.current_dialog = None

        # Referencias a campos de formulario
        self.actividad_field = None
        self.moderador_button = None
        self.obreros_container = None

        # Datos temporales para creación/edición
        self.selected_moderador = None
        self.selected_obreros = []
        self.editing_cuadrilla_id = None

    def get_screen(self):
        """Obtener pantalla principal de cuadrillas"""
        screen = MDScreen()
        screen.add_widget(self.create_main_layout())
        return screen

    def create_main_layout(self):
        """Crear layout principal de gestión de cuadrillas - ESTRUCTURA ORIGINAL"""
        layout = MDBoxLayout(orientation="vertical")

        # Toolbar
        toolbar = MDTopAppBar(
            title="Gestión de Cuadrillas",
            elevation=2,
            left_action_items=[["arrow-left", lambda x: self.go_back_to_main()]]
        )
        layout.add_widget(toolbar)

        # Card principal con botón y lista juntos (ESTRUCTURA ORIGINAL)
        cuadrillas_card = MDCard(
            elevation=1,
            padding="15dp"
        )

        card_content = MDBoxLayout(orientation="vertical", spacing="15dp")

        # Botón crear cuadrilla
        crear_button = MDRaisedButton(
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

        # Agregar componentes al card
        card_content.add_widget(crear_button)
        card_content.add_widget(lista_title)
        card_content.add_widget(self.cuadrillas_scroll)
        cuadrillas_card.add_widget(card_content)

        # Agregar card al layout principal
        layout.add_widget(cuadrillas_card)

        # Cargar datos iniciales
        Clock.schedule_once(lambda dt: self.load_cuadrillas_data(), 0)

        return layout

    def load_cuadrillas_data(self):
        """Cargar lista de cuadrillas desde API - ESTRUCTURA ORIGINAL"""
        try:
            print("🔄 Cargando cuadrillas...")

            # Limpiar lista actual
            if hasattr(self, 'cuadrillas_list'):
                self.cuadrillas_list.clear_widgets()

                # Mostrar indicador de carga
                from kivymd.uix.list import OneLineListItem
                loading_item = OneLineListItem(text="🔄 Cargando cuadrillas...")
                self.cuadrillas_list.add_widget(loading_item)

            # Cargar datos después de un momento
            Clock.schedule_once(self._load_cuadrillas_async, 0.1)

        except Exception as e:
            self.show_error_dialog(f"Error al cargar cuadrillas: {str(e)}")

    def _load_cuadrillas_async(self, dt):
        """Cargar cuadrillas de forma asíncrona - ESTRUCTURA ORIGINAL"""
        try:
            # Obtener datos de la API
            response = api_client.get_cuadrillas()
            self.cuadrillas_data = response.get('cuadrillas', [])  # ← CORRECCIÓN: 'cuadrillas' no 'data'
            print(f"🔍 DEBUG: Respuesta API = {len(self.cuadrillas_data)} cuadrillas encontradas")

            # Limpiar lista
            self.cuadrillas_list.clear_widgets()

            if not self.cuadrillas_data:
                # Mostrar estado vacío en la lista
                from kivymd.uix.list import OneLineListItem
                no_cuadrillas_item = OneLineListItem(
                    text="📝 No hay cuadrillas registradas. Crea una usando el botón +"
                )
                self.cuadrillas_list.add_widget(no_cuadrillas_item)
            else:
                # Agregar cuadrillas a la lista
                for cuadrilla in self.cuadrillas_data:
                    cuadrilla_item = CuadrillaListItem(
                        cuadrilla_data=cuadrilla,
                        on_select_callback=self.on_cuadrilla_selected
                    )
                    self.cuadrillas_list.add_widget(cuadrilla_item)

            print(f"✅ {len(self.cuadrillas_data)} cuadrillas cargadas")

        except Exception as e:
            self.cuadrillas_list.clear_widgets()
            from kivymd.uix.list import OneLineListItem
            error_item = OneLineListItem(text=f"⚠️ Error: {str(e)}")
            retry_item = OneLineListItem(
                text="🔄 Reintentar",
                on_release=lambda x: self.load_cuadrillas_data()
            )
            self.cuadrillas_list.add_widget(error_item)
            self.cuadrillas_list.add_widget(retry_item)
            print(f"❌ Error al cargar cuadrillas: {str(e)}")

    def on_cuadrilla_selected(self, cuadrilla_data):
        """Callback cuando se selecciona una cuadrilla - DIRECTO A DETALLES como en el backup original"""
        self.show_cuadrilla_details(cuadrilla_data)

    def show_cuadrilla_options(self, cuadrilla_data):
        """Mostrar opciones para cuadrilla seleccionada"""
        numero_cuadrilla = cuadrilla_data.get('numero_cuadrilla', 'Sin número')

        actions = [
            {
                'text': 'VER DETALLES',
                'color': utils.get_color('info'),
                'callback': lambda x: self.show_cuadrilla_details(cuadrilla_data)
            },
            {
                'text': 'EDITAR',
                'color': utils.get_color('warning'),
                'callback': lambda x: self.show_edit_cuadrilla_dialog(cuadrilla_data)
            },
            {
                'text': 'ELIMINAR',
                'color': utils.get_color('error'),
                'callback': lambda x: self.confirm_delete_cuadrilla(cuadrilla_data)
            }
        ]

        action_buttons = ui_components.create_action_buttons(actions)

        dialog = MDDialog(
            title=f"🚧 {numero_cuadrilla}",
            text="Seleccione una acción:",
            type="custom",
            content_cls=action_buttons,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )

        dialog.open()

    def show_cuadrilla_details(self, cuadrilla_data):
        """Mostrar detalles completos de la cuadrilla - ESTRUCTURA EXACTA DEL BACKUP ORIGINAL"""
        # No hay dialog de opciones que cerrar, vamos directo a detalles
        numero = cuadrilla_data.get('numero_cuadrilla', 'N/A')
        actividad = cuadrilla_data.get('actividad', 'Sin actividad especificada')
        moderador = cuadrilla_data.get('moderador', {})
        obreros = cuadrilla_data.get('obreros', [])

        # Metadatos
        fecha_creacion_raw = cuadrilla_data.get('fecha_creacion', 'No especificada')
        creado_por = cuadrilla_data.get('creado_por', 'No especificado')

        # Formatear fecha en español igual que moderadores y obreros
        fecha_creacion = utils.format_date_spanish(fecha_creacion_raw)

        # Crear texto de detalles completo
        detalles = f"Actividad: {actividad}\n\n"

        # Información del moderador
        detalles += f"Moderador:\n"
        detalles += f"   Nombre: {moderador.get('nombre', 'N/A')} {moderador.get('apellidos', 'N/A')}\n"
        detalles += f"   Cédula: {moderador.get('cedula', 'N/A')}\n\n"

        # Lista de obreros
        detalles += f"Obreros ({len(obreros)}):\n"
        for i, obrero in enumerate(obreros, 1):
            detalles += f"   {i}. {obrero.get('nombre', 'N/A')} {obrero.get('apellidos', 'N/A')} (CI: {obrero.get('cedula', 'N/A')})\n"

        # Información adicional
        detalles += f"\nInformación adicional:\n"
        detalles += f"   Creado: {fecha_creacion}\n"
        detalles += f"   Creado por: {creado_por}"

        # Crear diálogo personalizado con botón de eliminar igual que moderadores
        self.show_cuadrilla_details_dialog(cuadrilla_data, detalles, numero)

    def show_cuadrilla_details_dialog(self, cuadrilla_data, detalles_text, numero):
        """Mostrar diálogo de detalles con botón de eliminar igual que moderadores - ESTRUCTURA EXACTA"""
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
            text=f"Detalles - {numero}",
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
            on_release=lambda x: self.edit_cuadrilla_from_details(cuadrilla_data)
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
            on_release=lambda x: self.delete_cuadrilla_confirmation(cuadrilla_data)
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

        # Agregar layout de botones al contenido principal
        main_content.add_widget(buttons_layout)

        # Crear scroll para el contenido
        scroll_content = MDScrollView(size_hint_y=None, height="400dp")
        scroll_content.add_widget(main_content)

        # Crear diálogo SIN título (ya lo tenemos en el header personalizado)
        self.details_dialog = MDDialog(
            type="custom",
            content_cls=scroll_content,
            size_hint=(0.9, 0.8),
            auto_dismiss=True  # Permitir cerrar al hacer clic fuera
        )
        self.details_dialog.open()

    def edit_cuadrilla_from_details(self, cuadrilla_data):
        """Editar cuadrilla completa desde detalles - EN DESARROLLO"""
        numero = cuadrilla_data.get('numero_cuadrilla', 'Sin número')
        print(f"🚧 Función de editar cuadrilla en desarrollo: {numero}")

        # Cerrar diálogo actual
        if hasattr(self, 'details_dialog'):
            self.details_dialog.dismiss()

        # Mostrar mensaje de desarrollo
        utils.show_error_dialog(
            "🚧 En Desarrollo",
            f"La función de editar cuadrillas está en desarrollo.\n\nCuadrilla: {numero}\n\nPróximamente disponible."
        )

    def delete_cuadrilla_confirmation(self, cuadrilla_data):
        """Función llamada cuando se presiona el botón de eliminar - PASO 2: Primer confirmación"""
        print(f"🗑️ Iniciando eliminación de cuadrilla: {cuadrilla_data.get('numero_cuadrilla', 'Sin número')}")
        # Cerrar dialog de detalles primero
        if hasattr(self, 'details_dialog'):
            self.details_dialog.dismiss()

        # Obtener datos de la cuadrilla para el mensaje
        numero = cuadrilla_data.get('numero_cuadrilla', '')
        actividad = cuadrilla_data.get('actividad', '')
        num_obreros = cuadrilla_data.get('numero_obreros', 0)

        # Mensaje de confirmación personalizado
        mensaje_confirmacion = f"¿Seguro desea eliminar la cuadrilla:\n\n{numero}\nActividad: {actividad}\nObreros: {num_obreros}"
        print(f"📋 Mostrando primer mensaje de confirmación para: {numero}")

        # Crear primer dialog de confirmación
        self.first_delete_dialog = MDDialog(
            title="Confirmar Eliminación",
            text=mensaje_confirmacion,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],  # Gris
                    on_release=lambda x: self.cancel_delete_cuadrilla()
                ),
                MDRaisedButton(
                    text="ELIMINAR",
                    md_bg_color=[0.8, 0.2, 0.2, 1],  # Rojo
                    on_release=lambda x: self.show_final_delete_confirmation(cuadrilla_data)
                )
            ]
        )
        self.first_delete_dialog.open()

    def cancel_delete_cuadrilla(self):
        """Cancelar eliminación de cuadrilla"""
        print("❌ Eliminación cancelada por el usuario")
        if hasattr(self, 'first_delete_dialog'):
            self.first_delete_dialog.dismiss()

    def show_final_delete_confirmation(self, cuadrilla_data):
        """Mostrar confirmación final de eliminación - DOBLE CONFIRMACIÓN"""
        # Cerrar primer dialog
        if hasattr(self, 'first_delete_dialog'):
            self.first_delete_dialog.dismiss()

        numero = cuadrilla_data.get('numero_cuadrilla', '')
        mensaje_final = f"⚠️ ÚLTIMA CONFIRMACIÓN ⚠️\n\nEsta acción es IRREVERSIBLE.\n\nEliminará permanentemente la cuadrilla: {numero}"

        # Dialog final con advertencia severa
        self.final_delete_dialog = MDDialog(
            title="⚠️ ACCIÓN IRREVERSIBLE ⚠️",
            text=mensaje_final,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],  # Gris
                    on_release=lambda x: self.cancel_final_delete()
                ),
                MDRaisedButton(
                    text="SÍ, ELIMINAR",
                    md_bg_color=[0.9, 0.1, 0.1, 1],  # Rojo más intenso
                    on_release=lambda x: self.execute_delete_cuadrilla(cuadrilla_data)
                )
            ]
        )
        self.final_delete_dialog.open()

    def cancel_final_delete(self):
        """Cancelar eliminación final"""
        print("❌ Eliminación final cancelada")
        if hasattr(self, 'final_delete_dialog'):
            self.final_delete_dialog.dismiss()

    def execute_delete_cuadrilla(self, cuadrilla_data):
        """Ejecutar eliminación definitiva de cuadrilla"""
        # Cerrar dialog final
        if hasattr(self, 'final_delete_dialog'):
            self.final_delete_dialog.dismiss()

        numero = cuadrilla_data.get('numero_cuadrilla', '')
        cuadrilla_id = cuadrilla_data.get('_id', '')

        print(f"🗑️ Ejecutando eliminación de cuadrilla {numero} (ID: {cuadrilla_id})")

        try:
            # Llamar a la API para eliminar
            response = api_client.delete_cuadrilla(cuadrilla_id)

            if response and response.get('success'):
                print(f"✅ Cuadrilla {numero} eliminada exitosamente")
                # Recargar lista de cuadrillas
                self.load_cuadrillas_data()
                # Mostrar mensaje de éxito
                utils.show_success_dialog("Eliminación Exitosa", f"La cuadrilla {numero} fue eliminada correctamente.")
            else:
                error_msg = response.get('message', 'Error desconocido') if response else 'Sin respuesta del servidor'
                print(f"❌ Error eliminando cuadrilla: {error_msg}")
                utils.show_error_dialog("Error al Eliminar", f"No se pudo eliminar la cuadrilla:\n{error_msg}")

        except Exception as e:
            print(f"💥 Excepción eliminando cuadrilla: {e}")
            utils.show_error_dialog("Error Inesperado", f"Ocurrió un error inesperado:\n{str(e)}")


    def show_create_cuadrilla_dialog(self):
        """Mostrar ventana flotante para crear cuadrilla - ESTRUCTURA ORIGINAL COMPLETA"""
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
        # Capitalizar automáticamente la primera letra
        self.cuadrilla_actividad_field.bind(text=lambda instance, text: self.capitalize_first_letter(instance, text))

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

        # Agregar widgets al layout
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

    def show_cuadrillas_placeholder(self, instance=None):
        """Mostrar ventana flotante para crear cuadrilla"""
        self.show_create_cuadrilla_dialog()

    def get_next_cuadrilla_number(self):
        """Obtener el próximo número de cuadrilla automáticamente"""
        try:
            # Usar el endpoint específico del backend
            response = api_client.get_next_cuadrilla_number()
            return response.get('numero_cuadrilla', 'Cuadrilla-N°1')
        except Exception as e:
            # En caso de error, usar número por defecto
            print(f"Error obteniendo próximo número: {e}")
            return "Cuadrilla-N°1"

    def capitalize_first_letter(self, instance, text):
        """Capitalizar la primera letra del texto automáticamente"""
        if text and not text[0].isupper():
            instance.text = text[0].upper() + text[1:]

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
        """Abrir dropdown para seleccionar moderador de la lista existente - EXACTO AL ORIGINAL"""
        # Cargar moderadores desde API
        try:
            response = api_client.get_moderadores()
            moderadores = response.get('moderadores', [])

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

        except Exception as e:
            self.show_dialog("Error", f"Error cargando moderadores: {str(e)}")

    def select_moderador(self, moderador):
        """Seleccionar moderador para la cuadrilla - EXACTO AL ORIGINAL"""
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
        """Función que se ejecuta cuando cambia el número de obreros - EXACTO AL ORIGINAL"""
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

    def close_obrero_dropdown(self, index):
        """Cerrar dropdown de obrero si está abierto - FIX PARA BUG DE DROPDOWNS"""
        try:
            dropdown = self.campos_obreros[index].get('dropdown')
            if dropdown:
                dropdown.dismiss()
                self.campos_obreros[index]['dropdown'] = None
        except Exception as e:
            pass  # Silenciar errores de cierre

    def on_obrero_search(self, instance, value, index):
        """Búsqueda inteligente de obreros por cédula en tiempo real - EXACTO AL ORIGINAL"""
        try:
            # Obtener el campo de información correspondiente
            if index >= len(self.campos_obreros):
                return

            # VERIFICAR SI ESTÁ EN PROCESO DE SELECCIÓN - NO BUSCAR
            if self.campos_obreros[index].get('selecting', False):
                return

            info_label = self.campos_obreros[index]['info_label']

            # Si está vacío, restablecer Y CERRAR DROPDOWN
            if not value:
                info_label.text = "Ingrese cédula para buscar..."
                info_label.theme_text_color = "Secondary"
                self.campos_obreros[index]['obrero_data'] = None
                # FIX: Cerrar dropdown si está abierto
                self.close_obrero_dropdown(index)
                return

            # Mínimo 1 dígito para buscar
            if len(value) < 1:
                info_label.text = "Ingrese cédula para buscar..."
                info_label.theme_text_color = "Secondary"
                self.campos_obreros[index]['obrero_data'] = None
                # FIX: Cerrar dropdown si está abierto
                self.close_obrero_dropdown(index)
                return

            # Buscar obreros que coincidan con la cédula
            self.search_obreros_by_cedula(value, index)

        except Exception as e:
            print(f"Error en búsqueda de obreros: {e}")

    def search_obreros_by_cedula(self, cedula_partial, index):
        """Buscar obreros disponibles en la API que coincidan con la cédula parcial - EXACTO AL ORIGINAL"""
        try:
            # FIX: Cerrar dropdown anterior antes de nueva búsqueda
            self.close_obrero_dropdown(index)

            # Llamar a la API de obreros disponibles (no asignados a cuadrillas)
            response = api_client.get_obreros_disponibles()
            obreros = response.get('obreros', [])

            # Filtrar obreros que empiecen con la cédula parcial Y que no estén ya seleccionados
            matches = []
            for obrero in obreros:
                cedula = obrero.get('cedula', '')
                if cedula.startswith(cedula_partial):
                    # Verificar que no esté ya seleccionado en otro campo
                    if not self.is_obrero_already_selected(cedula, index):
                        matches.append(obrero)

            self.handle_search_results(matches, cedula_partial, index)

        except Exception as e:
            info_label = self.campos_obreros[index]['info_label']
            info_label.text = "❌ Error de conexión"
            info_label.theme_text_color = "Error"
            # FIX: Cerrar dropdown en caso de error
            self.close_obrero_dropdown(index)

    def is_obrero_already_selected(self, cedula, current_index):
        """Verificar si un obrero ya está seleccionado en otro campo - EXACTO AL ORIGINAL"""
        for i, campo in enumerate(self.campos_obreros):
            if i != current_index:  # No verificar el campo actual
                obrero_data = campo.get('obrero_data')
                if obrero_data and obrero_data.get('cedula') == cedula:
                    return True
        return False

    def handle_search_results(self, matches, cedula_partial, index):
        """Manejar los resultados de la búsqueda - EXACTO AL ORIGINAL"""
        info_label = self.campos_obreros[index]['info_label']

        if not matches:
            # No se encontraron coincidencias disponibles
            info_label.text = f"❌ No hay obreros disponibles con cédula que empiece por {cedula_partial}"
            info_label.theme_text_color = "Error"
            self.campos_obreros[index]['obrero_data'] = None
            # FIX: Cerrar dropdown si no hay coincidencias
            self.close_obrero_dropdown(index)
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
        """Mostrar dropdown con lista de obreros disponibles para seleccionar - EXACTO AL ORIGINAL"""
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

            # Crear dropdown con nombre único por campo y scroll mejorado
            dropdown_name = f"obreros_dropdown_{index}"

            # Calcular altura dinámica basada en número de items
            item_height = 50  # Altura de cada item
            padding = 20      # Padding adicional
            min_height = 100  # Altura mínima
            max_height = 300  # Altura máxima para permitir scroll

            calculated_height = len(menu_items) * item_height + padding
            dropdown_height = max(min_height, min(calculated_height, max_height))

            dropdown = MDDropdownMenu(
                caller=caller,
                items=menu_items,
                width_mult=4,
                max_height=dropdown_height,
                position="bottom"
            )

            # Guardar referencia al dropdown en el campo
            self.campos_obreros[index]['dropdown'] = dropdown
            dropdown.open()

        except Exception as e:
            print(f"Error mostrando dropdown de obreros: {e}")

    def select_obrero_from_dropdown(self, obrero, index):
        """Seleccionar obrero desde el dropdown - EXACTO AL ORIGINAL"""
        try:
            cedula = obrero.get('cedula', '')
            nombre = obrero.get('nombre', '')
            apellidos = obrero.get('apellidos', '')

            # MARCAR QUE ESTÁ EN PROCESO DE SELECCIÓN
            self.campos_obreros[index]['selecting'] = True

            # Actualizar campo de búsqueda con la cédula seleccionada
            busqueda_field = self.campos_obreros[index]['busqueda_field']
            busqueda_field.text = cedula

            # Actualizar información del obrero seleccionado
            info_label = self.campos_obreros[index]['info_label']
            info_label.text = f"✅ Seleccionado: {nombre} {apellidos}"
            info_label.theme_text_color = "Primary"

            # Guardar datos del obrero seleccionado
            self.campos_obreros[index]['obrero_data'] = obrero

            # Cerrar dropdown
            dropdown = self.campos_obreros[index].get('dropdown')
            if dropdown:
                dropdown.dismiss()
                self.campos_obreros[index]['dropdown'] = None

            # DESMARCAR PROCESO DE SELECCIÓN DESPUÉS DE UN BREVE DELAY
            def reset_selecting():
                if index < len(self.campos_obreros):
                    self.campos_obreros[index]['selecting'] = False

            # Usar Clock para delay mínimo
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: reset_selecting(), 0.1)

        except Exception as e:
            print(f"Error seleccionando obrero: {e}")
            # Asegurar reset del flag en caso de error
            if index < len(self.campos_obreros):
                self.campos_obreros[index]['selecting'] = False

    def save_cuadrilla(self, instance=None):
        """Guardar nueva cuadrilla conectada con API real - FUNCIONALIDAD ORIGINAL COMPLETA"""
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
            response = api_client.create_cuadrilla(cuadrilla_data)

            # Éxito
            numero_cuadrilla = response.get('cuadrilla', {}).get('numero_cuadrilla', 'N/A')

            self.cuadrilla_dialog.dismiss()
            self.show_dialog("¡Éxito!", f"Cuadrilla {numero_cuadrilla} creada exitosamente")
            self.load_cuadrillas_data()  # Recargar lista

        except Exception as e:
            self.show_dialog("Error", f"Error al crear cuadrilla: {str(e)}")
        finally:
            # Rehabilitar botón
            if instance:
                instance.disabled = False
                instance.text = "GUARDAR"

    # ==========================================
    # FUNCIONES DE EDICIÓN - COMENTADAS (EN DESARROLLO)
    # ==========================================

    """
    def show_edit_cuadrilla_dialog(self, cuadrilla_data):
        # Mostrar dialog para editar cuadrilla - CON FIX DEL PROBLEMA DE LAYOUT
        self.editing_cuadrilla_id = cuadrilla_data.get('_id')
        self.selected_moderador = cuadrilla_data.get('moderador', {})
        self.selected_obreros = cuadrilla_data.get('obreros', [])

        self._load_personal_data_for_form(lambda: self._show_edit_cuadrilla_fixed_dialog(cuadrilla_data))
    """

    """
    def _show_edit_cuadrilla_fixed_dialog(self, cuadrilla_data):
        # NUEVO DIALOG DE EDICIÓN - ESTRUCTURA AVANZADA PASO A PASO
        try:
            print("🎨 Creando nueva estructura de edición de cuadrillas...")

            # Extraer datos iniciales
            numero_cuadrilla = cuadrilla_data.get('numero_cuadrilla', 'N/A')
            actividad_actual = cuadrilla_data.get('actividad', '')
            moderador_actual = cuadrilla_data.get('moderador', {})
            self.current_obreros = cuadrilla_data.get('obreros', [])

            # Crear scroll view con tamaño controlado
            main_scroll = MDScrollView(
                size_hint_y=None,
                height="450dp"  # Altura fija más pequeña
            )

            main_container = MDBoxLayout(
                orientation="vertical",
                size_hint_y=None,
                spacing="15dp",
                padding="20dp"
            )
            main_container.bind(minimum_height=main_container.setter('height'))

            # === SECCIÓN 1: INFORMACIÓN BÁSICA ===
            # Campo Actividad
            self.actividad_field = MDTextField(
                text=actividad_actual,
                hint_text="Actividad de la cuadrilla",
                size_hint_y=None,
                height="56dp",
                mode="line"
            )
            main_container.add_widget(self.actividad_field)

            # Botón Moderador
            moderador_nombre = f"{moderador_actual.get('nombre', '')} {moderador_actual.get('apellidos', '')}"
            if not moderador_nombre.strip():
                moderador_nombre = "Seleccionar moderador"

            self.moderador_button = MDRaisedButton(
                text=f"👤 {moderador_nombre}",
                size_hint_y=None,
                height="50dp",
                md_bg_color=utils.get_color('secondary'),
                on_release=lambda x: self._open_moderador_dropdown()
            )
            main_container.add_widget(self.moderador_button)

            # === SECCIÓN 2: CONTADOR Y TÍTULO DE OBREROS ===
            # Header de obreros con contador
            obreros_header = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="60dp",
                spacing="10dp"
            )

            # Título con contador
            self.obreros_title = MDLabel(
                text=f"📋 OBREROS ({len(self.current_obreros)}/40)",
                theme_text_color="Primary",
                font_style="H6",
                size_hint_x=0.7,
                halign="left"
            )

            # Label de límites
            self.limits_label = MDLabel(
                text="Min: 4 | Max: 40",
                theme_text_color="Secondary",
                font_style="Caption",
                size_hint_x=0.3,
                halign="right"
            )

            obreros_header.add_widget(self.obreros_title)
            obreros_header.add_widget(self.limits_label)
            main_container.add_widget(obreros_header)

            # === SECCIÓN 3: LISTA DE OBREROS CON CHECKBOXES ===
            # Contenedor para lista de obreros
            self.obreros_container = MDBoxLayout(
                orientation="vertical",
                size_hint_y=None,
                spacing="8dp"
            )
            self.obreros_container.bind(minimum_height=self.obreros_container.setter('height'))

            # Crear lista de obreros con checkboxes
            self._create_obreros_with_checkboxes()

            main_container.add_widget(self.obreros_container)

            # === SECCIÓN 4: AGREGAR OBREROS DINÁMICAMENTE ===
            # Label de sección
            add_section_label = MDLabel(
                text="➕ Agregar Obreros Nuevos",
                theme_text_color="Primary",
                font_style="Subtitle1",
                size_hint_y=None,
                height="40dp"
            )
            main_container.add_widget(add_section_label)

            # Campo numérico para cantidad de obreros a agregar
            self.nuevos_obreros_field = MDTextField(
                hint_text="¿Cuántos obreros desea agregar? (1-10)",
                input_filter="int",
                size_hint_y=None,
                height="56dp",
                mode="line"
            )
            # Conectar manualmente el callback
            self.nuevos_obreros_field.bind(text=self.on_nuevos_obreros_change)
            main_container.add_widget(self.nuevos_obreros_field)

            # Contenedor para campos de nuevos obreros
            self.nuevos_obreros_container = MDBoxLayout(
                orientation="vertical",
                size_hint_y=None,
                spacing="8dp"
            )
            self.nuevos_obreros_container.bind(minimum_height=self.nuevos_obreros_container.setter('height'))

            main_container.add_widget(self.nuevos_obreros_container)

            # Inicializar lista de campos para nuevos obreros
            self.campos_nuevos_obreros = []

            # Inicializar set de obreros marcados para remover si no existe
            if not hasattr(self, 'obreros_to_remove'):
                self.obreros_to_remove = set()

            # Debug: Confirmar que el sistema está listo
            print(f"🔧 Sistema de agregar obreros inicializado - Obreros actuales: {len(self.current_obreros)}")

            # Agregar contenedor al scroll
            main_scroll.add_widget(main_container)

            # Crear dialog con scroll y tamaño optimizado
            self.edit_dialog = MDDialog(
                title=f"✏️ Editar {numero_cuadrilla}",
                type="custom",
                content_cls=main_scroll,
                size_hint=(0.85, None),
                height="550dp",  # Altura fija más controlada
                buttons=[
                    MDRaisedButton(
                        text="CANCELAR",
                        md_bg_color=[0.5, 0.5, 0.5, 1],
                        on_release=lambda x: self.edit_dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="💾 GUARDAR",
                        md_bg_color=utils.get_color('primary'),
                        on_release=lambda x: self._save_edited_cuadrilla()
                    )
                ]
            )

            self.edit_dialog.open()
            print(f"✅ Dialog de edición creado con {len(self.current_obreros)} obreros")

        except Exception as e:
            print(f"❌ Error creando dialog de edición: {e}")
            utils.show_error_dialog("Error", f"No se pudo abrir el editor:\n{str(e)}")
    """

    # ==========================================
    # TODOS LOS MÉTODOS DE EDICIÓN COMENTADOS (EN DESARROLLO)
    # ==========================================
    """
    def _create_obreros_with_checkboxes(self):
        # Crear campos de obreros con checkboxes de remover
        self.obreros_container.clear_widgets()

        # Lista para trackear estados de remoción
        if not hasattr(self, 'obreros_to_remove'):
            self.obreros_to_remove = set()

        for index, obrero in enumerate(self.current_obreros):
            obrero_widget = self._create_obrero_field_with_checkbox(obrero, index)
            self.obreros_container.add_widget(obrero_widget)

        # Actualizar contador
        self._update_obreros_counter_real()

    def _create_obrero_field_with_checkbox(self, obrero, index):
        # Función de edición comentada - En desarrollo
        pass

    def _on_remove_checkbox_change(self, obrero_index, is_active):
        # Callback cuando se cambia el estado del checkbox de remover
        if is_active:
            # Marcar obrero para remoción
            self.obreros_to_remove.add(obrero_index)
            print(f"⚠️ Obrero {obrero_index + 1} marcado para remover")
        else:
            # Desmarcar obrero
            self.obreros_to_remove.discard(obrero_index)
            print(f"✅ Obrero {obrero_index + 1} desmarcado")

        # Recrear la lista para actualizar estilos visuales
        self._create_obreros_with_checkboxes()

    def _update_obreros_counter_real(self):
        # COMENTARIO 
        total_obreros = len(self.current_obreros)
        obreros_removidos = len(self.obreros_to_remove)
        obreros_finales = total_obreros - obreros_removidos

        # Actualizar texto del título
        if obreros_removidos > 0:
            self.obreros_title.text = f"📋 OBREROS ({obreros_finales}/40) - {obreros_removidos} marcados para remover"
        else:
            self.obreros_title.text = f"📋 OBREROS ({obreros_finales}/40)"

        # Cambiar color según validación (considerando remoción)
        if 4 <= obreros_finales <= 40:
            self.obreros_title.theme_text_color = "Primary"
            self.limits_label.theme_text_color = "Primary"
        else:
            self.obreros_title.theme_text_color = "Error"
            self.limits_label.theme_text_color = "Error"

        print(f"📊 Contador actualizado: {obreros_finales}/40 obreros ({obreros_removidos} marcados para remover)")

    def _create_obrero_item(self, obrero, index):
        # COMENTARIO 
        from kivymd.uix.widget import MDWidget

        # Contenedor del item
        item_container = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="70dp",
            spacing="10dp",
            padding=["10dp", "5dp", "10dp", "5dp"]
        )

        # Información del obrero
        info_container = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.6
        )

        # Nombre completo
        nombre_label = MDLabel(
            text=f"{index + 1}. {obrero.get('nombre', '')} {obrero.get('apellidos', '')}",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="35dp"
        )

        # Cédula
        cedula_label = MDLabel(
            text=f"Cédula: {obrero.get('cedula', '')}",
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height="35dp"
        )

        info_container.add_widget(nombre_label)
        info_container.add_widget(cedula_label)

        # Contenedor de botones
        buttons_container = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=0.4,
            spacing="5dp"
        )

        # Botón reemplazar
        replace_button = MDIconButton(
            icon="account-switch",
            theme_icon_color="Custom",
            icon_color=utils.get_color('warning'),
            size_hint=(None, None),
            size=("40dp", "40dp"),
            on_release=lambda x, idx=index: self._replace_obrero_dialog(idx)
        )

        # Botón eliminar
        remove_button = MDIconButton(
            icon="delete",
            theme_icon_color="Custom",
            icon_color=utils.get_color('error'),
            size_hint=(None, None),
            size=("40dp", "40dp"),
            on_release=lambda x, idx=index: self._remove_obrero_confirmation(idx)
        )

        buttons_container.add_widget(replace_button)
        buttons_container.add_widget(remove_button)

        # Agregar todo al contenedor principal
        item_container.add_widget(info_container)
        item_container.add_widget(buttons_container)

        return item_container

    def _update_obreros_counter(self):
        # COMENTARIO 
        current_count = len(self.current_obreros)
        print(f"📊 Contador: {current_count}/40 obreros")

    def on_nuevos_obreros_change(self, instance, value):
        # COMENTARIO 
        print(f"🔄 on_nuevos_obreros_change llamado con valor: '{value}'")

        try:
            # Limpiar campos existentes
            self.nuevos_obreros_container.clear_widgets()
            self.campos_nuevos_obreros = []

            # Validar que sea un número
            if not value.isdigit() or value == "":
                print("❌ Valor no es número válido o está vacío")
                return

            num_nuevos_obreros = int(value)

            # Validar rango 1-10 (razonable para agregar)
            if num_nuevos_obreros < 1 or num_nuevos_obreros > 10:
                self.nuevos_obreros_field.helper_text = "❌ Debe ser entre 1 y 10 obreros"
                self.nuevos_obreros_field.helper_text_mode = "persistent"
                return
            else:
                # Restablecer helper text
                self.nuevos_obreros_field.helper_text = ""
                self.nuevos_obreros_field.helper_text_mode = "none"

            # Verificar límite total (actuales - removidos + nuevos <= 40)
            obreros_actuales = len(self.current_obreros) - len(self.obreros_to_remove)
            total_final = obreros_actuales + num_nuevos_obreros

            if total_final > 40:
                self.nuevos_obreros_field.helper_text = f"❌ Excede límite: {total_final}/40 obreros total"
                self.nuevos_obreros_field.helper_text_mode = "persistent"
                return

            print(f"🔢 Creando {num_nuevos_obreros} campos para nuevos obreros")

            # Crear campos dinámicos para nuevos obreros
            for i in range(num_nuevos_obreros):
                campo_obrero = self._create_nuevo_obrero_field(i)
                self.nuevos_obreros_container.add_widget(campo_obrero)

        except Exception as e:
            print(f"❌ Error en on_nuevos_obreros_change: {e}")

    def _create_nuevo_obrero_field(self, index):
        # COMENTARIO 

        # Contenedor para este obrero
        obrero_container = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing="5dp"
        )

        # Título del obrero
        obrero_titulo = MDLabel(
            text=f"Nuevo Obrero {index + 1}:",
            theme_text_color="Primary",
            font_style="Body1",
            size_hint_y=None,
            height="30dp"
        )
        obrero_container.add_widget(obrero_titulo)

        # Campo de búsqueda por cédula (IGUAL AL SISTEMA ORIGINAL)
        busqueda_field = MDTextField(
            hint_text="Escriba cédula del obrero...",
            size_hint_y=None,
            height="50dp",
            mode="line",
            on_text=lambda instance, text, idx=index: self.on_nuevo_obrero_search(idx, text)
        )

        # Label informativo
        info_label = MDLabel(
            text="Escriba la cédula para buscar obreros disponibles",
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height="25dp"
        )

        obrero_container.add_widget(busqueda_field)
        obrero_container.add_widget(info_label)

        # Guardar referencias en diccionario (IGUAL AL SISTEMA ORIGINAL)
        campo_data = {
            'busqueda_field': busqueda_field,
            'info_label': info_label,
            'obrero_data': None,
            'dropdown': None,
            'selecting': False
        }
        self.campos_nuevos_obreros.append(campo_data)

        # Calcular altura total
        obrero_container.height = "110dp"  # 30 + 50 + 25 + 5 spacing

        return obrero_container

    def on_nuevo_obrero_search(self, index, text):
        # COMENTARIO 
        try:
            # Verificar que el campo existe
            if index >= len(self.campos_nuevos_obreros):
                return

            campo_data = self.campos_nuevos_obreros[index]

            # Evitar bucles infinitos durante selección
            if campo_data.get('selecting', False):
                campo_data['selecting'] = False
                return

            # Limpiar texto si es muy corto
            if len(text) < 2:
                campo_data['info_label'].text = "Escriba al menos 2 dígitos de la cédula"
                campo_data['info_label'].theme_text_color = "Secondary"
                # Cerrar dropdown si existe
                if campo_data.get('dropdown'):
                    campo_data['dropdown'].dismiss()
                    campo_data['dropdown'] = None
                return

            # Cerrar dropdown anterior si existe (IMPORTANTE: evita bug de múltiples dropdowns)
            self.close_nuevo_obrero_dropdown(index)

            print(f"🔍 Buscando nuevos obreros por cédula: '{text}' para campo {index + 1}")

            # Filtrar obreros disponibles por cédula
            obreros_filtrados = []
            for obrero in self.obreros_disponibles:
                cedula = obrero.get('cedula', '')
                if text.lower() in cedula.lower():
                    # Verificar que no esté ya en la cuadrilla actual
                    already_in_cuadrilla = any(
                        current_obrero.get('cedula') == cedula
                        for current_obrero in self.current_obreros
                    )
                    # Verificar que no esté ya seleccionado en otro campo de nuevos
                    already_selected = any(
                        campo.get('obrero_data', {}).get('cedula') == cedula
                        for campo in self.campos_nuevos_obreros
                        if campo.get('obrero_data')
                    )

                    if not already_in_cuadrilla and not already_selected:
                        obreros_filtrados.append(obrero)

            if obreros_filtrados:
                self.show_nuevos_obreros_dropdown(campo_data['busqueda_field'], obreros_filtrados, index)
                campo_data['info_label'].text = f"✅ {len(obreros_filtrados)} obrero(s) disponible(s)"
                campo_data['info_label'].theme_text_color = "Primary"
            else:
                campo_data['info_label'].text = "❌ No se encontraron obreros disponibles"
                campo_data['info_label'].theme_text_color = "Error"

        except Exception as e:
            print(f"❌ Error en búsqueda de nuevo obrero: {e}")

    def show_nuevos_obreros_dropdown(self, caller, obreros, index):
        # COMENTARIO 
        try:
            # Crear items del menú
            menu_items = []
            for obrero in obreros:
                nombre_completo = f"{obrero.get('nombre', '')} {obrero.get('apellidos', '')}"
                cedula = obrero.get('cedula', '')

                menu_items.append({
                    'text': f"CI: {cedula} | {nombre_completo}",
                    'on_release': lambda x=obrero, idx=index: self.select_nuevo_obrero_from_dropdown(x, idx)
                })

            # Calcular altura del dropdown
            item_height = 48
            padding = 20
            min_height = 100
            max_height = 300

            calculated_height = len(menu_items) * item_height + padding
            dropdown_height = max(min_height, min(calculated_height, max_height))

            dropdown = MDDropdownMenu(
                caller=caller,
                items=menu_items,
                width_mult=4,
                max_height=dropdown_height,
                position="bottom"
            )

            # Guardar referencia al dropdown
            self.campos_nuevos_obreros[index]['dropdown'] = dropdown
            dropdown.open()

        except Exception as e:
            print(f"Error mostrando dropdown de nuevos obreros: {e}")

    def close_nuevo_obrero_dropdown(self, index):
        # COMENTARIO 
        try:
            if index < len(self.campos_nuevos_obreros):
                dropdown = self.campos_nuevos_obreros[index].get('dropdown')
                if dropdown:
                    dropdown.dismiss()
                    self.campos_nuevos_obreros[index]['dropdown'] = None
        except Exception as e:
            print(f"Error cerrando dropdown: {e}")

    def select_nuevo_obrero_from_dropdown(self, obrero, index):
        # COMENTARIO 
        try:
            cedula = obrero.get('cedula', '')
            nombre = obrero.get('nombre', '')
            apellidos = obrero.get('apellidos', '')

            # Marcar que está en proceso de selección
            self.campos_nuevos_obreros[index]['selecting'] = True

            # Actualizar campo de búsqueda con la cédula seleccionada
            busqueda_field = self.campos_nuevos_obreros[index]['busqueda_field']
            busqueda_field.text = cedula

            # Actualizar información del obrero seleccionado
            info_label = self.campos_nuevos_obreros[index]['info_label']
            info_label.text = f"✅ Seleccionado: {nombre} {apellidos}"
            info_label.theme_text_color = "Primary"

            # Guardar datos del obrero seleccionado
            self.campos_nuevos_obreros[index]['obrero_data'] = obrero

            # Cerrar dropdown
            self.close_nuevo_obrero_dropdown(index)

            print(f"✅ Nuevo obrero seleccionado para campo {index + 1}: {nombre} {apellidos} (CI: {cedula})")

        except Exception as e:
            print(f"❌ Error seleccionando nuevo obrero: {e}")

    # Métodos placeholder para las acciones (implementaremos en siguientes pasos)
    def _open_moderador_dropdown(self):
        # COMENTARIO 
        print("🔄 TODO: Abrir selector de moderador")

    def _replace_obrero_dialog(self, index):
        # COMENTARIO 
        print(f"🔄 TODO: Reemplazar obrero en posición {index}")

    def _remove_obrero_confirmation(self, index):
        # COMENTARIO 
        print(f"❌ TODO: Confirmar eliminación de obrero en posición {index}")

    def _save_edited_cuadrilla(self):
        # COMENTARIO 
        print("💾 TODO: Guardar cuadrilla editada")
    """

    # ==========================================
    # FUNCIONES ACTIVAS DE CUADRILLAS
    # ==========================================

    def _show_cuadrilla_form_dialog(self, title, button_text, cuadrilla_data):
        # COMENTARIO 
        # Crear contenido del formulario
        content = MDBoxLayout(
            orientation="vertical",
            spacing="12dp",
            size_hint_y=None,
            height="400dp",
            padding="15dp"
        )

        # Campo actividad
        self.actividad_field = ui_components.create_form_field(
            hint_text="Actividad de la cuadrilla",
            text=cuadrilla_data.get('actividad', ''),
            required=True
        )
        content.add_widget(self.actividad_field)

        # Botón moderador
        moderador_text = "Seleccionar Moderador"
        if self.selected_moderador:
            moderador_text = f"Moderador: {self.selected_moderador.get('nombre', '')} {self.selected_moderador.get('apellidos', '')}"

        self.moderador_button = MDRaisedButton(
            text=moderador_text,
            size_hint_y=None,
            height="48dp",
            md_bg_color=utils.get_color('secondary'),
            on_release=lambda x: self._open_moderador_dropdown()
        )
        content.add_widget(self.moderador_button)

        # Botón agregar obreros
        add_obrero_button = MDRaisedButton(
            text="Agregar Obreros",
            size_hint_y=None,
            height="48dp",
            md_bg_color=utils.get_color('info'),
            on_release=lambda x: self._show_obreros_selection()
        )
        content.add_widget(add_obrero_button)

        # Contenedor de obreros seleccionados
        self.obreros_container = MDBoxLayout(
            orientation="vertical",
            spacing="8dp",
            adaptive_height=True
        )
        content.add_widget(self.obreros_container)

        # Actualizar lista de obreros
        self._update_obreros_display()

        # Crear dialog
        self.current_dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=content,
            size_hint=(0.9, None),
            height="500dp",
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.current_dialog.dismiss()
                ),
                MDRaisedButton(
                    text=button_text,
                    md_bg_color=utils.get_color('success'),
                    on_release=lambda x: self.save_cuadrilla()
                )
            ]
        )

        self.current_dialog.open()

    def _load_personal_data_for_form(self, callback):
        # COMENTARIO 
        try:
            # Cargar moderadores
            moderadores_response = api_client.get_moderadores()
            self.moderadores_disponibles = moderadores_response.get('moderadores', [])  # ← CORRECCIÓN

            # Cargar obreros disponibles
            obreros_response = api_client.get_obreros_disponibles()
            self.obreros_disponibles = obreros_response.get('obreros', [])  # ← CORRECCIÓN

            # Ejecutar callback
            callback()

        except Exception as e:
            self.show_error_dialog(f"Error al cargar datos del personal: {str(e)}")

    def _open_moderador_dropdown(self):
        # COMENTARIO 
        if not self.moderadores_disponibles:
            self.show_error_dialog("No hay moderadores disponibles")
            return

        dropdown = ui_components.create_moderadores_dropdown(
            button=self.moderador_button,
            moderadores_list=self.moderadores_disponibles,
            callback=self._on_moderador_selected
        )
        dropdown.open()

    def _on_moderador_selected(self, moderador):
        """Callback para moderador seleccionado"""
        self.selected_moderador = moderador
        moderador_nombre = f"{moderador.get('nombre', '')} {moderador.get('apellidos', '')}"
        self.moderador_button.text = f"Moderador: {moderador_nombre}"

    def _show_obreros_selection(self):
        """Mostrar dialog para seleccionar obreros"""
        if not self.obreros_disponibles:
            self.show_error_dialog("No hay obreros disponibles")
            return

        # Crear lista de obreros disponibles
        content = MDBoxLayout(orientation="vertical", spacing="8dp")
        scroll = MDScrollView()
        obreros_list = MDList()

        for obrero in self.obreros_disponibles:
            # Verificar si ya está seleccionado
            already_selected = any(
                o.get('_id') == obrero.get('_id') for o in self.selected_obreros
            )

            if not already_selected:
                nombre_completo = f"{obrero.get('nombre', '')} {obrero.get('apellidos', '')}"
                cedula = obrero.get('cedula', '')

                item = ui_components.create_list_item(
                    primary_text=f"CI: {cedula}",
                    secondary_text=nombre_completo,
                    on_release=lambda x, obr=obrero: self._add_obrero_to_selection(obr, selection_dialog)
                )
                obreros_list.add_widget(item)

        scroll.add_widget(obreros_list)
        content.add_widget(scroll)

        selection_dialog = MDDialog(
            title="Seleccionar Obrero",
            type="custom",
            content_cls=content,
            size_hint=(0.8, 0.6),
            buttons=[
                MDRaisedButton(
                    text="CERRAR",
                    on_release=lambda x: selection_dialog.dismiss()
                )
            ]
        )

        selection_dialog.open()

    def _add_obrero_to_selection(self, obrero, dialog):
        """Agregar obrero a la selección"""
        self.selected_obreros.append(obrero)
        self._update_obreros_display()
        dialog.dismiss()

    def _update_obreros_display(self):
        """Actualizar display de obreros seleccionados"""
        if not hasattr(self, 'obreros_container') or not self.obreros_container:
            return

        self.obreros_container.clear_widgets()

        for i, obrero in enumerate(self.selected_obreros):
            obrero_layout = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="40dp",
                spacing="8dp"
            )

            nombre_completo = f"{obrero.get('nombre', '')} {obrero.get('apellidos', '')}"
            cedula = obrero.get('cedula', '')

            obrero_label = MDLabel(
                text=f"{i+1}. CI: {cedula} | {nombre_completo}",
                size_hint_x=0.8
            )

            remove_button = MDIconButton(
                icon="close",
                size_hint_x=0.2,
                on_release=lambda x, idx=i: self._remove_obrero_from_selection(idx)
            )

            obrero_layout.add_widget(obrero_label)
            obrero_layout.add_widget(remove_button)
            self.obreros_container.add_widget(obrero_layout)

    def _remove_obrero_from_selection(self, index):
        """Remover obrero de la selección"""
        if 0 <= index < len(self.selected_obreros):
            self.selected_obreros.pop(index)
            self._update_obreros_display()

    def save_cuadrilla_changes(self):
        """Guardar cambios en cuadrilla existente"""
        try:
            # Validar actividad
            if not self.actividad_field.text.strip():
                self.show_error_dialog("La actividad es obligatoria")
                return

            # Preparar datos para actualización
            cuadrilla_data = {
                'actividad': self.actividad_field.text.strip(),
                'moderador_id': self.selected_moderador.get('_id') if self.selected_moderador else None
            }

            # Actualizar en API
            response = api_client.update_cuadrilla(self.editing_cuadrilla_id, cuadrilla_data)

            # Cerrar dialog y recargar
            self.current_dialog.dismiss()
            self.show_success_dialog("Cuadrilla actualizada exitosamente", lambda: self.load_cuadrillas_data())

        except Exception as e:
            self.show_error_dialog(f"Error al actualizar cuadrilla: {str(e)}")

    def confirm_delete_cuadrilla(self, cuadrilla_data):
        """Confirmar eliminación de cuadrilla"""
        numero_cuadrilla = cuadrilla_data.get('numero_cuadrilla', 'Sin número')

        dialog = ui_components.create_double_confirmation_dialog(
            title="⚠️ Eliminar Cuadrilla",
            message=f"¿Está seguro que desea eliminar la cuadrilla {numero_cuadrilla}?",
            final_message="⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER ⚠️\n\nSe eliminará permanentemente la cuadrilla y se liberarán todos los obreros asignados.",
            confirm_callback=lambda: self.delete_cuadrilla(cuadrilla_data)
        )

        dialog.open()

    def delete_cuadrilla(self, cuadrilla_data):
        """Eliminar cuadrilla definitivamente"""
        try:
            response = api_client.delete_cuadrilla(cuadrilla_data.get('_id'))
            numero_cuadrilla = cuadrilla_data.get('numero_cuadrilla', 'Sin número')
            self.show_success_dialog(
                f"Cuadrilla {numero_cuadrilla} eliminada exitosamente",
                lambda: self.load_cuadrillas_data()
            )
        except Exception as e:
            self.show_error_dialog(f"Error al eliminar cuadrilla: {str(e)}")

    def show_dialog(self, title, text):
        """Mostrar diálogo con título y texto - MÉTODO ORIGINAL"""
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

    def show_error_dialog(self, message):
        """Mostrar dialog de error"""
        dialog = ui_components.create_error_dialog(message)
        dialog.open()

    def show_success_dialog(self, message, callback=None):
        """Mostrar dialog de exito"""
        dialog = ui_components.create_success_dialog(message, callback)
        dialog.open()

    def go_back_to_main(self):
        """Volver al menu principal"""
        if self.main_screen:
            self.main_screen.go_back_to_main('personal')


# Instancia para uso directo
cuadrillas_manager = CuadrillasManager()