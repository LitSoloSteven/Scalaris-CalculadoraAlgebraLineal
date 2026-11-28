"""Contrato de los controles de la cabecera de inicio en una portada estrecha."""
import asyncio

from tests.comun_construccion_vistas import construir_pagina


def test_cabecera_agrupa_el_selector_de_tema_sin_control_de_sonido(monkeypatch):
    """La portada conserva el selector de tema y oculta el control flotante de sonido."""
    async def comprobar(_vista, cliente):
        """Comprueba que la cabecera de inicio solo expone el selector de tema."""
        elementos = cliente.elements.values()
        cabecera, = (elemento for elemento in elementos if "inicio-cabecera" in elemento.classes)
        zona, = (elemento for elemento in cabecera.descendants() if "inicio-controles" in elemento.classes)
        sonidos = [elemento for elemento in elementos if "data-sonido-control" in elemento._props]
        assert sonidos == []
        controles = tuple(zona.descendants())
        tema, = (elemento for elemento in controles if "selector-tema-textual" in elemento.classes)
        assert tema._props["aria-haspopup"] == "menu"

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))
