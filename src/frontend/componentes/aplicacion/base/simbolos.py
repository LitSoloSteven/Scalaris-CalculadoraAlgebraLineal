"""Acceso por teclado y puntero al selector de símbolos desde los campos de expresión."""
import html
import json
from nicegui import ui


def habilitar_simbolos(campo, perfil: str, *, atajos: str = "") -> None:
    """Identifica el perfil de símbolos del campo y declara sus atajos de teclado."""
    teclas = ("Control+Shift+Space " + atajos).strip()
    campo.props(f'data-simbolos={perfil} aria-keyshortcuts="{teclas}"')


def renderizar_boton_simbolos(etiqueta: str = "Símbolos", *, campo_objetivo: str = "") -> ui.button:
    """Renderiza un botón accesible de al menos 44 px para abrir el selector de símbolos."""
    selector = f"document.getElementById({json.dumps(campo_objetivo)})" if campo_objetivo else "null"
    codigo = f"window.scalaris?.selectorSimbolos?.abrir?.({selector});"
    extra = f' data-campo-simbolos="{html.escape(campo_objetivo, quote=True)}"' if campo_objetivo else ""
    return ui.button(
        etiqueta,
        icon="functions",
        color=None,
        on_click=lambda: ui.run_javascript(codigo),
    ).classes("boton-discreto px-3 text-xs").props(
        f'flat no-caps ripple=false data-abrir-simbolos aria-label="Abrir selector de símbolos"{extra}'
    ).tooltip("Abrir selector de símbolos (Ctrl+Mayús+Espacio)")
