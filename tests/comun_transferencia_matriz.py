"""Escenarios compartidos de transferencia mediante controles reales."""
from tests.comun_construccion_vistas import VISTAS_RUTAS

MATRIZ_TRANSFERIDA = [["1/1001", "-2/3"], ["0", "1"]]
DESTINOS_MATRICIALES = ("sistemas", "inversa", "determinantes", "factorizacion_lu",
                        "matrices", "leontief", "transformaciones")


def preparar_ruta_lu(monkeypatch) -> None:
    """Registra LU en el arnés conservando su ruta y su constructor reales."""
    monkeypatch.setitem(VISTAS_RUTAS, "factorizacion_lu",
                        ("operaciones_matrices.vista_factorizacion_lu", "VistaFactorizacionLU"))


def leer_matriz(vista, herramienta: str) -> list[list[str]]:
    """Extrae la captura del panel receptor sin ejecutar el cálculo."""
    if herramienta == "sistemas":
        return vista.cuadricula.obtener_datos_matriz()[0]
    if herramienta == "inversa":
        return vista.panel_matriz_cuadrada.obtener_datos_matriz()
    if herramienta in ("determinantes", "factorizacion_lu"):
        return vista.panel_matriz.obtener_datos_matriz()
    if herramienta == "matrices":
        return vista.panel_captura_matrices.obtener_datos_crudos()["A"]["datos"]
    return [[entrada.value for entrada in fila] for fila in vista.entradas_coeficientes]


def activar_boton(boton) -> None:
    """Activa el manejador registrado de un botón sin simular el dominio."""
    manejador = next(evento.handler for evento in boton._event_listeners.values() if evento.type == "click")
    manejador(None)


def token_desde_url(url: str) -> str:
    """Extrae el token de una navegación generada por la acción real."""
    from urllib.parse import parse_qs, urlsplit
    return parse_qs(urlsplit(url).query)["handoff"][0]
