"""Paginación genérica y compatibilidad visual de datos de bisección."""
import asyncio

import pytest
from nicegui import Client, core, ui

from src.frontend.componentes.tabla_iteraciones import PaginacionIteraciones
from src.frontend.controladores.biseccion.controlador import resolver_captura
from src.frontend.controladores.biseccion.presentacion import COLUMNAS, filas_tabla
from src.frontend.controladores.biseccion.salidas_biseccion import COLUMNAS_EXAMEN, datos_examen
from src.frontend.vistas.biseccion.tabla_iteraciones import mostrar_tabla
from tests.comun_biseccion_criterios import captura_criterio
from tests.comun_construccion_vistas import preparar_transporte, cerrar_cliente


def _ejecutar(monkeypatch, comprobar):
    async def ejecutar():
        monkeypatch.setattr(core, "script_mode", False)
        cliente = Client(ui.page("/prueba_paginacion_raices"))
        preparar_transporte(monkeypatch, cliente)
        try:
            with cliente:
                comprobar(cliente)
        finally:
            await cerrar_cliente(cliente, [])
    asyncio.run(ejecutar())


def _pulsar(boton):
    evento = next(evento for evento in boton._event_listeners.values() if evento.type == "click")
    evento.handler(None)


@pytest.mark.parametrize("total", [0, 1, 15, 16, 500])
def test_componente_recibe_solo_las_filas_visibles(monkeypatch, total):
    """Pagina hasta el límite del motor y conserva botones/estado en extremos y vacío."""
    def comprobar(cliente):
        solicitudes = []

        def preparar(inicio, fin):
            solicitudes.append((inicio, fin))
            return (("i", "Iteración"),), [{"i": indice + 1} for indice in range(inicio, fin)]

        tabla = ui.table(columns=[], rows=[], row_key="i")
        paginacion = PaginacionIteraciones(tabla, total, preparar)
        paginacion.construir()
        assert tabla.rows == [{"i": indice + 1} for indice in range(min(15, total))]
        assert not paginacion.anterior.enabled
        while paginacion.siguiente.enabled:
            _pulsar(paginacion.siguiente)
        assert solicitudes[-1] == ((max(0, total - 1) // 15) * 15, total)
        assert len(tabla.rows) <= 15
        assert paginacion.estado.text == f"Filas {solicitudes[-1][0] + 1 if total else 0} a {total} de {total}"
        assert not paginacion.siguiente.enabled
        while paginacion.anterior.enabled:
            _pulsar(paginacion.anterior)
        assert solicitudes[-1] == (0, min(15, total))
    _ejecutar(monkeypatch, comprobar)


def test_preferencias_actualizan_solo_pagina_actual_y_respetan_desmontaje(monkeypatch):
    """El formato no vuelve a la primera página ni escribe en una tabla eliminada."""
    def comprobar(cliente):
        precision, solicitudes = ui.switch("Precisión"), []

        def preparar(inicio, fin):
            solicitudes.append((inicio, fin))
            return (("i", "Fila"),), [{"i": str(indice) if precision.value else indice}
                                       for indice in range(inicio, fin)]

        tabla = ui.table(columns=[], rows=[], row_key="i")
        paginacion = PaginacionIteraciones(tabla, 16, preparar, (precision,))
        paginacion.construir()
        _pulsar(paginacion.siguiente)
        precision.set_value(True)
        assert solicitudes[-1] == (15, 16) and tabla.rows == [{"i": "15"}]
        tabla.delete()
        cantidad = len(solicitudes)
        precision.set_value(False)
        _pulsar(paginacion.anterior)
        assert len(solicitudes) == cantidad
    _ejecutar(monkeypatch, comprobar)


@pytest.mark.parametrize("caso", ["traza", "extremo", "sin_signo"])
def test_fachada_biseccion_conserva_columnas_examen_e_inspeccion(monkeypatch, caso):
    """Compara tabla visible contra las salidas originales, incluso sin filas."""
    captura = captura_criterio("iteraciones", 40)
    if caso == "extremo":
        captura.update(expresion="x-1")
    elif caso == "sin_signo":
        captura.update(expresion="x^2+1")
    respuesta = resolver_captura(captura)

    def comprobar(cliente):
        examen = ui.switch("Modo examen")
        mostrar_tabla(respuesta, examen)
        tabla = next(elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.table))
        precision = next(elemento for elemento in cliente.elements.values()
                         if isinstance(elemento, ui.switch) and elemento is not examen)
        assert tabla.rows == filas_tabla(respuesta)[:15]
        precision.set_value(True)
        examen.set_value(True)
        originales = respuesta["iteraciones"][:15]
        esperadas = filas_tabla({"iteraciones": originales}, True)
        for fila, original in zip(esperadas, originales, strict=True):
            fila.update(datos_examen(original, respuesta["estado"]))
        assert tabla.rows == esperadas
        assert [(columna["name"], columna["label"]) for columna in tabla.columns] == list(COLUMNAS + COLUMNAS_EXAMEN)
        examen.set_value(False)
        assert tabla.rows == filas_tabla(respuesta, True)[:15]
        assert len(tabla.columns) == len(COLUMNAS)
    _ejecutar(monkeypatch, comprobar)
