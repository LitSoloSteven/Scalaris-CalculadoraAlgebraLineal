"""Campos restaurables y reflejo de la normalización del dominio."""
from dataclasses import asdict

from src.ai.huellas import calcular_huella
from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.frontend.controladores.regla_falsa.captura import preparar_entrada
from src.frontend.vistas.biseccion.estado_captura import transaccion
from .selector_criterio import capturar_criterio, actualizar_guia

CAMPOS = {
    "expresion": "expresion", "extremo_izquierdo": "inferior", "extremo_derecho": "superior",
    "tolerancia": "tolerancia", "limite_iteraciones": "limite", "unidad_angular": "unidad_angular",
}
PREFERENCIAS_INICIALES = {
    "tolerancia": str(EntradaReglaFalsa.tolerancia),
    "limite_iteraciones": str(EntradaReglaFalsa.limite_iteraciones),
    "unidad_angular": EntradaReglaFalsa.unidad_angular,
}
CAMPOS_EJERCICIO = ("expresion", "extremo_izquierdo", "extremo_derecho")


def capturar(vista) -> dict:
    """Devuelve los valores crudos de los controles sin incluir preferencias visuales."""
    captura = {clave: getattr(vista, atributo).value for clave, atributo in CAMPOS.items()}
    if vista.criterio.value != "residuo":
        captura["criterio"] = capturar_criterio(vista)
    if getattr(vista, "_cero_preferido", None) is not None:
        captura["cero_preferido"] = vista._cero_preferido
    return captura


def restaurar_captura(vista, captura: dict) -> None:
    """Carga solo campos presentes como una unidad, sin ejecutar ni convertir números."""
    with transaccion(vista):
        for clave, atributo in CAMPOS.items():
            if clave in captura:
                getattr(vista, atributo).set_value(captura[clave])
        criterio = captura.get("criterio")
        if criterio is not None:
            vista.criterio.set_value(criterio["tipo"])
            vista.parametros_criterio[criterio["tipo"]].set_value(criterio["parametro"])
        elif "tolerancia" in captura:
            vista.criterio.set_value("residuo")
        if any(clave in captura for clave in (*CAMPOS_EJERCICIO, "unidad_angular", "cero_preferido")):
            vista._cero_preferido = captura.get("cero_preferido")
        actualizar_guia(vista)


def reflejar_intervalo(vista, respuesta: dict, huella: str) -> str:
    """Refleja extremos canónicos vigentes y devuelve la huella visible, incluso ante error sintáctico."""
    entrada = respuesta.get("entrada")
    if entrada is None:
        try:
            entrada = asdict(preparar_entrada(capturar(vista)))
        except ValueError:
            return huella
    if entrada["intervalo_invertido"]:
        extremos = {clave: str(entrada[clave]) for clave in CAMPOS_EJERCICIO[1:]}
        restaurar_captura(vista, {**extremos, "cero_preferido": getattr(vista, "_cero_preferido", None)})
        return calcular_huella(capturar(vista))
    return huella


def vaciar_captura(vista) -> None:
    """Vacía función y extremos conservando tolerancia, límite y unidad seleccionados."""
    restaurar_captura(vista, dict.fromkeys(CAMPOS_EJERCICIO, ""))
