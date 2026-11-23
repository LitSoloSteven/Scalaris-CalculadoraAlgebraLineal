"""Motor común de barridos y parada para los métodos iterativos."""
from collections.abc import Callable
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Generic, TypeVar

from .aritmetica_iterativa import (
    LimiteAritmeticoIterativo,
    LimiteResiduoIterativo,
    PresupuestoAritmetico,
    norma_infinito,
    residuo_sistema,
)
from .contrato_iterativo import (
    CodigoIterativo,
    DiagnosticoIterativo,
    PasoIterativo,
    ResultadoIterativo,
    VectorIterativo,
)
from .modelos_iterativos import EntradaPreparada

TipoResultado = TypeVar("TipoResultado", bound=ResultadoIterativo)

CalculadoraSiguiente = Callable[
    [EntradaPreparada, VectorIterativo, PresupuestoAritmetico], VectorIterativo,
]
CalculadoraResiduo = Callable[
    [
        tuple[tuple[Fraction, ...], ...],
        VectorIterativo,
        VectorIterativo,
        PresupuestoAritmetico,
    ],
    VectorIterativo,
]


@dataclass(frozen=True, kw_only=True)
class FabricaResultado(Generic[TipoResultado]):
    """Agrupa las clases del método para construir pasos, resultados y diagnósticos."""

    crear_paso: Callable[..., PasoIterativo]
    crear_resultado: Callable[..., TipoResultado]
    crear_diagnostico: Callable[..., DiagnosticoIterativo]


@dataclass(frozen=True, kw_only=True)
class ContextoMotor(Generic[TipoResultado]):
    """Reúne la entrada preparada, el presupuesto y las funciones del método."""

    preparada: EntradaPreparada
    presupuesto: PresupuestoAritmetico
    calcular_siguiente: CalculadoraSiguiente
    fabrica: FabricaResultado[TipoResultado]
    calcular_residuo: CalculadoraResiduo


def ejecutar_metodo(
    preparada: EntradaPreparada,
    presupuesto: PresupuestoAritmetico,
    calcular_siguiente: CalculadoraSiguiente,
    fabrica: FabricaResultado[TipoResultado],
    calcular_residuo: CalculadoraResiduo = residuo_sistema,
) -> TipoResultado:
    """Evalúa el inicio y ejecuta barridos completos hasta una causa de parada."""
    contexto = ContextoMotor(
        preparada=preparada,
        presupuesto=presupuesto,
        calcular_siguiente=calcular_siguiente,
        fabrica=fabrica,
        calcular_residuo=calcular_residuo,
    )
    try:
        residuo = calcular_residuo(
            preparada.matriz, preparada.vector_b, preparada.vector_inicial, presupuesto,
        )
    except LimiteResiduoIterativo:
        return _iterar(contexto, None)
    except LimiteAritmeticoIterativo as error:
        return _resultado_limite(contexto, None, (), None, error)
    norma = norma_infinito(residuo)
    if norma == 0:
        return _resultado_con_vector(
            "SOLUCION_EXACTA", contexto, preparada.vector_inicial, residuo, (),
        )
    if norma <= preparada.tolerancia:
        return _resultado_con_vector(
            "TOLERANCIA_ALCANZADA", contexto, preparada.vector_inicial, residuo, (),
        )
    return _iterar(contexto, residuo)


def _iterar(
    contexto: ContextoMotor[TipoResultado], residuo_actual: VectorIterativo | None,
) -> TipoResultado:
    """Construye cada barrido completo y aplica la prioridad de parada."""
    pasos: list[PasoIterativo] = []
    anterior = contexto.preparada.vector_inicial
    for indice in range(1, contexto.preparada.maximo_iteraciones + 1):
        try:
            nuevo, residuo_nuevo, norma_cambio = _calcular_barrido(contexto, anterior)
        except LimiteAritmeticoIterativo as error:
            return _resultado_limite(
                contexto, anterior, tuple(pasos), residuo_actual, error,
            )
        paso = contexto.fabrica.crear_paso(
            indice=indice,
            vector_anterior=anterior,
            vector_nuevo=nuevo,
            norma_cambio=norma_cambio,
            norma_residuo=norma_infinito(residuo_nuevo),
        )
        pasos.append(paso)
        parada = _parada_alcanzada(paso, contexto.preparada.tolerancia)
        if parada is not None:
            return _resultado_con_vector(
                parada, contexto, nuevo, residuo_nuevo, tuple(pasos),
            )
        anterior = nuevo
        residuo_actual = residuo_nuevo
    assert residuo_actual is not None
    return _resultado_maximo(contexto, anterior, residuo_actual, tuple(pasos))


def _calcular_barrido(
    contexto: ContextoMotor[TipoResultado], anterior: VectorIterativo,
) -> tuple[VectorIterativo, VectorIterativo, Fraction]:
    """Calcula el vector nuevo, su residuo y la norma del cambio de un barrido."""
    nuevo = contexto.calcular_siguiente(
        contexto.preparada, anterior, contexto.presupuesto,
    )
    residuo_nuevo = contexto.calcular_residuo(
        contexto.preparada.matriz,
        contexto.preparada.vector_b,
        nuevo,
        contexto.presupuesto,
    )
    norma_cambio = _norma_cambio(
        anterior,
        nuevo,
        contexto.presupuesto,
        contexto.presupuesto.configuracion.maximo_bits_cambio,
    )
    return nuevo, residuo_nuevo, norma_cambio


def _parada_alcanzada(
    paso: PasoIterativo, tolerancia: Fraction,
) -> CodigoIterativo | None:
    """Devuelve el código de parada certificable o None si debe continuar."""
    if paso.norma_residuo == 0:
        return "SOLUCION_EXACTA"
    if paso.norma_residuo <= tolerancia:
        return "TOLERANCIA_ALCANZADA"
    return None


def _norma_cambio(
    anterior: VectorIterativo,
    nuevo: VectorIterativo,
    presupuesto: PresupuestoAritmetico,
    maximo_bits: int,
) -> Fraction:
    """Devuelve la norma infinito de la diferencia con la cota de tamaño de la traza."""
    diferencias = tuple(
        presupuesto.registrar(componente - previo, maximo_bits)
        for componente, previo in zip(nuevo, anterior, strict=True)
    )
    return norma_infinito(diferencias)


def _resultado_con_vector(
    codigo: CodigoIterativo,
    contexto: ContextoMotor[TipoResultado],
    vector: VectorIterativo,
    residuo: VectorIterativo,
    pasos: tuple[PasoIterativo, ...],
) -> TipoResultado:
    """Construye un resultado con un vector completo ya verificado."""
    return contexto.fabrica.crear_resultado(
        codigo=codigo,
        aproximacion=vector,
        residuo=residuo,
        norma_residuo=norma_infinito(residuo),
        dominancia_estricta=contexto.preparada.dominancia_estricta,
        pasos=pasos,
        entrada_canonica=contexto.preparada,
    )


def _resultado_maximo(
    contexto: ContextoMotor[TipoResultado],
    vector: VectorIterativo,
    residuo: VectorIterativo,
    pasos: tuple[PasoIterativo, ...],
) -> TipoResultado:
    """Cierra por agotamiento del máximo sin ocultar la última aproximación."""
    resultado = _resultado_con_vector(
        "MAXIMO_ITERACIONES", contexto, vector, residuo, pasos,
    )
    diagnostico = contexto.fabrica.crear_diagnostico(
        mensaje="Se alcanzó el máximo de iteraciones sin cumplir la tolerancia del residuo."
    )
    return replace(resultado, diagnostico=diagnostico)


def _resultado_limite(
    contexto: ContextoMotor[TipoResultado],
    anterior: VectorIterativo | None,
    pasos: tuple[PasoIterativo, ...],
    residuo: VectorIterativo | None,
    error: LimiteAritmeticoIterativo,
) -> TipoResultado:
    """Cierra por presupuesto aritmético y conserva el último vector verificable."""
    if anterior is None or residuo is None:
        mensaje = f"{error} No se pudo verificar el vector inicial."
        diagnostico = contexto.fabrica.crear_diagnostico(mensaje=mensaje)
        return contexto.fabrica.crear_resultado(
            codigo="LIMITE_ARITMETICO",
            dominancia_estricta=contexto.preparada.dominancia_estricta,
            diagnostico=diagnostico,
            entrada_canonica=contexto.preparada,
        )
    mensaje = f"{error} Se conserva la última aproximación completa."
    resultado = _resultado_con_vector(
        "LIMITE_ARITMETICO", contexto, anterior, residuo, pasos,
    )
    diagnostico = contexto.fabrica.crear_diagnostico(mensaje=mensaje)
    return replace(resultado, diagnostico=diagnostico)
