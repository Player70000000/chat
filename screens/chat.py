# screens/chat.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock
import requests

from config import API_URL, USUARIO, CANAL

class ChatNormal(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(10)
        self.spacing = dp(10)
        self.build_ui()
        Clock.schedule_interval(self.obtener_mensajes, 3)

    def build_ui(self):
        self.scroll = ScrollView()
        self.mensajes_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.mensajes_layout.bind(minimum_height=self.mensajes_layout.setter("height"))
        self.scroll.add_widget(self.mensajes_layout)
        self.add_widget(self.scroll)

        input_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)

        self.entrada = TextInput(
            hint_text="Escribe MSJ",
            multiline=False,
            foreground_color=(1, 1, 1, 1),
            background_color=(0.1, 0.1, 0.1, 1),
            padding=(10, 10),
            cursor_color=(1, 1, 1, 1)
        )

        btn_enviar = Button(
            text="Enviar",
            size_hint_x=None,
            width=dp(80),
            background_color=(0.2, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        btn_enviar.bind(on_release=self.enviar_mensaje)

        input_layout.add_widget(self.entrada)
        input_layout.add_widget(btn_enviar)
        self.add_widget(input_layout)

        self.obtener_mensajes(0)

    def agregar_mensaje(self, autor, texto):
        msg_label = Label(
            text=f"[b]{autor}:[/b] {texto}",
            markup=True,
            size_hint_y=None,
            height=dp(30),
            color=(1, 1, 1, 1),
            halign="left",
            text_size=(Window.width - 40, None)
        )
        self.mensajes_layout.add_widget(msg_label)
        self.scroll.scroll_y = 0

    def enviar_mensaje(self, instancia):
        texto = self.entrada.text.strip()
        if texto:
            try:
                requests.post(f"{API_URL}/enviar", json={
                    "usuario": USUARIO,
                    "mensaje": texto,
                    "canal": CANAL
                })
                self.entrada.text = ""
                self.obtener_mensajes(0)
            except Exception as e:
                print("[ERROR] No se pudo enviar el mensaje:", e)

    def obtener_mensajes(self, dt):
        try:
            res = requests.get(f"{API_URL}/mensajes?canal={CANAL}")
            mensajes = res.json()
            self.mensajes_layout.clear_widgets()
            for msg in mensajes:
                self.agregar_mensaje(msg['usuario'], msg['mensaje'])
        except Exception as e:
            print("[ERROR] No se pudo obtener mensajes:", e)
