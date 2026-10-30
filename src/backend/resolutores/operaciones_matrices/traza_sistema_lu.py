"""Presentacion de las operaciones ya calculadas al resolver un sistema con LU."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import numero_a_latex
from .comprobacion_productos import crear_paso_analisis
from .formateadores import matriz_a_latex
from .sustitucion_lu import DatosFilaSustitucion


def crear_traza_sistema_lu(permutada: Matriz, filas_inferiores: list[DatosFilaSustitucion],
                           filas_superiores: list[DatosFilaSustitucion], solucion: list[Fraction]) -> list[dict]:
    """Devuelve la traza desde permutada, filas inferiores y superiores y solucion.
    Recibe el vector permutado como matriz columna y no recalcula las operaciones."""
    traza = [crear_paso_analisis("Planteamiento del sistema", r"PA=LU,\quad LUx=Pb,\quad Ly=Pb,\quad Ux=y",
                                 "Permutamos los terminos y resolvemos los dos sistemas triangulares.", "planteamiento"),
             crear_paso_analisis("Terminos permutados", f"Pb={matriz_a_latex(permutada)}", tipo="operacion")]
    traza.extend(_paso_sustitucion(fila, "y") for fila in filas_inferiores)
    traza.extend(_paso_sustitucion(fila, "x") for fila in filas_superiores)
    columna = Matriz(len(solucion), 1, [[valor] for valor in solucion])
    traza.append(crear_paso_analisis("Solucion del sistema", f"x={matriz_a_latex(columna)}", tipo="resultado"))
    return traza


def _paso_sustitucion(datos: DatosFilaSustitucion, variable: str) -> dict:
    indice = datos["fila"] + 1
    termino = numero_a_latex(datos["termino"])
    acumulado = numero_a_latex(datos["acumulado"])
    diagonal = numero_a_latex(datos["diagonal"])
    valor = numero_a_latex(datos["valor"])
    productos = " + ".join(f"({numero_a_latex(producto)})" for producto in datos["productos"]) or "0"
    detalle = rf"{variable}_{{{indice}}}=\frac{{{termino}-({productos})}}{{{diagonal}}}=\frac{{{termino}-({acumulado})}}{{{diagonal}}}={valor}"
    return crear_paso_analisis(f"Sustitucion para {variable}_{indice}", detalle, tipo="sustitucion")
