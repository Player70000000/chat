import re
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

def format_date(fecha):
    """Formatear fecha de forma consistente"""
    if isinstance(fecha, datetime):
        return fecha.strftime('%d/%m/%Y %H:%M')
    if isinstance(fecha, str):
        try:
            fecha_obj = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
            return fecha_obj.strftime('%d/%m/%Y %H:%M')
        except:
            pass
    return 'Fecha no disponible'

def validate_canal_data(datos):
    """Validar datos de canal de forma centralizada"""
    nombre = datos.get('nombre', '').strip()
    descripcion = datos.get('descripcion', '').strip()
    
    if not nombre:
        return None, "El nombre del canal es obligatorio"
    
    if len(nombre) > 50:
        return None, "El nombre no puede exceder 50 caracteres"
    
    if len(descripcion) > 300:
        return None, "La descripción no puede exceder 300 caracteres"
    
    if not re.match(r'^[a-zA-Z0-9\s\-_#]+$', nombre):
        return None, "El nombre contiene caracteres no permitidos"
    
    return {"nombre": nombre, "descripcion": descripcion}, None

def validate_message_data(datos):
    """Validar datos de mensaje"""
    mensaje = datos.get('mensaje', '').strip()
    
    if not mensaje:
        return None, "El mensaje no puede estar vacío"
    
    if len(mensaje) > 1000:
        return None, "El mensaje no puede exceder 1000 caracteres"
    
    return {"mensaje": mensaje}, None

def validate_object_id(id_string):
    """Validar y convertir string a ObjectId"""
    try:
        return ObjectId(id_string)
    except (InvalidId, TypeError):
        return None

def validate_message_estado(estado):
    """Validar estado de mensaje"""
    estados_validos = ['enviado', 'entregado', 'leido', 'editado']
    estado = estado.strip().lower()
    
    if estado not in estados_validos:
        return None, f"Estado inválido. Estados válidos: {', '.join(estados_validos)}"
    
    return estado, None

def validate_cuadrilla_data(datos):
    """Validar datos de cuadrilla"""
    numero_cuadrilla = str(datos.get('numero_cuadrilla', '')).strip()
    actividad = datos.get('actividad', '').strip()
    
    if not numero_cuadrilla:
        return None, "El número de cuadrilla es obligatorio"
    
    if not actividad:
        return None, "La actividad es obligatoria"
    
    if len(numero_cuadrilla) > 10:
        return None, "El número de cuadrilla no puede exceder 10 caracteres"
    
    if len(actividad) > 100:
        return None, "La actividad no puede exceder 100 caracteres"
    
    return {
        "numero_cuadrilla": numero_cuadrilla,
        "actividad": actividad
    }, None

def validate_obrero_data(datos):
    """Validar datos de obrero"""
    nombre = datos.get('nombre', '').strip()
    apellido = datos.get('apellido', '').strip()
    cedula = str(datos.get('cedula', '')).strip()
    
    if not nombre:
        return None, "El nombre es obligatorio"
    
    if not apellido:
        return None, "El apellido es obligatorio"
    
    if not cedula:
        return None, "La cédula es obligatoria"
    
    if len(nombre) > 50:
        return None, "El nombre no puede exceder 50 caracteres"
    
    if len(apellido) > 50:
        return None, "El apellido no puede exceder 50 caracteres"
    
    if len(cedula) > 20:
        return None, "La cédula no puede exceder 20 caracteres"
    
    if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', nombre):
        return None, "El nombre contiene caracteres no válidos"
    
    if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', apellido):
        return None, "El apellido contiene caracteres no válidos"
    
    if not re.match(r'^[0-9V-]+$', cedula):
        return None, "La cédula contiene caracteres no válidos"
    
    return {
        "nombre": nombre,
        "apellido": apellido,
        "cedula": cedula
    }, None