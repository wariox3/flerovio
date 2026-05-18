"""Configuración del sistema de registro (logging) de la aplicación."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from flerovio.nucleo.rutas import directorio_registros

_FORMATO = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_NOMBRE_ARCHIVO = "flerovio.log"
_TAMANO_MAX_BYTES = 1_048_576  # 1 MiB
_COPIAS = 5


def configurar_registro(nivel: int = logging.INFO) -> Path:
    """Configura el logger raíz con salida a archivo rotado y a stderr.

    Devuelve la ruta del archivo de log para que el llamador pueda mostrarla.
    Idempotente: si ya estaba configurado, no duplica manejadores.
    """
    raiz = logging.getLogger()
    raiz.setLevel(nivel)

    archivo_log = directorio_registros() / _NOMBRE_ARCHIVO

    if any(getattr(h, "_flerovio", False) for h in raiz.handlers):
        return archivo_log

    formato = logging.Formatter(_FORMATO)

    manejador_archivo = logging.handlers.RotatingFileHandler(
        archivo_log,
        maxBytes=_TAMANO_MAX_BYTES,
        backupCount=_COPIAS,
        encoding="utf-8",
    )
    manejador_archivo.setFormatter(formato)
    manejador_archivo._flerovio = True  # type: ignore[attr-defined]
    raiz.addHandler(manejador_archivo)

    manejador_consola = logging.StreamHandler()
    manejador_consola.setFormatter(formato)
    manejador_consola._flerovio = True  # type: ignore[attr-defined]
    raiz.addHandler(manejador_consola)

    logging.getLogger(__name__).info("Registro configurado en %s", archivo_log)
    return archivo_log
