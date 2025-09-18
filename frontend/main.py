#!/usr/bin/env python3
"""
Empresa Limpieza - Aplicación Móvil KivyMD
Punto de entrada principal
"""

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.metrics import dp

from screens.chat_screen import ChatScreen
from screens.personal_screen import PersonalScreen  
from screens.reportes_screen import ReportesScreen


class TabContent(MDFloatLayout, MDTabsBase):
    """Clase base para el contenido de las pestañas"""
    pass


class CustomBottomNav(MDBoxLayout):
    """Navegación inferior personalizada compatible con KivyMD 1.2.0"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(60)
        self.md_bg_color = [0.2, 0.6, 1, 1]  # Color azul
        self.spacing = 0
        self.current_screen = None
        self.screens = {}
        self.buttons = {}
        
    def add_tab(self, name, text, icon, screen_widget):
        """Agregar una pestaña con su pantalla asociada"""
        self.screens[name] = screen_widget
        
        # Crear contenedor para el botón
        button_container = MDBoxLayout(
            orientation="vertical",
            size_hint_x=1,
            spacing=dp(2),
            adaptive_height=True
        )
        
        # Botón con icono
        button = MDIconButton(
            icon=icon,
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],  # Blanco
            size_hint=(1, None),
            height=dp(32),
            on_release=lambda x, tab_name=name: self.switch_tab(tab_name)
        )
        
        # Etiqueta de texto
        label = MDLabel(
            text=text,
            font_size=dp(10),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],  # Blanco
            halign="center",
            size_hint_y=None,
            height=dp(16)
        )
        
        button_container.add_widget(button)
        button_container.add_widget(label)
        self.add_widget(button_container)
        
        self.buttons[name] = (button, label)
        
        # Si es la primera pestaña, activarla
        if len(self.screens) == 1:
            self.switch_tab(name)
    
    def switch_tab(self, tab_name):
        """Cambiar a una pestaña específica"""
        if tab_name not in self.screens:
            return
            
        # Actualizar colores de botones
        for name, (button, label) in self.buttons.items():
            if name == tab_name:
                # Pestaña activa - naranja
                button.icon_color = [1, 0.6, 0, 1]
                label.text_color = [1, 0.6, 0, 1]
            else:
                # Pestaña inactiva - blanco
                button.icon_color = [1, 1, 1, 0.7]
                label.text_color = [1, 1, 1, 0.7]
        
        # Notificar cambio de pantalla al padre
        if hasattr(self.parent, 'switch_screen'):
            self.parent.switch_screen(tab_name)


class MainLayout(MDBoxLayout):
    """Layout principal con navegación de pestañas"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.current_tab = "chat"
        self.setup_ui()
        
    def setup_ui(self):
        # Barra superior
        self.toolbar = MDTopAppBar(
            title="Empresa Limpieza",
            elevation=2,
            md_bg_color=[0.2, 0.6, 1, 1]  # Color azul
        )
        
        # Contenedor para las pantallas
        self.content_container = MDBoxLayout()
        
        # Navegación inferior personalizada
        self.bottom_nav = CustomBottomNav()
        
        # Agregar pestañas
        self.chat_screen = ChatScreen()
        self.personal_screen = PersonalScreen()
        self.reportes_screen = ReportesScreen()
        
        # Configurar referencia al layout principal en cada pantalla
        self.chat_screen.main_layout = self
        self.personal_screen.main_layout = self
        self.reportes_screen.main_layout = self
        
        self.bottom_nav.add_tab("chat", "Chat", "chat-processing", self.chat_screen)
        self.bottom_nav.add_tab("personal", "Personal", "account-group", self.personal_screen)
        self.bottom_nav.add_tab("reportes", "Reportes", "file-document-multiple", self.reportes_screen)
        
        # Ensamblar layout
        self.add_widget(self.toolbar)
        self.add_widget(self.content_container)
        self.add_widget(self.bottom_nav)
        
        # Mostrar la primera pantalla
        self.switch_screen("chat")
        
    def switch_screen(self, screen_name):
        """Cambiar la pantalla visible"""
        self.content_container.clear_widgets()
        if screen_name in self.bottom_nav.screens:
            self.current_tab = screen_name
            self.content_container.add_widget(self.bottom_nav.screens[screen_name])
            
    def go_back_to_main(self, tab_name):
        """Volver a la pantalla principal de una pestaña"""
        if hasattr(self.bottom_nav.screens[tab_name], 'show_main_screen'):
            self.bottom_nav.screens[tab_name].show_main_screen()
            
    def show_channel_list(self):
        """Método de compatibilidad para chat screen"""
        if hasattr(self.chat_screen, 'show_main_screen'):
            self.chat_screen.show_main_screen()
            
    def load_channels(self):
        """Método de compatibilidad para recargar canales"""
        if hasattr(self.chat_screen, 'load_channels'):
            self.chat_screen.load_channels()


class EmpresaLimpiezaApp(MDApp):
    def build(self):
        # Configurar tema
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"
        self.title = "Empresa Limpieza"
        
        # Configurar ventana móvil
        Window.size = (360, 640)
        Window.minimum_width = 300
        Window.minimum_height = 500
        
        return MainLayout()


if __name__ == "__main__":
    EmpresaLimpiezaApp().run()