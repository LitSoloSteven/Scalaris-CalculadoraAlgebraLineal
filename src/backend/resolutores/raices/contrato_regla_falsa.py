"""Contrato de entrada y salida del motor de regla falsa."""
from dataclasses import dataclass, field
from typing import Literal

from .contrato_biseccion import AVISO_INTERVALO_INVERTIDO, ContextoFallo
from .contrato_continuidad import InformeContinuidad
from .decision_biseccion import SignoProducto
from .limites_raices import LIMITE_ITERACIONES_DEFECTO

AccionReglaFalsa = Literal["reemplazar_a", "reemplazar_b", "raiz", "sin_cambio"]
DiagnosticoReglaFalsa = dict


@dataclass(frozen=True, kw_only=True)
class EntradaReglaFalsa:
    """Expresion, intervalo y tolerancia de residuo validados para falsa posicion."""

    expresion: str
    extremo_izquierdo: float
    extremo_derecho: float
    tolerancia: float = 1e-6
    limite_iteraciones: int = LIMITE_ITERACIONES_DEFECTO
    unidad_angular: Literal["radianes", "grados"] = "radianes"
    intervalo_invertido: bool = False

    @property
    def advertencias(self) -> tuple[str, ...]:
        """Devuelve el aviso de normalizacion conservado al revalidar la entrada canonica."""
        return (AVISO_INTERVALO_INVERTIDO,) if self.intervalo_invertido else ()


@dataclass(frozen=True)
class IteracionReglaFalsa:
    """Registro inmutable de una iteracion del metodo."""

    i: int
    extremo_izquierdo: float
    extremo_derecho: float
    valor_izquierdo: float
    valor_derecho: float
    aproximacion: float
    valor_aproximacion: float
    residuo: float
    ancho: float
    peso_secante: float
    error_relativo_porcentual: float | None
    signo_producto: SignoProducto
    accion: AccionReglaFalsa
    intervalo_siguiente: tuple[float, float]
    motivo_parada: str = ""


@dataclass(frozen=True)
class ResultadoReglaFalsa:
    """Resultado completo del metodo con estado, intervalo final y metricas."""

    metodo: Literal["regla_falsa"] = field(default="regla_falsa", init=False)
    entrada: EntradaReglaFalsa | None = None
    estado: Literal["EXITO", "SIN_CAMBIO_DE_SIGNO", "ESTANCAMIENTO", "LIMITE_ITERACIONES", "ERROR"] = "ERROR"
    mensaje: str = ""
    codigo_diagnostico: str = ""
    motivo_parada: str = ""
    aproximacion: float | None = None
    residuo: float | None = None
    intervalo_final: tuple[float, float] | None = None
    iteraciones: tuple[IteracionReglaFalsa, ...] = ()
    iteraciones_totales: int = 0
    advertencias: tuple[str, ...] = ()
    informe_continuidad: InformeContinuidad | None = None
    contexto_fallo: ContextoFallo | None = None