import requests
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

from config import API_URL, USUARIO

class MenuChatDesplegable(RelativeLayout):
    """MenÃº desplegable para el chat - BASADO EN EL SELECTOR QUE FUNCIONA"""
    def __init__(self, opciones, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        
        # Crear el menÃº usando la misma lÃ³gica del selector
        self.crear_menu(opciones)
    
    def crear_menu(self, opciones):
        """Crear el contenido del menÃº - ESTILOS IDÃ‰NTICOS AL SELECTOR"""
        # Layout principal del menÃº
        menu_layout = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(150, len(opciones) * 40)  # Mismo tamaÃ±o que el selector
        )
        
        # Crear botones para cada opciÃ³n - ESTILOS EXACTOS DEL SELECTOR
        for opcion in opciones:
            btn = Button(
                text=opcion,
                size_hint=(1, None),
                height=40,
                background_color=(0.2, 0.2, 0.2, 0.9)  # MISMO COLOR QUE EL SELECTOR
            )
            btn.bind(on_press=lambda instance, opt=opcion: self.seleccionar_opcion(opt))
            menu_layout.add_widget(btn)
        
        self.add_widget(menu_layout)
        self.menu_layout = menu_layout
    
    def update_rect(self, *args):
        """MÃ©todo removido - no necesario con el estilo del selector"""
        pass
    
    def seleccionar_opcion(self, opcion):
        """Manejar selecciÃ³n de opciÃ³n"""
        self.callback(opcion)
        self.cerrar_menu()
    
    def cerrar_menu(self):
        """Cerrar el menÃº"""
        if self.parent:
            self.parent.remove_widget(self)

class ChatNormal(Screen):
    def __init__(self, nombre_canal=None, **kwargs):
        super().__init__(**kwargs)
        # Si no se pasa nombre, usar None y no cargar mensajes hasta set_canal()
        self.nombre_canal = nombre_canal
        self.name = f"chat_{nombre_canal}" if nombre_canal else "chat_canal"
        self.menu_actual = None  # CAMBIO: usar menu_actual como en el selector
        
        self.setup_ui()

        # Solo cargar mensajes si hay un canal definido
        if self.nombre_canal:
            Clock.schedule_once(lambda dt: self.cargar_mensajes(), 1)
            Clock.schedule_interval(lambda dt: self.cargar_mensajes(), 5)

    def on_touch_down(self, touch):
        """Detectar toques para cerrar menÃº al tocar fuera"""
        # Si hay un menÃº abierto y el toque no estÃ¡ dentro del menÃº
        if self.menu_actual and not self.menu_actual.collide_point(*touch.pos):
            self.cerrar_menu_actual()
            return True
        
        return super().on_touch_down(touch)

    def cerrar_menu_actual(self):
        """Cerrar el menÃº actual - IGUAL QUE EN SELECTOR"""
        if self.menu_actual and self.menu_actual.parent:
            self.remove_widget(self.menu_actual)
        self.menu_actual = None

    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal
        layout = BoxLayout(orientation='vertical')

        # Cabecera con menÃº - USANDO LA MISMA ESTRUCTURA DEL SELECTOR
        top_bar = BoxLayout(size_hint_y=None, height=50, padding=5, spacing=10)
        
        # BotÃ³n volver
        btn_volver = Button(
            text="â†", 
            size_hint_x=None, 
            width=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_volver.bind(on_press=self.volver)
        
        # TÃ­tulo del canal (expandible)
        self.lbl_titulo = Label(
            text=f"[b]# {self.nombre_canal}[/b]" if self.nombre_canal else "[b]Selecciona un canal[/b]", 
            markup=True,
            size_hint_x=1
        )
        
        # BotÃ³n menÃº desplegable - IGUAL QUE EN SELECTOR
        self.btn_menu = Button(
            text='â‹®',
            size_hint_x=None,
            width=50,
            font_size=20,
            background_color=(0.7, 0.7, 0.7, 1)
        )
        self.btn_menu.bind(on_press=self.mostrar_menu)

        top_bar.add_widget(btn_volver)
        top_bar.add_widget(self.lbl_titulo)
        top_bar.add_widget(self.btn_menu)

        # Mensajes (sin cambios - mantiene toda tu funcionalidad)
        self.mensajes_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5, padding=10)
        self.mensajes_layout.bind(minimum_height=self.mensajes_layout.setter('height'))

        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.scroll.add_widget(self.mensajes_layout)

        # Input y botÃ³n (sin cambios)
        self.input = TextInput(hint_text='Escribe un mensaje...', size_hint=(0.8, 1), multiline=False)
        self.boton = Button(text='Enviar', size_hint=(0.2, 1))
        self.boton.bind(on_press=self.enviar_mensaje)

        input_box = BoxLayout(size_hint=(1, 0.1), padding=5, spacing=5)
        input_box.add_widget(self.input)
        input_box.add_widget(self.boton)

        # Ensamblar layout
        layout.add_widget(top_bar)
        layout.add_widget(self.scroll)
        layout.add_widget(input_box)
        self.add_widget(layout)

    def set_canal(self, nombre_canal):
        """Establecer el canal actual"""
        self.nombre_canal = nombre_canal
        self.lbl_titulo.text = f"[b]# {nombre_canal}[/b]"
        # Recargar mensajes del nuevo canal
        self.cargar_mensajes()
        # Iniciar auto-actualizaciÃ³n si no estÃ¡ activa
        Clock.schedule_interval(lambda dt: self.cargar_mensajes(), 5)

    def mostrar_menu(self, instance):
        """Mostrar menÃº desplegable - COPIADO EXACTO DEL SELECTOR"""
        # Cerrar menÃº anterior si existe
        if self.menu_actual:
            self.cerrar_menu_actual()
            return
        
        # Opciones del menÃº
        opciones = ["Ajustes del canal", "Futuras opciones"]
        
        # Calcular posiciÃ³n del menÃº - TAMAÃ‘O AJUSTADO AL SELECTOR
        menu_width = 150  # Mismo que el selector
        menu_height = len(opciones) * 40
        
        # PosiciÃ³n X: alineado a la derecha del botÃ³n, pero dentro de pantalla
        pos_x = instance.x + instance.width - menu_width
        # PosiciÃ³n Y: debajo del botÃ³n
        pos_y = instance.y - menu_height
        
        # Crear menÃº desplegable
        self.menu_actual = MenuChatDesplegable(
            opciones=opciones,
            callback=self.manejar_seleccion_menu,
            size_hint=(None, None),
            size=(menu_width, menu_height),
            pos=(pos_x, pos_y)
        )
        
        # Agregar menÃº al layout principal
        self.add_widget(self.menu_actual)
    
    def manejar_seleccion_menu(self, opcion):
        """Manejar la selecciÃ³n del menÃº"""
        if opcion == "Ajustes del canal":
            self.abrir_configuracion_canal()
        elif opcion == "Futuras opciones":
            self.mostrar_popup("Info", "Funcionalidad en desarrollo")
        
        # Cerrar menÃº
        self.cerrar_menu_actual()
    
    def abrir_configuracion_canal(self):
        """Navegar a configuraciÃ³n del canal"""
        if hasattr(self.manager, 'get_screen'):
            try:
                config_screen = self.manager.get_screen('config_canal')
                config_screen.set_canal(self.nombre_canal)
                self.manager.current = 'config_canal'
            except:
                print(f"Error: No se pudo encontrar la pantalla 'config_canal'")

    # MÃ‰TODOS ORIGINALES - SIN CAMBIOS (mantienen toda tu funcionalidad)
    def cargar_mensajes(self):
        # No cargar mensajes si no hay canal seleccionado
        if not self.nombre_canal:
            return
            
        try:
            response = requests.get(f"{API_URL}/mensajes/{self.nombre_canal}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                mensajes = data.get('mensajes', [])
                self.mensajes_layout.clear_widgets()
                for msg in mensajes:
                    texto = f"[b]{msg.get('usuario')}[/b]: {msg.get('mensaje')}"
                    lbl = Label(text=texto, size_hint_y=None, height=30, markup=True, halign='left', valign='middle')
                    lbl.text_size = (self.width - 40, None)
                    self.mensajes_layout.add_widget(lbl)
                self.scroll_to_bottom()
        except Exception as e:
            print(f"Error cargando mensajes: {e}")

    def scroll_to_bottom(self):
        """Hacer scroll al final de los mensajes"""
        if self.mensajes_layout.children:
            Clock.schedule_once(lambda dt: self.scroll.scroll_to(self.mensajes_layout.children[0]), 0.1)

    def enviar_mensaje(self, instance):
        # No enviar si no hay canal seleccionado
        if not self.nombre_canal:
            self.mostrar_popup("Error", "No hay canal seleccionado")
            return
            
        texto = self.input.text.strip()
        if not texto:
            return
        
        datos = {
            "usuario": USUARIO,
            "mensaje": texto,
            "canal": self.nombre_canal
        }
        
        try:
            response = requests.post(f"{API_URL}/enviar", json=datos, timeout=5)
            if response.status_code == 200 or response.status_code == 201:
                self.input.text = ""
                self.cargar_mensajes()
            else:
                self.mostrar_popup("Error", "No se pudo enviar el mensaje.")
        except Exception:
            self.mostrar_popup("Error", "Error de conexiÃ³n al enviar mensaje.")

    def mostrar_popup(self, titulo, mensaje):
        """Mostrar popup de notificaciÃ³n"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=mensaje))
        
        btn_ok = Button(text="OK", size_hint_y=None, height=40)
        popup = Popup(title=titulo, content=content, size_hint=(0.8, 0.3))
        btn_ok.bind(on_press=popup.dismiss)
        content.add_widget(btn_ok)
        popup.open()

    def volver(self, instance):
        """Volver al selector de canales"""
        # Cerrar menÃº si estÃ¡ abierto antes de navegar
        self.cerrar_menu_actual()
        self.manager.current = 'canal_selector'

    def on_leave(self):
        """Al salir de la pantalla, cerrar el menÃº"""
        self.cerrar_menu_actual()
        super().on_leave()