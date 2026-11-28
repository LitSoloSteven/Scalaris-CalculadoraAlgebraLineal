"""Contexto y señales de Glosa para Newton-Raphson y el método de la secante."""
from src.ai.contexto.contexto import (
    CapturaPaso,
    ContextoIA,
    EstadoContexto,
    ReferenciaPaso,
    sanear_cadena_usuario,
)
from src.frontend.componentes.glosa.interaccion.glosa_foco import crear_accion_explicacion
from src.frontend.presentacion.sugerencias import Senales

_METODOS_ETIQUETAS = {"newton": "Newton-Raphson", "secante": "Secante"}
_CAMPOS_RESUMEN = (
    "estado", "metodo", "raiz", "residuo", "iteraciones_totales",
    "codigo_diagnostico", "mensaje", "derivada_expresion", "advertencias",
)


def construir_contexto(vista) -> ContextoIA:
    """Entrega la captura, el resumen del cálculo y el paso activo a Glosa."""
    captura = vista._captura_actual()
    expresion = str(captura.get("expresion") or "").strip()
    captura_saneada = {
        **captura,
        "expresion": sanear_cadena_usuario(expresion, 256) if expresion else "",
    }
    resumen = _resumir_resultado(vista.ultimo_resultado)
    reproductor = vista.reproductor
    foco = _foco_actual(reproductor)
    metodo = captura.get("metodo", "newton")
    etiqueta = _METODOS_ETIQUETAS.get(metodo, "Métodos abiertos")
    return ContextoIA(
        "metodos_abiertos",
        f"Métodos abiertos · {etiqueta}",
        "Búsqueda de raíces",
        captura_saneada,
        EstadoContexto(
            resultado=resumen,
            foco=foco,
            vacio=getattr(vista, "_cerrada", False) or not bool(expresion),
            nota_ventana="La convergencia local depende de los puntos iniciales y de f'(x) != 0.",
        ),
    )


def construir_senales(vista) -> Senales:
    """Emite el estado y las banderas vigentes para seleccionar sugerencias."""
    metodo = vista.metodo.value if getattr(vista, "metodo", None) else "newton"
    banderas = {metodo}
    resultado = vista.ultimo_resultado
    if not resultado:
        return Senales(herramienta="metodos_abiertos", estado="sin_resultado", banderas=frozenset(banderas))
    estado_motor = resultado.get("estado")
    if estado_motor == "EXITO":
        estado = "exito"
    else:
        estado = "error"
        if estado_motor in ("DERIVADA_NULA", "DENOMINADOR_NULO", "DIVERGENCIA", "LIMITE_ITERACIONES"):
            banderas.add(estado_motor.lower())
    return Senales(herramienta="metodos_abiertos", estado=estado, banderas=frozenset(banderas))


def opciones_glosa(salida, datos: dict, pasos: tuple) -> dict:
    """Enlaza la explicación de paso solo mientras el resultado y paso sigan vigentes."""
    vista = getattr(salida, "vista", None)
    panel = getattr(vista, "panel_ia", None)
    if panel is None:
        return {}

    def _sigue_vigente(paso) -> bool:
        reproductor = salida.reproductor
        return (
            not getattr(vista, "_cerrada", False)
            and salida.resultado is datos
            and reproductor is not None
            and reproductor.pasos[reproductor.indice_actual] is paso
        )

    return {
        "al_explicar": crear_accion_explicacion(panel, pasos, sigue_vigente=_sigue_vigente),
        "esta_ocupado": lambda: bool(getattr(panel, "_esta_enviando", False)),
    }


def _resumir_resultado(resultado: dict | None) -> dict | None:
    if not resultado:
        return None
    resumen = {clave: resultado.get(clave) for clave in _CAMPOS_RESUMEN}
    iteraciones = resultado.get("iteraciones") or ()
    if iteraciones:
        resumen["ultima_iteracion"] = iteraciones[-1]
    return resumen


def _foco_actual(reproductor) -> ReferenciaPaso | None:
    if reproductor is None or not reproductor.pasos:
        return None
    paso = reproductor.pasos[reproductor.indice_actual]
    detalle = paso.cuerpo if isinstance(paso.cuerpo, dict) else None
    return ReferenciaPaso(
        indice=reproductor.indice_actual + 1,
        total=len(reproductor.pasos),
        tipo=paso.tipo,
        operacion=paso.descripcion,
        captura=CapturaPaso(detalle=detalle),
    )
