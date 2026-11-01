"""Contrato serializable de aplicación de una matriz a un vector columna."""
import json
from fractions import Fraction

from src.backend.constantes import DIMENSION_MAXIMA_MODELOS
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.captura_modelos import parsear_matriz_modelo
from src.backend.resolutores.operaciones_matrices.comprobacion_productos import comprobar_producto
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales
from src.frontend.controladores.utilidades import parsear_carga_json, serializar_matriz


class ControladorAplicacionTransformacion:
    """Adapta captura JSON al dominio y devuelve resultados y comprobación exacta."""

    @staticmethod
    def procesar(carga_json: str) -> str:
        """Recibe JSON con matriz por filas y vector_original por componentes.
        Devuelve aplicación serializada o estado ERROR ante una entrada inválida.
        """
        datos, error = parsear_carga_json(carga_json)
        if error:
            return error
        try:
            resultado = _aplicar_captura(datos)
        except ValueError as error:
            resultado = {"estado": "ERROR", "mensaje": str(error)}
        return json.dumps(resultado, ensure_ascii=False, allow_nan=False)


def _aplicar_captura(datos: dict) -> dict:
    datos_matriz = datos.get("matriz_transformacion")
    if not isinstance(datos_matriz, list) or not datos_matriz:
        raise ValueError("Falta la matriz A. Ingresa sus filas y columnas.")
    matriz = parsear_matriz_modelo(datos_matriz, "A")
    vector = _capturar_vector(datos.get("vector_original"))
    resultado = ResolutorTransformacionesLineales().aplicar(matriz, vector)
    if resultado.get("estado") != "EXITO":
        return resultado
    esperado = Matriz(matriz.filas, 1, [
        [Fraction(valor)] for valor in resultado["vector_transformado"]["exacta"]
    ])
    comprobacion = comprobar_producto(matriz, vector, esperado, "Av=y")
    return {
        **resultado,
        "matriz_a": serializar_matriz(matriz),
        "dimension_dominio": matriz.columnas,
        "dimension_codominio": matriz.filas,
        "verificacion": comprobacion["coincide"],
        "traza_comprobacion": comprobacion["traza"],
    }


def _capturar_vector(componentes: object) -> Matriz:
    if not isinstance(componentes, list) or not componentes:
        raise ValueError("Falta el vector original. Ingresa una lista de componentes.")
    if len(componentes) > DIMENSION_MAXIMA_MODELOS:
        raise ValueError(f"El vector original admite hasta {DIMENSION_MAXIMA_MODELOS} componentes.")
    return parsear_matriz_modelo([[componente] for componente in componentes], "v")
