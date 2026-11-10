"""Paginación y selección de filas reales del método de regla falsa."""
from types import SimpleNamespace

from nicegui import ui

from src.frontend.controladores.regla_falsa.controlador import resolver_captura
from src.frontend.vistas.regla_falsa.tabla_iteraciones import TablaReglaFalsa
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


def test_tabla_sigue_fila_de_otra_pagina_y_conserva_inspeccion(monkeypatch):
    """El índice activo cambia la página y el formato no pierde la selección del procedimiento."""
    async def comprobar(vista):
        """Monta una traza lenta real y navega a una fila que no está en la página inicial."""
        respuesta = resolver_captura(captura_regla_falsa(
            expresion="x^10-1", extremo_izquierdo="0", extremo_derecho="2", limite_iteraciones="40"))
        elegidos = []
        with ui.column():
            tabla = TablaReglaFalsa(respuesta["iteraciones"], elegidos.append)
            tabla.construir()
        assert len(tabla.tabla.rows) == 15
        tabla.seleccionar(respuesta["iteraciones"][20])
        assert tabla.paginacion.pagina == 1 and tabla.tabla.selected[0]["i"] == "21"
        tabla.precision.set_value(True)
        assert tabla.paginacion.pagina == 1 and tabla.tabla.selected[0]["i"] == "21"
        tabla._elegir(SimpleNamespace(selection=[tabla.tabla.rows[1]]))
        assert elegidos == [17]
        tabla._elegir(SimpleNamespace(selection=[{"i": "inexistente"}]))
        assert elegidos == [17]
    ejecutar_escenario(monkeypatch, comprobar)


def test_tabla_vacia_y_navegacion_acotada(monkeypatch):
    """El componente genérico admite cero filas y acota índices externos a páginas existentes."""
    async def comprobar(vista):
        """Comprueba una traza vacía sin marcar aproximaciones ni habilitar navegación ficticia."""
        with ui.column():
            tabla = TablaReglaFalsa((), lambda indice: None)
            tabla.construir()
        tabla.paginacion.mostrar_indice(500)
        assert tabla.paginacion.pagina == 0 and tabla.tabla.rows == []
        assert not tabla.paginacion.anterior.enabled and not tabla.paginacion.siguiente.enabled
    ejecutar_escenario(monkeypatch, comprobar)
