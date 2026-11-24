"""Contrato tipado y constructor homogeneo del resultado por adjunta."""
from fractions import Fraction
from typing import Literal, TypedDict

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.determinante.cofactores import (
    MAXIMO_NODOS_COFACTORES,
)

METODO_ADJUNTA = "adjunta"

CODIGO_INVERSA_CALCULADA = "INVERSA_CALCULADA"
CODIGO_MATRIZ_SINGULAR = "MATRIZ_SINGULAR"
CODIGO_ENTRADA_INVALIDA = "ENTRADA_INVALIDA"
CODIGO_DIMENSION_EXCEDIDA = "DIMENSION_ADJUNTA_EXCEDIDA"
CODIGO_PRESUPUESTO_EXCEDIDO = "PRESUPUESTO_COFACTORES_EXCEDIDO"
CODIGO_VERIFICACION_INCONSISTENTE = "VERIFICACION_INCONSISTENTE"

EstadoAdjunta = Literal["EXITO", "SINGULAR", "ERROR"]
CodigoAdjunta = Literal[
    "INVERSA_CALCULADA",
    "MATRIZ_SINGULAR",
    "ENTRADA_INVALIDA",
    "DIMENSION_ADJUNTA_EXCEDIDA",
    "PRESUPUESTO_COFACTORES_EXCEDIDO",
    "VERIFICACION_INCONSISTENTE",
]


class DetalleCofactor(TypedDict):
    """Menor y cofactor de una coordenada, con indices originales en base cero."""

    fila: int
    columna: int
    filas_originales: tuple[int, ...]
    columnas_originales: tuple[int, ...]
    matriz_menor: Matriz | None
    valor_menor: Fraction
    signo: int
    cofactor: Fraction
    menor_vacio: bool


class PasoAdjunta(TypedDict):
    """Paso didactico completo; las claves ausentes se representan con None."""

    indice: int
    tipo: str
    descripcion: str
    explicacion: str
    matriz: Matriz | None
    coordenada: tuple[int, int] | None
    valor: Fraction | None
    detalle: str | None


class ComprobacionAdjunta(TypedDict):
    """Producto exacto comparado con la matriz esperada y su detalle textual."""

    clave: str
    descripcion: str
    coincide: bool
    producto: Matriz | None
    esperado: Matriz | None
    detalle_latex: str | None


class ResultadoInversaAdjunta(TypedDict):
    """Salida unica del motor; todas las ramas conservan las mismas claves."""

    estado: EstadoAdjunta
    codigo: CodigoAdjunta
    mensaje: str
    metodo: str
    dimension: int
    matriz_a: Matriz | None
    determinante: Fraction | None
    menores: Matriz | None
    cofactores: Matriz | None
    adjunta: Matriz | None
    inversa: Matriz | None
    detalle_cofactores: tuple[DetalleCofactor, ...]
    traza: tuple[PasoAdjunta, ...]
    comprobaciones: tuple[ComprobacionAdjunta, ...]
    nodos_cofactores: int
    limite_nodos: int


def crear_resultado_adjunta(
    estado: EstadoAdjunta,
    codigo: CodigoAdjunta,
    mensaje: str,
    dimension: int = 0,
) -> ResultadoInversaAdjunta:
    """Devuelve un resultado completo con vacios para las ramas sin calculo."""
    return {
        "estado": estado,
        "codigo": codigo,
        "mensaje": mensaje,
        "metodo": METODO_ADJUNTA,
        "dimension": dimension,
        "matriz_a": None,
        "determinante": None,
        "menores": None,
        "cofactores": None,
        "adjunta": None,
        "inversa": None,
        "detalle_cofactores": (),
        "traza": (),
        "comprobaciones": (),
        "nodos_cofactores": 0,
        "limite_nodos": MAXIMO_NODOS_COFACTORES,
    }
