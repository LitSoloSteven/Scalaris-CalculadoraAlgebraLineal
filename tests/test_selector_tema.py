"""Conexión del menú con la selección local y el origen de su activación."""
from src.frontend.componentes import selector_tema


def test_opciones_de_tema_delegan_en_cliente_sin_viaje_al_servidor(monkeypatch):
    """El menú expone sus valores sin callbacks que pierdan el evento original."""
    opciones_creadas = []
    crear_elemento = selector_tema.ui.menu_item

    def registrar_opcion(*argumentos, **opciones):
        """Conserva las propiedades y eventos del componente real."""
        elemento = crear_elemento(*argumentos, **opciones)
        opciones_creadas.append((elemento, opciones))
        return elemento

    monkeypatch.setattr(selector_tema.ui, "menu_item", registrar_opcion)
    boton = selector_tema.renderizar_boton_tema()
    assert boton is not None
    assert len(opciones_creadas) == 3
    assert all("on_click" not in argumentos for _, argumentos in opciones_creadas)
    assert [elemento._props["data-tema-opcion"] for elemento, _ in opciones_creadas] == [
        "papel", "marea", "medianoche",
    ]
    assert all(elemento._props["role"] == "menuitemradio" for elemento, _ in opciones_creadas)
