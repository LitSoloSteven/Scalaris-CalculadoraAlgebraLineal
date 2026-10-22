"""Interpretacion y comprobacion de Ax=0 usando la solucion parametrica canonica."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS
from src.backend.utilidades.formateadores import formatear_variable_para_latex
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.operaciones_matrices.comprobacion_productos import comprobar_producto, crear_paso_analisis
from .gauss import ResolutorGauss
from .comprobacion_sistemas import comprobar_familia


def resolver_homogeneo(matriz: Matriz, simbolo: str = "x") -> dict:
    """Resuelve Ax=0 sin otro eliminador y entrega traza y verificaciones; ValueError si excede limites."""
    if not isinstance(matriz, Matriz):
        raise ValueError("Se esperaba una Matriz de coeficientes.")
    if max(matriz.filas, matriz.columnas) > DIMENSION_MAXIMA_SISTEMAS:
        raise ValueError(f"El sistema admite hasta {DIMENSION_MAXIMA_SISTEMAS} filas y columnas.")
    aumentada = Matriz(matriz.filas, matriz.columnas + 1, [fila + [Fraction(0)] for fila in matriz.datos])
    resultado = ResolutorGauss(aumentada).resolver()
    analisis = analizar_resultado_homogeneo(matriz, resultado, simbolo)
    eliminacion = [crear_paso_analisis(paso["descripcion"], matriz_a_latex(paso["matriz"]), tipo="eliminacion")
                   for paso in resultado["pasos"]]
    analisis["traza"] = eliminacion + analisis["traza"]
    return analisis


def analizar_resultado_homogeneo(matriz: Matriz, resultado: dict, simbolo: str = "x") -> dict:
    """Interpreta una solucion existente con b=0 y comprueba trivial y direcciones exactas."""
    if simbolo not in ("x", "c"):
        raise ValueError("El simbolo del sistema debe ser x o c.")
    parametros = resultado["parametros_solucion"]
    if any(parametros["particular"]):
        raise ValueError("El analisis homogeneo requiere terminos independientes iguales a cero.")
    direcciones = parametros["direcciones"]
    rango = matriz.columnas - len(direcciones)
    mensaje = (f"Solo existe la solucion trivial {simbolo}=0." if not direcciones else
               f"Hay familias parametricas no triviales, con {len(direcciones)} parametros libres.")
    traza = [crear_paso_analisis("Sistema homogeneo asociado", rf"{matriz_a_latex(matriz)}{simbolo}=0", tipo="planteamiento"),
             crear_paso_analisis(f"Rango {rango}; nulidad {len(direcciones)}", rf"\operatorname{{rg}}(A)={rango},\quad n-r={len(direcciones)}", mensaje)]
    formula = _formula_familia(parametros, simbolo)
    traza.append(crear_paso_analisis("Familia completa de soluciones", formula, mensaje, "resultado"))
    cero = [Fraction(0)] * matriz.columnas
    comprobaciones = [_comprobar_direccion(matriz, vector, indice) for indice, vector in enumerate([cero] + direcciones)]
    for comprobacion in comprobaciones:
        traza.extend(comprobacion["traza"])
    familia = comprobar_familia(matriz.datos, [Fraction(0)] * matriz.filas, parametros)
    traza.extend(crear_paso_analisis(f"Sustitucion simbolica en ecuacion {indice+1}", detalle,
                                   "Agrupamos el termino constante y cada parametro; todos sus coeficientes deben anularse.", "verificacion")
                 for indice, detalle in enumerate(familia["pasos_latex"]))
    return {"estado": "EXITO", "mensaje": mensaje, "rango": rango, "nulidad": len(direcciones),
            "solo_trivial": not direcciones, "direcciones": direcciones, "solucion_trivial": cero,
            "parametros_solucion": parametros, "formula_familia": formula, "comprobaciones": comprobaciones, "traza": traza}


def _formula_familia(parametros: dict, simbolo: str) -> str:
    direcciones = parametros["direcciones"]
    if not direcciones:
        return simbolo + r"=\mathbf{0}"
    nombres = [formatear_variable_para_latex(nombre) for nombre in parametros["nombres_parametros"]]
    terminos = [rf"{nombre}{matriz_a_latex(Matriz(len(vector), 1, [[valor] for valor in vector]))}"
                for nombre, vector in zip(nombres, direcciones)]
    return simbolo + "=" + "+".join(terminos) + r",\quad " + ",".join(nombres) + r"\in\mathbb{R}"


def _comprobar_direccion(matriz: Matriz, vector: list, indice: int) -> dict:
    columna = Matriz(len(vector), 1, [[valor] for valor in vector])
    cero = Matriz(matriz.filas, 1)
    etiqueta = "A0=0" if indice == 0 else f"Ad_{{{indice}}}=0"
    comprobacion = comprobar_producto(matriz, columna, cero, etiqueta)
    comprobacion["vector"] = list(vector)
    return comprobacion
