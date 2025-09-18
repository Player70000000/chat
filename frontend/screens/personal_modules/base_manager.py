"""
Clase base para los gestores de personal
Centraliza funcionalidades comunes para evitar duplicación
"""

from . import ui_components


class BasePersonalManager:
    """Clase base con funcionalidades comunes para todos los managers de personal"""

    def show_error_dialog(self, message):
        """Mostrar dialog de error"""
        dialog = ui_components.create_error_dialog(message)
        dialog.open()

    def show_success_dialog(self, message, callback=None):
        """Mostrar dialog de éxito"""
        dialog = ui_components.create_success_dialog(message, callback)
        dialog.open()

    def show_info_dialog(self, title, message, callback=None):
        """Mostrar dialog informativo"""
        dialog = ui_components.create_info_dialog(title, message, callback)
        dialog.open()