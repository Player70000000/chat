import requests
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivy.clock import Clock
from kivy.metrics import dp

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import API_BASE_URL, DEFAULT_USERNAME


class ChannelListItem(OneLineListItem):
    def __init__(self, channel_name, on_select_callback, **kwargs):
        super().__init__(**kwargs)
        self.text = f"# {channel_name}"
        self.channel_name = channel_name
        self.on_select_callback = on_select_callback
        self.on_release = self.select_channel
        
    def select_channel(self):
        self.on_select_callback(self.channel_name)


class ChatChannelScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "chat_channel"
        self.channel_name = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # Top bar con back button
        self.top_bar = MDTopAppBar(
            title="Selecciona un canal",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["dots-vertical", lambda x: self.show_channel_options_menu(x)]]
        )
        
        # Área de mensajes
        self.messages_card = MDCard(
            elevation=1,
            padding="10dp",
            size_hint_y=0.85
        )
        
        self.messages_layout = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing="5dp",
            padding="10dp"
        )
        
        self.messages_scroll = MDScrollView()
        self.messages_scroll.add_widget(self.messages_layout)
        self.messages_card.add_widget(self.messages_scroll)
        
        # Área de entrada de mensajes
        input_layout = MDBoxLayout(
            size_hint_y=None,
            height="60dp",
            spacing="10dp",
            padding=["10dp", "5dp"]
        )
        
        self.message_input = MDTextField(
            hint_text="Escribe un mensaje...",
            size_hint_x=0.8,
            multiline=False,
            on_text_validate=self.send_message
        )
        
        send_button = MDIconButton(
            icon="send",
            theme_icon_color="Primary",
            on_release=self.send_message
        )
        
        input_layout.add_widget(self.message_input)
        input_layout.add_widget(send_button)
        
        layout.add_widget(self.top_bar)
        layout.add_widget(self.messages_card)
        layout.add_widget(input_layout)
        
        self.add_widget(layout)
        
    def set_channel(self, channel_name):
        self.channel_name = channel_name
        self.top_bar.title = f"# {channel_name}"
        self.load_messages()
        # Auto-actualizar cada 10 segundos para mejor rendimiento
        self.auto_update_event = Clock.schedule_interval(self.auto_load_messages, 10)
        
    def update_channel_name(self, old_name, new_name):
        """Actualizar solo el nombre del canal si coincide"""
        if self.channel_name == old_name:
            self.channel_name = new_name
            self.top_bar.title = f"# {new_name}"
    
    def stop_auto_update(self):
        """Detener actualización automática para mejorar rendimiento"""
        if hasattr(self, 'auto_update_event') and self.auto_update_event:
            Clock.unschedule(self.auto_update_event)
            self.auto_update_event = None
    
    def cleanup(self):
        """Limpiar recursos y referencias para liberar memoria"""
        self.stop_auto_update()
        if hasattr(self, 'messages_layout'):
            self.messages_layout.clear_widgets()
        self.channel_name = None
        self._last_message_count = 0
        
    def auto_load_messages(self, dt):
        self.load_messages()
        
    def load_messages(self):
        if not self.channel_name:
            return
            
        try:
            response = requests.get(f"{API_BASE_URL}/mensajes/{self.channel_name}", timeout=3)
            if response.status_code == 200:
                data = response.json()
                messages = data.get('mensajes', [])
                
                # Solo actualizar si hay cambios reales para mejorar rendimiento
                if not hasattr(self, '_last_message_count') or len(messages) != self._last_message_count:
                    self._last_message_count = len(messages)
                    self.messages_layout.clear_widgets()
                    
                    if not messages:
                        no_messages_label = MDLabel(
                            text="No hay mensajes en este canal",
                            theme_text_color="Secondary",
                            halign="center",
                            size_hint_y=None,
                            height="40dp"
                        )
                        self.messages_layout.add_widget(no_messages_label)
                    else:
                        for msg in messages:
                            message_text = f"{msg.get('usuario', 'Usuario')}: {msg.get('mensaje', '')}"
                            message_label = MDLabel(
                                text=message_text,
                                size_hint_y=None,
                                height="35dp",
                                theme_text_color="Primary",
                                text_size=(None, None),
                                halign="left"
                            )
                            self.messages_layout.add_widget(message_label)
                            
                    self.scroll_to_bottom()
        except Exception as e:
            print(f"Error loading messages: {e}")
            
    def scroll_to_bottom(self):
        if self.messages_layout.children:
            # Optimización: reducir delay del scroll
            Clock.schedule_once(lambda dt: setattr(self.messages_scroll, 'scroll_y', 0), 0.05)
            
    def send_message(self, instance=None):
        if not self.channel_name:
            self.show_dialog("Error", "No hay canal seleccionado")
            return
            
        text = self.message_input.text.strip()
        if not text:
            return
            
        data = {
            "usuario": DEFAULT_USERNAME,
            "mensaje": text,
            "canal": self.channel_name
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/enviar", json=data, timeout=5)
            if response.status_code in [200, 201]:
                self.message_input.text = ""
                self.load_messages()
            else:
                self.show_dialog("Error", "No se pudo enviar el mensaje")
        except Exception:
            self.show_dialog("Error", "Error de conexión al enviar mensaje")
            
    def go_back(self):
        # Buscar el layout principal navegando hacia arriba
        current = self.parent
        while current:
            if hasattr(current, 'show_channel_list'):
                current.show_channel_list()
                return
            elif hasattr(current, 'main_layout') and current.main_layout:
                current.main_layout.show_channel_list()
                return
            current = current.parent
        
    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
        
    def show_channel_options_menu(self, button):
        """Mostrar menú de opciones del canal actual"""
        if not self.channel_name:
            self.show_dialog("Error", "No hay canal seleccionado")
            return
            
        # Limpiar menú anterior si existe
        if hasattr(self, 'channel_menu') and self.channel_menu:
            self.channel_menu.dismiss()
            self.channel_menu = None
            
        menu_items = [
            {
                "text": "Ajustes del canal",
                "icon": "cog",
                "on_release": self.open_channel_settings,
            },
        ]
        
        self.channel_menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
        )
        self.channel_menu.open()
        
    def open_channel_settings(self, *args):
        """Abrir los ajustes del canal"""
        self.channel_menu.dismiss()
        
        # Buscar el ChatScreen padre para acceder a settings_screen
        current = self.parent
        while current:
            if hasattr(current, 'settings_screen') and hasattr(current, 'show_channel_settings'):
                current.settings_screen.set_channel_data(self.channel_name)
                current.show_channel_settings()
                return
            current = current.parent
        self.show_dialog("Error", "No se pudo acceder a los ajustes del canal")
            


class CreateChannelScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "create_channel"
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical", padding="20dp", spacing="20dp")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Crear Canal",
            left_action_items=[["arrow-left", lambda x: self.go_back()]]
        )
        
        # Content card
        content_card = MDCard(
            elevation=2,
            padding="20dp",
            size_hint_y=None,
            height="300dp"
        )
        
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp")
        
        # Título
        title_label = MDLabel(
            text="Nuevo Canal de Chat",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )
        
        # Channel name input
        self.name_input = MDTextField(
            hint_text="Nombre del canal",
            required=True,
            helper_text="Ej: general, soporte, anuncios",
            helper_text_mode="on_focus"
        )
        
        # Channel description input
        self.description_input = MDTextField(
            hint_text="Descripción (opcional)",
            multiline=True,
            max_text_length=200
        )
        
        # Create button
        self.create_button = MDRaisedButton(
            text="CREAR CANAL",
            size_hint_y=None,
            height="40dp",
            on_release=self.create_channel
        )
        
        content_layout.add_widget(title_label)
        content_layout.add_widget(self.name_input)
        content_layout.add_widget(self.description_input)
        content_layout.add_widget(self.create_button)
        
        content_card.add_widget(content_layout)
        
        layout.add_widget(top_bar)
        layout.add_widget(content_card)
        
        self.add_widget(layout)
        
    def create_channel(self, instance):
        name = self.name_input.text.strip()
        description = self.description_input.text.strip()
        
        if not name:
            self.show_dialog("Error", "El nombre del canal no puede estar vacío")
            return
            
        self.create_button.disabled = True
        self.create_button.text = "CREANDO..."
        
        try:
            data = {"nombre": name}
            if description:
                data["descripcion"] = description
                
            response = requests.post(f"{API_BASE_URL}/crear_canal", json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                self.name_input.text = ""
                self.description_input.text = ""
                self.show_success_dialog("¡Éxito!", f"Canal '{name}' creado exitosamente")
            elif response.status_code == 409:
                self.show_dialog("Error", "El canal ya existe")
            else:
                self.show_dialog("Error", f"Error del servidor (código {response.status_code})")
                
        except requests.exceptions.Timeout:
            self.show_dialog("Error", "El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "No se pudo conectar al servidor")
        except Exception as e:
            self.show_dialog("Error", "Error inesperado al crear el canal")
        finally:
            self.create_button.disabled = False
            self.create_button.text = "CREAR CANAL"
            
    def show_success_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: self.close_and_return(dialog)
                )
            ]
        )
        dialog.open()
        
    def close_and_return(self, dialog):
        dialog.dismiss()
        self.go_back_with_refresh()
        
    def go_back_with_refresh(self):
        # Buscar el layout principal navegando hacia arriba
        current = self.parent
        while current:
            if hasattr(current, 'show_channel_list'):
                current.show_channel_list()
                if hasattr(current, 'load_channels'):
                    current.load_channels()
                return
            elif hasattr(current, 'main_layout') and current.main_layout:
                current.main_layout.show_channel_list()
                current.main_layout.load_channels()
                return
            current = current.parent
        
    def go_back(self):
        # Buscar el layout principal navegando hacia arriba 
        current = self.parent
        while current:
            if hasattr(current, 'show_channel_list'):
                current.show_channel_list()
                return
            elif hasattr(current, 'main_layout') and current.main_layout:
                current.main_layout.show_channel_list()
                return
            current = current.parent
        
    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()



class ChannelEditScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "channel_edit"
        self.channel_name = None
        self.channel_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical", padding="20dp", spacing="20dp")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Editar Canal",
            left_action_items=[["arrow-left", lambda x: self.go_back()]]
        )
        
        # Content card
        content_card = MDCard(
            elevation=2,
            padding="20dp",
            size_hint_y=None,
            height="400dp"
        )
        
        content_layout = MDBoxLayout(orientation="vertical", spacing="20dp")
        
        # Campo para nombre del canal
        self.name_field = MDTextField(
            hint_text="Nombre del canal",
            required=True,
            helper_text="El nombre del canal es obligatorio",
            helper_text_mode="on_error",
            size_hint_y=None,
            height="60dp"
        )
        
        # Campo para descripción del canal
        self.description_field = MDTextField(
            hint_text="Descripción del canal",
            multiline=True,
            max_text_length=500,
            size_hint_y=None,
            height="120dp"
        )
        
        # Botón de guardar
        self.save_button = MDRaisedButton(
            text="GUARDAR CAMBIOS",
            md_bg_color=[0.2, 0.6, 1, 1],
            size_hint_y=None,
            height="50dp",
            on_release=self.save_changes
        )
        
        content_layout.add_widget(self.name_field)
        content_layout.add_widget(self.description_field)
        content_layout.add_widget(MDLabel(size_hint_y=None, height="20dp"))  # Spacer
        content_layout.add_widget(self.save_button)
        
        content_card.add_widget(content_layout)
        layout.add_widget(top_bar)
        layout.add_widget(content_card)
        
        self.add_widget(layout)
    
    def set_channel_data(self, channel_name):
        """Configurar datos del canal para edición"""
        self.channel_name = channel_name
        self._original_channel_name = channel_name  # Guardar nombre original para comparación
        self.name_field.text = channel_name
        
        # Cargar datos del canal desde el API
        self.load_channel_data()
    
    def load_channel_data(self):
        """Cargar datos actuales del canal"""
        try:
            response = requests.get(f"{API_BASE_URL}/canales", timeout=5)
            if response.status_code == 200:
                data = response.json()
                channels = data.get('canales', []) if isinstance(data, dict) else data
                
                # Buscar el canal específico
                for channel in channels:
                    if channel.get('nombre') == self.channel_name:
                        self.channel_data = channel
                        self.description_field.text = channel.get('descripcion', '')
                        break
        except Exception as e:
            print(f"Error cargando datos del canal: {e}")
    
    def save_changes(self, *args):
        """Guardar cambios del canal"""
        # Validar nombre no vacío
        if not self.name_field.text.strip():
            self.name_field.error = True
            return
        
        self.save_button.disabled = True
        self.save_button.text = "GUARDANDO..."
        
        try:
            # Preparar datos para actualizar
            update_data = {
                "nombre": self.name_field.text.strip(),
                "descripcion": self.description_field.text.strip()
            }
            
            # Hacer llamada al API para actualizar
            endpoint = f"{API_BASE_URL}/canal/{self.channel_name}"
            response = requests.put(endpoint, json=update_data, timeout=10)
            
            if response.status_code == 200:
                # Éxito - mostrar mensaje y regresar
                from kivymd.toast import toast
                toast("Canal editado exitosamente")
                
                # Actualizar el nombre local si cambió
                self.channel_name = self.name_field.text.strip()
                
                # Regresar a ajustes del canal después de un breve delay
                Clock.schedule_once(lambda dt: self.return_to_settings(), 1)
                
            else:
                # Error del servidor
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', 'Error desconocido')
                except:
                    error_message = f"Error del servidor: {response.status_code}"
                
                self.show_dialog("Error", f"No se pudo actualizar el canal:\n{error_message}")
                
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "No se pudo conectar al servidor. Verifica tu conexión a internet.")
        except Exception as e:
            self.show_dialog("Error", f"Error inesperado: {str(e)}")
        finally:
            self.save_button.disabled = False
            self.save_button.text = "GUARDAR CAMBIOS"
    
    def return_to_settings(self):
        """Regresar a la pantalla de ajustes del canal"""
        chat_screen_ref = getattr(self, '_chat_screen_ref', None)
        if chat_screen_ref:
            old_channel_name = getattr(self, '_original_channel_name', self.channel_name)
            new_channel_name = self.channel_name
            
            # Actualizar el nombre en la pantalla de ajustes
            if hasattr(chat_screen_ref, 'settings_screen'):
                chat_screen_ref.settings_screen.channel_name = new_channel_name
                chat_screen_ref.settings_screen.title_label.text = f"# {new_channel_name}"
                # Recargar información del canal
                chat_screen_ref.settings_screen.load_channel_info()
            
            # Actualizar el chat individual si existe
            if hasattr(chat_screen_ref, 'chat_screen') and hasattr(chat_screen_ref.chat_screen, 'update_channel_name'):
                chat_screen_ref.chat_screen.update_channel_name(old_channel_name, new_channel_name)
            
            # Recargar la lista de canales para mostrar cambios inmediatamente
            if hasattr(chat_screen_ref, 'load_channels'):
                chat_screen_ref.load_channels()
            
            # Cambiar a la pantalla de ajustes
            chat_screen_ref.screen_manager.current = "channel_settings"
    
    def go_back(self):
        """Volver a la pantalla de ajustes"""
        self.return_to_settings()
    
    def show_dialog(self, title, text):
        """Mostrar diálogo informativo"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class ChannelSettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "channel_settings"
        self.channel_name = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical", padding="20dp", spacing="20dp")
        
        # Top bar
        self.top_bar = MDTopAppBar(
            title="Ajustes del canal",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["dots-vertical", lambda x: self.show_settings_menu()]]
        )
        
        # Content card
        content_card = MDCard(
            elevation=2,
            padding="20dp",
            size_hint_y=None,
            height="400dp"
        )
        
        content_layout = MDBoxLayout(orientation="vertical", spacing="20dp")
        
        # Título con nombre del canal
        self.title_label = MDLabel(
            text="Canal",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None,
            height="40dp",
            halign="center"
        )
        
        # Información del canal
        info_layout = MDBoxLayout(orientation="vertical", spacing="15dp")
        
        # Descripción y fecha juntas
        details_card = MDCard(
            elevation=1,
            padding="20dp",
            size_hint_y=None,
            height="120dp"
        )
        details_layout = MDBoxLayout(orientation="vertical", spacing="10dp")
        
        # Descripción
        desc_layout = MDBoxLayout(orientation="horizontal", spacing="10dp", size_hint_y=None, height="30dp")
        desc_icon = MDLabel(
            text="📝",
            size_hint_x=None,
            width="40dp",
            font_size="18sp"
        )
        self.desc_label = MDLabel(
            text="Descripción: Cargando...",
            theme_text_color="Secondary",
            font_style="Body1"
        )
        desc_layout.add_widget(desc_icon)
        desc_layout.add_widget(self.desc_label)
        
        # Fecha de creación
        date_layout = MDBoxLayout(orientation="horizontal", spacing="10dp", size_hint_y=None, height="30dp")
        date_icon = MDLabel(
            text="📅",
            size_hint_x=None,
            width="40dp",
            font_size="18sp"
        )
        self.date_label = MDLabel(
            text="Creado: Cargando...",
            theme_text_color="Secondary",
            font_style="Body1"
        )
        date_layout.add_widget(date_icon)
        date_layout.add_widget(self.date_label)
        
        details_layout.add_widget(desc_layout)
        details_layout.add_widget(date_layout)
        details_card.add_widget(details_layout)
        
        info_layout.add_widget(details_card)
        
        # Botón de eliminar canal
        self.delete_button = MDRaisedButton(
            text="ELIMINAR CANAL",
            size_hint_y=None,
            height="45dp",
            md_bg_color=[0.8, 0.2, 0.2, 1],  # Color rojo
            on_release=self.confirm_delete_channel
        )
        
        content_layout.add_widget(self.title_label)
        content_layout.add_widget(info_layout)
        content_layout.add_widget(self.delete_button)
        
        content_card.add_widget(content_layout)
        
        layout.add_widget(self.top_bar)
        layout.add_widget(content_card)
        
        self.add_widget(layout)
        
    def set_channel_data(self, channel_name):
        """Configurar los datos del canal"""
        self.channel_name = channel_name
        self.title_label.text = f"# {channel_name}"
        
        # Cargar información real del canal desde el API
        self.load_channel_info()
        
    def load_channel_info(self):
        """Cargar información detallada del canal desde el API"""
        try:
            # Hacer llamada al API para obtener información del canal
            response = requests.get(f"{API_BASE_URL}/canal_info/{self.channel_name}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                descripcion = data.get('descripcion', 'Sin descripción')
                fecha_creacion = data.get('fecha_creacion', 'Fecha no disponible')
                
                self.desc_label.text = f"Descripción: {descripcion}"
                self.date_label.text = f"Creado: {fecha_creacion}"
            else:
                # Si no hay endpoint específico, intentar obtener de la lista de canales
                self.load_channel_from_list()
        except Exception as e:
            print(f"Error cargando info del canal: {e}")
            self.load_channel_from_list()
            
    def load_channel_from_list(self):
        """Cargar información del canal desde la lista de canales"""
        try:
            response = requests.get(f"{API_BASE_URL}/canales", timeout=5)
            if response.status_code == 200:
                data = response.json()
                channels = data.get('canales', []) if isinstance(data, dict) else data
                
                print(f"DEBUG: Datos recibidos: {data}")  # Debug
                
                # Buscar el canal específico
                channel_info = None
                for channel in channels:
                    if channel.get('nombre') == self.channel_name:
                        channel_info = channel
                        break
                
                if channel_info:
                    print(f"DEBUG: Info del canal encontrada: {channel_info}")  # Debug
                    
                    descripcion = channel_info.get('descripcion', 'Sin descripción')
                    
                    # Intentar varios campos posibles para la fecha
                    fecha_creacion = (
                        channel_info.get('fecha_creacion') or 
                        channel_info.get('creado_en') or 
                        channel_info.get('created_at') or
                        channel_info.get('fecha') or
                        channel_info.get('_id', {}).get('$date') if isinstance(channel_info.get('_id'), dict) else None
                    )
                    
                    # Si tenemos fecha, formatearla
                    if fecha_creacion and fecha_creacion != 'Fecha no disponible':
                        try:
                            # Si es timestamp de MongoDB ($date)
                            if isinstance(fecha_creacion, (int, float)):
                                from datetime import datetime
                                fecha_formateada = datetime.fromtimestamp(fecha_creacion/1000 if fecha_creacion > 1000000000000 else fecha_creacion).strftime('%d/%m/%Y')
                            # Si ya es string
                            elif isinstance(fecha_creacion, str):
                                if 'T' in fecha_creacion:  # ISO format
                                    from datetime import datetime
                                    fecha_dt = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                                    fecha_formateada = fecha_dt.strftime('%d/%m/%Y')
                                else:
                                    fecha_formateada = fecha_creacion
                            else:
                                fecha_formateada = str(fecha_creacion)
                        except Exception as e:
                            print(f"DEBUG: Error formateando fecha {fecha_creacion}: {e}")
                            from datetime import datetime
                            fecha_formateada = datetime.now().strftime('%d/%m/%Y')
                    else:
                        # Sin fecha disponible, usar actual
                        from datetime import datetime
                        fecha_formateada = datetime.now().strftime('%d/%m/%Y')
                    
                    self.desc_label.text = f"Descripción: {descripcion}"
                    self.date_label.text = f"Creado: {fecha_formateada}"
                    
                    print(f"DEBUG: Descripción final: {descripcion}")  # Debug
                    print(f"DEBUG: Fecha final: {fecha_formateada}")  # Debug
                else:
                    print(f"DEBUG: Canal '{self.channel_name}' no encontrado en la lista")  # Debug
                    # Datos por defecto si no se encuentra
                    self.desc_label.text = "Descripción: Sin descripción"
                    from datetime import datetime
                    self.date_label.text = f"Creado: {datetime.now().strftime('%d/%m/%Y')}"
            else:
                print(f"DEBUG: Error en respuesta: {response.status_code}")  # Debug
                # Datos por defecto en caso de error
                self.desc_label.text = "Descripción: Sin descripción"
                from datetime import datetime
                self.date_label.text = f"Creado: {datetime.now().strftime('%d/%m/%Y')}"
        except Exception as e:
            print(f"ERROR cargando canales: {e}")
            # Datos por defecto
            self.desc_label.text = "Descripción: Sin descripción"
            from datetime import datetime
            self.date_label.text = f"Creado: {datetime.now().strftime('%d/%m/%Y')}"
        
    def confirm_delete_channel(self, instance):
        """Confirmar eliminación del canal"""
        dialog = MDDialog(
            title="⚠️ Eliminar Canal",
            text=f"¿Estás seguro de que deseas eliminar el canal '# {self.channel_name}'?\n\n• Se perderán todos los mensajes\n• Esta acción no se puede deshacer\n• Los miembros perderán acceso al canal",
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="ELIMINAR",
                    md_bg_color=[0.8, 0.2, 0.2, 1],
                    on_release=lambda x: self.delete_channel(dialog)
                )
            ]
        )
        dialog.open()
        
    def delete_channel(self, dialog):
        """Eliminar el canal"""
        dialog.dismiss()
        
        self.delete_button.disabled = True
        self.delete_button.text = "ELIMINANDO..."
        
        try:
            print(f"DEBUG: Intentando eliminar canal: {self.channel_name}")
            
            # Endpoint correcto para eliminación
            endpoint = f"{API_BASE_URL}/canal/{self.channel_name}"
            
            print(f"DEBUG: Usando endpoint: {endpoint}")
            response = requests.delete(endpoint, timeout=10)
            print(f"DEBUG: Respuesta: {response.status_code}")
            print(f"DEBUG: Contenido: {response.text}")
            
            if response.status_code == 200:
                print("DEBUG: Canal eliminado exitosamente")
                
                # Mostrar mensaje simple
                from kivymd.toast import toast
                toast(f"Canal eliminado exitosamente")
                
                # Regresar inmediatamente a la lista de canales y recargar
                self.return_to_channel_list()
            elif response.status_code == 404:
                self.show_dialog("Error", f"El canal '# {self.channel_name}' no existe en el servidor.")
            elif response.status_code == 403:
                self.show_dialog("Error", "No tienes permisos para eliminar este canal.")
            else:
                try:
                    error_detail = response.json().get('error', 'Error desconocido')
                except:
                    error_detail = response.text if response.text else 'Sin detalles'
                self.show_dialog("Error", f"Error del servidor (código {response.status_code})\n\nDetalle: {error_detail}")
                
        except requests.exceptions.Timeout:
            self.show_dialog("Error", "El servidor tardó demasiado en responder. Intenta de nuevo.")
        except requests.exceptions.ConnectionError:
            self.show_dialog("Error", "No se pudo conectar al servidor. Verifica tu conexión a internet.")
        except Exception as e:
            self.show_dialog("Error", f"Error inesperado al eliminar el canal: {str(e)}")
        finally:
            self.delete_button.disabled = False
            self.delete_button.text = "ELIMINAR CANAL"
            
    def return_to_channel_list(self):
        """Regresar a la lista de canales después de eliminar"""
        # Usar la referencia guardada al ChatScreen
        chat_screen_ref = getattr(self, '_chat_screen_ref', None)
        if chat_screen_ref:
            # Cambiar a la pantalla de canales
            if hasattr(chat_screen_ref, 'show_main_screen'):
                chat_screen_ref.show_main_screen()
            
            # Forzar recarga de la lista de canales
            if hasattr(chat_screen_ref, 'load_channels'):
                # Programar la recarga después de un pequeño delay
                Clock.schedule_once(lambda dt: chat_screen_ref.load_channels(), 0.5)
                
        print("DEBUG: Navegación completada")
        
    def go_back(self):
        """Volver al chat del canal"""
        current = self.parent
        while current:
            if hasattr(current, 'show_chat_channel'):
                current.show_chat_channel()
                return
            elif hasattr(current, 'screen_manager'):
                current.screen_manager.current = "chat_channel"
                return
            current = current.parent
    
    def show_settings_menu(self):
        """Mostrar menú de opciones de ajustes del canal"""
        # Limpiar menú anterior para optimizar memoria
        if hasattr(self, 'settings_menu') and self.settings_menu:
            self.settings_menu.dismiss()
            self.settings_menu = None
            
        menu_items = [
            {
                "text": "Editar canal",
                "on_release": self.open_edit_channel,
            }
        ]
        
        self.settings_menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
            caller=self.top_bar,
            position="bottom"
        )
        
        self.settings_menu.open()
    
    def open_edit_channel(self, *args):
        """Abrir pantalla de edición del canal"""
        self.settings_menu.dismiss()
        
        # Buscar el ChatScreen para navegar a edición
        chat_screen_ref = getattr(self, '_chat_screen_ref', None)
        if chat_screen_ref:
            chat_screen_ref.edit_channel(self.channel_name)
        
    def show_dialog(self, title, text):
        """Mostrar diálogo informativo"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class ChatScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.main_layout = None  # Referencia al layout principal
        self.setup_ui()
        # Optimización: reducir delay inicial 
        Clock.schedule_once(lambda dt: self.load_channels(), 0.2)
        
    def setup_ui(self):
        # Screen manager para diferentes vistas
        self.screen_manager = MDScreenManager()
        
        # Pantalla de lista de canales
        self.channel_screen = MDScreen(name="channels")
        self.setup_channel_list()
        
        # Pantalla de chat
        self.chat_screen = ChatChannelScreen()
        
        # Pantalla de crear canal
        self.create_screen = CreateChannelScreen()
        
        
        # Pantalla de ajustes del canal
        self.settings_screen = ChannelSettingsScreen()
        self.settings_screen._chat_screen_ref = self
        
        # Pantalla de edición de canal (nueva)
        self.channel_edit_screen = ChannelEditScreen()
        self.channel_edit_screen._chat_screen_ref = self
        
        self.screen_manager.add_widget(self.channel_screen)
        self.screen_manager.add_widget(self.chat_screen)
        self.screen_manager.add_widget(self.create_screen)
        self.screen_manager.add_widget(self.settings_screen)
        self.screen_manager.add_widget(self.channel_edit_screen)
        
        self.add_widget(self.screen_manager)
        
    def setup_channel_list(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # Top bar
        self.top_bar = MDTopAppBar(
            title="Canales de Chat",
            right_action_items=[["dots-vertical", lambda x: self.show_options_menu(x)]]
        )
        
        # Canales list
        self.channels_card = MDCard(
            elevation=1,
            padding="10dp"
        )
        
        self.channels_scroll = MDScrollView()
        self.channels_list = MDList()
        self.channels_scroll.add_widget(self.channels_list)
        self.channels_card.add_widget(self.channels_scroll)
        
        layout.add_widget(self.top_bar)
        layout.add_widget(self.channels_card)
        
        self.channel_screen.add_widget(layout)
        
    def load_channels(self):
        self.channels_list.clear_widgets()
        
        # Indicador de carga
        loading_item = OneLineListItem(text="🔄 Cargando canales...")
        self.channels_list.add_widget(loading_item)
        
        try:
            response = requests.get(f"{API_BASE_URL}/canales", timeout=8)
            self.channels_list.clear_widgets()
            
            if response.status_code == 200:
                data = response.json()
                channels = data.get('canales', []) if isinstance(data, dict) else data
                
                if not channels:
                    no_channels_item = OneLineListItem(
                        text="📝 No hay canales disponibles. Crea uno usando el botón +"
                    )
                    self.channels_list.add_widget(no_channels_item)
                else:
                    for channel in channels:
                        channel_name = str(channel.get('nombre', 'Canal sin nombre'))
                        channel_item = ChannelListItem(
                            channel_name=channel_name,
                            on_select_callback=self.select_channel
                        )
                        self.channels_list.add_widget(channel_item)
            else:
                error_item = OneLineListItem(text=f"❌ Error del servidor: {response.status_code}")
                self.channels_list.add_widget(error_item)
                
        except requests.exceptions.Timeout:
            self.show_error("⏱️ Timeout: El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_error("🌐 Error de conexión: Verifica tu conexión a internet")
        except Exception as e:
            self.show_error(f"⚠️ Error inesperado: {str(e)}")
            
    def show_error(self, message):
        self.channels_list.clear_widgets()
        error_item = OneLineListItem(text=message)
        self.channels_list.add_widget(error_item)
        
        retry_item = OneLineListItem(
            text="🔄 Reintentar carga",
            on_release=lambda x: self.load_channels()
        )
        self.channels_list.add_widget(retry_item)
        
    def select_channel(self, channel_name):
        self.chat_screen.set_channel(channel_name)
        self.screen_manager.current = "chat_channel"
        
    def show_create_channel(self):
        self.screen_manager.current = "create_channel"
        
    def show_edit_channel(self):
        self.screen_manager.current = "edit_channel"
        
    def show_channel_settings(self):
        self.screen_manager.current = "channel_settings"
        
    def show_channel_list(self):
        self.screen_manager.current = "channels"
        
        
    def show_main_screen(self):
        """Mostrar la pantalla principal de canales"""
        self.show_channel_list()
        
    def show_dialog(self, title, text):
        """Mostrar diálogo informativo"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
        
    def show_options_menu(self, button):
        """Mostrar menú desplegable con opciones"""
        # Limpiar menú anterior para optimizar memoria
        if hasattr(self, 'menu') and self.menu:
            self.menu.dismiss()
            self.menu = None
            
        # Crear elementos del menú
        menu_items = [
            {
                "text": "Crear Canal",
                "icon": "plus-circle",
                "on_release": lambda x="crear_canal": self.handle_menu_option(x),
            },
            {
                "text": "Cerrar Sesión", 
                "icon": "logout",
                "on_release": lambda x="cerrar_sesion": self.handle_menu_option(x),
            },
            {
                "text": "Futuras Opciones",
                "icon": "cog",
                "on_release": lambda x="futuras_opciones": self.handle_menu_option(x),
            },
        ]
        
        # Crear y mostrar el menú
        self.menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()
        
    def handle_menu_option(self, option):
        """Manejar las opciones del menú desplegable"""
        self.menu.dismiss()
        
        if option == "crear_canal":
            self.show_create_channel()
        elif option == "cerrar_sesion":
            self.show_dialog(
                "Cerrar Sesión",
                "Esta función aún no está operativa.\n\nLa gestión de sesiones se maneja automáticamente por el momento."
            )
        elif option == "futuras_opciones":
            self.show_dialog(
                "Futuras Opciones",
                "Esta sección estará disponible en próximas actualizaciones.\n\nFunciones planificadas:\n• Configuración de notificaciones\n• Gestión de usuarios\n• Temas personalizados\n• Configuración avanzada"
            )
    
    def edit_channel(self, channel_name):
        """Mostrar pantalla de edición del canal"""
        # Configurar la pantalla de edición con los datos del canal
        if hasattr(self, 'channel_edit_screen'):
            self.channel_edit_screen.set_channel_data(channel_name)
            self.screen_manager.current = "channel_edit"
        else:
            print(f"ERROR: channel_edit_screen no encontrada")
    
    def cleanup_menus(self):
        """Limpiar todos los menús dropdown para liberar memoria"""
        if hasattr(self, 'menu') and self.menu:
            self.menu.dismiss()
            self.menu = None
        
        # Limpiar menús de pantallas hijas
        if hasattr(self, 'chat_screen') and hasattr(self.chat_screen, 'channel_menu'):
            if self.chat_screen.channel_menu:
                self.chat_screen.channel_menu.dismiss()
                self.chat_screen.channel_menu = None
        
        if hasattr(self, 'settings_screen') and hasattr(self.settings_screen, 'settings_menu'):
            if self.settings_screen.settings_menu:
                self.settings_screen.settings_menu.dismiss()
                self.settings_screen.settings_menu = None