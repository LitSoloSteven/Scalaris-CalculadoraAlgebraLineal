"""Contexto de Glosa basado exclusivamente en la captura y el resultado vigente."""
from src.ai.contexto import ContextoIA, EstadoContexto, describir_matriz, sanear_cadena_usuario
from src.backend.utilidades.formateadores import formatear_fraccion_texto


def obtener_contexto_determinante(vista) -> ContextoIA:
    """Devuelve entrada saneada y metodo; omite cualquier resultado invalidado."""
    datos = vista.panel_matriz.obtener_datos_matriz()
    descripcion = describir_matriz([[sanear_cadena_usuario(valor or "", 32) for valor in fila] for fila in datos])
    contexto = ContextoIA(
        herramienta="determinantes", vista="Determinantes", etiqueta="Matriz A",
        entrada={"A": descripcion, "metodo": vista.metodos_determinante.value},
        estado=EstadoContexto(vacio=vista.panel_matriz.esta_vacio()),
    )
    resultado = vista.ultimo_resultado
    if resultado and resultado.get("estado") == "EXITO":
        contexto.resultado = {"determinante": formatear_fraccion_texto(resultado["determinante"]),
                              "metodo": resultado["metodo"], "es_singular": resultado["es_singular"],
                              "pasos_totales": len(resultado["traza"])}
    return contexto
