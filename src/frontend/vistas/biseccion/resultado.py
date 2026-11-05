"""Presentación del veredicto y de la traza del cálculo individual."""
from .grafico_compartido import mostrar_paso_principal
from .modo_examen import crear_interruptor_examen
from .procedimiento import mostrar_traza
from .resumen_criterio import mostrar_resumen


def mostrar_resultado(vista, respuesta: dict) -> None:
    """Presenta el cálculo vigente y conserva el contexto de Glosa en sus pasos."""
    with vista.contenedor_resultados:
        hay_filas = bool(respuesta.get("iteraciones"))
        examen = crear_interruptor_examen(vista) if hay_filas else None
        mostrar_resumen(vista, respuesta, examen)
        mostrar_paso_principal(vista, respuesta)
        if examen is not None:
            examen.move(vista.contenedor_resultados)
            vista.reproductor_pasos = mostrar_traza(
                respuesta, examen, lambda paso: mostrar_paso_principal(vista, respuesta, paso),
                "biseccion", vista.panel_ia)
