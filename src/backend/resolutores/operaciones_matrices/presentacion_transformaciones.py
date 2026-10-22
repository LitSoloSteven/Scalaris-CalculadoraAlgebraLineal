"""Presentacion de bases y propiedades de una transformacion ya reducida."""
from fractions import Fraction
from src.backend.constantes import EXITO
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from .comprobacion_transformaciones import comprobar_transformacion


def _base_nucleo(parametros: dict, nombres: list[str]) -> list[dict]:
    cantidad = len(parametros["columnas_libres"])
    return [{"parametro": f"t_{indice+1}" if cantidad > 1 else "t",
             "variable_libre": nombres[columna],
             "vector": [formatear_fraccion_texto(valor) for valor in direccion]}
            for indice, (columna, direccion) in enumerate(zip(parametros["columnas_libres"], parametros["direcciones"]))]


def _base_imagen(matriz: Matriz, pivotes: list[int]) -> list[dict]:
    return [{"indice_columna": columna + 1,
             "vector": [formatear_fraccion_texto(Fraction(matriz.obtener(fila, columna))) for fila in range(matriz.filas)]}
            for columna in pivotes]


def _conclusiones(inyectiva: bool, sobreyectiva: bool, nulidad: int, rango: int, ecuaciones: int) -> dict:
    texto_inyectiva = ("T es INYECTIVA: ker(T) = {0} (nulidad = 0)." if inyectiva
                      else f"T NO es inyectiva: ker(T) tiene dimensión {nulidad} > 0.")
    texto_sobreyectiva = (f"T es SOBREYECTIVA: Im(T) = R^{ecuaciones} (rango = {rango} = m)." if sobreyectiva
                         else f"T NO es sobreyectiva: Im(T) ⊊ R^{ecuaciones} (rango = {rango} < {ecuaciones}).")
    biyectividad = None
    if inyectiva and sobreyectiva:
        biyectividad = "T es BIYECTIVA (isomorfismo)."
    elif not inyectiva and not sobreyectiva:
        biyectividad = "T no es inyectiva ni sobreyectiva."
    return {"inyectividad": texto_inyectiva, "sobreyectividad": texto_sobreyectiva, "biyectividad": biyectividad}


def presentar_transformacion(matriz: Matriz, reduccion: dict, parametros: dict, nombres: list[str]) -> dict:
    """Devuelve el contrato de transformacion usando matriz original, reduccion, parametros y etiquetas."""
    rango = reduccion["rango"]
    nulidad = len(parametros["columnas_libres"])
    inyectiva, sobreyectiva = nulidad == 0, rango == matriz.filas
    return {
        "estado": EXITO,
        "traza_comprobacion": comprobar_transformacion(matriz, reduccion, parametros),
        "mensaje": f"Análisis de transformación lineal T: R^{matriz.columnas} → R^{matriz.filas} completado.",
        "dimension_codominio": matriz.filas, "dimension_dominio": matriz.columnas,
        "rango": rango, "nulidad": nulidad,
        "columnas_pivote": reduccion["columnas_pivote"], "columnas_libres": parametros["columnas_libres"],
        "es_inyectiva": inyectiva, "es_sobreyectiva": sobreyectiva,
        "base_nucleo": _base_nucleo(parametros, nombres),
        "base_imagen": _base_imagen(matriz, reduccion["columnas_pivote"]),
        "teorema_dimension": f"rango(T) + nulidad(T) = n  →  {rango} + {nulidad} = {matriz.columnas}  ✓",
        "conclusiones": _conclusiones(inyectiva, sobreyectiva, nulidad, rango, matriz.filas),
        "aviso_convencion": (
            "CONVENCIÓN ADOPTADA (columna estándar): la base de Im(T) está "
            "formada por las columnas pivote de A. Algunos textos usan la "
            "convención fila (vectores transpuestos); en ese caso la base "
            "visual difiere pero el espacio generado es el mismo."
        ),
        "pasos_reduccion": [{"descripcion": paso.get("descripcion", ""), "matriz": matriz_a_latex(paso["matriz"])}
                            for paso in reduccion["pasos"]],
    }
