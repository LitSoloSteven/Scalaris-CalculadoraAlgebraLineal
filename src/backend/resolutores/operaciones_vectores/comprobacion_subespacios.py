"""Comprobaciones exactas y testigos del analisis de subespacios."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.independencia import (
    analizar_independencia,
)
from src.backend.resolutores.sistemas_lineales.comprobacion_sistemas import (
    comprobar_familia,
)
from .contrato_subespacios import (
    ErrorVerificacionSubespacio,
    TestigoSubespacio,
)


def verificar_base_generadores(
    generadores: tuple[Matriz, ...],
    base: tuple[tuple[Fraction, ...], ...],
    indices: tuple[int, ...],
) -> tuple[dict, ...]:
    """Confirma que cada vector base es una columna original y que la familia es independiente."""
    if len(indices) != len(base) or len(set(indices)) != len(indices):
        raise ErrorVerificacionSubespacio(
            "Los indices de la base no son unicos ni corresponden uno a uno con sus vectores."
        )
    if any(not 0 <= indice < len(generadores) for indice in indices):
        raise ErrorVerificacionSubespacio(
            "La base referencia una columna de generador fuera de rango."
        )
    comprobaciones = []
    for indice, vector in zip(indices, base):
        columna = tuple(Fraction(generadores[indice].obtener(fila, 0))
                        for fila in range(generadores[indice].filas))
        if columna != vector:
            raise ErrorVerificacionSubespacio(
                f"La columna {indice} no coincide con el vector base seleccionado."
            )
        comprobaciones.append({
            "tipo": "columna_original",
            "indice": indice,
            "coincide": True,
            "detalle": f"La base usa la columna original {indice}.",
        })
    comprobaciones.append(_comprobacion_independencia(base))
    return tuple(comprobaciones)


def comprobar_familia_exacta(
    matriz_a: Matriz,
    vector_b: tuple[Fraction, ...],
    parametros: dict,
) -> tuple[dict, ...]:
    """Verifica A·p=b y A·d=0 para toda direccion; lanza error si alguna fila no coincide."""
    parametros_con_nombres = {
        **parametros,
        "nombres_parametros": [
            f"t_{indice + 1}" for indice in range(len(parametros["direcciones"]))
        ],
    }
    verificacion = comprobar_familia(matriz_a.datos, list(vector_b), parametros_con_nombres)
    if not verificacion["coincide"]:
        raise ErrorVerificacionSubespacio(
            "La familia propuesta no satisface todas las ecuaciones originales."
        )
    return tuple({
        "tipo": "familia",
        "fila": indice + 1,
        "coincide": fila["coincide"],
        "detalle_latex": fila["detalle_latex"],
    } for indice, fila in enumerate(verificacion["filas"]))


def construir_testigo_contradictorio(
    matriz_reducida: Matriz, numero_variables: int
) -> TestigoSubespacio:
    """Devuelve la primera fila reducida 0=c con c distinto de cero; error si no existe."""
    for indice, fila in enumerate(matriz_reducida.datos):
        coeficientes = tuple(Fraction(valor) for valor in fila[:numero_variables])
        termino = Fraction(fila[numero_variables])
        if all(valor == 0 for valor in coeficientes) and termino != 0:
            return {
                "tipo": "fila_contradictoria",
                "indice_fila": indice,
                "coeficientes": coeficientes,
                "termino_independiente": termino,
                "valor_izquierdo": Fraction(0),
                "descripcion": f"La fila {indice + 1} reducida queda 0 = {termino}.",
            }
    raise ErrorVerificacionSubespacio(
        "El sistema se clasifico como incompatible sin fila contradictoria."
    )


def construir_testigo_origen(
    matriz_a: Matriz, vector_b: tuple[Fraction, ...]
) -> TestigoSubespacio:
    """Devuelve una ecuacion original con b distinto de cero que el origen no satisface."""
    for indice, (fila, termino) in enumerate(zip(matriz_a.datos, vector_b)):
        if termino != 0:
            coeficientes = tuple(Fraction(valor) for valor in fila)
            izquierda = sum((coeficiente * 0 for coeficiente in coeficientes), Fraction(0))
            return {
                "tipo": "origen_no_pertenece",
                "indice_fila": indice,
                "coeficientes": coeficientes,
                "termino_independiente": Fraction(termino),
                "valor_izquierdo": izquierda,
                "descripcion": (
                    f"En el origen, la ecuacion {indice + 1} da {izquierda} = {termino}."
                ),
            }
    raise ErrorVerificacionSubespacio(
        "El conjunto afin no contiene al origen pero el vector b es nulo."
    )


def _comprobacion_independencia(
    base: tuple[tuple[Fraction, ...], ...]
) -> dict:
    if not base:
        return {
            "tipo": "independencia_base",
            "coincide": True,
            "detalle": "La base vacia describe el subespacio cero.",
        }
    vectores = [
        Matriz(len(vector), 1, [[valor] for valor in vector]) for vector in base
    ]
    analisis = analizar_independencia(vectores)
    if not analisis["es_independiente"]:
        raise ErrorVerificacionSubespacio(
            "La base seleccionada no es linealmente independiente."
        )
    return {
        "tipo": "independencia_base",
        "coincide": True,
        "detalle": analisis["mensaje"],
    }
