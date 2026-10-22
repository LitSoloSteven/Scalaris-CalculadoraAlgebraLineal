"""Estados reales de bases y romanos con entradas desfavorables."""
import asyncio

import pytest
from nicegui import ui
from tests.comun_construccion_vistas import construir_pagina
from src.backend.resolutores.sistemas_numericos.pasos_didacticos import desglosar_bits


@pytest.mark.parametrize("herramienta", ["bases", "romanos"])
def test_estado_vacio_ofrece_una_accion(monkeypatch, herramienta):
    """Ambas vistas orientan antes de la primera operación."""
    async def comprobar(vista, cliente):
        """Comprueba el mensaje inicial publicado como estado accesible."""
        etiquetas = [elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.label)]
        assert any("Ingresa" in elemento.text and elemento._props.get("role") == "status" for elemento in etiquetas)
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize("valor", ["", "9" * 257 + "x", "<script>alert(1)</script>"])
def test_bases_error_limpia_resultado_y_recupera_conversion(monkeypatch, valor):
    """El error de entrada reemplaza un resultado válido y permite volver a convertir."""
    async def comprobar(vista, cliente):
        """Ejercita éxito, error y recuperación con controles montados."""
        vista.entrada_valor.set_value("42")
        await vista._convertir_boton()
        assert vista.tiene_resultado is True
        vista.entrada_valor.set_value(valor)
        await vista._convertir_boton()
        assert vista.tiene_resultado is False
        assert vista.etiqueta_error.text
        assert vista.etiqueta_error._props["role"] == "alert"
        vista.entrada_valor.set_value("-12345678901234567890")
        await vista._convertir_boton()
        assert vista.tiene_resultado is True
        assert vista.resultados["decimal"].replace(" ", "") == "-12345678901234567890"
        assert vista.boton_convertir._props.get("loading", False) is False
    asyncio.run(construir_pagina(monkeypatch, "bases", comprobar))


def test_bases_numero_de_doscientos_bits_se_muestra_completo(monkeypatch):
    """La cifra extensa conserva su valor en etiquetas y pasos, sin truncamiento numérico."""
    async def comprobar(vista, cliente):
        """Convierte una magnitud exacta extensa y comprueba la presentación."""
        valor = str(2 ** 200 - 1)
        vista.entrada_valor.set_value(valor)
        await vista._convertir_boton()
        assert vista.resultados["decimal"].replace(" ", "") == valor
        assert vista.resultados["binario"].replace(" ", "") == "1" * 200
        assert vista.etiqueta_bits.text == "200 BITS"
        assert vista.reproductor is not None
        assert "break-all" in vista.etiquetas_valores["decimal"]._classes
    asyncio.run(construir_pagina(monkeypatch, "bases", comprobar))


@pytest.mark.parametrize("operando", ["", "MMMM", "<img src=x onerror=alert(1)>", "I" * 1000])
def test_romanos_error_detiene_reproductor_y_recupera(monkeypatch, operando):
    """Un operando adverso limpia el resultado y detiene la reproducción anterior."""
    async def comprobar(vista, cliente):
        """Ejecuta éxito, error y recuperación por el manejador real."""
        vista.cargar_ejemplo("I", "I", "suma")
        await vista._operar_desde_control()
        reproductor = vista.reproductor
        assert vista.ultimo_resultado.resultado_romano == "II"
        vista.entrada_a.set_value(operando)
        await vista._operar_desde_control()
        assert vista.ultimo_resultado is None
        assert vista.reproductor is None
        assert vista.ultimo_error is not None
        assert vista.etiqueta_error.text
        assert vista.entrada_a._props.get("error") is True
        assert vista.boton_calcular._props.get("loading", False) is False
        vista.cargar_ejemplo("XIV", "IX", "suma")
        await vista._operar_desde_control()
        assert vista.ultimo_resultado.resultado_romano == "XXIII"
        assert vista.reproductor is not reproductor
    asyncio.run(construir_pagina(monkeypatch, "romanos", comprobar))


@pytest.mark.parametrize("herramienta", ["bases", "romanos"])
def test_carga_visible_y_cancelacion_libera_control(monkeypatch, herramienta):
    """El primer turno asíncrono publica carga y la cancelación libera el botón."""
    async def comprobar(vista, cliente):
        """Observa y cancela la tarea antes del cálculo síncrono."""
        if herramienta == "bases":
            vista.entrada_valor.set_value("2")
            ejecutar, boton = vista._convertir_boton, vista.boton_convertir
        else:
            vista.cargar_ejemplo("I", "I", "suma")
            ejecutar, boton = vista._operar_desde_control, vista.boton_calcular
        tarea = asyncio.create_task(ejecutar())
        await asyncio.sleep(0)
        assert boton._props["loading"] is True
        tarea.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tarea
        assert boton._props.get("loading", False) is False
        assert vista._calculando is False
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_pesos_de_bits_exactos_en_backend():
    """Los pesos didácticos tienen una fuente única de dominio."""
    assert desglosar_bits("101") == [
        {"bit": "1", "exponente": 2, "peso": 4},
        {"bit": "0", "exponente": 1, "peso": 2},
        {"bit": "1", "exponente": 0, "peso": 1},
    ]
    assert desglosar_bits("") == []
