"""Contratos del formato compartido por las tablas de resultados."""
from unittest.mock import Mock

import pytest

from src.frontend.componentes.raices.resultados.tabla_iteraciones import (
    columnas_iteraciones,
    presentar_tabla_iteraciones,
)
from src.frontend.vistas.sistemas_numericos.compartido._plantillas_numericas import renderizar_tabla


def test_columnas_numericas_y_textuales_conservan_orden_y_encabezados():
    """Alinea métricas a la derecha y descripciones a la izquierda."""
    etiquetas = (("i", "i"), ("residuo", "|f(c)|"), ("accion_examen", "Acción"))

    assert columnas_iteraciones(etiquetas) == [
        {"name": "i", "label": "i", "field": "i", "align": "right"},
        {"name": "residuo", "label": "|f(c)|", "field": "residuo", "align": "right"},
        {"name": "accion_examen", "label": "Acción", "field": "accion_examen", "align": "left"},
    ]


@pytest.mark.parametrize("paginacion_propia", [True, False])
def test_traza_vacia_se_muestra_con_ambos_tipos_de_paginacion(paginacion_propia):
    """La paginación externa oculta los controles nativos y conserva el mensaje vacío."""
    tabla = Mock()
    tabla.classes.return_value = tabla
    presentar_tabla_iteraciones(tabla, paginacion_propia=paginacion_propia)
    tabla.classes.assert_called_once_with("tabla-resultados w-full")

    propiedades = [llamada.args[0] for llamada in tabla.props.call_args_list]
    assert 'no-data-label="El cálculo no generó iteraciones."' in propiedades[0]
    assert all("hide-bottom" not in valor for valor in propiedades)
    assert ("hide-pagination hide-selected-banner" in propiedades) is paginacion_propia


def test_tabla_numerica_vacia_conserva_encabezados_y_pie():
    """El estado abarca las columnas y conserva escapado el título."""
    pie = "<tfoot><tr><td>0</td></tr></tfoot>"
    tabla = renderizar_tabla(("Valor < 0", "Base"), [], pie)

    assert "<th scope='col'>Valor &lt; 0</th>" in tabla
    assert '<td colspan="2" class="tabla-resultados-vacia">' in tabla
    assert "Este cálculo no generó filas para mostrar." in tabla
    assert pie in tabla


def test_tabla_numerica_conserva_numero_largo_completo():
    """La tabla recibe el contenido con todos los dígitos en su orden original."""
    numero = "1234567890" * 15
    tabla = renderizar_tabla(("Valor exacto",), [f"<tr><td>{numero}</td></tr>"])

    assert f"<td>{numero}</td>" in tabla
    assert "tabla-resultados-vacia" not in tabla
