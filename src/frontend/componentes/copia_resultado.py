"""Copia explícita de valores calculados con confirmación del portapapeles."""
import json
from nicegui import ui
from src.frontend.componentes.sonido import notificar

from src.frontend import textos


def texto_resultado_copiable(resultado: dict) -> str:
    """Devuelve magnitudes ya calculadas en texto tabular, sin interpretar fórmulas."""
    return "\n\n".join(f"{etiqueta}:\n{_texto_valor(resultado[clave])}"
                       for clave, etiqueta in textos.RESULTADO_CAMPOS_COPIABLES
                       if resultado.get(clave) is not None)


def _texto_valor(valor) -> str:
    datos = getattr(valor, "datos", valor)
    if isinstance(datos, dict):
        return _texto_valor(datos.get("datos", datos.get("vector", datos))) if "datos" in datos or "vector" in datos else str(datos)
    if isinstance(datos, list):
        return "\n".join("\t".join(str(celda) for celda in fila) if isinstance(fila, list)
                         else _texto_valor(fila) for fila in datos)
    return str(datos)


def renderizar_copia_resultado(resultado: dict) -> None:
    """Monta un botón que copia solo esta respuesta y avisa si falta permiso del navegador."""
    contenido = texto_resultado_copiable(resultado)
    if not contenido or resultado.get("estado") == "ERROR":
        return

    async def copiar() -> None:
        """Confirma la escritura antes de anunciar éxito y tolera el cliente desmontado."""
        try:
            copiado = await ui.run_javascript(
                f"(async () => {{ try {{ await navigator.clipboard.writeText({json.dumps(contenido)}); return true; }} catch {{ return false; }} }})()")
        except Exception:
            copiado = False
        if not boton.is_deleted:
            notificar(textos.RESULTADO_COPIADO if copiado else textos.RESULTADO_COPIAR_ERROR,
                      type="positive" if copiado else "warning")

    boton = ui.button(textos.RESULTADO_COPIAR, icon="content_copy", color=None, on_click=copiar).classes(
        "boton-discreto").props(f'ripple=false aria-label="{textos.RESULTADO_COPIAR}"')
