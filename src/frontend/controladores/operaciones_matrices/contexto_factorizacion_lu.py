"""Contexto y señales vigentes de la factorización LU para Glosa."""
from src.ai.contexto import ContextoIA, EstadoContexto, describir_matriz, generar_nota_ventana, sanear_cadena_usuario
from src.ai.huellas import calcular_huella
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend.sugerencias import Senales, primera_celda_invalida


def localizar_invalida(datos: list[list[str]]):
    """Devuelve la primera celda inválida de los datos, o None si no existe."""
    elementos = [(f"A[{fila + 1},{columna + 1}]", valor, (fila, columna))
                 for fila, valores in enumerate(datos) for columna, valor in enumerate(valores)]
    return primera_celda_invalida(elementos)


def _resultado_vigente(vista, datos: list[list[str]]) -> dict | None:
    resultado = vista.ultimo_resultado
    if not resultado or resultado.get("estado") != "EXITO":
        return None
    if getattr(vista, "_huella_resultado", None) != calcular_huella({"matriz_a": datos}):
        return None
    return resultado


def _describir_factor(matriz) -> dict:
    return describir_matriz([[formatear_fraccion_texto(valor) for valor in fila] for fila in matriz.datos])


def obtener_contexto_ia(vista) -> ContextoIA:
    """Describe la captura de vista y el resultado vigente para Glosa."""
    panel = vista.panel_matriz
    datos = panel.obtener_datos_matriz()
    descripcion = describir_matriz([[sanear_cadena_usuario(str(valor), 32) for valor in fila] for fila in datos])
    contexto = ContextoIA(herramienta="factorizacion_lu", vista="Factorización LU",
                          etiqueta=f"A ({panel.filas}×{panel.columnas})", entrada={"A": descripcion},
                          estado=EstadoContexto(vacio=panel.esta_vacio()))
    resultado = _resultado_vigente(vista, datos)
    descriptores = [descripcion]
    if resultado:
        factores = {nombre: _describir_factor(resultado[clave]) for nombre, clave in
                    (("P", "permutacion"), ("L", "inferior"), ("U", "superior"))}
        contexto.resultado = {"rango": resultado["rango"], **factores,
                              "coincide": resultado["comprobacion"]["coincide"],
                              "pasos_totales": len(resultado["traza"])}
        descriptores.extend(factores.values())
    contexto.desactualizado = bool(vista.ultimo_resultado and not resultado and vista.ultimo_resultado.get("estado") == "EXITO")
    contexto.nota_ventana = generar_nota_ventana(*descriptores)
    return contexto


def obtener_senales_ia(vista) -> Senales:
    """Devuelve estado, celda inválida y banderas de la captura y resultado vigentes."""
    panel = vista.panel_matriz
    datos = panel.obtener_datos_matriz()
    resultado = _resultado_vigente(vista, datos)
    banderas = set()
    if panel.filas != panel.columnas:
        banderas.add("rectangular")
    if resultado:
        if any(paso["tipo"] == "intercambio" for paso in resultado["traza"]):
            banderas.add("intercambio")
        if resultado["rango"] < min(panel.filas, panel.columnas):
            banderas.add("rango_deficiente")
    return Senales(herramienta="factorizacion_lu", estado="exito" if resultado else "sin_resultado",
                   banderas=frozenset(banderas), invalida=localizar_invalida(datos))
