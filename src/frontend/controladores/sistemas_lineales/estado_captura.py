"""Estado y sincronizacion de la captura de sistemas lineales."""
from src.backend.utilidades.estado_captura import (
    ajustar_numero_ecuaciones, captura_vacia, opciones_transferencia_sistema,
)
from src.frontend.controladores.sesion_matricial import actualizar_contexto


def valores_ecuaciones(vista) -> list[str]:
    """Extrae el texto actual de cada ecuacion editable."""
    return [entrada.value or '' for entrada in vista.entradas_ecuaciones]


def modo_homogeneo_activo(vista) -> bool:
    """Indica si la captura matricial fija los terminos independientes a cero."""
    return vista.pestanas_modo.value == "Matriz" and getattr(vista.cuadricula, "modo_homogeneo", False)


def matriz_vacia(vista) -> bool:
    """Delega la presencia de datos matriciales a la regla comun de captura."""
    coeficientes, independientes = vista.cuadricula.obtener_datos_matriz()
    return captura_vacia([valor for fila in coeficientes for valor in fila] + independientes)


def ecuaciones_vacias(vista, considerar_cero: bool = True) -> bool:
    """Delega la presencia de texto en las ecuaciones capturadas."""
    return captura_vacia(valores_ecuaciones(vista), considerar_cero)


def cambiar_numero_ecuaciones(vista, incremento: int) -> None:
    """Reconstruye la captura al cambiar el numero dentro del limite del dominio."""
    numero = ajustar_numero_ecuaciones(vista.num_ecuaciones, incremento)
    if numero != vista.num_ecuaciones:
        vista.num_ecuaciones = numero
        vista.renderizar_ecuaciones()
        vista.actualizar_botones_sincronizacion()


def cambiar_modo(vista, modo: str) -> None:
    """Sincroniza la captura anterior antes de presentar el modo elegido."""
    if modo == 'Ecuaciones' and not matriz_vacia(vista):
        vista.sincronizar_desde_matriz()
    elif modo == 'Matriz' and not ecuaciones_vacias(vista):
        vista.sincronizar_desde_ecuaciones()
    vista._programar_vista_previa()
    actualizar_contexto(vista)


def opciones_transferencia(coeficientes: list) -> dict:
    """Delega la disponibilidad de destinos al dominio."""
    return opciones_transferencia_sistema(coeficientes)
