"""Vacío, errores por celda y carga de operaciones matriciales montadas."""
import asyncio
import pytest
from nicegui import ui
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("valor", ["texto", "9" * 257, "<img src=x onerror=alert(1)>"])
def test_error_matricial_identifica_celda_sin_html_activo(monkeypatch, valor):
    """El error publicado identifica matriz y celda; el dato adverso no se interpreta."""
    async def comprobar(vista, cliente):
        """Ejercita captura, serialización y presentación reales."""
        vista.panel_captura_matrices.cargar_datos({"A": [[valor]]})
        vista.entrada_expresion.set_value("A+A")
        await vista.evaluar_expresion(ui.button("Evaluar prueba"))
        assert vista.ultimo_resultado["estado"] == "ERROR"
        assert "Matriz A, celda [1,1]" in vista.ultimo_resultado["mensaje"]
        elementos = list(vista.contenedor_resultados.descendants())
        assert any("[1,1]" in elemento.text for elemento in elementos if isinstance(elemento, ui.label))
        assert not any("<img" in elemento.content for elemento in elementos if isinstance(elemento, ui.html))
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_expresion_vacia_detiene_y_reemplaza_resultado(monkeypatch):
    """Borrar la expresión y evaluar vuelve al estado vacío sin reproducción activa."""
    async def comprobar(vista, cliente):
        """Calcula primero una suma exacta y luego evalúa la entrada vacía."""
        vista.panel_captura_matrices.cargar_datos({"A": [["1/3"]]})
        vista.entrada_expresion.set_value("A+A")
        await vista.evaluar_expresion(ui.button("Evaluar prueba"))
        assert vista.ultimo_resultado["matriz_resultado"]["datos"] == [["2/3"]]
        vista.entrada_expresion.set_value("")
        await vista.evaluar_expresion(ui.button("Evaluar prueba"))
        assert vista.ultimo_resultado is None
        assert vista.reproductor_pasos is None
        assert any(elemento.text == "Sin resultados" for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label))
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_carga_matricial_publica_estado_y_evitar_doble_ejecucion(monkeypatch):
    """Un segundo evento durante la carga no inicia otro cálculo."""
    async def comprobar(vista, cliente):
        """Retiene el núcleo para observar la ejecución y el estado accesible."""
        iniciado, terminar = asyncio.Event(), asyncio.Event()
        llamadas = []
        async def calcular(boton, expresion):
            """Retiene solo la ejecución interna de esta prueba."""
            llamadas.append(expresion)
            iniciado.set()
            await terminar.wait()
        monkeypatch.setattr(vista, "_evaluar_nucleo", calcular)
        vista.entrada_expresion.set_value("A+A")
        boton = ui.button("Evaluar prueba")
        tarea = asyncio.create_task(vista.evaluar_expresion(boton))
        await iniciado.wait()
        assert boton._props["loading"] is True
        assert any(elemento.text == "Evaluando…" for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label))
        await vista.evaluar_expresion(boton)
        assert llamadas == ["A+A"]
        terminar.set()
        await tarea
        assert boton._props.get("loading", False) is False
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_vaciado_durante_calculo_no_republica_resultado_obsoleto(monkeypatch):
    """La limpieza invalida el cálculo pendiente antes de que pueda volver a mostrarlo."""
    async def comprobar(vista, cliente):
        """Intercala la entrada vacía en la espera real del cálculo."""
        vista.panel_captura_matrices.cargar_datos({"A": [["1"]]})
        vista.entrada_expresion.set_value("A+A")
        boton = ui.button("Evaluar prueba")
        tarea = asyncio.create_task(vista.evaluar_expresion(boton))
        await asyncio.sleep(0)
        vista.entrada_expresion.set_value("")
        await vista.evaluar_expresion(boton)
        assert vista.ultimo_resultado is None
        await tarea
        assert vista.ultimo_resultado is None
        assert any(elemento.text == "Sin resultados" for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label))
        assert boton._props.get("loading", False) is False
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))
