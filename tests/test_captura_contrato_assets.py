"""Contratos HTML y orden de carga de los adaptadores reales de captura."""
import json

import pytest

from src.frontend import tema
from src.frontend.componentes import cuadricula_base
from src.frontend.componentes.equation_grid import EquationGrid
from src.frontend.componentes.matrix_capture import MatrixCapturePanel
from src.frontend.componentes.square_matrix_panel import SquareMatrixPanel
from src.frontend.componentes.vector_capture import VectorCapturePanel
from tests.comun import RAIZ


@pytest.mark.parametrize("fila,columna", [(0, 0), (2, 4)])
@pytest.mark.parametrize("identificador", [None, "A"])
def test_propiedades_celda_usan_un_solo_contrato_espanol(fila, columna, identificador):
    """Las coordenadas mantienen nombre accesible y pertenecen a su adaptador."""
    propiedades = cuadricula_base.props_celda_accesible(fila, columna, id_matriz=identificador, nombre_campo="celda")
    assert f'aria-label="Fila {fila + 1}, columna {columna + 1}"' in propiedades
    assert 'name="celda"' in propiedades
    assert 'borderless autocomplete="new-password"' in propiedades
    if identificador:
        assert f'data-matriz-identificador="{identificador}"' in propiedades
        assert f'data-matriz-fila="{fila}" data-matriz-columna="{columna}"' in propiedades
        assert 'data-ecuaciones-' not in propiedades
    else:
        assert f'data-ecuaciones-fila="{fila}" data-ecuaciones-columna="{columna}"' in propiedades
        assert 'data-matriz-' not in propiedades
    assert 'data-row=' not in propiedades
    assert 'data-col=' not in propiedades
    assert 'data-matrix-' not in propiedades


@pytest.mark.parametrize("componente,adaptador", [
    (EquationGrid, "captura_ecuaciones.js"),
    (MatrixCapturePanel, "captura_matrices.js"),
    (SquareMatrixPanel, "captura_matrices.js"),
    (VectorCapturePanel, "captura_vectores.js"),
])
def test_componentes_inyectan_su_adaptador_existente(monkeypatch, componente, adaptador):
    """Cada componente solicita un asset real después de la cabecera compartida."""
    etiquetas = []
    monkeypatch.setattr(cuadricula_base.ui, "add_head_html", etiquetas.append)
    componente.inject_scripts()
    assert f'<script src="/assets/js/{adaptador}"></script>' in etiquetas
    assert (RAIZ / "src/frontend/assets/js" / adaptador).is_file()


def test_cabecera_carga_dependencias_de_captura_en_orden():
    """El catálogo es la fuente común del orden y todos sus assets existen."""
    activos = RAIZ / "src/frontend/assets"
    nombres = json.loads((activos / "catalogo_captura.json").read_text(encoding="utf-8"))
    posiciones = [tema._CABECERA_HTML.index(f'/assets/js/{nombre}') for nombre in nombres]
    assert posiciones == sorted(posiciones)
    assert posiciones[0] > tema._CABECERA_HTML.index('/assets/js/cuadricula_compartida.js')
    assert posiciones[-1] < tema._CABECERA_HTML.index('/assets/js/recoleccion_basura.js')
    assert nombres == ["captura_celdas.js", "navegacion_captura.js", "pegado_captura.js", "foco_captura.js", "eventos_captura.js"]
    assert all((activos / "js" / nombre).is_file() for nombre in nombres)
