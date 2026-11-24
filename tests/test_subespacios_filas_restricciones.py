"""El editor de restricciones permite editar y retirar ecuaciones por fila."""
import asyncio

from nicegui import ui

from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


def test_restricciones_edita_filas_y_conserva_la_conversion_exacta(monkeypatch):
    """Comprueba la captura activa, retirada de una ecuación inválida y conversión."""
    monkeypatch.setitem(VISTAS_RUTAS, "espacios_subespacios", (
        "algebra.operaciones_vectores.vista_espacios_subespacios", "VistaEspaciosSubespacios",
    ))

    async def _comprobar(vista, _cliente):
        captura = vista.captura
        captura.selector.set_value("ecuaciones")
        editor = captura.ecuaciones
        primera, segunda = captura.campos_entrada()
        assert isinstance(primera, ui.input)
        assert segunda.props.get("aria-label") == "Ecuación 2"
        primera.set_value("x1 = 1/3")
        segunda.set_value("x2 = 0")
        await editor.cambiar_cantidad(1)
        captura.campos_entrada()[-1].set_value("x3")
        captura.selector.set_value("matriz")
        assert captura.formato == "ecuaciones"
        assert editor.props.get("aria-invalid") == "true"
        await editor.cambiar_cantidad(-1)
        assert captura.obtener()["ecuaciones"] == "x1 = 1/3\nx2 = 0"
        assert editor.props.get("aria-invalid") is None
        await vista.analizar()
        resultado = vista.ultimo_resultado
        assert resultado["clasificacion"] == "AFIN_NO_SUBESPACIO"
        captura.selector.set_value("matriz")
        assert captura.obtener()["vector_b"] == ["1/3", "0"]

    asyncio.run(construir_pagina(monkeypatch, "espacios_subespacios", _comprobar, {"modo": "restricciones"}))
