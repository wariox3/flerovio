import logging

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from flerovio import __version__
from flerovio.nucleo.configuracion import (
    cargar_geometria_ventana,
    guardar_geometria_ventana,
)
from flerovio.servicios.modelos import Sesion
from flerovio.ui.dialogo_acerca_de import DialogoAcercaDe

_log = logging.getLogger(__name__)


class VentanaPrincipal(QMainWindow):
    cerrar_sesion_solicitado = Signal()

    def __init__(self, sesion: Sesion | None = None) -> None:
        super().__init__()
        self._sesion = sesion
        self.setWindowTitle("Flerovio")
        self.resize(800, 600)

        self._etiqueta_bienvenida: QLabel | None = None
        self._construir_central()
        self._construir_menu()
        self._construir_barra_estado()
        self._restaurar_geometria()
        self._refrescar_textos_sesion()

        _log.info("Ventana principal inicializada")

    def actualizar_sesion(self, sesion: Sesion) -> None:
        """Reemplaza la sesión activa y refresca los textos visibles."""
        self._sesion = sesion
        self._refrescar_textos_sesion()
        _log.info("Sesión activa actualizada para %s", sesion.usuario.email)

    def _construir_central(self) -> None:
        central = QWidget(self)
        disposicion = QVBoxLayout(central)
        self._etiqueta_bienvenida = QLabel("")
        disposicion.addWidget(self._etiqueta_bienvenida)
        self.setCentralWidget(central)

    def _construir_menu(self) -> None:
        barra = self.menuBar()

        menu_archivo = barra.addMenu("&Archivo")

        self.accion_cerrar_sesion = QAction("&Cerrar sesión", self)
        self.accion_cerrar_sesion.setStatusTip("Cerrar la sesión actual")
        self.accion_cerrar_sesion.triggered.connect(self._pedir_cerrar_sesion)
        menu_archivo.addAction(self.accion_cerrar_sesion)

        menu_archivo.addSeparator()

        self.accion_salir = QAction("&Salir", self)
        self.accion_salir.setShortcut(QKeySequence.StandardKey.Quit)
        self.accion_salir.setStatusTip("Cerrar la aplicación")
        self.accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(self.accion_salir)

        menu_ayuda = barra.addMenu("A&yuda")
        self.accion_acerca_de = QAction("&Acerca de Flerovio…", self)
        self.accion_acerca_de.setStatusTip("Información sobre la aplicación")
        self.accion_acerca_de.triggered.connect(self._mostrar_acerca_de)
        menu_ayuda.addAction(self.accion_acerca_de)

    def _construir_barra_estado(self) -> None:
        self.statusBar().showMessage(f"Flerovio {__version__}")

    def _refrescar_textos_sesion(self) -> None:
        if self._etiqueta_bienvenida is not None:
            if self._sesion is not None:
                texto = (
                    f"Bienvenido, {self._sesion.usuario.email} "
                    f"({self._sesion.usuario.tenant_nombre})"
                )
            else:
                texto = "Flerovio — extensión para Semántica ERP - Transporte"
            self._etiqueta_bienvenida.setText(texto)

        partes = [f"Flerovio {__version__}"]
        if self._sesion is not None:
            partes.append(self._sesion.usuario.email)
            partes.append(self._sesion.usuario.tenant_nombre)
        self.statusBar().showMessage("  —  ".join(partes))

    def _pedir_cerrar_sesion(self) -> None:
        respuesta = QMessageBox.question(
            self,
            "Cerrar sesión",
            "¿Deseas cerrar la sesión actual?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            _log.info("Cierre de sesión solicitado")
            self.cerrar_sesion_solicitado.emit()

    def _mostrar_acerca_de(self) -> None:
        DialogoAcercaDe(self).exec()

    def _restaurar_geometria(self) -> None:
        geometria, estado = cargar_geometria_ventana()
        if geometria is not None:
            self.restoreGeometry(geometria)
        if estado is not None:
            self.restoreState(estado)

    def closeEvent(self, event: QCloseEvent) -> None:
        guardar_geometria_ventana(self.saveGeometry(), self.saveState())
        _log.info("Cerrando ventana principal")
        super().closeEvent(event)
