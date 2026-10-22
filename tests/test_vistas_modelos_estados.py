"""Montaje, datos desfavorables y estados de captura matricial."""
import asyncio
import pytest
from nicegui import ui
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("herramienta", ["leontief", "transformaciones"])
def test_cuadricula_compartida_tiene_coordenadas_y_desplazamiento(monkeypatch, herramienta):
    """La captura real comparte accesibilidad y soporta matrices que exceden el ancho."""
    async def comprobar(vista, cliente):
        """Inspecciona propiedades de las celdas reales montadas."""
        assert "modelos-captura" in vista.contenedor_coeficientes._classes
        assert '<script src="/assets/js/captura_matrices.js"></script>' in cliente.head_html
        for fila, entradas in enumerate(vista.entradas_coeficientes):
            for columna, entrada in enumerate(entradas):
                assert entrada._props["data-matriz-fila"] == str(fila)
                assert entrada._props["data-matriz-columna"] == str(columna)
                assert entrada._props["aria-label"] == f"Fila {fila + 1}, columna {columna + 1}"
        etiquetas = [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert any("Ingresa" in texto for texto in etiquetas)
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize("herramienta,coordenada", [("leontief", "C[2,1]"), ("transformaciones", "A[2,1]")])
@pytest.mark.parametrize("valor", ["texto", "9" * 257, "<script>alert(1)</script>"])
def test_error_identifica_celda_y_no_interpreta_html(monkeypatch, herramienta, coordenada, valor):
    """Los mensajes de backend mantienen coordenadas y entradas hostiles como texto."""
    async def comprobar(vista, cliente):
        """Ejecuta el cálculo desde la celda inválida real."""
        vista.entradas_coeficientes[1][0].set_value(valor)
        calcular = vista._calcular if herramienta == "leontief" else vista._analizar
        boton = ui.button("Calcular prueba")
        await calcular(boton)
        assert vista.ultimo_resultado["estado"] == "ERROR"
        assert coordenada in vista.ultimo_resultado["mensaje"]
        etiquetas = [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert any(coordenada in texto for texto in etiquetas)
        assert not any(isinstance(elemento, ui.html) and "<script" in elemento.content for elemento in vista.contenedor_resultados.descendants())
        assert boton._props.get("loading", False) is False
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize("herramienta", ["leontief", "transformaciones"])
def test_carga_visible_rechaza_doble_calculo_y_libera_boton(monkeypatch, herramienta):
    """La carga se publica antes de delegar y no admite una segunda ejecución simultánea."""
    async def comprobar(vista, cliente):
        """Retiene el cálculo para observar el estado intermedio."""
        iniciado, terminar = asyncio.Event(), asyncio.Event()
        llamadas = []
        async def calcular():
            """Simula exclusivamente el tiempo de respuesta del cálculo."""
            llamadas.append(True)
            iniciado.set()
            await terminar.wait()
        nombre = "_calcular_nucleo" if herramienta == "leontief" else "_analizar_nucleo"
        monkeypatch.setattr(vista, nombre, calcular)
        ejecutar = vista._calcular if herramienta == "leontief" else vista._analizar
        boton = ui.button("Calcular prueba")
        tarea = asyncio.create_task(ejecutar(boton))
        await iniciado.wait()
        assert boton._props["loading"] is True
        assert any(elemento.text == "Calculando…" for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label))
        await ejecutar(boton)
        assert llamadas == [True]
        terminar.set()
        await tarea
        assert boton._props.get("loading", False) is False
        assert vista._calculando is False
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize("herramienta", ["leontief", "transformaciones"])
def test_todos_los_ejemplos_montan_y_calculan(monkeypatch, herramienta):
    """Cada ejemplo vigente se carga sin alias y produce el análisis esperado."""
    from src.frontend.vistas.operaciones_matrices._ejemplos_leontief import EJEMPLOS_LEONTIEF
    from src.frontend.vistas.operaciones_matrices._ejemplos_transformaciones import EJEMPLOS_TRANSFORMACIONES
    ejemplos = EJEMPLOS_LEONTIEF if herramienta == "leontief" else EJEMPLOS_TRANSFORMACIONES
    async def comprobar(vista, cliente):
        """Verifica captura, estado vacío y cálculo de cada ejemplo."""
        for ejemplo in ejemplos:
            vista._cargar_ejemplo(ejemplo)
            assert vista.ultimo_resultado is None
            calcular = vista._calcular if herramienta == "leontief" else vista._analizar
            await calcular(ui.button("Calcular prueba"))
            assert vista.ultimo_resultado["estado"] != "ERROR"
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_sector_largo_y_hostil_conserva_title_sin_html_activo(monkeypatch):
    """Los nombres de sectores son texto con título y los números conservan todas sus cifras."""
    async def comprobar(vista, cliente):
        """Comprueba el resultado económico con etiquetas y magnitudes largas."""
        sector = '<img src=x onerror=alert(1)>' + 'sector' * 200
        demanda = "123456789012345678901234567890"
        vista.entradas_sectores[0].set_value(sector)
        vista.entradas_demanda[0].set_value(demanda)
        await vista._calcular(ui.button("Calcular prueba"))
        assert vista.ultimo_resultado["vector_produccion"][0] == demanda
        etiquetas = [elemento for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert any(elemento.text == sector and elemento._props.get("title") == sector for elemento in etiquetas)
        assert any(elemento.text == demanda for elemento in etiquetas)
        assert not any("<img" in elemento.content for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.html))
    asyncio.run(construir_pagina(monkeypatch, "leontief", comprobar))
