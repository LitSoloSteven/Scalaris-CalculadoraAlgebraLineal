"""Motor del método de Gauss-Seidel para sistemas lineales cuadrados exactos."""
from fractions import Fraction

from ..iterativos.aritmetica_iterativa import (
    PresupuestoAritmetico, producto_fila_mixto, residuo_sistema,
)
from ..iterativos.motor_iterativo import FabricaResultado, ejecutar_metodo
from ..iterativos.modelos_iterativos import EntradaPreparada
from .contrato_gauss_seidel import (
    DiagnosticoGaussSeidel, EntradaGaussSeidel, PasoGaussSeidel, ResultadoGaussSeidel,
)
from .limites_gauss_seidel import CONFIGURACION_ARITMETICA_GAUSS_SEIDEL
from .validacion_gauss_seidel import (
    FalloValidacionGaussSeidel, preparar_captura, preparar_entrada,
)

_FABRICA_GAUSS_SEIDEL = FabricaResultado(
    crear_paso=PasoGaussSeidel,
    crear_resultado=ResultadoGaussSeidel,
    crear_diagnostico=DiagnosticoGaussSeidel,
)


def resolver_gauss_seidel(entrada: EntradaGaussSeidel) -> ResultadoGaussSeidel:
    """Resuelve Ax=b desde una cuadrícula de coeficientes crudos y parámetros tipados.
    La tolerancia se aplica a la norma infinito del residuo."""
    return _resolver_validacion(preparar_entrada(entrada))


def resolver_gauss_seidel_desde_captura(captura: object) -> ResultadoGaussSeidel:
    """Resuelve desde matriz_a, vector_b, tolerancia y maximo_iteraciones crudos.
    Usa cero si se omite vector_inicial y devuelve un diagnóstico si la captura es inválida."""
    return _resolver_validacion(preparar_captura(captura))


def _resolver_validacion(
    preparada: EntradaPreparada | FalloValidacionGaussSeidel,
) -> ResultadoGaussSeidel:
    if isinstance(preparada, FalloValidacionGaussSeidel):
        return ResultadoGaussSeidel(
            codigo=preparada.codigo,
            dominancia_estricta=preparada.dominancia_estricta,
            diagnostico=preparada.diagnostico,
        )
    presupuesto = PresupuestoAritmetico(CONFIGURACION_ARITMETICA_GAUSS_SEIDEL)
    return ejecutar_metodo(
        preparada, presupuesto, _siguiente_vector, _FABRICA_GAUSS_SEIDEL,
        residuo_sistema,
    )


def _siguiente_vector(
    preparada: EntradaPreparada,
    anterior: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> tuple[Fraction, ...]:
    """Recorre las filas en orden y reutiliza de inmediato cada componente nueva."""
    trabajo = list(anterior)
    for indice, fila in enumerate(preparada.matriz):
        suma = producto_fila_mixto(
            fila, indice, anterior, tuple(trabajo), presupuesto,
        )
        presupuesto.consumir(2)
        componente = (preparada.vector_b[indice] - suma) / fila[indice]
        trabajo[indice] = presupuesto.registrar(componente)
    return tuple(trabajo)
