"""Motor exacto de inversa por adjunta con comprobaciones y traza."""
from fractions import Fraction

from src.backend.constantes import (
    ERROR,
    EXITO,
    SINGULAR,
)
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.operaciones.construcciones import identidad
from src.backend.resolutores.operaciones_matrices.compartido.comprobacion_productos import (
    comprobar_producto,
)
from src.backend.resolutores.operaciones_matrices.determinante import cofactores
from .construccion_adjunta import ConstruccionAdjunta, construir_adjunta
from .contrato_adjunta import (
    CODIGO_INVERSA_CALCULADA,
    CODIGO_MATRIZ_SINGULAR,
    CODIGO_PRESUPUESTO_EXCEDIDO,
    CODIGO_VERIFICACION_INCONSISTENTE,
    CodigoAdjunta,
    ComprobacionAdjunta,
    EstadoAdjunta,
    PasoAdjunta,
    ResultadoInversaAdjunta,
    crear_resultado_adjunta,
)
from .traza_adjunta import ContextoTrazaAdjunta, construir_traza_adjunta
from .validacion_adjunta import validar_entrada_adjunta


def calcular_inversa_adjunta(matriz: Matriz) -> ResultadoInversaAdjunta:
    """Devuelve menores, cofactores, adjunta, inversa y comprobaciones exactas."""
    rechazo = _resultado_entrada_invalida(matriz)
    if rechazo is not None:
        return rechazo
    try:
        construccion = construir_adjunta(_copiar_datos(matriz))
    except cofactores.ErrorPresupuestoCofactores as error:
        return _resultado_presupuesto(matriz, error)
    return _resultado_calculo(matriz, construccion)


def _crear_resultado(
    estado: EstadoAdjunta,
    codigo: CodigoAdjunta,
    mensaje: str,
    dimension: int = 0,
) -> ResultadoInversaAdjunta:
    resultado = crear_resultado_adjunta(estado, codigo, mensaje, dimension)
    resultado["limite_nodos"] = cofactores.MAXIMO_NODOS_COFACTORES
    return resultado


def _resultado_entrada_invalida(matriz: object) -> ResultadoInversaAdjunta | None:
    rechazo = validar_entrada_adjunta(matriz)
    if rechazo is None:
        return None
    codigo, mensaje, dimension = rechazo
    return _crear_resultado(ERROR, codigo, mensaje, dimension)


def _copiar_datos(matriz: Matriz) -> list[list[Fraction]]:
    return [[Fraction(valor) for valor in fila] for fila in matriz.datos]


def _resultado_presupuesto(
    matriz: Matriz, error: cofactores.ErrorPresupuestoCofactores
) -> ResultadoInversaAdjunta:
    mensaje = "Se supero el presupuesto compartido de cofactores. Reduce la dimension o usa Gauss-Jordan."
    resultado = _crear_resultado(ERROR, CODIGO_PRESUPUESTO_EXCEDIDO, mensaje, matriz.filas)
    resultado["matriz_a"] = matriz.clonar()
    resultado["nodos_cofactores"] = error.nodos
    resultado["limite_nodos"] = error.limite
    return resultado


def _resultado_calculo(
    matriz: Matriz, construccion: ConstruccionAdjunta
) -> ResultadoInversaAdjunta:
    resultado = _crear_resultado(
        EXITO,
        CODIGO_INVERSA_CALCULADA,
        "Inversa calculada por adjunta con comprobaciones exactas.",
        matriz.filas,
    )
    resultado.update(
        matriz_a=matriz.clonar(),
        determinante=construccion["determinante"],
        menores=construccion["menores"],
        cofactores=construccion["cofactores"],
        adjunta=construccion["adjunta"],
        detalle_cofactores=construccion["detalles"],
        nodos_cofactores=construccion["nodos"],
    )
    if construccion["determinante"] == 0:
        return _cerrar_singular(resultado, matriz, construccion)
    return _cerrar_invertible(resultado, matriz, construccion)


def _cerrar_singular(
    resultado: ResultadoInversaAdjunta,
    matriz: Matriz,
    construccion: ConstruccionAdjunta,
) -> ResultadoInversaAdjunta:
    comprobacion = _comprobar_a_adjunta(
        matriz, construccion["adjunta"], construccion["determinante"]
    )
    if not comprobacion["coincide"]:
        return _resultado_verificacion(matriz, construccion)
    resultado.update(
        estado=SINGULAR,
        codigo=CODIGO_MATRIZ_SINGULAR,
        mensaje="La matriz es singular (det = 0). Se conservan menores, cofactores y adjunta, sin inversa.",
        comprobaciones=(comprobacion,),
    )
    resultado["traza"] = _traza(matriz, construccion, None, (comprobacion,))
    return resultado


def _cerrar_invertible(
    resultado: ResultadoInversaAdjunta,
    matriz: Matriz,
    construccion: ConstruccionAdjunta,
) -> ResultadoInversaAdjunta:
    inversa = _dividir_adjunta(construccion["adjunta"], construccion["determinante"])
    comprobaciones = (
        _comprobar_a_adjunta(matriz, construccion["adjunta"], construccion["determinante"]),
        _comprobar_identidad(matriz, inversa, "derecha"),
        _comprobar_identidad(inversa, matriz, "izquierda"),
    )
    if not all(comprobacion["coincide"] for comprobacion in comprobaciones):
        return _resultado_verificacion(matriz, construccion)
    resultado.update(inversa=inversa, comprobaciones=comprobaciones)
    resultado["traza"] = _traza(matriz, construccion, inversa, comprobaciones)
    return resultado


def _resultado_verificacion(
    matriz: Matriz, construccion: ConstruccionAdjunta
) -> ResultadoInversaAdjunta:
    mensaje = "La comprobacion exacta no coincide; no se certifica el resultado por adjunta."
    resultado = _crear_resultado(ERROR, CODIGO_VERIFICACION_INCONSISTENTE, mensaje, matriz.filas)
    resultado["nodos_cofactores"] = construccion["nodos"]
    return resultado


def _traza(
    matriz: Matriz,
    construccion: ConstruccionAdjunta,
    inversa: Matriz | None,
    comprobaciones: tuple[ComprobacionAdjunta, ...],
) -> tuple[PasoAdjunta, ...]:
    contexto: ContextoTrazaAdjunta = {
        "matriz_a": matriz.clonar(),
        "determinante": construccion["determinante"],
        "menores": construccion["menores"].clonar(),
        "cofactores": construccion["cofactores"].clonar(),
        "adjunta": construccion["adjunta"].clonar(),
        "inversa": inversa.clonar() if inversa is not None else None,
        "detalles": construccion["detalles"],
        "comprobaciones": comprobaciones,
        "fila_expansion": construccion["fila_expansion"],
    }
    return construir_traza_adjunta(contexto)


def _dividir_adjunta(adjunta: Matriz, determinante: Fraction) -> Matriz:
    return Matriz(
        adjunta.filas,
        adjunta.columnas,
        [[adjunta.obtener(fila, columna) / determinante for columna in range(adjunta.columnas)]
         for fila in range(adjunta.filas)],
    )


def _comprobar_a_adjunta(
    matriz: Matriz, adjunta: Matriz, determinante: Fraction
) -> ComprobacionAdjunta:
    dimension = matriz.filas
    esperado = Matriz(
        dimension,
        dimension,
        [[determinante if fila == columna else Fraction(0) for columna in range(dimension)]
         for fila in range(dimension)],
    )
    comprobacion = comprobar_producto(
        matriz, adjunta, esperado, r"A \cdot \operatorname{adj}(A) = \det(A) \cdot I"
    )
    return _convertir_comprobacion(comprobacion, "a_adjunta", "A · adj(A) = det(A) · I")


def _comprobar_identidad(
    izquierda: Matriz, derecha: Matriz, clave: str
) -> ComprobacionAdjunta:
    if clave == "derecha":
        etiqueta, descripcion = r"A \cdot A^{-1} = I", "A · A⁻¹ = I"
    else:
        etiqueta, descripcion = r"A^{-1} \cdot A = I", "A⁻¹ · A = I"
    comprobacion = comprobar_producto(izquierda, derecha, identidad(izquierda.filas), etiqueta)
    return _convertir_comprobacion(comprobacion, clave, descripcion)


def _convertir_comprobacion(
    comprobacion: dict, clave: str, descripcion: str
) -> ComprobacionAdjunta:
    traza = comprobacion.get("traza") or []
    detalle = traza[-1].get("detalle_latex") if traza else None
    return {
        "clave": clave,
        "descripcion": descripcion,
        "coincide": bool(comprobacion["coincide"]),
        "producto": comprobacion["producto"],
        "esperado": comprobacion["esperado"],
        "detalle_latex": detalle,
    }
