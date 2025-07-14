# screens/canal.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.core.window import Window

class CanalNoticias(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(10)
        self.spacing = dp(10)
        self.build_ui()

    def build_ui(self):
        label_titulo = Label(
            text="[b]Canal CORPOTÁCHIRA Novedades[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(40),
            color=(0.9, 0.9, 0.1, 1)
        )
        self.add_widget(label_titulo)

        self.scroll = ScrollView()
        self.noticias_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.noticias_layout.bind(minimum_height=self.noticias_layout.setter("height"))
        self.scroll.add_widget(self.noticias_layout)
        self.add_widget(self.scroll)

        noticias = [
            "¡Bienvenidos al canal oficial de reportes!",
            "Mañana se realizará jornada de trabajo en San Cristóbal.",
        ]

        for texto in noticias:
            noticia_label = Label(
                text=f"• {texto}",
                size_hint_y=None,
                height=dp(30),
                color=(1, 1, 1, 1),
                halign="left",
                text_size=(Window.width - 40, None)
            )
            self.noticias_layout.add_widget(noticia_label)
