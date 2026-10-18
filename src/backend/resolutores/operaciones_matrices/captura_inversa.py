"""Validación y formateo de comprobaciones formales para cálculo de inversa."""
from fractions import Fraction

from src.backend.constantes import (
    DIMENSION_MAXIMA_INVERSA,
    DIMENSION_MAXIMA_LATEX_INVERSA,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from .celdas_exactas import parsear_celda_exacta
from .opciones_resultado import OpcionesResultadoVacio


def construir_resultado_vacio(estado: str, mensaje: str, opciones: OpcionesResultadoVacio | None = None) -> dict:
    """Construye un resultado vacío homogéneo para errores y matrices singulares."""
    configuracion = opciones if opciones is not None else {}
    dimension = configuracion.get('dimension', 0)
    tiempo_s = configuracion.get('tiempo_s', 0.0)
    determinante = configuracion.get('determinante', None)
    matriz_a = configuracion.get('matriz_a', None)
    celda_error = configuracion.get('celda_error', None)
    latex_a = (
        matriz_a_latex(matriz_a)
        if (matriz_a is not None and dimension <= DIMENSION_MAXIMA_LATEX_INVERSA)
        else None
    )
    return {
        "estado": estado,
        "mensaje": mensaje,
        "dimension": dimension,
        "tiempo_transcurrido_segundos": round(tiempo_s, 4),
        "determinante": determinante,
        "determinante_texto": formatear_fraccion_texto(determinante) if determinante is not None else None,
        "matriz_a": matriz_a,
        "matriz_a_latex": latex_a,
        "inversa": None,
        "inversa_latex": None,
        "pasos": [],
        "grupos": [],
        "estadisticas": {
            "total": 0,
            "pivotes": 0,
            "intercambios": 0,
            "eliminaciones": 0,
            "normalizaciones": 0,
        },
        "comprobaciones": [],
        "celda_error": celda_error,
    }


def _parsear_celdas_inversa(datos: list, dimension: int) -> tuple[list[list[Fraction]] | None, list[int] | None, str | None]:
    """Parsea cada celda a fracción exacta y reporta coordenadas del primer fallo."""
    matriz_parseada = []
    for i in range(dimension):
        fila = datos[i]
        if not isinstance(fila, list) or len(fila) != dimension:
            return None, None, f"La fila {i + 1} debe contener {dimension} columnas."
        fila_parseada = []
        for j in range(dimension):
            try:
                valor = parsear_celda_exacta(fila[j], f"Error en A[{i + 1},{j + 1}]", vacio_como_cero=True)
            except ValueError as error:
                return None, [i, j], str(error)
            fila_parseada.append(valor)
        matriz_parseada.append(fila_parseada)
    return matriz_parseada, None, None


def validar_y_parsear_matriz_cuadrada(datos_crudos: dict) -> tuple[Matriz | None, int, dict | None]:
    """Valida dimensión, estructura y contenido numérico de la matriz cuadrada."""
    dimension = datos_crudos.get("dimension")
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 1 or dimension > DIMENSION_MAXIMA_INVERSA:
        dim = dimension if (isinstance(dimension, int) and not isinstance(dimension, bool)) else 0
        mensaje = f"La dimensión n debe ser un entero entre 1 y {DIMENSION_MAXIMA_INVERSA}."
        return None, dim, construir_resultado_vacio("ERROR", mensaje, opciones={'dimension': dim})

    datos = datos_crudos.get("datos")
    if not isinstance(datos, list) or len(datos) != dimension:
        return None, dimension, construir_resultado_vacio("ERROR", f"Se esperaban {dimension} filas en la matriz.", opciones={'dimension': dimension})

    matriz_parseada, celda_error, mensaje_error = _parsear_celdas_inversa(datos, dimension)
    if mensaje_error is not None:
        return None, dimension, construir_resultado_vacio("ERROR", mensaje_error, opciones={'dimension': dimension, 'celda_error': celda_error})

    matriz_a = Matriz(dimension, dimension, matriz_parseada)
    return matriz_a, dimension, None


def extraer_comprobaciones_inversa(resultado: dict, dimension: int) -> list[dict]:
    """Extrae las tres propiedades de verificación formal para matrices invertibles."""
    verificaciones = []
    paso_derecha = resultado.get("paso_verificacion")
    if paso_derecha:
        latex_derecha = paso_derecha.get("detalle_latex") if dimension <= DIMENSION_MAXIMA_LATEX_INVERSA else None
        verificaciones.append({"clave": "derecha", "titulo": "A · A⁻¹ = I", "coincide": bool(paso_derecha.get("coincide")), "detalle_latex": latex_derecha})

    paso_izquierda = resultado.get("paso_verificacion_inverso")
    if paso_izquierda:
        latex_izquierda = paso_izquierda.get("detalle_latex") if dimension <= DIMENSION_MAXIMA_LATEX_INVERSA else None
        verificaciones.append({"clave": "izquierda", "titulo": "A⁻¹ · A = I", "coincide": bool(paso_izquierda.get("coincide")), "detalle_latex": latex_izquierda})

    paso_trans = resultado.get("paso_propiedad_transpuesta")
    if paso_trans:
        latex_trans = paso_trans.get("detalle_latex") if dimension <= DIMENSION_MAXIMA_LATEX_INVERSA else None
        verificaciones.append({"clave": "transpuesta", "titulo": "(Aᵀ)⁻¹ = (A⁻¹)ᵀ", "coincide": bool(paso_trans.get("coincide")), "detalle_latex": latex_trans})

    return verificaciones
