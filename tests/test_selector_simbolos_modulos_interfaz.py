"""Contratos de vista, metadato de módulo y perfiles de campos en la interfaz."""
import asyncio
from types import SimpleNamespace

from nicegui import ui

from src.frontend import tema
from src.frontend.componentes.borrador_intervalo_raices import construir_borrador
from src.frontend.componentes.captura_exploracion_raices import campos_rango
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


def test_configurar_tema_inyecta_meta_modulo_escapada_en_una_cabecera(monkeypatch):
    """La cabecera principal declara el módulo activo con escape HTML y sin duplicarse."""
    cabeceras = []
    monkeypatch.setattr(tema.ui, "add_head_html", cabeceras.append)
    monkeypatch.setattr(tema.banderas, "panel_lateral_habilitado", lambda: False)

    tema.configurar_tema("sistemas")
    assert len(cabeceras) == 1
    assert '<meta name="scalaris-modulo" content="sistemas">' in cabeceras[0]

    cabeceras.clear()
    tema.configurar_tema('sistemas"><script>')
    assert '<meta name="scalaris-modulo" content="sistemas&quot;&gt;&lt;script&gt;">' in cabeceras[0]

    cabeceras.clear()
    tema.configurar_tema()
    assert len(cabeceras) == 1
    assert 'name="scalaris-modulo"' not in cabeceras[0]


def test_campos_de_bases_y_romanos_declaran_sus_perfiles(monkeypatch):
    """El conversor de bases y la calculadora romana asignan perfiles propios."""
    async def _comprobar_bases(vista, cliente):
        """Verifica metadato de módulo y perfil del campo en bases."""
        assert '<meta name="scalaris-modulo" content="bases">' in cliente.head_html
        assert vista.entrada_valor._props.get("data-simbolos") == "base"

    async def _comprobar_romanos(vista, cliente):
        """Verifica metadato de módulo y perfil de operandos romanos."""
        assert '<meta name="scalaris-modulo" content="romanos">' in cliente.head_html
        assert vista.entrada_a._props.get("data-simbolos") == "romano"
        assert vista.entrada_b._props.get("data-simbolos") == "romano"

    asyncio.run(construir_pagina(monkeypatch, "bases", _comprobar_bases))
    asyncio.run(construir_pagina(monkeypatch, "romanos", _comprobar_romanos))


def test_campos_de_metodos_abiertos_declaran_perfiles_real_y_entero(monkeypatch):
    """Newton-Raphson y secante distinguen función, reales e iteraciones enteras."""
    async def _comprobar(vista, cliente):
        """Verifica perfiles de función, reales y enteros en métodos abiertos."""
        assert '<meta name="scalaris-modulo" content="metodos_abiertos">' in cliente.head_html
        assert vista.expresion._props.get("data-simbolos") == "funcion"
        for campo in (vista.x0, vista.x1, vista.tolerancia):
            assert campo._props.get("data-simbolos") == "real"
        assert vista.limite._props.get("data-simbolos") == "entero"

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", _comprobar))


def test_campos_de_metodos_cerrados_declaran_perfiles_real_y_entero(monkeypatch):
    """Métodos cerrados asigna perfil real o entero a captura, exploración y lote."""
    monkeypatch.setitem(
        VISTAS_RUTAS, "metodos_cerrados", ("metodos_cerrados.vista_metodos_cerrados", "VistaMetodosCerrados"),
    )

    async def _comprobar(vista, cliente):
        """Verifica perfiles en captura, exploración y lote de métodos cerrados."""
        assert '<meta name="scalaris-modulo" content="metodos_cerrados">' in cliente.head_html
        captura = vista.captura
        assert captura.expresion._props.get("data-simbolos") == "funcion"
        for campo in (captura.inferior, captura.superior, captura.minimo, captura.maximo,
                      vista.exploracion.minimo, vista.exploracion.maximo, vista.exploracion.paso):
            assert campo._props.get("data-simbolos") == "real"
        for tipo in ("relativo", "ancho", "residuo"):
            assert captura.parametros_criterio[tipo]._props.get("data-simbolos") == "real"
        for campo_entero in (captura.limite, vista.exploracion.lote.presupuesto,
                             captura.parametros_criterio["decimales"],
                             captura.parametros_criterio["iteraciones"]):
            assert campo_entero._props.get("data-simbolos") == "entero"

    asyncio.run(construir_pagina(monkeypatch, "metodos_cerrados", _comprobar))


def test_componentes_compartidos_de_raices_declaran_perfil_real():
    """El rango de exploración y el borrador gráfico declaran el perfil real."""
    seleccion = SimpleNamespace(
        inicio=None, region=None, campos=(), estado=None,
        iniciar=lambda: None, confirmar=lambda: None, cancelar=lambda **_: None,
    )
    with ui.column() as contenedor:
        try:
            minimo, maximo = campos_rango("intervalo", "row")
            construir_borrador(seleccion, "Elige extremos", lambda: None)
            assert minimo._props.get("data-simbolos") == "real"
            assert maximo._props.get("data-simbolos") == "real"
            assert [campo._props.get("data-simbolos") for campo in seleccion.campos] == ["real", "real"]
        finally:
            contenedor.delete()
