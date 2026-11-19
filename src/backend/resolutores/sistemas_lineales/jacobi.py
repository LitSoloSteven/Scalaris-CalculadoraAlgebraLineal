"""Motor del método de Jacobi para sistemas lineales cuadrados exactos."""
from dataclasses import replace
from fractions import Fraction

from .aritmetica_jacobi import (
    LimiteAritmeticoJacobi, PresupuestoAritmetico, norma_infinito,
    producto_fila_sin_diagonal, residuo_sistema,
)
from .contrato_jacobi import (
    CodigoJacobi, DiagnosticoJacobi, EntradaJacobi, PasoJacobi, ResultadoJacobi,
)
from .limites_jacobi import MAXIMO_BITS_CAMBIO_JACOBI
from .validacion_jacobi import (
    EntradaPreparadaJacobi, FalloValidacionJacobi, preparar_captura, preparar_entrada,
)


def resolver_jacobi(entrada: EntradaJacobi) -> ResultadoJacobi:
    """Resuelve Ax=b desde una Matriz ya exacta, con tolerancia sobre la norma infinito del residuo.
    Para coeficientes ingresados por el usuario, usa resolver_jacobi_desde_captura."""
    return _resolver_validacion(preparar_entrada(entrada))


def resolver_jacobi_desde_captura(captura: object) -> ResultadoJacobi:
    """Resuelve desde matriz_a, vector_b, tolerancia y maximo_iteraciones crudos.
    Usa cero si se omite vector_inicial y devuelve un diagnóstico si la captura es inválida."""
    return _resolver_validacion(preparar_captura(captura))


def _resolver_validacion(preparada: EntradaPreparadaJacobi | FalloValidacionJacobi) -> ResultadoJacobi:
    if isinstance(preparada, FalloValidacionJacobi):
        return ResultadoJacobi(
            codigo=preparada.codigo,
            dominancia_estricta=preparada.dominancia_estricta,
            diagnostico=preparada.diagnostico,
        )
    return _resolver_preparada(preparada)


def _resolver_preparada(preparada: EntradaPreparadaJacobi) -> ResultadoJacobi:
    """Evalúa el inicio y decide si hay parada inmediata antes de iterar."""
    presupuesto = PresupuestoAritmetico()
    try:
        residuo = residuo_sistema(
            preparada.matriz, preparada.vector_b, preparada.vector_inicial, presupuesto,
        )
    except LimiteAritmeticoJacobi as error:
        return _resultado_limite(preparada, None, (), None, error)
    norma = norma_infinito(residuo)
    if norma == 0:
        return _resultado_con_vector(
            "SOLUCION_EXACTA", preparada, preparada.vector_inicial, residuo, (),
        )
    if norma <= preparada.tolerancia:
        return _resultado_con_vector(
            "TOLERANCIA_ALCANZADA", preparada, preparada.vector_inicial, residuo, (),
        )
    return _iterar(preparada, presupuesto, residuo)


def _iterar(
    preparada: EntradaPreparadaJacobi,
    presupuesto: PresupuestoAritmetico,
    residuo_actual: tuple[Fraction, ...],
) -> ResultadoJacobi:
    """Construye cada vector nuevo desde el anterior y aplica la prioridad de parada."""
    pasos = []
    anterior = preparada.vector_inicial
    for indice in range(1, preparada.maximo_iteraciones + 1):
        try:
            nuevo = _siguiente_vector(preparada, anterior, presupuesto)
            residuo_nuevo = residuo_sistema(
                preparada.matriz, preparada.vector_b, nuevo, presupuesto,
            )
            norma_cambio = _norma_cambio(anterior, nuevo, presupuesto)
        except LimiteAritmeticoJacobi as error:
            return _resultado_limite(preparada, anterior, tuple(pasos), residuo_actual, error)
        paso = PasoJacobi(
            indice=indice,
            vector_anterior=anterior,
            vector_nuevo=nuevo,
            norma_cambio=norma_cambio,
            norma_residuo=norma_infinito(residuo_nuevo),
        )
        pasos.append(paso)
        if paso.norma_residuo == 0:
            return _resultado_con_vector(
                "SOLUCION_EXACTA", preparada, nuevo, residuo_nuevo, tuple(pasos),
            )
        if paso.norma_residuo <= preparada.tolerancia:
            return _resultado_con_vector(
                "TOLERANCIA_ALCANZADA", preparada, nuevo, residuo_nuevo, tuple(pasos),
            )
        anterior = nuevo
        residuo_actual = residuo_nuevo
    return _resultado_maximo(preparada, anterior, residuo_actual, tuple(pasos))


def _siguiente_vector(
    preparada: EntradaPreparadaJacobi,
    anterior: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> tuple[Fraction, ...]:
    """Calcula las n componentes nuevas leyendo solo el vector anterior."""
    nuevo = []
    for indice, fila in enumerate(preparada.matriz):
        suma = producto_fila_sin_diagonal(fila, indice, anterior, presupuesto)
        presupuesto.consumir(2)
        componente = (preparada.vector_b[indice] - suma) / fila[indice]
        nuevo.append(presupuesto.registrar(componente))
    return tuple(nuevo)


def _norma_cambio(
    anterior: tuple[Fraction, ...],
    nuevo: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> Fraction:
    """Devuelve la norma infinito de la diferencia con la cota de tamaño de la traza."""
    diferencias = tuple(
        presupuesto.registrar(componente - previo, MAXIMO_BITS_CAMBIO_JACOBI)
        for componente, previo in zip(nuevo, anterior, strict=True)
    )
    return norma_infinito(diferencias)


def _resultado_con_vector(
    codigo: CodigoJacobi,
    preparada: EntradaPreparadaJacobi,
    vector: tuple[Fraction, ...],
    residuo: tuple[Fraction, ...],
    pasos: tuple[PasoJacobi, ...],
) -> ResultadoJacobi:
    """Construye un resultado con un vector completo ya verificado."""
    return ResultadoJacobi(
        codigo=codigo,
        aproximacion=vector,
        residuo=residuo,
        norma_residuo=norma_infinito(residuo),
        dominancia_estricta=preparada.dominancia_estricta,
        pasos=pasos,
    )


def _resultado_maximo(
    preparada: EntradaPreparadaJacobi,
    vector: tuple[Fraction, ...],
    residuo: tuple[Fraction, ...],
    pasos: tuple[PasoJacobi, ...],
) -> ResultadoJacobi:
    """Cierra por agotamiento del máximo sin ocultar la última aproximación."""
    resultado = _resultado_con_vector(
        "MAXIMO_ITERACIONES", preparada, vector, residuo, pasos,
    )
    diagnostico = DiagnosticoJacobi(
        mensaje="Se alcanzó el máximo de iteraciones sin cumplir la tolerancia del residuo."
    )
    return replace(resultado, diagnostico=diagnostico)


def _resultado_limite(
    preparada: EntradaPreparadaJacobi,
    anterior: tuple[Fraction, ...] | None,
    pasos: tuple[PasoJacobi, ...],
    residuo: tuple[Fraction, ...] | None,
    error: LimiteAritmeticoJacobi,
) -> ResultadoJacobi:
    """Cierra por presupuesto aritmético y conserva el último vector verificable."""
    if anterior is None or residuo is None:
        mensaje = f"{error} No se pudo verificar el vector inicial."
        return ResultadoJacobi(
            codigo="LIMITE_ARITMETICO",
            dominancia_estricta=preparada.dominancia_estricta,
            diagnostico=DiagnosticoJacobi(mensaje=mensaje),
        )
    mensaje = f"{error} Se conserva la última aproximación completa."
    resultado = _resultado_con_vector(
        "LIMITE_ARITMETICO", preparada, anterior, residuo, pasos,
    )
    return replace(resultado, diagnostico=DiagnosticoJacobi(mensaje=mensaje))
