import pytest
from PySide6.QtCore import QCoreApplication, QSettings


@pytest.fixture(autouse=True)
def ajustes_aislados(tmp_path, monkeypatch):
    """Aísla QSettings por test usando un archivo .ini temporal.

    Sin esto, los tests escribirían en la configuración real del usuario.
    """
    QCoreApplication.setOrganizationName("FlerovioTest")
    QCoreApplication.setApplicationName("FlerovioTest")
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path),
    )
    yield
