"""La vista de determinante descarta respuestas tras editar o abandonar la página."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import Client, core, run, ui

from src.frontend.vistas.operaciones_matrices.vista_determinante import VistaDeterminante
from tests.comun_construccion_vistas import preparar_transporte


@pytest.mark.parametrize("desmontar", [False, True])
def test_respuesta_tardia_no_publica_en_captura_invalida(monkeypatch, desmontar):
    """Editar o eliminar el cliente invalida el resultado y no toca controles eliminados."""
    async def comprobar():
        """Coordina explícitamente el trabajador y la invalidación de su captura."""
        monkeypatch.setattr(core, "script_mode", False)
        cliente = Client(ui.page("/determinante_espera"))
        preparar_transporte(monkeypatch, cliente)
        preparado, terminar = asyncio.Event(), asyncio.Event()
        async def trabajador(funcion, captura):
            """Retiene el resultado hasta después de la edición o el desmontaje."""
            preparado.set()
            await terminar.wait()
            return {"estado": "EXITO", "determinante": 1, "pasos": []}
        monkeypatch.setattr(run, "io_bound", trabajador)
        with cliente:
            vista = VistaDeterminante()
            vista.construir()
            mostrar = Mock()
            monkeypatch.setattr(vista, "_mostrar_resultado", mostrar)
            boton = next(elemento for elemento in cliente.elements.values()
                         if isinstance(elemento, ui.button) and elemento.text == "Calcular determinante")
            tarea = asyncio.create_task(vista.calcular(SimpleNamespace(sender=boton)))
            await preparado.wait()
            cliente.delete() if desmontar else vista._invalidar_resultado()
            terminar.set()
            await tarea
            mostrar.assert_not_called()
            assert vista.ultimo_resultado is None
            assert vista._montada is (not desmontar)
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
            assert not vista._calculando
            assert any(isinstance(elemento, ui.label) and "No pudimos calcular" in elemento.text
                       for elemento in cliente.elements.values())
        cliente.delete()
    asyncio.run(comprobar())
