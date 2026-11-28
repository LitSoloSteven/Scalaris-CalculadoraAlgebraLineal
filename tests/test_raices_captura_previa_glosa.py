"""Cobertura de previa matemática, Glosa y captura ordenada en raíces."""
import asyncio

from nicegui import ui
import pytest

from src.frontend.controladores.raices.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA
from src.frontend.nucleo import banderas
from tests.comun_construccion_vistas import construir_pagina
from tests.test_metodos_cerrados_calculo import captura_ejercicio, montar_vista


def _descendientes_etiqueta(contenedor) -> list[str]:
    return [elemento.text for elemento in contenedor.descendants() if isinstance(elemento, ui.label)]


def _descendientes_html(contenedor) -> list[str]:
    return [elemento.content for elemento in contenedor.descendants() if isinstance(elemento, ui.html)]


def test_metodos_abiertos_inicia_vacio_y_restaura_sin_calcular(monkeypatch):
    """La sesión nueva abre vacía en ejercicio y permite restaurar sin autocalcular."""
    async def _comprobar(vista, _):
        assert vista.expresion.value == ""
        assert vista.x0.value == ""
        assert vista.x1.value == ""
        assert vista.tolerancia.value == "1e-6"
        assert vista.limite.value == "100"
        assert not hasattr(vista, "selector_ejemplos")
        assert vista.previa_formula.estado.text == "Escribe f(x) para ver su representación matemática."
        assert not list(vista.previa_formula.region.descendants())
        assert vista.obtener_contexto_ia().vacio is True

        vista.restaurar_captura({
            "metodo": "secante", "expresion": "x^2 - 2",
            "x0": "1", "x1": "2", "tolerancia": "1e-5", "limite_iteraciones": "25",
        })
        assert vista.x1.visible
        assert vista.ultimo_resultado is None
        assert vista.expresion.value == "x^2 - 2"
        assert vista.tolerancia.value == "1e-5"
        assert vista.limite.value == "25"
        await vista.previa_formula._tarea
        assert not _descendientes_etiqueta(vista.previa_formula.region)
        assert len(_descendientes_html(vista.previa_formula.region)) == 1

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", _comprobar))


def test_metodos_abiertos_previa_matematica_valida_invalida_y_recupera(monkeypatch):
    """La previa solo matemática limpia entradas inválidas, escapa texto y se recupera."""
    async def _comprobar(vista, _):
        vista.expresion.set_value("sin(x) - x/2")
        await vista.previa_formula._tarea
        bloques = _descendientes_html(vista.previa_formula.region)
        assert len(bloques) == 1 and r"\sin" in bloques[0] and r"\frac{x}{2}" in bloques[0]
        assert vista.previa_formula.estado.text == ""
        assert not _descendientes_etiqueta(vista.previa_formula.region)

        vista.expresion.set_value("<img src=x onerror=alert(1)>")
        assert not list(vista.previa_formula.region.descendants())
        await vista.previa_formula._tarea
        assert not list(vista.previa_formula.region.descendants())
        assert "sintaxis" in vista.previa_formula.estado.text.lower()
        assert "<img" not in vista.previa_formula.estado.text

        vista.expresion.set_value("x^3 - 2")
        await vista.previa_formula._tarea
        assert len(_descendientes_html(vista.previa_formula.region)) == 1
        assert vista.previa_formula.estado.text == ""

        vista.metodo.set_value("secante")
        await vista.previa_formula._tarea
        assert len(_descendientes_html(vista.previa_formula.region)) == 1

        vista.limpiar_todo()
        assert vista.expresion.value == "" and vista.x0.value == "" and vista.x1.value == ""
        assert not list(vista.previa_formula.region.descendants())
        assert vista.previa_formula.estado.text == "Escribe f(x) para ver su representación matemática."

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", _comprobar))


def test_metodos_abiertos_salida_visual_y_superficie_grafica(monkeypatch):
    """El resultado prioriza estado, raíz, términos destacados y superficie propia de gráfica."""
    async def _comprobar(vista, cliente):
        superficies = [el for el in cliente.elements.values() if "metodos-abiertos-grafica-superficie" in el._classes]
        assert len(superficies) == 1
        assert vista.grafica in superficies[0].descendants()

        vista.expresion.set_value("x^3 - x - 2")
        vista.x0.set_value("1.5")
        vista.calcular()
        etiquetas = _descendientes_etiqueta(vista.resultados)
        assert "Convergió" in etiquetas
        assert "Newton-Raphson" in etiquetas
        assert "Puntos iniciales" in etiquetas
        assert any("x₀ = 1.5" in texto for texto in etiquetas)

        vista.reproductor.ir_a(1)
        etiquetas_paso = _descendientes_etiqueta(vista.contenedor_reproductor)
        assert "→ xₙ₊₁" in etiquetas_paso

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", _comprobar))


@pytest.mark.parametrize("dock,nav", [("1", "1"), ("0", "1"), ("0", "0")])
def test_metodos_abiertos_glosa_lateral_y_clasico_con_foco(monkeypatch, dock, nav):
    """Glosa abre por acción explícita, conserva contexto y devuelve el foco al cerrar."""
    monkeypatch.setattr(banderas, "panel_lateral_habilitado", lambda: dock == "1")
    monkeypatch.setenv("SCALARIS_NAV", nav)
    js_emitido = []
    consultas = []

    async def _comprobar(vista, cliente):
        monkeypatch.setattr(ui, "run_javascript", lambda codigo, **_kw: js_emitido.append(codigo))
        monkeypatch.setattr(vista.panel_ia, "_enviar_consulta", lambda *a, **kw: consultas.append((a, kw)))
        vista.expresion.set_value("x^2 - 2")
        vista.x0.set_value("1.5")
        assert vista.obtener_contexto_ia().vacio is False
        assert vista.obtener_contexto_ia().resultado is None
        vista.calcular()
        assert vista.obtener_contexto_ia().resultado["estado"] == "EXITO"
        assert consultas == []

        if dock == "1":
            vista.panel_ia.alternar()
            assert any("scalaris.glosa.alternar()" in codigo for codigo in js_emitido)
            return

        botones = [
            el for el in cliente.elements.values()
            if isinstance(el, ui.button) and el._props.get("aria-controls") == "ia-panel-clasico"
        ]
        assert len(botones) == 1
        assert vista.panel_ia.contenedor_panel._props.get("role") == "dialog"
        assert vista.panel_ia.contenedor_panel._props.get("aria-hidden") == "true"
        vista.panel_ia.alternar()
        assert vista.panel_ia.esta_abierto is True
        assert vista.panel_ia.contenedor_panel._props.get("aria-hidden") == "false"
        vista.panel_ia.alternar()
        assert vista.panel_ia.esta_abierto is False
        assert vista.panel_ia.contenedor_panel._props.get("aria-hidden") == "true"
        assert any("_origenGlosaClasico" in codigo for codigo in js_emitido)

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", _comprobar))


def test_metodos_cerrados_captura_ordenada_sin_ejemplos_y_plegables(monkeypatch):
    """Métodos cerrados muestra requisitos visibles, retira ejemplos y preserva valores al plegar."""
    async def _comprobar():
        async with montar_vista(monkeypatch, BISECCION) as (vista, cliente):
            captura = vista.captura
            assert not hasattr(captura, "ejemplos")
            assert captura.expresion._props.get("placeholder") is None
            assert captura.expresion.visible and captura.inferior.visible and captura.superior.visible
            assert "Bisección" in captura.requisito_metodo.text

            captura.metodo.set_value(REGLA_FALSA)
            assert "Regla falsa" in captura.requisito_metodo.text

            assert captura.seccion_avanzado.value is False
            captura.limite.set_value("42")
            captura.seccion_avanzado.set_value(True)
            captura.seccion_avanzado.set_value(False)
            assert captura.limite.value == "42"

            assert captura.seccion_sintaxis.value is False
            assert not _descendientes_etiqueta(captura.seccion_sintaxis)
            captura.seccion_sintaxis.set_value(True)
            ayuda = " ".join(_descendientes_etiqueta(captura.seccion_sintaxis)).lower()
            assert "funciones" in ayuda and "ejemplo" not in ayuda

            vista.cargar_captura(captura_ejercicio("x^2 - 2", "1", "2", "radianes"))
            await vista.resolver()
            assert "1 cálculo guardado" in vista.acciones.seccion._props.get("caption", "")

            superficies = [el for el in cliente.elements.values() if "metodos-raices-grafica-superficie" in el._classes]
            assert len(superficies) == 1 and vista.grafica.nodo in superficies[0].descendants()

    asyncio.run(_comprobar())
