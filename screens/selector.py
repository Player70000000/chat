import requests
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.uix.relativelayout import RelativeLayout

from config import API_URL, USUARIO

class MenuDesplegable(RelativeLayout):
    """Menú desplegable personalizado"""
    def __init__(self, opciones, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.menu_abierto = False
        
        # Crear el menú
        self.crear_menu(opciones)
    
    def crear_menu(self, opciones):
        """Crear el contenido del menú"""
        # Layout principal del menú
        menu_layout = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(150, len(opciones) * 40)
        )
        
        # Crear botones para cada opción
        for opcion in opciones:
            btn = Button(
                text=opcion,
                size_hint=(1, None),
                height=40,
                background_color=(0.2, 0.2, 0.2, 0.9)
            )
            btn.bind(on_press=lambda instance, opt=opcion: self.seleccionar_opcion(opt))
            menu_layout.add_widget(btn)
        
        self.add_widget(menu_layout)
        self.menu_layout = menu_layout
    
    def seleccionar_opcion(self, opcion):
        """Manejar selección de opción"""
        self.callback(opcion)
        self.cerrar_menu()
    
    def cerrar_menu(self):
        """Cerrar el menú"""
        if self.parent:
            self.parent.remove_widget(self)

class SelectorCanales(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.menu_actual = None

        # Header principal: "Canales" y botón menú
        header_layout = BoxLayout(size_hint_y=None, height=50, padding=[10, 5])
        titulo_canales = Label(text='[b]Canales[/b]', markup=True, halign='left', valign='middle', 
                              size_hint_x=0.8)
        titulo_canales.bind(size=titulo_canales.setter('text_size'))

        self.boton_menu = Button(text="≡", size_hint=(None, None), size=(40, 40))
        self.boton_menu.bind(on_press=self.mostrar_menu)

        header_layout.add_widget(titulo_canales)
        header_layout.add_widget(self.boton_menu)
        self.layout.add_widget(header_layout)

        # Subtítulo "Lista de canales" (sin botón)
        subtitulo_layout = BoxLayout(size_hint_y=None, height=40, padding=[10, 0])
        subtitulo = Label(text='Lista de canales', halign='left', valign='middle',
                         color=(0.8, 0.8, 0.8, 1))
        subtitulo.bind(size=subtitulo.setter('text_size'))
        subtitulo_layout.add_widget(subtitulo)
        self.layout.add_widget(subtitulo_layout)

        # Scroll de canales
        self.scroll = ScrollView(size_hint=(1, 1))
        self.lista_botones = BoxLayout(orientation='vertical', size_hint_y=None)
        self.lista_botones.bind(minimum_height=self.lista_botones.setter('height'))
        self.scroll.add_widget(self.lista_botones)

        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

        Clock.schedule_once(lambda dt: self.cargar_canales(), 0.5)

    def on_touch_down(self, touch):
        """NUEVO: Detectar toques para cerrar menú al tocar fuera"""
        # Si hay un menú abierto y el toque no está dentro del menú
        if self.menu_actual and not self.menu_actual.collide_point(*touch.pos):
            self.cerrar_menu_actual()
            return True  # Consumir el evento para que no se propague
        
        # Continuar con el comportamiento normal
        return super().on_touch_down(touch)

    def mostrar_menu(self, instance):
        """Mostrar menú desplegable"""
        # Cerrar menú anterior si existe
        if self.menu_actual:
            self.cerrar_menu_actual()
            return
        
        # Opciones del menú
        opciones = ["Crear Canal", "Cerrar Sesión", "Futuras opciones"]
        
        # Calcular posición del menú
        menu_width = 150
        menu_height = len(opciones) * 40
        
        # Posición X: alineado a la derecha del botón, pero dentro de pantalla
        pos_x = instance.x + instance.width - menu_width
        # Posición Y: debajo del botón
        pos_y = instance.y - menu_height
        
        # Crear menú desplegable
        self.menu_actual = MenuDesplegable(
            opciones=opciones,
            callback=self.manejar_seleccion_menu,
            size_hint=(None, None),
            size=(menu_width, menu_height),
            pos=(pos_x, pos_y)
        )
        
        # Agregar menú al layout principal
        self.add_widget(self.menu_actual)
    
    def cerrar_menu_actual(self):
        """Cerrar el menú actual"""
        if self.menu_actual and self.menu_actual.parent:
            self.remove_widget(self.menu_actual)
        self.menu_actual = None
    
    def manejar_seleccion_menu(self, opcion):
        """Manejar la selección del menú"""
        if opcion == "Crear Canal":
            self.abrir_ventana_crear()
        elif opcion == "Cerrar Sesión":
            self.cerrar_sesion()
        elif opcion == "Futuras opciones":
            self.mostrar_popup("Info", "Funcionalidad en desarrollo")
        
        # Cerrar menú
        self.cerrar_menu_actual()
    
    def cerrar_sesion(self):
        """Manejar cierre de sesión"""
        # Por ahora volver a la pantalla principal
        # En el futuro se puede modificar para cerrar sesión real
        try:
            # Buscar el ScreenManager principal
            root_manager = self.manager
            while hasattr(root_manager, 'parent') and root_manager.parent:
                if hasattr(root_manager.parent, 'manager'):
                    root_manager = root_manager.parent.manager
                    break
                root_manager = root_manager.parent
            
            # Si encontramos un manager con screen 'main', ir allí
            if hasattr(root_manager, 'has_screen') and root_manager.has_screen('main'):
                root_manager.current = 'main'
            else:
                self.mostrar_popup("Info", "Función de cerrar sesión en desarrollo")
        except Exception:
            self.mostrar_popup("Info", "Función de cerrar sesión en desarrollo")

    def on_enter(self):
        """Se ejecuta cada vez que se entra a esta pantalla"""
        self.cargar_canales()

    def cargar_canales(self):
        """Cargar canales desde el servidor"""
        self.lista_botones.clear_widgets()
        
        # Indicador de carga
        loading_label = Label(text="Cargando canales...", size_hint_y=None, height=50)
        self.lista_botones.add_widget(loading_label)
        
        try:
            response = requests.get(f"{API_URL}/canales", timeout=8)
            self.lista_botones.clear_widgets()
            
            if response.status_code == 200:
                data = response.json()
                # Manejar ambos formatos: {"canales": []} o directamente []
                if isinstance(data, dict):
                    canales = data.get('canales', [])
                elif isinstance(data, list):
                    canales = data
                else:
                    canales = []
                
                if not canales:
                    no_canales_label = Label(
                        text="No hay canales disponibles.\nCrea uno usando el botón ≡", 
                        size_hint_y=None, 
                        height=100,
                        halign='center',
                        valign='middle'
                    )
                    no_canales_label.bind(size=no_canales_label.setter('text_size'))
                    self.lista_botones.add_widget(no_canales_label)
                else:
                    # Crear botones para cada canal
                    for canal in canales:
                        nombre_canal = str(canal.get('nombre', 'Canal sin nombre'))
                        
                        # Truncar nombres largos
                        if len(nombre_canal) > 50:
                            texto_boton = nombre_canal[:47] + "..."
                        else:
                            texto_boton = nombre_canal
                        
                        btn = Button(
                            text=f"   {texto_boton}",  # Agregar # para consistencia
                            size_hint_y=None, 
                            height=60,
                            background_color=(0.3, 0.3, 0.3, 1),
                            halign='left',
                            valign='middle'
                        )
                        btn.bind(size=btn.setter('text_size'))
                        # CAMBIO PRINCIPAL: usar abrir_chat_canal en lugar de abrir_chat
                        btn.bind(on_press=lambda instance, nombre=nombre_canal: self.abrir_chat_canal(nombre))
                        self.lista_botones.add_widget(btn)
                        
            else:
                self.mostrar_error(f"Error del servidor: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.mostrar_error("Timeout: El servidor tardó demasiado en responder.")
        except requests.exceptions.ConnectionError:
            self.mostrar_error("Error de conexión: Verifica tu conexión a internet.")
        except Exception as e:
            self.mostrar_error(f"Error inesperado: {str(e)}")

    def mostrar_error(self, mensaje):
        """Mostrar error en la lista"""
        self.lista_botones.clear_widgets()
        
        error_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=120, spacing=10)
        
        error_label = Label(
            text=f"❌ {mensaje}", 
            size_hint_y=None, 
            height=60,
            color=(1, 0.5, 0.5, 1),
            halign='center',
            valign='middle'
        )
        error_label.bind(size=error_label.setter('text_size'))
        
        retry_btn = Button(
            text="Reintentar", 
            size_hint_y=None, 
            height=50,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        retry_btn.bind(on_press=lambda x: self.cargar_canales())
        
        error_layout.add_widget(error_label)
        error_layout.add_widget(retry_btn)
        self.lista_botones.add_widget(error_layout)

    def abrir_chat_canal(self, nombre_canal):
        """NUEVO MÉTODO: Abrir el chat del canal usando la nueva arquitectura"""
        # Cerrar menú si está abierto antes de navegar
        self.cerrar_menu_actual()
        
        try:
            # Obtener la pantalla de chat desde el ScreenManager
            chat_screen = self.manager.get_screen('chat_canal')
            
            # Configurar el canal en la pantalla de chat
            chat_screen.set_canal(nombre_canal)
            
            # Navegar al chat
            self.manager.current = 'chat_canal'
            
        except Exception as e:
            print(f"Error abriendo chat del canal: {e}")
            self.mostrar_popup("Error", f"No se pudo abrir el chat del canal '{nombre_canal}'")

    def abrir_ventana_crear(self):
        """Abrir ventana para crear canal - navegación mejorada"""
        try:
            # Navegar a la pantalla de crear canal
            if self.manager.has_screen('crear_canal'):
                self.manager.current = 'crear_canal'
            else:
                self.mostrar_popup("Error", "Pantalla de crear canal no encontrada")
        except Exception as e:
            print(f"Error abriendo crear canal: {e}")
            self.mostrar_popup("Error", "No se pudo abrir la ventana de crear canal")

    def mostrar_popup(self, titulo, mensaje):
        """Mostrar popup informativo"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=mensaje))
        
        btn_ok = Button(text="OK", size_hint_y=None, height=40)
        content.add_widget(btn_ok)
        
        popup = Popup(title=titulo, content=content, size_hint=(0.8, 0.4))
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()

    def on_leave(self):
        """NUEVO: Al salir de la pantalla, cerrar el menú"""
        self.cerrar_menu_actual()
        super().on_leave()