"""
Componentes UI reutilizables para sistema de personal
Dialogs, dropdowns y widgets estandarizados
"""

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.card import MDCard
from kivymd.uix.progressbar import MDProgressBar
from kivy.metrics import dp
from .utils import PersonalUtils


class PersonalUIComponents:
    """Clase con componentes UI reutilizables para el sistema de personal"""

    @staticmethod
    def create_confirmation_dialog(title, message, confirm_callback, cancel_callback=None):
        """
        Crear dialog de confirmación estándar
        """
        def on_confirm(*args):
            dialog.dismiss()
            if confirm_callback:
                confirm_callback()

        def on_cancel(*args):
            dialog.dismiss()
            if cancel_callback:
                cancel_callback()

        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(
                    text="CANCELAR",
                    theme_text_color="Primary",
                    on_release=on_cancel
                ),
                MDRaisedButton(
                    text="CONFIRMAR",
                    md_bg_color=PersonalUtils.get_color('error'),
                    on_release=on_confirm
                )
            ]
        )

        return dialog

    @staticmethod
    def create_double_confirmation_dialog(title, message, final_message, confirm_callback):
        """
        Crear dialog de doble confirmación para acciones críticas
        """
        def show_second_confirmation(*args):
            first_dialog.dismiss()

            # Crear segundo dialog personalizado con título ADVERTENCIA
            def on_final_confirm(*args):
                second_dialog.dismiss()
                if confirm_callback:
                    confirm_callback()

            def on_final_cancel(*args):
                second_dialog.dismiss()

            second_dialog = MDDialog(
                title="⚠️ ADVERTENCIA",
                text=final_message,
                buttons=[
                    MDFlatButton(
                        text="CANCELAR",
                        theme_text_color="Primary",
                        on_release=on_final_cancel
                    ),
                    MDRaisedButton(
                        text="ELIMINAR",
                        md_bg_color=PersonalUtils.get_color('error'),
                        on_release=on_final_confirm
                    )
                ]
            )
            second_dialog.open()

        first_dialog = PersonalUIComponents.create_confirmation_dialog(
            title=title,
            message=message,
            confirm_callback=show_second_confirmation
        )

        return first_dialog

    @staticmethod
    def create_info_dialog(title, content, ok_callback=None):
        """
        Crear dialog informativo
        """
        def on_ok(*args):
            dialog.dismiss()
            if ok_callback:
                ok_callback()

        dialog = MDDialog(
            title=title,
            text=content,
            buttons=[
                MDRaisedButton(
                    text="ENTENDIDO",
                    md_bg_color=PersonalUtils.get_color('primary'),
                    on_release=on_ok
                )
            ]
        )

        return dialog

    @staticmethod
    def create_error_dialog(message, callback=None):
        """
        Crear dialog de error estándar
        """
        return PersonalUIComponents.create_info_dialog(
            title="❌ Error",
            content=message,
            ok_callback=callback
        )

    @staticmethod
    def create_success_dialog(message, callback=None):
        """
        Crear dialog de éxito estándar
        """
        return PersonalUIComponents.create_info_dialog(
            title="✅ Éxito",
            content=message,
            ok_callback=callback
        )

    @staticmethod
    def create_loading_dialog(message="🔄 Cargando..."):
        """
        Crear dialog de carga
        """
        content = MDBoxLayout(
            orientation="vertical",
            spacing="15dp",
            size_hint_y=None,
            height="100dp"
        )

        progress_bar = MDProgressBar()
        label = MDLabel(
            text=message,
            halign="center",
            size_hint_y=None,
            height="40dp"
        )

        content.add_widget(progress_bar)
        content.add_widget(label)

        dialog = MDDialog(
            title="Procesando",
            type="custom",
            content_cls=content,
            auto_dismiss=False
        )

        return dialog

    @staticmethod
    def create_talla_ropa_dropdown(button, callback):
        """
        Crear dropdown para tallas de ropa
        """
        menu_items = []

        for talla_option in PersonalUtils.get_talla_ropa_options():
            menu_items.append({
                "text": talla_option['text'],
                "on_release": lambda x=None, talla=talla_option['value']: PersonalUIComponents._on_dropdown_select(
                    button, talla, callback, dropdown_menu
                )
            })

        dropdown_menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=2,
            max_height="200dp",
            position="bottom"
        )

        return dropdown_menu

    @staticmethod
    def create_talla_zapatos_dropdown(button, callback):
        """
        Crear dropdown para tallas de zapatos
        """
        menu_items = []

        for talla in PersonalUtils.get_tallas_zapatos_options():
            menu_items.append({
                "text": f"Talla {talla}",
                "on_release": lambda x, talla_val=talla: PersonalUIComponents._on_dropdown_select(
                    button, talla_val, callback, dropdown_menu
                )
            })

        dropdown_menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=3
        )

        return dropdown_menu

    @staticmethod
    def create_moderadores_dropdown(button, moderadores_list, callback):
        """
        Crear dropdown para selección de moderadores
        """
        menu_items = []

        for moderador in moderadores_list:
            nombre_completo = f"{moderador.get('nombre', '')} {moderador.get('apellidos', '')}"
            menu_items.append({
                "text": nombre_completo,
                "on_release": lambda x, mod=moderador: PersonalUIComponents._on_dropdown_select(
                    button, mod, callback, dropdown_menu
                )
            })

        dropdown_menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
            max_height=dp(300)
        )

        return dropdown_menu

    @staticmethod
    def create_obreros_dropdown(button, obreros_list, callback):
        """
        Crear dropdown para selección de obreros
        """
        menu_items = []

        for obrero in obreros_list:
            nombre_completo = f"{obrero.get('nombre', '')} {obrero.get('apellidos', '')}"
            cedula = obrero.get('cedula', '')
            display_text = f"CI: {cedula} | {nombre_completo}"

            menu_items.append({
                "text": display_text,
                "on_release": lambda x, obr=obrero: PersonalUIComponents._on_dropdown_select(
                    button, obr, callback, dropdown_menu
                )
            })

        dropdown_menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=5,
            max_height=dp(300)
        )

        return dropdown_menu

    @staticmethod
    def _on_dropdown_select(button, selected_value, callback, dropdown_menu):
        """
        Callback interno para selección en dropdown
        """
        dropdown_menu.dismiss()
        if callback:
            callback(selected_value)

    @staticmethod
    def create_form_field(hint_text, text="", required=False, field_type="text"):
        """
        Crear campo de formulario estándar
        """
        field = MDTextField(
            hint_text=hint_text + (" *" if required else ""),
            text=text,
            size_hint_y=None,
            height="56dp"
        )

        # Configuraciones específicas por tipo
        if field_type == "email":
            field.input_type = "mail"  # ← CORRECCIÓN: KivyMD usa 'mail' no 'email'
        elif field_type == "number":
            field.input_filter = "int"
        elif field_type == "phone":
            field.input_filter = "int"

        return field

    @staticmethod
    def create_details_card(title, details_dict):
        """
        Crear card con detalles de información
        """
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            adaptive_height=True,
            padding="16dp",
            spacing="8dp",
            elevation=2
        )

        # Título
        title_label = MDLabel(
            text=title,
            font_style="H6",
            theme_text_color="Primary",
            size_hint_y=None,
            height="32dp"
        )
        card.add_widget(title_label)

        # Detalles
        for key, value in details_dict.items():
            if value:  # Solo mostrar campos con valor
                detail_layout = MDBoxLayout(
                    orientation="horizontal",
                    size_hint_y=None,
                    height="24dp",
                    spacing="8dp"
                )

                key_label = MDLabel(
                    text=f"{key}:",
                    font_style="Body2",
                    theme_text_color="Secondary",
                    size_hint_x=None,
                    width="120dp"
                )

                value_label = MDLabel(
                    text=str(value),
                    font_style="Body2",
                    theme_text_color="Primary"
                )

                detail_layout.add_widget(key_label)
                detail_layout.add_widget(value_label)
                card.add_widget(detail_layout)

        return card

    @staticmethod
    def create_list_item(primary_text, secondary_text="", tertiary_text="", on_release=None):
        """
        Crear item de lista personalizado
        """
        if tertiary_text:
            from kivymd.uix.list import ThreeLineListItem
            item = ThreeLineListItem(
                text=primary_text,
                secondary_text=secondary_text,
                tertiary_text=tertiary_text
            )
        elif secondary_text:
            from kivymd.uix.list import TwoLineListItem
            item = TwoLineListItem(
                text=primary_text,
                secondary_text=secondary_text
            )
        else:
            item = OneLineListItem(text=primary_text)

        if on_release:
            item.on_release = on_release

        return item

    @staticmethod
    def create_action_buttons(actions_list):
        """
        Crear layout con botones de acción
        """
        layout = MDBoxLayout(
            orientation="horizontal",
            spacing="8dp",
            size_hint_y=None,
            height="48dp",
            adaptive_width=True
        )

        for action in actions_list:
            button = MDRaisedButton(
                text=action.get('text', 'Acción'),
                md_bg_color=action.get('color', PersonalUtils.get_color('primary')),
                size_hint_x=None,
                width="120dp",
                on_release=action.get('callback', lambda x: None)
            )
            layout.add_widget(button)

        return layout

    @staticmethod
    def create_search_field(hint_text="Buscar...", on_text_change=None):
        """
        Crear campo de búsqueda con icono
        """
        search_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="56dp",
            spacing="8dp"
        )

        search_field = MDTextField(
            hint_text=hint_text,
            size_hint_x=1
        )

        if on_text_change:
            search_field.bind(text=on_text_change)

        search_layout.add_widget(search_field)

        return search_layout, search_field

    @staticmethod
    def create_empty_state(message, icon="inbox", action_text=None, action_callback=None):
        """
        Crear estado vacío para listas
        """
        layout = MDBoxLayout(
            orientation="vertical",
            spacing="16dp",
            adaptive_height=True,
            padding="32dp"
        )

        # Icono
        from kivymd.uix.label import MDIcon
        icon_widget = MDIcon(
            icon=icon,
            font_size="64dp",
            theme_icon_color="Hint",
            halign="center",
            size_hint_y=None,
            height="80dp"
        )
        layout.add_widget(icon_widget)

        # Mensaje
        message_label = MDLabel(
            text=message,
            halign="center",
            font_style="Body1",
            theme_text_color="Hint",
            size_hint_y=None,
            height="32dp"
        )
        layout.add_widget(message_label)

        # Botón de acción opcional
        if action_text and action_callback:
            action_button = MDRaisedButton(
                text=action_text,
                md_bg_color=PersonalUtils.get_color('primary'),
                size_hint=(None, None),
                size=("200dp", "40dp"),
                pos_hint={"center_x": 0.5},
                on_release=action_callback
            )
            layout.add_widget(action_button)

        return layout

    @staticmethod
    def create_stat_card(title, value, subtitle="", color_name="primary"):
        """
        Crear card con estadística
        """
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height="120dp",
            padding="16dp",
            spacing="4dp",
            elevation=2,
            md_bg_color=PersonalUtils.get_color(color_name)
        )

        # Valor principal
        value_label = MDLabel(
            text=str(value),
            font_style="H3",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            halign="center",
            size_hint_y=None,
            height="48dp"
        )
        card.add_widget(value_label)

        # Título
        title_label = MDLabel(
            text=title,
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            halign="center",
            size_hint_y=None,
            height="24dp"
        )
        card.add_widget(title_label)

        # Subtítulo opcional
        if subtitle:
            subtitle_label = MDLabel(
                text=subtitle,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.6],
                halign="center",
                size_hint_y=None,
                height="16dp"
            )
            card.add_widget(subtitle_label)

        return card


# Instancia singleton para uso global
ui_components = PersonalUIComponents()