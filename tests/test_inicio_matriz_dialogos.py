"""Semántica, estados, disposición y contraste del inicio."""
import asyncio
from dataclasses import replace
from pathlib import Path
import re

from src.frontend.controladores.inicio._modelo import acceso_destacado
from src.frontend.navegacion import consultas
from src.frontend.navegacion.secciones_inicio import secciones_inicio
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, razon_contraste,
    leer_css_inicio, buscar_cierre_bloque, bloque_css,
)


RUTA_CSS_TEMAS = Path("src/frontend/recursos/css/tokens.css")
RUTA_JS_INICIO = Path("src/frontend/recursos/js/inicio.js")


def quitar_comentarios(css: str) -> str:
    """Retira comentarios CSS para inspeccionar solo declaraciones activas."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def test_contrato_dom_secciones_y_enlaces_nativos(monkeypatch):
    """El directorio monta secciones con título y enlaces nativos con destino."""
    async def comprobar(vista, cliente):
        """Inspecciona la semántica y los destinos montados por la portada."""
        elementos = tuple(cliente.elements.values())
        directorio = next(elemento for elemento in elementos if "inicio-directorio" in elemento.classes)
        assert "data-directorio-listo" in directorio._props
        contenido = tuple(directorio.descendants())
        secciones = [elemento for elemento in contenido if "inicio-seccion" in elemento.classes]
        enlaces = [elemento for elemento in contenido if "inicio-enlace" in elemento.classes]
        assert len(secciones) == 5
        assert directorio.tag == "nav"
        assert directorio._props["aria-labelledby"] == "inicio-herramientas"
        assert [seccion.style.get("--inicio-indice") for seccion in secciones] == ["0", "1", "2", "3", "4"]
        assert all(seccion.tag == "section" for seccion in secciones)
        for seccion in secciones:
            titulo = next(elemento for elemento in seccion.descendants()
                          if elemento._props.get("tag", elemento.tag) in {"h2", "h3"})
            assert seccion._props["aria-labelledby"] == titulo._props["id"]
        assert len(enlaces) == 15
        assert all(enlace.tag == "a" and enlace._props.get("href") for enlace in enlaces)
        assert all(enlace._props.get("data-clave") for enlace in enlaces)
        assert not any(elemento.tag == "dialog" for elemento in contenido)

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


def test_contrato_cliente_directorio():
    """El cliente añade gestos a los enlaces sin sustituir su activación nativa."""
    fuente = RUTA_JS_INICIO.read_text(encoding="utf-8")

    fuente_recientes = Path("src/frontend/recursos/js/inicio_recientes.js").read_text(encoding="utf-8")
    assert "window.scalaris.recientes =" in fuente_recientes
    assert "leer: leerRecientes" in fuente_recientes
    assert "registrar: registrarVisita" in fuente_recientes
    assert "window.scalarisHubSelect" not in fuente
    assert "data-gesto-inicio" in fuente
    assert ".inicio-simbolo" in fuente
    assert "showModal(" not in fuente
    assert "preventDefault(" not in fuente
    assert ".focus(" not in fuente
    assert "addEventListener('popstate'" not in fuente

    assert not re.search(r"addEventListener\s*\(\s*['\"]scroll['\"]", fuente)
    assert ".onscroll" not in fuente
    for retirados in (
        "hub-carousel",
        "hub-viewport",
        "hub-track",
        "hub-card",
        "hub-panel",
        "hub-nav-btn",
        "ResizeObserver",
        "onPointerDown",
        "onWheel",
        "scalarisHubSelect",
    ):
        assert retirados not in fuente


def test_acceso_predeterminado_destaca_sistemas(monkeypatch):
    """El vínculo destacado abre Sistemas durante el montaje."""
    seleccionado = acceso_destacado()
    assert seleccionado.identificador == "sistemas"
    assert "catch (_) { return { valido: false, identificadores: [] }; }" in Path(
        "src/frontend/recursos/js/inicio_recientes.js"
    ).read_text(encoding="utf-8")

    async def comprobar(vista, cliente):
        """Comprueba el destino del enlace destacado en la portada montada."""
        destacado = next(elemento for elemento in cliente.elements.values()
                         if "inicio-destacado" in elemento.classes)
        assert destacado.tag == "a"
        assert destacado._props["href"] == seleccionado.ruta

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


def test_renderizado_herramientas_vacias_y_cantidades_variables(monkeypatch):
    """Los grupos vacíos se omiten y los accesos con textos largos permiten saltos."""
    catalogo = tuple(replace(herramienta, habilitada=False)
                     if herramienta.identificador_pilar == "utilidades" else herramienta
                     for herramienta in consultas.HERRAMIENTAS)
    monkeypatch.setattr(consultas, "HERRAMIENTAS", catalogo)
    assert [seccion.identificador for seccion in secciones_inicio()] == [
        "sistemas-lineales", "matrices", "vectores-geometria",
    ]
    css = leer_css_inicio()
    assert "overflow-wrap: anywhere" in bloque_css(css, ".inicio-enlace {")
    assert "-webkit-line-clamp:" not in css
    assert "line-clamp:" not in css

def test_css_inicio_usa_tokens_y_efectos_permitidos():
    """Las reglas usan tokens definidos y evitan efectos y capas no autorizados."""
    from tests.comun import leer_css_completo
    css_completo = leer_css_completo()
    css = quitar_comentarios(leer_css_inicio())

    assert "100vh" not in css
    assert "backdrop-filter" not in css
    assert "blur(" not in css
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert not re.search(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", css)
    selectores_retirados = re.compile(
        r"\.hub-(?:carousel|viewport|track|card(?=[\s.:#\[,>]|$)|nav-btn|"
        r"panels|panel(?=[\s.:#\[,>]|$)|aug)(?![a-zA-Z0-9_-])"
    )
    assert not selectores_retirados.search(css)

    tokens_definidos = set(re.findall(r"(--[a-zA-Z0-9_-]+)\s*:", quitar_comentarios(css_completo)))
    tokens_usados = set(re.findall(r"var\(\s*(--[a-zA-Z0-9_-]+)", css))
    assert tokens_usados - tokens_definidos <= {"--inicio-indice"}
    assert "var(--inicio-indice, 0)" in css

    indices_elevacion = [
        int(valor)
        for valor in re.findall(r"z-index\s*:\s*(\d+)", css, re.IGNORECASE)
        if int(valor) > 10
    ]
    assert indices_elevacion == []


def test_efecto_puntero_inicio_requiere_precision():
    """Todas las reglas hover están dentro de la consulta de puntero preciso."""
    css = quitar_comentarios(leer_css_inicio())
    patron_medios = re.compile(
        r"@media\s*\(hover:\s*hover\)\s*and\s*\(pointer:\s*fine\)\s*\{",
        re.IGNORECASE,
    )
    rangos_medios = []
    for coincidencia in patron_medios.finditer(css):
        indice_apertura = css.find("{", coincidencia.start())
        rangos_medios.append((coincidencia.start(), buscar_cierre_bloque(css, indice_apertura)))

    for regla_puntero in re.finditer(r":hover\b", css):
        assert any(inicio < regla_puntero.start() < fin for inicio, fin in rangos_medios), (
            f":hover fuera de la media query de puntero preciso: {css[regla_puntero.start()-40:regla_puntero.start()+20]}"
        )


def test_fondo_activo_definido_en_cuatro_bloques_tematicos():
    """La raíz y los tres temas conservan el token de fondo activo."""
    css_completo = RUTA_CSS_TEMAS.read_text(encoding="utf-8")
    todos_bloques = re.findall(r"(:root[^\{]*)\{([^}]+)\}", css_completo, re.DOTALL)
    bloques = [b for b in todos_bloques if "--hub-card-active-bg" in b[1]]

    assert len(bloques) == 4
    assert css_completo.count("--hub-card-active-bg:") == 4
    token = re.compile(
        r"--hub-card-active-bg\s*:\s*color-mix\(\s*in\s+srgb\s*,\s*"
        r"var\(--accent\)\s+(\d+)%\s*,\s*var\(--bg-elevated\)\s*\)"
    )
    for selector, cuerpo in bloques:
        assert token.search(cuerpo), f"Falta el token de fondo activo en {selector.strip()}"


def test_fondo_activo_conserva_contraste_en_todos_los_temas():
    """La mezcla del fondo activo mantiene contraste AA para sus textos."""
    css_completo = RUTA_CSS_TEMAS.read_text(encoding="utf-8")
    coincidencia = re.search(
        r"--hub-card-active-bg\s*:\s*color-mix\(\s*in\s+srgb\s*,\s*"
        r"var\(--accent\)\s+(\d+)%\s*,\s*var\(--bg-elevated\)",
        css_completo,
    )
    assert coincidencia is not None
    porcentaje_acento = int(coincidencia.group(1)) / 100
    temas = analizar_tokens(RUTA_CSS_TEMAS, pasadas=1, exigir_cierre=False)

    for nombre_tema in ("papel", "marea", "medianoche"):
        tema = temas[nombre_tema]
        acento = hexadecimal_a_rgb(tema["--accent"], limpiar_espacios=False)
        superficie_elevada = hexadecimal_a_rgb(tema["--bg-elevated"], limpiar_espacios=False)
        fondo_activo = tuple(
            porcentaje_acento * canal_acento + (1 - porcentaje_acento) * canal_elevado
            for canal_acento, canal_elevado in zip(acento, superficie_elevada)
        )
        for color_frente in ("--text-main", "--text-sec", "--accent"):
            proporcion = razon_contraste(hexadecimal_a_rgb(tema[color_frente], limpiar_espacios=False), fondo_activo)
            assert proporcion >= 4.5, (
                f"Contraste de {color_frente} en {nombre_tema}: {proporcion:.2f}:1 < 4.5:1"
            )


def test_disposicion_directorio_y_foco_visible():
    """El directorio se apila, ajusta los textos y conserva el foco visible."""
    css = leer_css_inicio()
    raiz = bloque_css(css, ".inicio-raiz {")
    assert "width: 100%" in raiz and "max-width: 71rem" in raiz
    assert "min-width: 0" in raiz
    assert "grid-template-columns: minmax(0, .92fr) minmax(0, 1.08fr)" in css
    estrecho = bloque_css(css, "@container (max-width: 40rem)")
    assert ".inicio-secciones" in estrecho
    assert "grid-template-columns: minmax(0, 1fr)" in estrecho
    assert not re.search(r"data-inicio-dialogo-abierto|\.inicio-dialogo::backdrop", css)
    foco = bloque_css(css, ".inicio-tema button):focus-visible")
    assert "outline: 2px solid var(--focus-ring)" in foco
    assert "outline-offset: 2px" in foco
