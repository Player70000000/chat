from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import API_BASE_URL

# Importar módulos especializados
from .reportes_modules import (
    ReportesObrerosManager,
    ReportesModeradoresManager,
    ReportesGeneralesManager,
    ReportCard
)




class ReportesScreen(MDBoxLayout):
    """Coordinador principal del módulo de reportes modular"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.main_layout = None

        # Inicializar gestores especializados
        self.reportes_obreros = ReportesObrerosManager(self)
        self.reportes_moderadores = ReportesModeradoresManager(self)
        self.reportes_generales = ReportesGeneralesManager(self)

        self.setup_ui()

    def setup_ui(self):
        """Configurar interfaz del menú principal de reportes"""
        # Screen manager para navegación
        self.screen_manager = MDScreenManager()

        # Pantalla del menú principal
        self.main_screen = MDScreen(name="menu_principal")
        self.setup_menu_principal()

        self.screen_manager.add_widget(self.main_screen)
        self.add_widget(self.screen_manager)

    def setup_menu_principal(self):
        """Configurar menú principal con las 3 opciones de reportes"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")

        # Top bar
        top_bar = MDTopAppBar(
            title="📊 Sistema de Reportes Modular",
            right_action_items=[["chart-line", lambda x: None]]
        )

        # Contenido del menú
        content_scroll = MDScrollView()
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp", adaptive_height=True)

        # Las 3 opciones principales de reportes
        reportes_opciones = [
            {
                "titulo": "👷‍♂️ Reportes de Obreros",
                "descripcion": "Estadísticas detalladas, distribución de tallas y análisis de obreros",
                "color": (0.95, 1, 0.95, 1),
                "accion": self.mostrar_reportes_obreros
            },
            {
                "titulo": "👤 Reportes de Moderadores",
                "descripcion": "Análisis específico de moderadores y comparaciones",
                "color": (0.95, 0.95, 1, 1),
                "accion": self.mostrar_reportes_moderadores
            },
            {
                "titulo": "📈 Reportes Generales",
                "descripcion": "Resumen del sistema, chat, cuadrillas y estadísticas globales",
                "color": (1, 0.95, 1, 1),
                "accion": self.mostrar_reportes_generales
            }
        ]

        for opcion in reportes_opciones:
            reporte_card = ReportCard(
                titulo=opcion["titulo"],
                descripcion=opcion["descripcion"],
                color=opcion["color"],
                on_click=opcion["accion"]
            )
            content_layout.add_widget(reporte_card)

        # Información del sistema
        from .reportes_modules.report_components import StatsCard
        info_card = StatsCard(
            titulo="💡 Información del Sistema",
            datos={
                "🔄 Estado": "Operativo",
                "📊 Módulos": "3 tipos de reportes",
                "🎯 Arquitectura": "Modular",
                "📡 Datos": "Tiempo real"
            },
            color=(0.98, 0.98, 0.98, 1)
        )
        content_layout.add_widget(info_card)

        content_scroll.add_widget(content_layout)

        layout.add_widget(top_bar)
        layout.add_widget(content_scroll)

        self.main_screen.add_widget(layout)

    def mostrar_reportes_obreros(self):
        """Mostrar módulo de reportes de obreros"""
        self.reportes_obreros.mostrar_reportes_obreros()

    def mostrar_reportes_moderadores(self):
        """Mostrar módulo de reportes de moderadores"""
        self.reportes_moderadores.mostrar_reportes_moderadores()

    def mostrar_reportes_generales(self):
        """Mostrar módulo de reportes generales"""
        self.reportes_generales.mostrar_reportes_generales()

    def mostrar_menu_reportes(self):
        """Volver al menú principal de reportes"""
        self.clear_widgets()
        self.setup_ui()

    def show_main_screen(self):
        """Mostrar la pantalla principal de reportes (compatibilidad)"""
        self.mostrar_menu_reportes()