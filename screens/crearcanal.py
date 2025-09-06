import requests
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from config import API_URL


class CrearCanalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Layout principal
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)

        # Header con botón volver y título
        header_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        # Botón volver (flecha hacia atrás) en la izquierda
        boton_volver = Button(
            text='←', 
            size_hint=(None, None), 
            size=(40, 40),
            background_color=(0.4, 0.4, 0.4, 1)
        )
        boton_volver.bind(on_press=self.volver_a_canales)
        
        # Título centrado
        titulo = Label(
            text='[b]Crear un nuevo canal[/b]',
            markup=True,
            halign='center',
            valign='middle'
        )
        titulo.bind(size=titulo.setter('text_size'))
        
        # Espacio vacío a la derecha para balance
        espacio_derecho = Label(text='', size_hint=(None, None), size=(40, 40))
        
        header_layout.add_widget(boton_volver)
        header_layout.add_widget(titulo)
        header_layout.add_widget(espacio_derecho)
        
        layout.add_widget(header_layout)
        
        # Espaciador superior para centrar el contenido
        layout.add_widget(Label(text='', size_hint_y=0.2))

        # Contenedor para los campos de entrada
        inputs_container = BoxLayout(orientation='vertical', size_hint_y=None, height=200, spacing=15, padding=[20, 0])
        
        # Campo nombre del canal
        nombre_container = BoxLayout(orientation='vertical', size_hint_y=None, height=60, spacing=5)
        nombre_label = Label(
            text='Nombre del canal:',
            size_hint_y=None,
            height=20,
            color=(0.3, 0.3, 0.3, 1),
            halign='left',
            font_size=14
        )
        nombre_label.bind(size=nombre_label.setter('text_size'))
        
        self.input_nombre = TextInput(
            hint_text='Ingresa el nombre del canal',
            size_hint_y=None,
            height=45,
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 12],
            multiline=False
        )
        
        nombre_container.add_widget(nombre_label)
        nombre_container.add_widget(self.input_nombre)
        
        # Campo descripción del canal (opcional)
        descripcion_container = BoxLayout(orientation='vertical', size_hint_y=None, height=120, spacing=5)
        descripcion_label = Label(
            text='Descripción (opcional):',
            size_hint_y=None,
            height=20,
            color=(0.3, 0.3, 0.3, 1),
            halign='left',
            font_size=14
        )
        descripcion_label.bind(size=descripcion_label.setter('text_size'))
        
        self.input_descripcion = TextInput(
            hint_text='Describe brevemente el propósito del canal...',
            size_hint_y=None,
            height=90,
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 12],
            multiline=True
        )
        
        descripcion_container.add_widget(descripcion_label)
        descripcion_container.add_widget(self.input_descripcion)
        
        # Agregar ambos contenedores al contenedor principal
        inputs_container.add_widget(nombre_container)
        inputs_container.add_widget(descripcion_container)
        
        layout.add_widget(inputs_container)
        
        # Espaciador para empujar el botón hacia abajo
        layout.add_widget(Label(text='', size_hint_y=0.5))

        # Botón crear canal en la parte inferior
        boton_container = BoxLayout(orientation='vertical', size_hint_y=None, height=60, padding=[20, 0])
        self.boton_crear = Button(
            text='Crear canal',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.2, 1),
            font_size=16
        )
        self.boton_crear.bind(on_press=self.crear_canal)
        boton_container.add_widget(self.boton_crear)
        layout.add_widget(boton_container)

        self.add_widget(layout)

    def crear_canal(self, instance):
        nombre = self.input_nombre.text.strip()
        descripcion = self.input_descripcion.text.strip()
        
        # Validación del nombre (obligatorio)
        if not nombre:
            self.mostrar_popup("Error", "El nombre del canal no puede estar vacío.")
            return
        
        # Validación opcional de longitud de descripción
        if descripcion and len(descripcion) > 300:
            self.mostrar_popup("Error", "La descripción no puede exceder los 300 caracteres.")
            return

        self.boton_crear.disabled = True
        self.boton_crear.text = "Creando..."

        try:
            # Preparar datos para enviar
            datos_canal = {"nombre": nombre}
            if descripcion:  # Solo incluir descripción si no está vacía
                datos_canal["descripcion"] = descripcion

            response = requests.post(
                f"{API_URL}/crear_canal", 
                json=datos_canal,
                timeout=10
            )

            if response.status_code in [200, 201]:
                # Limpiar campos después del éxito
                self.input_nombre.text = ""
                self.input_descripcion.text = ""
                
                # Mensaje de éxito personalizado
                if descripcion:
                    mensaje = f"Canal '{nombre}' creado exitosamente con descripción."
                else:
                    mensaje = f"Canal '{nombre}' creado exitosamente."
                
                self.mostrar_popup_exito("¡Éxito!", mensaje)
                
            elif response.status_code == 409:
                self.mostrar_popup("Error", "El canal ya existe.")
                
            elif response.status_code == 400:
                try:
                    data = response.json()
                    error_msg = data.get("error", "Datos inválidos.")
                except:
                    error_msg = "Datos inválidos."
                self.mostrar_popup("Error", error_msg)
                
            else:
                self.mostrar_popup("Error", f"Error del servidor (código {response.status_code})")

        except requests.exceptions.Timeout:
            self.mostrar_popup("Error de Conexión", "El servidor tardó demasiado en responder.")
            
        except requests.exceptions.ConnectionError:
            self.mostrar_popup("Error de Conexión", "No se pudo conectar al servidor.")
            
        except Exception as e:
            self.mostrar_popup("Error", "Error inesperado al crear el canal.")
            
        finally:
            self.boton_crear.disabled = False
            self.boton_crear.text = "Crear canal"

    def mostrar_popup_exito(self, titulo, mensaje):
        """Popup de éxito que redirige automáticamente"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        mensaje_label = Label(
            text=mensaje,
            halign='center',
            valign='middle'
        )
        mensaje_label.bind(size=mensaje_label.setter('text_size'))
        content.add_widget(mensaje_label)
        
        btn_ok = Button(text="OK", size_hint_y=None, height=40, background_color=(0.2, 0.7, 0.2, 1))
        content.add_widget(btn_ok)
        
        popup = Popup(title=titulo, content=content, size_hint=(0.8, 0.4))
        
        def cerrar_y_volver(instance):
            popup.dismiss()
            self.volver_a_canales_con_recarga()
            
        btn_ok.bind(on_press=cerrar_y_volver)
        
        def auto_cerrar(dt):
            popup.dismiss()
            self.volver_a_canales_con_recarga()
            
        Clock.schedule_once(auto_cerrar, 2.5)
        popup.open()

    def mostrar_popup(self, titulo, mensaje):
        """Popup para errores y notificaciones"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        label = Label(
            text=mensaje, 
            text_size=(300, None), 
            halign="center", 
            valign="middle"
        )
        content.add_widget(label)
        
        btn_ok = Button(text="OK", size_hint_y=None, height=40)
        content.add_widget(btn_ok)
        
        popup = Popup(title=titulo, content=content, size_hint=(0.8, 0.5))
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()

    def volver_a_canales_con_recarga(self):
        """Volver a canales y forzar recarga"""
        # Navegación directa dentro del sm_canales interno
        self.manager.current = 'canal_selector'
        
        # Recargar canales después de crear uno nuevo
        canal_selector = self.manager.get_screen('canal_selector')
        Clock.schedule_once(lambda dt: canal_selector.cargar_canales(), 0.1)

    def volver_a_canales(self, instance):
        """Volver a canales sin recarga"""
        self.manager.current = 'canal_selector'
    
    def on_enter(self):
        """Al entrar a la pantalla, limpiar campos"""
        self.input_nombre.text = ""
        self.input_descripcion.text = ""