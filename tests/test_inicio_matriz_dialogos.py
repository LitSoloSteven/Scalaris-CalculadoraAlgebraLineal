"""Contratos estáticos de la matriz, los diálogos y el contraste del inicio."""
from pathlib import Path
import re

from src.frontend.controladores.inicio._modelo import pilares_inicio, seleccion_inicial
from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, razon_contraste,
    leer_css_inicio, buscar_cierre_bloque,
)


RUTA_CSS_TEMAS = Path("src/frontend/recursos/css/tokens.css")
RUTA_JS_INICIO = Path("src/frontend/recursos/js/inicio.js")
RUTA_VISTA_INICIO = Path("src/frontend/vistas/inicio/vista_inicio.py")


def quitar_comentarios(css: str) -> str:
    """Retira comentarios CSS para inspeccionar solo declaraciones activas."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def test_contrato_dom_matriz_y_dialogos_nativos():
    """Las filas controlan diálogos nativos con nombres y relaciones accesibles."""
    fuente = RUTA_VISTA_INICIO.read_text(encoding="utf-8")
    pilares = pilares_inicio()

    assert len(pilares) == 3
    assert fuente.count("for pilar in pilares:") == 1
    assert "for indice_fila, pilar in enumerate(pilares):" in fuente
    assert 'role="group" aria-label="Áreas de Scalaris"' in fuente
    assert 'type="button" id="inicio-fila-{pilar.identificador}"' in fuente
    assert 'aria-haspopup="dialog" aria-expanded="false"' in fuente
    assert 'aria-controls="inicio-dialogo-{pilar.identificador}"' in fuente
    assert "ui.element('dialog').classes('inicio-dialogo').props(atributos_dialogo)," in fuente
    assert 'aria-labelledby="inicio-dialogo-titulo-{pilar.identificador}"' in fuente
    assert "titulo.props(f'id=\"inicio-dialogo-titulo-{pilar.identificador}\"')" in fuente
    assert "ui.element('dialog')" in fuente

    fuente_filas = fuente.split("ui.element('button').classes('inicio-fila ' + _CLASES_ORDEN[indice_fila])", 1)[1]
    fuente_filas = fuente_filas.split("self.filas[pilar.identificador]", 1)[0]
    assert "'h2'" not in fuente_filas
    assert "inicio-titulo-fila" in fuente_filas


def test_contrato_cliente_matriz_y_dialogos():
    """El cliente conserva apertura, cierre, foco y delegación de eventos."""
    fuente = RUTA_JS_INICIO.read_text(encoding="utf-8")

    fuente_recientes = Path("src/frontend/recursos/js/inicio_recientes.js").read_text(encoding="utf-8")
    assert "window.scalaris.recientes =" in fuente_recientes
    assert "leer: leerRecientes" in fuente_recientes
    assert "registrar: registrarVisita" in fuente_recientes
    assert "window.scalarisHubSelect" not in fuente
    assert "function abrir(" in fuente
    assert "function cerrar(" in fuente
    assert "dialogo.showModal()" in fuente
    assert "setAttribute('data-abierto'" in fuente
    assert "removeAttribute('data-abierto'" in fuente
    assert "evento.detail === 0" in fuente
    assert "addEventListener('cancel'" in fuente
    assert "objetivo === dialogo" in fuente
    assert "window.__scalarisInicioDelegado" in fuente
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

    llamadas_foco = re.findall(r"\.focus\(([^)]*)\)", fuente)
    assert llamadas_foco
    assert all("preventScroll" in argumentos and "true" in argumentos for argumentos in llamadas_foco)


def test_seleccion_predeterminada_marca_fila_y_tarjeta():
    """La selección sin historial destaca sistemas en el área de álgebra."""
    fuente = RUTA_VISTA_INICIO.read_text(encoding="utf-8")
    seleccion = seleccion_inicial(None)

    assert seleccion.identificador_pilar == "algebra"
    assert seleccion.clave_tarjeta == "sistemas"
    assert seleccion.hay_historial is False
    assert "tarjeta.classes(add='esta-destacada')" in fuente
    assert "fila.classes(add='esta-destacada')" in fuente
    assert "'Sigue aquí' if seleccion.hay_historial else 'Empieza aquí'" in fuente
    assert "scalarisHubSelect" not in fuente
    assert "catch (_) { return { valido: false, identificadores: [] }; }" in Path("src/frontend/recursos/js/inicio_recientes.js").read_text(encoding="utf-8")


def test_renderizado_herramientas_vacias_y_cantidades_variables():
    """El área vacía explica su estado y las listas admiten desplazamiento."""
    fuente = RUTA_VISTA_INICIO.read_text(encoding="utf-8")
    css = leer_css_inicio()

    assert "if len(pilar.tarjetas) == 0:" in fuente
    assert "for modelo_tarjeta in pilar.tarjetas:" in fuente
    assert "Esta área aún no tiene herramientas." in fuente
    assert ".inicio-lista-herramientas" in css
    assert "overflow-y: auto" in css
    assert "overscroll-behavior: contain" in css
    assert "overflow-wrap: anywhere" in css
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
    assert tokens_usados <= tokens_definidos

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


def test_disposicion_dialogo_y_bloqueo_desplazamiento():
    """El diálogo contiene su lista y bloquea el desplazamiento de la página."""
    css = leer_css_inicio()

    assert "width: min(92vw, 42rem)" in css
    assert "max-height: min(82dvh, 44rem)" in css
    assert ".inicio-dialogo::backdrop" in css
    assert "background: var(--scrim)" in css
    assert "html[data-inicio-dialogo-abierto]" in css
    assert "@media (max-width: 639px)" in css
    assert "max-height: 85dvh" in css
    assert "@media (max-width: 479px)" in css
    assert "grid-template-areas:\n            \"icono nombre\"\n            \"icono detalle\"" in css
