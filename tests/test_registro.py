import logging

from flerovio.nucleo.registro import configurar_registro


def test_configurar_registro_crea_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "flerovio.nucleo.registro.directorio_registros", lambda: tmp_path
    )

    archivo = configurar_registro(nivel=logging.DEBUG)
    logging.getLogger("prueba").info("hola")

    for h in logging.getLogger().handlers:
        h.flush()

    assert archivo.exists()
    assert archivo.parent == tmp_path
    assert "hola" in archivo.read_text(encoding="utf-8")


def test_configurar_registro_es_idempotente(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "flerovio.nucleo.registro.directorio_registros", lambda: tmp_path
    )

    configurar_registro()
    cantidad = len(logging.getLogger().handlers)
    configurar_registro()
    assert len(logging.getLogger().handlers) == cantidad
