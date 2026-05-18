"""Acceso centralizado a la configuración persistente con QSettings.

QSettings usa el nombre de organización y aplicación de QCoreApplication para
elegir el almacén (registro de Windows, archivo .ini en Linux, etc.). Por eso
es importante haber llamado a setOrganizationName/setApplicationName antes.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QSettings

_GRUPO_VENTANA = "ventana_principal"
_CLAVE_GEOMETRIA = "geometria"
_CLAVE_ESTADO = "estado"

_GRUPO_SESION = "sesion"
_CLAVE_ULTIMO_EMAIL = "ultimo_email"
_CLAVE_RECORDARME = "recordarme"


def _ajustes() -> QSettings:
    return QSettings()


def guardar_geometria_ventana(geometria: QByteArray, estado: QByteArray) -> None:
    s = _ajustes()
    s.beginGroup(_GRUPO_VENTANA)
    s.setValue(_CLAVE_GEOMETRIA, geometria)
    s.setValue(_CLAVE_ESTADO, estado)
    s.endGroup()


def cargar_geometria_ventana() -> tuple[QByteArray | None, QByteArray | None]:
    s = _ajustes()
    s.beginGroup(_GRUPO_VENTANA)
    geometria = s.value(_CLAVE_GEOMETRIA)
    estado = s.value(_CLAVE_ESTADO)
    s.endGroup()
    return geometria, estado


def guardar_ultimo_email(email: str) -> None:
    s = _ajustes()
    s.beginGroup(_GRUPO_SESION)
    s.setValue(_CLAVE_ULTIMO_EMAIL, email)
    s.endGroup()


def cargar_ultimo_email() -> str | None:
    s = _ajustes()
    s.beginGroup(_GRUPO_SESION)
    valor = s.value(_CLAVE_ULTIMO_EMAIL)
    s.endGroup()
    return valor if isinstance(valor, str) and valor else None


def guardar_recordarme(activo: bool) -> None:
    s = _ajustes()
    s.beginGroup(_GRUPO_SESION)
    s.setValue(_CLAVE_RECORDARME, activo)
    s.endGroup()


def cargar_recordarme() -> bool:
    s = _ajustes()
    s.beginGroup(_GRUPO_SESION)
    valor = s.value(_CLAVE_RECORDARME, False, type=bool)
    s.endGroup()
    return bool(valor)
