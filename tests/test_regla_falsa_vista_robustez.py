"""Cancelación, fallos parciales y contenido adversario en los controles reales."""
import asyncio
import importlib

import pytest
from nicegui import run, ui

from src.backend.excepciones import ErrorDominio
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario, textos_resultado


def test_cancelacion_libera_la_carga_sin_publicar(monkeypatch):
    """La cancelación del transporte no crea historial ni retiene el botón deshabilitado."""
    async def comprobar(vista):
        """Cancela una espera activa y comprueba el estado posterior del formulario."""
        inicio = asyncio.Event()

        async def esperar(calcular, captura):
            """Retiene la solicitud hasta que la prueba cancela su tarea."""
            inicio.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(run, "io_bound", esperar)
        vista.cargar_captura(captura_regla_falsa())
        tarea = asyncio.create_task(vista.resolver())
        await asyncio.wait_for(inicio.wait(), 2)
        tarea.cancel()
        await asyncio.wait_for(tarea, 2)
        assert not vista.ocupado and vista.tarea_calculo is None
        assert vista.boton_resolver.enabled and not vista.historial
        assert vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)


def test_fallo_parcial_se_presenta_y_guarda_como_error(monkeypatch):
    """Las filas válidas de un fallo se conservan para diagnóstico, contexto y reciente provisional."""
    motor = importlib.import_module("src.backend.resolutores.raices.regla_falsa")
    original, llamadas = motor.evaluar, []

    def evaluar_con_fallo(funcion, valor):
        """Delega las primeras evaluaciones y falla en el tercer cruce de secante."""
        llamadas.append(valor)
        if len(llamadas) == 3:
            raise ErrorDominio("La evaluación no pertenece al dominio.", "DOMINIO_INVALIDO")
        return original(funcion, valor)

    async def comprobar(vista):
        """Publica un fallo real del evaluador conservando exactamente las filas previas."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        assert respuesta["estado"] == "ERROR" and respuesta["iteraciones_totales"] == 2
        assert respuesta["aproximacion"] is None and respuesta["entrada"] is None
        assert vista.historial[0]["estado"] == "ERROR"
        assert vista.obtener_contexto_ia().resultado["ultima_fila_valida"] == respuesta["iteraciones"][-1]
        assert "Evaluación de la secante" in textos_resultado(vista)
        assert not any("Convergió" in texto for texto in textos_resultado(vista))

    monkeypatch.setattr(motor, "evaluar", evaluar_con_fallo)
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambios", [
    {"tolerancia": "nan"}, {"tolerancia": "1e-999"}, {"limite_iteraciones": "500.5"},
    {"expresion": "<img src=x onerror=alert(1)>"}, {"expresion": "x" * 513},
    {"extremo_izquierdo": "1e999"},
])
def test_captura_adversaria_no_crea_html_ni_aproximaciones(monkeypatch, cambios):
    """Los errores del dominio se presentan como texto y no generan controles HTML de usuario."""
    async def comprobar(vista):
        """Envía valores adversarios y revisa el árbol real de elementos del resultado."""
        vista.cargar_captura(captura_regla_falsa(**cambios))
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "ERROR"
        assert vista.ultimo_resultado["aproximacion"] is None and not vista.historial
        assert not any(isinstance(elemento, ui.html) for elemento in vista.contenedor_resultados.descendants())
    ejecutar_escenario(monkeypatch, comprobar)
