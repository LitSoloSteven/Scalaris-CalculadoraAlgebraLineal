"""Pruebas de representación geométrica Plotly y temas para subespacios."""
import pytest

from src.frontend.controladores.algebra.operaciones_vectores.controlador_subespacios import (
    analizar_generadores_desde_captura,
    analizar_subespacio_desde_captura,
    ejemplo_generadores,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    NOTA_CONJUNTO_VACIO,
    NOTA_DIMENSION_SUPERIOR,
    NOTA_GRAFICA_NO_DISPONIBLE,
)
from src.frontend.presentacion.tema import (
    COLORES_SOLUCION_POR_TEMA,
    COLORES_TEXTO_GRAFICOS,
)
from src.frontend.vistas.geometria.figuras.figura_subespacios import (
    preparar_figura_subespacio,
)


def _analizar(vectores: dict[str, list[str]], dimension: int) -> dict:
    return analizar_generadores_desde_captura({
        "modo": "generadores",
        "dimension_ambiente": dimension,
        "vectores": {
            etiqueta: {"orientacion": "columna", "datos": componentes}
            for etiqueta, componentes in vectores.items()
        },
    })


@pytest.mark.parametrize(
    "dimension_ambiente,vectores,esperado_1d,dimension_esperada",
    [
        (1, {"v_1": ["0"]}, True, 0),
        (1, {"v_1": ["2"]}, True, 1),
        (2, {"v_1": ["0", "0"]}, False, 0),
        (2, {"v_1": ["1", "2"]}, False, 1),
        (2, {"v_1": ["1", "0"], "v_2": ["0", "1"]}, False, 2),
        (3, {"v_1": ["0", "0", "0"]}, False, 0),
        (3, {"v_1": ["1", "1", "1"]}, False, 1),
        (3, {"v_1": ["1", "0", "1"], "v_2": ["0", "1", "1"]}, False, 2),
        (3, {"v_1": ["1", "0", "0"], "v_2": ["0", "1", "0"], "v_3": ["0", "0", "1"]}, False, 3),
    ],
)
def test_figuras_cubren_dimensiones_uno_a_tres_con_roles_de_tema(
    dimension_ambiente, vectores, esperado_1d, dimension_esperada
):
    """Genera figuras válidas con descripción accesible y roles cromáticos en cada traza."""
    resultado = _analizar(vectores, dimension_ambiente)
    preparada = preparar_figura_subespacio(resultado, tema="papel")
    assert preparada.disponible is True
    assert preparada.es_1d is esperado_1d
    assert "origen" in preparada.descripcion.lower()
    assert f"dimensión {dimension_esperada}" in preparada.descripcion.lower()
    assert len(preparada.figura.data) >= 1
    for traza in preparada.figura.data:
        assert "scalaris_colores" in (traza.meta or {})
    if esperado_1d:
        assert preparada.figura.layout.yaxis.visible is False
    if dimension_ambiente == 3 and dimension_esperada == 3:
        nombres = [traza.name for traza in preparada.figura.data]
        assert "Ejes de ℝ³" in nombres
        assert all(etiqueta in nombres for etiqueta in ("v_1", "v_2", "v_3"))


@pytest.mark.parametrize("tema", ["papel", "marea", "medianoche"])
def test_figura_subespacio_aplica_paletas_de_los_tres_temas(tema):
    """Respeta el color de texto y de solución correspondiente al tema activo."""
    resultado = _analizar(ejemplo_generadores(), 3)
    preparada = preparar_figura_subespacio(resultado, tema=tema)
    assert preparada.disponible is True
    assert preparada.figura.layout.font.color == COLORES_TEXTO_GRAFICOS[tema]
    plano = next(traza for traza in preparada.figura.data if traza.name == "Plano generado")
    assert plano.colorscale[0][1] == COLORES_SOLUCION_POR_TEMA[tema]


def test_dimension_mayor_a_tres_omite_figura_con_nota_clara():
    """En dimensión mayor a 3 conserva el análisis exacto y explica el límite visual."""
    resultado = _analizar({"v_1": ["1", "0", "0", "0"]}, 4)
    preparada = preparar_figura_subespacio(resultado)
    assert preparada.disponible is False
    assert preparada.figura is None
    assert preparada.motivo_indisponible == NOTA_DIMENSION_SUPERIOR
    assert "origen" in preparada.descripcion.lower()


@pytest.mark.parametrize(
    "coordenada",
    ["1" + "0" * 30, f"1/{'1' + '0' * 30}"],
)
def test_coordenadas_extremas_conservan_base_y_explican_indisponibilidad(coordenada):
    """Ante coordenadas fuera de rango visual no falla y conserva el resultado algebraico."""
    resultado = _analizar({"v_1": ["1", coordenada, "0"]}, 3)
    assert resultado["estado"] == "EXITO"
    assert resultado["base"] == (("1", coordenada, "0"),)
    preparada = preparar_figura_subespacio(resultado)
    assert preparada.disponible is False
    assert preparada.figura is None
    assert preparada.motivo_indisponible == NOTA_GRAFICA_NO_DISPONIBLE


def _analizar_restricciones(ecuaciones: str, dimension: int) -> dict:
    return analizar_subespacio_desde_captura({
        "modo": "restricciones",
        "formato": "ecuaciones",
        "dimension_ambiente": dimension,
        "ecuaciones": ecuaciones,
    })


@pytest.mark.parametrize(("dimension", "ecuaciones", "esperado_1d", "traza_esperada"), [
    (1, "x1 = 2", True, "Punto particular p"),
    (2, "x = 1\ny = 2", False, "Punto particular p"),
    (2, "x + y = 1", False, "Recta afín"),
    (3, "x = 1\ny = 1\nz = 1", False, "Punto particular p"),
    (3, "x + y = 1\nz = 2", False, "Recta afín"),
    (3, "-x1 - x2 + x3 = 1", False, "Plano afín"),
])
def test_figuras_afines_cubren_dimensiones_uno_a_tres(
    dimension, ecuaciones, esperado_1d, traza_esperada
):
    """Dibuja conjuntos afines en 1D..3D indicando que el origen no pertenece a W."""
    resultado = _analizar_restricciones(ecuaciones, dimension)
    preparada = preparar_figura_subespacio(resultado, tema="papel")
    assert preparada.disponible is True
    assert preparada.es_1d is esperado_1d
    descripcion = preparada.descripcion.lower()
    assert "no contiene al origen" in descripcion or "no pasa por el origen" in descripcion
    nombres = [traza.name for traza in preparada.figura.data]
    assert "Origen (0) ∉ W" in nombres
    assert "Punto particular p" in nombres
    assert traza_esperada in nombres
    assert all("scalaris_colores" in (traza.meta or {}) for traza in preparada.figura.data)


@pytest.mark.parametrize("tema", ["papel", "marea", "medianoche"])
def test_figura_afin_aplica_paletas_de_los_tres_temas(tema):
    """El plano afín del ejemplo oficial adapta su color y texto a los tres temas."""
    resultado = _analizar_restricciones("-x1 - x2 + x3 = 1", 3)
    preparada = preparar_figura_subespacio(resultado, tema=tema)
    assert preparada.disponible is True
    assert preparada.figura.layout.font.color == COLORES_TEXTO_GRAFICOS[tema]
    plano = next(traza for traza in preparada.figura.data if traza.name == "Plano afín")
    assert plano.colorscale[0][1] == COLORES_SOLUCION_POR_TEMA[tema]


def test_figura_homogenea_desde_restricciones_y_conjunto_vacio():
    """Grafica núcleos homogéneos con origen en W y omite la gráfica en conjuntos vacíos."""
    recta = preparar_figura_subespacio(_analizar_restricciones("y = 0", 2), tema="marea")
    assert recta.disponible is True
    nombres_recta = [traza.name for traza in recta.figura.data]
    assert "Recta generada" in nombres_recta
    assert "d_1" in nombres_recta
    assert "Origen (0)" in nombres_recta

    plano = preparar_figura_subespacio(_analizar_restricciones("-x1 - x2 + x3 = 0", 3))
    assert plano.disponible is True
    assert any(traza.name == "Plano generado" for traza in plano.figura.data)

    vacio = preparar_figura_subespacio(_analizar_restricciones("x = 0\nx = 1", 2))
    assert vacio.disponible is False
    assert vacio.figura is None
    assert vacio.motivo_indisponible == NOTA_CONJUNTO_VACIO


def test_figura_afin_dimension_superior_y_coordenadas_extremas():
    """En ℝ⁴ o coordenadas extremas conserva p exacto y explica por qué no hay figura."""
    en_r4 = _analizar_restricciones("x1 = 1", 4)
    assert en_r4["particular"] == ("1", "0", "0", "0")
    preparada_r4 = preparar_figura_subespacio(en_r4)
    assert preparada_r4.disponible is False
    assert preparada_r4.motivo_indisponible == NOTA_DIMENSION_SUPERIOR

    extrema = _analizar_restricciones(f"x1 = 1{'0' * 30}", 2)
    assert extrema["particular"] == ("1" + "0" * 30, "0")
    preparada_ext = preparar_figura_subespacio(extrema)
    assert preparada_ext.disponible is False
    assert preparada_ext.motivo_indisponible == NOTA_GRAFICA_NO_DISPONIBLE
