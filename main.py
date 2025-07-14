# main.py

from kivy.app import App
from kivy.core.window import Window
from screens.selector import InterfazMensajeriaSelector

class AppMensajeria(App):
    def build(self):
        Window.size = (360, 640)
        return InterfazMensajeriaSelector()

if __name__ == "__main__":
    AppMensajeria().run()
