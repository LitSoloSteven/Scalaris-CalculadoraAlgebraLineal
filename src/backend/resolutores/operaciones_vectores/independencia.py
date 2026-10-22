"""Independencia lineal por el sistema homogeneo de las columnas capturadas."""
from src.backend.constantes import DIMENSION_MAXIMA_VECTORES
from src.backend.modelos.construcciones import matriz_de_columnas
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.homogeneos import resolver_homogeneo
from src.backend.resolutores.operaciones_matrices.comprobacion_productos import crear_paso_analisis
from src.backend.utilidades.formateadores import numero_a_latex


def analizar_independencia(vectores: list[Matriz]) -> dict:
    """Devuelve rango, conclusion y relaciones no triviales comprobadas; ValueError ante conjunto invalido."""
    _validar_vectores(vectores)
    homogeneo = resolver_homogeneo(matriz_de_columnas(vectores), "c")
    independiente = homogeneo["solo_trivial"]
    conclusion = "linealmente independientes" if independiente else "linealmente dependientes"
    relaciones = [_relacion(vector) for vector in homogeneo["direcciones"]]
    traza = [crear_paso_analisis("Sistema de coeficientes asociado", r"[v_1|\cdots|v_k]c=0", tipo="planteamiento")]
    traza.extend(homogeneo["traza"])
    traza.extend(crear_paso_analisis("Relacion de dependencia no trivial", relacion["formula"],
                                   "Los coeficientes no son todos cero. La sustitucion numerica se muestra en las comprobaciones Ad=0.",
                                   "resultado") for relacion in relaciones)
    return {**homogeneo, "operacion": "independencia", "mensaje": f"Los vectores son {conclusion}.",
            "es_independiente": independiente, "relaciones": relaciones, "traza": traza}


def _validar_vectores(vectores: list[Matriz]) -> None:
    if not isinstance(vectores, list):
        raise ValueError("Los vectores deben ser una lista de columnas.")
    validar_cantidad_vectores(len(vectores))
    if any(not isinstance(vector, Matriz) for vector in vectores):
        raise ValueError("Cada vector debe ser una Matriz columna.")
    dimension = vectores[0].filas
    if any(vector.columnas != 1 or vector.filas != dimension for vector in vectores):
        raise ValueError("Los vectores deben ser columnas de la misma dimension.")


def validar_cantidad_vectores(cantidad: int) -> None:
    """Rechaza con ValueError una cantidad fuera del limite comun de independencia."""
    if not 1 <= cantidad <= DIMENSION_MAXIMA_VECTORES:
        raise ValueError(f"Introduce entre 1 y {DIMENSION_MAXIMA_VECTORES} vectores.")


def _relacion(coeficientes: list) -> dict:
    formula = "+".join(rf"({numero_a_latex(valor)})v_{{{indice+1}}}" for indice, valor in enumerate(coeficientes))
    return {"coeficientes": list(coeficientes), "formula": formula + r"=\mathbf{0}"}
