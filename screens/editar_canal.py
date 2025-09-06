from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import requests
import re
from config import API_URL

class EditarCanalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canal_actual = ""
        self.datos_originales = {}
        self._popup_progreso = None
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10, padding=[10, 5])
        
        btn_volver = Button(text='←', size_hint=(None, 1), width=50, font_size=20, background_color=(0.2, 0.6, 1, 1))
        btn_volver.bind(on_press=self.volver_config)
        
        titulo = Label(text='Editar Canal', font_size=18, color=(0, 0, 0, 1))
        
        header.add_widget(btn_volver)
        header.add_widget(titulo)
        header.add_widget(Label(size_hint=(None, 1), width=50))
        
        # Content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=20, padding=20, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Formulario de edición
        form_layout = BoxLayout(orientation='vertical', spacing=15, size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        
        # Campo Nombre
        label_nombre = Label(text='Nombre del Canal:', font_size=16, bold=True, color=(0, 0, 0, 1), 
                            size_hint_y=None, height=30, halign='left')
        label_nombre.bind(size=label_nombre.setter('text_size'))
        
        self.input_nombre = TextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=40,
            font_size=14,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1)
        )
        
        self.label_nombre_info = Label(
            text='Máximo 50 caracteres. Solo letras, números, espacios, guiones y #',
            font_size=12,
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=25,
            halign='left'
        )
        self.label_nombre_info.bind(size=self.label_nombre_info.setter('text_size'))
        
        # Campo Descripción
        label_descripcion = Label(text='Descripción (Opcional):', font_size=16, bold=True, color=(0, 0, 0, 1), 
                                 size_hint_y=None, height=30, halign='left')
        label_descripcion.bind(size=label_descripcion.setter('text_size'))
        
        self.input_descripcion = TextInput(
            text='',
            multiline=True,
            size_hint_y=None,
            height=80,
            font_size=14,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1)
        )
        
        self.label_desc_info = Label(
            text='Máximo 300 caracteres',
            font_size=12,
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=25,
            halign='left'
        )
        self.label_desc_info.bind(size=self.label_desc_info.setter('text_size'))
        
        # Mensajes de error
        self.label_error = Label(text='', font_size=12, color=(0.8, 0.4, 0.4, 1), size_hint_y=None, height=25, halign='center')
        self.label_error.bind(size=self.label_error.setter('text_size'))
        
        # Botones
        botones_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        
        btn_cancelar = Button(text='Cancelar', background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1), font_size=16)
        btn_cancelar.bind(on_press=self.volver_config)
        
        self.btn_guardar = Button(text='💾 Guardar Cambios', background_color=(0.2, 0.8, 0.2, 1), color=(1, 1, 1, 1), font_size=16)
        self.btn_guardar.bind(on_press=self.guardar_cambios)
        
        botones_layout.add_widget(btn_cancelar)
        botones_layout.add_widget(self.btn_guardar)
        
        # Ensamblar formulario
        form_layout.add_widget(label_nombre)
        form_layout.add_widget(self.input_nombre)
        form_layout.add_widget(self.label_nombre_info)
        form_layout.add_widget(Label(size_hint_y=None, height=20))
        form_layout.add_widget(label_descripcion)
        form_layout.add_widget(self.input_descripcion)
        form_layout.add_widget(self.label_desc_info)
        form_layout.add_widget(Label(size_hint_y=None, height=20))
        form_layout.add_widget(self.label_error)
        form_layout.add_widget(botones_layout)
        
        content.add_widget(form_layout)
        scroll.add_widget(content)
        main_layout.add_widget(header)
        main_layout.add_widget(scroll)
        self.add_widget(main_layout)
        
        # Bind eventos para validación
        self.input_nombre.bind(text=self.validar_nombre)
        self.input_descripcion.bind(text=self.validar_descripcion)
    
    def set_canal_datos(self, nombre_canal, datos_canal):
        """Establecer datos del canal a editar"""
        self.canal_actual = nombre_canal.strip() if nombre_canal else ""
        self.datos_originales = datos_canal if datos_canal else {}
        self.cargar_datos_formulario()
    
    def cargar_datos_formulario(self):
        """Cargar datos actuales en el formulario"""
        self.input_nombre.text = self.canal_actual
        self.input_descripcion.text = self.datos_originales.get('descripcion', '')
        self.label_error.text = ""
    
    def validar_nombre(self, instance, valor):
        """Validación en tiempo real del nombre"""
        if len(valor) > 50:
            self.label_nombre_info.text = f"❌ Excede límite: {len(valor)}/50 caracteres"
            self.label_nombre_info.color = (0.8, 0.4, 0.4, 1)
        else:
            self.label_nombre_info.text = f'✓ {len(valor)}/50 caracteres'
            self.label_nombre_info.color = (0.5, 0.5, 0.5, 1)
    
    def validar_descripcion(self, instance, valor):
        """Validación en tiempo real de la descripción"""
        if len(valor) > 300:
            self.label_desc_info.text = f"❌ Excede límite: {len(valor)}/300 caracteres"
            self.label_desc_info.color = (0.8, 0.4, 0.4, 1)
        else:
            self.label_desc_info.text = f'✓ {len(valor)}/300 caracteres'
            self.label_desc_info.color = (0.5, 0.5, 0.5, 1)
    
    def guardar_cambios(self, instance):
        """Validar y guardar cambios"""
        nuevo_nombre = self.input_nombre.text.strip()
        nueva_descripcion = self.input_descripcion.text.strip()
        
        # Validaciones locales
        if not nuevo_nombre:
            self.mostrar_error("El nombre del canal es obligatorio")
            return
        
        if len(nuevo_nombre) > 50:
            self.mostrar_error("El nombre no puede exceder 50 caracteres")
            return
        
        if len(nueva_descripcion) > 300:
            self.mostrar_error("La descripción no puede exceder 300 caracteres")
            return
        
        # Validar caracteres permitidos
        if not re.match(r'^[a-zA-Z0-9\s\-_#]+$', nuevo_nombre):
            self.mostrar_error("El nombre contiene caracteres no permitidos")
            return
        
        # Verificar si hay cambios
        nombre_cambio = nuevo_nombre != self.canal_actual
        descripcion_cambio = nueva_descripcion != self.datos_originales.get('descripcion', '')
        
        if not nombre_cambio and not descripcion_cambio:
            self.mostrar_error("No se detectaron cambios para guardar")
            return
        
        # Proceder con la actualización
        self.mostrar_progreso()
        Clock.schedule_once(lambda dt: self.request_update_canal(nuevo_nombre, nueva_descripcion), 0.1)
    
    def request_update_canal(self, nuevo_nombre, nueva_descripcion):
        """Petición PUT para actualizar canal"""
        try:
            nombre_api = self.canal_actual.replace('#', '').strip()
            datos = {
                "nombre": nuevo_nombre,
                "descripcion": nueva_descripcion
            }
            
            response = requests.put(f"{API_URL}/canal/{nombre_api}", json=datos, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                self.mostrar_exito(data)
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('mensaje', error_data.get('error', 'Error de validación'))
                self.mostrar_error_popup(f"Error de validación: {error_msg}")
            elif response.status_code == 404:
                error_data = response.json()
                error_msg = error_data.get('mensaje', f"Canal '{self.canal_actual}' no encontrado")
                self.mostrar_error_popup(f"Error: {error_msg}")
            elif response.status_code == 500:
                error_data = response.json()
                error_msg = error_data.get('mensaje', 'Error interno del servidor')
                self.mostrar_error_popup(f"Error del servidor: {error_msg}")
            else:
                self.mostrar_error_popup(f"Error HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.mostrar_error_popup("Tiempo de espera agotado. Verifica tu conexión a internet.")
        except requests.exceptions.ConnectionError:
            self.mostrar_error_popup("No se pudo conectar al servidor. Verifica que esté activo.")
        except Exception as e:
            self.mostrar_error_popup(f"Error inesperado: {str(e)}")
    
    def mostrar_progreso(self):
        """Popup de progreso durante la actualización"""
        content = Label(text='Guardando cambios...\n\nEsto puede tardar unos segundos.', halign='center', valign='middle')
        content.bind(size=content.setter('text_size'))
        
        self._popup_progreso = Popup(title='Actualizando Canal', content=content, size_hint=(0.6, 0.3), auto_dismiss=False)
        self._popup_progreso.open()
    
    def mostrar_exito(self, data):
        """Popup de actualización exitosa"""
        if self._popup_progreso:
            self._popup_progreso.dismiss()
        
        nombre_nuevo = data.get('canal_nuevo', '')
        nombre_cambio = data.get('nombre_cambio', False)
        mensajes_actualizados = data.get('mensajes_actualizados', 0)
        
        mensaje_base = 'Canal actualizado exitosamente\n\n'
        
        if nombre_cambio:
            mensaje_base += f'✓ Nombre: {self.canal_actual} → {nombre_nuevo}\n'
            if mensajes_actualizados > 0:
                mensaje_base += f'✓ Mensajes actualizados: {mensajes_actualizados}\n'
        else:
            mensaje_base += f'✓ Canal: {nombre_nuevo}\n'
        
        mensaje_base += '✓ Descripción actualizada'
        
        content = Label(text=mensaje_base, halign='center', valign='middle')
        content.bind(size=content.setter('text_size'))
        
        popup = Popup(title='✅ Actualización Exitosa', content=content, size_hint=(0.7, 0.4), auto_dismiss=False)
        popup.open()
        
        # Actualizar datos locales
        self.canal_actual = nombre_nuevo
        
        Clock.schedule_once(lambda dt: popup.dismiss(), 3.0)
        Clock.schedule_once(lambda dt: self.volver_config_actualizado(), 3.2)
    
    def mostrar_error_popup(self, mensaje):
        """Popup de error durante la actualización"""
        if self._popup_progreso:
            self._popup_progreso.dismiss()
        
        content = Label(text=f'❌ {mensaje}\n\nRevisa los datos e intenta nuevamente.',
                       halign='center', valign='middle')
        content.bind(size=content.setter('text_size'))
        
        popup = Popup(title='Error al Actualizar', content=content, size_hint=(0.7, 0.4), auto_dismiss=True)
        popup.open()
    
    def mostrar_error(self, mensaje):
        """Mostrar error en el label de la pantalla"""
        self.label_error.text = f"❌ {mensaje}"
    
    def volver_config_actualizado(self):
        """Volver a configuración con datos actualizados"""
        config_screen = self.manager.get_screen('config_canal')
        config_screen.set_canal(self.canal_actual)
        self.manager.current = 'config_canal'
    
    def volver_config(self, instance=None):
        """Volver a la pantalla de configuración sin cambios"""
        self.manager.current = 'config_canal'
    
    def on_enter(self):
        """Al entrar a la pantalla"""
        self.label_error.text = ""
        Clock.schedule_once(lambda dt: setattr(self.input_nombre, 'focus', True), 0.2)
    
    def on_leave(self):
        """Al salir de la pantalla"""
        self.input_nombre.text = ""
        self.input_descripcion.text = ""
        self.label_error.text = ""
        self.canal_actual = ""
        self.datos_originales = {}