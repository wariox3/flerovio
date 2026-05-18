from PySide6.QtCore import QByteArray

from flerovio.nucleo.configuracion import (
    cargar_geometria_ventana,
    cargar_recordarme,
    cargar_ultimo_email,
    guardar_geometria_ventana,
    guardar_recordarme,
    guardar_ultimo_email,
)


def test_geometria_sin_guardar_devuelve_none():
    geometria, estado = cargar_geometria_ventana()
    assert geometria is None
    assert estado is None


def test_geometria_se_guarda_y_se_recupera():
    geometria = QByteArray(b"datos-geometria")
    estado = QByteArray(b"datos-estado")

    guardar_geometria_ventana(geometria, estado)
    geometria_leida, estado_leido = cargar_geometria_ventana()

    assert bytes(geometria_leida) == b"datos-geometria"
    assert bytes(estado_leido) == b"datos-estado"


def test_ultimo_email_sin_guardar_es_none():
    assert cargar_ultimo_email() is None


def test_ultimo_email_se_guarda_y_se_recupera():
    guardar_ultimo_email("a@b.com")
    assert cargar_ultimo_email() == "a@b.com"


def test_recordarme_por_defecto_es_false():
    assert cargar_recordarme() is False


def test_recordarme_se_guarda_y_se_recupera():
    guardar_recordarme(True)
    assert cargar_recordarme() is True
    guardar_recordarme(False)
    assert cargar_recordarme() is False
