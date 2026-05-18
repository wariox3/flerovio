import logging
import sys

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication, QDialog, QWidget

from flerovio import __version__
from flerovio.nucleo import configuracion, credenciales
from flerovio.nucleo.excepciones import instalar_manejador_global
from flerovio.nucleo.registro import configurar_registro
from flerovio.servicios.actualizaciones import (
    Actualizacion,
    VerificadorActualizaciones,
)
from flerovio.servicios.cliente_api import ClienteAPI
from flerovio.servicios.modelos import ErrorAPI, Sesion
from flerovio.ui.dialogo_actualizacion import DialogoActualizacion
from flerovio.ui.dialogo_login import DialogoLogin
from flerovio.ui.ventana_principal import VentanaPrincipal


def _intentar_auto_login(cliente: ClienteAPI) -> Sesion | None:
    """Intenta restaurar sesión con un token guardado validándolo en /me."""
    if not configuracion.cargar_recordarme():
        return None
    email = configuracion.cargar_ultimo_email()
    if not email:
        return None
    token = credenciales.leer_token(email)
    if not token:
        return None

    _log = logging.getLogger(__name__)
    _log.info("Intentando auto-login para %s", email)
    try:
        return cliente.restaurar_desde_token(token)
    except ErrorAPI as e:
        _log.info("Token guardado no válido (%s); se requiere login", e.codigo)
        credenciales.eliminar_token(email)
        return None


def _solicitar_sesion(
    cliente: ClienteAPI, padre: QWidget | None = None
) -> tuple[Sesion, bool] | None:
    """Muestra el diálogo de login y devuelve (sesion, recordarme) o None."""
    dialogo = DialogoLogin(
        cliente,
        padre=padre,
        email_inicial=configuracion.cargar_ultimo_email() or "",
        recordarme_inicial=configuracion.cargar_recordarme(),
    )
    if dialogo.exec() != QDialog.DialogCode.Accepted or dialogo.sesion is None:
        return None
    return dialogo.sesion, dialogo.recordarme


def _persistir_eleccion(sesion: Sesion, recordarme: bool) -> None:
    """Guarda el email/token según la elección de 'Recordarme'."""
    configuracion.guardar_ultimo_email(sesion.usuario.email)
    configuracion.guardar_recordarme(recordarme)
    if recordarme:
        credenciales.guardar_token(sesion.usuario.email, sesion.token)
    else:
        credenciales.eliminar_token(sesion.usuario.email)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Flerovio")
    app.setOrganizationName("Semántica")
    app.setApplicationVersion(__version__)

    configurar_registro()
    instalar_manejador_global()

    _log = logging.getLogger(__name__)
    _log.info("Iniciando Flerovio %s", __version__)

    cliente = ClienteAPI()
    try:
        sesion = _intentar_auto_login(cliente)
        if sesion is None:
            resultado = _solicitar_sesion(cliente)
            if resultado is None:
                _log.info("Login cancelado, saliendo")
                return 0
            sesion, recordarme = resultado
            _persistir_eleccion(sesion, recordarme)

        ventana = VentanaPrincipal(sesion=sesion)

        def _al_cerrar_sesion() -> None:
            email_actual = (
                cliente.sesion.usuario.email if cliente.sesion is not None else None
            )
            cliente.cerrar_sesion()
            if email_actual is not None:
                credenciales.eliminar_token(email_actual)
            configuracion.guardar_recordarme(False)

            ventana.hide()
            resultado = _solicitar_sesion(cliente, padre=ventana)
            if resultado is None:
                _log.info("Login cancelado tras logout, saliendo")
                app.quit()
                return
            nueva, recordarme = resultado
            _persistir_eleccion(nueva, recordarme)
            ventana.actualizar_sesion(nueva)
            ventana.show()

        ventana.cerrar_sesion_solicitado.connect(_al_cerrar_sesion)
        cliente.sesion_invalidada.connect(_al_cerrar_sesion)
        ventana.show()

        hilo_actualizaciones, verificador = _lanzar_verificacion(app, ventana)

        try:
            return app.exec()
        finally:
            hilo_actualizaciones.quit()
            hilo_actualizaciones.wait(2000)
            _ = verificador  # mantener referencia durante app.exec()
    finally:
        cliente.cerrar()


def _lanzar_verificacion(
    app: QApplication, ventana: VentanaPrincipal
) -> tuple[QThread, VerificadorActualizaciones]:
    """Lanza la verificación de actualizaciones en un hilo de fondo."""
    hilo = QThread()
    verificador = VerificadorActualizaciones()
    verificador.moveToThread(hilo)
    hilo.started.connect(verificador.ejecutar)
    verificador.finalizado.connect(hilo.quit)

    def _al_disponible(actualizacion: Actualizacion) -> None:
        dialogo = DialogoActualizacion(actualizacion, padre=ventana)
        dialogo.instalacion_lanzada.connect(app.quit)
        dialogo.exec()

    verificador.actualizacion_disponible.connect(_al_disponible)
    hilo.start()
    return hilo, verificador


if __name__ == "__main__":
    sys.exit(main())
