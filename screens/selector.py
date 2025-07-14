# screens/selector.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.metrics import dp

from screens.chat import ChatNormal
from screens.canal import CanalNoticias

class InterfazMensajeriaSelector(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.layout)

        self.build_selector()
        self.contenido = BoxLayout()
        self.layout.add_widget(self.contenido)

        self.mostrar_chat()

    def build_selector(self):
        selector = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
        btn_chat = Button(text="Chat", on_release=lambda x: self.mostrar_chat())
        btn_canal = Button(text="Canal", on_release=lambda x: self.mostrar_canal())

        selector.add_widget(btn_chat)
        selector.add_widget(btn_canal)
        self.layout.add_widget(selector)

    def mostrar_chat(self):
        self.contenido.clear_widgets()
        self.contenido.add_widget(ChatNormal())

    def mostrar_canal(self):
        self.contenido.clear_widgets()
        self.contenido.add_widget(CanalNoticias())
