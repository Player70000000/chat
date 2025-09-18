from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp
from typing import Dict, Any, Callable, Optional, List


class ReportCard(MDCard):
    """Tarjeta reutilizable para mostrar reportes"""

    def __init__(self, titulo: str, descripcion: str, color: tuple = (0.95, 0.95, 1, 1),
                 on_click: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.elevation = 3
        self.padding = "20dp"
        self.size_hint_y = None
        self.height = "120dp"
        self.md_bg_color = color

        if on_click:
            self.on_release = on_click

        self.setup_content(titulo, descripcion)

    def setup_content(self, titulo: str, descripcion: str):
        """Configurar contenido de la tarjeta"""
        content = MDBoxLayout(orientation="vertical", spacing="10dp")

        title_label = MDLabel(
            text=titulo,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="30dp"
        )

        desc_label = MDLabel(
            text=descripcion,
            theme_text_color="Secondary",
            font_size="14sp",
            text_size=(None, None)
        )

        content.add_widget(title_label)
        content.add_widget(desc_label)
        self.add_widget(content)


class StatsCard(MDCard):
    """Tarjeta para mostrar estadísticas con datos"""

    def __init__(self, titulo: str, datos: Dict[str, Any], color: tuple = (0.95, 0.95, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.elevation = 2
        self.padding = "15dp"
        self.size_hint_y = None
        self.md_bg_color = color

        self.setup_stats(titulo, datos)

    def setup_stats(self, titulo: str, datos: Dict[str, Any]):
        """Configurar estadísticas en la tarjeta"""
        content = MDBoxLayout(orientation="vertical", spacing="5dp")

        title_label = MDLabel(
            text=titulo,
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        content.add_widget(title_label)

        for key, value in datos.items():
            stat_label = MDLabel(
                text=f"{key}: {value}",
                theme_text_color="Primary",
                font_size="16sp",
                size_hint_y=None,
                height="25dp"
            )
            content.add_widget(stat_label)

        self.height = f"{30 + (len(datos) * 25) + 20}dp"
        self.add_widget(content)


class ExportButton(MDRaisedButton):
    """Botón especializado para exportación de datos"""

    def __init__(self, texto: str, tipo_exportacion: str, on_export: Callable, **kwargs):
        super().__init__(**kwargs)
        self.text = texto
        self.size_hint_y = None
        self.height = "40dp"
        self.tipo_exportacion = tipo_exportacion
        self.on_release = lambda: on_export(self.tipo_exportacion)


class ErrorDisplay(MDBoxLayout):
    """Componente para mostrar errores con opción de reintentar"""

    def __init__(self, mensaje: str, on_retry: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.adaptive_height = True

        error_label = MDLabel(
            text=f"❌ {mensaje}",
            theme_text_color="Error",
            halign="center",
            size_hint_y=None,
            height="40dp"
        )
        self.add_widget(error_label)

        if on_retry:
            retry_btn = MDRaisedButton(
                text="🔄 Reintentar",
                size_hint_y=None,
                height="40dp",
                on_release=lambda x: on_retry()
            )
            self.add_widget(retry_btn)


class LoadingIndicator(MDLabel):
    """Indicador de carga reutilizable"""

    def __init__(self, mensaje: str = "🔄 Cargando datos...", **kwargs):
        super().__init__(**kwargs)
        self.text = mensaje
        self.theme_text_color = "Secondary"
        self.halign = "center"
        self.size_hint_y = None
        self.height = "40dp"


class DataTable(MDCard):
    """Tabla de datos reutilizable para mostrar listas"""

    def __init__(self, titulo: str, headers: List[str], datos: List[Dict], **kwargs):
        super().__init__(**kwargs)
        self.elevation = 1
        self.padding = "15dp"
        self.size_hint_y = None

        self.setup_table(titulo, headers, datos)

    def setup_table(self, titulo: str, headers: List[str], datos: List[Dict]):
        """Configurar tabla con datos"""
        content = MDBoxLayout(orientation="vertical", spacing="10dp")

        # Título
        title_label = MDLabel(
            text=titulo,
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        content.add_widget(title_label)

        # Scroll para los datos
        scroll = MDScrollView()
        table_content = MDBoxLayout(orientation="vertical", spacing="5dp", adaptive_height=True)

        # Headers
        header_layout = MDBoxLayout(orientation="horizontal", spacing="10dp", size_hint_y=None, height="25dp")
        for header in headers:
            header_label = MDLabel(
                text=header,
                theme_text_color="Primary",
                font_style="Caption",
                bold=True
            )
            header_layout.add_widget(header_label)
        table_content.add_widget(header_layout)

        # Datos
        for item in datos:
            row_layout = MDBoxLayout(orientation="horizontal", spacing="10dp", size_hint_y=None, height="25dp")
            for header in headers:
                value = item.get(header.lower().replace(' ', '_'), 'N/A')
                row_label = MDLabel(
                    text=str(value),
                    theme_text_color="Secondary",
                    font_size="14sp"
                )
                row_layout.add_widget(row_label)
            table_content.add_widget(row_layout)

        scroll.add_widget(table_content)
        content.add_widget(scroll)

        # Altura dinámica
        self.height = f"{50 + min(len(datos) * 25, 300)}dp"
        self.add_widget(content)


class SummarySection(MDBoxLayout):
    """Sección de resumen con múltiples estadísticas"""

    def __init__(self, titulo: str, estadisticas: List[Dict], **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "15dp"
        self.adaptive_height = True

        # Título de la sección
        title_label = MDLabel(
            text=titulo,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )
        self.add_widget(title_label)

        # Estadísticas
        for stat in estadisticas:
            stats_card = StatsCard(
                titulo=stat.get('titulo', ''),
                datos=stat.get('datos', {}),
                color=stat.get('color', (0.95, 0.95, 1, 1))
            )
            self.add_widget(stats_card)


class ExportDialog(MDDialog):
    """Dialog especializado para opciones de exportación"""

    def __init__(self, opciones_exportacion: List[Dict], on_export: Callable, **kwargs):
        self.title = "📋 Opciones de Exportación"
        self.type = "custom"
        self.content_cls = self._create_content(opciones_exportacion, on_export)
        super().__init__(**kwargs)

    def _create_content(self, opciones: List[Dict], on_export: Callable):
        """Crear contenido del dialog"""
        content = MDBoxLayout(orientation="vertical", spacing="10dp", adaptive_height=True)

        info_label = MDLabel(
            text="Selecciona el tipo de datos que deseas exportar:",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        content.add_widget(info_label)

        for opcion in opciones:
            btn = ExportButton(
                texto=opcion.get('texto', ''),
                tipo_exportacion=opcion.get('tipo', ''),
                on_export=lambda tipo: self._handle_export(tipo, on_export)
            )
            content.add_widget(btn)

        return content

    def _handle_export(self, tipo: str, callback: Callable):
        """Manejar exportación y cerrar dialog"""
        callback(tipo)
        self.dismiss()


class ChartCard(MDCard):
    """Tarjeta para mostrar gráficos simples (texto por ahora)"""

    def __init__(self, titulo: str, datos_grafico: List[Dict], **kwargs):
        super().__init__(**kwargs)
        self.elevation = 2
        self.padding = "15dp"
        self.size_hint_y = None
        self.md_bg_color = (0.98, 0.98, 1, 1)

        self.setup_chart(titulo, datos_grafico)

    def setup_chart(self, titulo: str, datos: List[Dict]):
        """Configurar representación de gráfico (textual)"""
        content = MDBoxLayout(orientation="vertical", spacing="10dp")

        title_label = MDLabel(
            text=titulo,
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        content.add_widget(title_label)

        for item in datos:
            label = item.get('label', 'Sin etiqueta')
            valor = item.get('valor', 0)
            porcentaje = item.get('porcentaje', 0)

            chart_item = MDLabel(
                text=f"📊 {label}: {valor} ({porcentaje:.1f}%)",
                theme_text_color="Secondary",
                font_size="14sp",
                size_hint_y=None,
                height="25dp"
            )
            content.add_widget(chart_item)

        self.height = f"{50 + len(datos) * 25}dp"
        self.add_widget(content)