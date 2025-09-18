"""
Manager especializado para gestión de moderadores
CRUD completo y validaciones para moderadores
"""

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, ThreeLineListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import dp

from .api_client import api_client
from .validators import validators
from .utils import utils
from .ui_components import ui_components


class ModeradorListItem(ThreeLineListItem):
    """Item de lista para mostrar moderadores"""

    def __init__(self, moderador_data, on_select_callback, **kwargs):
        super().__init__(**kwargs)

        # Datos del moderador
        self.moderador_data = moderador_data
        self.on_select_callback = on_select_callback

        # Configurar textos
        nombre_completo = f"{moderador_data.get('nombre', '')} {moderador_data.get('apellidos', '')}"
        cedula = moderador_data.get('cedula', '')
        email = moderador_data.get('email', '')
        telefono = utils.format_phone_number(moderador_data.get('telefono', ''))

        self.text = f"👤 {nombre_completo}"
        self.secondary_text = f"CI: {cedula} | Tel: {telefono}"
        self.tertiary_text = f"Email: {email}"

        # Configurar callback
        self.on_release = self.select_moderador

    def select_moderador(self):
        """Seleccionar moderador"""
        if self.on_select_callback:
            self.on_select_callback(self.moderador_data)


class ModeradoresManager:
    """Manager para gestión completa de moderadores"""

    def __init__(self, main_screen=None):
        self.main_screen = main_screen
        self.moderadores_data = []
        self.current_dialog = None

        # Referencias a campos de formulario
        self.nombre_field = None
        self.apellidos_field = None
        self.cedula_field = None
        self.email_field = None
        self.telefono_field = None
        self.talla_ropa_button = None
        self.talla_zapatos_button = None

        # Datos temporales para edición
        self.editing_moderador_id = None
        self.editing_moderador_cedula = None
        self.selected_talla_ropa = ""

    def get_screen(self):
        """Obtener pantalla principal de moderadores"""
        screen = MDScreen()
        screen.add_widget(self.create_main_layout())
        return screen

    def create_main_layout(self):
        """Crear layout principal de gestión de moderadores - ESTRUCTURA ORIGINAL"""
        layout = MDBoxLayout(orientation="vertical")

        # Toolbar
        toolbar = MDTopAppBar(
            title="Gestión de Moderadores",
            elevation=2,
            left_action_items=[["arrow-left", lambda x: self.go_back_to_main()]]
        )
        layout.add_widget(toolbar)

        # Card principal con botón y lista juntos (ESTRUCTURA ORIGINAL)
        moderadores_card = MDCard(
            elevation=1,
            padding="15dp"
        )

        card_content = MDBoxLayout(orientation="vertical", spacing="15dp")

        # Botón crear moderador
        crear_button = MDRaisedButton(
            text="➕ CREAR MODERADOR",
            md_bg_color=[0.3, 0.5, 0.8, 1],  # Azul moderador
            size_hint_y=None,
            height="50dp",
            on_release=lambda x: self.show_create_moderador_dialog()
        )

        # Título para la lista
        lista_title = MDLabel(
            text="Lista de Moderadores",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )

        # Lista de moderadores
        self.moderadores_scroll = MDScrollView()
        self.moderadores_list = MDList()
        self.moderadores_scroll.add_widget(self.moderadores_list)

        # Agregar componentes al card
        card_content.add_widget(crear_button)
        card_content.add_widget(lista_title)
        card_content.add_widget(self.moderadores_scroll)
        moderadores_card.add_widget(card_content)

        # Agregar card al layout principal
        layout.add_widget(moderadores_card)

        # Cargar datos iniciales
        Clock.schedule_once(lambda dt: self.load_moderadores_data(), 0)

        return layout

    def load_moderadores_data(self):
        """Cargar lista de moderadores desde API - OPTIMIZADO"""
        try:
            # Obtener datos de la API directamente (sin delays ni programación)
            response = api_client.get_moderadores()
            self.moderadores_data = response.get('moderadores', [])

            # Actualizar lista de forma eficiente
            self._update_moderadores_list()

        except Exception as e:
            self._show_error_state(f"Error al cargar moderadores: {str(e)}")

    def _update_moderadores_list(self):
        """Actualizar lista de moderadores de forma eficiente"""
        # Limpiar lista
        if hasattr(self, 'moderadores_list'):
            self.moderadores_list.clear_widgets()

            if not self.moderadores_data:
                # Mostrar estado vacío
                from kivymd.uix.list import OneLineListItem
                no_moderadores_item = OneLineListItem(
                    text="📝 No hay moderadores registrados. Crea uno usando el botón +"
                )
                self.moderadores_list.add_widget(no_moderadores_item)
            else:
                # Agregar moderadores a la lista
                for moderador in self.moderadores_data:
                    moderador_item = ModeradorListItem(
                        moderador_data=moderador,
                        on_select_callback=self.on_moderador_selected
                    )
                    self.moderadores_list.add_widget(moderador_item)

    def _show_error_state(self, error_message):
        """Mostrar estado de error en la lista"""
        if hasattr(self, 'moderadores_list'):
            self.moderadores_list.clear_widgets()
            from kivymd.uix.list import OneLineListItem
            error_item = OneLineListItem(text=f"⚠️ {error_message}")
            retry_item = OneLineListItem(
                text="🔄 Reintentar",
                on_release=lambda x: self.load_moderadores_data()
            )
            self.moderadores_list.add_widget(error_item)
            self.moderadores_list.add_widget(retry_item)

    def on_moderador_selected(self, moderador_data):
        """Callback cuando se selecciona un moderador - RESTAURADO: ir directo a detalles"""
        self.show_moderador_details(moderador_data)

    def show_moderador_options(self, moderador_data):
        """Mostrar opciones para moderador seleccionado"""
        nombre_completo = f"{moderador_data.get('nombre', '')} {moderador_data.get('apellidos', '')}"

        actions = [
            {
                'text': 'VER DETALLES',
                'color': utils.get_color('info'),
                'callback': lambda x: self.show_moderador_details(moderador_data)
            },
            {
                'text': 'EDITAR',
                'color': utils.get_color('warning'),
                'callback': lambda x: self.show_edit_moderador_dialog(moderador_data)
            },
            {
                'text': 'ELIMINAR',
                'color': utils.get_color('error'),
                'callback': lambda x: self.confirm_delete_moderador(moderador_data)
            }
        ]

        action_buttons = ui_components.create_action_buttons(actions)

        dialog = MDDialog(
            title=f"👤 {nombre_completo}",
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

    def show_moderador_details(self, moderador_data):
        """Mostrar detalles del moderador - ESTRUCTURA ORIGINAL"""
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
        fecha_creacion = utils.format_date_spanish(fecha_creacion_raw)

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
        """Mostrar diálogo de detalles con botón de editar - ESTRUCTURA ORIGINAL"""
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
            on_release=lambda x: self.moderador_details_dialog.dismiss()
        )

        # Agregar botones al layout
        buttons_layout.add_widget(delete_button)
        buttons_layout.add_widget(spacer)
        buttons_layout.add_widget(close_button)
        main_content.add_widget(buttons_layout)

        # Crear el diálogo
        self.moderador_details_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=main_content,
            size_hint=(0.9, 0.7)
        )

        self.moderador_details_dialog.open()

    def edit_moderador(self, moderador_data):
        """Editar moderador desde detalles - CALLBACK ORIGINAL"""
        self.moderador_details_dialog.dismiss()
        self.show_edit_moderador_dialog(moderador_data)

    def delete_moderador_confirmation(self, moderador_data):
        """Confirmar eliminación desde detalles - CALLBACK ORIGINAL"""
        self.moderador_details_dialog.dismiss()
        self.confirm_delete_moderador(moderador_data)


    def show_create_moderador_dialog(self):
        """Mostrar dialog para crear nuevo moderador"""
        self.editing_moderador_id = None
        self.editing_moderador_cedula = None
        self.selected_talla_ropa = ""

        self._show_moderador_form_dialog(
            title="Registrar Nuevo Moderador",
            button_text="REGISTRAR",
            moderador_data={}
        )

    def show_edit_moderador_dialog(self, moderador_data):
        """Mostrar dialog para editar moderador"""
        self.editing_moderador_id = moderador_data.get('_id')
        self.editing_moderador_cedula = moderador_data.get('cedula')
        self.selected_talla_ropa = moderador_data.get('talla_ropa', '')

        self._show_moderador_form_dialog(
            title=f"Editar Moderador: {moderador_data.get('nombre', '')}",
            button_text="GUARDAR CAMBIOS",
            moderador_data=moderador_data
        )

    def _show_moderador_form_dialog(self, title, button_text, moderador_data):
        """Mostrar formulario de moderador (crear o editar) - ESTRUCTURA ORIGINAL"""
        # Scroll para contenido extenso (IGUAL QUE EL ORIGINAL)
        scroll_content = MDScrollView(size_hint_y=None, height="400dp")
        content = MDBoxLayout(
            orientation="vertical",
            spacing="15dp",
            adaptive_height=True,  # ← CLAVE: Altura adaptativa como el original
            padding="10dp"
        )

        # Título (IGUAL QUE EL ORIGINAL)
        title_label = MDLabel(
            text=title,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp",
            halign="center"
        )
        content.add_widget(title_label)

        # Campos del formulario
        self.nombre_field = ui_components.create_form_field(
            hint_text="Nombre",
            text=moderador_data.get('nombre', ''),
            required=True
        )
        content.add_widget(self.nombre_field)

        self.apellidos_field = ui_components.create_form_field(
            hint_text="Apellidos",
            text=moderador_data.get('apellidos', ''),
            required=True
        )
        content.add_widget(self.apellidos_field)

        self.cedula_field = ui_components.create_form_field(
            hint_text="Cédula de Identidad",
            text=moderador_data.get('cedula', ''),
            required=True,
            field_type="number"
        )
        content.add_widget(self.cedula_field)

        self.email_field = ui_components.create_form_field(
            hint_text="Email",
            text=moderador_data.get('email', ''),
            required=True,
            field_type="email"
        )
        content.add_widget(self.email_field)

        self.telefono_field = ui_components.create_form_field(
            hint_text="Teléfono",
            text=moderador_data.get('telefono', ''),
            required=True,
            field_type="phone"
        )
        content.add_widget(self.telefono_field)

        # Título de campos opcionales (ESTRUCTURA ORIGINAL)
        opcional_label = MDLabel(
            text="Campos Opcionales",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="40dp",
            halign="left"
        )
        content.add_widget(opcional_label)

        # Botones para tallas
        if self.selected_talla_ropa and self.selected_talla_ropa != "No ingresado":
            talla_ropa_text = f"Talla Ropa: {self.selected_talla_ropa}"
        else:
            talla_ropa_text = "Seleccionar Talla de Ropa"
        self.talla_ropa_button = MDRaisedButton(
            text=talla_ropa_text,
            size_hint_y=None,
            height="48dp",
            md_bg_color=utils.get_color('secondary'),
            on_release=self._open_talla_ropa_dropdown
        )
        content.add_widget(self.talla_ropa_button)

        # Campo Talla de Zapatos (ESTRUCTURA ORIGINAL) - Campo de texto con validación
        talla_zapatos_value = moderador_data.get('talla_zapatos', '')
        if talla_zapatos_value == 'No ingresado':
            talla_zapatos_value = ''

        self.talla_zapatos_field = MDTextField(
            hint_text="Talla de Zapatos (opcional)",
            text=talla_zapatos_value,
            helper_text="Solo números del 30 al 50",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None,
            height="60dp"
        )
        content.add_widget(self.talla_zapatos_field)

        # Aplicar capitalización automática
        self.nombre_field.bind(text=self._on_nombre_change)
        self.apellidos_field.bind(text=self._on_apellidos_change)

        # Agregar content al scroll (ESTRUCTURA ORIGINAL)
        scroll_content.add_widget(content)

        # Crear dialog (TAMAÑO ORIGINAL)
        self.current_dialog = MDDialog(
            type="custom",
            content_cls=scroll_content,  # ← Usar scroll en lugar de content directo
            size_hint=(0.9, None),
            height="500dp",  # ← TAMAÑO ORIGINAL más pequeño
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: self.current_dialog.dismiss()
                ),
                MDRaisedButton(
                    text=button_text,
                    md_bg_color=utils.get_color('success'),
                    on_release=lambda x: self.save_moderador()
                )
            ]
        )

        self.current_dialog.open()

    def _on_nombre_change(self, instance, value):
        """Capitalizar nombre automáticamente"""
        if value and not value[-1].isspace():
            capitalized = validators.capitalize_first_letter(value)
            if capitalized != value:
                instance.text = capitalized

    def _on_apellidos_change(self, instance, value):
        """Capitalizar apellidos automáticamente"""
        if value and not value[-1].isspace():
            capitalized = validators.capitalize_first_letter(value)
            if capitalized != value:
                instance.text = capitalized

    def _open_talla_ropa_dropdown(self, button):
        """Abrir dropdown de tallas de ropa"""
        dropdown = ui_components.create_talla_ropa_dropdown(
            button=button,
            callback=self._on_talla_ropa_selected
        )
        dropdown.open()

    def _on_talla_ropa_selected(self, talla):
        """Callback para talla de ropa seleccionada"""
        self.selected_talla_ropa = talla
        # Mostrar texto limpio cuando se selecciona "Ninguno"
        if talla == "No ingresado":
            self.talla_ropa_button.text = "Seleccionar Talla de Ropa"
        else:
            self.talla_ropa_button.text = f"Talla Ropa: {talla}"


    def save_moderador(self):
        """Guardar moderador (crear o actualizar)"""
        try:
            # Recopilar datos del formulario
            moderador_data = {
                'nombre': self.nombre_field.text.strip(),
                'apellidos': self.apellidos_field.text.strip(),
                'cedula': validators.clean_cedula_input(self.cedula_field.text),
                'email': self.email_field.text.strip().lower(),
                'telefono': validators.clean_telefono_input(self.telefono_field.text),
                'talla_ropa': self.selected_talla_ropa or 'No ingresado',
                'talla_zapatos': self.talla_zapatos_field.text.strip() or 'No ingresado',
                'activo': True,
                'nivel': 'moderador'
            }

            # Validar campos
            is_valid, errors = validators.validate_moderador_fields(moderador_data)
            if not is_valid:
                error_messages = '\n'.join([f"• {error}" for error in errors.values()])
                self.show_error_dialog(f"Errores de validación:\n\n{error_messages}")
                return

            # Verificar duplicados
            if self._check_duplicates(moderador_data):
                return

            # Guardar en API
            if self.editing_moderador_id:
                # Actualizar
                moderador_data['_id'] = self.editing_moderador_id
                moderador_data['cedula_original'] = self.editing_moderador_cedula
                response = api_client.update_moderador(moderador_data)
                message = "Moderador actualizado exitosamente"
            else:
                # Crear
                response = api_client.create_moderador(moderador_data)
                message = "Moderador registrado exitosamente"

            # Cerrar dialog y recargar
            self.current_dialog.dismiss()
            self.show_success_dialog(message, lambda: self.load_moderadores_data())

        except Exception as e:
            self.show_error_dialog(f"Error al guardar moderador: {str(e)}")

    def _check_duplicates(self, moderador_data):
        """Verificar duplicados de cédula, email y teléfono (OPTIMIZADO)"""
        exclude_id = self.editing_moderador_id

        # Verificar todos los duplicados en una sola consulta optimizada
        cedula_exists, cedula_where, email_exists, email_where, telefono_exists, telefono_where = api_client.check_all_duplicates_optimized(
            moderador_data['cedula'],
            moderador_data['email'],
            moderador_data['telefono'],
            exclude_id
        )

        # Verificar cédula
        if cedula_exists:
            self.show_error_dialog(f"La cédula {moderador_data['cedula']} ya está registrada en {cedula_where}")
            return True

        # Verificar email
        if email_exists:
            self.show_error_dialog(f"El email {moderador_data['email']} ya está registrado en {email_where}")
            return True

        # Verificar teléfono
        if telefono_exists:
            self.show_error_dialog(f"El teléfono {moderador_data['telefono']} ya está registrado en {telefono_where}")
            return True

        return False

    def confirm_delete_moderador(self, moderador_data):
        """Confirmar eliminación de moderador"""
        nombre_completo = f"{moderador_data.get('nombre', '')} {moderador_data.get('apellidos', '')}"
        moderador_id = moderador_data.get('_id')

        # Buscar cuadrilla asignada
        cuadrilla_nombre = api_client.find_moderador_cuadrilla(moderador_id)

        # Construir mensaje final según si está en cuadrilla o no
        if cuadrilla_nombre:
            final_message = f"Se eliminará permanentemente la información del moderador y será removido de la cuadrilla ({cuadrilla_nombre}) asignada."
        else:
            final_message = "Se eliminará permanentemente toda la información del moderador."

        dialog = ui_components.create_double_confirmation_dialog(
            title="⚠️ Eliminar Moderador",
            message=f"¿Está seguro que desea eliminar al moderador {nombre_completo}?",
            final_message=final_message,
            confirm_callback=lambda: self.delete_moderador(moderador_data)
        )

        dialog.open()

    def delete_moderador(self, moderador_data):
        """Eliminar moderador definitivamente"""
        try:
            response = api_client.delete_moderador(moderador_data)
            nombre_completo = f"{moderador_data.get('nombre', '')} {moderador_data.get('apellidos', '')}"
            self.show_success_dialog(
                f"Moderador {nombre_completo} eliminado exitosamente",
                lambda: self.load_moderadores_data()
            )
        except Exception as e:
            self.show_error_dialog(f"Error al eliminar moderador: {str(e)}")

    def get_moderadores_for_selection(self):
        """Obtener lista de moderadores para selección en otras pantallas"""
        return self.moderadores_data

    def show_error_dialog(self, message):
        """Mostrar dialog de error"""
        dialog = ui_components.create_error_dialog(message)
        dialog.open()

    def show_success_dialog(self, message, callback=None):
        """Mostrar dialog de éxito"""
        dialog = ui_components.create_success_dialog(message, callback)
        dialog.open()

    def go_back_to_main(self):
        """Volver al menú principal"""
        if self.main_screen:
            self.main_screen.go_back_to_main('personal')


# Instancia para uso directo
moderadores_manager = ModeradoresManager()