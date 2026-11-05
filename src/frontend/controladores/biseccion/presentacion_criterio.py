"""Textos y magnitudes del resultado según el estado publicado por el motor."""
from .catalogo_criterios import CRITERIOS, condicion_criterio
from .presentacion import motivo, numero
from .presentacion_diagnostico import detalles_diagnostico, texto_sugerencia


def titulo_estado(respuesta: dict) -> str:
    """Describe primero el estado efectivo, sin reinterpretar el diagnóstico matemático."""
    estado = respuesta["estado"]
    parada = respuesta.get("motivo_parada")
    if estado == "EXITO":
        if parada == "raiz_exacta":
            return "Cero evaluado en un punto medio" if respuesta["iteraciones"] else "Cero evaluado en un extremo, sin iteraciones"
        tipo = respuesta["criterio_solicitado"]["tipo"]
        return "Convergió por " + CRITERIOS[tipo][0].lower()
    if estado == "ITERACIONES_COMPLETADAS":
        return f"{len(respuesta['iteraciones'])} iteraciones completadas"
    if parada == "estancamiento":
        return "Límite de precisión"
    if parada == "limite_iteraciones":
        return "Límite de iteraciones"
    if respuesta.get("codigo_diagnostico") == "SINGULARIDAD_DETECTADA":
        return "Singularidad identificada"
    titulos = {"SIN_CAMBIO_DE_SIGNO": "Sin cambio de signo",
               "CONTINUIDAD_NO_VERIFICADA": "Continuidad no verificada · aproximación provisional"}
    return titulos.get(estado, "Error de entrada o evaluación")


def metricas_resumen(respuesta: dict) -> tuple[tuple[str, str], ...]:
    """Prepara criterio, umbral, métrica e intervalo desde los datos recibidos, sin recalcular paradas."""
    criterio = respuesta.get("criterio_solicitado")
    datos = (("Unidad trigonométrica", respuesta.get("unidad_angular", "radianes")),) if "entrada" in respuesta else ()
    if criterio:
        datos += (("Criterio solicitado", CRITERIOS[criterio["tipo"]][0]),
                 ("Condición solicitada", condicion_criterio(criterio["tipo"], criterio["parametro"])),
                 ("Umbral", numero(respuesta["umbral"], True) + " " + respuesta["unidad_criterio"]),
                 ("Métrica final (" + respuesta["unidad_criterio"] + ")", numero(respuesta.get("metrica_final"), True)))
    if respuesta.get("intervalo_final") is None:
        return datos
    inferior, superior = respuesta["intervalo_final"]
    return datos + (("Intervalo final [a, b]", f"[{numero(inferior, True)}, {numero(superior, True)}]"),
                    ("Cota geométrica (b − a) / 2, si hay continuidad y encierro", numero(respuesta.get("cota"), True)),
                    ("Residuo |f(c)|", numero(respuesta["metricas"].get("residuo_final"), True)),
                    ("Iteraciones", str(len(respuesta["iteraciones"]))))


def aproximacion_presentada(respuesta: dict, decimales: int) -> str:
    """Formatea la aproximación ya calculada sin alterar las métricas ni el criterio."""
    valor = respuesta.get("aproximacion")
    return "No disponible" if valor is None else f"x ≈ {valor:.{decimales}f}"


def avisos_resumen(respuesta: dict) -> tuple[str, ...]:
    """Reúne avisos del motor y del adaptador sin repetir textos idénticos."""
    avisos = tuple(respuesta.get("advertencias", ()))
    if respuesta.get("aviso"):
        avisos += (respuesta["aviso"],)
    if respuesta.get("aviso_grafica"):
        avisos += (respuesta["aviso_grafica"],)
    return tuple(dict.fromkeys(avisos))


def texto_resumen(respuesta: dict, decimales: int) -> str:
    """Entrega el mismo estado, criterio, magnitudes y avisos mostrados para copiar el resultado."""
    lineas = [titulo_estado(respuesta), aproximacion_presentada(respuesta, decimales), motivo(respuesta)]
    lineas.extend(f"{etiqueta}: {valor}" for etiqueta, valor in metricas_resumen(respuesta))
    lineas.extend(avisos_resumen(respuesta))
    lineas.extend(f"{etiqueta}: {valor}" for etiqueta, valor in detalles_diagnostico(respuesta))
    lineas.extend(texto_sugerencia(sugerencia) for sugerencia in respuesta.get("sugerencias", ()))
    return "\n".join(lineas)
