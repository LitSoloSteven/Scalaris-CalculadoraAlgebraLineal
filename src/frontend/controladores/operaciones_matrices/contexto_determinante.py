"""Contexto de Glosa basado exclusivamente en la captura y el resultado vigente."""
from src.ai.contexto import ContextoIA, EstadoContexto, describir_matriz, sanear_cadena_usuario
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.ai.huellas import calcular_huella
from src.frontend.sugerencias import Senales
from .captura_factorizacion_lu import localizar_invalida


def _resultado_vigente(vista) -> dict | None:
    resultado = vista.ultimo_resultado
    if not resultado or resultado.get("estado") != "EXITO":
        return None
    if getattr(vista, "_huella_resultado", None) != calcular_huella(vista._capturar()):
        return None
    return resultado


def obtener_contexto_determinante(vista) -> ContextoIA:
    """Devuelve entrada saneada y metodo; omite cualquier resultado invalidado."""
    datos = vista.panel_matriz.obtener_datos_matriz()
    descripcion = describir_matriz([[sanear_cadena_usuario(valor or "", 32) for valor in fila] for fila in datos])
    contexto = ContextoIA(
        herramienta="determinantes", vista="Determinantes", etiqueta="Matriz A",
        entrada={"A": descripcion, "metodo": vista.metodos_determinante.value},
        estado=EstadoContexto(vacio=vista.panel_matriz.esta_vacio()),
    )
    resultado = _resultado_vigente(vista)
    if resultado and resultado.get("estado") == "EXITO":
        contexto.resultado = {"determinante": formatear_fraccion_texto(resultado["determinante"]),
                              "metodo": resultado["metodo"], "es_singular": resultado["es_singular"],
                              "pasos_totales": len(resultado["traza"])}
    return contexto


def obtener_senales_determinante(vista) -> Senales:
    """Describe éxito o singularidad vigente, método y primera celda inválida de A."""
    resultado = _resultado_vigente(vista)
    banderas = {vista.metodos_determinante.value}
    estado = "sin_resultado"
    if resultado:
        estado = "singular" if resultado["es_singular"] else "exito"
        if resultado["es_singular"]:
            banderas.add("rango_deficiente")
        if resultado.get("intercambios", 0):
            banderas.add("intercambio")
    return Senales(herramienta="determinantes", estado=estado, banderas=frozenset(banderas),
                   invalida=localizar_invalida(vista.panel_matriz.obtener_datos_matriz()))
