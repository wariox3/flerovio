"""Rutas estándar de la aplicación (logs, configuración, datos).

Usa QStandardPaths para respetar las convenciones de cada sistema operativo.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths


def _ruta(tipo: QStandardPaths.StandardLocation, subcarpeta: str | None = None) -> Path:
    base = Path(QStandardPaths.writableLocation(tipo))
    destino = base / subcarpeta if subcarpeta else base
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def directorio_datos() -> Path:
    """Datos de la aplicación (BD locales, caché persistente)."""
    return _ruta(QStandardPaths.StandardLocation.AppDataLocation)


def directorio_configuracion() -> Path:
    """Archivos de configuración del usuario."""
    return _ruta(QStandardPaths.StandardLocation.AppConfigLocation)


def directorio_registros() -> Path:
    """Directorio donde se escriben los archivos de log."""
    return _ruta(QStandardPaths.StandardLocation.AppDataLocation, "registros")
