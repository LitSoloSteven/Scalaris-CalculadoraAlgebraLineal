"""Conexión del menú de temas con la API real del cliente."""
from src.frontend.componentes import selector_tema


def test_opciones_de_tema_invocan_api_de_cliente(monkeypatch):
    """Cada opción del menú real llama al tema que le corresponde."""
    manejadores = []
    codigos = []
    crear_elemento = selector_tema.ui.menu_item

    def registrar_opcion(*argumentos, **opciones):
        """Procesa registrar opcion con los datos recibidos."""
        manejadores.append(opciones["on_click"])
        return crear_elemento(*argumentos, **opciones)

    monkeypatch.setattr(selector_tema.ui, "menu_item", registrar_opcion)
    monkeypatch.setattr(selector_tema.ui, "run_javascript", codigos.append)
    boton = selector_tema.renderizar_boton_tema()
    assert boton is not None
    assert len(manejadores) == 3
    assert codigos == []
    for manejador in manejadores:
        manejador()
    assert codigos == [
        "window.scalaris.tema.establecer('papel')",
        "window.scalaris.tema.establecer('marea')",
        "window.scalaris.tema.establecer('medianoche')",
    ]
