import httpx
from PySide6.QtWidgets import QDialogButtonBox

from flerovio.servicios.cliente_api import ClienteAPI
from flerovio.ui.dialogo_login import DialogoLogin


def _cliente(handler) -> ClienteAPI:
    transporte = httpx.MockTransport(handler)
    http = httpx.Client(base_url="https://api.test", transport=transporte)
    return ClienteAPI(url_base="https://api.test", cliente_http=http)


def test_dialogo_login_valida_campos_vacios(qtbot):
    dialogo = DialogoLogin(_cliente(lambda r: httpx.Response(200)))
    qtbot.addWidget(dialogo)

    dialogo._enviar()
    assert "correo y contraseña" in dialogo.etiqueta_estado.text().lower()


def test_dialogo_login_exito(qtbot):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "access_token": "t",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "email": "a@b.com",
                    "tenant_id": 1,
                    "tenant_nombre": "X",
                    "role": "admin",
                    "empleado_id": 1,
                },
            },
        )

    dialogo = DialogoLogin(_cliente(handler))
    qtbot.addWidget(dialogo)
    dialogo.campo_email.setText("a@b.com")
    dialogo.campo_contrasena.setText("secreto")

    with qtbot.waitSignal(dialogo.accepted, timeout=3000):
        dialogo.botones.button(QDialogButtonBox.StandardButton.Ok).click()

    assert dialogo.sesion is not None
    assert dialogo.sesion.usuario.email == "a@b.com"


def test_dialogo_login_credenciales_invalidas(qtbot):
    def handler(request):
        return httpx.Response(
            401,
            json={"error": {"code": "UNAUTHORIZED", "message": "Credenciales inválidas"}},
        )

    dialogo = DialogoLogin(_cliente(handler))
    qtbot.addWidget(dialogo)
    dialogo.campo_email.setText("a@b.com")
    dialogo.campo_contrasena.setText("malo")

    dialogo.botones.button(QDialogButtonBox.StandardButton.Ok).click()
    qtbot.waitUntil(
        lambda: "Credenciales" in dialogo.etiqueta_estado.text(),
        timeout=3000,
    )

    assert dialogo.sesion is None
    assert dialogo.campo_email.isEnabled()  # se rehabilita tras el error
