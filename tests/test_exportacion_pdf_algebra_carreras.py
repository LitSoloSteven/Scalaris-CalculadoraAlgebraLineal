"""Entrega PDF desde los contratos reales de estado de todas las vistas algebraicas."""
import asyncio

import pytest
from nicegui import ui
from src.frontend.componentes.exportacion_pdf import boton as modulo_boton
from tests.comun_exportacion_pdf import PORTADA, crear_captura
from tests.comun_exportacion_algebra import (
    HERRAMIENTAS, construir_algebra, calcular_algebra, editar_algebra, regiones_control,
)


def _trabajador_con_cambio(vista, control, herramienta, cambio):
    async def trabajar(funcion, *argumentos):
        """Completa el generador real después de aplicar una carrera controlada."""
        if cambio == 'editar':
            editar_algebra(herramienta, vista)
        elif cambio == 'cerrar':
            control.dialogo.dialogo.close()
        elif cambio == 'revision':
            atributo = {'vectores': '_revision_calculo', 'matrices': '_version_solicitud'}.get(herramienta, '_revision_captura')
            setattr(vista, atributo, getattr(vista, atributo) + 1)
        return funcion(*argumentos)
    return trabajar


@pytest.mark.parametrize('herramienta', HERRAMIENTAS)
@pytest.mark.parametrize('cambio', ('ninguno', 'editar', 'revision', 'cerrar'))
def test_descarga_o_descarta_segun_testigo_real(monkeypatch, herramienta, cambio):
    """El flujo completo descarga solo el cálculo vigente con portada abierta."""
    async def comprobar(vista, cliente):
        """Genera con captura sintética y conserva validación y trabajador reales."""
        await calcular_algebra(herramienta, vista)
        control = vista.actualizar_exportacion_pdf.__self__
        capturas = [crear_captura(region._props['data-pdf-captura']) for region in regiones_control(control)]
        control.abrir()
        for clave, valor in PORTADA.items():
            control.dialogo.campos[clave].set_value(valor)
        descargas = []
        monkeypatch.setattr(ui, 'download', lambda *argumentos, **opciones: descargas.append((argumentos, opciones)))
        async def capturar(identificador):
            """Sustituye únicamente el navegador y exige la raíz registrada en el enlace."""
            assert identificador == control.enlace.raiz
            return capturas
        monkeypatch.setattr(modulo_boton, 'capturar_regiones', capturar)
        monkeypatch.setattr(modulo_boton.run, 'io_bound', _trabajador_con_cambio(vista, control, herramienta, cambio))
        await control.generar()
        assert len(descargas) == int(cambio == 'ninguno')
        assert not control.ocupado
        if descargas:
            assert descargas[0][0][0].startswith(b'%PDF-')
            assert descargas[0][1]['filename'].isascii()
    asyncio.run(construir_algebra(monkeypatch, herramienta, comprobar))
