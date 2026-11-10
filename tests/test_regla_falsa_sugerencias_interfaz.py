"""Propuestas del dominio con acciones vigentes y carga sin ejecución."""
from copy import deepcopy

import pytest

from src.ai.huellas import calcular_huella
from src.frontend.controladores.regla_falsa.presentacion_grafica import calcular_presentacion
from src.frontend.vistas.regla_falsa.sugerencias import aplicar_sugerencia
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario, textos_resultado


def publicar_sugerencia(vista):
    """Publica una ejecución real de dominio parcial con su huella actual."""
    vista.cargar_captura(captura_regla_falsa(expresion="sqrt(x)-1", extremo_izquierdo="-1", extremo_derecho="4"))
    datos = calcular_presentacion(vista.capturar())
    vista._publicar(datos, calcular_huella(vista.capturar()))
    return datos


def test_cargar_propuesta_no_calcula_y_permanece_el_resultado_original(monkeypatch):
    async def comprobar(vista):
        datos = publicar_sugerencia(vista)
        original = deepcopy(datos["resultado"])
        assert len(datos["sugerencias"]) == 1
        assert any("no certifica continuidad" in texto for texto in textos_resultado(vista))
        aplicar_sugerencia(vista, datos, datos["sugerencias"][0])
        assert (vista.inferior.value, vista.superior.value) == ("0.0", "4.0")
        assert vista.ultimo_resultado is None and not vista.historial
        assert datos["resultado"] == original
        await vista.resolver()
        assert vista.ultimo_resultado["aproximacion"] is not None
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambio", ["expresion", "criterio", "cerrar", "ocupada", "propuesta_ajena"])
def test_sugerencia_antigua_o_ajena_no_carga_campos(monkeypatch, cambio):
    async def comprobar(vista):
        datos = publicar_sugerencia(vista)
        propuesta = datos["sugerencias"][0]
        if cambio == "expresion":
            vista.expresion.set_value("x")
        elif cambio == "criterio":
            vista.criterio.set_value("ancho")
        elif cambio == "cerrar":
            vista.cerrar()
        elif cambio == "ocupada":
            vista.ocupado = True
        else:
            propuesta = deepcopy(propuesta)
        captura = vista.capturar()
        aplicar_sugerencia(vista, datos, propuesta)
        assert vista.capturar() == captura
        vista.ocupado = False
    ejecutar_escenario(monkeypatch, comprobar)
