"""Datos, escalas y límites de las figuras de aplicación de matrices."""
import json
from copy import deepcopy

import pytest

from src.frontend.controladores.operaciones_matrices.controlador_aplicacion_transformacion import ControladorAplicacionTransformacion
from src.frontend.tema import COLORES_TEXTO_GRAFICOS, PALETAS_POR_TEMA
from src.frontend.vistas.operaciones_matrices.figura_aplicacion_transformacion import preparar_escenas_aplicacion


def _aplicar(matriz, vector):
    return json.loads(ControladorAplicacionTransformacion.procesar(json.dumps({
        "matriz_transformacion": matriz, "vector_original": vector,
    })))


@pytest.mark.parametrize("tema", PALETAS_POR_TEMA)
@pytest.mark.parametrize("dimension", [2, 3])
@pytest.mark.parametrize("tipo", ["vector", "punto"])
def test_identidad_conserva_datos_tema_y_distincion_superpuesta(tema, dimension, tipo):
    """Las coincidencias mantienen dos símbolos, leyendas y etiquetas exactas."""
    matriz = [[int(fila == columna) for columna in range(dimension)] for fila in range(dimension)]
    resultado = _aplicar(matriz, ["1/3"] * dimension)
    anterior = deepcopy(resultado)
    escenas = preparar_escenas_aplicacion(resultado, tipo, tema=tema)["escenas"]
    assert len(escenas) == 1 and escenas[0]["titulo"] == f"Espacio compartido: R^{dimension}"
    figura = escenas[0]["figura"]
    original, transformado = figura.data
    assert original.marker.symbol == "circle-open" and transformado.marker.symbol == "diamond"
    assert original.line.dash == "solid" and transformado.line.dash == "dash"
    assert original.name == "Original" and transformado.name == "Transformado"
    assert original.mode == ("lines+markers" if tipo == "vector" else "markers")
    assert original.x[-1] == pytest.approx(1 / 3)
    assert "1/3" in original.customdata[-1]
    for indice, traza in enumerate(figura.data):
        assert traza.marker.color == PALETAS_POR_TEMA[tema][indice]
        assert traza.meta["scalaris_colores"]["line.color"] == f"serie:{indice}"
    assert figura.layout.font.color == COLORES_TEXTO_GRAFICOS[tema]
    assert resultado == anterior
    json.dumps(figura.to_plotly_json(), allow_nan=False)


@pytest.mark.parametrize("matriz,vector", [
    ([[1, 0], [0, 1], [1, 1]], [2, 3]),
    ([[1, 0, 0], [0, 1, 0]], [2, 3, 5]),
])
def test_rectangulares_separan_espacios_con_escala_comparable(matriz, vector):
    """Dominio y codominio no se superponen ni reciben componentes inventadas."""
    escenas = preparar_escenas_aplicacion(_aplicar(matriz, vector), "vector")["escenas"]
    assert len(escenas) == 2
    assert escenas[0]["titulo"] == f"Dominio: R^{len(vector)}"
    assert escenas[1]["titulo"] == f"Codominio: R^{len(matriz)}"
    rangos = []
    for escena in escenas:
        figura = escena["figura"]
        assert len(figura.data) == 1
        assert figura.layout.showlegend is True
        if figura.data[0].type == "scatter3d":
            assert figura.layout.scene.aspectmode == "cube"
            assert figura.layout.scene.zaxis.title.text == "x₃"
            rangos.append(figura.layout.scene.xaxis.range)
        else:
            assert figura.layout.xaxis.scaleanchor == "y"
            assert figura.layout.xaxis.title.text == "x₁"
            rangos.append(figura.layout.xaxis.range)
    assert rangos[0] == rangos[1] == (-6.25, 6.25)


@pytest.mark.parametrize("matriz,vector,esperado", [
    ([[0, -1], [1, 0]], [3, 2], [-2, 3]),
    ([[1, 0], [0, -1]], [3, 2], [3, -2]),
    ([[2, 1], [1, 3]], ["1/2", "1/3"], [4 / 3, 3 / 2]),
    ([[0, 0], [0, 0]], [0, 0], [0, 0]),
])
def test_posiciones_corresponden_al_producto_del_backend(matriz, vector, esperado):
    """Giro, reflexión, fracciones y cero usan los decimales entregados por el dominio."""
    figura = preparar_escenas_aplicacion(_aplicar(matriz, vector), "vector")["escenas"][0]["figura"]
    assert figura.data[1].x[-1] == pytest.approx(esperado[0])
    assert figura.data[1].y[-1] == pytest.approx(esperado[1])
    assert figura.layout.xaxis.range[0] < figura.layout.xaxis.range[1]
    assert figura.data[1].marker.size[-1] > 0


@pytest.mark.parametrize("valor", [None, float("inf"), float("nan"), 1e308, 0.0])
def test_coordenadas_no_dibujables_conservan_resultado_exacto(valor):
    """Desbordes y subdesbordes no se dibujan como cero ni generan JSON inválido."""
    resultado = _aplicar([[1, 0], [0, 1]], [1, 2])
    resultado["vector_transformado"]["aproximado"][0] = valor
    presentacion = preparar_escenas_aplicacion(resultado, "vector")
    assert not presentacion["escenas"]
    assert "representación numérica" in presentacion["mensaje"]
    assert resultado["vector_transformado"]["exacta"] == ["1", "2"]


@pytest.mark.parametrize("dimension", [1, 4, 8])
def test_dimensiones_fuera_de_escena_no_se_proyectan(dimension):
    """No trunca ni rellena dimensiones para fabricar una representación geométrica."""
    resultado = _aplicar([[1] * dimension] * 2, [1] * dimension)
    presentacion = preparar_escenas_aplicacion(resultado, "punto")
    assert not presentacion["escenas"] and "dimensión 2 o 3" in presentacion["mensaje"]


@pytest.mark.parametrize("resultado", [{"estado": "ERROR"}, {"estado": "EXITO", "verificacion": False}])
def test_omite_resultados_sin_comprobacion(resultado):
    """No crea una escena que sugiera éxito cuando el resultado no está comprobado."""
    assert not preparar_escenas_aplicacion(resultado, "vector")["escenas"]
