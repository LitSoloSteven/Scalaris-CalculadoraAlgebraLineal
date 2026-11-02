"""Verificaciones resumidas de LU, ecuaciones independientes y limpieza al fallar."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.componentes.exportacion_pdf.secuencia import preparar_secuencia
from src.frontend.componentes.reproductor_pasos.modelo import PasoReproductor
from src.frontend.controladores.exportacion_pdf.secuencia import seleccionar_comprobaciones
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_exportacion_algebra import calcular_algebra


def test_lu_captura_igualdad_final_sin_montar_miles_de_celdas():
    """La comprobación final incluye la igualdad calculada y evita reproducir su desarrollo."""
    pasos = tuple(PasoReproductor(indice, 'verificacion', str(indice)) for indice in range(2502))
    assert seleccionar_comprobaciones(pasos, 'lu') == (pasos[-1],)


def test_sistemas_conserva_cada_ecuacion_de_comprobacion():
    """Las comprobaciones independientes de las ecuaciones no se reducen a la última."""
    pasos = tuple(PasoReproductor(indice, 'verificacion', str(indice)) for indice in range(10))
    assert seleccionar_comprobaciones(pasos, 'sistemas') == pasos
    assert seleccionar_comprobaciones((), 'sistemas') == ()


def test_montaje_fallido_retira_todos_los_elementos(monkeypatch):
    """Un fallo del renderizador también elimina entrada y pasos montados parcialmente."""
    async def comprobar(vista, cliente):
        """Fuerza una excepción después de montar contenido temporal real."""
        await calcular_algebra('inversa', vista)
        control = vista.actualizar_exportacion_pdf.__self__
        elementos = set(cliente.elements)
        def fallar(paso, contenedor):
            """Simula un cuerpo incompleto para ejercer la limpieza del contexto."""
            with contenedor:
                ui.label('Contenido parcial de prueba')
            raise ValueError('Fallo de prueba')
        monkeypatch.setattr(vista.reproductor_pasos, 'renderizar_cuerpo', fallar)
        with pytest.raises(ValueError, match='Fallo de prueba'):
            with preparar_secuencia('inversa', control.enlace):
                pytest.fail('El montaje debía fallar antes de ceder el contexto')
        assert set(cliente.elements) == elementos
    asyncio.run(construir_pagina(monkeypatch, 'inversa', comprobar))
