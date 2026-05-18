"""Cliente HTTP contra la API de Semántica."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from PySide6.QtCore import QObject, Signal

from flerovio.servicios.modelos import ErrorAPI, Sesion, Usuario

_log = logging.getLogger(__name__)

URL_BASE_POR_DEFECTO = "https://api.semanticaapi.com.co"
_TIEMPO_ESPERA = 15.0  # segundos
_TIEMPO_ESPERA_LOGOUT = 5.0


class ClienteAPI(QObject):
    """Cliente HTTP autenticado contra la API de Semántica.

    Emite ``sesion_invalidada`` cuando una llamada autenticada recibe 401
    (token expirado o revocado), para que la UI vuelva al diálogo de login.
    """

    sesion_invalidada = Signal()

    def __init__(
        self,
        url_base: str = URL_BASE_POR_DEFECTO,
        cliente_http: httpx.Client | None = None,
    ) -> None:
        super().__init__()
        self._url_base = url_base.rstrip("/")
        self._http = cliente_http or httpx.Client(
            base_url=self._url_base, timeout=_TIEMPO_ESPERA
        )
        self._propio = cliente_http is None
        self._sesion: Sesion | None = None

    @property
    def sesion(self) -> Sesion | None:
        return self._sesion

    def cerrar(self) -> None:
        if self._propio:
            self._http.close()

    def __enter__(self) -> ClienteAPI:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.cerrar()

    def autenticar(self, email: str, contrasena: str) -> Sesion:
        """Inicia sesión, guarda el token y lo aplica a llamadas posteriores."""
        datos = self._pedir(
            "POST",
            "/auth/seguridad/login",
            json={
                "email": email,
                "password": contrasena,
                "client_type": "api",
            },
        )
        sesion = Sesion(
            token=datos["access_token"],
            tipo_token=datos.get("token_type", "bearer"),
            usuario=Usuario.desde_json(datos["user"]),
        )
        self._adoptar_sesion(sesion)
        _log.info("Autenticación exitosa para %s", sesion.usuario.email)
        return sesion

    def obtener_perfil(self) -> Usuario:
        """Devuelve el usuario asociado al token actual (GET /me)."""
        datos = self._pedir("GET", "/auth/seguridad/me")
        return Usuario.desde_json(datos)

    def restaurar_desde_token(self, token: str, tipo: str = "bearer") -> Sesion:
        """Aplica un token guardado, lo valida con /me y adopta la sesión.

        Lanza ErrorAPI si el token ya no es válido.
        """
        self._http.headers["Authorization"] = f"{tipo.capitalize()} {token}"
        try:
            usuario = self.obtener_perfil()
        except ErrorAPI:
            self._http.headers.pop("Authorization", None)
            raise
        sesion = Sesion(token=token, tipo_token=tipo, usuario=usuario)
        self._sesion = sesion
        _log.info("Sesión restaurada para %s", usuario.email)
        return sesion

    def cerrar_sesion(self) -> None:
        """Cierra la sesión: notifica al servidor y limpia el estado local."""
        if self._sesion is None:
            return
        usuario = self._sesion.usuario
        self._sesion = None
        try:
            self._http.post(
                "/auth/seguridad/logout", timeout=_TIEMPO_ESPERA_LOGOUT
            )
        except httpx.HTTPError as e:
            _log.warning("Fallo al cerrar sesión en el servidor: %s", e)
        self._http.headers.pop("Authorization", None)
        _log.info("Sesión cerrada para %s", usuario.email)

    def obtener(self, ruta: str, **kwargs: Any) -> Any:
        """Realiza un GET autenticado y devuelve el cuerpo JSON."""
        return self._pedir("GET", ruta, **kwargs)

    def _adoptar_sesion(self, sesion: Sesion) -> None:
        self._sesion = sesion
        tipo = (sesion.tipo_token or "bearer").capitalize()
        self._http.headers["Authorization"] = f"{tipo} {sesion.token}"

    def _pedir(self, metodo: str, ruta: str, **kwargs: Any) -> Any:
        try:
            respuesta = self._http.request(metodo, ruta, **kwargs)
        except httpx.HTTPError as e:
            _log.warning("Fallo de red en %s %s: %s", metodo, ruta, e)
            raise ErrorAPI(
                "No se pudo conectar con el servidor.", codigo="RED"
            ) from e

        if respuesta.status_code >= 400:
            self._lanzar_error(respuesta)

        if not respuesta.content:
            return None
        return respuesta.json()

    def _lanzar_error(self, respuesta: httpx.Response) -> None:
        codigo = "HTTP"
        mensaje = f"Error del servidor ({respuesta.status_code})."
        try:
            cuerpo = respuesta.json()
            error = cuerpo.get("error") or {}
            codigo = error.get("code") or codigo
            mensaje = error.get("message") or mensaje
        except ValueError:
            pass
        _log.info("Solicitud rechazada: %s — %s", codigo, mensaje)

        if respuesta.status_code == 401 and self._sesion is not None:
            # Token expirado o revocado durante el uso normal de la app.
            _log.info("Sesión invalidada por el servidor")
            self._sesion = None
            self._http.headers.pop("Authorization", None)
            self.sesion_invalidada.emit()

        raise ErrorAPI(mensaje, codigo=codigo)
