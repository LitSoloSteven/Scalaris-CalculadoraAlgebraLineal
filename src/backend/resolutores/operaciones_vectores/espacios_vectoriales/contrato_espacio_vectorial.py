"""Contrato exacto para verificar espacios vectoriales con operaciones polinómicas."""
from fractions import Fraction
from typing import Literal, TypedDict, get_args

from ..subespacios.contrato_subespacios import EntradaSubespacio

AxiomaEspacioVectorial = Literal[
    "CIERRE_SUMA", "CIERRE_ESCALAR", "CONMUTATIVIDAD_SUMA", "ASOCIATIVIDAD_SUMA",
    "NEUTRO_SUMA", "INVERSO_SUMA", "IDENTIDAD_ESCALAR", "ASOCIATIVIDAD_ESCALAR",
    "DISTRIBUTIVIDAD_VECTORES", "DISTRIBUTIVIDAD_ESCALARES",
]
AXIOMAS_ESPACIO_VECTORIAL: tuple[AxiomaEspacioVectorial, ...] = get_args(AxiomaEspacioVectorial)
CodigoEspacioVectorial = Literal[
    "ESPACIO_VECTORIAL", "NO_ESPACIO_VECTORIAL", "CONJUNTO_VACIO", "ENTRADA_INVALIDA",
    "LIMITE_ARITMETICO", "ERROR_INTERNO",
]
CampoDiagnostico = Literal["conjunto", "suma", "producto_escalar", "general"]
CampoOperacion = Literal["suma", "producto_escalar"]
VectorExacto = tuple[Fraction, ...]


class TerminoPolinomico(TypedDict):
    """Representa un monomio en el orden de variables de su operación."""

    coeficiente: Fraction
    exponentes: tuple[int, ...]


OperacionPolinomica = tuple[tuple[TerminoPolinomico, ...], ...]


class EntradaEspacioVectorial(TypedDict):
    """Describe un conjunto real y las coordenadas de sus dos operaciones."""

    conjunto: EntradaSubespacio
    suma: OperacionPolinomica
    producto_escalar: OperacionPolinomica


class CertificadoAxioma(TypedDict):
    """Guarda los residuos exactos en el orden declarado de las variables libres."""

    variables_libres: tuple[str, ...]
    identidades: OperacionPolinomica


class TestigoAxioma(TypedDict):
    """Contiene operandos racionales y los dos lados de una igualdad fallida."""

    vectores: tuple[VectorExacto, ...]
    escalares: VectorExacto
    lado_izquierdo: VectorExacto
    lado_derecho: VectorExacto


class ComprobacionAxioma(TypedDict):
    """Describe un axioma y la evidencia disponible para su estado."""

    axioma: AxiomaEspacioVectorial
    estado: Literal["CUMPLE", "NO_CUMPLE", "NO_VERIFICADO"]
    explicacion: str
    certificado: CertificadoAxioma | None
    testigo: TestigoAxioma | None


class DiagnosticoEspacioVectorial(TypedDict):
    """Localiza un diagnóstico en la captura con índices desde uno."""

    campo: CampoDiagnostico
    coordenada: int | None
    termino: int | None
    mensaje: str


class ErrorCapturaEspacioVectorial(ValueError):
    """Indica que la captura no satisface el contrato de entrada."""

    def __init__(self, diagnostico: DiagnosticoEspacioVectorial) -> None:
        """Conserva el diagnóstico estructurado y expone su mensaje como excepción."""
        self.diagnostico = diagnostico
        super().__init__(diagnostico["mensaje"])


class ResultadoEspacioVectorial(TypedDict):
    """Contiene el veredicto y la evidencia exacta obtenida por el análisis."""

    estado: Literal["EXITO", "ERROR"]
    codigo: CodigoEspacioVectorial
    es_espacio_vectorial: bool | None
    dimension_ambiente: int | None
    vector_cero: VectorExacto | None
    comprobaciones: tuple[ComprobacionAxioma, ...]
    diagnostico: DiagnosticoEspacioVectorial | None
