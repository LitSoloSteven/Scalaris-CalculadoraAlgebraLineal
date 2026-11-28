"""Campo compartido para capturar funciones reales con el teclado."""
from nicegui import ui

from src.backend.resolutores.raices.compartido.limites_raices import LONGITUD_MAXIMA_EXPRESION
from src.frontend.componentes.aplicacion.base.simbolos import habilitar_simbolos


def crear_campo_funcion(*, valor: str = "", ejemplo: str | None = None) -> ui.input:
    """Monta el campo compartido y el acceso a los símbolos."""
    etiqueta = "Función f(x)"
    entrada = ui.input(etiqueta, value=valor) if ejemplo is None else ui.input(etiqueta, value=valor, placeholder=ejemplo)
    campo = entrada.classes("matriz-entrada w-full")
    ayuda = f"atajos-funcion-{campo.id}"
    campo.props(
        f'maxlength={LONGITUD_MAXIMA_EXPRESION} autocomplete=off spellcheck=false bottom-slots '
        f'aria-label="{etiqueta}" aria-describedby={ayuda}'
    )
    campo.add_slot("hint", f'<span id="{ayuda}">Ctrl+Mayús+Espacio para abrir Símbolos</span>')
    habilitar_simbolos(campo, "funcion", atajos="Control+Shift+2 Control+Shift+3 Control+Shift+4")
    return campo
