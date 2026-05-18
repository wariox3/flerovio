import httpx

from flerovio.servicios.actualizaciones import (
    VerificadorActualizaciones,
    es_mas_nueva,
)


def test_comparacion_de_versiones():
    assert es_mas_nueva("0.2.0", "0.1.0") is True
    assert es_mas_nueva("v0.2.0", "0.1.9") is True
    assert es_mas_nueva("0.1.0", "0.1.0") is False
    assert es_mas_nueva("0.0.9", "0.1.0") is False


def _verificador(handler, version_actual="0.1.0") -> VerificadorActualizaciones:
    transporte = httpx.MockTransport(handler)
    http = httpx.Client(transport=transporte)
    return VerificadorActualizaciones(
        url_latest="https://api.github.test/repos/x/y/releases/latest",
        version_actual=version_actual,
        cliente_http=http,
    )


def _respuesta_release(tag: str, con_exe: bool = True, notas: str = "cambios"):
    assets = []
    if con_exe:
        assets.append(
            {
                "name": f"flerovio-{tag.lstrip('v')}-setup.exe",
                "browser_download_url": f"https://example.test/{tag}/setup.exe",
            }
        )
    return {"tag_name": tag, "body": notas, "assets": assets}


def test_emite_actualizacion_si_hay_version_nueva(qtbot):
    def handler(_req):
        return httpx.Response(200, json=_respuesta_release("v0.2.0"))

    v = _verificador(handler, version_actual="0.1.0")
    with qtbot.waitSignal(v.actualizacion_disponible, timeout=2000) as bloqueador:
        v.ejecutar()
    actualizacion = bloqueador.args[0]
    assert actualizacion.version == "0.2.0"
    assert actualizacion.url_descarga.endswith("setup.exe")
    assert actualizacion.nombre_archivo == "flerovio-0.2.0-setup.exe"


def test_al_dia_si_misma_version(qtbot):
    def handler(_req):
        return httpx.Response(200, json=_respuesta_release("v0.1.0"))

    v = _verificador(handler, version_actual="0.1.0")
    with qtbot.waitSignal(v.al_dia, timeout=2000):
        v.ejecutar()


def test_al_dia_si_release_sin_exe(qtbot):
    def handler(_req):
        return httpx.Response(200, json=_respuesta_release("v0.2.0", con_exe=False))

    v = _verificador(handler, version_actual="0.1.0")
    with qtbot.waitSignal(v.al_dia, timeout=2000):
        v.ejecutar()


def test_error_de_red_emite_error(qtbot):
    def handler(_req):
        raise httpx.ConnectError("offline")

    v = _verificador(handler)
    with qtbot.waitSignal(v.error, timeout=2000):
        v.ejecutar()


def test_404_emite_error(qtbot):
    def handler(_req):
        return httpx.Response(404)

    v = _verificador(handler)
    with qtbot.waitSignal(v.error, timeout=2000):
        v.ejecutar()


def test_finalizado_siempre_se_emite(qtbot):
    def handler(_req):
        return httpx.Response(200, json=_respuesta_release("v0.2.0"))

    v = _verificador(handler, version_actual="0.1.0")
    with qtbot.waitSignal(v.finalizado, timeout=2000):
        v.ejecutar()
