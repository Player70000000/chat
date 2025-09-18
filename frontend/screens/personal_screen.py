"""
Personal Screen - Coordinador principal para gestión de personal
Versión modularizada que utiliza managers especializados
"""

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivy.metrics import dp

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import API_BASE_URL

# Importar managers modulares
from screens.personal_modules import (
    ObrerosManager,
    ModeradoresManager,
    CuadrillasManager,
    ui_components,
    utils
)


class PersonalScreen(MDBoxLayout):
    """
    Pantalla principal de gestión de personal
    Coordinador que orquesta los managers especializados
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.main_layout = None  # Referencia al layout principal

        # Inicializar managers especializados
        self.cuadrillas_manager = CuadrillasManager(main_screen=self)
        self.moderadores_manager = ModeradoresManager(main_screen=self)
        self.obreros_manager = ObrerosManager(main_screen=self)

        # Estado actual
        self.current_manager = None

        self.setup_ui()

    def setup_ui(self):
        """Configurar interfaz principal"""
        # Screen manager para diferentes vistas
        self.screen_manager = MDScreenManager()

        # Pantalla del menú principal
        self.main_screen = MDScreen(name="main_menu")
        self.setup_main_menu()

        # Agregar pantalla principal al manager
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.current = "main_menu"

        # Agregar screen manager al layout principal
        self.add_widget(self.screen_manager)

    def setup_main_menu(self):
        """Configurar menú principal de gestión de personal"""
        layout = MDBoxLayout(orientation="vertical", spacing="20dp", padding="20dp")

        # Título principal
        title = MDLabel(
            text="Sistema de Gestión de Personal",
            font_style="H4",
            theme_text_color="Primary",
            halign="center",
            size_hint_y=None,
            height="60dp"
        )
        layout.add_widget(title)

        # Contenedor de cards
        cards_container = MDBoxLayout(
            orientation="vertical",
            spacing="15dp",
            adaptive_height=True
        )

        # Card de Cuadrillas
        cuadrillas_card = self.create_module_card(
            title="👷‍♂️ Gestión de Cuadrillas",
            description="Crear, editar y administrar cuadrillas de trabajo.\nOrganiza los equipos por actividades.",
            color=[0.95, 0.95, 1, 1],  # Ligero tinte azul
            callback=self.switch_to_cuadrillas
        )
        cards_container.add_widget(cuadrillas_card)

        # Card de Moderadores
        moderadores_card = self.create_module_card(
            title="👤 Gestión de Moderadores",
            description="Registrar y administrar moderadores de cuadrilla.\nSupervisa y coordina los equipos.",
            color=[0.95, 1, 0.95, 1],  # Ligero tinte verde
            callback=self.switch_to_moderadores
        )
        cards_container.add_widget(moderadores_card)

        # Card de Obreros
        obreros_card = self.create_module_card(
            title="👷 Gestión de Obreros",
            description="Registrar y administrar obreros de la empresa.\nMantén el directorio de personal actualizado.",
            color=[1, 1, 0.95, 1],  # Ligero tinte amarillo
            callback=self.switch_to_obreros
        )
        cards_container.add_widget(obreros_card)

        # Scroll container para las cards
        scroll = MDScrollView()
        scroll.add_widget(cards_container)
        layout.add_widget(scroll)

        self.main_screen.add_widget(layout)

    def create_module_card(self, title, description, color, callback):
        """Crear card para un módulo del sistema - TARJETA CLICKEABLE COMPLETA"""
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height="140dp",
            padding="20dp",
            spacing="10dp",
            elevation=3,
            md_bg_color=color,  # Color de fondo según módulo
            on_release=lambda x: callback()  # ← TODA LA TARJETA ES CLICKEABLE
        )

        # Título
        title_label = MDLabel(
            text=title,
            font_style="H6",
            theme_text_color="Primary",
            size_hint_y=None,
            height="40dp"
        )
        card.add_widget(title_label)

        # Descripción
        desc_label = MDLabel(
            text=description,
            font_style="Body2",
            theme_text_color="Secondary",
            text_size=(None, None)
        )
        card.add_widget(desc_label)

        # Tip visual (sin botón)
        tip_label = MDLabel(
            text="💡 Toca la tarjeta para acceder",
            font_size="12sp",
            theme_text_color="Hint",
            size_hint_y=None,
            height="20dp",
            halign="center"
        )
        card.add_widget(tip_label)

        return card

    def switch_to_cuadrillas(self):
        """Cambiar a gestión de cuadrillas"""
        print("🚧 Cambiando a gestión de cuadrillas...")
        self.current_manager = 'cuadrillas'
        self._switch_to_manager_screen(self.cuadrillas_manager)

    def switch_to_moderadores(self):
        """Cambiar a gestión de moderadores"""
        print("👤 Cambiando a gestión de moderadores...")
        self.current_manager = 'moderadores'
        self._switch_to_manager_screen(self.moderadores_manager)

    def switch_to_obreros(self):
        """Cambiar a gestión de obreros"""
        print("👷 Cambiando a gestión de obreros...")
        self.current_manager = 'obreros'
        self._switch_to_manager_screen(self.obreros_manager)

    def _switch_to_manager_screen(self, manager):
        """Cambiar a pantalla de manager específico"""
        try:
            # Remover pantalla del manager si ya existe
            manager_screen_name = f"{self.current_manager}_screen"

            if self.screen_manager.has_screen(manager_screen_name):
                self.screen_manager.remove_widget(
                    self.screen_manager.get_screen(manager_screen_name)
                )

            # Crear nueva pantalla del manager
            manager_screen = MDScreen(name=manager_screen_name)
            manager_layout = manager.create_main_layout()
            manager_screen.add_widget(manager_layout)

            # Agregar y cambiar a la pantalla
            self.screen_manager.add_widget(manager_screen)
            self.screen_manager.current = manager_screen_name

            print(f"✅ Cambiado exitosamente a {self.current_manager}")

        except Exception as e:
            print(f"❌ Error al cambiar a {self.current_manager}: {e}")
            self.show_error_dialog(f"Error al abrir módulo: {str(e)}")

    def go_back_to_main(self, from_tab=None):
        """Volver al menú principal desde cualquier manager"""
        print("🔙 Volviendo al menú principal...")

        try:
            # Cambiar a pantalla principal
            self.screen_manager.current = "main_menu"

            # Limpiar manager actual
            self.current_manager = None

            print("✅ Regresado al menú principal exitosamente")

        except Exception as e:
            print(f"❌ Error al regresar al menú principal: {e}")

    def show_main_screen(self):
        """Mostrar pantalla principal - método de compatibilidad"""
        self.go_back_to_main()

    def show_error_dialog(self, message):
        """Mostrar dialog de error"""
        dialog = ui_components.create_error_dialog(message)
        dialog.open()

    def show_success_dialog(self, message, callback=None):
        """Mostrar dialog de éxito"""
        dialog = ui_components.create_success_dialog(message, callback)
        dialog.open()

    # ===========================================
    # MÉTODOS DE COMPATIBILIDAD CON MAIN.PY
    # ===========================================

    def switch_screen(self, screen_name):
        """Método de compatibilidad para navegación externa"""
        if screen_name == "main_menu":
            self.go_back_to_main()
        elif screen_name == "cuadrillas":
            self.switch_to_cuadrillas()
        elif screen_name == "moderadores":
            self.switch_to_moderadores()
        elif screen_name == "obreros":
            self.switch_to_obreros()

    def get_current_screen_name(self):
        """Obtener nombre de pantalla actual"""
        if self.current_manager:
            return f"{self.current_manager}_screen"
        return "main_menu"

    # ===========================================
    # MÉTODOS PARA ACCESO A MANAGERS EXTERNOS
    # ===========================================

    def get_cuadrillas_manager(self):
        """Obtener manager de cuadrillas"""
        return self.cuadrillas_manager

    def get_moderadores_manager(self):
        """Obtener manager de moderadores"""
        return self.moderadores_manager

    def get_obreros_manager(self):
        """Obtener manager de obreros"""
        return self.obreros_manager

    def reload_all_data(self):
        """Recargar datos de todos los managers"""
        try:
            if hasattr(self.cuadrillas_manager, 'load_cuadrillas_data'):
                self.cuadrillas_manager.load_cuadrillas_data()
            if hasattr(self.moderadores_manager, 'load_moderadores_data'):
                self.moderadores_manager.load_moderadores_data()
            if hasattr(self.obreros_manager, 'load_obreros_data'):
                self.obreros_manager.load_obreros_data()

            print("✅ Datos de todos los managers recargados")

        except Exception as e:
            print(f"❌ Error al recargar datos: {e}")
            self.show_error_dialog(f"Error al recargar datos: {str(e)}")


# ===========================================
# CLASES DE COMPATIBILIDAD (DEPRECATED)
# ===========================================

class CuadrillaListItem:
    """Clase de compatibilidad - DEPRECATED - Usar CuadrillasManager"""
    def __init__(self, *args, **kwargs):
        print("⚠️ DEPRECATED: CuadrillaListItem - Usar CuadrillasManager")
        pass

class EmpleadoListItem:
    """Clase de compatibilidad - DEPRECATED - Usar ObrerosManager/ModeradoresManager"""
    def __init__(self, *args, **kwargs):
        print("⚠️ DEPRECATED: EmpleadoListItem - Usar managers especializados")
        pass

class CuadrillasManagementScreen:
    """Clase de compatibilidad - DEPRECATED - Usar CuadrillasManager"""
    def __init__(self, *args, **kwargs):
        print("⚠️ DEPRECATED: CuadrillasManagementScreen - Usar CuadrillasManager")
        pass

class EmpleadosManagementScreen:
    """Clase de compatibilidad - DEPRECATED - Usar managers especializados"""
    def __init__(self, *args, **kwargs):
        print("⚠️ DEPRECATED: EmpleadosManagementScreen - Usar managers especializados")
        pass