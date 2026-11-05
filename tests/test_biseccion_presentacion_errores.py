"""Paridad de contexto, traza válida y propuestas en vista, copia y Glosa."""
import asyncio
import json

import pytest
from nicegui import ui

from src.frontend.controladores.biseccion.controlador import resolver_captura
from src.frontend.controladores.biseccion.presentacion_criterio import texto_resumen
from src.frontend.controladores.biseccion.presentacion_diagnostico import detalles_diagnostico, texto_sugerencia
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def _captura(expresion, intervalo):
    return {**captura_criterio(), "expresion": expresion,
            "extremo_izquierdo": str(intervalo[0]), "extremo_derecho": str(intervalo[1])}


@pytest.mark.parametrize("expresion,intervalo,etapa,abscisa", [
    ("sqrt(x)-2", (-1, 9), "Evaluación de extremos", "-1"),
    ("1/(x-.1234)", (-1, 1), "Análisis estructural", "No corresponde a una evaluación puntual."),
    ("sin()", (-1, 1), "Análisis de sintaxis", "No corresponde a una evaluación puntual."),
    ("(x-.1)/(x*x-.25)", (-1, 1), "Evaluación de punto medio", "-0.5"),
    ("x/2+5e307", (-1e308, 1e308), "Capacidad de representación numérica", "No corresponde a una evaluación puntual."),
])
def test_presentacion_no_confunde_estructura_con_punto_evaluado(expresion, intervalo, etapa, abscisa):
    """Las etiquetas proceden del contexto del motor y no inventan una coordenada de fallo."""
    respuesta = resolver_captura(_captura(expresion, intervalo))
    datos = dict(detalles_diagnostico(respuesta))
    assert datos["Etapa del fallo"] == etapa
    assert datos["Abscisa evaluada con fallo"] == abscisa
    texto = texto_resumen(respuesta, 4)
    for etiqueta, valor in datos.items():
        assert f"{etiqueta}: {valor}" in texto
    json.dumps(respuesta, allow_nan=False)


def test_error_conserva_tabla_y_contexto_identico_en_copia_y_glosa(monkeypatch):
    """La tabla válida sigue visible aunque no haya gráfica o aproximación final."""
    async def comprobar(vista):
        """Resuelve el fallo en segunda muestra y copia su diagnóstico mediante el botón real."""
        vista.cargar_captura(_captura("(x-.1)/(x*x-.25)", (-1, 1)))
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        assert respuesta["estado"] == "ERROR"
        assert len(respuesta["iteraciones"]) == 1
        assert "muestra" not in respuesta
        contexto = vista.obtener_contexto_ia().resultado
        assert contexto["contexto_fallo"] == respuesta["contexto_fallo"]
        elementos = list(vista.contenedor_resultados.descendants())
        textos = [getattr(elemento, "text", "") for elemento in elementos]
        for etiqueta, valor in detalles_diagnostico(respuesta):
            assert f"{etiqueta}: {valor}" in textos
        tablas = [elemento for elemento in elementos if isinstance(elemento, ui.table)]
        assert len(tablas) == 1
        assert len(tablas[0].rows) == 1
        assert tablas[0].rows[0]["c"] == "0"
        botones = [elemento for elemento in elementos if isinstance(elemento, ui.button)
                   and elemento._props.get("icon") == "content_copy"]
        assert len(botones) == 1
        codigos = []
        copiado = asyncio.Event()
        async def copiar(codigo):
            """Confirma el transporte y conserva el texto exacto para comprobar su contenido."""
            codigos.append(codigo)
            copiado.set()
            return True
        monkeypatch.setattr(ui, "run_javascript", copiar)
        accion = next(evento.handler for evento in botones[0]._event_listeners.values() if evento.type == "click")
        accion(None)
        await asyncio.wait_for(copiado.wait(), timeout=1)
        assert json.dumps("Solución:\n" + texto_resumen(respuesta, 4)) in codigos[0]
        assert vista.ultimo_resultado is respuesta
    ejecutar_escenario(monkeypatch, comprobar)


def test_sugerencias_visibles_y_copiables_no_se_presentan_como_aplicadas(monkeypatch):
    """El intervalo ofrecido y el fallo original coexisten en los tres consumidores."""
    async def comprobar(vista):
        """Contrasta el mismo texto de sugerencia sin tocar los campos ni recalcular."""
        vista.cargar_captura(_captura("sqrt(x)-2", (-1, 9)))
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        sugerencia = respuesta["sugerencias"][0]
        contexto = vista.obtener_contexto_ia().resultado
        assert contexto["sugerencias"] == respuesta["sugerencias"]
        mensaje = texto_sugerencia(sugerencia)
        assert mensaje in texto_resumen(respuesta, 4)
        assert mensaje in [getattr(elemento, "text", "") for elemento in vista.contenedor_resultados.descendants()]
        assert respuesta["contexto_fallo"]["x_fallo"] == -1
        assert vista.inferior.value == "-1"
        assert not vista.historial
    ejecutar_escenario(monkeypatch, comprobar)
