"""Ejercicios agrupados con preferencias explícitas de captura."""
from src.backend.resolutores.raices.contrato_biseccion import LIMITE_ITERACIONES_DEFECTO
from src.backend.resolutores.raices.unidades_angulares import UNIDAD_ANGULAR_DEFECTO
from src.frontend.controladores.biseccion.catalogo_criterios import CRITERIOS
from .modos_captura import MODO_INTERVALO


def _ejercicio(expresion: str, inferior: str, superior: str,
               criterio: tuple[str, int] = ("decimales", CRITERIOS["decimales"][2]),
               unidad: str = UNIDAD_ANGULAR_DEFECTO) -> dict:
    return {"expresion": expresion, "extremo_izquierdo": inferior, "extremo_derecho": superior,
            "criterio": {"tipo": criterio[0], "parametro": criterio[1]},
            "unidad_angular": unidad, "limite_iteraciones": LIMITE_ITERACIONES_DEFECTO,
            "modo": MODO_INTERVALO}


EJEMPLOS = {
    "Básicos": (
        ("Raíz de 2", _ejercicio("x^2 - 2", "1", "2")),
        ("Polinomio del Excel", _ejercicio("x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10", "0.6", "1")),
        ("Potencia décima", _ejercicio("x^10 - 1", "0", "1.3")),
        ("Seno en grados", _ejercicio("2sin(x) − 1", "0", "60", unidad="grados")),
    ),
    "Casos límite": (
        ("Cero en un extremo", _ejercicio("x² − 4", "2", "3")),
        ("Tres iteraciones", _ejercicio("x² − 2", "1", "2", ("iteraciones", 3))),
        ("Posible discontinuidad", _ejercicio("1/(x² − 0.2)", "0", "1")),
    ),
}
