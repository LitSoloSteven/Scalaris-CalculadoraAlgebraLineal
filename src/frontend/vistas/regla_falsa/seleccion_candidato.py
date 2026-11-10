"""Carga explícita de intervalos pertenecientes a la exploración vigente."""
from src.frontend.componentes.candidatos_raices import PresentacionCandidatos, mostrar_candidatos
from src.frontend.controladores.exploracion_raices import presentar_candidato

_PRESENTACION = PresentacionCandidatos(
    "Carga un intervalo y pulsa Calcular raíz. La búsqueda es acotada y no garantiza encontrar todas las raíces. "
    "En un cero evaluado se carga su intervalo: si ambos extremos son ceros, el cálculo clásico puede devolver el otro extremo.",
    "regla-falsa-numero",
)


def presentar_candidatos(panel, respuesta: dict) -> None:
    """Muestra evidencia del dominio y acciones únicamente para intervalos aptos."""
    mostrar_candidatos(respuesta, panel.seleccionar, _PRESENTACION)


def seleccionar_candidato(panel, respuesta: dict, candidato: dict) -> None:
    """Carga dos extremos vigentes en una transacción, sin resolver ni prometer un cero elegido."""
    if panel._cerrado or panel.contenedor_resultados.is_deleted or panel.vista.ocupado:
        return
    if panel.respuesta is not respuesta or not any(candidato is actual for actual in respuesta["candidatos"]):
        return
    if not presentar_candidato(candidato)["seleccionable"]:
        return
    inferior, superior = candidato["intervalo"]
    panel.vista.cargar_captura({"extremo_izquierdo": str(inferior), "extremo_derecho": str(superior)})
    panel.vista.inferior.run_method("focus")
