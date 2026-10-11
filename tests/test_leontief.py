"""Pruebas del modelo de Leontief para el solucionador y controlador."""
import json
from fractions import Fraction
import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.leontief import LeontiefSolver
from src.frontend.controladores.operaciones_matrices.controlador_leontief import (
    ControladorLeontief,
)


def _matriz(datos: list[list]) -> Matrix:
    """Construye una matriz desde listas de valores."""
    m = len(datos)
    n = len(datos[0])
    return Matrix(m, n, [[Fraction(v) for v in fila] for fila in datos])


class TestSolucionadorLeontiefBasico:
    """Modelo de dos sectores simple con solución exacta."""

    @pytest.fixture
    def solucionador(self):
        return LeontiefSolver()

    @pytest.fixture
    def modelo_dos_sectores(self, solucionador):
        matriz_c = _matriz([
            [Fraction(1, 5), Fraction(3, 10)],
            [Fraction(2, 5), Fraction(1, 10)],
        ])
        demanda = [Fraction(120), Fraction(80)]
        return solucionador.resolver(
            matriz_c, demanda, ["Agricultura", "Industria"]
        )

    def test_estado_exitoso(self, modelo_dos_sectores):
        assert modelo_dos_sectores["status"] == "SUCCESS"

    def test_cantidad_sectores(self, modelo_dos_sectores):
        assert modelo_dos_sectores["n"] == 2

    def test_nombres_sectores(self, modelo_dos_sectores):
        assert modelo_dos_sectores["sectores"] == ["Agricultura", "Industria"]

    def test_hawkins_simon_viable(self, modelo_dos_sectores):
        assert modelo_dos_sectores["hawkins_simon"]["viable"] is True

    def test_hawkins_simon_menores(self, modelo_dos_sectores):
        menores = modelo_dos_sectores["hawkins_simon"]["menores"]
        assert len(menores) == 2
        assert menores[0]["positivo"] is True
        assert menores[1]["positivo"] is True

    def test_vector_produccion_existente(self, modelo_dos_sectores):
        producciones = modelo_dos_sectores["vector_produccion"]
        assert len(producciones) == 2
        for produccion in producciones:
            assert produccion != "0"

    def test_analisis_sectorial_estructura(self, modelo_dos_sectores):
        analisis = modelo_dos_sectores["analisis_sectorial"]
        assert len(analisis) == 2
        for fila in analisis:
            assert "sector" in fila
            assert "produccion_total" in fila
            assert "insumos_intermedios" in fila
            assert "demanda_final" in fila
            assert "valor_anadido" in fila

    def test_matrices_latex_presentes(self, modelo_dos_sectores):
        assert "matriz_leontief_latex" in modelo_dos_sectores
        assert "matriz_multiplicador_latex" in modelo_dos_sectores
        assert "\\begin{bmatrix}" in modelo_dos_sectores["matriz_leontief_latex"]

    def test_sectores_predeterminados_sin_nombres(self, solucionador):
        matriz_c = _matriz([
            [Fraction(1, 5), Fraction(3, 10)],
            [Fraction(2, 5), Fraction(1, 10)],
        ])
        demanda = [Fraction(120), Fraction(80)]
        resultado = solucionador.resolver(matriz_c, demanda)
        assert resultado["sectores"] == ["Sector 1", "Sector 2"]


class TestSolucionadorLeontiefInviable:
    """Modelo con condición de Hawkins-Simon insatisfecha."""

    @pytest.fixture
    def solucionador(self):
        return LeontiefSolver()

    @pytest.fixture
    def modelo_inviable(self, solucionador):
        matriz_c = _matriz([
            [Fraction(4, 5), Fraction(1, 2)],
            [Fraction(3, 5), Fraction(9, 10)],
        ])
        demanda = [Fraction(50), Fraction(50)]
        return solucionador.resolver(matriz_c, demanda)

    def test_hawkins_simon_no_viable(self, modelo_inviable):
        if modelo_inviable["status"] == "SUCCESS":
            assert modelo_inviable["hawkins_simon"]["viable"] is False
        else:
            assert modelo_inviable["status"] in ("SINGULAR", "SUCCESS")

    def test_mensaje_singular_o_inviable(self, modelo_inviable):
        if modelo_inviable["status"] == "SINGULAR":
            mensaje = modelo_inviable["message"].lower()
            assert "singular" in mensaje or "viab" in mensaje


class TestSolucionadorLeontiefErrores:
    """Casos de error en el solucionador de Leontief."""

    def test_matriz_no_cuadrada(self):
        solucionador = LeontiefSolver()
        matriz_c = _matriz([[1, 0, 0], [0, 1, 0]])
        demanda = [Fraction(10), Fraction(10)]
        resultado = solucionador.resolver(matriz_c, demanda)
        assert resultado["status"] == "ERROR"
        assert "cuadrada" in resultado["message"].lower()

    def test_vector_dimension_incorrecta(self):
        solucionador = LeontiefSolver()
        matriz_c = _matriz([[Fraction(1, 5), 0], [0, Fraction(1, 5)]])
        demanda = [Fraction(10)]
        resultado = solucionador.resolver(matriz_c, demanda)
        assert resultado["status"] == "ERROR"

    def test_tres_sectores_viables(self):
        solucionador = LeontiefSolver()
        matriz_c = _matriz([
            [Fraction(1, 10), Fraction(2, 10), Fraction(1, 10)],
            [Fraction(2, 10), Fraction(3, 10), Fraction(2, 10)],
            [Fraction(1, 10), Fraction(1, 10), Fraction(3, 10)],
        ])
        demanda = [Fraction(100), Fraction(200), Fraction(150)]
        resultado = solucionador.resolver(
            matriz_c, demanda, ["Agro", "Industria", "Servicios"]
        )
        assert resultado["status"] == "SUCCESS"
        assert resultado["hawkins_simon"]["viable"] is True
        assert len(resultado["analisis_sectorial"]) == 3


class TestControladorLeontief:
    """Pruebas del controlador del modelo de Leontief."""

    def test_payload_valido_dos_sectores(self):
        carga = json.dumps({
            "C": [["0.2", "0.3"], ["0.4", "0.1"]],
            "d": ["120", "80"],
            "sectores": ["Agricultura", "Industria"],
        })
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["status"] == "SUCCESS"
        assert respuesta["n"] == 2

    def test_payload_sin_matriz_consumo(self):
        carga = json.dumps({"d": ["100", "200"]})
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["status"] == "ERROR"

    def test_payload_sin_demanda(self):
        carga = json.dumps({"C": [["0.2", "0.3"], ["0.4", "0.1"]]})
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["status"] == "ERROR"

    def test_json_invalido(self):
        respuesta = json.loads(ControladorLeontief.procesar("{broken json"))
        assert respuesta["status"] == "ERROR"

    def test_celda_invalida(self):
        carga = json.dumps({
            "C": [["abc", "0"], ["0", "0.1"]],
            "d": ["100", "100"],
        })
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["status"] == "ERROR"

    def test_procesar_exitoso(self):
        carga = json.dumps({
            "C": [["0.2", "0.3"], ["0.4", "0.1"]],
            "d": ["120", "80"],
        })
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["status"] == "SUCCESS"

    def test_hawkins_simon_en_respuesta(self):
        carga = json.dumps({
            "C": [["0.2", "0.3"], ["0.4", "0.1"]],
            "d": ["120", "80"],
        })
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert "hawkins_simon" in respuesta
        assert "viable" in respuesta["hawkins_simon"]

    def test_analisis_sectorial_en_respuesta(self):
        carga = json.dumps({
            "C": [["0.2", "0.3"], ["0.4", "0.1"]],
            "d": ["120", "80"],
            "sectores": ["A", "B"],
        })
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        analisis = respuesta.get("analisis_sectorial", [])
        assert len(analisis) == 2
        assert analisis[0]["sector"] == "A"
