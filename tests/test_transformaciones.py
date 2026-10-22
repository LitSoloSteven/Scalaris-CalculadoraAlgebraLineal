"""Pruebas del solucionador y controlador de transformaciones lineales."""
import json
from fractions import Fraction
import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales
from src.frontend.controladores.operaciones_matrices.controlador_transformaciones import (
    ControladorTransformaciones,
)


def _matriz(datos: list[list]) -> Matriz:
    """Construye una matriz desde listas de valores."""
    m = len(datos)
    n = len(datos[0])
    return Matriz(m, n, [[Fraction(v) for v in fila] for fila in datos])


class TestTransformacionesIdentidad:
    """Transformación identidad: biyectiva en R²."""

    @pytest.fixture
    def resultado(self):
        """Prepara el resultado del escenario para las pruebas."""
        solucionador = ResolutorTransformacionesLineales()
        matriz_a = _matriz([[1, 0], [0, 1]])
        return solucionador.resolver(matriz_a)

    def test_estado_exitoso(self, resultado):
        """Verifica estado exitoso."""
        assert resultado["estado"] == "EXITO"

    def test_rango_dos(self, resultado):
        """Verifica rango dos."""
        assert resultado["rango"] == 2

    def test_nulidad_cero(self, resultado):
        """Verifica nulidad cero."""
        assert resultado["nulidad"] == 0

    def test_inyectiva(self, resultado):
        """Verifica inyectiva."""
        assert resultado["es_inyectiva"] is True

    def test_sobreyectiva(self, resultado):
        """Verifica sobreyectiva."""
        assert resultado["es_sobreyectiva"] is True

    def test_nucleo_trivial(self, resultado):
        """Verifica nucleo trivial."""
        assert resultado["base_nucleo"] == []

    def test_imagen_dos_vectores(self, resultado):
        """Verifica imagen dos vectores."""
        assert len(resultado["base_imagen"]) == 2

    def test_teorema_dimension(self, resultado):
        """Verifica teorema dimension."""
        assert "2 + 0 = 2" in resultado["teorema_dimension"]


class TestTransformacionesProyeccion:
    """Proyección sobre eje x en R²."""

    @pytest.fixture
    def resultado(self):
        """Prepara el resultado del escenario para las pruebas."""
        solucionador = ResolutorTransformacionesLineales()
        matriz_a = _matriz([[1, 0], [0, 0]])
        return solucionador.resolver(matriz_a)

    def test_rango_uno(self, resultado):
        """Verifica rango uno."""
        assert resultado["rango"] == 1

    def test_nulidad_uno(self, resultado):
        """Verifica nulidad uno."""
        assert resultado["nulidad"] == 1

    def test_no_inyectiva(self, resultado):
        """Verifica no inyectiva."""
        assert resultado["es_inyectiva"] is False

    def test_nucleo_dimension_uno(self, resultado):
        """Verifica nucleo dimension uno."""
        assert len(resultado["base_nucleo"]) == 1

    def test_teorema_dimension(self, resultado):
        """Verifica teorema dimension."""
        assert "1 + 1 = 2" in resultado["teorema_dimension"]

    def test_nucleo_vector_correcto(self, resultado):
        """Verifica nucleo vector correcto."""
        vector = resultado["base_nucleo"][0]["vector"]
        assert vector[0] == "0"
        assert vector[1] == "1"


class TestTransformacionesInclusion:
    """Inclusión R² a R³: inyectiva, no sobreyectiva."""

    @pytest.fixture
    def resultado(self):
        """Prepara el resultado del escenario para las pruebas."""
        solucionador = ResolutorTransformacionesLineales()
        matriz_a = _matriz([[1, 0], [0, 1], [0, 0]])
        return solucionador.resolver(matriz_a)

    def test_rango_dos(self, resultado):
        """Verifica rango dos."""
        assert resultado["rango"] == 2

    def test_nulidad_cero(self, resultado):
        """Verifica nulidad cero."""
        assert resultado["nulidad"] == 0

    def test_inyectiva(self, resultado):
        """Verifica inyectiva."""
        assert resultado["es_inyectiva"] is True

    def test_no_sobreyectiva(self, resultado):
        """Verifica no sobreyectiva."""
        assert resultado["es_sobreyectiva"] is False

    def test_dimensiones(self, resultado):
        """Verifica dimensiones."""
        assert resultado["dimension_codominio"] == 3
        assert resultado["dimension_dominio"] == 2

    def test_teorema_dimension(self, resultado):
        """Verifica teorema dimension."""
        assert "2 + 0 = 2" in resultado["teorema_dimension"]


class TestTransformacionesProyeccionEspacio:
    """Proyección R³ a R²: sobreyectiva, no inyectiva."""

    @pytest.fixture
    def resultado(self):
        """Prepara el resultado del escenario para las pruebas."""
        solucionador = ResolutorTransformacionesLineales()
        matriz_a = _matriz([[1, 0, 0], [0, 1, 0]])
        return solucionador.resolver(matriz_a)

    def test_rango_dos(self, resultado):
        """Verifica rango dos."""
        assert resultado["rango"] == 2

    def test_nulidad_uno(self, resultado):
        """Verifica nulidad uno."""
        assert resultado["nulidad"] == 1

    def test_no_inyectiva(self, resultado):
        """Verifica no inyectiva."""
        assert resultado["es_inyectiva"] is False

    def test_sobreyectiva(self, resultado):
        """Verifica sobreyectiva."""
        assert resultado["es_sobreyectiva"] is True

    def test_teorema_dimension(self, resultado):
        """Verifica teorema dimension."""
        assert "2 + 1 = 3" in resultado["teorema_dimension"]

    def test_nucleo_vector_canonica(self, resultado):
        """Verifica nucleo vector canonica."""
        vector = resultado["base_nucleo"][0]["vector"]
        assert vector[0] == "0"
        assert vector[1] == "0"
        assert vector[2] == "1"


class TestTransformacionesCasosEspeciales:
    """Casos especiales como matriz nula y rotación."""

    def test_transformacion_nula(self):
        """Verifica transformacion nula."""
        solucionador = ResolutorTransformacionesLineales()
        matriz_a = _matriz([[0, 0], [0, 0]])
        resultado = solucionador.resolver(matriz_a)
        assert resultado["estado"] == "EXITO"
        assert resultado["rango"] == 0
        assert resultado["nulidad"] == 2
        assert resultado["es_inyectiva"] is False
        assert resultado["es_sobreyectiva"] is False

    def test_aviso_convencion_presente(self):
        """Verifica aviso convencion presente."""
        solucionador = ResolutorTransformacionesLineales()
        matriz_a = _matriz([[1, 0], [0, 1]])
        resultado = solucionador.resolver(matriz_a)
        assert "aviso_convencion" in resultado
        assert len(resultado["aviso_convencion"]) > 20


class TestControladorTransformaciones:
    """Pruebas del controlador de transformaciones lineales."""

    def test_identidad_dos_por_dos(self):
        """Verifica identidad dos por dos."""
        carga = json.dumps({"matriz_transformacion": [["1", "0"], ["0", "1"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["estado"] == "EXITO"
        assert respuesta["rango"] == 2
        assert respuesta["nulidad"] == 0

    def test_proyeccion(self):
        """Verifica proyeccion."""
        carga = json.dumps({"matriz_transformacion": [["1", "0"], ["0", "0"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["estado"] == "EXITO"
        assert respuesta["rango"] == 1
        assert respuesta["nulidad"] == 1

    def test_carga_sin_matriz(self):
        """Verifica carga sin matriz."""
        respuesta = json.loads(ControladorTransformaciones.procesar(json.dumps({})))
        assert respuesta["estado"] == "ERROR"

    def test_json_invalido(self):
        """Verifica json invalido."""
        respuesta = json.loads(ControladorTransformaciones.procesar("{bad"))
        assert respuesta["estado"] == "ERROR"

    def test_celda_invalida(self):
        """Verifica celda invalida."""
        carga = json.dumps({"matriz_transformacion": [["xyz", "0"], ["0", "1"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["estado"] == "ERROR"

    def test_nombres_variables_propagados(self):
        """Verifica nombres variables propagados."""
        carga = json.dumps({
            "matriz_transformacion": [["1", "0"], ["0", "1"]],
            "nombres_variables": ["u", "v"],
        })
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["estado"] == "EXITO"

    def test_dimensiones_rectangulares(self):
        """Verifica dimensiones rectangulares."""
        carga = json.dumps({"matriz_transformacion": [["1", "0"], ["0", "1"], ["0", "0"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["estado"] == "EXITO"
        assert respuesta["dimension_codominio"] == 3
        assert respuesta["dimension_dominio"] == 2

    def test_aviso_en_respuesta(self):
        """Verifica aviso en respuesta."""
        carga = json.dumps({"matriz_transformacion": [["1", "0"], ["0", "1"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert "aviso_convencion" in respuesta

    def test_conclusiones_biyectividad(self):
        """Verifica conclusiones biyectividad."""
        carga = json.dumps({"matriz_transformacion": [["1", "0"], ["0", "1"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        conclusiones = respuesta.get("conclusiones", {})
        assert "biyectividad" in conclusiones
        assert conclusiones["biyectividad"] is not None
        assert "BIYECTIVA" in conclusiones["biyectividad"]

    def test_base_nucleo_correcto(self):
        """Verifica base nucleo correcto."""
        carga = json.dumps({"matriz_transformacion": [["1", "0"], ["0", "0"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        nucleo = respuesta.get("base_nucleo", [])
        assert len(nucleo) == 1
        vector = nucleo[0]["vector"]
        assert vector[0] == "0"
        assert vector[1] == "1"

    def test_rotacion_noventa_grados(self):
        """Verifica rotacion noventa grados."""
        carga = json.dumps({"matriz_transformacion": [["0", "-1"], ["1", "0"]]})
        respuesta = json.loads(ControladorTransformaciones.procesar(carga))
        assert respuesta["estado"] == "EXITO"
        assert respuesta["rango"] == 2
        assert respuesta["nulidad"] == 0
        assert respuesta["es_inyectiva"] is True
        assert respuesta["es_sobreyectiva"] is True
