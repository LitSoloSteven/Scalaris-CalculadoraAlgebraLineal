"""Acceso al selector de símbolos desde los campos de expresión."""


def habilitar_simbolos(campo, perfil: str, *, atajos: str = "") -> None:
    """Identifica el campo y monta el botón que conserva su selección."""
    teclas = ("Control+Shift+Space " + atajos).strip()
    campo.props(f'data-simbolos={perfil} aria-keyshortcuts="{teclas}"')
    campo.add_slot("append", (
        f'<button type="button" class="simbolos-boton" data-campo-simbolos="c{campo.id}" '
        'aria-haspopup="dialog" aria-keyshortcuts="Control+Shift+Space" '
        'title="Ctrl+Mayús+Espacio">Símbolos</button>'
    ))
