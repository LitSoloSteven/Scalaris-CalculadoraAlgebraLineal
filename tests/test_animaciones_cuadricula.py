"""Invocaciones Python de animaciones verificadas contra los recursos reales del cliente."""
import asyncio

import pytest

from src.frontend.componentes import cuadricula_base
from tests.comun_animaciones_cliente import observar_invocaciones_cliente


@pytest.mark.parametrize("metodo, duracion", [
    (cuadricula_base.animar_entrada_cuadricula, 450),
    (cuadricula_base.animar_salida_cuadricula, 340),
])
@pytest.mark.parametrize("nombre_matriz", ["A", None])
@pytest.mark.parametrize("selector", [
    "[data-matriz-fila='0']", '[data-matriz-columna="1"]',
    "[data-ecuaciones-fila='0'];globalThis.inyeccion_detectada=true;//",
])
def test_codigo_emitido_conserva_selector_y_ejecuta_animacion(monkeypatch, metodo, duracion, nombre_matriz, selector):
    """Las comillas del selector permanecen como datos y se llama a la API disponible."""
    codigos = []

    async def registrar_codigo(codigo):
        """Procesa registrar codigo con los datos recibidos."""
        codigos.append(codigo)

    monkeypatch.setattr(cuadricula_base.ui, "run_javascript", registrar_codigo)
    asyncio.run(metodo(selector, nombre_matriz=nombre_matriz))
    assert len(codigos) == 1
    observacion = observar_invocaciones_cliente(codigos)[0]
    esperado = f"input[data-matriz-identificador='{nombre_matriz}']{selector}" if nombre_matriz else selector
    assert observacion["selectores"] == [esperado]
    assert observacion["duraciones"] == [duracion]
    assert observacion["inyeccion"] is False
