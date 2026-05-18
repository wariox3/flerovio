"""Almacenamiento seguro de credenciales (tokens) usando keyring.

El backend depende del sistema (Secret Service en Linux, Credential Locker en
Windows, Keychain en macOS). Si keyring no está disponible o falla, todas las
operaciones se degradan silenciosamente (devuelven None / no guardan) y se
registra una advertencia: la app sigue funcionando sin recordar credenciales.
"""

from __future__ import annotations

import logging

import keyring
import keyring.errors

_log = logging.getLogger(__name__)

_SERVICIO = "flerovio"


def guardar_token(email: str, token: str) -> bool:
    """Guarda el token asociado a un email. Devuelve True si tuvo éxito."""
    try:
        keyring.set_password(_SERVICIO, email, token)
        return True
    except keyring.errors.KeyringError as e:
        _log.warning("No se pudo guardar el token en keyring: %s", e)
        return False


def leer_token(email: str) -> str | None:
    try:
        return keyring.get_password(_SERVICIO, email)
    except keyring.errors.KeyringError as e:
        _log.warning("No se pudo leer el token de keyring: %s", e)
        return None


def eliminar_token(email: str) -> None:
    try:
        keyring.delete_password(_SERVICIO, email)
    except keyring.errors.PasswordDeleteError:
        # No había nada guardado, no es un error.
        pass
    except keyring.errors.KeyringError as e:
        _log.warning("No se pudo eliminar el token de keyring: %s", e)
