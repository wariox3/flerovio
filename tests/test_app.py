from PySide6.QtWidgets import QMenu

from flerovio import __version__
from flerovio.servicios.modelos import Sesion, Usuario
from flerovio.ui.ventana_principal import VentanaPrincipal


def _sesion_falsa(email: str = "a@b.com", tenant: str = "EMPRESA X") -> Sesion:
    return Sesion(
        token="t",
        tipo_token="bearer",
        usuario=Usuario(
            id=1,
            email=email,
            tenant_id=1,
            tenant_nombre=tenant,
            rol="admin",
            empleado_id=1,
        ),
    )


def test_titulo_ventana_principal(qtbot):
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)
    assert ventana.windowTitle() == "Flerovio"


def test_menu_tiene_archivo_y_ayuda(qtbot):
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)
    titulos = [m.title() for m in ventana.menuBar().findChildren(QMenu)]
    assert any("Archivo" in t for t in titulos)
    assert any("yuda" in t for t in titulos)


def test_acciones_principales_existen(qtbot):
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)
    assert ventana.accion_salir.text() == "&Salir"
    assert "Acerca de" in ventana.accion_acerca_de.text()
    assert "Cerrar sesión" in ventana.accion_cerrar_sesion.text()


def test_cerrar_sesion_emite_senal_al_confirmar(qtbot, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    ventana = VentanaPrincipal(sesion=_sesion_falsa())
    qtbot.addWidget(ventana)

    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes
    )

    with qtbot.waitSignal(ventana.cerrar_sesion_solicitado, timeout=1000):
        ventana.accion_cerrar_sesion.trigger()


def test_cerrar_sesion_no_emite_si_se_cancela(qtbot, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    ventana = VentanaPrincipal(sesion=_sesion_falsa())
    qtbot.addWidget(ventana)

    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.No
    )

    with qtbot.assertNotEmitted(ventana.cerrar_sesion_solicitado):
        ventana.accion_cerrar_sesion.trigger()


def test_actualizar_sesion_refresca_textos(qtbot):
    ventana = VentanaPrincipal(sesion=_sesion_falsa(email="vieja@b.com"))
    qtbot.addWidget(ventana)
    assert "vieja@b.com" in ventana.statusBar().currentMessage()

    ventana.actualizar_sesion(_sesion_falsa(email="nueva@b.com", tenant="OTRA"))
    assert "nueva@b.com" in ventana.statusBar().currentMessage()
    assert "OTRA" in ventana.statusBar().currentMessage()


def test_barra_estado_muestra_version(qtbot):
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)
    assert __version__ in ventana.statusBar().currentMessage()


def test_geometria_se_persiste_al_cerrar(qtbot):
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)
    ventana.resize(1024, 768)
    ventana.close()

    from flerovio.nucleo.configuracion import cargar_geometria_ventana

    geometria, _ = cargar_geometria_ventana()
    assert geometria is not None
