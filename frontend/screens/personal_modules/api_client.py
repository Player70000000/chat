"""
Cliente API centralizado para gestión de personal
Todas las llamadas HTTP del sistema de personal
"""

import requests
import sys
import os

# Importar configuración
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import API_BASE_URL


class PersonalAPIClient:
    """Cliente centralizado para todas las operaciones API del sistema de personal"""

    def __init__(self):
        self.base_url = API_BASE_URL
        self.timeout = 10

    def _make_request(self, method, endpoint, data=None, params=None):
        """Método genérico para hacer requests con manejo de errores"""
        try:
            url = f"{self.base_url}{endpoint}"

            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")

            response.raise_for_status()

            # Si la respuesta está vacía, retornar success
            if not response.content:
                return {"success": True}

            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("La conexión ha tardado demasiado. Verifica tu conexión a internet.")
        except requests.exceptions.ConnectionError:
            raise Exception("No se pudo conectar al servidor. Verifica tu conexión a internet.")
        except requests.exceptions.HTTPError as e:
            if hasattr(e.response, 'json') and e.response.content:
                try:
                    error_data = e.response.json()
                    raise Exception(error_data.get('error', f'Error HTTP {e.response.status_code}'))
                except:
                    raise Exception(f"Error del servidor: {e.response.status_code}")
            else:
                raise Exception(f"Error HTTP: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Error inesperado: {str(e)}")

    # ===========================================
    # MÉTODOS PARA CUADRILLAS
    # ===========================================

    def get_cuadrillas(self):
        """Obtener lista de todas las cuadrillas"""
        return self._make_request('GET', '/api/personnel/cuadrillas/')

    def create_cuadrilla(self, cuadrilla_data):
        """Crear nueva cuadrilla"""
        return self._make_request('POST', '/api/personnel/cuadrillas/', data=cuadrilla_data)

    def update_cuadrilla(self, cuadrilla_id, cuadrilla_data):
        """Actualizar cuadrilla existente"""
        return self._make_request('PUT', f'/api/personnel/cuadrillas/', data={
            'id': cuadrilla_id,
            **cuadrilla_data
        })

    def delete_cuadrilla(self, cuadrilla_id):
        """Eliminar cuadrilla"""
        return self._make_request('DELETE', f'/api/personnel/cuadrillas/{cuadrilla_id}')

    def get_next_cuadrilla_number(self):
        """Obtener próximo número de cuadrilla disponible"""
        return self._make_request('GET', '/api/personnel/cuadrillas/next-number/')

    # ===========================================
    # MÉTODOS PARA MODERADORES
    # ===========================================

    def get_moderadores(self):
        """Obtener lista de todos los moderadores"""
        return self._make_request('GET', '/api/personnel/moderadores/')

    def create_moderador(self, moderador_data):
        """Crear nuevo moderador"""
        return self._make_request('POST', '/api/personnel/moderadores/', data=moderador_data)

    def update_moderador(self, moderador_data):
        """Actualizar moderador existente"""
        return self._make_request('PUT', '/api/personnel/moderadores/', data=moderador_data)

    def delete_moderador(self, moderador_data):
        """Eliminar moderador"""
        delete_data = {"cedula": moderador_data.get('cedula')}
        return self._make_request('DELETE', '/api/personnel/moderadores/', data=delete_data)

    # ===========================================
    # MÉTODOS PARA OBREROS
    # ===========================================

    def get_obreros(self):
        """Obtener lista de todos los obreros"""
        return self._make_request('GET', '/api/personnel/obreros/')

    def create_obrero(self, obrero_data):
        """Crear nuevo obrero"""
        return self._make_request('POST', '/api/personnel/obreros/', data=obrero_data)

    def update_obrero(self, obrero_data):
        """Actualizar obrero existente"""
        return self._make_request('PUT', '/api/personnel/obreros/', data=obrero_data)

    def delete_obrero(self, obrero_data):
        """Eliminar obrero"""
        delete_data = {"cedula": obrero_data.get('cedula')}
        return self._make_request('DELETE', '/api/personnel/obreros/', data=delete_data)

    def get_obreros_disponibles(self):
        """Obtener obreros disponibles para asignar a cuadrillas"""
        return self._make_request('GET', '/api/personnel/obreros/disponibles/')

    def search_obreros_by_cedula(self, cedula_partial):
        """Buscar obreros por cédula parcial"""
        return self._make_request('GET', '/api/personnel/obreros/', params={'cedula_partial': cedula_partial})

    def find_obrero_cuadrilla(self, obrero_id):
        """Encontrar la cuadrilla a la que pertenece un obrero"""
        try:
            cuadrillas_response = self.get_cuadrillas()
            cuadrillas = cuadrillas_response.get('cuadrillas', [])

            for cuadrilla in cuadrillas:
                obreros_ids = cuadrilla.get('obreros', [])
                if obrero_id in obreros_ids:
                    return cuadrilla.get('actividad', 'Cuadrilla sin nombre')

            return None  # No está en ninguna cuadrilla
        except:
            return None

    def find_moderador_cuadrilla(self, moderador_id):
        """Encontrar la cuadrilla que tiene asignado un moderador"""
        try:
            cuadrillas_response = self.get_cuadrillas()
            cuadrillas = cuadrillas_response.get('cuadrillas', [])

            for cuadrilla in cuadrillas:
                moderador_asignado_id = cuadrilla.get('moderador_id')
                if moderador_asignado_id == moderador_id:
                    return cuadrilla.get('actividad', 'Cuadrilla sin nombre')

            return None  # No tiene cuadrillas asignadas
        except:
            return None

    # ===========================================
    # MÉTODOS DE VALIDACIÓN
    # ===========================================

    def check_all_duplicates_optimized(self, cedula, email, telefono, exclude_id=None):
        """
        Verificar duplicados de cédula, email y teléfono en una sola consulta optimizada
        Returns: (cedula_exists, cedula_where, email_exists, email_where, telefono_exists, telefono_where)
        """
        try:
            # Hacer solo 2 llamadas en lugar de 6
            moderadores_data = self.get_moderadores()
            obreros_data = self.get_obreros()

            moderadores = moderadores_data.get('moderadores', [])
            obreros = obreros_data.get('obreros', [])

            # Variables de resultado
            cedula_exists, cedula_where = False, None
            email_exists, email_where = False, None
            telefono_exists, telefono_where = False, None

            # Verificar en moderadores
            for mod in moderadores:
                mod_id = str(mod.get('_id', ''))
                if mod_id != str(exclude_id or ''):
                    if not cedula_exists and mod.get('cedula') == cedula:
                        cedula_exists, cedula_where = True, 'moderadores'
                    if not email_exists and mod.get('email', '').lower() == email.lower():
                        email_exists, email_where = True, 'moderadores'
                    if not telefono_exists and mod.get('telefono') == telefono:
                        telefono_exists, telefono_where = True, 'moderadores'

            # Verificar en obreros
            for obr in obreros:
                obr_id = str(obr.get('_id', ''))
                if obr_id != str(exclude_id or ''):
                    if not cedula_exists and obr.get('cedula') == cedula:
                        cedula_exists, cedula_where = True, 'obreros'
                    if not email_exists and obr.get('email', '').lower() == email.lower():
                        email_exists, email_where = True, 'obreros'
                    if not telefono_exists and obr.get('telefono') == telefono:
                        telefono_exists, telefono_where = True, 'obreros'

            return cedula_exists, cedula_where, email_exists, email_where, telefono_exists, telefono_where

        except Exception:
            # Si hay error, asumir que no existen duplicados
            return False, None, False, None, False, None

    def check_cedula_exists(self, cedula, exclude_id=None):
        """Verificar si una cédula ya existe en el sistema"""
        params = {'cedula': cedula}
        if exclude_id:
            params['exclude_id'] = exclude_id

        try:
            # Verificar en moderadores
            moderadores = self.get_moderadores()
            for mod in moderadores.get('moderadores', []):  # ← CORRECCIÓN
                if mod.get('cedula') == cedula and str(mod.get('_id', '')) != str(exclude_id or ''):
                    return True, 'moderadores'

            # Verificar en obreros
            obreros = self.get_obreros()
            for obr in obreros.get('obreros', []):  # ← CORRECCIÓN
                if obr.get('cedula') == cedula and str(obr.get('_id', '')) != str(exclude_id or ''):
                    return True, 'obreros'

            return False, None

        except Exception:
            # Si hay error en la verificación, asumir que no existe
            return False, None

    def check_email_exists(self, email, exclude_id=None):
        """Verificar si un email ya existe en el sistema"""
        try:
            # Verificar en moderadores
            moderadores = self.get_moderadores()
            for mod in moderadores.get('moderadores', []):  # ← CORRECCIÓN
                if mod.get('email', '').lower() == email.lower() and str(mod.get('_id', '')) != str(exclude_id or ''):
                    return True, 'moderadores'

            # Verificar en obreros
            obreros = self.get_obreros()
            for obr in obreros.get('obreros', []):  # ← CORRECCIÓN
                if obr.get('email', '').lower() == email.lower() and str(obr.get('_id', '')) != str(exclude_id or ''):
                    return True, 'obreros'

            return False, None

        except Exception:
            return False, None

    def check_telefono_exists(self, telefono, exclude_id=None):
        """Verificar si un teléfono ya existe en el sistema"""
        try:
            # Verificar en moderadores
            moderadores = self.get_moderadores()
            for mod in moderadores.get('moderadores', []):  # ← CORRECCIÓN
                if mod.get('telefono') == telefono and str(mod.get('_id', '')) != str(exclude_id or ''):
                    return True, 'moderadores'

            # Verificar en obreros
            obreros = self.get_obreros()
            for obr in obreros.get('obreros', []):  # ← CORRECCIÓN
                if obr.get('telefono') == telefono and str(obr.get('_id', '')) != str(exclude_id or ''):
                    return True, 'obreros'

            return False, None

        except Exception:
            return False, None


# Instancia singleton para uso global
api_client = PersonalAPIClient()