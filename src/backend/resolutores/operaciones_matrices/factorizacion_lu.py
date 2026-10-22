"""Factorizacion PA=LU por composicion con el reductor comun y pivoteo parcial."""
from src.backend.constantes import DIMENSION_MAXIMA_MATRICES
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.construcciones import identidad
from src.backend.modelos.calculo_matricial import multiplicar_matrices
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.reduccion import ReductorFilas
from .pasos_determinante import RegistroPasosDeterminante
from .comprobacion_productos import comprobar_producto, crear_paso_analisis, desarrollar_producto
from .formateadores import matriz_a_latex


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
    return {"estado": "EXITO", "mensaje": "Factorizacion PA = LU con pivoteo parcial.",
            "operacion": "factorizacion_lu", "convencion": "PA=LU", "rango": reduccion["rango"],
            "permutacion": registro.permutacion, "inferior": registro.inferior, "superior": superior,
            "formulas_resultado": [f"{nombre}={matriz_a_latex(factor)}" for nombre, factor in
                                   (("P", registro.permutacion), ("L", registro.inferior), ("U", superior))],
            "comprobacion": comprobacion, "traza": traza + desarrollo_permutacion + comprobacion["traza"]}


def _presentar_factores(registro: _RegistroFactorizacion, superior: Matriz) -> list[dict]:
    traza = [crear_paso_analisis(
        "Convencion PA = LU", r"PA=LU",
        "P registra los intercambios; L es triangular inferior con diagonal 1; U es escalonada. "
        "La singularidad no impide esta factorizacion. Al intercambiar filas tambien permutamos los multiplicadores previos de L.",
        "planteamiento")]
    traza.extend(crear_paso_analisis(paso["descripcion"], matriz_a_latex(paso["matriz"]),
                                   f"{paso['descripcion']}. Conservamos los multiplicadores de eliminacion en L.", paso["tipo"])
                 for paso in registro.registro.traza)
    for nombre, matriz in (("P", registro.permutacion), ("L", registro.inferior), ("U", superior)):
        traza.append(crear_paso_analisis(f"Factor {nombre}", f"{nombre}={matriz_a_latex(matriz)}", tipo="resultado"))
    return traza
