"""Contexto de Glosa para el resultado y el paso que se están consultando."""
from src.ai.contexto.contexto import ContextoIA, EstadoContexto
from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.controladores.biseccion.contexto_biseccion import resumir_contexto_biseccion
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION, METODOS
from src.frontend.controladores.regla_falsa.contexto_regla_falsa import resumir_contexto_regla_falsa
from src.frontend.controladores.regla_falsa.pasos import referencia_paso


def construir_contexto(vista) -> ContextoIA:
    """Devuelve el ejercicio activo, con el resumen y el foco del detalle visible."""
    captura = vista.capturar()
    metodo = captura["metodo"]
    respuesta = vista.ultimo_resultado
    candidato = vista.candidato_activo
    if candidato is not None and respuesta and respuesta.get("entrada"):
        captura = {**respuesta["entrada"], "metodo": metodo, "identificador_candidato": candidato}
        ampliado = vista.ultimo_ampliado or {}
        if ampliado.get("criterio") is not None:
            captura["criterio"] = ampliado["criterio"]
    resumen = (resumir_contexto_biseccion(respuesta) if metodo == BISECCION else
               resumir_contexto_regla_falsa(respuesta, vista.ultimo_ampliado))
    reproductor = vista.salida.reproductor
    foco = (referencia_paso(reproductor.pasos[reproductor.indice_actual], len(reproductor.pasos))
            if reproductor is not None and reproductor.pasos else None)
    return ContextoIA(
        metodo, METODOS[metodo], "Búsqueda de raíces", captura,
        EstadoContexto(resultado=resumen, foco=foco, vacio=vista._cerrada or not bool(captura["expresion"]),
                       nota_ventana="La garantía requiere continuidad. El residuo no es una cota del error en x."),
    )


def opciones_glosa(salida, datos: dict, pasos: tuple) -> dict:
    """Enlaza la acción únicamente con el resultado y el paso que siguen visibles."""
    panel = salida.vista.panel_ia
    def _sigue_vigente(paso) -> bool:
        reproductor = salida.reproductor
        return (not salida.vista._cerrada and salida.datos is datos and reproductor is not None
                and reproductor.pasos[reproductor.indice_actual] is paso)

    return {"al_explicar": crear_accion_explicacion(panel, pasos, sigue_vigente=_sigue_vigente),
            "esta_ocupado": lambda: bool(getattr(panel, "_esta_enviando", False))}
