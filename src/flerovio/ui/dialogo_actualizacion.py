"""Diálogo que ofrece descargar e instalar una actualización."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx
from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from flerovio.servicios.actualizaciones import Actualizacion

_log = logging.getLogger(__name__)

_TIEMPO_ESPERA_DESCARGA = 120.0
_TAMANO_BLOQUE = 64 * 1024


class _Descargador(QObject):
    """Descarga el instalador en streaming a un archivo temporal."""

    progreso = Signal(int, int)  # descargados, total (0 si desconocido)
    completado = Signal(str)  # ruta del archivo descargado
    error = Signal(str)

    def __init__(self, url: str, nombre_archivo: str) -> None:
        super().__init__()
        self._url = url
        self._nombre = nombre_archivo

    def ejecutar(self) -> None:
        ruta = Path(tempfile.gettempdir()) / self._nombre
        try:
            with httpx.stream(
                "GET",
                self._url,
                follow_redirects=True,
                timeout=_TIEMPO_ESPERA_DESCARGA,
            ) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", "0") or 0)
                descargado = 0
                with open(ruta, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=_TAMANO_BLOQUE):
                        f.write(chunk)
                        descargado += len(chunk)
                        self.progreso.emit(descargado, total)
        except httpx.HTTPError as e:
            _log.warning("Fallo descargando actualización: %s", e)
            self.error.emit("No se pudo descargar la actualización.")
            return
        except OSError as e:
            _log.warning("Fallo escribiendo el instalador: %s", e)
            self.error.emit("No se pudo guardar el instalador en disco.")
            return

        self.completado.emit(str(ruta))


class DialogoActualizacion(QDialog):
    instalacion_lanzada = Signal()

    def __init__(
        self,
        actualizacion: Actualizacion,
        padre: QWidget | None = None,
    ) -> None:
        super().__init__(padre)
        self._actualizacion = actualizacion
        self._hilo: QThread | None = None
        self._descargador: _Descargador | None = None

        self.setWindowTitle("Actualización disponible")
        self.setMinimumWidth(460)
        self._construir_ui()

    def _construir_ui(self) -> None:
        disposicion = QVBoxLayout(self)

        titulo = QLabel(
            f"<b>Nueva versión disponible: {self._actualizacion.version}</b>"
        )
        disposicion.addWidget(titulo)

        if self._actualizacion.notas.strip():
            disposicion.addWidget(QLabel("Cambios:"))
            self.notas = QTextEdit(self._actualizacion.notas)
            self.notas.setReadOnly(True)
            self.notas.setMaximumHeight(200)
            disposicion.addWidget(self.notas)

        self.barra = QProgressBar()
        self.barra.setVisible(False)
        disposicion.addWidget(self.barra)

        self.etiqueta_estado = QLabel("")
        self.etiqueta_estado.setWordWrap(True)
        disposicion.addWidget(self.etiqueta_estado)

        self.botones = QDialogButtonBox()
        self.btn_instalar = self.botones.addButton(
            "Instalar ahora", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.btn_mas_tarde = self.botones.addButton(
            "Más tarde", QDialogButtonBox.ButtonRole.RejectRole
        )
        self.btn_instalar.clicked.connect(self._iniciar_descarga)
        self.btn_mas_tarde.clicked.connect(self.reject)
        disposicion.addWidget(self.botones)

    def _iniciar_descarga(self) -> None:
        self.btn_instalar.setEnabled(False)
        self.btn_mas_tarde.setEnabled(False)
        self.barra.setVisible(True)
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.etiqueta_estado.setText("Descargando…")

        self._hilo = QThread(self)
        self._descargador = _Descargador(
            self._actualizacion.url_descarga,
            self._actualizacion.nombre_archivo,
        )
        self._descargador.moveToThread(self._hilo)
        self._hilo.started.connect(self._descargador.ejecutar)
        self._descargador.progreso.connect(self._on_progreso)
        self._descargador.completado.connect(self._on_completado)
        self._descargador.error.connect(self._on_error)
        self._descargador.completado.connect(self._hilo.quit)
        self._descargador.error.connect(self._hilo.quit)
        self._hilo.finished.connect(self._limpiar_hilo)
        self._hilo.start()

    def _on_progreso(self, descargado: int, total: int) -> None:
        if total > 0:
            self.barra.setValue(int(descargado / total * 100))
        else:
            self.barra.setRange(0, 0)

    def _on_completado(self, ruta: str) -> None:
        ruta_path = Path(ruta)
        if not ruta_path.exists():
            _log.error("El instalador descargado no existe en %s", ruta)
            self._on_error(f"El archivo descargado no se encuentra: {ruta}")
            return
        tamano = ruta_path.stat().st_size
        _log.info("Instalador descargado: %s (%.1f MB)", ruta, tamano / 1024 / 1024)
        if tamano < 1024 * 1024:  # < 1 MB es sospechoso
            _log.error("El instalador parece truncado: %d bytes", tamano)
            self._on_error(
                f"La descarga parece estar incompleta ({tamano} bytes).\n"
                "Intenta de nuevo."
            )
            return

        self.etiqueta_estado.setText("Lanzando instalador…")
        try:
            self._lanzar_instalador(ruta)
            _log.info("Instalador lanzado correctamente")
        except OSError as e:
            _log.exception("Fallo al lanzar instalador")
            self._on_error(
                f"No se pudo lanzar el instalador automáticamente.\n"
                f"Puedes ejecutarlo manualmente desde:\n{ruta}\n\nDetalle: {e}"
            )
            return

        self.etiqueta_estado.setText(
            "El instalador se está iniciando. Si Windows pide permisos, "
            "acéptalos. Flerovio se cerrará en unos segundos."
        )
        # Pausa para que Windows muestre el UAC y el instalador tome el foco
        # antes de cerrar Flerovio. Sin esta pausa el UAC se "pierde".
        QTimer.singleShot(2500, self._finalizar)

    def _finalizar(self) -> None:
        self.instalacion_lanzada.emit()
        self.accept()

    def _on_error(self, mensaje: str) -> None:
        self.etiqueta_estado.setText(mensaje)
        self.btn_instalar.setEnabled(True)
        self.btn_mas_tarde.setEnabled(True)
        self.barra.setVisible(False)

    def done(self, resultado: int) -> None:
        """Garantiza que el hilo de descarga termine antes de cerrar el diálogo."""
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
        if self._descargador is not None:
            self._descargador.deleteLater()
            self._descargador = None
        if self._hilo is not None:
            self._hilo.deleteLater()
            self._hilo = None

    @staticmethod
    def _lanzar_instalador(ruta: str) -> None:
        if sys.platform.startswith("win"):
            # startfile lanza con la asociación del sistema y desliga el proceso.
            os.startfile(ruta)  # type: ignore[attr-defined]
        else:
            # En Linux/macOS solo es útil para desarrollo manual.
            subprocess.Popen([ruta], close_fds=True)
