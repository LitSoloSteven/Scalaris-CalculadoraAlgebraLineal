"""Acceso por teclado al selector de símbolos desde los campos de expresión."""


def habilitar_simbolos(campo, perfil: str, *, atajos: str = "") -> None:
    """Identifica el perfil de símbolos del campo y declara sus atajos de teclado."""
    teclas = ("Control+Shift+Space " + atajos).strip()
    campo.props(f'data-simbolos={perfil} aria-keyshortcuts="{teclas}"')
