"""Pruebas de representación geométrica Plotly y temas para subespacios."""
import pytest

from src.frontend.controladores.algebra.operaciones_vectores.controlador_subespacios import (
    analizar_generadores_desde_captura,
    ejemplo_generadores,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
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
