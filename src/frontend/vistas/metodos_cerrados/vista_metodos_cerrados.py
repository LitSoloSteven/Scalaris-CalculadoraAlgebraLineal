"""Composición interna de Bisección y Regla falsa."""
from nicegui import ui

from src.frontend.componentes.aplicacion.controles.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.raices.captura.modos_captura_raices import MODO_BUSQUEDA, MODO_INTERVALO
from src.frontend.componentes.glosa.panel.panel_ia import PanelIA
from src.frontend.controladores.compartido.sesion.actualizacion_cancelable import cancelar_actualizacion
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION
from src.frontend.navegacion import ruta_de
from src.frontend.presentacion.tema import configurar_tema
from .acciones import AccionesMetodosCerrados
from .calculo import CalculoIndividual
from .captura import CapturaMetodosCerrados, captura_vacia, limpiar_captura
from .contexto import construir_contexto
from .continuidad import ContinuidadMetodosCerrados
from .exploracion import ExploracionMetodosCerrados
from .grafica import GraficaMetodosCerrados
from .montaje import MENSAJE_INICIAL, montar_contenido
from .presentacion_vigente import PresentacionVigente
from .salida import SalidaMetodosCerrados

class VistaMetodosCerrados:
    """Conecta ambas tareas con las regiones compartidas y su ciclo de vida."""

    def __init__(self, metodo: str = BISECCION):
        self.captura = CapturaMetodosCerrados(self, metodo)
        self.grafica = GraficaMetodosCerrados(self.captura)
        self.salida = SalidaMetodosCerrados(self)
        self.presentacion = PresentacionVigente(self)
        self.acciones = AccionesMetodosCerrados(self.aplicar_intervalo)
        self.continuidad = ContinuidadMetodosCerrados(self)
        self.exploracion = ExploracionMetodosCerrados(
            self, self.aplicar_intervalo, self.presentacion.mostrar_detalle,
            al_editar_rango=self.grafica.editar_rango_busqueda, al_buscar=self.captura.mostrar_carga_busqueda,
        )
        self.calculo = CalculoIndividual(self)
        self.tarea_calculo = self.ultimo_resultado = self.ultimo_ampliado = self.interruptor_examen = None
        self.ocupado = self._cerrada = False
        self._revision_captura = 0
        self.candidato_activo = self._huella_resultado = None

    @property
    def en_busqueda(self) -> bool:
        """Indica si el formulario se dedica a buscar intervalos."""
        return self.modos.value == MODO_BUSQUEDA

    @property
    def inferior(self):
        """Expone el campo donde enfocan las propuestas de intervalo."""
        return self.captura.inferior

    @property
    def _precision_visual(self) -> int:
        return self.acciones.precision(self.captura.metodo_activo)

    @_precision_visual.setter
    def _precision_visual(self, precision: int) -> None:
        self.acciones.fijar_precision(self.captura.metodo_activo, precision)

    @property
    def modo_examen(self) -> bool:
        """Devuelve la preferencia aplicable al resultado activo."""
        if self._examen_lote:
            return self.exploracion.lote.modo_examen
        return self.acciones.examen(self.captura.metodo_activo)

    @modo_examen.setter
    def modo_examen(self, activo: bool) -> None:
        """Guarda el modo examen en el cálculo o lote que está a la vista."""
        if self._examen_lote:
            self.exploracion.lote.modo_examen = activo
        else:
            self.acciones.fijar_examen(self.captura.metodo_activo, activo)

    @property
    def _examen_lote(self) -> bool:
        return self.candidato_activo is not None and self.captura.metodo_activo == BISECCION

    @property
    def boton_resolver(self):
        """Expone el botón asociado a la solicitud individual."""
        return self.captura.boton_resolver

    @property
    def parametros_criterio(self) -> dict:
        """Expone los borradores que el diagnóstico puede seleccionar."""
        return self.captura.parametros_criterio

    def construir(self) -> None:
        """Monta la vista dentro de la página que la consume."""
        self.panel_ia = PanelIA(self)
        regiones = montar_contenido(self)
        self.contenedor_resultados = regiones.resultados
        self.contenedor_procedimiento = regiones.procedimiento
        cliente = ui.context.client
        cliente.on_disconnect(self.cerrar)
        cliente.on_delete(self.cerrar)
        cliente.on_connect(self._reabrir)
        self.panel_ia.construir()
        self.exploracion.actualizar_captura()

    def capturar(self) -> dict:
        """Entrega una instantánea cruda de la solicitud y su método."""
        return self.captura.capturar()

    async def resolver(self) -> None:
        """Publica el cálculo individual solo si su método y captura siguen vigentes."""
        await self.calculo.resolver()

    async def enviar(self) -> None:
        """Envía exclusivamente la tarea seleccionada en el formulario."""
        if self.en_busqueda:
            await self.exploracion.buscar()
        elif self.estados_entrada.validar():
            await self.resolver()

    def cambiar_modo(self, _evento) -> None:
        """Revoca trabajos de la tarea anterior y conserva sus borradores."""
        if self._cerrada:
            return
        self.calculo.revocar()
        self.grafica.cancelar_seleccion()
        if self.salida.reproductor is not None:
            self.salida.reproductor.pausar()
        self.exploracion.establecer_activa(self.en_busqueda)
        self.continuidad.actualizar()
        self.actualizar_grafica()
        if self.ultimo_resultado is None:
            self.estado.set_text(MENSAJE_INICIAL)

    def editar_captura(self) -> None:
        """Revoca el cálculo anterior después de editar campos o cambiar de método."""
        if self._cerrada:
            return
        self.calculo.revocar()
        self.grafica.cancelar_seleccion()
        self.presentacion.descartar()
        self.exploracion.actualizar_captura()
        self.estado.set_text(MENSAJE_INICIAL)
        self.continuidad.actualizar()
        self.captura.actualizar_guia()
        self.actualizar_grafica()

    def actualizar_grafica(self) -> None:
        """Actualiza la orientación, la fórmula y la curva de la captura visible."""
        if not self._cerrada:
            self.estados_entrada.actualizar()
            self.captura.previa_expresion.programar(self.captura.expresion.value or "")
            self.grafica.actualizar()

    def cargar_captura(self, captura: dict) -> None:
        """Restaura un ejercicio o una propuesta sin lanzar el cálculo."""
        self.captura.restaurar(captura)
        self.editar_captura()

    def aplicar_intervalo(self, captura: dict) -> None:
        """Carga un intervalo encontrado y prepara el recorrido de cálculo individual."""
        if self._cerrada:
            return
        self.modos.set_value(MODO_INTERVALO)
        self.cargar_captura(captura)
        self.inferior.run_method("focus")

    def obtener_contexto_ia(self):
        """Entrega a Glosa el contexto de la captura, el resultado y el paso vigentes."""
        return construir_contexto(self)

    def esta_completamente_vacio(self) -> bool:
        """Indica si limpiar retiraría datos del ejercicio o del rango visual."""
        return captura_vacia(self.captura) and not self.exploracion.hay_datos()

    def limpiar_todo(self) -> None:
        """Vacía el ejercicio y el encuadre, y conserva las preferencias del método."""
        self.estados_entrada.limpiar()
        limpiar_captura(self.captura)
        self.exploracion.restablecer()
        self.editar_captura()

    def cerrar(self) -> None:
        """Revoca ambos trabajos y detiene la reproducción al desconectar el cliente."""
        if self._cerrada:
            return
        self._cerrada = True
        self.calculo.cerrar()
        self.grafica.cancelar_seleccion()
        self.presentacion.individual = None
        self.exploracion.cerrar()
        self.continuidad.cancelar()
        cancelar_actualizacion(getattr(self.panel_ia, "_tarea_actualizacion", None))
        self.panel_ia.foco_explicacion = None
        self.panel_ia.contexto_adjuntado = ""
        if not self.contenedor_resultados.is_deleted:
            self._retirar_resultado()
        self.grafica.cerrar()
        self.captura.previa_expresion.cerrar()

    def _reabrir(self) -> None:
        if self._cerrada and not self.contenedor_resultados.is_deleted:
            self._cerrada = False
            self.calculo.reabrir()
            self.estado.set_text(MENSAJE_INICIAL)
            self.exploracion.reabrir()
            self.continuidad.actualizar()
            self.grafica.reabrir()
            self.captura.previa_expresion.reabrir(self.captura.expresion.value or "")
            self.panel_ia.limpiar_foco_explicacion()
            self.panel_ia.limpiar_contexto()
            self.panel_ia.programar_actualizacion_contexto()

    def _retirar_resultado(self) -> None:
        self.presentacion.retirar()

    def _publicar(self, datos: dict, _huella: str, *, puntero: bool = False) -> None:
        respuesta = datos["resultado"]
        entrada = respuesta.get("entrada") or {}
        if entrada.get("intervalo_invertido"):
            self.captura.reflejar_intervalo(entrada)
            self.captura.actualizar_guia()
        self.estado.set_text("Resultado disponible." if respuesta["estado"] != "ERROR" else "Revisa el diagnóstico del cálculo.")
        self.presentacion.publicar(datos, puntero=puntero)
        self.acciones.registrar(self.capturar(), respuesta, datos.get("ampliado"))


def montar_pagina(vista: VistaMetodosCerrados) -> None:
    """Monta la vista y sus recursos con la identidad de navegación canónica."""
    configurar_tema("metodos_cerrados")
    crear_estructura_aplicacion(vista, ruta_activa=ruta_de("metodos_cerrados"))
    vista.construir()
