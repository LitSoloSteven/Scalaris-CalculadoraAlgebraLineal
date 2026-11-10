"""Adaptación serializable de la exploración y sus etiquetas de presentación."""
from dataclasses import asdict

from src.backend.resolutores.raices.contrato_exploracion import EntradaExploracion
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
from src.backend.resolutores.raices.limites_exploracion import MAXIMO_EVALUACIONES_REFINAMIENTO
from src.frontend.controladores.captura_real import real_capturado
from src.frontend.controladores.biseccion.presentacion import numero
from src.frontend.controladores.biseccion.presentacion_diagnostico import texto_intervalo
from src.frontend.controladores.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO, rango_grafica

LONGITUD_CAMPO_EXPLORACION = 64
PASO_EXPLORACION_DEFECTO = "0.1"
_DENSIDAD_AUTOMATICA = (RANGO_GRAFICA_DEFECTO[1] - RANGO_GRAFICA_DEFECTO[0]) / float(PASO_EXPLORACION_DEFECTO)
ETIQUETAS_CANDIDATOS = {
    "cruce": "Cruce de signo",
    "cero_evaluado": "Cero evaluado aproximado",
    "posible_contacto": "Posible contacto con el eje",
    "segmento_invalido": "Segmento con evaluación inválida",
    "discontinuidad": "Restricción estructural identificada",
}
_MOTIVOS_CONTACTO = {
    "limite_refinamientos": "Se alcanzó el límite de refinamientos locales; el contacto sigue sin certificar.",
    "presupuesto_global": "El presupuesto global no permite otro refinamiento de este contacto.",
    "precision": "La precisión disponible no permite dos sondeos interiores distintos.",
    "cero_evaluado": "El refinamiento encontró un cero evaluado aproximado, sin prueba simbólica.",
    "cruce": "El refinamiento encontró un cambio de signo evaluado; la continuidad no está certificada.",
    "segmento_invalido": "Se detuvo el refinamiento por una evaluación inválida.",
    "discontinuidad": "Se detuvo el refinamiento por una restricción estructural identificada.",
}


def resolver_exploracion(captura: dict) -> dict:
    """Convierte texto y delega al dominio; devuelve éxito o error visible sin lanzar ValueError."""
    try:
        if not isinstance(captura, dict):
            raise ValueError("Revisa los campos de exploración.")
        expresion = captura.get("expresion", "")
        entrada = EntradaExploracion(expresion, _campo(captura, "x_min"),
                                     _campo(captura, "x_max"), _campo(captura, "paso"),
                                     unidad_angular=captura.get("unidad_angular", "radianes"))
        return {"estado": "EXITO", "mensaje": "Exploración disponible.", **asdict(explorar_intervalos(entrada))}
    except ValueError as error:
        return {"estado": "ERROR", "mensaje": str(error), "candidatos": (), "advertencias": (), "evaluaciones": 0}


def sugerir_paso(captura: dict) -> float:
    """Divide la escala antes de restar extremos para evitar desbordamiento."""
    minimo, maximo = rango_grafica(captura)
    paso = maximo / _DENSIDAD_AUTOMATICA - minimo / _DENSIDAD_AUTOMATICA
    if paso <= 0:
        raise ValueError("No se puede representar el paso automático para este rango. Introduce un paso manual.")
    return paso


def presentar_candidato(candidato: dict) -> dict:
    """Entrega etiqueta, intervalo completo y aptitud según la clasificación del dominio."""
    muestra = ""
    if candidato["abscisa"] is not None:
        muestra = f"x = {numero(candidato['abscisa'], True)}; f(x) = {numero(candidato['valor'], True)}"
    return {"etiqueta": ETIQUETAS_CANDIDATOS[candidato["tipo"]],
            "intervalo": texto_intervalo(candidato["intervalo"]), "muestra": muestra,
            "seleccionable": candidato["tipo"] in ("cruce", "cero_evaluado")}


def texto_consumo_exploracion(respuesta: dict) -> str:
    """Distingue muestras de malla y consumo auxiliar sin recalcular sus contadores."""
    return (f"Evaluaciones de malla: {respuesta['evaluaciones']} · "
            f"Auxiliares: {respuesta.get('evaluaciones_refinamiento', 0)}/{MAXIMO_EVALUACIONES_REFINAMIENTO} · "
            f"Refinamientos: {respuesta.get('refinamientos', 0)} · Registros: {len(respuesta['candidatos'])}")


def detalles_contacto(candidato: dict) -> tuple[str, ...]:
    """Presenta evidencia y cierre locales; capturas antiguas sin evidencia conservan su formato."""
    evidencia = candidato.get("evidencia_contacto")
    if evidencia is None:
        return ()
    return (f"Refinamiento local: {evidencia['refinamientos']} pasos y {evidencia['evaluaciones']} evaluaciones auxiliares.",
            f"f(x) inicial: {numero(evidencia['valor_inicial'], True)}; "
            f"escala vecinal inicial: {numero(evidencia['escala_inicial'], True)}.",
            _MOTIVOS_CONTACTO[evidencia["motivo"]])


def _campo(captura: dict, nombre: str) -> float:
    valor = captura.get(nombre)
    if isinstance(valor, str) and len(valor) > LONGITUD_CAMPO_EXPLORACION:
        raise ValueError("Un campo de exploración es demasiado largo; usa notación científica.")
    return real_capturado(valor, {"x_min": "El mínimo de exploración", "x_max": "El máximo de exploración",
                                 "paso": "El paso de exploración"}[nombre])
