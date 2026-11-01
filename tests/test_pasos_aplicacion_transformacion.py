"""Secuencia matemática y agrupación del procedimiento de aplicación lineal."""
from copy import deepcopy
import json

import pytest

from src.frontend.controladores.operaciones_matrices.controlador_aplicacion_transformacion import ControladorAplicacionTransformacion
from src.frontend.vistas.operaciones_matrices.pasos_aplicacion_transformacion import adaptar_pasos_aplicacion


def _resolver(dominio, codominio):
    captura = {"matriz_transformacion": [["1/3"] * dominio for _ in range(codominio)],
               "vector_original": ["1/2"] * dominio, "tipo_objeto": "vector"}
    resultado = json.loads(ControladorAplicacionTransformacion.procesar(json.dumps(captura)))
    return captura, resultado


@pytest.mark.parametrize("dominio,codominio", [(2, 2), (3, 3), (2, 3), (3, 2), (1, 4), (8, 8)])
def test_conserva_formulas_fases_y_componente_de_cada_paso(dominio, codominio):
    """Cada fórmula original pertenece a una fase y a su componente sin recalcularla."""
    captura, resultado = _resolver(dominio, codominio)
    copia = deepcopy(resultado)
    pasos, grupos, componentes = adaptar_pasos_aplicacion(resultado, captura)
    assert len(pasos) == 2 * codominio + 3
    assert [grupo.titulo for grupo in grupos] == ["Planteamiento", "Aplicación por componentes", "Comprobación exacta"]
    assert grupos[0].indices_pasos == (0,)
    assert grupos[1].indices_pasos == tuple(range(1, codominio + 1))
    assert componentes == (None, *range(codominio), None, *range(codominio), None)
    originales = resultado["pasos"] + resultado["traza_comprobacion"]
    assert [paso.cuerpo.latex for paso in pasos[1:]] == [paso["detalle_latex"] for paso in originales]
    assert all(paso.meta_explicar is None for paso in pasos)
    assert pasos[-1].tipo == "verificacion" and "coincide" in pasos[-1].descripcion
    assert resultado == copia


@pytest.mark.parametrize("resultado", [{"estado": "ERROR"}, {"estado": "EXITO", "verificacion": False}])
def test_error_o_discrepancia_no_crea_un_procedimiento_certificado(resultado):
    """El adaptador no ofrece pasos de éxito para resultados sin igualdad verificada."""
    assert adaptar_pasos_aplicacion(resultado, {}) == ((), (), ())
