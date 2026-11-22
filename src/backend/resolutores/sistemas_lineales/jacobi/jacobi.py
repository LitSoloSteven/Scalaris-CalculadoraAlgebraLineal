"""Motor del método de Jacobi para sistemas lineales cuadrados exactos."""
from fractions import Fraction

from ..iterativos.aritmetica_iterativa import PresupuestoAritmetico as PresupuestoAritmeticoComun
from ..iterativos.motor_iterativo import FabricaResultado, ejecutar_metodo
from ..iterativos.modelos_iterativos import EntradaPreparada
from .aritmetica_jacobi import (
    PresupuestoAritmetico, producto_fila_sin_diagonal, residuo_sistema,
)
from .contrato_jacobi import (
    DiagnosticoJacobi, EntradaJacobi, PasoJacobi, ResultadoJacobi,
)
from .validacion_jacobi import FalloValidacionJacobi, preparar_captura, preparar_entrada

_FABRICA_JACOBI: FabricaResultado[ResultadoJacobi] = FabricaResultado(
    crear_paso=PasoJacobi,
    crear_resultado=ResultadoJacobi,
    crear_diagnostico=DiagnosticoJacobi,
)


def resolver_jacobi(entrada: EntradaJacobi) -> ResultadoJacobi:
    """Resuelve Ax=b desde una cuadrícula de coeficientes crudos y parámetros tipados.
    La tolerancia se aplica a la norma infinito del residuo."""
    return _resolver_validacion(preparar_entrada(entrada))


def resolver_jacobi_desde_captura(captura: object) -> ResultadoJacobi:
    """Resuelve desde matriz_a, vector_b, tolerancia y maximo_iteraciones crudos.
    Usa cero si se omite vector_inicial y devuelve un diagnóstico si la captura es inválida."""
    return _resolver_validacion(preparar_captura(captura))


def _resolver_validacion(
    preparada: EntradaPreparada | FalloValidacionJacobi,
) -> ResultadoJacobi:
    if isinstance(preparada, FalloValidacionJacobi):
        return ResultadoJacobi(
            codigo=preparada.codigo,
            dominancia_estricta=preparada.dominancia_estricta,
            diagnostico=preparada.diagnostico,
        )
    return ejecutar_metodo(
        preparada, PresupuestoAritmetico(), _siguiente_vector, _FABRICA_JACOBI,
        residuo_sistema,
    )


def _siguiente_vector(
    preparada: EntradaPreparada,
    anterior: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmeticoComun,
) -> tuple[Fraction, ...]:
    """Calcula las n componentes nuevas leyendo solo el vector anterior."""
    nuevo = []
    for indice, fila in enumerate(preparada.matriz):
        suma = producto_fila_sin_diagonal(fila, indice, anterior, presupuesto)
        presupuesto.consumir(2)
        componente = (preparada.vector_b[indice] - suma) / fila[indice]
        nuevo.append(presupuesto.registrar(componente))
    return tuple(nuevo)
