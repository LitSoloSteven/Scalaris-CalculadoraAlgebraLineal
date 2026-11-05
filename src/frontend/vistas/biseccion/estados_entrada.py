"""Orientación de la captura sin evaluar la función ni afirmar continuidad."""
from src.frontend.controladores.biseccion.captura_criterio import preparar_entrada
from src.frontend.controladores.biseccion.metadatos_expresion import sensible_a_unidad


def actualizar_expresion(vista, *, validar: bool = False) -> None:
    """Informa sobre sintaxis y muestra la unidad solo si el AST la usa."""
    expresion = vista.expresion.value or ""
    sensible = False
    if not expresion.strip():
        texto = "Escribe una función de x."
    else:
        try:
            sensible = sensible_a_unidad(expresion)
            texto = "Sintaxis válida."
        except ValueError as error:
            texto = str(error) if validar else "Completa la función para revisar su sintaxis."
    vista.unidad_angular.set_visibility(sensible)
    vista.estado_expresion.set_text(texto)


def actualizar_intervalo(vista, *, validar: bool = False) -> None:
    """Orienta sobre extremos pendientes y valida la captura solo al salir o enviar."""
    captura = vista.capturar()
    completo = all(captura[clave] is not None and str(captura[clave]).strip()
                   for clave in ("extremo_izquierdo", "extremo_derecho"))
    texto = "Continuidad no verificada." if completo else "Completa ambos extremos para definir el intervalo."
    if validar and completo and (vista.expresion.value or "").strip():
        try:
            preparar_entrada(captura)
        except ValueError as error:
            texto = str(error)
    vista.estado_continuidad.set_text(texto)
    vista.estado_continuidad.set_visibility(texto != "Continuidad no verificada." and completo)
