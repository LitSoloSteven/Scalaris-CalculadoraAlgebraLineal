"""Casos complementarios del recorrido público con captura y motor reales."""
import asyncio
import json

import pytest

from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina
from tests.comun_regla_falsa_vista import captura_regla_falsa, textos_resultado


@pytest.mark.parametrize("cambios,estado,codigo,filas", [
    ({"expresion": "1/x", "extremo_izquierdo": "-1", "extremo_derecho": "1"},
     "ERROR", "SINGULARIDAD_DETECTADA", 0),
    ({"expresion": "x-1", "extremo_izquierdo": "0", "limite_iteraciones": "1"},
     "EXITO", "RAIZ_EN_APROXIMACION", 1),
    ({"expresion": "x^10-1", "extremo_izquierdo": "0", "limite_iteraciones": "2",
      "tolerancia": "1e-12"}, "LIMITE_ITERACIONES", "LIMITE_ITERACIONES", 2),
    ({"expresion": "__import__('os')"}, "ERROR", "EXPRESION_INVALIDA", 0),
])
def test_casos_limite_desde_la_pagina_registrada(monkeypatch, cambios, estado, codigo, filas):
    """La ruta pública distingue polos, éxito final, extremo fijo y gramática hostil."""
    monkeypatch.setitem(VISTAS_RUTAS, "regla_falsa", ("regla_falsa.pagina", "VistaReglaFalsa"))

    async def comprobar(vista, cliente):
        """Envía textos de captura y verifica presentación y detalle de la página real."""
        vista.cargar_captura(captura_regla_falsa(**cambios))
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        assert (respuesta["estado"], respuesta["codigo_diagnostico"]) == (estado, codigo)
        assert respuesta["iteraciones_totales"] == len(respuesta["iteraciones"]) == filas
        assert vista.obtener_contexto_ia().resultado["codigo_diagnostico"] == codigo
        assert len(vista.detalle_procedimiento.reproductor.pasos) == filas + 2
        assert respuesta["mensaje"] in textos_resultado(vista)
        if estado == "ERROR":
            assert vista.detalle_procedimiento.datos["muestra"] is None
            assert not vista.detalle_procedimiento.tabla.tabla.rows
        else:
            assert respuesta["intervalo_final"] == respuesta["iteraciones"][-1]["intervalo_siguiente"]
        json.dumps(respuesta, allow_nan=False)
        assert vista.panel_ia is not None and cliente.elements

    asyncio.run(construir_pagina(monkeypatch, "regla_falsa", comprobar))
