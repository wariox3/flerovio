"""Tests para nucleo.credenciales con un backend de keyring en memoria."""

from __future__ import annotations

import keyring
import keyring.backend
import keyring.errors
import pytest

from flerovio.nucleo import credenciales


class _KeyringEnMemoria(keyring.backend.KeyringBackend):
    priority = 1  # type: ignore[assignment]

    def __init__(self) -> None:
        super().__init__()
        self._datos: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._datos.get((service, username))

    def set_password(self, service, username, password):
        self._datos[(service, username)] = password

    def delete_password(self, service, username):
        if (service, username) not in self._datos:
            raise keyring.errors.PasswordDeleteError("no existe")
        del self._datos[(service, username)]


@pytest.fixture
def backend(monkeypatch):
    b = _KeyringEnMemoria()
    monkeypatch.setattr(keyring, "get_keyring", lambda: b)
    monkeypatch.setattr(keyring, "set_password", b.set_password)
    monkeypatch.setattr(keyring, "get_password", b.get_password)
    monkeypatch.setattr(keyring, "delete_password", b.delete_password)
    return b


def test_guardar_y_leer_token(backend):
    assert credenciales.guardar_token("a@b.com", "tk-1") is True
    assert credenciales.leer_token("a@b.com") == "tk-1"


def test_leer_token_inexistente(backend):
    assert credenciales.leer_token("nadie@b.com") is None


def test_eliminar_token(backend):
    credenciales.guardar_token("a@b.com", "tk-1")
    credenciales.eliminar_token("a@b.com")
    assert credenciales.leer_token("a@b.com") is None


def test_eliminar_token_inexistente_no_falla(backend):
    credenciales.eliminar_token("nadie@b.com")  # no debe lanzar


def test_guardar_token_falla_silenciosamente(monkeypatch):
    def romper(*a, **kw):
        raise keyring.errors.KeyringError("backend muerto")

    monkeypatch.setattr(keyring, "set_password", romper)
    assert credenciales.guardar_token("a@b.com", "tk") is False
