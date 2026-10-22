"""Comprobaciones exactas con desarrollo de cada celda del producto."""
from src.backend.modelos.calculo_matricial import multiplicar_matrices
from src.backend.modelos.matriz import Matriz
from .formateadores import matriz_a_latex
from .presentacion_producto import describir_producto_celda


def crear_paso_analisis(descripcion: str, detalle: str, explicacion: str = "", tipo: str = "operacion") -> dict:
    """Devuelve un paso matematico serializable para los reproductores existentes."""
    return {"descripcion": descripcion, "detalle_latex": detalle,
            "explicacion": explicacion or descripcion, "tipo": tipo}


def comprobar_producto(izquierda: Matriz, derecha: Matriz, esperado: Matriz, etiqueta: str) -> dict:
    """Calcula y desarrolla un producto y su igualdad exacta; ValueError ante dimensiones incompatibles."""
    producto = multiplicar_matrices(izquierda, derecha)
    return desarrollar_producto(izquierda, derecha, producto, esperado, etiqueta)


def desarrollar_producto(izquierda: Matriz, derecha: Matriz, producto: Matriz | None, esperado: Matriz, etiqueta: str) -> dict:
    """Desarrolla un producto ya calculado sin repetirlo; un resultado ausente no se certifica."""
    if not isinstance(producto, Matriz):
        traza = [crear_paso_analisis("No se pudo comprobar el producto", etiqueta,
                                    "Falta el producto calculado; no se certifica la igualdad.", "verificacion")]
        return {"coincide": False, "producto": None, "esperado": esperado, "traza": traza}
    coincide = producto.datos == esperado.datos
    traza = [crear_paso_analisis(f"Propiedad por comprobar: {etiqueta}", etiqueta,
                               "Calculamos el producto con los datos originales y lo comparamos exactamente con la matriz esperada.", "verificacion")]
    for fila in range(producto.filas):
        for columna in range(producto.columnas):
            _, detalle = describir_producto_celda(izquierda, derecha, fila, columna, producto.obtener(fila, columna))
            traza.append(crear_paso_analisis(f"{etiqueta}: fila {fila + 1}, columna {columna + 1}", detalle, tipo="verificacion"))
    comparacion = "=" if coincide else r"\ne"
    detalle = (rf"{matriz_a_latex(izquierda)}{matriz_a_latex(derecha)}"
               rf"={matriz_a_latex(producto)}{comparacion}{matriz_a_latex(esperado)}")
    traza.append(crear_paso_analisis(f"Comprobacion exacta de {etiqueta}: {'coincide' if coincide else 'no coincide'}",
                                     detalle, tipo="verificacion"))
    return {"coincide": coincide, "producto": producto, "esperado": esperado, "traza": traza}
