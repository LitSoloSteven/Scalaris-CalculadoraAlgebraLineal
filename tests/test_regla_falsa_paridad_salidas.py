"""Paridad de todos los pasos visibles con el resultado real de cada estado."""
import json

import pytest

from src.frontend.controladores.regla_falsa.presentacion import metricas_resumen, titulo_estado
from src.frontend.controladores.regla_falsa.salidas_regla_falsa import texto_copia_regla_falsa
from src.frontend.controladores.regla_falsa.tabla import COLUMNAS, valor_columna
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario, textos_resultado


@pytest.mark.parametrize("cambios", [
    {}, {"limite_iteraciones": "1", "tolerancia": "1e-12"},
    {"extremo_izquierdo": "1.414213562373095", "extremo_derecho": "1.4142135623730951",
     "tolerancia": "1e-30"},
    {"expresion": "sin(x)-0.5", "extremo_izquierdo": "0", "extremo_derecho": "90",
     "unidad_angular": "grados"},
])
def test_cada_paso_conserva_tabla_secante_contexto_y_copia(monkeypatch, cambios):
    """Recorre todas las filas, incluidos cierres provisionales y unidades angulares."""
    async def comprobar(vista):
        """Contrasta cada consumidor con la misma fila sin sustituir el cálculo."""
        vista.cargar_captura(captura_regla_falsa(**cambios))
        await vista.resolver()
        respuesta, panel = vista.ultimo_resultado, vista.detalle_procedimiento
        original = json.dumps(respuesta, allow_nan=False, sort_keys=True)
        copia = texto_copia_regla_falsa(respuesta, vista._precision_visual)
        assert titulo_estado(respuesta) in textos_resultado(vista) and titulo_estado(respuesta) in copia
        for etiqueta, valor in metricas_resumen(respuesta):
            assert valor in textos_resultado(vista) and f"{etiqueta}: {valor}" in copia
        for indice, fila in enumerate(respuesta["iteraciones"], 1):
            panel.reproductor.ir_a(indice)
            assert panel.fila_activa is fila
            assert vista.obtener_contexto_ia().foco.captura.detalle["iteracion"] is fila
            seleccion = panel.tabla.tabla.selected[0]
            assert seleccion == {clave: valor_columna(fila, clave) for clave, _ in COLUMNAS}
            trazas = {traza["name"]: traza for traza in panel.grafica.figure["data"]}
            assert trazas["Cruce de secante (c, 0)"]["x"] == [fila["aproximacion"]]
            assert trazas["Cruce de secante (c, 0)"]["y"] == [0]
            assert trazas["Evaluación (c, f(c))"]["y"] == [fila["valor_aproximacion"]]
            assert trazas["Intervalo siguiente del motor"]["x"] == list(fila["intervalo_siguiente"])
        assert json.dumps(respuesta, allow_nan=False, sort_keys=True) == original
    ejecutar_escenario(monkeypatch, comprobar)
