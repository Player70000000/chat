"""
Utilidades generales para sistema de personal
Funciones helper y constantes del sistema
"""

from datetime import datetime, timedelta
import re


class PersonalUtils:
    """Clase con utilidades generales del sistema de personal"""

    # Constantes del sistema
    TALLAS_ROPA_OPTIONS = [
        {'text': 'XS', 'value': 'XS'},                 # ← Solo la talla, sin descripción
        {'text': 'S', 'value': 'S'},
        {'text': 'M', 'value': 'M'},
        {'text': 'L', 'value': 'L'},
        {'text': 'XL', 'value': 'XL'},
        {'text': 'XXL', 'value': 'XXL'},
        {'text': 'Ninguno', 'value': 'No ingresado'}   # ← Opción al final como original
    ]

    TALLAS_ZAPATOS_OPTIONS = [str(i) for i in range(30, 51)]

    ESTADOS_CUADRILLA = [
        'Activa',
        'Inactiva',
        'En formación',
        'Completada'
    ]

    COLORES_TEMA = {
        'primary': [0.2, 0.6, 1, 1],        # Azul
        'secondary': [0.3, 0.5, 0.8, 1],    # Azul más oscuro
        'success': [0.2, 0.7, 0.3, 1],      # Verde
        'warning': [1, 0.6, 0, 1],          # Naranja
        'error': [0.9, 0.1, 0.1, 1],        # Rojo
        'info': [0.1, 0.6, 0.9, 1],         # Azul claro
        'text_primary': [0, 0, 0, 0.87],    # Negro primario
        'text_secondary': [0, 0, 0, 0.6],   # Gris secundario
        'background': [1, 1, 1, 1],         # Blanco
        'surface': [0.95, 0.95, 0.95, 1]   # Gris claro
    }

    @staticmethod
    def get_talla_ropa_options():
        """Obtener opciones de tallas de ropa"""
        return PersonalUtils.TALLAS_ROPA_OPTIONS

    @staticmethod
    def get_tallas_zapatos_options():
        """Obtener opciones de tallas de zapatos"""
        return PersonalUtils.TALLAS_ZAPATOS_OPTIONS

    @staticmethod
    def get_estados_cuadrilla():
        """Obtener estados posibles de cuadrilla"""
        return PersonalUtils.ESTADOS_CUADRILLA

    @staticmethod
    def get_color(color_name):
        """Obtener color por nombre"""
        return PersonalUtils.COLORES_TEMA.get(color_name, [0, 0, 0, 1])

    @staticmethod
    def format_phone_number(phone):
        """
        Formatear número de teléfono para mostrar
        """
        if not phone:
            return ""

        # Limpiar teléfono (solo números)
        phone_clean = re.sub(r'[^\d]', '', str(phone))

        # Formato venezolano: 0424-123-4567
        if len(phone_clean) >= 10:
            if len(phone_clean) == 10:
                # Agregar 0 al inicio si no lo tiene
                phone_clean = "0" + phone_clean

            return f"{phone_clean[:4]}-{phone_clean[4:7]}-{phone_clean[7:]}"

        return phone_clean

    @staticmethod
    def clean_numeric_input(value):
        """
        Limpiar input para que solo contenga números
        """
        if not value:
            return ""

        return re.sub(r'[^\d]', '', str(value))

    @staticmethod
    def capitalize_words(text):
        """
        Capitalizar primera letra de cada palabra
        """
        if not text:
            return text

        return ' '.join(word.capitalize() for word in str(text).split())

    @staticmethod
    def truncate_text(text, max_length=50):
        """
        Truncar texto con puntos suspensivos
        """
        if not text:
            return ""

        if len(text) <= max_length:
            return text

        return text[:max_length - 3] + "..."

    @staticmethod
    def format_date_relative(date_obj):
        """
        Formatear fecha de forma relativa (hace X días)
        """
        if not date_obj:
            return "Fecha no disponible"

        try:
            if isinstance(date_obj, str):
                # Intentar parsear la fecha
                date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))

            now = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
            diff = now - date_obj

            if diff.days == 0:
                if diff.seconds < 3600:  # Menos de 1 hora
                    minutes = diff.seconds // 60
                    return f"Hace {minutes} minutos" if minutes > 0 else "Ahora mismo"
                else:  # Menos de 24 horas
                    hours = diff.seconds // 3600
                    return f"Hace {hours} horas"
            elif diff.days == 1:
                return "Ayer"
            elif diff.days < 7:
                return f"Hace {diff.days} días"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"Hace {weeks} semanas"
            else:
                months = diff.days // 30
                return f"Hace {months} meses"

        except:
            return "Fecha inválida"

    @staticmethod
    def format_date_spanish(fecha_raw):
        """Formatear fecha en español con formato Dom, 14/07/2025 13:20:32 - IMPLEMENTACIÓN ORIGINAL"""
        if not fecha_raw or fecha_raw == 'No especificada':
            return 'No especificada'

        try:
            # Diccionario de días en español
            dias_espanol = {
                'Monday': 'Lun',
                'Tuesday': 'Mar',
                'Wednesday': 'Mié',
                'Thursday': 'Jue',
                'Friday': 'Vie',
                'Saturday': 'Sáb',
                'Sunday': 'Dom'
            }

            # Si fecha_raw es un diccionario (respuesta de MongoDB), extraer el timestamp
            if isinstance(fecha_raw, dict) and '$date' in fecha_raw:
                timestamp = fecha_raw['$date']
                if isinstance(timestamp, (int, float)):
                    # Timestamp en milisegundos, convertir a segundos
                    fecha = datetime.fromtimestamp(timestamp / 1000)
                else:
                    # Probablemente string ISO
                    fecha = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(fecha_raw, str):
                # Intentar parsear diferentes formatos de string
                try:
                    # Formato GMT: "Sun, 14 Sep 2025 17:20:32 GMT"
                    if fecha_raw.endswith(' GMT'):
                        from datetime import timedelta
                        fecha_utc = datetime.strptime(fecha_raw, "%a, %d %b %Y %H:%M:%S GMT")
                        # Convertir de UTC a hora de Venezuela (UTC-4)
                        fecha = fecha_utc - timedelta(hours=4)
                    # ISO format with Z
                    elif 'T' in fecha_raw and fecha_raw.endswith('Z'):
                        fecha = datetime.fromisoformat(fecha_raw.replace('Z', '+00:00'))
                    # ISO format standard
                    elif 'T' in fecha_raw:
                        fecha = datetime.fromisoformat(fecha_raw)
                    else:
                        # Fallback genérico
                        fecha = datetime.fromisoformat(fecha_raw)
                except:
                    return fecha_raw  # Si no se puede parsear, devolver como está
            else:
                # Si es datetime object directamente
                fecha = fecha_raw

            # Formatear en español: Dom, 14/07/2025 13:20:32
            dia_ingles = fecha.strftime('%A')
            dia_espanol = dias_espanol.get(dia_ingles, dia_ingles[:3])
            fecha_formateada = fecha.strftime(f"{dia_espanol}, %d/%m/%Y %H:%M:%S")

            return fecha_formateada

        except Exception as e:
            print(f"Error formateando fecha: {e}, fecha_raw: {fecha_raw}")
            return str(fecha_raw)  # En caso de error, devolver como string

    @staticmethod
    def get_cuadrilla_estado_color(estado):
        """
        Obtener color según el estado de la cuadrilla
        """
        colores_estado = {
            'Activa': PersonalUtils.get_color('success'),
            'Inactiva': PersonalUtils.get_color('error'),
            'En formación': PersonalUtils.get_color('warning'),
            'Completada': PersonalUtils.get_color('info')
        }

        return colores_estado.get(estado, PersonalUtils.get_color('text_secondary'))

    @staticmethod
    def count_words(text):
        """
        Contar palabras en un texto
        """
        if not text:
            return 0

        return len(str(text).split())

    @staticmethod
    def sanitize_filename(filename):
        """
        Limpiar nombre de archivo para evitar caracteres problemáticos
        """
        if not filename:
            return "archivo"

        # Reemplazar caracteres problemáticos
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', str(filename))
        sanitized = re.sub(r'\s+', '_', sanitized)  # Espacios a guiones bajos
        sanitized = sanitized.strip('._')  # Remover puntos y guiones al inicio/final

        return sanitized if sanitized else "archivo"

    @staticmethod
    def generate_cuadrilla_code(numero_cuadrilla, actividad):
        """
        Generar código único para cuadrilla
        """
        if not numero_cuadrilla or not actividad:
            return "CUAD-000"

        # Tomar las primeras 3 letras de la actividad
        actividad_code = re.sub(r'[^a-zA-Z]', '', str(actividad))[:3].upper()
        if not actividad_code:
            actividad_code = "ACT"

        return f"CUAD-{numero_cuadrilla:03d}-{actividad_code}"

    @staticmethod
    def validate_file_size(file_size_bytes, max_size_mb=5):
        """
        Validar tamaño de archivo
        """
        max_size_bytes = max_size_mb * 1024 * 1024  # Convertir MB a bytes

        if file_size_bytes > max_size_bytes:
            return False, f"El archivo es demasiado grande. Máximo permitido: {max_size_mb}MB"

        return True, ""

    @staticmethod
    def get_file_extension(filename):
        """
        Obtener extensión de archivo
        """
        if not filename or '.' not in filename:
            return ""

        return filename.split('.')[-1].lower()

    @staticmethod
    def is_valid_image_extension(filename):
        """
        Verificar si la extensión es de imagen válida
        """
        valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        extension = PersonalUtils.get_file_extension(filename)

        return extension in valid_extensions

    @staticmethod
    def show_loading_message():
        """
        Mensaje de carga estándar
        """
        return "🔄 Cargando..."

    @staticmethod
    def show_success_message(action="operación"):
        """
        Mensaje de éxito estándar
        """
        return f"✅ {action.capitalize()} completada exitosamente"

    @staticmethod
    def show_error_message(action="operación"):
        """
        Mensaje de error estándar
        """
        return f"❌ Error al realizar {action}"

    @staticmethod
    def show_error_dialog(title, message):
        """Mostrar dialog de error"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton

        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDRaisedButton(
                    text="CERRAR",
                    md_bg_color=[0.5, 0.5, 0.5, 1],
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    @staticmethod
    def show_success_dialog(title, message):
        """Mostrar dialog de éxito"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton

        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDRaisedButton(
                    text="CERRAR",
                    md_bg_color=[0.2, 0.7, 0.3, 1],  # Verde
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    @staticmethod
    def format_currency(amount):
        """
        Formatear cantidad como moneda venezolana
        """
        if not amount:
            return "Bs. 0,00"

        try:
            # Convertir a float si es string
            if isinstance(amount, str):
                amount = float(amount.replace(',', '.'))

            # Formatear con puntos para miles y comas para decimales
            formatted = f"{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

            return f"Bs. {formatted}"

        except:
            return "Bs. 0,00"

    @staticmethod
    def get_age_from_date(birth_date):
        """
        Calcular edad desde fecha de nacimiento
        """
        if not birth_date:
            return None

        try:
            if isinstance(birth_date, str):
                birth_date = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))

            today = datetime.now()
            age = today.year - birth_date.year

            # Ajustar si no ha pasado el cumpleaños este año
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1

            return age

        except:
            return None

    @staticmethod
    def search_text_in_list(search_term, text_list, field_name=None):
        """
        Buscar término en lista de textos o diccionarios
        """
        if not search_term or not text_list:
            return text_list

        search_term = search_term.lower().strip()
        results = []

        for item in text_list:
            if field_name and isinstance(item, dict):
                # Buscar en campo específico de diccionario
                text_to_search = str(item.get(field_name, '')).lower()
            elif isinstance(item, dict):
                # Buscar en todos los valores del diccionario
                text_to_search = ' '.join(str(v).lower() for v in item.values())
            else:
                # Buscar en string directamente
                text_to_search = str(item).lower()

            if search_term in text_to_search:
                results.append(item)

        return results


# Instancia singleton para uso global
utils = PersonalUtils()

# Función helper para compatibilidad
def get_color(color_name):
    """Helper function para compatibilidad con imports directos"""
    return PersonalUtils.get_color(color_name)