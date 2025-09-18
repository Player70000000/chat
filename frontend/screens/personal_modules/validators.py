"""
Validadores centralizados para sistema de personal
Todas las reglas de validación y formateo
"""

import re
from datetime import datetime


class PersonalValidators:
    """Clase con todas las validaciones del sistema de personal"""

    # Constantes de validación
    MIN_CEDULA_LENGTH = 6
    MAX_CEDULA_LENGTH = 10
    MIN_TELEFONO_LENGTH = 10
    TALLAS_ROPA = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    MIN_TALLA_ZAPATOS = 30
    MAX_TALLA_ZAPATOS = 50

    @staticmethod
    def validate_cedula(cedula):
        """
        Validar cédula de identidad
        Returns: (is_valid, error_message)
        """
        if not cedula:
            return False, "La cédula es obligatoria"

        # Limpiar la cédula (solo números)
        cedula_clean = re.sub(r'[^\d]', '', str(cedula))

        if len(cedula_clean) < PersonalValidators.MIN_CEDULA_LENGTH:
            return False, f"La cédula debe tener al menos {PersonalValidators.MIN_CEDULA_LENGTH} dígitos"

        if len(cedula_clean) > PersonalValidators.MAX_CEDULA_LENGTH:
            return False, f"La cédula no puede tener más de {PersonalValidators.MAX_CEDULA_LENGTH} dígitos"

        if not cedula_clean.isdigit():
            return False, "La cédula solo puede contener números"

        return True, ""

    @staticmethod
    def validate_email(email):
        """
        Validar formato de email
        Returns: (is_valid, error_message)
        """
        if not email:
            return False, "El email es obligatorio"

        # Patrón básico de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            return False, "El formato del email no es válido (ejemplo: usuario@dominio.com)"

        return True, ""

    @staticmethod
    def validate_telefono(telefono):
        """
        Validar número de teléfono
        Returns: (is_valid, error_message)
        """
        if not telefono:
            return False, "El teléfono es obligatorio"

        # Limpiar teléfono (solo números)
        telefono_clean = re.sub(r'[^\d]', '', str(telefono))

        if len(telefono_clean) < PersonalValidators.MIN_TELEFONO_LENGTH:
            return False, f"El teléfono debe tener al menos {PersonalValidators.MIN_TELEFONO_LENGTH} dígitos"

        if not telefono_clean.isdigit():
            return False, "El teléfono solo puede contener números"

        return True, ""

    @staticmethod
    def validate_nombre(nombre, campo_nombre="nombre"):
        """
        Validar nombre o apellido
        Returns: (is_valid, error_message)
        """
        if not nombre:
            return False, f"El {campo_nombre} es obligatorio"

        if not isinstance(nombre, str):
            return False, f"El {campo_nombre} debe ser texto"

        # Verificar que no contenga números
        if any(char.isdigit() for char in nombre):
            return False, f"El {campo_nombre} no puede contener números"

        # Verificar longitud mínima
        if len(nombre.strip()) < 2:
            return False, f"El {campo_nombre} debe tener al menos 2 caracteres"

        return True, ""

    @staticmethod
    def validate_apellidos(apellidos):
        """Validar apellidos específicamente"""
        return PersonalValidators.validate_nombre(apellidos, "apellidos")

    @staticmethod
    def validate_talla_ropa(talla):
        """
        Validar talla de ropa
        Returns: (is_valid, error_message)
        """
        if not talla:
            return True, ""  # Talla es opcional

        if talla == "No ingresado":
            return True, ""  # Opción de no seleccionar talla

        if talla not in PersonalValidators.TALLAS_ROPA:
            return False, f"Talla inválida. Opciones: {', '.join(PersonalValidators.TALLAS_ROPA)}"

        return True, ""

    @staticmethod
    def validate_talla_zapatos(talla):
        """
        Validar talla de zapatos
        Returns: (is_valid, error_message)
        """
        if not talla:
            return True, ""  # Talla es opcional

        if talla == "No ingresado":
            return True, ""  # Opción de no seleccionar talla

        try:
            talla_num = int(talla)
            if talla_num < PersonalValidators.MIN_TALLA_ZAPATOS or talla_num > PersonalValidators.MAX_TALLA_ZAPATOS:
                return False, f"Talla de zapatos debe estar entre {PersonalValidators.MIN_TALLA_ZAPATOS} y {PersonalValidators.MAX_TALLA_ZAPATOS}"
            return True, ""
        except ValueError:
            return False, "La talla de zapatos debe ser un número"

    @staticmethod
    def validate_actividad(actividad):
        """
        Validar actividad de cuadrilla
        Returns: (is_valid, error_message)
        """
        if not actividad:
            return False, "La actividad es obligatoria"

        if len(actividad.strip()) < 3:
            return False, "La actividad debe tener al menos 3 caracteres"

        return True, ""

    @staticmethod
    def validate_moderador_fields(data):
        """
        Validar todos los campos de un moderador
        Returns: (is_valid, errors_dict)
        """
        errors = {}

        # Validar nombre
        is_valid, error = PersonalValidators.validate_nombre(data.get('nombre', ''))
        if not is_valid:
            errors['nombre'] = error

        # Validar apellidos
        is_valid, error = PersonalValidators.validate_apellidos(data.get('apellidos', ''))
        if not is_valid:
            errors['apellidos'] = error

        # Validar cédula
        is_valid, error = PersonalValidators.validate_cedula(data.get('cedula', ''))
        if not is_valid:
            errors['cedula'] = error

        # Validar email
        is_valid, error = PersonalValidators.validate_email(data.get('email', ''))
        if not is_valid:
            errors['email'] = error

        # Validar teléfono
        is_valid, error = PersonalValidators.validate_telefono(data.get('telefono', ''))
        if not is_valid:
            errors['telefono'] = error

        # Validar talla de ropa (opcional)
        if data.get('talla_ropa'):
            is_valid, error = PersonalValidators.validate_talla_ropa(data.get('talla_ropa'))
            if not is_valid:
                errors['talla_ropa'] = error

        # Validar talla de zapatos (opcional)
        if data.get('talla_zapatos'):
            is_valid, error = PersonalValidators.validate_talla_zapatos(data.get('talla_zapatos'))
            if not is_valid:
                errors['talla_zapatos'] = error

        return len(errors) == 0, errors

    @staticmethod
    def validate_obrero_fields(data):
        """
        Validar todos los campos de un obrero
        Returns: (is_valid, errors_dict)
        """
        # Los obreros tienen las mismas validaciones que los moderadores
        return PersonalValidators.validate_moderador_fields(data)

    @staticmethod
    def validate_cuadrilla_fields(data):
        """
        Validar todos los campos de una cuadrilla
        Returns: (is_valid, errors_dict)
        """
        errors = {}

        # Validar actividad
        is_valid, error = PersonalValidators.validate_actividad(data.get('actividad', ''))
        if not is_valid:
            errors['actividad'] = error

        # Validar que tenga moderador
        if not data.get('moderador_id'):
            errors['moderador'] = "Debe seleccionar un moderador para la cuadrilla"

        # Validar que tenga al menos un obrero
        obreros = data.get('obreros', [])
        if not obreros or len(obreros) == 0:
            errors['obreros'] = "Debe asignar al menos un obrero a la cuadrilla"

        return len(errors) == 0, errors

    @staticmethod
    def capitalize_first_letter(text):
        """
        Capitalizar primera letra de cada palabra
        """
        if not text:
            return text

        return ' '.join(word.capitalize() for word in str(text).split())

    @staticmethod
    def clean_cedula_input(cedula):
        """
        Limpiar entrada de cédula (solo números)
        """
        if not cedula:
            return ""

        return re.sub(r'[^\d]', '', str(cedula))

    @staticmethod
    def clean_telefono_input(telefono):
        """
        Limpiar entrada de teléfono (solo números)
        """
        if not telefono:
            return ""

        return re.sub(r'[^\d]', '', str(telefono))

    @staticmethod
    def format_cedula_display(cedula):
        """
        Formatear cédula para mostrar (con puntos)
        """
        if not cedula:
            return ""

        cedula_clean = PersonalValidators.clean_cedula_input(cedula)

        # Agregar puntos cada 3 dígitos desde la derecha
        if len(cedula_clean) > 3:
            # Formato: 12.345.678
            formatted = ""
            for i, digit in enumerate(reversed(cedula_clean)):
                if i > 0 and i % 3 == 0:
                    formatted = "." + formatted
                formatted = digit + formatted
            return formatted

        return cedula_clean

    @staticmethod
    def format_telefono_display(telefono):
        """
        Formatear teléfono para mostrar
        """
        if not telefono:
            return ""

        telefono_clean = PersonalValidators.clean_telefono_input(telefono)

        # Formato para Venezuela: 0424-123-4567
        if len(telefono_clean) >= 10:
            return f"{telefono_clean[:4]}-{telefono_clean[4:7]}-{telefono_clean[7:]}"

        return telefono_clean

    @staticmethod
    def format_date_spanish(date_obj):
        """
        Formatear fecha en español
        """
        if not date_obj:
            return "Fecha no disponible"

        try:
            if isinstance(date_obj, str):
                # Intentar parsear la fecha
                date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))

            # Nombres de meses en español
            meses = [
                'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
            ]

            return f"{date_obj.day} de {meses[date_obj.month - 1]} de {date_obj.year}"

        except:
            return "Fecha inválida"


# Instancia singleton para uso global
validators = PersonalValidators()