"""Contexto y señales de Leontief y Transformaciones con huella vigente."""
from src.ai.contexto import ContextoIA, EstadoContexto, describir_matriz, sanear_cadena_usuario
from src.ai.huellas import calcular_huella
from src.frontend.sugerencias import Senales, primera_celda_invalida
from .capturas_modelos import capturar_leontief, capturar_transformaciones

_CAPTURADORES = {"leontief": capturar_leontief, "transformaciones": capturar_transformaciones}
_CLAVES_MATRIZ = {"leontief": "matriz_coeficientes", "transformaciones": "matriz_transformacion"}
_CLAVES_NOMBRES = {"leontief": "nombres_sectores", "transformaciones": "nombres_variables"}


def capturar_modelo(vista) -> dict:
    """Devuelve la captura serializable del modelo sin consultar el resultado."""
    return _CAPTURADORES[vista.herramienta_modelo](vista)


def resultado_modelo_vigente(vista) -> dict | None:
    """Omite errores y resultados de capturas anteriores, incluidos nombres y demanda."""
    resultado = vista.ultimo_resultado
    if not resultado or resultado.get("estado") == "ERROR":
        return None
    return resultado if getattr(vista, "_huella_resultado", None) == calcular_huella(capturar_modelo(vista)) else None


def obtener_contexto_modelo(vista) -> ContextoIA:
    """Describe entrada saneada y conclusiones calculadas del modelo vigente."""
    herramienta = vista.herramienta_modelo
    entrada = _describir_entrada_modelo(vista)
    vacio = not any(str(campo.value or "").strip() for campo in vista._campos_captura())
    contexto = ContextoIA(herramienta=herramienta, vista=herramienta.capitalize(),
                          etiqueta="C" if herramienta == "leontief" else "A", entrada=entrada,
                          estado=EstadoContexto(vacio=vacio))
    resultado = resultado_modelo_vigente(vista)
    if resultado:
        claves = ("estado", "rango", "nulidad", "conclusiones", "vector_produccion", "vector_demanda",
                  "determinante_leontief", "hawkins_simon", "analisis_sistema")
        contexto.resultado = {clave: resultado[clave] for clave in claves if clave in resultado}
    contexto.desactualizado = bool(vista.ultimo_resultado and not resultado)
    return contexto


def _describir_entrada_modelo(vista) -> dict:
    herramienta = vista.herramienta_modelo
    captura = capturar_modelo(vista)
    matriz = captura[_CLAVES_MATRIZ[herramienta]]
    entrada = {"matriz": describir_matriz([[sanear_cadena_usuario(str(valor), 32) for valor in fila] for fila in matriz]),
               "nombres": [sanear_cadena_usuario(nombre, 160) for nombre in captura[_CLAVES_NOMBRES[herramienta]]]}
    if herramienta == "leontief":
        entrada["demanda"] = [sanear_cadena_usuario(str(valor), 32) for valor in captura["vector_demanda"]]
    return entrada


def obtener_senales_modelo(vista) -> Senales:
    """Emite estado, banderas e invalidez numérica sin interpretar texto libre como números."""
    herramienta = vista.herramienta_modelo
    resultado = resultado_modelo_vigente(vista)
    datos = capturar_modelo(vista)[_CLAVES_MATRIZ[herramienta]]
    etiqueta = "C" if herramienta == "leontief" else "A"
    elementos = [(f"{etiqueta}[{fila + 1},{columna + 1}]", valor, (fila, columna))
                 for fila, valores in enumerate(datos) for columna, valor in enumerate(valores)]
    if herramienta == "leontief":
        elementos.extend((f"d[{indice + 1}]", entrada.value, None) for indice, entrada in enumerate(vista.entradas_demanda))
    banderas = _banderas_modelo(herramienta, datos, resultado)
    estado = "sin_resultado" if not resultado else ("exito" if resultado["estado"] == "EXITO" else "singular")
    return Senales(herramienta, estado, frozenset(banderas), primera_celda_invalida(elementos))


def _banderas_modelo(herramienta: str, datos: list, resultado: dict | None) -> set[str]:
    banderas = {"rectangular"} if datos and len(datos) != len(datos[0]) else set()
    if not resultado:
        return banderas
    if herramienta == "leontief":
        if resultado.get("hawkins_simon", {}).get("es_economicamente_viable") is False:
            banderas.add("no_viable")
    elif resultado.get("nulidad", 0) > 0:
        banderas.add("nucleo_no_trivial")
    return banderas
