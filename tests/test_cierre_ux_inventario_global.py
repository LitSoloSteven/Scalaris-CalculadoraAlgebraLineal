"""Inventario global de rutas sin placeholders, logo limpio y autoajuste."""
import asyncio
from pathlib import Path

import pytest
from nicegui import Client, core, ui

from src.frontend.componentes.aplicacion.controles.barra_navegacion import crear_barra_navegacion
from src.frontend.nucleo.textos.textos_espacio_vectorial import MODO_PERSONALIZADO
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina
from tests.comun_estilos import bloque_css

_RUTAS_COMPLEMENTARIAS = {
    "metodos_iterativos": ("algebra.sistemas_lineales.vista_metodos_iterativos", "VistaMetodosIterativos"),
    "espacios_subespacios": ("algebra.operaciones_vectores.vista_espacios_subespacios", "VistaEspaciosSubespacios"),
    "factorizacion_lu": ("algebra.operaciones_matrices.factorizacion_lu.vista_factorizacion_lu", "VistaFactorizacionLU"),
    "metodos_cerrados": ("raices.metodos_cerrados.vista_metodos_cerrados", "VistaMetodosCerrados"),
}

_RUTAS_HERRAMIENTAS = [
    ("sistemas", None),
    ("metodos_iterativos", None),
    ("matrices", None),
    ("inversa", None),
    ("determinantes", None),
    ("factorizacion_lu", None),
    ("leontief", None),
    ("transformaciones", None),
    ("vectores", None),
    ("espacios_subespacios", {"modo": "generadores"}),
    ("espacios_subespacios", {"modo": "restricciones"}),
    ("espacios_subespacios", {"modo": MODO_PERSONALIZADO}),
    ("visualizador", {"escena": "rectas-planos"}),
    ("visualizador", {"escena": "vectores"}),
    ("visualizador", {"escena": "combinacion"}),
    ("bases", None),
    ("romanos", None),
    ("metodos_cerrados", None),
    ("metodos_abiertos", None),
]


@pytest.fixture
def _catalogo_completo(monkeypatch):
    for clave, destino in _RUTAS_COMPLEMENTARIAS.items():
        monkeypatch.setitem(VISTAS_RUTAS, clave, destino)


def _sin_placeholder_en_campos(cliente: Client) -> None:
    """Comprueba que ningun campo de texto activo conserve atributo placeholder."""
    for elemento in cliente.elements.values():
        if isinstance(elemento, (ui.input, ui.textarea)):
            assert "placeholder" not in elemento._props


def _sin_controles_de_ejemplo(cliente: Client) -> None:
    """Comprueba que botones, pestanas y selectores omitan muestras o ejemplos."""
    for elemento in cliente.elements.values():
        if isinstance(elemento, ui.button):
            assert "ejemplo" not in (elemento.text or "").lower()
        elif isinstance(elemento, ui.tab):
            assert "ejemplo" not in str(elemento._props.get("label") or "").lower()
        elif isinstance(elemento, ui.select):
            assert "ejemplo" not in str(elemento._props.get("label") or "").lower()


def _verificar_estado_vacio_inicial(vista) -> None:
    """Confirma que las vistas con comprobacion de vacio inicien sin datos de ejercicio."""
    if callable(getattr(vista, "esta_completamente_vacio", None)):
        assert vista.esta_completamente_vacio() is True


@pytest.mark.parametrize(("herramienta", "parametros"), _RUTAS_HERRAMIENTAS)
def test_rutas_activas_sin_placeholders_ni_ejemplos(monkeypatch, _catalogo_completo, herramienta, parametros):
    """Todas las herramientas activas abren sin placeholders ni controles de ejemplo."""
    async def comprobar(vista, cliente):
        _sin_placeholder_en_campos(cliente)
        _sin_controles_de_ejemplo(cliente)
        _verificar_estado_vacio_inicial(vista)

    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar, parametros))


def test_portada_y_dialogo_simbolos_sin_placeholders(monkeypatch):
    """La portada y la plantilla de simbolos omiten placeholders de muestra."""
    async def comprobar(_vista, cliente):
        _sin_placeholder_en_campos(cliente)

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))
    plantilla = Path("src/frontend/recursos/plantillas/cabecera/simbolos.html").read_text(encoding="utf-8")
    assert "placeholder=" not in plantilla
    assert 'aria-describedby="simbolos-ayuda-busqueda"' in plantilla


def test_bases_y_romanos_muestran_rotulos_persistentes(monkeypatch):
    """Los campos numericos conservan etiquetas visibles asociadas fuera del placeholder."""
    async def comprobar_bases(vista, cliente):
        etiquetas = [el for el in cliente.elements.values() if el._props.get("id") == "bases-etiqueta-entrada"]
        assert len(etiquetas) == 1
        assert vista.entrada_valor._props.get("aria-labelledby") == "bases-etiqueta-entrada"
        assert vista.entrada_valor._props.get("aria-label") == "Número de entrada"

    async def comprobar_romanos(vista, cliente):
        etiqueta_a = [el for el in cliente.elements.values() if el._props.get("id") == "romanos-etiqueta-a"]
        etiqueta_b = [el for el in cliente.elements.values() if el._props.get("id") == "romanos-etiqueta-b"]
        assert len(etiqueta_a) == 1 and len(etiqueta_b) == 1
        assert vista.entrada_a._props.get("aria-label") == "Operando A"
        assert vista.entrada_b._props.get("aria-label") == "Operando B"

    asyncio.run(construir_pagina(monkeypatch, "bases", comprobar_bases))
    asyncio.run(construir_pagina(monkeypatch, "romanos", comprobar_romanos))


def test_barra_contextual_renderiza_logo_sin_circulo_decorativo(monkeypatch):
    """El acceso a Inicio omite la clase de pastilla y mantiene transparencia en reposo."""
    monkeypatch.setattr(core, "script_mode", False)
    monkeypatch.setenv("SCALARIS_NAV", "1")
    cliente = Client(ui.page("/prueba_logo_sin_circulo"))
    try:
        with cliente:
            crear_barra_navegacion(ruta_activa="/algebra-lineal/sistemas")
        enlace = next(el for el in cliente.elements.values() if "navegacion-inicio" in el.classes)
        assert "navegacion-accion" not in enlace.classes
        assert enlace._props.get("href") == "/"
        assert enlace._props.get("aria-label") == "Inicio"
        contenido = "".join(getattr(h, "content", "") for h in enlace.descendants() if isinstance(h, ui.html))
        assert "/assets/LogoOscuro.png" in contenido and "/assets/LogoClaro.png" in contenido
    finally:
        cliente.delete()

    css = Path("src/frontend/recursos/css/utilidades/vistas_navegacion.css").read_text(encoding="utf-8")
    bloque = bloque_css(css, ".navegacion-inicio {")
    assert "background: transparent;" in bloque
    assert "box-shadow: none;" in bloque


def test_estilos_de_captura_aseguran_autoajuste_y_scroll_interno():
    """Las hojas compartidas contienen min-width 0 y centrado seguro para el reflujo."""
    entradas = Path("src/frontend/recursos/css/componentes/componentes_entradas.css").read_text(encoding="utf-8")
    assert ".matriz-entrada .q-field__inner" in entradas
    assert "min-width: 0;" in bloque_css(entradas, ".cuadricula-desplazamiento {")
    assert "align-items: stretch;" in bloque_css(entradas, ".cuadricula-contenido { padding:")

    sesion = Path("src/frontend/recursos/css/algebra/espacios/vistas_sesion_matricial.css").read_text(encoding="utf-8")
    assert ".sistemas-panel-captura {" in sesion
    assert "min-width: 0;" in bloque_css(sesion, ".sistemas-panel-captura .cuadricula-area-desplazamiento {")

    geometria = Path("src/frontend/recursos/css/algebra/espacios/vistas_geometria.css").read_text(encoding="utf-8")
    assert "align-items: safe center;" in bloque_css(geometria, ".geometria-captura-centrada .cuadricula-area-desplazamiento {")
    assert "flex: 1 1 min(100%, 13.5rem);" in bloque_css(geometria, ".geometria-captura-centrada .vectores-captura-tarjeta {")
    assert "min-height: 44px;" in bloque_css(geometria, ".geometria-captura-centrada .vectores-captura-cabecera {")


def test_estilos_de_tablas_y_glosa_contienen_desbordamiento():
    """Las tablas de raices y campos de Glosa contienen desplazamiento y separan el rotulo."""
    tablas = Path("src/frontend/recursos/css/componentes/tablas_resultados.css").read_text(encoding="utf-8")
    assert "inline-size: 100%;" in bloque_css(tablas, ".tabla-resultados {")
    bloque_tabla_media = bloque_css(tablas, ".tabla-resultados .q-table__middle {")
    assert "inline-size: 100%;" in bloque_tabla_media
    assert "overscroll-behavior-x: contain;" in bloque_tabla_media

    glosa_lateral = Path("src/frontend/recursos/css/glosa/vistas_glosa_panel_lateral.css").read_text(encoding="utf-8")
    assert "padding: var(--space-1) var(--space-3) !important;" in bloque_css(glosa_lateral, ".glosa-entrada .q-field__control {")
    assert "padding-top:" in bloque_css(glosa_lateral, ".glosa-entrada .q-field__native,")

    glosa_bitacora = Path("src/frontend/recursos/css/glosa/vistas_glosa_bitacora.css").read_text(encoding="utf-8")
    assert "text-align: left !important;" in bloque_css(glosa_bitacora, ".glosa-campo-entrada.matriz-entrada .q-field__native {")


@pytest.mark.parametrize(
    ("herramienta", "modulo_vista", "atributo_esperado"),
    [
        ("bases", "src.frontend.vistas.sistemas_numericos.bases.vista_sistemas_numericos", "entrada_valor"),
        ("romanos", "src.frontend.vistas.sistemas_numericos.romanos.vista_calculadora_romana", "entrada_a"),
    ],
)
def test_numericos_configuran_retorno_de_foco_al_limpiar(monkeypatch, herramienta, modulo_vista, atributo_esperado):
    """El boton de limpieza en Bases y Romanos apunta al primer campo de entrada al confirmar."""
    import importlib
    from src.frontend.componentes.captura.ecuaciones import limpieza_captura

    registrado = {}
    modulo = importlib.import_module(modulo_vista)
    original = limpieza_captura.crear_boton_limpieza

    def capturar_llamada(*args, **kwargs):
        registrado["campo_foco"] = kwargs.get("campo_foco")
        return original(*args, **kwargs)

    monkeypatch.setattr(modulo, "crear_boton_limpieza", capturar_llamada)

    async def comprobar(vista, _cliente):
        assert registrado["campo_foco"] is getattr(vista, atributo_esperado)

    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))
