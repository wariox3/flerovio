"""Manejador global de excepciones no capturadas."""

from __future__ import annotations

import logging
import sys
import traceback
from types import TracebackType

from PySide6.QtWidgets import QApplication, QMessageBox

_log = logging.getLogger(__name__)


def _manejar(
    tipo: type[BaseException],
    valor: BaseException,
    rastro: TracebackType | None,
) -> None:
    if issubclass(tipo, KeyboardInterrupt):
        sys.__excepthook__(tipo, valor, rastro)
        return

    _log.critical("Excepción no capturada", exc_info=(tipo, valor, rastro))

    if QApplication.instance() is None:
        return

    detalle = "".join(traceback.format_exception(tipo, valor, rastro))
    dialogo = QMessageBox()
    dialogo.setIcon(QMessageBox.Icon.Critical)
    dialogo.setWindowTitle("Error inesperado")
    dialogo.setText("Ha ocurrido un error inesperado en la aplicación.")
    dialogo.setInformativeText(f"{tipo.__name__}: {valor}")
    dialogo.setDetailedText(detalle)
    dialogo.setStandardButtons(QMessageBox.StandardButton.Close)
    dialogo.exec()


def instalar_manejador_global() -> None:
    """Reemplaza sys.excepthook por uno que registra y muestra un diálogo."""
    sys.excepthook = _manejar
