"""Contrato de los controles de la cabecera de inicio en una portada estrecha."""
import asyncio

from tests.comun_construccion_vistas import construir_pagina


def test_cabecera_agrupa_el_control_de_sonido_y_el_selector_de_tema(monkeypatch):
    """La portada monta una sola instancia del control compartido junto al tema."""
    async def comprobar(_vista, cliente):
        """Comprueba la estructura y los nombres accesibles de ambos botones."""
        elementos = cliente.elements.values()
        cabecera, = (elemento for elemento in elementos if "inicio-cabecera" in elemento.classes)
        zona, = (elemento for elemento in cabecera.descendants() if "inicio-controles" in elemento.classes)
        sonido, = (elemento for elemento in elementos if "data-sonido-control" in elemento._props)
        controles = tuple(zona.descendants())
        assert sonido in controles
        assert sonido._props["aria-pressed"] == "false"
        tema, = (elemento for elemento in controles if "selector-tema-textual" in elemento.classes)
        assert tema._props["aria-haspopup"] == "menu"

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))
