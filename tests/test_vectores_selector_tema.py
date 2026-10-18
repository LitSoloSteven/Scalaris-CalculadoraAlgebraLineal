"""Selección vectorial independiente y semántica exclusiva del menú de temas."""
import asyncio
from pathlib import Path

from nicegui import ui
from tests.comun_construccion_vistas import construir_pagina


def test_pestanas_vectoriales_independientes_conservan_operacion_y_capturas(monkeypatch):
    """Los cambios reales de pestaña mantienen las celdas de cada operación."""
    async def comprobar(vista, cliente):
        """Recorre los paneles sin reconstruir el selector de métodos de sistemas."""
        assert "pestanas-vectores" in vista.pestanas.classes
        assert "pestanas-metodo" not in vista.pestanas.classes
        assert vista.pestanas._props["outside-arrows"]
        assert vista.pestanas._props["aria-label"] == "Operaciones con vectores"
        vista.panel_suma_resta.vectores["u"]["celdas"][0] = "1/1001"
        vista.pestanas.set_value("escalar")
        assert vista.operacion_activa == "escalar"
        assert vista.panel_vectorial is vista.panel_escalar
        vista.panel_escalar.vectores["u"]["celdas"][0] = "-2/3"
        vista.pestanas.set_value("combinacion_lineal")
        assert vista.panel_vectorial is vista.panel_combinacion
        vista.pestanas.set_value("suma_resta")
        assert vista.panel_suma_resta.vectores["u"]["celdas"][0] == "1/1001"
        assert vista.panel_escalar.vectores["u"]["celdas"][0] == "-2/3"
    asyncio.run(construir_pagina(monkeypatch, "vectores", comprobar))


def test_menu_tema_tiene_opciones_de_seleccion_exclusiva(monkeypatch):
    """Cada opción declara su valor y la marca es decorativa para lectores."""
    async def comprobar(vista, cliente):
        """Inspecciona el menú real que sincroniza el recurso del navegador."""
        opciones = [elemento for elemento in cliente.elements.values()
                    if elemento._props.get("role") == "menuitemradio"]
        assert [elemento._props["data-tema-opcion"] for elemento in opciones] == ["papel", "marea", "medianoche"]
        assert all(elemento._props["aria-checked"] == "false" for elemento in opciones)
        marcas = [elemento.content for elemento in cliente.elements.values()
                  if isinstance(elemento, ui.html) and "tema-marca-activa" in elemento.content]
        assert len(marcas) == 3
        assert all('aria-hidden="true"' in marca for marca in marcas)
    asyncio.run(construir_pagina(monkeypatch, "vectores", comprobar))


def test_estilos_no_heredan_marcas_activas_de_papel():
    """La marca visual depende de aria-checked y no de tokens acumulables."""
    recursos = Path("src/frontend/recursos")
    controles = (recursos / "css/componentes_controles.css").read_text(encoding="utf-8")
    tokens = (recursos / "css/tokens.css").read_text(encoding="utf-8")
    vectores = (recursos / "css/vistas_vectores.css").read_text(encoding="utf-8")
    assert "--show-" not in tokens + controles
    assert '[data-tema-opcion][aria-checked="true"] .tema-marca-activa' in controles
    assert "visibility: hidden;" in controles
    assert ".pestanas-vectores.q-tabs--scrollable .q-tabs__content" in vectores
    assert "width: calc(100% - 72px)" in vectores
