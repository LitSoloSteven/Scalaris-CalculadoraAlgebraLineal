"""Pruebas del solucionador y controlador de transformaciones lineales."""
import json
from fractions import Fraction
import pytest

from src.backend.models.matrix import Matrix
from src.backend.solvers.matrix_ops.transformations import LinearTransformationSolver
from src.frontend.controladores.operaciones_matrices.controlador_transformaciones import (
    ControladorTransformaciones,
)


def _matriz(datos: list[list]) -> Matrix:
    """Construye una matriz desde listas de valores."""
    m = len(datos)
    n = len(datos[0])
    return Matrix(m, n, [[Fraction(v) for v in fila] for fila in datos])


class TestTransformacionesIdentidad:
    """Transformación identidad: biyectiva en R²."""

    @pytest.fixture
    def resultado(self):
        solucionador = LinearTransformationSolver()
        matriz_a = _matriz([[1, 0], [0, 1]])
        return solucionador.resolver(matriz_a)

    def test_estado_exitoso(self, resultado):
        assert resultado["status"] == "SUCCESS"

    def test_rango_dos(self, resultado):
        assert resultado["rango"] == 2

    def test_nulidad_cero(self, resultado):
        assert resultado["nulidad"] == 0

    def test_inyectiva(self, resultado):
        assert resultado["es_inyectiva"] is True

    def test_sobreyectiva(self, resultado):
        assert resultado["es_sobreyectiva"] is True

    def test_nucleo_trivial(self, resultado):
        assert resultado["base_nucleo"] == []

    def test_imagen_dos_vectores(self, resultado):
        assert len(resultado["base_imagen"]) == 2

    def test_teorema_dimension(self, resultado):
        assert "2 + 0 = 2" in resultado["teorema_dimension"]


class TestTransformacionesProyeccion:
    """Proyección sobre eje x en R²."""

    @pytest.fixture
    def resultado(self):
        solucionador = LinearTransformationSolver()
        matriz_a = _matriz([[1, 0], [0, 0]])
        return solucionador.resolver(matriz_a)

    def test_rango_uno(self, resultado):
        assert resultado["rango"] == 1

    def test_nulidad_uno(self, resultado):
        assert resultado["nulidad"] == 1

    def test_no_inyectiva(self, resultado):
        assert resultado["es_inyectiva"] is False

    def test_nucleo_dimension_uno(self, resultado):
        assert len(resultado["base_nucleo"]) == 1

    def test_teorema_dimension(self, resultado):
        assert "1 + 1 = 2" in resultado["teorema_dimension"]

    def test_nucleo_vector_correcto(self, resultado):
        vector = resultado["base_nucleo"][0]["vector"]
        assert vector[0] == "0"
        assert vector[1] == "1"


class TestTransformacionesInclusion:
    """Inclusión R² a R³: inyectiva, no sobreyectiva."""

    @pytest.fixture
    def resultado(self):
        solucionador = LinearTransformationSolver()
        matriz_a = _matriz([[1, 0], [0, 1], [0, 0]])
        return solucionador.resolver(matriz_a)

    def test_rango_dos(self, resultado):
        assert resultado["rango"] == 2

    def test_nulidad_cero(self, resultado):
        assert resultado["nulidad"] == 0

    def test_inyectiva(self, resultado):
        assert resultado["es_inyectiva"] is True

    def test_no_sobreyectiva(self, resultado):
        assert resultado["es_sobreyectiva"] is False

    def test_dimensiones(self, resultado):
        assert resultado["m"] == 3
        assert resultado["n"] == 2

    def test_teorema_dimension(self, resultado):
        assert "2 + 0 = 2" in resultado["teorema_dimension"]


class TestTransformacionesProyeccionEspacio:
    """Proyección R³ a R²: sobreyectiva, no inyectiva."""

    @pytest.fixture
    def resultado(self):
        solucionador = LinearTransformationSolver()
        matriz_a = _matriz([[1, 0, 0], [0, 1, 0]])
        return solucionador.resolver(matriz_a)

    def test_rango_dos(self, resultado):
        assert resultado["rango"] == 2

    def test_nulidad_uno(self, resultado):
        assert resultado["nulidad"] == 1

    def test_no_inyectiva(self, resultado):
        assert resultado["es_inyectiva"] is False

    def test_sobreyectiva(self, resultado):
        assert resultado["es_sobreyectiva"] is True

    def test_teorema_dimension(self, resultado):
        assert "2 + 1 = 3" in resultado["teorema_dimension"]

    def test_nucleo_vector_canonica(self, resultado):
        vector = resultado["base_nucleo"][0]["vector"]
        assert vector[0] == "0"
        assert vector[1] == "0"
        assert vector[2] == "1"


class TestTransformacionesCasosEspeciales:
    """Casos especiales como matriz nula y rotación."""

    def test_transformacion_nula(self):
        solucionador = LinearTransformationSolver()
        matriz_a = _matriz([[0, 0], [0, 0]])
        resultado = solucionador.resolver(matriz_a)
        assert resultado["status"] == "SUCCESS"
        assert resultado["rango"] == 0
        assert resultado["nulidad"] == 2
        assert resultado["es_inyectiva"] is False
        assert resultado["es_sobreyectiva"] is False

    def test_aviso_convencion_presente(self):
        solucionador = LinearTransformationSolver()
        matriz_a = _matriz([[1, 0], [0, 1]])
        resultado = solucionador.resolver(matriz_a)
        assert "callout_convencion" in resultado
        assert len(resultado["callout_convencion"]) > 20


class TestControladorTransformaciones:
    """Pruebas del controlador de transformaciones lineales."""

    def test_identidad_dos_por_dos(self):
        carga = json.dumps({"A": [["1", "0"], ["0", "1"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["status"] == "SUCCESS"
        assert respuesta["rango"] == 2
        assert respuesta["nulidad"] == 0

    def test_proyeccion(self):
        carga = json.dumps({"A": [["1", "0"], ["0", "0"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["status"] == "SUCCESS"
        assert respuesta["rango"] == 1
        assert respuesta["nulidad"] == 1

    def test_payload_sin_matriz(self):
        respuesta = json.loads(ControladorTransformaciones.procesar(json.dumps({})))
        assert respuesta["status"] == "ERROR"

    def test_json_invalido(self):
        respuesta = json.loads(ControladorTransformaciones.procesar("{bad"))
        assert respuesta["status"] == "ERROR"

    def test_celda_invalida(self):
        carga = json.dumps({"A": [["xyz", "0"], ["0", "1"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["status"] == "ERROR"

    def test_nombres_variables_propagados(self):
        carga = json.dumps({
            "A": [["1", "0"], ["0", "1"]],
            "variables": ["u", "v"],
        })
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["status"] == "SUCCESS"

    def test_dimensiones_rectangulares(self):
        carga = json.dumps({"A": [["1", "0"], ["0", "1"], ["0", "0"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["status"] == "SUCCESS"
        assert respuesta["m"] == 3
        assert respuesta["n"] == 2

    def test_aviso_en_respuesta(self):
        carga = json.dumps({"A": [["1", "0"], ["0", "1"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert "callout_convencion" in respuesta

    def test_conclusiones_biyectividad(self):
        carga = json.dumps({"A": [["1", "0"], ["0", "1"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        conclusiones = respuesta.get("conclusiones", {})
        assert "biyectividad" in conclusiones
        assert conclusiones["biyectividad"] is not None
        assert "BIYECTIVA" in conclusiones["biyectividad"]

    def test_base_nucleo_correcto(self):
        carga = json.dumps({"A": [["1", "0"], ["0", "0"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        nucleo = respuesta.get("base_nucleo", [])
        assert len(nucleo) == 1
        vector = nucleo[0]["vector"]
        assert vector[0] == "0"
        assert vector[1] == "1"

    def test_rotacion_noventa_grados(self):
        carga = json.dumps({"A": [["0", "-1"], ["1", "0"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["status"] == "SUCCESS"
        assert respuesta["rango"] == 2
        assert respuesta["nulidad"] == 0
        assert respuesta["es_inyectiva"] is True
        assert respuesta["es_sobreyectiva"] is True
