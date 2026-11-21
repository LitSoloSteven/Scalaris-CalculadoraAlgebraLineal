"""Recientes de sesión y preferencias de presentación de métodos cerrados."""
from collections.abc import Callable

from nicegui import ui

from src.frontend.controladores.raices.biseccion.captura.catalogo_criterios import DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.raices.biseccion.presentacion.presentacion_criterio import titulo_estado
from src.frontend.controladores.raices.metodos_cerrados.adaptadores import BISECCION, METODOS
from src.frontend.controladores.raices.regla_falsa.presentacion.presentacion_ampliada import descripcion_captura, titulo_configurado
from src.frontend.controladores.compartido.sesion.sesion_matricial import registrar_calculo
from src.frontend.vistas.biseccion.acciones_captura import desplegable


class AccionesMetodosCerrados:
    """Conserva ejercicios y preferencias visuales durante la vida de la vista."""

    def __init__(self, cargar_captura: Callable[[dict], None]):
        self._cargar_captura = cargar_captura
        self._historial: dict[str, list[dict]] = {metodo: [] for metodo in METODOS}
        self._precisiones: dict[str, int] = {}
        self._examenes: dict[str, bool] = {}

    def construir(self) -> None:
        """Monta los recientes en una sección operable con teclado."""
        with desplegable("Recientes de esta sesión"):
            self._recientes = ui.column().classes("w-full min-w-0 gap-2")
        self._mostrar_recientes()

    def registrar(self, captura: dict, respuesta: dict, ampliado: dict | None = None) -> None:
        """Guarda una captura del resultado individual cuando tiene valor o filas válidas."""
        if respuesta.get("aproximacion") is None and not respuesta.get("iteraciones"):
            return
        metodo = captura["metodo"]
        titulo = titulo_estado(respuesta) if metodo == BISECCION else titulo_configurado(respuesta, ampliado)
        registrar_calculo(self._historial[metodo], {"captura": captura, "titulo": titulo})
        if not self._recientes.is_deleted:
            self._mostrar_recientes()

    def precision(self, metodo: str) -> int:
        """Devuelve los decimales de presentación elegidos para el método."""
        return self._precisiones.get(metodo, DECIMALES_PRESENTACION_DEFECTO)

    def fijar_precision(self, metodo: str, precision: int) -> None:
        """Guarda los decimales ya validados por el control visual."""
        self._precisiones[metodo] = precision

    def examen(self, metodo: str) -> bool:
        """Indica si el modo examen individual está activo para el método."""
        return self._examenes.get(metodo, False)

    def fijar_examen(self, metodo: str, activo: bool) -> None:
        """Guarda la preferencia individual al accionar el interruptor."""
        self._examenes[metodo] = activo

    def _mostrar_recientes(self) -> None:
        self._recientes.clear()
        with self._recientes:
            if not any(self._historial.values()):
                ui.label("Los cálculos con aproximación o filas válidas aparecerán aquí.").classes(
                    "text-sm texto-secundario")
            for metodo, registros in self._historial.items():
                if registros:
                    self._mostrar_metodo(metodo, registros)

    def _mostrar_metodo(self, metodo: str, registros: list[dict]) -> None:
        with ui.column().classes("w-full min-w-0 gap-1"):
            ui.label(METODOS[metodo]).classes("font-semibold texto-principal")
            for registro in registros:
                captura = registro["captura"]
                ui.button(_etiqueta(captura, registro["titulo"]), color=None,
                          on_click=lambda captura=captura: self._cargar_captura(captura)).classes(
                              "boton-discreto max-w-full min-w-0 text-left [overflow-wrap:anywhere]").props(
                                  "type=button ripple=false")


def _etiqueta(captura: dict, titulo: str) -> str:
    extremos = f"[{captura['extremo_izquierdo']}, {captura['extremo_derecho']}]"
    return (f"{captura['expresion']} · {extremos} · {descripcion_captura(captura)} · "
            f"{captura['unidad_angular']} · {titulo}")
