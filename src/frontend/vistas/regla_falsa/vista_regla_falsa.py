"""Orquestación del cálculo vigente y de las capturas de regla falsa."""
from nicegui import ui

from src.ai.contexto import ContextoIA, EstadoContexto
from src.frontend.controladores.biseccion.catalogo_criterios import DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.calculo_raices import ConfiguracionCalculoRaices, resolver_calculo_raices
from src.frontend.controladores.regla_falsa.contexto_regla_falsa import resumir_contexto_regla_falsa
from src.frontend.controladores.regla_falsa.presentacion_grafica import calcular_presentacion
from src.frontend.controladores.regla_falsa.presentacion import titulo_estado
from src.frontend.controladores.sesion_matricial import actualizar_contexto, invalidar_resultado, registrar_calculo
from .acciones_captura import mostrar_recientes
from .composicion import componer_herramienta
from .estado_captura import CAMPOS, CAMPOS_EJERCICIO, capturar, reflejar_intervalo, restaurar_captura, vaciar_captura
from .resultado import mostrar_resultado
from .procedimiento import PanelProcedimiento
from .modos_captura import MODO_BUSQUEDA, MODO_INTERVALO

_CONFIGURACION = ConfiguracionCalculoRaices(
    mensaje_carga="Calculando la raíz por regla falsa…",
    mensaje_error="No se pudo completar el cálculo. Revisa la función y vuelve a intentarlo.",
    mensaje_registro="No se pudo presentar el cálculo de regla falsa",
)
_MENSAJE_RECALCULAR = "No hay un resultado vigente. Calcula de nuevo para continuar."


class VistaReglaFalsa:
    """Compone captura, resultados reales y contexto pedagógico independiente por cliente."""

    def __init__(self):
        self.ultimo_resultado = self.reproductor_pasos = self.tarea_calculo = self.panel_ia = None
        self._revision_captura = self._identificador_calculo = 0
        self.ocupado = self._cargando_captura = self._cerrada = False
        self.historial = []
        self._precision_visual = DECIMALES_PRESENTACION_DEFECTO
        self.detalle_procedimiento = self._foco_procedimiento = self.velocidad_procedimiento = None

    def construir(self) -> None:
        """Monta la herramienta y enlaza edición, Enter y revocación por desconexión o desmontaje."""
        componer_herramienta(self)
        for campo in self._campos_captura():
            campo.on_value_change(self._editar)
            campo.on("keydown.enter", self.enviar_captura)
        for campo in (self.expresion, self.unidad_angular):
            campo.on_value_change(self._editar_exploracion)
        cliente = ui.context.client
        cliente.on_disconnect(self.cerrar)
        cliente.on_delete(self.cerrar)
        cliente.on_connect(self.reabrir)

    def _campos_captura(self) -> tuple:
        return tuple(getattr(self, atributo) for atributo in CAMPOS.values())

    def capturar(self) -> dict:
        """Entrega campos crudos al controlador excluyendo la precisión visual."""
        return capturar(self)

    def _editar(self) -> None:
        if not self._cargando_captura:
            self._retirar_resultado()
            self.estado.set_text("Datos editados. Calcula para obtener un resultado vigente.")

    def _editar_exploracion(self) -> None:
        if not self._cargando_captura:
            self.exploracion.invalidar()
            self._actualizar_previas()

    def _actualizar_previas(self) -> None:
        self.vista_previa.programar()
        self.previa_expresion.programar(self.expresion.value or "")

    async def enviar_captura(self) -> None:
        """Dirige Enter a la tarea activa sin validar parámetros de la otra tarea."""
        if self.modos.value == MODO_BUSQUEDA:
            await self.exploracion.enviar_busqueda()
        else:
            await self.resolver()

    def cambiar_modo(self) -> None:
        """Revoca candidatos al abandonar la búsqueda conservando los campos montados."""
        if self.modos.value == MODO_INTERVALO:
            self.exploracion.invalidar()
        self.seleccion_grafico.cancelar()

    def _retirar_resultado(self) -> None:
        if self.reproductor_pasos is not None:
            self.velocidad_procedimiento = self.reproductor_pasos.velocidad
        invalidar_resultado(self)
        self.detalle_procedimiento = self._foco_procedimiento = None
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
        if not self.contenedor_detalle.is_deleted:
            self.contenedor_detalle.clear()
        if self.panel_ia is not None:
            self.panel_ia.limpiar_foco_explicacion()
        actualizar_contexto(self)

    async def resolver(self, *, puntero: bool = False) -> None:
        """Coordina un trabajador por vista y publica únicamente la captura aún vigente."""
        if not self._cerrada:
            await resolver_calculo_raices(self, calcular_presentacion, _CONFIGURACION, puntero=puntero)
            if not self.ocupado and not self.estado.is_deleted and self.estado.text == _CONFIGURACION.mensaje_carga:
                self.estado.set_text(_MENSAJE_RECALCULAR)

    def _publicar(self, datos: dict, huella: str, *, puntero: bool = False) -> None:
        respuesta = datos["resultado"]
        self._huella_resultado = reflejar_intervalo(self, respuesta, huella)
        self.ultimo_resultado = respuesta
        mostrar_resultado(self, respuesta)
        self.detalle_procedimiento = PanelProcedimiento(self, datos)
        self.detalle_procedimiento.reproductor.velocidad = self.velocidad_procedimiento or "Normal"
        self.detalle_procedimiento.construir()
        self.reproductor_pasos = self.detalle_procedimiento.reproductor
        self.estado.set_text(titulo_estado(respuesta))
        if respuesta["aproximacion"] is not None or respuesta["iteraciones"]:
            registrar_calculo(self.historial, {
                "captura": self.capturar(), "estado": respuesta["estado"], "titulo": titulo_estado(respuesta),
            })
            mostrar_recientes(self)
        actualizar_contexto(self)

    def cargar_captura(self, captura: dict) -> None:
        """Restaura los campos indicados sin calcular y retira cualquier resultado anterior."""
        restaurar_captura(self, captura)
        self.modos.set_value(MODO_INTERVALO)
        self.exploracion.invalidar()
        self._actualizar_previas()
        self._editar()

    def esta_completamente_vacio(self) -> bool:
        """Indica si función y extremos están vacíos, independientemente de las preferencias."""
        captura = self.capturar()
        return (not any(captura[clave] is not None and str(captura[clave]).strip() for clave in CAMPOS_EJERCICIO)
                and not self.exploracion.hay_datos())

    def limpiar_todo(self) -> None:
        """Vacía el ejercicio y retira el resultado conservando preferencias y recientes de sesión."""
        vaciar_captura(self)
        self.exploracion.restablecer()
        self.vista_previa.sincronizar_busqueda()
        self.previa_expresion.programar("")
        self._retirar_resultado()
        self.estado.set_text("Captura vacía. Ingresa una función o carga un ejemplo.")

    def cerrar(self) -> None:
        """Revoca resultados pendientes y publicados al perder el cliente o desmontar la vista."""
        self._cerrada = True
        self.exploracion.cerrar()
        self.vista_previa.cerrar()
        self.previa_expresion.cerrar()
        self._retirar_resultado()
        if not self.estado.is_deleted:
            self.estado.set_text(_MENSAJE_RECALCULAR)

    def reabrir(self) -> None:
        """Permite nuevas solicitudes si el cliente vuelve a conectar con controles montados."""
        self._cerrada = self.contenedor_resultados.is_deleted
        if not self._cerrada:
            self.exploracion.reabrir()
            self.vista_previa.reabrir()
            self.previa_expresion.reabrir(self.expresion.value or "")

    def obtener_contexto_ia(self) -> ContextoIA:
        """Devuelve captura y resumen vigente para Glosa sin incluir el historial completo."""
        return ContextoIA(
            "regla_falsa", "Método de regla falsa", "Búsqueda de raíces", self.capturar(),
            EstadoContexto(resultado=resumir_contexto_regla_falsa(self.ultimo_resultado),
                           foco=self._foco_procedimiento,
                           vacio=not bool(self.expresion.value),
                           nota_ventana="El residuo no es una cota del error en x. La garantía requiere continuidad."),
        )
