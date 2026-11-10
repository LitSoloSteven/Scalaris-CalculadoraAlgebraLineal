"""Carga explícita de intervalos pertenecientes a la exploración vigente."""
from src.frontend.componentes.candidatos_raices import PresentacionCandidatos, mostrar_candidatos
from src.frontend.controladores.captura_exploratoria_raices import intervalo_seleccionable

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
    intervalo = intervalo_seleccionable(panel, respuesta, candidato)
    if intervalo is None:
        return
    inferior, superior = intervalo
    panel.vista.cargar_captura({"extremo_izquierdo": str(inferior), "extremo_derecho": str(superior)})
    panel.vista.inferior.run_method("focus")
