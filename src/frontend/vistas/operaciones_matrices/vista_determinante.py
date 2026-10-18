"""Captura y presentación del determinante exacto por triangulación."""
from nicegui import run, ui

from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.panel_matriz_cuadrada import PanelMatrizCuadrada
from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante
from src.frontend.navegacion import ruta_de


class VistaDeterminante:
    """Orquesta una captura cuadrada y delega cálculo/validación al controlador."""

    def __init__(self):
        self.panel_matriz = PanelMatrizCuadrada()
        self._version = 0
        self._calculando = False
        self.ultimo_resultado = None
        self._cliente = ui.context.client
        self._montada = True
        self._cliente.on_delete(self._desmontar)

    def construir(self) -> None:
        """Monta captura, estado accesible y acceso al asistente."""
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("determinantes"))
        ui.page_title("Determinantes | Scalaris")
        self.panel_matriz.inyectar_recursos_cliente()
        with ui.column().classes("vista-raiz w-full max-w-7xl mx-auto p-6 gap-4"):
            ui.label("Determinantes").classes("text-2xl font-bold texto-principal")
            ui.label("Triangulación LU con aritmética exacta.").classes("texto-secundario")
            self.panel_matriz.construir_contenedor()
            ui.button("Calcular determinante", on_click=self.calcular, color=None).classes("boton-principal").props("ripple=false")
            self.resultados = ui.column().classes("panel-tarjeta p-6 w-full min-w-0")
            self.panel_matriz.al_cambiar_datos = self._invalidar_resultado
            self._invalidar_resultado()
        self.panel_ia = PanelIA(self)
        self.panel_ia.construir()

    def _invalidar_resultado(self) -> None:
        self._version += 1
        self.ultimo_resultado = None
        self.resultados.clear()
        with self.resultados:
            ui.label("Introduce una matriz cuadrada y calcula su determinante.").props('role="status"')

    def _desmontar(self) -> None:
        self._montada = False
        self._version += 1

    async def calcular(self, evento) -> None:
        """Ejecuta fuera del bucle UI y descarta resultados de capturas obsoletas."""
        if self._calculando:
            return
        self._calculando = True
        self.ultimo_resultado = None
        version = self._version
        evento.sender.props("loading")
        captura = {"dimension": self.panel_matriz.dimension, "datos": self.panel_matriz.obtener_datos_matriz()}
        self.resultados.clear()
        with self.resultados:
            ui.label("Calculando determinante…").props('role="status" aria-live="polite"')
        try:
            respuesta = await run.io_bound(ControladorDeterminante.procesar_captura, captura)
            if self._montada and not self.resultados.is_deleted and version == self._version:
                self.ultimo_resultado = respuesta
                self._mostrar_resultado(respuesta)
        except Exception:
            if self._montada and not self.resultados.is_deleted and version == self._version:
                self._mostrar_resultado({"estado": "ERROR", "mensaje": "No pudimos calcular el determinante. Revisa los datos y vuelve a intentarlo."})
        finally:
            self._calculando = False
            if not evento.sender.is_deleted:
                evento.sender.props(remove="loading")

    def _mostrar_resultado(self, respuesta: dict) -> None:
        self.resultados.clear()
        with self.resultados:
            if respuesta.get("estado") == "ERROR":
                ui.label(respuesta["mensaje"]).props('role="alert"').classes("distintivo-error")
                return
            valor = formatear_fraccion_texto(respuesta["determinante"])
            ui.label(f"Determinante: {valor}").classes("determinante-valor text-xl texto-principal").props('role="status" aria-live="polite"')
            if respuesta.get("es_singular"):
                ui.label("La matriz es singular.").classes("texto-secundario")
            with ui.expansion("Pasos del cálculo").classes("w-full"):
                for paso in respuesta["pasos"]:
                    ui.label(paso).classes("matematicas-desplazamiento w-full")
