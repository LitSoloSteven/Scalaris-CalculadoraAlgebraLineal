"""Pruebas para validación de payload y construcción de matrices aumentadas."""
from fractions import Fraction
import json

from src.frontend.controladores.sistemas_lineales import (
    validar_y_construir_aumentada,
)
from src.frontend.controladores.utilidades import parsear_payload


class TestParsearPayload:
    """Valida el análisis de sintaxis y tipado de payloads JSON."""

    def test_json_malformado_reporta_linea_y_columna(self):
        """Identifica errores sintácticos de JSON reportando línea y columna."""
        data, err = parsear_payload('{"a": }')
        assert data is None
        parsed = json.loads(err)
        assert parsed["status"] == "ERROR"
        assert "malformado" in parsed["message"].lower()

    def test_json_no_objeto_rechazado(self):
        """Rechaza estructuras JSON que no correspondan a un diccionario."""
        data, err = parsear_payload("[1, 2, 3]")
        assert data is None
        parsed = json.loads(err)
        assert parsed["status"] == "ERROR"
        assert "objeto JSON" in parsed["message"]

    def test_diccionario_valido_aceptado(self):
        """Acepta un diccionario válido conservando sus claves y contenido."""
        payload = json.dumps({"matrix_A": [[1]], "vector_b": [2]})
        data, err = parsear_payload(payload)
        assert err is None
        assert data == {"matrix_A": [[1]], "vector_b": [2]}


class TestValidarYConstruirAumentada:
    """Valida la consistencia dimensional y conversión exacta a fracciones."""

    def test_matriz_vacia_rechazada(self):
        """Rechaza matrices sin filas."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada(
            {"matrix_A": [], "vector_b": []}
        )
        assert matriz is None and A is None and b is None
        parsed = json.loads(err)
        assert "vacía" in parsed["message"]

    def test_fila_no_lista_rechazada(self):
        """Rechaza matrices cuyas filas no son listas."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada(
            {"matrix_A": ["no es lista"], "vector_b": [1]}
        )
        assert matriz is None
        parsed = json.loads(err)
        assert "lista de filas" in parsed["message"]

    def test_cero_columnas_rechazado(self):
        """Rechaza matrices con filas vacías de cero columnas."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada(
            {"matrix_A": [[]], "vector_b": [1]}
        )
        assert matriz is None
        parsed = json.loads(err)
        assert "0 columnas" in parsed["message"]

    def test_longitud_vector_b_incompatible_rechazada(self):
        """Rechaza vectores independientes que no coinciden en número de filas."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada({
            "matrix_A": [[1, 2], [3, 4]],
            "vector_b": [5],
        })
        assert matriz is None
        parsed = json.loads(err)
        assert "vector b tiene 1" in parsed["message"]
        assert "se esperaban 2" in parsed["message"]

    def test_celda_invalida_reporta_coordenadas(self):
        """Reporta la celda exacta de la matriz A que falló la conversión."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada({
            "matrix_A": [[1, "no_numerico"], [3, 4]],
            "vector_b": [5, 6],
        })
        assert matriz is None
        parsed = json.loads(err)
        assert "A[1,2]" in parsed["message"]

    def test_error_en_vector_b_reporta_indice(self):
        """Reporta el índice exacto de b que falló la conversión numérica."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada({
            "matrix_A": [[1, 2]],
            "vector_b": ["no_numerico"],
        })
        assert matriz is None
        parsed = json.loads(err)
        assert "b[1]" in parsed["message"]

    def test_denominador_mayor_a_mil_conservado(self):
        """Preserva fracciones exactas con denominadores superiores a 1000."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada({
            "matrix_A": [["1/1001"]],
            "vector_b": ["1"],
        })
        assert err is None
        assert A[0][0] == Fraction(1, 1001)
        assert b[0] == Fraction(1, 1)
        assert matriz.obtener(0, 0) == Fraction(1, 1001)
        assert matriz.obtener(0, 1) == Fraction(1, 1)

    def test_retorna_dimensiones_correctamente(self):
        """Calcula dimensiones m y n considerando la columna añadida para b."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada({
            "matrix_A": [[1, 2, 3], [4, 5, 6]],
            "vector_b": [7, 8],
        })
        assert err is None
        assert m == 2
        assert n == 3
        assert matriz.filas == 2
        assert matriz.columnas == 4

    def test_celdas_vacias_tratadas_como_cero(self):
        """Normaliza celdas vacías o nulas como fracciones de valor cero."""
        matriz, A, b, m, n, err = validar_y_construir_aumentada({
            "matrix_A": [[None, ""]],
            "vector_b": [5],
        })
        assert err is None
        assert A[0][0] == Fraction(0)
        assert A[0][1] == Fraction(0)
