"""Carga de matrices por las rutas reales y conservación de campos auxiliares."""
import asyncio
from unittest.mock import Mock
import pytest
from nicegui import ui

from src.frontend.componentes import transferencia
from src.frontend.vistas.sistemas_lineales._transferencia_sistemas import procesar_transferencia_matriz
from tests.comun_construccion_vistas import construir_pagina, VISTAS_RUTAS
from tests.comun_transferencia_matriz import (
    MATRIZ_TRANSFERIDA, DESTINOS_MATRICIALES, preparar_ruta_lu, leer_matriz,
)


@pytest.mark.parametrize("herramienta", DESTINOS_MATRICIALES)
def test_ruta_recibe_matriz_exacta_sin_calcular(monkeypatch, herramienta):
    """Todos los destinos consumen handoff y montan un aviso de estado accesible."""
    preparar_ruta_lu(monkeypatch)
    limpiar = Mock()
    monkeypatch.setattr(transferencia, "limpiar_url_transferencia", limpiar)
    token = transferencia.guardar_matriz("determinantes", MATRIZ_TRANSFERIDA)

    async def comprobar(vista, cliente):
        """Comprueba captura exacta, ausencia de cálculo y aviso en el contenedor."""
        assert leer_matriz(vista, herramienta) == MATRIZ_TRANSFERIDA
        assert vista.ultimo_resultado is None
        etiquetas = [elemento.text for elemento in vista.contenedor_transferencia.descendants()
                     if isinstance(elemento, ui.label)]
        assert any("2×2" in texto and "Determinantes" in texto for texto in etiquetas)
        assert any(elemento._props.get("role") == "status"
                   for elemento in vista.contenedor_transferencia.descendants())
        limpiar.assert_called_once_with()
        assert transferencia.consumir_matriz(token, dimension_maxima=50).estado == "ausente"
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar, {"handoff": token}))


def test_matrices_carga_solo_a_sin_perder_ediciones_de_b_y_c(monkeypatch):
    """La carga focalizada conserva otras matrices, dimensiones y expresión."""
    async def comprobar(vista, cliente):
        """Carga A sobre una colección editada, con un único aviso de cambio."""
        panel = vista.panel_captura_matrices
        panel.cargar_datos({"A": [["9"]], "B": [["1/3", "2"]], "C": [["7"]]})
        panel.matrices["B"]["entradas"][0][1].set_value("-5/7")
        vista.entrada_expresion.set_value("A+B")
        observador = Mock(wraps=panel.al_cambiar_datos)
        panel.al_cambiar_datos = observador
        panel.cargar_matriz_a(MATRIZ_TRANSFERIDA)
        capturas = panel.obtener_datos_crudos()
        assert capturas["A"]["datos"] == MATRIZ_TRANSFERIDA
        assert capturas["B"]["datos"] == [["1/3", "-5/7"]]
        assert capturas["C"]["datos"] == [["7"]]
        assert vista.entrada_expresion.value == "A+B" and vista.ultimo_resultado is None
        observador.assert_called_once_with()
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_sistemas_recepcion_retira_modo_homogeneo_y_deja_b_vacio(monkeypatch):
    """La captura recibida permite completar b aunque antes se estuviera en Ax=0."""
    async def comprobar(vista, cliente):
        """Recibe sobre una sesión homogénea con términos anteriores."""
        vista.casilla_homogeneo.set_value(True)
        token = transferencia.guardar_matriz("inversa", MATRIZ_TRANSFERIDA)
        procesar_transferencia_matriz(vista, token)
        assert not vista.casilla_homogeneo.value and not vista.cuadricula.modo_homogeneo
        assert leer_matriz(vista, "sistemas") == MATRIZ_TRANSFERIDA
        assert all(entrada.value == "" for entrada in vista.cuadricula.entradas_independientes)
    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))


def test_variante_matrices_determinante_propaga_handoff(monkeypatch):
    """La ruta compatible con operacion=determinante no pierde la transferencia."""
    monkeypatch.setitem(VISTAS_RUTAS, "matrices",
                        ("operaciones_matrices.vista_determinante", "VistaDeterminante"))
    token = transferencia.guardar_matriz("inversa", MATRIZ_TRANSFERIDA)

    async def comprobar(vista, cliente):
        """Comprueba que se construyó Determinantes con la matriz recibida."""
        assert leer_matriz(vista, "determinantes") == MATRIZ_TRANSFERIDA
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar,
                                {"operacion": "determinante", "handoff": token}))
