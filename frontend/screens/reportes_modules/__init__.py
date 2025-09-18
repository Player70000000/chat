# Módulos de Reportes - Sistema Empresa Limpieza
# Arquitectura modular para gestión de reportes especializados

from .reportes_obreros import ReportesObrerosManager
from .reportes_moderadores import ReportesModeradoresManager
from .reportes_generales_manager import ReportesGeneralesManager
from .api_client import ReportesAPIClient
from .report_components import (
    ReportCard,
    StatsCard,
    ExportButton,
    ErrorDisplay,
    LoadingIndicator
)

__all__ = [
    'ReportesObrerosManager',
    'ReportesModeradoresManager',
    'ReportesGeneralesManager',
    'ReportesAPIClient',
    'ReportCard',
    'StatsCard',
    'ExportButton',
    'ErrorDisplay',
    'LoadingIndicator'
]