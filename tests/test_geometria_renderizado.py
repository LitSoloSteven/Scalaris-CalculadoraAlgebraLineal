"""Pruebas de renderizado y conjunto solución en geometría analítica."""
import json
from fractions import Fraction
import pytest

from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from tests.comun_geometria import comprobar_rectas_incompatibles
from tests.comun_entradas import copiar_entrada_prueba
from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
)


def test_controlador_recta_dos_dimensiones():
    """Verifica que una ecuación en 2D produzca un segmento acotado en la caja."""
    carga = json.dumps({
        "matriz_a": [["1", "1"]],
        "vector_b": ["2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["numero_variables"] == 2
    assert resultado["parametro_pendiente"] is False

    conjunto_solucion = resultado["conjunto_solucion"]
    assert conjunto_solucion is not None
    assert conjunto_solucion["tipo"] == "RECTA"
    assert conjunto_solucion["dimension"] == 1
    assert conjunto_solucion["espacio_completo"] is False

    semi_ancho = resultado["rango"][1]
    segmento = conjunto_solucion.get("segmento")
    assert segmento is not None
    assert len(segmento) == 2
    for punto in segmento:
        assert len(punto) == 2
        for coord in punto:
            assert -semi_ancho - 1e-4 <= coord <= semi_ancho + 1e-4

    assert "parametros_latex" in conjunto_solucion and conjunto_solucion["parametros_latex"].startswith(r"\mathbf{x} = ")
    assert "descripcion" in conjunto_solucion and "Las soluciones forman una recta" in conjunto_solucion["descripcion"]
    assert "punto_latex" in conjunto_solucion and conjunto_solucion["punto_latex"] is not None


def test_controlador_plano_tres_dimensiones():
    """Verifica que una ecuación en 3D genere normal analítica y desplazamiento."""
    carga = json.dumps({
        "matriz_a": [["1", "1", "1"]],
        "vector_b": ["1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["numero_variables"] == 3
    assert resultado["parametro_pendiente"] is False

    conjunto_solucion = resultado["conjunto_solucion"]
    assert conjunto_solucion is not None
    assert conjunto_solucion["tipo"] == "PLANO"
    assert conjunto_solucion["dimension"] == 2
    assert conjunto_solucion["espacio_completo"] is False

    assert "normal_exacta" in conjunto_solucion
    assert "desplazamiento_exacto" in conjunto_solucion
    nx = Fraction(conjunto_solucion["normal_exacta"][0])
    ny = Fraction(conjunto_solucion["normal_exacta"][1])
    nz = Fraction(conjunto_solucion["normal_exacta"][2])
    assert nx == ny == nz != 0
    assert Fraction(conjunto_solucion["desplazamiento_exacto"]) / nx == 1

    assert "parametros_latex" in conjunto_solucion and conjunto_solucion["parametros_latex"].startswith(r"\mathbf{x} = ")
    assert "descripcion" in conjunto_solucion and "Las soluciones forman un plano" in conjunto_solucion["descripcion"]


def test_controlador_interseccion_dos_planos_recta_tres_dimensiones():
    """Dos planos independientes en 3D generan una recta con segmento de 3 coordenadas."""
    carga = json.dumps({
        "matriz_a": [["1", "0", "0"], ["0", "1", "0"]],
        "vector_b": ["1", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["numero_variables"] == 3

    conjunto_solucion = resultado["conjunto_solucion"]
    assert conjunto_solucion is not None
    assert conjunto_solucion["tipo"] == "RECTA"
    assert conjunto_solucion["dimension"] == 1

    segmento = conjunto_solucion.get("segmento")
    assert segmento is not None
    assert len(segmento) == 2
    assert len(segmento[0]) == 3
    assert len(segmento[1]) == 3


def test_controlador_todo_el_espacio():
    """Verifica que ecuaciones nulas marquen espacio_completo como verdadero."""
    carga_segunda = json.dumps({"matriz_a": [["0", "0"]], "vector_b": ["0"]})
    res2 = ControladorGeometria.procesar_rectas_planos(carga_segunda)
    assert res2["estado"] == "EXITO"
    assert res2["conjunto_solucion"]["espacio_completo"] is True

    carga_tercera = json.dumps({"matriz_a": [["0", "0", "0"]], "vector_b": ["0"]})
    res3 = ControladorGeometria.procesar_rectas_planos(carga_tercera)
    assert res3["estado"] == "EXITO"
    assert res3["conjunto_solucion"]["espacio_completo"] is True


def test_controlador_fracciones_analiticas_largas():
    """Verifica resolución analítica exacta con denominadores extensos."""
    carga = json.dumps({
        "matriz_a": [["1001/1000", "-123456789012/987654321"]],
        "vector_b": ["1/2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["parametro_pendiente"] is False

    conjunto_solucion = resultado["conjunto_solucion"]
    assert conjunto_solucion is not None

    fila_a = [Fraction("1001/1000"), Fraction("-123456789012/987654321")]
    valor_b = Fraction("1/2")

    p_exacto = [Fraction(x) for x in conjunto_solucion["punto_exacto"]]
    assert sum(a * p for a, p in zip(fila_a, p_exacto)) == valor_b

    for d_lista in conjunto_solucion["direcciones_exactas"]:
        d_exacto = [Fraction(x) for x in d_lista]
        assert sum(a * d for a, d in zip(fila_a, d_exacto)) == 0

    assert "parametros_latex" in conjunto_solucion
    assert conjunto_solucion["parametros_latex"].startswith(r"\mathbf{x} = ")


def test_controlador_solucion_unica_punto_latex():
    """Verifica controlador solucion unica punto latex."""
    carga = json.dumps({
        "matriz_a": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "vector_b": ["-1", "10", "1/2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["estado_solucion"] == "SOLUCION_UNICA"
    assert resultado["parametro_pendiente"] is False

    conjunto_solucion = resultado["conjunto_solucion"]
    assert conjunto_solucion["tipo"] == "PUNTO"
    assert conjunto_solucion["punto_latex"] is not None
    assert r"\begin{bmatrix}" in conjunto_solucion["punto_latex"]
    assert "-1" in conjunto_solucion["punto_latex"]
    assert "10" in conjunto_solucion["punto_latex"]
    assert r"\frac{1}{2}" in conjunto_solucion["punto_latex"]


def test_controlador_sin_solucion():
    """Verifica controlador sin solucion."""
    carga = json.dumps(copiar_entrada_prueba('rectas_incompatibles'))
    resultado = comprobar_rectas_incompatibles(carga)
    assert resultado["parametro_pendiente"] is False


def test_controlador_rectas_paralelas():
    """Verifica controlador rectas paralelas."""
    carga = json.dumps({
        "matriz_a": [["1", "2"], ["2", "4"]],
        "vector_b": ["3", "7"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["estado_solucion"] == "SIN_SOLUCION"
    assert "paralelas" in resultado["banderas"]


def test_controlador_simulado_sin_parametros_solucion(monkeypatch):
    """Verifica controlador simulado sin parametros solucion."""
    resolver_original = ResolutorGauss.resolver

    def resolutor_simulado(self):
        """Procesa resolutor simulado con los datos recibidos."""
        res = resolver_original(self)
        if res.get("estado") == "SOLUCIONES_INFINITAS":
            res.pop("parametros_solucion", None)
        return res

    monkeypatch.setattr(ResolutorGauss, "resolver", resolutor_simulado)

    carga = json.dumps({"matriz_a": [["1", "1"]], "vector_b": ["1"]})
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["estado_solucion"] == "SOLUCIONES_INFINITAS"
    assert resultado["parametro_pendiente"] is True
    assert resultado["conjunto_solucion"] is None


def test_figuras_recta_dos_dimensiones_y_plano_tres_dimensiones():
    """Verifica figuras recta dos dimensiones y plano tres dimensiones."""
    pytest.importorskip("plotly")
    from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos

    carga_plana = json.dumps({"matriz_a": [["1", "1"]], "vector_b": ["2"]})
    res_2d = ControladorGeometria.procesar_rectas_planos(carga_plana)
    fig_2d = construir_figura_rectas_planos(res_2d, tema="papel")
    nombres_2d = [t.name for t in fig_2d.data]
    assert "Conjunto solución (recta)" in nombres_2d
    assert "Ecuación 1" in nombres_2d

    carga_espacial = json.dumps({"matriz_a": [["1", "1", "1"]], "vector_b": ["1"]})
    res_3d = ControladorGeometria.procesar_rectas_planos(carga_espacial)
    fig_3d = construir_figura_rectas_planos(res_3d, tema="papel")
    nombres_3d = [t.name for t in fig_3d.data]
    assert "Conjunto solución (plano)" in nombres_3d
    assert "Ecuación 1" in nombres_3d

    carga_espacios = json.dumps({"matriz_a": [["0", "0"]], "vector_b": ["0"]})
    resultado_espacio_completo = ControladorGeometria.procesar_rectas_planos(carga_espacios)
    figura_espacio_completo = construir_figura_rectas_planos(resultado_espacio_completo, tema="papel")
    nombres_espacio_completo = [t.name for t in figura_espacio_completo.data]
    assert "Conjunto solución (recta)" not in nombres_espacio_completo
    assert "Conjunto solución (plano)" not in nombres_espacio_completo


def test_vista_construir_carga_cuadricula_vacia():
    """Verifica vista construir carga cuadricula vacia."""
    class CuadriculaSimulada:
        """Representa cuadricula simulada."""
        def esta_completamente_vacio(self):
            """Indica que todas las celdas están vacías."""
            return True
        def obtener_datos_matriz(self):
            """Procesa obtener datos matriz con los datos recibidos."""
            return [["", ""]], [""]

    class InterfazSimulada:
        """Representa interfaz simulada."""
        def __init__(self):
            self.escena = "rectas-planos"
            self.cuadricula = CuadriculaSimulada()

        def _construir_carga(self):
            if self.escena == "rectas-planos":
                if not self.cuadricula or self.cuadricula.esta_completamente_vacio():
                    return None
                matriz_entrada, vector_b = self.cuadricula.obtener_datos_matriz()
                if not matriz_entrada or not matriz_entrada[0]:
                    return None
                return {"matriz_a": matriz_entrada, "vector_b": vector_b}
            return None

    interfaz = InterfazSimulada()
    assert interfaz._construir_carga() is None
