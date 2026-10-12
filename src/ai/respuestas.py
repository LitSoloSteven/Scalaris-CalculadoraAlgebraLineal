"""Tipos inmutables de consulta y respuesta entre Glosa y su cliente de IA."""
from dataclasses import dataclass
from enum import Enum


class TipoErrorIA(str, Enum):
    """Distingue las causas de fallo sin exponer detalles del proveedor."""

    SIN_CLAVE = "SIN_CLAVE"
    AUTENTICACION = "AUTENTICACION"
    TIEMPO_AGOTADO = "TIEMPO_AGOTADO"
    LIMITE_PETICIONES = "LIMITE_PETICIONES"
    VACIO = "VACIO"
    RED = "RED"
    SERVICIO = "SERVICIO"
    CANCELADO = "CANCELADO"


@dataclass(frozen=True)
class ResultadoIA:
    """Transporta texto, causa de fallo, modelo y procedencia de la respuesta."""

    exito: bool
    texto: str
    tipo_error: TipoErrorIA | None = None
    modelo: str | None = None
    desde_cache: bool = False


@dataclass(frozen=True)
class OpcionesConsulta:
    """Indica si se permite caché y si se solicita una explicación más simple."""

    usar_cache: bool = False
    respuesta_simple: bool = False
