import requests
import json
from typing import Dict, List, Optional, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import API_BASE_URL


class ReportesAPIClient:
    """Cliente API centralizado para todos los reportes del sistema"""

    def __init__(self):
        self.base_url = API_BASE_URL
        self.timeout = 10

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Realizar petición HTTP con manejo de errores centralizado"""
        try:
            url = f"{self.base_url}{endpoint}"

            if method.upper() == 'GET':
                response = requests.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': f"Error del servidor: {response.status_code}",
                    'status_code': response.status_code
                }

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': "Error de conexión al servidor",
                'status_code': 0
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': "Tiempo de espera agotado",
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error inesperado: {str(e)}",
                'status_code': 0
            }

    # === REPORTES DE OBREROS ===
    def get_resumen_obreros(self) -> Dict[str, Any]:
        """Obtener resumen estadístico de obreros"""
        return self._make_request('GET', '/api/reports/obreros/resumen')

    def get_obreros_por_talla_ropa(self) -> Dict[str, Any]:
        """Obtener distribución de obreros por talla de ropa"""
        return self._make_request('GET', '/api/reports/obreros/tallas-ropa')

    def get_obreros_por_talla_zapatos(self) -> Dict[str, Any]:
        """Obtener distribución de obreros por talla de zapatos"""
        return self._make_request('GET', '/api/reports/obreros/tallas-zapatos')

    def get_obreros_activos_inactivos(self) -> Dict[str, Any]:
        """Obtener estadísticas de obreros activos vs inactivos"""
        return self._make_request('GET', '/api/reports/obreros/activos-inactivos')

    def get_obreros_recientes(self, dias: int = 30) -> Dict[str, Any]:
        """Obtener obreros registrados recientemente"""
        return self._make_request('GET', f'/api/reports/obreros/recientes?dias={dias}')

    def exportar_obreros(self) -> Dict[str, Any]:
        """Exportar datos completos de obreros"""
        return self._make_request('GET', '/api/reports/exportar/obreros')

    # === REPORTES DE MODERADORES ===
    def get_resumen_moderadores(self) -> Dict[str, Any]:
        """Obtener resumen estadístico de moderadores"""
        return self._make_request('GET', '/api/reports/moderadores/resumen')

    def get_moderadores_por_talla_ropa(self) -> Dict[str, Any]:
        """Obtener distribución de moderadores por talla de ropa"""
        return self._make_request('GET', '/api/reports/moderadores/tallas-ropa')

    def get_moderadores_por_talla_zapatos(self) -> Dict[str, Any]:
        """Obtener distribución de moderadores por talla de zapatos"""
        return self._make_request('GET', '/api/reports/moderadores/tallas-zapatos')

    def get_moderadores_activos_inactivos(self) -> Dict[str, Any]:
        """Obtener estadísticas de moderadores activos vs inactivos"""
        return self._make_request('GET', '/api/reports/moderadores/activos-inactivos')

    def get_moderadores_recientes(self, dias: int = 30) -> Dict[str, Any]:
        """Obtener moderadores registrados recientemente"""
        return self._make_request('GET', f'/api/reports/moderadores/recientes?dias={dias}')

    def exportar_moderadores(self) -> Dict[str, Any]:
        """Exportar datos completos de moderadores"""
        return self._make_request('GET', '/api/reports/exportar/moderadores')

    # === REPORTES GENERALES ===
    def get_resumen_general(self) -> Dict[str, Any]:
        """Obtener resumen general del sistema"""
        return self._make_request('GET', '/api/reports/general/resumen')

    def get_resumen_personal(self) -> Dict[str, Any]:
        """Obtener resumen de personal (legacy - mantener compatibilidad)"""
        return self._make_request('GET', '/api/reports/personal/resumen')

    def get_actividad_chat(self) -> Dict[str, Any]:
        """Obtener estadísticas de actividad del chat"""
        return self._make_request('GET', '/api/reports/chat/resumen')

    def get_cuadrillas_por_actividad(self) -> Dict[str, Any]:
        """Obtener distribución de cuadrillas por actividad"""
        return self._make_request('GET', '/api/reports/personal/cuadrillas-por-actividad')

    def get_estadisticas_globales(self) -> Dict[str, Any]:
        """Obtener estadísticas globales del sistema"""
        return self._make_request('GET', '/api/reports/general/estadisticas-globales')

    def exportar_cuadrillas(self) -> Dict[str, Any]:
        """Exportar datos de cuadrillas"""
        return self._make_request('GET', '/api/reports/exportar/cuadrillas')

    def exportar_canales(self) -> Dict[str, Any]:
        """Exportar datos de canales de chat"""
        return self._make_request('GET', '/api/reports/exportar/canales')

    # === UTILIDADES ===
    def verificar_conexion(self) -> Dict[str, Any]:
        """Verificar conexión con el servidor"""
        return self._make_request('GET', '/verificar')

    def get_status_sistema(self) -> Dict[str, Any]:
        """Obtener estado general del sistema"""
        return self._make_request('GET', '/api/auth/status')