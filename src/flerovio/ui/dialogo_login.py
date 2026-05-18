"""Diálogo modal de inicio de sesión."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from flerovio import __version__
from flerovio.servicios.cliente_api import ClienteAPI
from flerovio.servicios.modelos import ErrorAPI, Sesion

_log = logging.getLogger(__name__)


class _TrabajadorLogin(QObject):
    """Ejecuta la llamada de login en un hilo aparte."""

    exito = Signal(object)  # Sesion
    error = Signal(str)

    def __init__(self, cliente: ClienteAPI, email: str, contrasena: str) -> None:
        super().__init__()
        self._cliente = cliente
        self._email = email
        self._contrasena = contrasena

    def ejecutar(self) -> None:
        try:
            sesion = self._cliente.autenticar(self._email, self._contrasena)
        except ErrorAPI as e:
            self.error.emit(e.mensaje)
        except Exception as e:  # noqa: BLE001 — protección defensiva del hilo
            _log.exception("Error inesperado en login")
            self.error.emit(f"Error inesperado: {e}")
        else:
            self.exito.emit(sesion)


class DialogoLogin(QDialog):
    def __init__(
        self,
        cliente: ClienteAPI,
        padre: QWidget | None = None,
        email_inicial: str = "",
        recordarme_inicial: bool = False,
    ) -> None:
        super().__init__(padre)
        self._cliente = cliente
        self._sesion: Sesion | None = None
        self._hilo: QThread | None = None
        self._trabajador: _TrabajadorLogin | None = None

        self.setWindowTitle("Iniciar sesión — Flerovio")
        self.setModal(True)
        self.setMinimumWidth(420)

        self._construir_ui(email_inicial, recordarme_inicial)

    @property
    def sesion(self) -> Sesion | None:
        return self._sesion

    @property
    def recordarme(self) -> bool:
        return self.casilla_recordarme.isChecked()

    def _construir_ui(self, email_inicial: str, recordarme_inicial: bool) -> None:
        disposicion = QVBoxLayout(self)

        formulario = QFormLayout()
        self.campo_email = QLineEdit(email_inicial)
        self.campo_email.setPlaceholderText("correo@empresa.com")
        formulario.addRow("Correo:", self.campo_email)

        self.campo_contrasena = QLineEdit()
        self.campo_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        formulario.addRow("Contraseña:", self.campo_contrasena)
        disposicion.addLayout(formulario)

        self.casilla_recordarme = QCheckBox("Recordarme en este equipo")
        self.casilla_recordarme.setChecked(recordarme_inicial)
        disposicion.addWidget(self.casilla_recordarme)

        self.etiqueta_estado = QLabel("")
        self.etiqueta_estado.setWordWrap(True)
        self.etiqueta_estado.setStyleSheet("color: #b00020;")
        disposicion.addWidget(self.etiqueta_estado)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setText("Ingresar")
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.botones.accepted.connect(self._enviar)
        self.botones.rejected.connect(self.reject)
        disposicion.addWidget(self.botones)

        self.etiqueta_version = QLabel(f"Versión {__version__}")
        self.etiqueta_version.setStyleSheet("color: #888; font-size: 11px;")
        self.etiqueta_version.setAlignment(Qt.AlignmentFlag.AlignRight)
        disposicion.addWidget(self.etiqueta_version)

        self.campo_email.returnPressed.connect(self._enviar)
        self.campo_contrasena.returnPressed.connect(self._enviar)

        # Si ya hay email pre-cargado, posicionar foco en contraseña.
        if email_inicial:
            self.campo_contrasena.setFocus()

    def _enviar(self) -> None:
        email = self.campo_email.text().strip()
        contrasena = self.campo_contrasena.text()

        if not email or not contrasena:
            self.etiqueta_estado.setText("Ingresa correo y contraseña.")
            return

        self._poner_estado_cargando(True)
        self.etiqueta_estado.setText("Autenticando…")
        self.etiqueta_estado.setStyleSheet("color: #555;")

        self._hilo = QThread(self)
        self._trabajador = _TrabajadorLogin(self._cliente, email, contrasena)
        self._trabajador.moveToThread(self._hilo)
        self._hilo.started.connect(self._trabajador.ejecutar)
        self._trabajador.exito.connect(self._on_exito)
        self._trabajador.error.connect(self._on_error)
        self._trabajador.exito.connect(self._hilo.quit)
        self._trabajador.error.connect(self._hilo.quit)
        self._hilo.finished.connect(self._limpiar_hilo)
        self._hilo.start()

    def _on_exito(self, sesion: Sesion) -> None:
        self._sesion = sesion
        _log.info("Sesión iniciada para %s", sesion.usuario.email)
        self.accept()

    def _on_error(self, mensaje: str) -> None:
        self.etiqueta_estado.setStyleSheet("color: #b00020;")
        self.etiqueta_estado.setText(mensaje)
        self._poner_estado_cargando(False)

    def _poner_estado_cargando(self, cargando: bool) -> None:
        self.campo_email.setEnabled(not cargando)
        self.campo_contrasena.setEnabled(not cargando)
        self.casilla_recordarme.setEnabled(not cargando)
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setEnabled(not cargando)
        cursor = Qt.CursorShape.WaitCursor if cargando else Qt.CursorShape.ArrowCursor
        self.setCursor(cursor)

    def done(self, resultado: int) -> None:
        """Garantiza que el hilo de login termine antes de cerrar el diálogo."""
        self._terminar_hilo_si_corre()
        super().done(resultado)

    def closeEvent(self, evento: QCloseEvent) -> None:
        self._terminar_hilo_si_corre()
        super().closeEvent(evento)

    def _terminar_hilo_si_corre(self) -> None:
        if self._hilo is not None and self._hilo.isRunning():
            self._hilo.quit()
            self._hilo.wait(2000)

    def _limpiar_hilo(self) -> None:
        if self._trabajador is not None:
            self._trabajador.deleteLater()
            self._trabajador = None
        if self._hilo is not None:
            self._hilo.deleteLater()
            self._hilo = None
