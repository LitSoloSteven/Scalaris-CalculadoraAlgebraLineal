"""Página principal de análisis exacto de espacios y subespacios vectoriales."""
from __future__ import annotations

import logging

from nicegui import ui

from src.frontend.componentes.aplicacion.base.sonido import emitir_sonido
from src.frontend.componentes.aplicacion.controles.estructura_aplicacion import (
    crear_estructura_aplicacion,
)
from src.frontend.componentes.glosa.panel.panel_ia import PanelIA
from src.frontend.componentes.resultados.acciones.avisos_resultado import (
    MENSAJE_ERROR_INESPERADO,
)
from src.frontend.controladores.algebra.operaciones_vectores.contexto_subespacios import (
    obtener_contexto_subespacio,
    obtener_senales_subespacio,
)
from src.frontend.controladores.algebra.operaciones_vectores.controlador_subespacios import (
    analizar_subespacio_desde_captura,
    normalizar_modo_subespacios,
)
from src.frontend.controladores.compartido.sesion.calculo_vigente import (
    ejecutar_calculo_vigente,
)
from src.frontend.controladores.compartido.sesion.sesion_matricial import (
    actualizar_contexto,
    invalidar_resultado,
)
from src.frontend.navegacion import ruta_de
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    AYUDA_MODOS,
    ESTADO_CALCULO_MODOS,
    ESTADO_EDICION,
    ESTADO_INICIAL_MODOS,
    MODO_GENERADORES,
    MODO_RESTRICCIONES,
    NOMBRES_MODOS,
    TITULO_PAGINA,
)
from src.frontend.vistas.algebra.operaciones_vectores.panel.captura_generadores import (
    CapturaGeneradores,
)
from src.frontend.vistas.algebra.operaciones_vectores.panel.captura_restricciones import (
    CapturaRestricciones,
)
from src.frontend.vistas.algebra.operaciones_vectores.panel.exportacion_subespacios import (
    montar_exportacion_subespacio,
)
from src.frontend.vistas.algebra.operaciones_vectores.panel.resultado_subespacios import (
    mostrar_resultado_subespacio,
)

_REGISTRO = logging.getLogger(__name__)


def _limpiar_asistente(vista: VistaEspaciosSubespacios) -> None:
    vista.actualizar_exportacion_pdf = None
    vista.panel_ia.limpiar_foco_explicacion()
    vista.panel_ia.limpiar_contexto()
    cancelar = getattr(vista.panel_ia, "cancelar_consulta_activa", None)
    if callable(cancelar):
        cancelar()


def _crear_vigencia_paso(vista: VistaEspaciosSubespacios, resultado: dict):
    def _sigue_vigente(paso) -> bool:
        reproductor = vista.reproductor_pasos
        return (
            vista.ultimo_resultado is resultado and vista.modo == resultado.get("modo")
            and not vista.contenedor_resultados.is_deleted and reproductor is not None
            and reproductor.pasos[reproductor.indice_actual] is paso
        )

    return _sigue_vigente


def _sonido_resultado(resultado: dict) -> str:
    if resultado.get("estado") != "EXITO":
        return "error"
    return "exito" if resultado.get("es_subespacio") else "aviso"


class VistaEspaciosSubespacios:
    """Orquesta generadores y restricciones, el análisis vigente y la presentación."""

    def __init__(self, modo_inicial: str = MODO_GENERADORES) -> None:
        self.modo = normalizar_modo_subespacios(modo_inicial)
        self.captura_generadores = CapturaGeneradores(self.editar)
        self.captura_restricciones = CapturaRestricciones(self.editar)
        self.reproductor_pasos = None
        self.ultimo_resultado = None
        self.actualizar_exportacion_pdf = None
        self._identificador_calculo = 0
        self._revision_captura = 0
        self._huella_resultado = None
        self._cliente = None
        self.panel_ia = PanelIA(self)
        self.selector_modo = None
        self.ayuda = None
        self.contenedor_generadores = None
        self.contenedor_restricciones = None
        self.boton_analizar = None
        self.estado = None
        self.contenedor_resultados = None

    @property
    def captura(self) -> CapturaGeneradores | CapturaRestricciones:
        """Devuelve el panel de captura correspondiente al modo activo."""
        if self.modo == MODO_RESTRICCIONES:
            return self.captura_restricciones
        return self.captura_generadores

    def construir(self) -> None:
        """Monta la estructura compartida, el selector de modo y los paneles principales."""
        self._cliente = ui.context.client
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("espacios_subespacios"))
        self.captura_generadores.inyectar_recursos_cliente()
        self.captura_restricciones.inyectar_recursos_cliente()
        self._cliente.on_delete(self._cerrar)
        with ui.column().classes("vista-raiz subespacios-raiz w-full max-w-7xl mx-auto mt-4"):
            self._construir_cabecera()
            with ui.element("div").classes("disposicion-dividida"):
                self._construir_panel_entrada()
                self._construir_panel_resultados()
        self.panel_ia.construir()

    def _construir_cabecera(self) -> None:
        ui.label(TITULO_PAGINA).classes("text-2xl font-bold texto-principal").props(
            "role=heading aria-level=1"
        )
        with ui.tabs(value=self.modo).classes("pestanas-controles pestanas-metodo").props(
            'dense no-caps aria-label="Modo de definición del conjunto"'
        ) as self.selector_modo:
            for clave, etiqueta in NOMBRES_MODOS.items():
                ui.tab(clave, label=etiqueta)
        self.ayuda = ui.label(AYUDA_MODOS[self.modo]).classes("texto-secundario")
        self.selector_modo.on_value_change(lambda evento: self._cambiar_modo(evento.value))

    def _construir_panel_entrada(self) -> None:
        with ui.column().classes("disposicion-panel panel-tarjeta subespacios-panel"):
            with ui.column().classes("w-full min-w-0") as self.contenedor_generadores:
                self.captura_generadores.construir()
            with ui.column().classes("w-full min-w-0") as self.contenedor_restricciones:
                self.captura_restricciones.construir()
            self._actualizar_visibilidad_modos()
            with ui.row().classes("w-full items-center flex-wrap gap-2 mt-2"):
                ui.button("Cargar ejemplo", on_click=self._cargar_ejemplo_activo, color=None).classes(
                    "boton-discreto"
                ).props("ripple=false")
                ui.button("Limpiar", on_click=self._limpiar_activo, color=None).classes(
                    "boton-discreto"
                ).props("ripple=false")
                self.boton_analizar = ui.button(
                    "Analizar", on_click=self.analizar, color=None
                ).classes("boton-principal").props("ripple=false aria-label=Analizar")

    def _construir_panel_resultados(self) -> None:
        with ui.column().classes("disposicion-panel panel-tarjeta subespacios-panel"):
            ui.label("Resultado").classes("text-xl font-semibold texto-principal")
            self.estado = ui.label(ESTADO_INICIAL_MODOS[self.modo]).classes("texto-secundario").props(
                "role=status aria-live=polite"
            )
            self.contenedor_resultados = ui.column().classes("w-full min-w-0")

    def _actualizar_visibilidad_modos(self) -> None:
        if self.contenedor_generadores is not None:
            self.contenedor_generadores.set_visibility(self.modo == MODO_GENERADORES)
        if self.contenedor_restricciones is not None:
            self.contenedor_restricciones.set_visibility(self.modo == MODO_RESTRICCIONES)

    def _cambiar_modo(self, nuevo_modo: object) -> None:
        if not isinstance(nuevo_modo, str) or nuevo_modo not in NOMBRES_MODOS or nuevo_modo == self.modo:
            return
        self.modo = nuevo_modo
        self._actualizar_visibilidad_modos()
        if self.ayuda is not None:
            self.ayuda.set_text(AYUDA_MODOS[self.modo])
        self._retirar_resultado()
        if self.boton_analizar is not None and not self.boton_analizar.is_deleted:
            self.boton_analizar.props("loading=false")
        if self.estado is not None and not self.estado.is_deleted:
            self.estado.set_text(ESTADO_INICIAL_MODOS[self.modo])
        actualizar_contexto(self)

    def _cargar_ejemplo_activo(self) -> None:
        self.captura.cargar_ejemplo()

    def _limpiar_activo(self) -> None:
        self.captura.limpiar()

    def editar(self) -> None:
        """Retira resultados obsoletos al cambiar cualquier dato de entrada."""
        self._retirar_resultado()
        if self.boton_analizar is not None and not self.boton_analizar.is_deleted:
            self.boton_analizar.props("loading=false")
        if self.estado is not None and not self.estado.is_deleted:
            self.estado.set_text(ESTADO_EDICION)
        actualizar_contexto(self)

    def _campos_captura(self) -> list[ui.input]:
        return self.captura.campos_entrada()

    async def analizar(self) -> None:
        """Ejecuta el análisis en segundo plano y publica solo si la captura sigue vigente."""
        self._retirar_resultado()
        solicitud = self._identificador_calculo
        self.captura.marcar_diagnostico(None)
        self.estado.set_text(ESTADO_CALCULO_MODOS[self.modo])
        self.boton_analizar.props("loading=true")
        actualizar_contexto(self)
        try:
            respuesta = await ejecutar_calculo_vigente(
                self, self.captura.obtener, analizar_subespacio_desde_captura
            )
            if respuesta is not None:
                tema = await self._tema_actual()
                if self._identificador_calculo == solicitud and not self.contenedor_resultados.is_deleted:
                    self._publicar(respuesta[0], respuesta[1], tema)
        except Exception as error:
            self._manejar_fallo_inesperado(error, solicitud)
        finally:
            if self._identificador_calculo == solicitud and not self.boton_analizar.is_deleted:
                self.boton_analizar.props("loading=false")

    def _manejar_fallo_inesperado(self, error: Exception, solicitud: int) -> None:
        _REGISTRO.error("Error en espacios y subespacios: %s", type(error).__name__)
        if self._identificador_calculo == solicitud and not self.estado.is_deleted:
            self._retirar_resultado()
            self.estado.set_text(MENSAJE_ERROR_INESPERADO)
            emitir_sonido("error")

    async def _tema_actual(self) -> str:
        cliente = self._cliente
        if cliente is None or cliente.is_deleted or not cliente.has_socket_connection:
            return "papel"
        try:
            valor = await cliente.run_javascript(
                "document.documentElement.getAttribute('data-tema') || 'papel'", timeout=2.0
            )
            return valor if valor in ("papel", "marea", "medianoche") else "papel"
        except Exception:
            return "papel"

    def _publicar(self, resultado: dict, huella: str, tema: str) -> None:
        self.estado.set_text("")
        self.captura.marcar_diagnostico(resultado.get("diagnostico"))
        self.ultimo_resultado = resultado
        self._huella_resultado = huella
        with self.contenedor_resultados:
            self.reproductor_pasos = mostrar_resultado_subespacio(
                resultado, tema=tema, panel_ia=self.panel_ia, sigue_vigente=_crear_vigencia_paso(self, resultado),
            )
            montar_exportacion_subespacio(self, resultado)
        emitir_sonido(_sonido_resultado(resultado))
        actualizar_contexto(self)

    def _retirar_resultado(self) -> None:
        invalidar_resultado(self)
        _limpiar_asistente(self)
        if self.contenedor_resultados is not None and not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()

    def _cerrar(self) -> None:
        invalidar_resultado(self)
        _limpiar_asistente(self)

    def obtener_contexto_ia(self):
        """Entrega a Glosa la captura activa y el resumen del resultado vigente."""
        return obtener_contexto_subespacio(self)

    def obtener_senales_ia(self):
        """Devuelve el estado, celda inválida y banderas de Espacios y subespacios."""
        return obtener_senales_subespacio(self)
