import httpx
import pytest

from flerovio.servicios.cliente_api import ClienteAPI
from flerovio.servicios.modelos import ErrorAPI


def _cliente_con_transporte(handler) -> ClienteAPI:
    transporte = httpx.MockTransport(handler)
    http = httpx.Client(base_url="https://api.test", transport=transporte)
    return ClienteAPI(url_base="https://api.test", cliente_http=http)


def test_autenticar_exito():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/auth/seguridad/login"
        cuerpo = request.read().decode()
        assert "client_type" in cuerpo
        return httpx.Response(
            200,
            json={
                "access_token": "token-xyz",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "email": "alguien@test.com",
                    "tenant_id": 7,
                    "tenant_nombre": "EMPRESA",
                    "role": "admin",
                    "empleado_id": 42,
                },
            },
        )

    with _cliente_con_transporte(handler) as cliente:
        sesion = cliente.autenticar("alguien@test.com", "secreto")

    assert sesion.token == "token-xyz"
    assert sesion.usuario.email == "alguien@test.com"
    assert sesion.usuario.tenant_nombre == "EMPRESA"
    assert sesion.usuario.empleado_id == 42


def test_autenticar_credenciales_invalidas():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "success": False,
                "error": {"code": "UNAUTHORIZED", "message": "Credenciales inválidas"},
            },
        )

    with _cliente_con_transporte(handler) as cliente, pytest.raises(ErrorAPI) as exc:
        cliente.autenticar("a@b.com", "x")

    assert exc.value.codigo == "UNAUTHORIZED"
    assert "Credenciales" in exc.value.mensaje


def test_autenticar_error_de_red():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no se pudo conectar")

    with _cliente_con_transporte(handler) as cliente, pytest.raises(ErrorAPI) as exc:
        cliente.autenticar("a@b.com", "x")

    assert exc.value.codigo == "RED"


def _respuesta_login_ok() -> dict:
    return {
        "access_token": "token-xyz",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": "a@b.com",
            "tenant_id": 7,
            "tenant_nombre": "EMPRESA",
            "role": "admin",
            "empleado_id": 42,
        },
    }


def test_autenticar_aplica_header_a_llamadas_siguientes():
    autorizaciones: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        autorizaciones.append(request.headers.get("authorization"))
        if request.url.path == "/auth/seguridad/login":
            return httpx.Response(200, json=_respuesta_login_ok())
        return httpx.Response(200, json={"ok": True})

    with _cliente_con_transporte(handler) as cliente:
        cliente.autenticar("a@b.com", "x")
        cliente.obtener("/algun/recurso")

    assert autorizaciones[0] is None  # login no lleva header
    assert autorizaciones[1] == "Bearer token-xyz"


def test_cerrar_sesion_quita_header_y_llama_logout():
    rutas_visitadas: list[str] = []
    autorizaciones_no_logout: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        rutas_visitadas.append(request.url.path)
        if request.url.path == "/auth/seguridad/login":
            return httpx.Response(200, json=_respuesta_login_ok())
        if request.url.path == "/auth/seguridad/logout":
            return httpx.Response(200, json={"message": "Sesión cerrada"})
        autorizaciones_no_logout.append(request.headers.get("authorization"))
        return httpx.Response(200, json={"ok": True})

    with _cliente_con_transporte(handler) as cliente:
        cliente.autenticar("a@b.com", "x")
        assert cliente.sesion is not None
        cliente.cerrar_sesion()
        assert cliente.sesion is None
        cliente.obtener("/algun/recurso")

    assert "/auth/seguridad/logout" in rutas_visitadas
    assert autorizaciones_no_logout == [None]


def test_cerrar_sesion_es_resiliente_a_fallo_de_red():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/seguridad/login":
            return httpx.Response(200, json=_respuesta_login_ok())
        raise httpx.ConnectError("offline")

    with _cliente_con_transporte(handler) as cliente:
        cliente.autenticar("a@b.com", "x")
        cliente.cerrar_sesion()  # no debe lanzar
        assert cliente.sesion is None


def test_obtener_propaga_error_api():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"error": {"code": "NOT_FOUND", "message": "Recurso no existe"}},
        )

    with _cliente_con_transporte(handler) as cliente, pytest.raises(ErrorAPI) as exc:
        cliente.obtener("/algo")

    assert exc.value.codigo == "NOT_FOUND"


def test_obtener_perfil():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/auth/seguridad/me"
        return httpx.Response(
            200,
            json={
                "id": 1,
                "email": "a@b.com",
                "tenant_id": 7,
                "tenant_nombre": "EMPRESA",
                "role": "admin",
                "empleado_id": 42,
            },
        )

    with _cliente_con_transporte(handler) as cliente:
        usuario = cliente.obtener_perfil()

    assert usuario.email == "a@b.com"
    assert usuario.tenant_nombre == "EMPRESA"


def test_restaurar_desde_token_valido():
    autorizaciones: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        autorizaciones.append(request.headers.get("authorization"))
        return httpx.Response(
            200,
            json={
                "id": 1,
                "email": "a@b.com",
                "tenant_id": 7,
                "tenant_nombre": "EMPRESA",
                "role": "admin",
                "empleado_id": 42,
            },
        )

    with _cliente_con_transporte(handler) as cliente:
        sesion = cliente.restaurar_desde_token("guardado-abc")

    assert sesion.token == "guardado-abc"
    assert sesion.usuario.email == "a@b.com"
    assert autorizaciones == ["Bearer guardado-abc"]


def test_restaurar_desde_token_invalido_limpia_header():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "UNAUTHORIZED", "message": "Token inválido"}},
        )

    with _cliente_con_transporte(handler) as cliente:
        with pytest.raises(ErrorAPI):
            cliente.restaurar_desde_token("malo")
        assert cliente._http.headers.get("Authorization") is None


def test_401_en_operacion_emite_sesion_invalidada(qtbot):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/seguridad/login":
            return httpx.Response(200, json=_respuesta_login_ok())
        return httpx.Response(
            401,
            json={"error": {"code": "UNAUTHORIZED", "message": "Token expirado"}},
        )

    with _cliente_con_transporte(handler) as cliente:
        cliente.autenticar("a@b.com", "x")
        with (
            qtbot.waitSignal(cliente.sesion_invalidada, timeout=1000),
            pytest.raises(ErrorAPI),
        ):
            cliente.obtener("/algo")
        assert cliente.sesion is None


def test_401_en_login_no_emite_sesion_invalidada(qtbot):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": "UNAUTHORIZED", "message": "Credenciales inválidas"}},
        )

    with (
        _cliente_con_transporte(handler) as cliente,
        qtbot.assertNotEmitted(cliente.sesion_invalidada),
        pytest.raises(ErrorAPI),
    ):
        cliente.autenticar("a@b.com", "x")
