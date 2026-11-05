"""Orquestación de captura, vigencia y presentación de la herramienta de raíces."""
import logging

from nicegui import ui

from src.ai.contexto import ContextoIA, EstadoContexto
from src.backend.resolutores.raices.contrato_biseccion import ESTADO_DISCONTINUIDAD
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.controladores.biseccion.controlador import calcular_presentacion
from src.frontend.controladores.biseccion.catalogo_criterios import DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.biseccion.contexto_biseccion import resumir_contexto_biseccion
from src.frontend.controladores.biseccion.presentacion_criterio import etiqueta_aproximacion, titulo_estado
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto, registrar_calculo
from src.frontend.navegacion import ruta_de
from .acciones_captura import mostrar_recientes
from .composicion import componer_herramienta
from .estado_captura import hay_rangos_editados, restaurar_captura, vaciar_captura
from .estados_entrada import actualizar_expresion, actualizar_intervalo
from .modos_captura import MODO_BUSQUEDA, MODO_INTERVALO
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
        self._cero_preferido = None
        self.modo_examen = False

    def construir(self) -> None:
        """Monta la herramienta y enlaza teclado, invalidación y limpieza del reproductor."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("biseccion"))
        componer_herramienta(self)
        self._enlazar_captura()
        self.panel_ia.construir()
        ui.context.client.on_disconnect(self._desconectar)
        ui.context.client.on_connect(self._reconectar)

    def _enlazar_captura(self) -> None:
        self.expresion.on_value_change(self._editar_funcion)
        self.unidad_angular.on_value_change(self._editar_funcion)
        self.expresion.on("blur", lambda: actualizar_expresion(self, validar=True))
        for campo in (self.inferior, self.superior, self.limite):
            campo.on("keydown.enter", self.enviar_calculo)
            campo.on("blur", lambda: actualizar_intervalo(self, validar=True))
        self.inferior.on_value_change(self._editar_intervalo)
        self.superior.on_value_change(self._editar_intervalo)
        self.limite.on_value_change(self._editar)
        self.criterio.on_value_change(self._editar)
        self.expresion.on("keydown.enter", self._enviar_funcion)
        enlazar_parametros(self)
        actualizar_expresion(self)
        actualizar_intervalo(self)
        actualizar_guia(self)

    def _campos_captura(self) -> tuple:
        return self.expresion, self.inferior, self.superior, self.limite, self.criterio, self.unidad_angular

    def capturar(self) -> dict:
        """Devuelve únicamente datos matemáticos comunes y el parámetro activo sin convertirlos."""
        tipo = self.criterio.value
        parametro = self.parametros_criterio[tipo].value
        captura = {"expresion": self.expresion.value, "extremo_izquierdo": self.inferior.value,
                   "extremo_derecho": self.superior.value, "limite_iteraciones": self.limite.value,
                   "decimales": parametro if tipo == "decimales" else DECIMALES_PRESENTACION_DEFECTO,
                   "criterio": {"tipo": tipo, "parametro": parametro}, "unidad_angular": self.unidad_angular.value}
        if self._cero_preferido is not None:
            captura["cero_preferido"] = self._cero_preferido
        return captura

    def _editar_intervalo(self) -> None:
        if self._cargando_captura:
            return
        self._cero_preferido = None
        self._invalidar_calculo()

    def _editar_funcion(self) -> None:
        if self._cargando_captura:
            return
        self._cero_preferido = None
        self._invalidar_funcion()
        self._invalidar_calculo()

    def _invalidar_funcion(self) -> None:
        self.exploracion.invalidar()
        self.vista_previa.programar()
        actualizar_expresion(self)

    def _editar(self) -> None:
        if self._cargando_captura:
            return
        self.exploracion.invalidar()
        self.vista_previa.programar()
        self._invalidar_calculo()

    def _invalidar_calculo(self) -> None:
        self._retirar_resultado()
        actualizar_intervalo(self)
        actualizar_guia(self)
        self.estado.set_text("Datos editados. Calcula para obtener un resultado vigente.")

    def _retirar_resultado(self) -> None:
        invalidar_resultado(self)
        self.contenedor_resultados.clear()
        self.panel_ia.limpiar_foco_explicacion()
        actualizar_contexto(self)

    def cambiar_modo(self, evento) -> None:
        """Pausa el procedimiento al ocultarlo y conserva la captura y sus resultados."""
        if evento.value == MODO_BUSQUEDA and self.reproductor_pasos is not None:
            self.reproductor_pasos.pausar()

    async def _enviar_funcion(self) -> None:
        if self.modos.value == MODO_BUSQUEDA:
            await self.exploracion.enviar_busqueda()
        else:
            await self.enviar_calculo()

    async def enviar_calculo(self) -> None:
        """Envía el cálculo desde los controles de Tengo el intervalo."""
        if self.modos.value == MODO_INTERVALO and not self.ocupado:
            actualizar_expresion(self, validar=True)
            actualizar_intervalo(self, validar=True)
            actualizar_guia(self, validar=True)
            await self.resolver()

    async def resolver(self) -> None:
        """Ejecuta en trabajador y publica solo si la captura y solicitud siguen vigentes."""
        if self.ocupado or self.contenedor_resultados.is_deleted:
            return
        self._retirar_resultado()
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
        if respuesta.get("aproximacion") is not None or respuesta.get("iteraciones"):
            titulo = titulo_estado(respuesta)
            if respuesta["estado"] not in ("EXITO", ESTADO_DISCONTINUIDAD) and respuesta.get("aproximacion") is not None:
                titulo += " · " + etiqueta_aproximacion(respuesta)
            registrar_calculo(self.historial, {"captura": self.capturar(), "estado": respuesta["estado"], "titulo": titulo})
            mostrar_recientes(self)
        actualizar_contexto(self)

    def cargar_captura(self, captura: dict) -> None:
        """Restaura los campos como unidad y abre la tarea del intervalo si recibe un par."""
        anterior = self.capturar()
        restaurar_captura(self, captura)
        modo = captura.get("modo")
        if modo in (MODO_INTERVALO, MODO_BUSQUEDA):
            self.modos.set_value(modo)
        elif "extremo_izquierdo" in captura and "extremo_derecho" in captura:
            self.modos.set_value(MODO_INTERVALO)
        actual = self.capturar()
        if any(anterior[clave] != actual[clave] for clave in ("expresion", "unidad_angular")):
            self._invalidar_funcion()
        elif any(anterior[clave] != actual[clave] for clave in ("criterio", "limite_iteraciones")):
            self._editar()
            return
        if anterior != actual or "expresion" in captura:
            self._invalidar_calculo()

    def esta_completamente_vacio(self) -> bool:
        """Indica si limpiar dejaría intactos el ejercicio y sus rangos."""
        campos = self.expresion, self.inferior, self.superior
        hay_ejercicio = any(campo.value is not None and str(campo.value).strip() for campo in campos)
        return not (hay_ejercicio or hay_rangos_editados(self))

    def limpiar_todo(self) -> None:
        """Vacía el ejercicio y retira sus resultados conservando las preferencias de precisión."""
        vaciar_captura(self)
        self._invalidar_funcion()
        self.exploracion.mostrar_estado_inicial()
        self._invalidar_calculo()
        self.estado.set_text("Captura vacía. Ingresa una función o carga un ejemplo.")

    def _desconectar(self) -> None:
        invalidar_resultado(self)
        self.exploracion.cerrar()
        self.vista_previa.cerrar()
        self.resolucion_multiple.cerrar()

    def _reconectar(self) -> None:
        self.exploracion.reabrir()
        self.vista_previa.reabrir()
        self.resolucion_multiple.reabrir()

    def obtener_contexto_ia(self) -> ContextoIA:
        """Entrega a Glosa la captura y un resumen acotado del resultado vigente."""
        resumen = resumir_contexto_biseccion(self.ultimo_resultado)
        return ContextoIA("biseccion", "Método de bisección", "Búsqueda de raíces", self.capturar(),
                          EstadoContexto(resultado=resumen, vacio=not bool(self.expresion.value),
                                         nota_ventana="Aritmética aproximada. La garantía requiere continuidad en todo el intervalo."))
