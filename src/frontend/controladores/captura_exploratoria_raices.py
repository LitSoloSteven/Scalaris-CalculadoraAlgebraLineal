"""Captura y pertenencia de intervalos exploratorios independientes del método."""
from src.backend.resolutores.raices.unidades_angulares import opciones_unidad
from src.frontend.controladores.exploracion_raices import presentar_candidato


def capturar_exploracion(panel) -> dict:
    """Lee función, unidad y malla sin consultar extremos ni criterios de parada."""
    return {"expresion": panel.vista.expresion.value, "x_min": panel.minimo.value,
            "x_max": panel.maximo.value, "paso": panel._capturar_paso(),
            **opciones_unidad(panel.vista.unidad_angular.value)}


def intervalo_seleccionable(panel, respuesta: dict, candidato: dict) -> tuple | None:
    """Devuelve extremos solo si el candidato apto pertenece al panel vigente y montado."""
    if panel._cerrado or panel.contenedor_resultados.is_deleted or panel.vista.ocupado:
        return None
    if panel.respuesta is not respuesta or not any(candidato is actual for actual in respuesta["candidatos"]):
        return None
    if not presentar_candidato(candidato)["seleccionable"]:
        return None
    return candidato["intervalo"]
