"""Acciones de la colección de matrices y conservación de sus capturas exactas."""
import asyncio
from urllib.parse import parse_qs, urlsplit
from unittest.mock import Mock

from nicegui import ui

from src.frontend.componentes.transferencia import consumir_matriz
from tests.comun_construccion_vistas import construir_pagina


def test_anadir_sincroniza_celdas_y_no_resucita_valores_borrados(monkeypatch):
    """Reconstruir recoge las entradas actuales incluso con un caché desfasado."""
    async def comprobar(vista, cliente):
        """Agrega una tarjeta después de editar y vaciar la matriz inicial."""
        panel = vista.panel_captura_matrices
        panel.matrices["A"]["entradas"][0][0].set_value("1/1001")
        panel.matrices["A"]["cache"].clear()
        panel.matrices["A"]["cache"][(0, 1)] = "valor borrado"
        panel.agregar_matriz()
        datos = panel.obtener_datos_crudos()
        assert datos["A"]["datos"][0][:2] == ["1/1001", ""]
        assert datos["B"]["datos"] == [[""] * 3 for _ in range(3)]
        vista.entrada_expresion.set_value("A+B")
        panel.eliminar_matriz("A")
        panel.matrices["B"]["entradas"][1][1].set_value("-2/3")
        panel.agregar_matriz()
        assert panel.obtener_datos_crudos()["B"]["datos"][1][1] == "-2/3"
        assert panel.obtener_datos_crudos()["A"]["datos"][0][0] == ""
        assert vista.entrada_expresion.value == "A+B"
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_dimensiones_conservan_interseccion_y_descartan_celdas_retiradas(monkeypatch):
    """Ampliar conserva datos; reducir elimina únicamente las celdas fuera del rango."""
    async def comprobar(vista, cliente):
        """Amplía y reduce filas y columnas usando los manejadores reales."""
        panel = vista.panel_captura_matrices
        panel.cargar_datos({"A": [["1/1001", "2"], ["3", "4"]], "B": [["-7/9"]]})
        await panel.ajustar_tamano("A", incremento_filas=1)
        await panel.ajustar_tamano("A", incremento_columnas=1)
        assert panel.obtener_datos_crudos()["A"]["datos"] == [["1/1001", "2", ""], ["3", "4", ""], ["", "", ""]]
        await panel.ajustar_tamano("A", incremento_filas=-2)
        await panel.ajustar_tamano("A", incremento_columnas=-2)
        assert panel.obtener_datos_crudos()["A"]["datos"] == [["1/1001"]]
        assert panel.matrices["A"]["boton_quitar_fila"]._props["disable"]
        assert panel.matrices["A"]["boton_quitar_columna"]._props["disable"]
        await panel.ajustar_tamano("A", incremento_filas=1)
        await panel.ajustar_tamano("A", incremento_columnas=1)
        assert panel.obtener_datos_crudos()["A"]["datos"] == [["1/1001", ""], ["", ""]]
        assert panel.obtener_datos_crudos()["B"]["datos"] == [["-7/9"]]
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_flecha_transfiere_una_copia_exacta_hacia_inversa(monkeypatch):
    """La acción de la referencia conserva la captura y abre el destino con un token."""
    destinos = []
    monkeypatch.setattr(ui.navigate, "to", destinos.append)
    async def comprobar(vista, cliente):
        """Activa el botón real y consume el sobre enviado a la vista de inversa."""
        panel = vista.panel_captura_matrices
        panel.cargar_datos({"A": [["1/1001", ""], ["-2/3", "1"]]})
        antes = panel.obtener_datos_crudos()
        boton = next(elemento for elemento in cliente.elements.values()
                     if elemento._props.get("aria-label") == "Abrir matriz A en Matriz inversa")
        next(evento.handler for evento in boton._event_listeners.values() if evento.type == "click")(None)
        assert len(destinos) == 1
        destino = urlsplit(destinos[0])
        assert destino.path == "/algebra-lineal/inversa"
        token = parse_qs(destino.query)["handoff"][0]
        assert consumir_matriz(token, dimension_maxima=10).datos == [["1/1001", "0"], ["-2/3", "1"]]
        assert panel.obtener_datos_crudos() == antes
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_transferencia_no_cuadrada_informa_sin_perder_capturas(monkeypatch):
    """El rechazo de forma mantiene matrices y expresión en la misma vista."""
    destino, aviso = Mock(), Mock()
    monkeypatch.setattr(ui.navigate, "to", destino)
    monkeypatch.setattr(ui, "notify", aviso)
    async def comprobar(vista, cliente):
        """Intenta transferir un rectángulo conservando el estado de edición."""
        panel = vista.panel_captura_matrices
        panel.cargar_datos({"A": [["1/3", "2"]], "B": [["9"]]})
        vista.entrada_expresion.set_value("A+B")
        antes = panel.obtener_datos_crudos()
        vista._navegar_a_inversa("A")
        destino.assert_not_called()
        assert "debe ser cuadrada" in aviso.call_args.args[0]
        assert panel.obtener_datos_crudos() == antes
        assert vista.entrada_expresion.value == "A+B"
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_evaluacion_y_error_conservan_las_capturas(monkeypatch):
    """El éxito exacto y una referencia inexistente mantienen todas las celdas."""
    async def comprobar(vista, cliente):
        """Evalúa la suma y provoca un error sin reconstruir las entradas."""
        panel = vista.panel_captura_matrices
        panel.cargar_datos({"A": [["1/1001"]], "B": [["2/1001"]]})
        antes = panel.obtener_datos_crudos()
        vista.entrada_expresion.set_value("A+B")
        await vista.evaluar_expresion(ui.button("Evaluar prueba"))
        assert vista.ultimo_resultado["matriz_resultado"]["datos"] == [["3/1001"]]
        vista.entrada_expresion.set_value("A+C")
        await vista.evaluar_expresion(ui.button("Evaluar prueba"))
        assert vista.ultimo_resultado["estado"] == "ERROR"
        assert panel.obtener_datos_crudos() == antes
        assert vista.entrada_expresion.value == "A+C"
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))
