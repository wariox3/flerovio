import logging
import sys

from flerovio.nucleo import excepciones
from flerovio.nucleo.excepciones import instalar_manejador_global


def test_instalar_manejador_global_reemplaza_excepthook():
    original = sys.excepthook
    try:
        instalar_manejador_global()
        assert sys.excepthook is not original
    finally:
        sys.excepthook = original


def test_manejador_registra_excepcion(caplog, monkeypatch):
    # Evita que el manejador abra un QMessageBox modal real, que bloquearía en
    # entornos sin UI (Windows CI con offscreen, headless en general).
    monkeypatch.setattr(excepciones, "_mostrar_dialogo", lambda *a, **kw: None)

    original = sys.excepthook
    try:
        instalar_manejador_global()
        try:
            raise ValueError("fallo de prueba")
        except ValueError:
            tipo, valor, rastro = sys.exc_info()

        with caplog.at_level(logging.CRITICAL):
            sys.excepthook(tipo, valor, rastro)

        assert any("Excepción no capturada" in r.message for r in caplog.records)
    finally:
        sys.excepthook = original
