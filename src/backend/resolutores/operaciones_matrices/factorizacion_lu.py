"""Factorizacion PA=LU por composicion con el reductor comun y pivoteo parcial."""
from fractions import Fraction
from math import isfinite
from typing import Any

from src.backend.constantes import DIMENSION_MAXIMA_MATRICES, DIMENSION_MINIMA, EXITO
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.construcciones import identidad
from src.backend.modelos.calculo_matricial import multiplicar_matrices
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.reduccion import ReductorFilas
from .pasos_determinante import RegistroPasosDeterminante
from .comprobacion_productos import comprobar_producto, crear_paso_analisis, desarrollar_producto
from .formateadores import matriz_a_latex
from .sustitucion_lu import sustituir_adelante, sustituir_atras
from .traza_sistema_lu import crear_traza_sistema_lu


class _RegistroFactorizacion:
    """Acumula factores sin recalcular ninguna operacion de eliminacion."""

    def __init__(self, filas: int) -> None:
        self.inferior = identidad(filas)
        self.permutacion = identidad(filas)
        self.registro = RegistroPasosDeterminante()

    def registrar(self, tipo: str, matriz: Matriz, datos: dict) -> None:
        """Recibe eventos y mantiene P y las columnas previas de L ante cada intercambio."""
        if tipo == "intercambio":
            fila, seleccionada = datos["fila"], datos["seleccionada"]
            self.permutacion.intercambiar_filas(fila, seleccionada)
            for columna in range(fila):
                self.inferior.datos[fila][columna], self.inferior.datos[seleccionada][columna] = (
                    self.inferior.datos[seleccionada][columna], self.inferior.datos[fila][columna])
        elif tipo == "eliminacion":
            self.inferior.datos[datos["fila"]][datos["fila_pivote"]] = datos["factor"]
        self.registro.registrar(tipo, matriz, datos)
        _agregar_instantaneas(self.registro.traza[-1], self.permutacion, self.inferior)


def factorizar_lu(matriz: Matriz) -> dict:
    """Devuelve P,L,U y verificacion exacta, incluso rectangular o singular; ValueError si excede limites."""
    if not isinstance(matriz, Matriz):
        raise ValueError("Se esperaba una Matriz para factorizar.")
    if max(matriz.filas, matriz.columnas) > DIMENSION_MAXIMA_MATRICES:
        raise ValueError(f"LU admite hasta {DIMENSION_MAXIMA_MATRICES} filas y columnas.")
    registro = _RegistroFactorizacion(matriz.filas)
    opciones = ConfiguracionReduccion(normalizar_pivotes=False, estrategia_pivote="parcial")
    reduccion = ReductorFilas(matriz, matriz.columnas, opciones, registro.registrar).reducir()
    superior = reduccion["matriz_reducida"]
    permutada = multiplicar_matrices(registro.permutacion, matriz)
    comprobacion = comprobar_producto(registro.inferior, superior, permutada, "LU=PA")
    desarrollo_permutacion = desarrollar_producto(registro.permutacion, matriz, permutada, permutada, "PA")["traza"]
    for paso in desarrollo_permutacion:
        paso.update(tipo="operacion", explicacion="Desarrollamos el producto PA ya calculado. Esta es la evaluacion del lado izquierdo, no una verificacion independiente.")
    desarrollo_permutacion[-1]["descripcion"] = "Producto PA calculado"
    traza = _presentar_factores(registro, superior)
    pasos_comprobacion = [dict(paso) for paso in comprobacion["traza"]]
    for paso in desarrollo_permutacion + pasos_comprobacion:
        _agregar_instantaneas(paso, registro.permutacion, registro.inferior)
    return {"estado": "EXITO", "mensaje": "Factorizacion PA = LU con pivoteo parcial.",
            "operacion": "factorizacion_lu", "convencion": "PA=LU", "rango": reduccion["rango"],
            "permutacion": registro.permutacion, "inferior": registro.inferior, "superior": superior,
            "formulas_resultado": [f"{nombre}={matriz_a_latex(factor)}" for nombre, factor in
                                   (("P", registro.permutacion), ("L", registro.inferior), ("U", superior))],
            "comprobacion": comprobacion, "traza": traza + desarrollo_permutacion + pasos_comprobacion}


def _presentar_factores(registro: _RegistroFactorizacion, superior: Matriz) -> list[dict]:
    traza = [crear_paso_analisis(
        "Convencion PA = LU", r"PA=LU",
        "P registra los intercambios; L es triangular inferior con diagonal 1; U es escalonada. "
        "La singularidad no impide esta factorizacion. Al intercambiar filas tambien permutamos los multiplicadores previos de L.",
        "planteamiento")]
    _agregar_instantaneas(traza[0], identidad(superior.filas), identidad(superior.filas))
    for paso in registro.registro.traza:
        presentado = crear_paso_analisis(paso["descripcion"], matriz_a_latex(paso["matriz"]),
                                        f"{paso['descripcion']}. Conservamos los multiplicadores de eliminacion en L.", paso["tipo"])
        _agregar_instantaneas(presentado, paso["permutacion"], paso["inferior"])
        traza.append(presentado)
    for nombre, matriz in (("P", registro.permutacion), ("L", registro.inferior), ("U", superior)):
        traza.append(crear_paso_analisis(f"Factor {nombre}", f"{nombre}={matriz_a_latex(matriz)}", tipo="resultado"))
        _agregar_instantaneas(traza[-1], registro.permutacion, registro.inferior)
    return traza


def _agregar_instantaneas(paso: dict, permutacion: Matriz, inferior: Matriz) -> None:
    paso.update(permutacion=permutacion.clonar(), inferior=inferior.clonar())


def _validar_sistema_lu(matriz: Matriz, terminos: list[Fraction]) -> None:
    """Valida la matriz y los términos antes de factorizar o resolver."""
    _validar_matriz(matriz)
    _validar_terminos(terminos, matriz.filas)


def _validar_matriz(matriz: Matriz) -> None:
    """Verifica tipo, forma cuadrada, dimensión y valores finitos de la matriz."""
    if not isinstance(matriz, Matriz):
        raise ValueError("La entrada no es una Matriz. Proporciona una matriz cuadrada.")
    if matriz.filas != matriz.columnas:
        raise ValueError("La matriz no es cuadrada. Proporciona una matriz con igual numero de filas y columnas.")
    if not DIMENSION_MINIMA <= matriz.filas <= DIMENSION_MAXIMA_MATRICES:
        raise ValueError(f"La dimension esta fuera del limite. Usa entre {DIMENSION_MINIMA} y {DIMENSION_MAXIMA_MATRICES} filas.")
    if _tiene_valores_no_finitos(matriz):
        raise ValueError("La matriz contiene valores no finitos. Usa numeros finitos en todas las celdas.")


def _tiene_valores_no_finitos(matriz: Matriz) -> bool:
    """Indica si alguna celda es un flotante no finito."""
    return any(isinstance(valor, float) and not isfinite(valor) for fila in matriz.datos for valor in fila)


def _validar_terminos(terminos: list[Fraction], filas: int) -> None:
    """Verifica que sea una lista de longitud adecuada y con tipos numéricos exactos."""
    if not isinstance(terminos, list) or len(terminos) != filas:
        raise ValueError("Los terminos no forman una lista de la longitud esperada. Proporciona un termino por fila.")
    if _tiene_terminos_invalidos(terminos):
        raise ValueError("Hay terminos de tipo no admitido. Usa enteros o fracciones exactas.")


def _tiene_terminos_invalidos(terminos: list[Fraction]) -> bool:
    """Indica si algún término es booleano o un tipo no admitido."""
    return any(isinstance(valor, bool) or not isinstance(valor, (int, Fraction)) for valor in terminos)


def resolver_sistema_lu(matriz: Matriz, terminos: list[Fraction]) -> dict[str, Any]:
    """Resuelve matriz por terminos sin mutarlos; devuelve factores, vectores y traza.
    Lanza ValueError ante entradas invalidas, fuera de limites o matriz singular."""
    _validar_sistema_lu(matriz, terminos)
    factores = factorizar_lu(matriz)
    if factores["rango"] < matriz.filas:
        raise ValueError("La matriz es singular y no permite una solucion unica. Usa una matriz invertible.")
    permutacion, inferior, superior = (factores[clave] for clave in ("permutacion", "inferior", "superior"))
    vector = Matriz(matriz.filas, 1, [[Fraction(valor)] for valor in terminos])
    permutada = multiplicar_matrices(permutacion, vector)
    intermedio, filas_inferiores = sustituir_adelante(inferior, [Fraction(fila[0]) for fila in permutada.datos])
    solucion, filas_superiores = sustituir_atras(superior, intermedio)
    traza = crear_traza_sistema_lu(permutada, filas_inferiores, filas_superiores, solucion)
    return {"estado": EXITO, "convencion": "PA=LU", "permutacion": permutacion, "inferior": inferior,
            "superior": superior, "intermedio": intermedio, "solucion": solucion, "traza": traza}
