"""Adaptación serializable de la exploración y sus etiquetas de presentación."""
from dataclasses import asdict

from src.backend.resolutores.raices.contrato_exploracion import EntradaExploracion
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
from .captura_criterio import real_capturado
from .presentacion import numero
from .presentacion_diagnostico import texto_intervalo

LONGITUD_CAMPO_EXPLORACION = 64
PASO_EXPLORACION_DEFECTO = "0.1"
ETIQUETAS_CANDIDATOS = {
    "cruce": "Cruce de signo",
    "cero_evaluado": "Cero evaluado aproximado",
    "posible_contacto": "Posible contacto con el eje",
    "segmento_invalido": "Segmento con evaluación inválida",
    "discontinuidad": "Restricción estructural identificada",
}


def resolver_exploracion(captura: dict) -> dict:
    """Convierte texto y delega al dominio; devuelve éxito o error visible sin lanzar ValueError."""
    try:
        if not isinstance(captura, dict):
            raise ValueError("Revisa los campos de exploración.")
        expresion = captura.get("expresion", "")
        entrada = EntradaExploracion(expresion, _campo(captura, "x_min"),
                                     _campo(captura, "x_max"), _campo(captura, "paso"))
        return {"estado": "EXITO", "mensaje": "Exploración disponible.", **asdict(explorar_intervalos(entrada))}
    except ValueError as error:
        return {"estado": "ERROR", "mensaje": str(error), "candidatos": (), "advertencias": (), "evaluaciones": 0}


def presentar_candidato(candidato: dict) -> dict:
    """Entrega etiqueta, intervalo completo y aptitud según la clasificación del dominio."""
    muestra = ""
    if candidato["abscisa"] is not None:
        muestra = f"x = {numero(candidato['abscisa'], True)}; f(x) = {numero(candidato['valor'], True)}"
    return {"etiqueta": ETIQUETAS_CANDIDATOS[candidato["tipo"]],
            "intervalo": texto_intervalo(candidato["intervalo"]), "muestra": muestra,
            "seleccionable": candidato["tipo"] in ("cruce", "cero_evaluado")}


def _campo(captura: dict, nombre: str) -> float:
    valor = captura.get(nombre)
    if isinstance(valor, str) and len(valor) > LONGITUD_CAMPO_EXPLORACION:
        raise ValueError("Un campo de exploración es demasiado largo; usa notación científica.")
    return real_capturado(valor, {"x_min": "El mínimo de exploración", "x_max": "El máximo de exploración",
                                 "paso": "El paso de exploración"}[nombre])
