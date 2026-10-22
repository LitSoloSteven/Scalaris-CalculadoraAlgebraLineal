"""Comprobacion del nucleo y de la generacion de la imagen desde la reduccion existente."""
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.construcciones import identidad
from src.backend.resolutores.sistemas_lineales.comprobacion_sistemas import comprobar_familia
from .comprobacion_productos import comprobar_producto, crear_paso_analisis
from .formateadores import matriz_a_latex


def comprobar_transformacion(matriz: Matriz, reduccion: dict, parametros: dict) -> list[dict]:
    """Desarrolla Ax=0 y A=B R con B columnas pivote originales y R filas pivote reducidas."""
    cantidad = len(parametros["direcciones"])
    nombres = [f"t_{indice+1}" if cantidad > 1 else "t" for indice in range(cantidad)]
    familia = comprobar_familia(matriz.datos, [0] * matriz.filas, dict(parametros, nombres_parametros=nombres))
    traza = [crear_paso_analisis("Identidad del nucleo", r"x\in\ker(T)\iff Ax=0",
                                "Sustituimos la familia obtenida; cada coeficiente de parametro debe ser cero.", "verificacion")]
    traza.extend(crear_paso_analisis(f"Nucleo: ecuacion {indice+1}", detalle, tipo="verificacion")
                 for indice, detalle in enumerate(familia["pasos_latex"]))
    pivotes = reduccion["columnas_pivote"]
    if pivotes:
        base = Matriz(matriz.filas, len(pivotes), [[fila[columna] for columna in pivotes] for fila in matriz.datos])
        coordenadas = Matriz(len(pivotes), matriz.columnas, [fila[:matriz.columnas] for fila in reduccion["matriz_reducida"].datos[:len(pivotes)]])
        traza.extend(comprobar_producto(base, coordenadas, matriz, "A=BR")["traza"])
    else:
        traza.append(crear_paso_analisis("Imagen nula", rf"A={matriz_a_latex(matriz)}=0\implies\operatorname{{Im}}(T)=\{{0\}}", tipo="verificacion"))
    traza.extend(_comprobar_columnas_imagen(matriz, pivotes))
    traza.append(crear_paso_analisis("Dimension y propiedades", rf"r+n_0={len(pivotes)}+{cantidad}={matriz.columnas}",
                                   f"Hay {len(pivotes)} pivotes distintos y {cantidad} variables libres. Las columnas pivote son independientes y A=BR muestra que generan todas las columnas. "
                                   f"T es inyectiva si {cantidad}=0 y sobreyectiva si {len(pivotes)}={matriz.filas}. "
                                   "Esta conclusion usa la misma reduccion; no es una segunda eliminacion.", "verificacion"))
    return traza


def _comprobar_columnas_imagen(matriz: Matriz, pivotes: list[int]) -> list[dict]:
    canonica = identidad(matriz.columnas)
    traza = []
    for columna in pivotes:
        vector = Matriz(matriz.columnas, 1, [[fila[columna]] for fila in canonica.datos])
        imagen = Matriz(matriz.filas, 1, [[fila[columna]] for fila in matriz.datos])
        traza.extend(comprobar_producto(matriz, vector, imagen, f"T(e_{{{columna+1}}})=a_{{{columna+1}}}")["traza"])
    return traza
