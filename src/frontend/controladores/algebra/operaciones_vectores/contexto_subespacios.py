"""Contexto pedagógico saneado, vigencia y señales para Espacios y subespacios."""
from __future__ import annotations

from src.ai.contexto.contexto import (
    ContextoIA,
    EstadoContexto,
    compactar_numero,
    describir_matriz,
    generar_nota_ventana,
    sanear_cadena_usuario,
)
from src.ai.huellas import esta_desactualizado
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    MODO_RESTRICCIONES,
    NOMBRES_MODOS,
    TITULO_PAGINA,
)
from src.frontend.presentacion.sugerencias import Senales, primera_celda_invalida

_LIMITE_CELDA = 32
_LIMITE_ECUACION = 120
_LIMITE_RESUMEN = 48
_LIMITE_LINEAS_ECUACIONES = 12
_CLASIFICACIONES_SENAL = {
    "SUBESPACIO": "subespacio",
    "AFIN_NO_SUBESPACIO": "afin_no_subespacio",
    "VACIO_NO_SUBESPACIO": "vacio_no_subespacio",
}


def resultado_subespacio_vigente(vista) -> dict | None:
    """Devuelve el resultado únicamente si coincide con modo y captura vigentes."""
    resultado = getattr(vista, "ultimo_resultado", None)
    if not resultado or resultado.get("modo") != vista.modo:
        return None
    if esta_desactualizado(vista.captura.obtener(), getattr(vista, "_huella_resultado", None)):
        return None
    return resultado


def _compactar_vectores(vectores: tuple | list) -> list[list[str]]:
    return [
        [compactar_numero(sanear_cadena_usuario(str(valor), 128), _LIMITE_RESUMEN) for valor in vector]
        for vector in vectores
    ]


def _entrada_restricciones_saneada(vista, captura: dict) -> tuple[dict, str | None, bool]:
    formato = str(captura.get("formato", "matriz"))
    dimension = captura.get("dimension_ambiente")
    if formato == "ecuaciones":
        lineas = [
            sanear_cadena_usuario(linea, _LIMITE_ECUACION)
            for linea in str(captura.get("ecuaciones", "")).splitlines() if linea.strip()
        ][:_LIMITE_LINEAS_ECUACIONES]
        entrada = {"dimension_ambiente": dimension, "formato": "ecuaciones", "ecuaciones": lineas}
        return entrada, None, vista.captura_restricciones.esta_vacia()
    datos_a = [[sanear_cadena_usuario(str(celda), _LIMITE_CELDA) for celda in fila] for fila in captura["matriz_a"]]
    datos_b = [[sanear_cadena_usuario(str(celda), _LIMITE_CELDA)] for celda in captura["vector_b"]]
    descriptor_a = describir_matriz(datos_a)
    descriptor_b = describir_matriz(datos_b)
    entrada = {"dimension_ambiente": dimension, "formato": "matriz", "A": descriptor_a, "b": descriptor_b}
    return entrada, generar_nota_ventana(descriptor_a, descriptor_b), vista.captura_restricciones.esta_vacia()


def _entrada_generadores_saneada(captura: dict) -> tuple[dict, str | None, bool]:
    vectores = captura.get("vectores", {})
    descriptores: list[dict] = []
    datos_vectores: dict[str, dict] = {}
    tiene_contenido = False
    for etiqueta, vector in vectores.items():
        nombre = sanear_cadena_usuario(str(etiqueta), _LIMITE_CELDA) or "v"
        valores = vector.get("datos", ())
        if any(str(celda).strip() for celda in valores):
            tiene_contenido = True
        celdas = [[sanear_cadena_usuario(str(celda), _LIMITE_CELDA)] for celda in valores]
        descriptor = describir_matriz(celdas)
        descriptor["orientacion"] = "columna"
        datos_vectores[nombre] = descriptor
        descriptores.append(descriptor)
    entrada = {"dimension_ambiente": captura.get("dimension_ambiente"), "vectores": datos_vectores}
    return entrada, generar_nota_ventana(*descriptores), not tiene_contenido


def _serializar_criterios_contexto(criterios: tuple | list) -> list[dict]:
    return [
        {
            "clave": criterio.get("clave", ""),
            "titulo": criterio.get("titulo", ""),
            "estado": criterio.get("estado", ""),
            "origen": criterio.get("origen", "teorema"),
            "resumen": sanear_cadena_usuario(str(criterio.get("resumen", "")), 200),
        }
        for criterio in criterios
    ]


def _serializar_verificaciones_contexto(comprobaciones: tuple | list) -> list[dict]:
    return [
        {
            "coincide": bool(elemento.get("coincide", False)),
            "detalle": sanear_cadena_usuario(str(elemento.get("detalle", "")), 160),
        }
        for elemento in comprobaciones
    ]


def _resumir_detalle_conjunto(resumen: dict, resultado: dict) -> None:
    for clave in ("base", "direcciones"):
        if resultado.get(clave) is not None:
            resumen[clave] = _compactar_vectores(resultado[clave])
    if resultado.get("particular") is not None:
        resumen["particular"] = [
            compactar_numero(sanear_cadena_usuario(str(valor), 128), _LIMITE_RESUMEN)
            for valor in resultado["particular"]
        ]
    _resumir_textos_conjunto(resumen, resultado)


def _resumir_textos_conjunto(resumen: dict, resultado: dict) -> None:
    if resultado.get("dependencias"):
        resumen["dependencias"] = [
            sanear_cadena_usuario(str(dependencia.get("texto", "")), 120)
            for dependencia in resultado["dependencias"]
        ]
    familia = resultado.get("familia_parametrica")
    if isinstance(familia, dict) and familia.get("texto"):
        resumen["familia_parametrica"] = sanear_cadena_usuario(familia["texto"], 180)
    testigo = resultado.get("testigo")
    if isinstance(testigo, dict) and testigo.get("descripcion"):
        resumen["testigo"] = sanear_cadena_usuario(testigo["descripcion"], 160)


def _resumir_resultado_subespacio(resultado: dict) -> dict:
    if resultado.get("estado") != "EXITO":
        return {
            "estado": "ERROR",
            "codigo": str(resultado.get("codigo", "ENTRADA_INVALIDA")),
            "modo": resultado.get("modo"),
            "mensaje": sanear_cadena_usuario(str(resultado.get("mensaje", "")), 180),
        }
    resumen = {
        "estado": "EXITO",
        "modo": resultado.get("modo"),
        "codigo": resultado.get("codigo"),
        "clasificacion": resultado.get("clasificacion"),
        "veredicto": resultado.get("veredicto"),
        "mensaje": sanear_cadena_usuario(str(resultado.get("veredicto") or resultado.get("mensaje", "")), 200),
        "es_subespacio": resultado.get("es_subespacio"),
        "es_espacio_vectorial": resultado.get("es_espacio_vectorial"),
        "rango": resultado.get("rango"),
        "rango_aumentada": resultado.get("rango_aumentada"),
        "dimension": resultado.get("dimension"),
        "dimension_afin": resultado.get("dimension_afin"),
        "variables_pivote": list(resultado.get("variables_pivote", ())),
        "variables_libres": list(resultado.get("variables_libres", ())),
        "criterios_teorema": _serializar_criterios_contexto(resultado.get("criterios", ())),
        "verificaciones_motor": _serializar_verificaciones_contexto(resultado.get("comprobaciones", ())),
    }
    _resumir_detalle_conjunto(resumen, resultado)
    return resumen


def obtener_contexto_subespacio(vista) -> ContextoIA:
    """Construye el contexto saneado de Espacios y subespacios sin exponer obsoletos."""
    captura = vista.captura.obtener()
    if vista.modo == MODO_RESTRICCIONES:
        entrada, nota_ventana, vacio = _entrada_restricciones_saneada(vista, captura)
    else:
        entrada, nota_ventana, vacio = _entrada_generadores_saneada(captura)
    huella = getattr(vista, "_huella_resultado", None)
    ultimo = getattr(vista, "ultimo_resultado", None)
    desactualizado = esta_desactualizado(captura, huella) or bool(ultimo and ultimo.get("modo") != vista.modo)
    resumen = None if (desactualizado or not ultimo) else _resumir_resultado_subespacio(ultimo)
    return ContextoIA(
        "espacios_subespacios",
        TITULO_PAGINA,
        NOMBRES_MODOS[vista.modo],
        entrada,
        EstadoContexto(resultado=resumen, nota_ventana=nota_ventana, desactualizado=desactualizado, vacio=vacio),
    )


def _celdas_restricciones(captura: dict) -> list[tuple]:
    if captura.get("formato") != "matriz":
        return []
    elementos: list[tuple] = []
    matriz_a = captura["matriz_a"]
    columnas = len(matriz_a[0]) if matriz_a else 0
    for indice_fila, fila in enumerate(matriz_a):
        for indice_columna, valor in enumerate(fila):
            elementos.append((f"A[{indice_fila + 1},{indice_columna + 1}]", valor, (indice_fila, indice_columna)))
    for indice_fila, valor in enumerate(captura["vector_b"]):
        elementos.append((f"b[{indice_fila + 1}]", valor, (indice_fila, columnas)))
    return elementos


def _celdas_generadores(captura: dict) -> list[tuple]:
    elementos: list[tuple] = []
    for etiqueta, vector in captura.get("vectores", {}).items():
        nombre = sanear_cadena_usuario(str(etiqueta), 20) or "v"
        for indice, valor in enumerate(vector.get("datos", ())):
            elementos.append((f"{nombre}[{indice + 1}]", valor, None))
    return elementos


def obtener_senales_subespacio(vista) -> Senales:
    """Devuelve estado vigente, celda inválida y banderas de Espacios y subespacios."""
    captura = vista.captura.obtener()
    vigente = resultado_subespacio_vigente(vista)
    banderas = {vista.modo}
    estado = "sin_resultado"
    if vigente is not None:
        if vigente.get("estado") != "EXITO":
            estado = "error"
        else:
            estado = _CLASIFICACIONES_SENAL.get(str(vigente.get("clasificacion", "")), "sin_resultado")
            if vigente.get("es_subespacio_cero"):
                banderas.add("subespacio_cero")
    celdas = _celdas_restricciones(captura) if vista.modo == MODO_RESTRICCIONES else _celdas_generadores(captura)
    return Senales(
        herramienta="espacios_subespacios",
        estado=estado,
        banderas=frozenset(banderas),
        invalida=primera_celda_invalida(celdas),
    )
