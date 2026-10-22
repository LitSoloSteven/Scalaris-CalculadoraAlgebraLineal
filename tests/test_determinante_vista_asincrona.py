"""La vista de determinante descarta respuestas tras editar o abandonar la página."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import Client, core, run, ui

from src.frontend.vistas.operaciones_matrices.vista_determinante import VistaDeterminante
from tests.comun_construccion_vistas import preparar_transporte
from tests.comun_calculo_determinante import retener_calculo


@pytest.mark.parametrize("desmontar", [False, True])
def test_respuesta_tardia_no_publica_en_captura_invalida(monkeypatch, desmontar):
    """Editar o eliminar el cliente invalida el resultado y no toca controles eliminados."""
    async def comprobar():
        """Coordina explícitamente el trabajador y la invalidación de su captura."""
        monkeypatch.setattr(core, "script_mode", False)
        cliente = Client(ui.page("/determinante_espera"))
        preparar_transporte(monkeypatch, cliente)
        with cliente:
            vista = VistaDeterminante()
            vista.construir()
            mostrar = Mock()
            monkeypatch.setattr(vista, "_mostrar_resultado", mostrar)
            boton = next(elemento for elemento in cliente.elements.values()
                         if isinstance(elemento, ui.button) and elemento.text == "Calcular determinante")
            revision = vista._revision_captura
            async with retener_calculo(monkeypatch, vista, boton):
                cliente.delete() if desmontar else vista._invalidar_resultado()
            mostrar.assert_not_called()
            assert vista.ultimo_resultado is None
            assert vista._revision_captura > revision
            assert vista.contenedor_resultados.is_deleted is desmontar
        if not desmontar:
            cliente.delete()
    asyncio.run(comprobar())


def test_recalculo_fallido_retira_exito_anterior(monkeypatch):
    """Un fallo del trabajador no conserva un éxito anterior como resultado vigente."""
    async def comprobar():
        """Monta la vista y provoca un fallo después de un resultado anterior."""
        monkeypatch.setattr(core, "script_mode", False)
        cliente = Client(ui.page("/determinante_fallo"))
        preparar_transporte(monkeypatch, cliente)
        async def fallar(funcion, captura):
            """Reproduce un error inesperado del trabajador sin cambiar la captura."""
            raise RuntimeError("fallo controlado del trabajador")
        monkeypatch.setattr(run, "io_bound", fallar)
        with cliente:
            vista = VistaDeterminante()
            vista.construir()
            vista.ultimo_resultado = {"estado": "EXITO", "determinante": 1}
            boton = next(elemento for elemento in cliente.elements.values()
                         if isinstance(elemento, ui.button) and elemento.text == "Calcular determinante")
            await vista.calcular(SimpleNamespace(sender=boton))
            assert vista.ultimo_resultado is None
            assert boton._props['loading'] == 'false'
            assert vista.obtener_contexto_ia().resultado is None
            assert any(isinstance(elemento, ui.label) and "No pudimos calcular" in elemento.text
                       for elemento in cliente.elements.values())
        cliente.delete()
    asyncio.run(comprobar())
