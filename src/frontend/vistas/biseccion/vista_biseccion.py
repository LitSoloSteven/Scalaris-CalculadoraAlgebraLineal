"""Orquestación de captura, vigencia y presentación de la herramienta de raíces."""
import logging

from nicegui import ui

from src.ai.contexto import ContextoIA, EstadoContexto
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.controladores.biseccion.controlador import calcular_presentacion
from src.frontend.controladores.biseccion.catalogo_criterios import CRITERIOS, DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto, registrar_calculo
from src.frontend.navegacion import ruta_de
from .captura import construir_captura
from .resultado import mostrar_resultado
from .selector_criterio import actualizar_guia, enlazar_parametros
from .intervalo_canonico import reflejar_intervalo

registro = logging.getLogger(__name__)


class VistaBiseccion:
    """Compone el módulo con resultados vigentes, reproductor y contexto pedagógico."""

    def __init__(self):
        self.ultimo_resultado = None
        self.reproductor_pasos = None
        self._revision_captura = 0
        self._identificador_calculo = 0
        self.ocupado = False
        self.historial = []
        self._cargando_captura = False

    def construir(self) -> None:
        """Monta la herramienta y enlaza teclado, invalidación y limpieza del reproductor."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("biseccion"))
        with ui.column().classes("biseccion-vista vista-raiz w-full mx-auto p-4 gap-5"):
            construir_captura(self)
            self.estado = ui.label("Ingresa una función o carga un ejemplo para comenzar.").classes("texto-secundario").props('role=status aria-live=polite')
            self.recientes = ui.row().classes("w-full gap-2")
            self.contenedor_resultados = ui.column().classes("w-full min-w-0 gap-5")
        for campo in self._campos_captura():
            campo.on_value_change(self._editar)
            if campo is not self.criterio:
                campo.on("keydown.enter", self.resolver)
        enlazar_parametros(self)
        actualizar_guia(self)
        self.panel_ia.construir()
        ui.context.client.on_disconnect(self._desconectar)

    def _campos_captura(self) -> tuple:
        return self.expresion, self.inferior, self.superior, self.limite, self.criterio

    def capturar(self) -> dict:
        """Devuelve únicamente datos matemáticos comunes y el parámetro activo sin convertirlos."""
        tipo = self.criterio.value
        parametro = self.parametros_criterio[tipo].value
        return {"expresion": self.expresion.value, "extremo_izquierdo": self.inferior.value,
                "extremo_derecho": self.superior.value, "limite_iteraciones": self.limite.value,
                "decimales": parametro if tipo == "decimales" else DECIMALES_PRESENTACION_DEFECTO,
                "criterio": {"tipo": tipo, "parametro": parametro}}

    def _editar(self) -> None:
        if self._cargando_captura:
            return
        invalidar_resultado(self)
        self.contenedor_resultados.clear()
        actualizar_guia(self)
        self.estado.set_text("Datos editados. Calcula para obtener un resultado vigente.")
        self.panel_ia.limpiar_foco_explicacion()
        actualizar_contexto(self)

    async def resolver(self) -> None:
        """Ejecuta en trabajador y publica solo si la captura y solicitud siguen vigentes."""
        if self.ocupado or self.contenedor_resultados.is_deleted:
            return
        self._editar()
        self.ocupado = True
        self.boton_resolver.disable()
        self.boton_resolver.props("loading")
        self.estado.set_text("Calculando el intervalo y preparando la gráfica…")
        try:
            vigente = await ejecutar_calculo_vigente(self, self.capturar, calcular_presentacion)
            if vigente is not None:
                self._publicar(*vigente)
        except Exception:
            registro.exception("No se pudo presentar el cálculo de bisección")
            if not self.estado.is_deleted:
                self.estado.set_text("No se pudo completar el cálculo. Revisa la función y vuelve a intentarlo.")
        finally:
            self.ocupado = False
            if not self.boton_resolver.is_deleted:
                self.boton_resolver.enable()
                self.boton_resolver.props(remove="loading")

    def _publicar(self, respuesta: dict, huella: str) -> None:
        huella = reflejar_intervalo(self, respuesta) or huella
        self.ultimo_resultado, self._huella_resultado = respuesta, huella
        mostrar_resultado(self, respuesta)
        self.estado.set_text("Resultado disponible." if respuesta["estado"] == "EXITO" else respuesta["mensaje"])
        if respuesta.get("aproximacion") is not None:
            registrar_calculo(self.historial, {"captura": self.capturar(), "estado": respuesta["estado"]})
            self._mostrar_recientes()
        actualizar_contexto(self)

    def cargar_captura(self, captura: dict) -> None:
        """Restaura el criterio explícito o el decimal antiguo; los ejemplos conservan preferencias omitidas."""
        self._cargando_captura = True
        try:
            campos = {"expresion": self.expresion, "extremo_izquierdo": self.inferior,
                      "extremo_derecho": self.superior, "limite_iteraciones": self.limite}
            for clave, campo in campos.items():
                if clave in captura:
                    campo.set_value(captura[clave])
            criterio = captura.get("criterio")
            if criterio is not None:
                self.criterio.set_value(criterio["tipo"])
                self.parametros_criterio[criterio["tipo"]].set_value(criterio["parametro"])
            elif "decimales" in captura:
                self.criterio.set_value("decimales")
                self.decimales.set_value(captura["decimales"])
        finally:
            self._cargando_captura = False
        self._editar()

    def _mostrar_recientes(self) -> None:
        self.recientes.clear()
        with self.recientes:
            ui.label("Recientes de esta sesión:").classes("text-sm texto-secundario")
            for indice, calculo in enumerate(self.historial, 1):
                captura = calculo["captura"]
                criterio = captura.get("criterio", {"tipo": "decimales", "parametro": captura["decimales"]})
                etiqueta = f"{CRITERIOS[criterio['tipo']][0]} · {criterio['parametro']}"
                ui.button(f"{indice} · {etiqueta}", color=None,
                          on_click=lambda captura=captura: self.cargar_captura(captura)).classes("boton-discreto").tooltip(str(captura["expresion"]))

    def esta_completamente_vacio(self) -> bool:
        """Indica si los campos del ejercicio no contienen texto."""
        return not any(str(campo.value or "").strip() for campo in (self.expresion, self.inferior, self.superior))

    def limpiar_todo(self) -> None:
        """Vacía el ejercicio y retira sus resultados conservando las preferencias de precisión."""
        for campo in (self.expresion, self.inferior, self.superior):
            campo.set_value("")
        self._editar()
        self.estado.set_text("Captura vacía. Ingresa una función o carga un ejemplo.")

    def _desconectar(self) -> None:
        invalidar_resultado(self)

    def obtener_contexto_ia(self) -> ContextoIA:
        """Entrega a Glosa la captura y un resumen acotado del resultado vigente."""
        resultado = self.ultimo_resultado
        resumen = None if resultado is None else {clave: resultado.get(clave) for clave in (
            "estado", "mensaje", "aproximacion", "intervalo_final", "tolerancia", "cota", "motivo_parada", "metricas",
            "criterio_solicitado", "unidad_criterio", "umbral", "metrica_final", "codigo_diagnostico", "advertencias",
            "diagnostico", "aviso_grafica", "contexto_fallo", "sugerencias")}
        return ContextoIA("biseccion", "Método de bisección", "Búsqueda de raíces", self.capturar(),
                          EstadoContexto(resultado=resumen, vacio=not bool(self.expresion.value),
                                         nota_ventana="Aritmética aproximada. La garantía requiere continuidad en todo el intervalo."))
