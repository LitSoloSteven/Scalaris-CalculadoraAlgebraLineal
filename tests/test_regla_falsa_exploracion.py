"""Exploración real independiente de extremos y preferencias de parada."""
import json
import math

import pytest

from tests.comun_regla_falsa_vista import ejecutar_escenario


def preparar_busqueda(vista, expresion="x^2-2"):
    """Activa la búsqueda con función y rango reproducibles, sin completar extremos."""
    vista.expresion.set_value(expresion)
    vista.modos.set_value("busqueda")
    vista.exploracion.minimo.set_value("-2")
    vista.exploracion.maximo.set_value("2")
    return vista.exploracion


@pytest.mark.parametrize("indice", [0, 1])
def test_buscar_cargar_y_resolver_sin_extremos_iniciales(monkeypatch, indice):
    """Cada cruce conduce por selección explícita al motor clásico de regla falsa."""
    async def comprobar(vista):
        """Explora sin parada válida y completa esa preferencia solo para resolver."""
        panel = preparar_busqueda(vista)
        vista.tolerancia.set_value("incorrecta")
        vista.limite.set_value("")
        assert vista.inferior.value == vista.superior.value == ""
        await vista.enviar_captura()
        respuesta = panel.respuesta
        assert respuesta["estado"] == "EXITO"
        cruces = [candidato for candidato in respuesta["candidatos"] if candidato["tipo"] == "cruce"]
        assert len(cruces) == 2 and vista.ultimo_resultado is None
        json.dumps(respuesta, allow_nan=False)
        panel.seleccionar(respuesta, cruces[indice])
        assert vista.modos.value == "intervalo" and vista.ultimo_resultado is None
        assert not vista.historial
        vista.tolerancia.set_value("1e-6")
        vista.limite.set_value("100")
        await vista.enviar_captura()
        resultado = vista.ultimo_resultado
        assert resultado["estado"] == "EXITO" and resultado["metodo"] == "regla_falsa"
        assert math.isclose(abs(resultado["aproximacion"]), math.sqrt(2), abs_tol=1e-6)
        assert (resultado["aproximacion"] > 0) == bool(indice)
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("expresion", ["x^2+1", "1/x", "sqrt(x)"])
def test_evidencia_no_inventa_una_raiz(monkeypatch, expresion):
    """Los polos y segmentos inválidos no se convierten en cruces seleccionables."""
    async def comprobar(vista):
        """Inspecciona los registros reales sin ejecutar un cálculo individual."""
        panel = preparar_busqueda(vista, expresion)
        await panel.enviar_busqueda()
        assert panel.respuesta["estado"] == "EXITO"
        tipos = {candidato["tipo"] for candidato in panel.respuesta["candidatos"]}
        assert "cruce" not in tipos
        assert vista.ultimo_resultado is None
        if expresion == "x^2+1":
            assert not panel.respuesta["candidatos"]
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("minimo,maximo,paso", [
    ("2", "-2", None), ("nan", "2", None), ("-2", "2", "1e-10"),
    ("1e20", "1.00000000000001e20", "1e-10"), ("", "2", None),
])
def test_rango_paso_y_presupuesto_tienen_error_visible(monkeypatch, minimo, maximo, paso):
    """El dominio rechaza rangos imposibles y mallas excesivas sin dejar carga activa."""
    async def comprobar(vista):
        """Envía la captura adversa por el panel real y comprueba recuperación."""
        panel = preparar_busqueda(vista)
        panel.minimo.set_value(minimo)
        panel.maximo.set_value(maximo)
        if paso is not None:
            panel.paso.set_value(paso)
        await panel.enviar_busqueda()
        assert panel.respuesta["estado"] == "ERROR" and panel.estado.text
        assert panel.boton.enabled and panel.tarea is None
        assert not panel.respuesta["candidatos"] and vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)


def test_limpieza_restablece_rango_y_paso_con_preferencias(monkeypatch):
    """Un rango editado cuenta como datos incluso con la función vacía."""
    async def comprobar(vista):
        """Comprueba limpieza, preferencias y vuelta al paso automático efectivo."""
        assert vista.modos.value == "intervalo"
        vista.exploracion.minimo.set_value("-3")
        vista.exploracion.paso.set_value(".3")
        vista.tolerancia.set_value("1e-9")
        vista.unidad_angular.set_value("grados")
        assert not vista.esta_completamente_vacio()
        vista.limpiar_todo()
        panel = vista.exploracion
        assert vista.esta_completamente_vacio()
        assert (panel.minimo.value, panel.maximo.value, panel.paso.value) == ("-10", "10", "0.1")
        assert "automático efectivo" in panel.etiqueta_paso.text
        assert vista.tolerancia.value == "1e-9" and vista.unidad_angular.value == "grados"
    ejecutar_escenario(monkeypatch, comprobar)
