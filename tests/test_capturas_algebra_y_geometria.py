"""Contratos de redistribucion, limpieza y retiro de ejemplos en Fase 2."""
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from nicegui import ui

from src.frontend.componentes.captura.ecuaciones.limpieza_captura import LimpiezaCaptura
from src.frontend.nucleo.textos.textos_espacio_vectorial import MODO_PERSONALIZADO
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina
from tests.comun_estilos import bloque_css

_RUTAS_EXTRA = {
    "metodos_iterativos": ("algebra.sistemas_lineales.vista_metodos_iterativos", "VistaMetodosIterativos"),
    "espacios_subespacios": ("algebra.operaciones_vectores.vista_espacios_subespacios", "VistaEspaciosSubespacios"),
}


@pytest.fixture
def _rutas_completas(monkeypatch):
    for clave, destino in _RUTAS_EXTRA.items():
        monkeypatch.setitem(VISTAS_RUTAS, clave, destino)


def _leer_css(ruta: str) -> str:
    return Path(f"src/frontend/recursos/css/{ruta}").read_text(encoding="utf-8")


def test_css_expande_cuadriculas_y_distribuye_tarjetas():
    """Las hojas compartidas y modulares aplican ancho util, pestanas iguales y filas adaptables."""
    entradas = _leer_css("componentes/componentes_entradas.css")
    assert ".cuadricula-cabecera-fija, .cuadricula-contenido { width: 100%; min-width: min-content; }" in entradas
    assert "flex: 1 0 var(--cell-w);" in bloque_css(entradas, ".cuadricula-cabecera-fija .cuadricula-celda,")

    sesion = _leer_css("algebra/espacios/vistas_sesion_matricial.css")
    assert "flex: 1 1 0%;" in bloque_css(sesion, ".sesion-pestanas-herramientas .q-tab {")
    assert "background: transparent !important;" in bloque_css(sesion, ".sistemas-panel-captura .cuadricula-area-desplazamiento {")

    iterativos = _leer_css("algebra/espacios/vistas_metodos_iterativos.css")
    assert "flex-direction: column;" in bloque_css(iterativos, ".iterativos-parametros .vectores-captura-celdas.vectores-captura-columna {")

    vectores = _leer_css("algebra/espacios/vistas_vectores.css")
    subespacios = _leer_css("algebra/espacios/vistas_subespacios.css")
    for css in (vectores, subespacios):
        assert "repeat(auto-fill, minmax(min(100%, 10.5rem), 1fr))" in css
        assert "grid-template-columns: minmax(0, 1.65fr) minmax(0, 0.75fr);" in css

    geometria = _leer_css("algebra/espacios/vistas_geometria.css")
    assert ".geometria-captura-bloque {" in geometria
    assert "--cell-w: clamp(5.25rem, 8.5vw, 7rem);" in bloque_css(geometria, ".geometria-captura-centrada {")
    assert ".geometria-acciones {" in geometria


@pytest.mark.parametrize(("herramienta", "parametros"), [
    ("sistemas", None),
    ("metodos_iterativos", None),
    ("matrices", None),
    ("leontief", None),
    ("transformaciones", None),
    ("vectores", None),
    ("espacios_subespacios", {"modo": "generadores"}),
    ("espacios_subespacios", {"modo": "restricciones"}),
    ("espacios_subespacios", {"modo": MODO_PERSONALIZADO}),
    ("visualizador", {"escena": "rectas-planos"}),
    ("visualizador", {"escena": "vectores"}),
    ("visualizador", {"escena": "combinacion"}),
])
def test_vistas_fase_dos_sin_placeholders_ni_controles_de_ejemplo(monkeypatch, _rutas_completas, herramienta, parametros):
    """Ninguna vista de Fase 2 expone placeholders de muestra ni botones o selectores de ejemplo."""
    async def comprobar(_vista, cliente):
        """Recorre controles de entrada, botones y selectores buscando muestras o placeholders."""
        for elemento in cliente.elements.values():
            if isinstance(elemento, ui.input):
                placeholder = str(elemento._props.get("placeholder") or "")
                assert placeholder != "0" and not placeholder.startswith("Ej.")
            if isinstance(elemento, ui.button):
                texto = (elemento.text or "").lower()
                assert "ejemplo" not in texto
            if isinstance(elemento, ui.select):
                etiqueta = str(elemento._props.get("label") or "").lower()
                assert "ejemplo" not in etiqueta

    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar, parametros))


def test_matrices_separa_anadir_matriz_y_limpia_expresion(monkeypatch):
    """El boton Anadir matriz precede a la fila dividida y la columna captura abre con Matriz A."""
    async def comprobar(vista, cliente):
        """Comprueba disposicion de Anadir matriz, campo de expresion y estado vacio."""
        fila = next(el for el in cliente.elements.values() if "disposicion-captura-fila" in el._classes)
        assert len(fila.default_slot.children) == 2
        botones_anadir = [el for el in cliente.elements.values() if isinstance(el, ui.button) and el.text == "Añadir matriz"]
        assert len(botones_anadir) == 1
        assert botones_anadir[0] not in list(fila.descendants())
        assert "matrices-campo-expresion" in vista.entrada_expresion._classes
        assert vista.esta_completamente_vacio()

    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_iterativos_limpieza_comun_y_disposicion(monkeypatch, _rutas_completas):
    """Iterativos separa el selector sobre la fila dividida y limpia captura, resultado y Glosa."""
    async def comprobar(vista, cliente):
        """Verifica orden del selector, parametros y flujo completo de limpieza."""
        fila = next(el for el in cliente.elements.values() if "disposicion-captura-fila" in el._classes)
        assert vista.captura.selector not in list(fila.descendants())
        parametros = list(fila.default_slot.children[1].descendants())
        assert vista.captura.vector.contenedor in parametros
        assert vista.captura.tolerancia in parametros and vista.captura.maximo in parametros
        assert parametros.index(vista.captura.vector.contenedor) < parametros.index(vista.captura.tolerancia)

        botones = [el for el in cliente.elements.values() if el._props.get("id") == "boton-limpiar-principal"]
        assert len(botones) == 1
        control = LimpiezaCaptura(vista, lambda: not cliente.is_deleted)
        aviso = Mock()
        monkeypatch.setattr(ui, "notify", aviso)
        await control.confirmar()
        aviso.assert_called_once_with("No hay datos que limpiar.", type="info", position="top")

        vista.captura.cuadricula.entradas_coeficientes[0][0].set_value("4")
        vista.ultimo_resultado = {"estado": "SOLUCION_EXACTA"}
        vista._huella_resultado = "huella"
        foco = Mock()
        monkeypatch.setattr(vista.panel_ia, "limpiar_foco_explicacion", foco)
        await control.confirmar()
        monkeypatch.setattr(ui, "run_javascript", AsyncMock(side_effect=TimeoutError()))
        await control.ejecutar()
        assert vista.esta_completamente_vacio()
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        foco.assert_called()

    asyncio.run(construir_pagina(monkeypatch, "metodos_iterativos", comprobar))


def test_modelos_ocultan_nombres_en_desplegables(monkeypatch):
    """Leontief y Transformaciones mueven los nombres opcionales a secciones expansion."""
    for herramienta in ("leontief", "transformaciones"):
        async def comprobar(vista, cliente):
            """Comprueba que existan secciones expansion para nombres opcionales."""
            expansiones = [el for el in cliente.elements.values() if isinstance(el, ui.expansion)]
            etiquetas = [el._props.get("label", "") for el in expansiones]
            assert any("opcional" in etiqueta.lower() for etiqueta in etiquetas)

        asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_vectores_escalar_vacio_y_orientacion_fila(monkeypatch):
    """Operaciones con vectores inicia escalar vacio y alterna la clase de fila completa."""
    async def comprobar(vista, _cliente):
        """Comprueba escalar inicial vacio y alternancia de clase fila completa."""
        assert vista.valor_escalar == ""
        assert vista.esta_completamente_vacio()
        panel = vista.panel_suma_resta
        tarjeta = panel._tarjetas["u"]
        assert "vectores-captura-tarjeta-fila" not in tarjeta._classes
        panel.alternar_orientacion("u")
        assert "vectores-captura-tarjeta-fila" in tarjeta._classes
        panel.alternar_orientacion("u")
        assert "vectores-captura-tarjeta-fila" not in tarjeta._classes

    asyncio.run(construir_pagina(monkeypatch, "vectores", comprobar))


@pytest.mark.parametrize("modo", ["generadores", "restricciones", MODO_PERSONALIZADO])
def test_subespacios_ayuda_compacta_limpieza_y_orden(monkeypatch, _rutas_completas, modo):
    """Espacios y subespacios usa ayuda compacta, limpieza comun y conserva el orden vectorial."""
    async def comprobar(vista, cliente):
        """Comprueba ayuda compacta, orden vectorial y limpieza comun en cada modo."""
        simbolos = [el for el in cliente.elements.values() if "subespacios-ayuda-simbolo" in el._classes]
        assert len(simbolos) >= 3
        botones = [el for el in cliente.elements.values() if el._props.get("id") == "boton-limpiar-principal"]
        assert len(botones) == 1
        control = LimpiezaCaptura(vista, lambda: not cliente.is_deleted)
        assert vista.esta_completamente_vacio()

        if modo == "generadores":
            panel = vista.captura.panel
            panel.agregar_vector()
            panel.agregar_vector()
            panel.agregar_vector()
            panel.vectores["v_1"]["celdas"][0] = "5"
            panel.eliminar_vector("v_2")
            assert list(panel.vectores) == ["v_1", "v_3", "v_4"]
        else:
            vista.captura.cargar_ejemplo()

        assert not vista.esta_completamente_vacio()
        vista.ultimo_resultado = {"estado": "EXITO", "modo": modo}
        foco = Mock()
        monkeypatch.setattr(vista.panel_ia, "limpiar_foco_explicacion", foco)
        await control.confirmar()
        monkeypatch.setattr(ui, "run_javascript", AsyncMock(side_effect=TimeoutError()))
        await control.ejecutar()
        assert vista.esta_completamente_vacio()
        assert vista.ultimo_resultado is None
        foco.assert_called()

    asyncio.run(construir_pagina(monkeypatch, "espacios_subespacios", comprobar, {"modo": modo}))


@pytest.mark.parametrize("escena", ["rectas-planos", "vectores", "combinacion"])
def test_visualizador_centra_captura_sobre_acciones(monkeypatch, escena):
    """Las tres escenas agrupan la captura arriba y las acciones debajo dentro del bloque centrado."""
    async def comprobar(vista, cliente):
        """Comprueba orden de controles centrados sobre acciones en cada escena."""
        bloque = next(el for el in cliente.elements.values() if "geometria-captura-bloque" in el._classes)
        hijos = bloque.default_slot.children
        assert vista.contenedor_controles is hijos[0]
        assert "geometria-captura-centrada" in vista.contenedor_controles._classes
        acciones = next(el for el in hijos[1].descendants() if "geometria-acciones" in el._classes)
        assert any(isinstance(el, ui.button) and el._props.get("id") == "boton-limpiar-principal" for el in acciones.descendants())

    asyncio.run(construir_pagina(monkeypatch, "visualizador", comprobar, {"escena": escena}))
