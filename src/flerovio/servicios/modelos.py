"""Modelos de datos para los servicios del ERP."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Usuario:
    id: int
    email: str
    tenant_id: int
    tenant_nombre: str
    rol: str
    empleado_id: int | None

    @classmethod
    def desde_json(cls, datos: dict) -> Usuario:
        return cls(
            id=datos["id"],
            email=datos["email"],
            tenant_id=datos["tenant_id"],
            tenant_nombre=datos.get("tenant_nombre", ""),
            rol=datos.get("role", ""),
            empleado_id=datos.get("empleado_id"),
        )


@dataclass(frozen=True)
class Sesion:
    """Resultado de una autenticación exitosa."""

    token: str
    tipo_token: str
    usuario: Usuario


class ErrorAPI(Exception):
    """Error genérico de la API con detalles del servicio."""

    def __init__(self, mensaje: str, codigo: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
