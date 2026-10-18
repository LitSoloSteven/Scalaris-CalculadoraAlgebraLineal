"""Pruebas para validación de carga y construcción de matrices aumentadas."""
from src.backend.resolutores.sistemas_lineales.captura import validar_y_construir_aumentada
from fractions import Fraction
import json

from src.frontend.controladores.utilidades import parsear_carga_json


class TestParsearCarga:
    """Valida el análisis de sintaxis y tipado de cargas JSON."""

    def test_json_malformado_reporta_linea_y_columna(self):
        """Identifica errores sintácticos de JSON reportando línea y columna."""
        datos, error = parsear_carga_json('{"a": }')
        assert datos is None
        parseado = json.loads(error)
        assert parseado["estado"] == "ERROR"
        assert "malformado" in parseado["mensaje"].lower()

    def test_json_no_objeto_rechazado(self):
        """Rechaza estructuras JSON que no correspondan a un diccionario."""
        datos, error = parsear_carga_json("[1, 2, 3]")
        assert datos is None
        parseado = json.loads(error)
        assert parseado["estado"] == "ERROR"
        assert "objeto JSON" in parseado["mensaje"]

    def test_diccionario_valido_aceptado(self):
        """Acepta un diccionario válido conservando sus claves y contenido."""
        carga = json.dumps({"matriz_a": [[1]], "vector_b": [2]})
        datos, error = parsear_carga_json(carga)
        assert error is None
        assert datos == {"matriz_a": [[1]], "vector_b": [2]}


class TestValidarYConstruirAumentada:
    """Valida la consistencia dimensional y conversión exacta a fracciones."""

    def test_matriz_vacia_rechazada(self):
        """Rechaza matrices sin filas."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada(
            {"matriz_a": [], "vector_b": []}
        )
        assert matriz is None and A is None and b is None
        parseado = json.loads(error)
        assert "vacía" in parseado["mensaje"]

    def test_fila_no_lista_rechazada(self):
        """Rechaza matrices cuyas filas no son listas."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada(
            {"matriz_a": ["no es lista"], "vector_b": [1]}
        )
        assert matriz is None
        parseado = json.loads(error)
        assert "lista de filas" in parseado["mensaje"]

    def test_cero_columnas_rechazado(self):
        """Rechaza matrices con filas vacías de cero columnas."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada(
            {"matriz_a": [[]], "vector_b": [1]}
        )
        assert matriz is None
        parseado = json.loads(error)
        assert "0 columnas" in parseado["mensaje"]

    def test_longitud_vector_b_incompatible_rechazada(self):
        """Rechaza vectores independientes que no coinciden en número de filas."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada({
            "matriz_a": [[1, 2], [3, 4]],
            "vector_b": [5],
        })
        assert matriz is None
        parseado = json.loads(error)
        assert "vector b tiene 1" in parseado["mensaje"]
        assert "se esperaban 2" in parseado["mensaje"]

    def test_celda_invalida_reporta_coordenadas(self):
        """Reporta la celda exacta de la matriz A que falló la conversión."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada({
            "matriz_a": [[1, "no_numerico"], [3, 4]],
            "vector_b": [5, 6],
        })
        assert matriz is None
        parseado = json.loads(error)
        assert "A[1,2]" in parseado["mensaje"]

    def test_error_en_vector_b_reporta_indice(self):
        """Reporta el índice exacto de b que falló la conversión numérica."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada({
            "matriz_a": [[1, 2]],
            "vector_b": ["no_numerico"],
        })
        assert matriz is None
        parseado = json.loads(error)
        assert "b[1]" in parseado["mensaje"]

    def test_denominador_mayor_a_mil_conservado(self):
        """Preserva fracciones exactas con denominadores superiores a 1000."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada({
            "matriz_a": [["1/1001"]],
            "vector_b": ["1"],
        })
        assert error is None
        assert A[0][0] == Fraction(1, 1001)
        assert b[0] == Fraction(1, 1)
        assert matriz.obtener(0, 0) == Fraction(1, 1001)
        assert matriz.obtener(0, 1) == Fraction(1, 1)

    def test_retorna_dimensiones_correctamente(self):
        """Calcula dimensiones m y n considerando la columna añadida para b."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada({
            "matriz_a": [[1, 2, 3], [4, 5, 6]],
            "vector_b": [7, 8],
        })
        assert error is None
        assert m == 2
        assert n == 3
        assert matriz.filas == 2
        assert matriz.columnas == 4

    def test_celdas_vacias_tratadas_como_cero(self):
        """Normaliza celdas vacías o nulas como fracciones de valor cero."""
        matriz, A, b, m, n, error = validar_y_construir_aumentada({
            "matriz_a": [[None, ""]],
            "vector_b": [5],
        })
        assert error is None
        assert A[0][0] == Fraction(0)
        assert A[0][1] == Fraction(0)
