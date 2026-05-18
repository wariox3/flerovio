"""Diálogo «Acerca de Flerovio»."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from flerovio import __version__


class DialogoAcercaDe(QDialog):
    def __init__(self, padre: QWidget | None = None) -> None:
        super().__init__(padre)
        self.setWindowTitle("Acerca de Flerovio")

        disposicion = QVBoxLayout(self)

        titulo = QLabel(f"<b>Flerovio</b> {__version__}")
        titulo.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        disposicion.addWidget(titulo)

        descripcion = QLabel(
            "Reemplazo de cromo escritorio.\n"
            "Extensión para Semántica ERP — Transporte."
        )
        descripcion.setWordWrap(True)
        disposicion.addWidget(descripcion)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.reject)
        botones.accepted.connect(self.accept)
        disposicion.addWidget(botones)
