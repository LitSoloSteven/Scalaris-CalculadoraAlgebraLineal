"""Acoplamiento entre celdas reales de vectores y su adaptador JavaScript."""
import json
import shutil
import subprocess

import pytest
from nicegui import ui

from src.frontend.componentes.captura_vectores import PanelCapturaVectores
from tests.comun import RAIZ


def _observar_adaptador(propiedades):
    ejecutable = shutil.which("node")
    assert ejecutable, "Se necesita el runtime Node existente para comprobar el cliente."
    proceso = subprocess.run(
        [ejecutable, str(RAIZ / "tests/comun_contrato_captura.js")],
        input=json.dumps(propiedades), text=True, encoding="utf-8",
        capture_output=True, check=True, timeout=15,
    )
    return json.loads(proceso.stdout)


@pytest.mark.parametrize("orientacion,esperada", [("columna", "columna"), ("fila", "fila")])
def test_panel_vectorial_emite_el_contrato_que_ejecuta_su_adaptador(orientacion, esperada):
    """Enter y pegado funcionan sobre las propiedades reales, en ambos ejes."""
    panel = PanelCapturaVectores("p_add", opciones={'maximo_vectores': 2, 'orientacion_inicial': orientacion})
    contenedor = ui.column()
    try:
        with contenedor:
            panel.construir(contenedor)
        entradas = [elemento for elemento in panel.vectores["u"]["contenedor"].descendants() if isinstance(elemento, ui.input)]
        propiedades = [entrada._props for entrada in entradas]
        assert [datos["data-geometria-vector"] for datos in propiedades] == ["p_add_u"] * 3
        assert [datos["data-geometria-indice"] for datos in propiedades] == ["0", "1", "2"]
        assert [datos["data-geometria-orientacion"] for datos in propiedades] == [esperada] * 3
        observacion = _observar_adaptador(propiedades)
        assert observacion == {"destino": 1, "cancelaciones": [1, 1], "valores": ["1", "2", "3"], "eventos": [1, 1, 1]}
    finally:
        contenedor.delete()
