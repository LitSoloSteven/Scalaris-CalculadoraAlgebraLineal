"""Asocia errores del dominio con campos de captura sin calcular raíces."""
from src.backend.resolutores.raices.validacion_raices import validar_expresion, validar_extremo
from src.backend.resolutores.raices.unidades_angulares import validar_unidad_angular
from src.frontend.controladores.captura_real import real_capturado
from src.frontend.controladores.formato_funcion_real import formatear_expresion
from .captura import preparar_entrada
from .continuidad_intervalo import CLAVES_CONTINUIDAD
from .configuracion_ampliada import criterio_capturado


def errores_captura(captura: dict) -> dict[str, str]:
    """Devuelve mensajes por campo delegando todas las restricciones matemáticas al dominio."""
    errores = {}
    validadores = {
        "expresion": lambda: formatear_expresion(validar_expresion(captura.get("expresion"))),
        "extremo_izquierdo": lambda: _validar_extremo(captura, "extremo_izquierdo", "El extremo a"),
        "extremo_derecho": lambda: _validar_extremo(captura, "extremo_derecho", "El extremo b"),
        "unidad_angular": lambda: validar_unidad_angular(captura.get("unidad_angular")),
        "tolerancia": lambda: _validar_tolerancia_activa(captura),
        "limite_iteraciones": lambda: _validar_parametro(captura, "limite_iteraciones"),
        "criterio": lambda: _validar_criterio_activo(captura),
    }
    for campo, validar in validadores.items():
        try:
            validar()
        except ValueError as error:
            errores[campo] = str(error)
    if not any(clave in errores for clave in CLAVES_CONTINUIDAD):
        try:
            preparar_entrada({clave: captura[clave] for clave in CLAVES_CONTINUIDAD})
        except ValueError as error:
            errores["extremo_derecho"] = str(error)
    return errores


def _validar_extremo(captura: dict, clave: str, etiqueta: str) -> None:
    validar_extremo(real_capturado(captura.get(clave), etiqueta), etiqueta)


def _validar_parametro(captura: dict, clave: str) -> None:
    # El intervalo neutro permite validar un parámetro sin exigir los demás borradores.
    preparar_entrada({"expresion": "x", "extremo_izquierdo": 0, "extremo_derecho": 1,
                      clave: captura.get(clave)})


def _validar_tolerancia_activa(captura: dict) -> None:
    if "criterio" not in captura:
        _validar_parametro(captura, "tolerancia")


def _validar_criterio_activo(captura: dict) -> None:
    if "criterio" in captura:
        criterio_capturado(captura)
