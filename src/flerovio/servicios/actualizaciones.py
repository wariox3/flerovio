"""Verificador de actualizaciones contra GitHub Releases."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx
from PySide6.QtCore import QObject, Signal

from flerovio import __version__

_log = logging.getLogger(__name__)

REPO_GITHUB = "wariox3/flerovio"
URL_LATEST = f"https://api.github.com/repos/{REPO_GITHUB}/releases/latest"
_TIEMPO_ESPERA = 10.0


@dataclass(frozen=True)
class Actualizacion:
    version: str
    url_descarga: str
    notas: str
    nombre_archivo: str
    url_pagina: str = ""


def _parse_version(s: str) -> tuple[int, ...]:
    """Convierte '1.2.3' o 'v1.2.3' en tupla numérica para comparar.

    Ignora sufijos no numéricos (rc1, beta, etc.) para una comparación simple;
    es suficiente para versionado SemVer básico.
    """
    s = s.lstrip("vV").strip()
    partes = re.split(r"[.\-+]", s)
    return tuple(int(p) for p in partes if p.isdigit())


def es_mas_nueva(remota: str, local: str) -> bool:
    try:
        return _parse_version(remota) > _parse_version(local)
    except ValueError:
        return False


def _encontrar_asset_exe(assets: list[dict]) -> dict | None:
    for a in assets:
        nombre = (a.get("name") or "").lower()
        if nombre.endswith(".exe"):
            return a
    return None


class VerificadorActualizaciones(QObject):
    """Consulta GitHub Releases y notifica si hay una versión más nueva."""

    actualizacion_disponible = Signal(object)  # Actualizacion
    al_dia = Signal()
    error = Signal(str)
    finalizado = Signal()

    def __init__(
        self,
        url_latest: str = URL_LATEST,
        version_actual: str = __version__,
        cliente_http: httpx.Client | None = None,
    ) -> None:
        super().__init__()
        self._url = url_latest
        self._version_actual = version_actual
        self._http_inyectado = cliente_http

    def ejecutar(self) -> None:
        try:
            http = self._http_inyectado or httpx.Client(timeout=_TIEMPO_ESPERA)
            try:
                r = http.get(
                    self._url,
                    headers={"Accept": "application/vnd.github+json"},
                )
            finally:
                if self._http_inyectado is None:
                    http.close()
            r.raise_for_status()
            datos = r.json()
        except httpx.HTTPError as e:
            _log.info("No se pudo verificar actualizaciones: %s", e)
            self.error.emit("No se pudo verificar actualizaciones.")
            self.finalizado.emit()
            return

        tag = datos.get("tag_name", "")
        if not es_mas_nueva(tag, self._version_actual):
            _log.info(
                "App al día (local=%s, remota=%s)", self._version_actual, tag
            )
            self.al_dia.emit()
            self.finalizado.emit()
            return

        asset = _encontrar_asset_exe(datos.get("assets", []) or [])
        if asset is None:
            _log.info("Versión %s publicada sin instalador .exe", tag)
            self.al_dia.emit()
            self.finalizado.emit()
            return

        actualizacion = Actualizacion(
            version=tag.lstrip("vV"),
            url_descarga=asset["browser_download_url"],
            notas=datos.get("body") or "",
            nombre_archivo=asset["name"],
            url_pagina=datos.get("html_url") or "",
        )
        _log.info("Actualización %s disponible", actualizacion.version)
        self.actualizacion_disponible.emit(actualizacion)
        self.finalizado.emit()
