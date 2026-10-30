"""Adaptación de sesiones para expresiones matriciales y familias vectoriales."""
from src.frontend.componentes.sesion_capturas import SesionCapturas
from src.frontend.vistas.operaciones_vectores.contexto import entrada_actual


def conectar_sesion_capturas(vista, herramienta: str) -> None:
    """Monta vista previa e historial junto al resultado de una herramienta."""
    destino = vista.contenedor_resultados if herramienta == "matrices" else vista.panel_resultados
    with destino.parent_slot.parent:
        vista.sesion_capturas = SesionCapturas(lambda captura: restaurar_captura(vista, herramienta, captura))
    actualizar_previa_captura(vista, herramienta)


def obtener_captura_sesion(vista, herramienta: str) -> dict:
    """Copia la captura completa, incluidas expresión, operación y orientaciones."""
    if herramienta == "vectores":
        return entrada_actual(vista)
    return {"matrices": {nombre: datos["datos"] for nombre, datos in
                         vista.panel_captura_matrices.obtener_datos_crudos().items()},
            "expresion": vista.entrada_expresion.value or ""}


def actualizar_previa_captura(vista, herramienta: str) -> None:
    """Refleja valores de la captura sin evaluar expresiones ni ejecutar operaciones."""
    sesion = getattr(vista, "sesion_capturas", None)
    if sesion is None:
        return
    captura = obtener_captura_sesion(vista, herramienta)
    if herramienta == "matrices":
        partes = [f"{nombre}:\n" + "\n".join("\t".join(fila) for fila in datos)
                  for nombre, datos in captura["matrices"].items()]
        partes.append(captura["expresion"])
    else:
        partes = [f"{nombre} ({datos['orientacion']}): " + ", ".join(datos["datos"])
                  for nombre, datos in captura["vectores"].items()]
        if captura["operacion"] == "escalar":
            partes.append(f"k = {captura['escalar']}")
    sesion.actualizar_previa("\n\n".join(partes))


def registrar_captura_sesion(vista, herramienta: str, respuesta: dict) -> None:
    """Registra solo respuestas sin error que pertenecen a la captura publicada."""
    if respuesta.get("estado") == "ERROR" or not getattr(vista, "sesion_capturas", None):
        return
    vista.sesion_capturas.registrar(obtener_captura_sesion(vista, herramienta), respuesta.get("mensaje", respuesta.get("estado", "")))


def restaurar_captura(vista, herramienta: str, captura: dict) -> None:
    """Restaura la captura sin calcular y conserva orientación y opciones vectoriales."""
    if herramienta == "matrices":
        vista.panel_captura_matrices.cargar_datos(captura["matrices"])
        vista.entrada_expresion.set_value(captura["expresion"])
        vista.restablecer_resultados()
        return
    vista.pestanas.set_value(captura["operacion"])
    vista.valor_escalar = captura["escalar"]
    vista.operacion_suma_resta = captura["suma_resta"]
    vista.orientacion_estricta = captura["estricto"]
    vista.entrada_escalar.set_value(captura["escalar"])
    vista.selector_operacion.set_value(captura["suma_resta"])
    vista.casilla_estricta.set_value(captura["estricto"])
    vista.panel_vectorial.cargar_datos({nombre: datos["datos"] for nombre, datos in captura["vectores"].items()})
    for nombre, datos in captura["vectores"].items():
        vista.panel_vectorial.vectores[nombre]["orientacion"] = datos["orientacion"]
    vista.panel_vectorial.renderizar_todos_vectores()
    vista._al_cambiar_vectores()
