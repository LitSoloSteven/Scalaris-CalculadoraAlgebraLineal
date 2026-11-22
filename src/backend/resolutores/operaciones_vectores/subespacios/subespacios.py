"""Analisis exacto de subespacios descritos por generadores o por ecuaciones lineales."""
from fractions import Fraction
from types import MappingProxyType

from src.backend.constantes import SIN_SOLUCION
from src.backend.modelos.operaciones.construcciones import matriz_de_columnas
from src.backend.modelos.escalares.conversion_fracciones import convertir_fila_fracciones
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.solucion.calculo_solucion import (
    calcular_solucion_parametrica,
)
from src.backend.resolutores.sistemas_lineales.reduccion.clasificacion_sistema import (
    clasificar_sistema,
)
from src.backend.resolutores.sistemas_lineales.reduccion.reduccion import ReductorFilas
from .comprobacion_subespacios import (
    CONFIGURACION_EXACTA,
    comprobar_familia_exacta,
    construir_testigo_contradictorio,
    construir_testigo_origen,
    verificar_base_generadores,
)
from .contrato_subespacios import (
    MODO_GENERADORES,
    MODO_RESTRICCIONES,
    ContextoRestricciones,
    EntradaGeneradores,
    EntradaRestricciones,
    EntradaSubespacio,
    ErrorCapturaSubespacio,
    ErrorVerificacionSubespacio,
    MatrizInmutable,
    PasoSubespacio,
    ResultadoSubespacio,
    validar_entrada_subespacio,
)
from .resultado_subespacios import resultado_error, resultado_inicial

CODIGO_ENTRADA_INVALIDA = "ENTRADA_INVALIDA"
CODIGO_VERIFICACION = "VERIFICACION_INCONSISTENTE"
CODIGO_ERROR_INTERNO = "ERROR_INTERNO"
CLASIFICACION_SUBESPACIO = "SUBESPACIO"
CLASIFICACION_AFIN = "AFIN_NO_SUBESPACIO"
CLASIFICACION_VACIO = "VACIO_NO_SUBESPACIO"


def analizar_subespacio(
    entrada: EntradaSubespacio,
) -> ResultadoSubespacio:
    """Analiza generadores o restricciones con racionales exactos y devuelve el contrato completo."""
    try:
        validar_entrada_subespacio(entrada)
    except ErrorCapturaSubespacio as error:
        return resultado_error(entrada, CODIGO_ENTRADA_INVALIDA, str(error))
    try:
        if entrada["modo"] == MODO_GENERADORES:
            return _analizar_generadores(entrada)
        return _analizar_restricciones(entrada)
    except ErrorCapturaSubespacio as error:
        return resultado_error(entrada, CODIGO_ENTRADA_INVALIDA, str(error))
    except ErrorVerificacionSubespacio as error:
        return resultado_error(entrada, CODIGO_VERIFICACION, str(error))
    except (AssertionError, ValueError, ArithmeticError) as error:
        return resultado_error(
            entrada,
            CODIGO_ERROR_INTERNO,
            f"Error interno al analizar el conjunto: {type(error).__name__}: {error}",
        )


def _analizar_generadores(entrada: EntradaGeneradores) -> ResultadoSubespacio:
    generadores = tuple(entrada["generadores"])
    matriz = _matriz_exacta(matriz_de_columnas(list(generadores)))
    reduccion, pasos = _reducir(matriz, matriz.columnas)
    rango = reduccion["rango"]
    pivotes = tuple(reduccion["columnas_pivote"])
    base = tuple(_columna(matriz, columna) for columna in pivotes)
    etiquetas = tuple(entrada["etiquetas"][columna] for columna in pivotes)
    resultado = resultado_inicial(MODO_GENERADORES, entrada["dimension_ambiente"])
    resultado.update({
        "codigo": "SUBESPACIO_GENERADO",
        "mensaje": _mensaje_generadores(rango, len(generadores)),
        "clasificacion": CLASIFICACION_SUBESPACIO,
        "es_subespacio": True,
        "contiene_origen": True,
        "es_vacio": False,
        "rango": rango,
        "base": base,
        "dimension": rango,
        "indices_generadores_base": pivotes,
        "etiquetas_generadores_base": etiquetas,
        "columnas_pivote": pivotes,
        "columnas_libres": tuple(
            columna for columna in range(len(generadores)) if columna not in pivotes
        ),
        "matriz_original": matriz,
        "matriz_reducida": reduccion["matriz_reducida"],
        "pasos": pasos,
        "comprobaciones": verificar_base_generadores(
            generadores, base, pivotes, reduccion["matriz_reducida"]
        ),
    })
    return resultado


def _analizar_restricciones(entrada: EntradaRestricciones) -> ResultadoSubespacio:
    matriz_a = _matriz_exacta(entrada["matriz_a"])
    vector_b = tuple(Fraction(valor) for valor in entrada["vector_b"])
    aumentada = _aumentada(matriz_a, vector_b)
    reduccion, pasos = _reducir(aumentada, matriz_a.columnas)
    rango = reduccion["rango"]
    pivotes = tuple(reduccion["columnas_pivote"])
    contexto: ContextoRestricciones = {
        "entrada": entrada,
        "matriz_a": matriz_a,
        "vector_b": vector_b,
        "aumentada": aumentada,
        "reduccion": reduccion,
        "pasos": pasos,
        "rango": rango,
        "pivotes": pivotes,
        "libres": tuple(
            columna for columna in range(matriz_a.columnas) if columna not in pivotes
        ),
    }
    estado, _ = clasificar_sistema(
        reduccion["matriz_reducida"], matriz_a.columnas, rango, 0
    )
    if estado == SIN_SOLUCION:
        return _resultado_incompatible(contexto)
    parametros = calcular_solucion_parametrica(
        reduccion["matriz_reducida"], list(pivotes), matriz_a.columnas
    )
    comprobaciones = comprobar_familia_exacta(matriz_a, vector_b, parametros, contexto["libres"])
    if all(valor == 0 for valor in vector_b):
        return _resultado_homogeneo(contexto, parametros, comprobaciones)
    return _resultado_afin(contexto, parametros, comprobaciones)


def _reducir(matriz: Matriz, numero_variables: int) -> tuple[dict, tuple[PasoSubespacio, ...]]:
    eventos: list[PasoSubespacio] = []
    reduccion = ReductorFilas(
        matriz, numero_variables, CONFIGURACION_EXACTA, _crear_registro(eventos)
    ).reducir()
    return reduccion, tuple(eventos)


def _crear_registro(eventos: list[PasoSubespacio]):
    def _registrar(tipo: str, matriz: Matriz, datos: dict) -> None:
        eventos.append(MappingProxyType({
            "tipo": tipo,
            "datos": MappingProxyType(dict(datos)),
            "matriz": MatrizInmutable(matriz.filas, matriz.columnas, matriz.datos),
        }))

    return _registrar


def _aumentada(matriz_a: Matriz, vector_b: tuple[Fraction, ...]) -> Matriz:
    return Matriz(
        matriz_a.filas,
        matriz_a.columnas + 1,
        [list(fila) + [termino] for fila, termino in zip(matriz_a.datos, vector_b)],
    )


def _matriz_exacta(matriz: Matriz) -> Matriz:
    return Matriz(
        matriz.filas, matriz.columnas,
        [convertir_fila_fracciones(fila) for fila in matriz.datos],
    )


def _resultado_incompatible(contexto: ContextoRestricciones) -> ResultadoSubespacio:
    rango = contexto["rango"]
    testigo = construir_testigo_contradictorio(
        contexto["reduccion"]["matriz_reducida"], contexto["matriz_a"].columnas
    )
    resultado = resultado_inicial(
        MODO_RESTRICCIONES, contexto["entrada"]["dimension_ambiente"]
    )
    resultado.update({
        "codigo": "SISTEMA_INCOMPATIBLE",
        "mensaje": "El sistema no tiene solucion: el conjunto es vacio y no es un subespacio.",
        "clasificacion": CLASIFICACION_VACIO,
        "es_subespacio": False,
        "contiene_origen": False,
        "es_vacio": True,
        "rango": rango,
        "rango_aumentada": rango + 1,
        "columnas_pivote": contexto["pivotes"],
        "columnas_libres": contexto["libres"],
        "testigo": testigo,
        "matriz_original": contexto["aumentada"],
        "matriz_reducida": contexto["reduccion"]["matriz_reducida"],
        "pasos": contexto["pasos"],
        "comprobaciones": ({
            "tipo": "rango_aumentado",
            "coincide": True,
            "detalle": (
                f"El rango aumentado es {rango + 1} y supera en uno al rango de A."
            ),
        },),
    })
    return resultado


def _resultado_homogeneo(
    contexto: ContextoRestricciones, parametros: dict, comprobaciones: tuple[dict, ...]
) -> ResultadoSubespacio:
    direcciones = _direcciones(parametros)
    numero_variables = contexto["matriz_a"].columnas
    resultado = resultado_inicial(
        MODO_RESTRICCIONES, contexto["entrada"]["dimension_ambiente"]
    )
    resultado.update({
        "codigo": "NUCLEO_HOMOGENEO",
        "mensaje": _mensaje_homogeneo(contexto["rango"], numero_variables),
        "clasificacion": CLASIFICACION_SUBESPACIO,
        "es_subespacio": True,
        "contiene_origen": True,
        "es_vacio": False,
        "rango": contexto["rango"],
        "rango_aumentada": contexto["rango"],
        "base": direcciones,
        "dimension": numero_variables - contexto["rango"],
        "columnas_pivote": contexto["pivotes"],
        "columnas_libres": contexto["libres"],
        "particular": _vector(parametros["particular"]),
        "direcciones": direcciones,
        "matriz_original": contexto["aumentada"],
        "matriz_reducida": contexto["reduccion"]["matriz_reducida"],
        "pasos": contexto["pasos"],
        "comprobaciones": comprobaciones,
    })
    return resultado


def _resultado_afin(
    contexto: ContextoRestricciones, parametros: dict, comprobaciones: tuple[dict, ...]
) -> ResultadoSubespacio:
    numero_variables = contexto["matriz_a"].columnas
    resultado = resultado_inicial(
        MODO_RESTRICCIONES, contexto["entrada"]["dimension_ambiente"]
    )
    resultado.update({
        "codigo": "AFIN_NO_CONTIENE_ORIGEN",
        "mensaje": (
            "El sistema es compatible y b no es cero: el conjunto es afin y no contiene al origen."
        ),
        "clasificacion": CLASIFICACION_AFIN,
        "es_subespacio": False,
        "contiene_origen": False,
        "es_vacio": False,
        "rango": contexto["rango"],
        "rango_aumentada": contexto["rango"],
        "particular": _vector(parametros["particular"]),
        "direcciones": _direcciones(parametros),
        "dimension_afin": numero_variables - contexto["rango"],
        "columnas_pivote": contexto["pivotes"],
        "columnas_libres": contexto["libres"],
        "testigo": construir_testigo_origen(contexto["matriz_a"], contexto["vector_b"]),
        "matriz_original": contexto["aumentada"],
        "matriz_reducida": contexto["reduccion"]["matriz_reducida"],
        "pasos": contexto["pasos"],
        "comprobaciones": comprobaciones,
    })
    return resultado


def _mensaje_generadores(rango: int, cantidad: int) -> str:
    if rango == 0:
        return f"Los {cantidad} generadores describen el subespacio cero de dimension 0."
    return f"Los {cantidad} generadores describen un subespacio de dimension {rango}."


def _mensaje_homogeneo(rango: int, numero_variables: int) -> str:
    if rango == numero_variables:
        return "El sistema homogeneo solo tiene la solucion trivial: el subespacio es {0}."
    return (
        "El sistema homogeneo describe un subespacio de dimension "
        f"{numero_variables - rango}."
    )


def _direcciones(parametros: dict) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(_vector(direccion) for direccion in parametros["direcciones"])


def _vector(valores) -> tuple[Fraction, ...]:
    return tuple(Fraction(valor) for valor in valores)


def _columna(matriz: Matriz, columna: int) -> tuple[Fraction, ...]:
    return tuple(Fraction(matriz.obtener(fila, columna)) for fila in range(matriz.filas))
