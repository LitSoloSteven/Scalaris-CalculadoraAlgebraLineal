"""Pruebas del modelo de Leontief para el solucionador y controlador."""
from tests.comun_entradas import copiar_entrada_prueba
import json
from fractions import Fraction
import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.leontief import ResolutorModeloLeontief
from src.frontend.controladores.operaciones_matrices.controlador_leontief import (
    ControladorLeontief,
)


def _matriz(datos: list[list]) -> Matriz:
    """Construye una matriz desde listas de valores."""
    m = len(datos)
    n = len(datos[0])
    return Matriz(m, n, [[Fraction(v) for v in fila] for fila in datos])


class TestSolucionadorLeontiefBasico:
    """Modelo de dos sectores simple con solución exacta."""

    @pytest.fixture
    def solucionador(self):
        """Prepara el resolutor utilizado por las pruebas."""
        return ResolutorModeloLeontief()

    @pytest.fixture
    def modelo_dos_sectores(self, solucionador):
        """Procesa modelo dos sectores con los datos recibidos."""
        matriz_c = _matriz(copiar_entrada_prueba('consumo_leontief'))
        demanda = copiar_entrada_prueba('demanda_leontief')
        return solucionador.resolver(
            matriz_c, demanda, ["Agricultura", "Industria"]
        )

    def test_estado_exitoso(self, modelo_dos_sectores):
        """Verifica estado exitoso."""
        assert modelo_dos_sectores["estado"] == "EXITO"

    def test_cantidad_sectores(self, modelo_dos_sectores):
        """Verifica cantidad sectores."""
        assert modelo_dos_sectores["numero_sectores"] == 2

    def test_nombres_sectores(self, modelo_dos_sectores):
        """Verifica nombres sectores."""
        assert modelo_dos_sectores["nombres_sectores"] == ["Agricultura", "Industria"]

    def test_hawkins_simon_viable(self, modelo_dos_sectores):
        """Verifica hawkins simon viable."""
        assert modelo_dos_sectores["hawkins_simon"]["es_economicamente_viable"] is True

    def test_hawkins_simon_menores(self, modelo_dos_sectores):
        """Verifica hawkins simon menores."""
        menores = modelo_dos_sectores["hawkins_simon"]["menores_principales"]
        assert len(menores) == 2
        assert menores[0]["es_positivo"] is True
        assert menores[1]["es_positivo"] is True

    def test_vector_produccion_existente(self, modelo_dos_sectores):
        """Verifica vector produccion existente."""
        producciones = modelo_dos_sectores["vector_produccion"]
        assert len(producciones) == 2
        for produccion in producciones:
            assert produccion != "0"

    def test_analisis_sectorial_estructura(self, modelo_dos_sectores):
        """Verifica analisis sectorial estructura."""
        analisis = modelo_dos_sectores["analisis_sectorial"]
        assert len(analisis) == 2
        for fila in analisis:
            assert "sector" in fila
            assert "produccion_total" in fila
            assert "consumo_intermedio" in fila
            assert "demanda_final" in fila
            assert "valor_anadido" in fila

    def test_matrices_latex_presentes(self, modelo_dos_sectores):
        """Verifica matrices latex presentes."""
        assert "matriz_leontief_latex" in modelo_dos_sectores
        assert "matriz_multiplicador_latex" in modelo_dos_sectores
        assert "\\begin{bmatrix}" in modelo_dos_sectores["matriz_leontief_latex"]

    def test_sectores_predeterminados_sin_nombres(self, solucionador):
        """Verifica sectores predeterminados sin nombres."""
        matriz_c = _matriz(copiar_entrada_prueba('consumo_leontief'))
        demanda = copiar_entrada_prueba('demanda_leontief')
        resultado = solucionador.resolver(matriz_c, demanda)
        assert resultado["nombres_sectores"] == ["Sector 1", "Sector 2"]


class TestSolucionadorLeontiefInviable:
    """Modelo con condición de Hawkins-Simon insatisfecha."""

    @pytest.fixture
    def solucionador(self):
        """Prepara el resolutor utilizado por las pruebas."""
        return ResolutorModeloLeontief()

    @pytest.fixture
    def modelo_inviable(self, solucionador):
        """Procesa modelo inviable con los datos recibidos."""
        matriz_c = _matriz([
            [Fraction(4, 5), Fraction(1, 2)],
            [Fraction(3, 5), Fraction(9, 10)],
        ])
        demanda = [Fraction(50), Fraction(50)]
        return solucionador.resolver(matriz_c, demanda)

    def test_hawkins_simon_no_viable(self, modelo_inviable):
        """Verifica hawkins simon no viable."""
        if modelo_inviable["estado"] == "EXITO":
            assert modelo_inviable["hawkins_simon"]["es_economicamente_viable"] is False
        else:
            assert modelo_inviable["estado"] in ("SINGULAR", "EXITO")

    def test_mensaje_singular_o_inviable(self, modelo_inviable):
        """Verifica mensaje singular o inviable."""
        if modelo_inviable["estado"] == "SINGULAR":
            mensaje = modelo_inviable["mensaje"].lower()
            assert "singular" in mensaje or "viab" in mensaje


class TestSolucionadorLeontiefErrores:
    """Casos de error en el solucionador de Leontief."""

    def test_matriz_no_cuadrada(self):
        """Verifica matriz no cuadrada."""
        solucionador = ResolutorModeloLeontief()
        matriz_c = _matriz([[1, 0, 0], [0, 1, 0]])
        demanda = [Fraction(10), Fraction(10)]
        resultado = solucionador.resolver(matriz_c, demanda)
        assert resultado["estado"] == "ERROR"
        assert "cuadrada" in resultado["mensaje"].lower()

    def test_vector_dimension_incorrecta(self):
        """Verifica vector dimension incorrecta."""
        solucionador = ResolutorModeloLeontief()
        matriz_c = _matriz([[Fraction(1, 5), 0], [0, Fraction(1, 5)]])
        demanda = [Fraction(10)]
        resultado = solucionador.resolver(matriz_c, demanda)
        assert resultado["estado"] == "ERROR"

    def test_tres_sectores_viables(self):
        """Verifica tres sectores viables."""
        solucionador = ResolutorModeloLeontief()
        matriz_c = _matriz([
            [Fraction(1, 10), Fraction(2, 10), Fraction(1, 10)],
            [Fraction(2, 10), Fraction(3, 10), Fraction(2, 10)],
            [Fraction(1, 10), Fraction(1, 10), Fraction(3, 10)],
        ])
        demanda = [Fraction(100), Fraction(200), Fraction(150)]
        resultado = solucionador.resolver(
            matriz_c, demanda, ["Agro", "Industria", "Servicios"]
        )
        assert resultado["estado"] == "EXITO"
        assert resultado["hawkins_simon"]["es_economicamente_viable"] is True
        assert len(resultado["analisis_sectorial"]) == 3


class TestControladorLeontief:
    """Pruebas del controlador del modelo de Leontief."""

    def test_carga_valido_dos_sectores(self):
        """Verifica carga valido dos sectores."""
        carga = json.dumps({
            "matriz_coeficientes": [["0.2", "0.3"], ["0.4", "0.1"]],
            "vector_demanda": ["120", "80"],
            "nombres_sectores": ["Agricultura", "Industria"],
        })
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["estado"] == "EXITO"
        assert respuesta["numero_sectores"] == 2

    def test_carga_sin_matriz_consumo(self):
        """Verifica carga sin matriz consumo."""
        carga = json.dumps({"vector_demanda": ["100", "200"]})
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["estado"] == "ERROR"

    def test_carga_sin_demanda(self):
        """Verifica carga sin demanda."""
        carga = json.dumps({"matriz_coeficientes": [["0.2", "0.3"], ["0.4", "0.1"]]})
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["estado"] == "ERROR"

    def test_json_invalido(self):
        """Verifica json invalido."""
        respuesta = json.loads(ControladorLeontief.procesar("{broken json"))
        assert respuesta["estado"] == "ERROR"

    def test_celda_invalida(self):
        """Verifica celda invalida."""
        carga = json.dumps({
            "matriz_coeficientes": [["abc", "0"], ["0", "0.1"]],
            "vector_demanda": ["100", "100"],
        })
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["estado"] == "ERROR"

    def test_procesar_exitoso(self):
        """Verifica procesar exitoso."""
        carga = json.dumps(copiar_entrada_prueba('captura_leontief'))
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert respuesta["estado"] == "EXITO"

    def test_hawkins_simon_en_respuesta(self):
        """Verifica hawkins simon en respuesta."""
        carga = json.dumps(copiar_entrada_prueba('captura_leontief'))
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        assert "hawkins_simon" in respuesta
        assert "es_economicamente_viable" in respuesta["hawkins_simon"]

    def test_analisis_sectorial_en_respuesta(self):
        """Verifica analisis sectorial en respuesta."""
        carga = json.dumps({
            "matriz_coeficientes": [["0.2", "0.3"], ["0.4", "0.1"]],
            "vector_demanda": ["120", "80"],
            "nombres_sectores": ["A", "B"],
        })
        respuesta = json.loads(ControladorLeontief.procesar(carga))
        analisis = respuesta.get("analisis_sectorial", [])
        assert len(analisis) == 2
        assert analisis[0]["sector"] == "A"
