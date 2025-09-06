from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.metrics import dp
import requests
from config import API_URL

class MenuDesplegableConfig(RelativeLayout):
    """Menú desplegable personalizado para configuración - estilo consistente con selector"""
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
                background_color=(0.2, 0.2, 0.2, 0.9),
                color=(1, 1, 1, 1),
                font_size=14
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

class ConfigCanalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canal_actual = ""
        self._popup_progreso = None
        self.menu_actual = None  # Cambio: usar menu desplegable en lugar de popup
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10, padding=[10, 5])
        
        btn_volver = Button(text='←', size_hint=(None, 1), width=50, font_size=20, background_color=(0.2, 0.6, 1, 1))
        btn_volver.bind(on_press=self.volver_chat)
        
        titulo = Label(text='Configuración del Canal', font_size=18, color=(0, 0, 0, 1))
        
        # Botón de menú desplegable - mismo estilo que selector
        self.btn_menu = Button(text='⋮', size_hint=(None, 1), width=50, font_size=24, 
                              background_color=(0.3, 0.3, 0.3, 1), color=(1, 1, 1, 1))
        self.btn_menu.bind(on_press=self.mostrar_menu)
        
        header.add_widget(btn_volver)
        header.add_widget(titulo)
        header.add_widget(self.btn_menu)
        
        # Content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=20, padding=20, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        info_titulo = Label(text='Información del Canal:', font_size=16, bold=True, color=(0, 0, 0, 1), 
                           size_hint_y=None, height=30, halign='left')
        info_titulo.bind(size=info_titulo.setter('text_size'))
        
        self.label_info = Label(text='Cargando información...', font_size=14, color=(0.3, 0.3, 0.3, 1),
                               size_hint_y=None, height=80, halign='left', valign='top')
        self.label_info.bind(size=self._on_label_size)
        
        self.label_error = Label(text='', font_size=12, color=(0.8, 0.4, 0.4, 1), size_hint_y=None, height=25, halign='center')
        self.label_error.bind(size=self.label_error.setter('text_size'))
        
        btn_eliminar = Button(text='🗑️ Eliminar Canal', font_size=16, size_hint_y=None, height=50,
                             background_color=(0.9, 0.3, 0.3, 1), color=(1, 1, 1, 1))
        btn_eliminar.bind(on_press=self.confirmar_eliminacion)
        
        # Layout assembly
        content.add_widget(info_titulo)
        content.add_widget(self.label_info)
        content.add_widget(self.label_error)
        content.add_widget(Label(size_hint_y=None, height=40))  # Spacer
        content.add_widget(btn_eliminar)
        
        scroll.add_widget(content)
        main_layout.add_widget(header)
        main_layout.add_widget(scroll)
        self.add_widget(main_layout)
    
    def on_touch_down(self, touch):
        """Detectar toques para cerrar menú al tocar fuera - mismo comportamiento que selector"""
        # Si hay un menú abierto y el toque no está dentro del menú
        if self.menu_actual and not self.menu_actual.collide_point(*touch.pos):
            self.cerrar_menu_actual()
            return True  # Consumir el evento para que no se propague
        
        # Continuar con el comportamiento normal
        return super().on_touch_down(touch)
    
    def mostrar_menu(self, instance):
        """Mostrar menú desplegable - estilo consistente con selector"""
        # Cerrar menú anterior si existe
        if self.menu_actual:
            self.cerrar_menu_actual()
            return
        
        # Opciones del menú
        opciones = ["✏️ Editar Canal", "Futuras opciones"]
        
        # Calcular posición del menú
        menu_width = 150
        menu_height = len(opciones) * 40
        
        # Posición X: alineado a la derecha del botón, pero dentro de pantalla
        pos_x = instance.x + instance.width - menu_width
        # Posición Y: debajo del botón
        pos_y = instance.y - menu_height
        
        # Crear menú desplegable
        self.menu_actual = MenuDesplegableConfig(
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
        """Manejar la selección del menú - reemplaza mostrar_menu popup"""
        if opcion == "✏️ Editar Canal":
            self._ir_editar()
        elif opcion == "Futuras opciones":
            self._mostrar_popup_info("Info", "Funcionalidad en desarrollo")
        
        # Cerrar menú
        self.cerrar_menu_actual()
    
    def _ir_editar(self):
        """Navegar a pantalla de edición - sin cerrar popup ya que no hay popup"""
        # Pasar datos del canal actual a la pantalla de edición
        editar_screen = self.manager.get_screen('editar_canal')
        editar_screen.set_canal_datos(self.canal_actual, self._obtener_datos_actuales())
        self.manager.current = 'editar_canal'
    
    def _obtener_datos_actuales(self):
        """Obtener datos actuales del canal desde el label_info"""
        # Extraer descripción del texto actual
        texto_info = self.label_info.text
        if "Descripción:" in texto_info:
            lineas = texto_info.split('\n')
            descripcion_linea = lineas[0].replace('Descripción:', '').strip()
            return {"descripcion": descripcion_linea}
        return {"descripcion": ""}
    
    def _mostrar_popup_info(self, titulo, mensaje):
        """Mostrar popup informativo simple"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=mensaje))
        
        btn_ok = Button(text="OK", size_hint_y=None, height=40)
        content.add_widget(btn_ok)
        
        popup = Popup(title=titulo, content=content, size_hint=(0.8, 0.4))
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()
    
    def set_canal(self, nombre_canal):
        """Establecer canal y cargar información"""
        self.canal_actual = nombre_canal.strip() if nombre_canal else ""
        self.cargar_info_canal()
    
    def _on_label_size(self, instance, size):
        """Ajustar text_size del label info"""
        if size[0] > 0:
            instance.text_size = (size[0] - 20, None)
    
    def cargar_info_canal(self):
        """Cargar información del canal"""
        if not self.canal_actual:
            self._mostrar_error("No se ha especificado un canal")
            return
        
        self.label_info.text = "Cargando información del canal..."
        self.label_error.text = ""
        Clock.schedule_once(lambda dt: self._request_canal_info(), 0.1)
    
    def _request_canal_info(self):
        """Petición GET para info del canal"""
        try:
            nombre_api = self.canal_actual.replace('#', '').strip()
            response = requests.get(f"{API_URL}/canal/{nombre_api}", timeout=10)
            
            if response.status_code == 200:
                self._actualizar_info(response.json())
            elif response.status_code == 404:
                error_msg = response.json().get('mensaje', f"Canal '{self.canal_actual}' no encontrado")
                self._mostrar_error(error_msg)
            else:
                self._mostrar_error(f"Error del servidor: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self._mostrar_error("Tiempo de espera agotado. Verifica tu conexión.")
        except requests.exceptions.ConnectionError:
            self._mostrar_error("No se pudo conectar al servidor.")
        except Exception as e:
            self._mostrar_error(f"Error inesperado: {str(e)}")
    
    def _actualizar_info(self, data):
        """Actualizar UI con info del canal"""
        descripcion = data.get('descripcion', 'Sin descripción').strip() or 'Sin descripción'
        fecha = data.get('fecha_creacion', 'Fecha no disponible')
        fecha_texto = f"Se creó el {fecha}" if fecha != 'Fecha no disponible' else "Fecha de creación no disponible"
        
        self.label_info.text = f"Descripción: {descripcion}\n\n{fecha_texto}"
        self.label_error.text = ""
        Clock.schedule_once(lambda dt: self._ajustar_texto_size(), 0.1)
    
    def _ajustar_texto_size(self):
        """Ajustar tamaño de texto"""
        if self.width > 0 and hasattr(self.label_info, 'text_size'):
            self.label_info.text_size = (self.width - 40, None)
    
    def _mostrar_error(self, mensaje):
        """Mostrar error en UI"""
        self.label_error.text = f"❌ Error: {mensaje}"
        if "Cargando" in self.label_info.text:
            self.label_info.text = "No se pudo cargar la información del canal"
    
    def confirmar_eliminacion(self, instance):
        """Diálogo de confirmación"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        mensaje = Label(text='¿Estás seguro de que deseas eliminar este canal?\n\nEsta acción no se puede deshacer.',
                       halign='center', valign='middle')
        mensaje.bind(size=mensaje.setter('text_size'))
        
        botones = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        btn_cancelar = Button(text='Cancelar', background_color=(0.7, 0.7, 0.7, 1))
        btn_eliminar = Button(text='Eliminar', background_color=(0.9, 0.3, 0.3, 1))
        
        botones.add_widget(btn_cancelar)
        botones.add_widget(btn_eliminar)
        content.add_widget(mensaje)
        content.add_widget(botones)
        
        popup = Popup(title='Confirmar Eliminación', content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        
        btn_cancelar.bind(on_press=popup.dismiss)
        btn_eliminar.bind(on_press=lambda x: self._eliminar_canal(popup))
        popup.open()
    
    def _eliminar_canal(self, popup):
        """Proceso de eliminación"""
        popup.dismiss()
        self._mostrar_progreso()
        Clock.schedule_once(lambda dt: self._request_delete_canal(), 0.1)

    def _mostrar_progreso(self):
        """Popup de progreso"""
        content = Label(text='Eliminando canal...\n\nEsto puede tardar unos segundos.', halign='center', valign='middle')
        content.bind(size=content.setter('text_size'))
        
        self._popup_progreso = Popup(title='Eliminando Canal', content=content, size_hint=(0.6, 0.3), auto_dismiss=False)
        self._popup_progreso.open()

    def _request_delete_canal(self):
        """Petición DELETE para eliminar canal"""
        try:
            nombre_api = self.canal_actual.replace('#', '').strip()
            response = requests.delete(f"{API_URL}/canal/{nombre_api}", timeout=15)
            
            if response.status_code == 200:
                mensajes_eliminados = response.json().get('mensajes_eliminados', 0)
                self._mostrar_exito(mensajes_eliminados)
            elif response.status_code == 404:
                error_msg = response.json().get('mensaje', f"Canal '{self.canal_actual}' no encontrado")
                self._mostrar_error_popup(f"Error: {error_msg}")
            elif response.status_code == 500:
                error_msg = response.json().get('mensaje', 'Error interno del servidor')
                self._mostrar_error_popup(f"Error del servidor: {error_msg}")
            else:
                self._mostrar_error_popup(f"Error HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self._mostrar_error_popup("Tiempo de espera agotado.\nVerifica tu conexión a internet.")
        except requests.exceptions.ConnectionError:
            self._mostrar_error_popup("No se pudo conectar al servidor.\nVerifica que esté activo.")
        except Exception as e:
            self._mostrar_error_popup(f"Error inesperado: {str(e)}")

    def _mostrar_exito(self, mensajes_eliminados):
        """Popup de eliminación exitosa"""
        if self._popup_progreso:
            self._popup_progreso.dismiss()
        
        if mensajes_eliminados > 0:
            mensaje = f'Canal eliminado exitosamente\n\n✓ Canal: {self.canal_actual}\n✓ Mensajes eliminados: {mensajes_eliminados}'
        else:
            mensaje = f'Canal eliminado exitosamente\n\n✓ Canal: {self.canal_actual}\n✓ Sin mensajes que eliminar'
        
        content = Label(text=mensaje, halign='center', valign='middle')
        content.bind(size=content.setter('text_size'))
        
        popup = Popup(title='✅ Eliminación Exitosa', content=content, size_hint=(0.7, 0.4), auto_dismiss=False)
        popup.open()
        
        Clock.schedule_once(lambda dt: popup.dismiss(), 3.0)
        Clock.schedule_once(lambda dt: self.volver_selector(), 3.2)

    def _mostrar_error_popup(self, mensaje):
        """Popup de error"""
        if self._popup_progreso:
            self._popup_progreso.dismiss()
        
        content = Label(text=f'❌ {mensaje}\n\nIntenta nuevamente o contacta soporte si el problema persiste.',
                       halign='center', valign='middle')
        content.bind(size=content.setter('text_size'))
        
        popup = Popup(title='Error al Eliminar', content=content, size_hint=(0.7, 0.4), auto_dismiss=True)
        popup.open()
    
    def volver_chat(self, instance):
        """Volver al chat"""
        self.manager.current = 'chat_canal'
    
    def volver_selector(self):
        """Volver al selector"""
        self.manager.current = 'canal_selector'
    
    def on_enter(self):
        """Al entrar a la pantalla"""
        if self.canal_actual:
            self.cargar_info_canal()
    
    def on_leave(self):
        """Al salir de la pantalla, cerrar el menú - consistente con selector"""
        self.cerrar_menu_actual()
        super().on_leave()
    
    def on_size(self, *args):
        """Al cambiar tamaño"""
        Clock.schedule_once(lambda dt: self._ajustar_texto_size(), 0.1)