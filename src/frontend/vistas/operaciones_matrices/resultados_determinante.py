"""Cálculo vigente, presentación y registro de determinantes exitosos."""
from nicegui import run, ui

from src.ai.huellas import calcular_huella
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante
from src.frontend.controladores.sesion_matricial import actualizar_contexto, captura_sigue_vigente, calculo_sigue_vigente
from src.frontend import textos
from ._presentacion_determinante import montar_reproductor
from ._tarjeta_determinante import mostrar_tarjeta_determinante, mostrar_interpretacion_determinante
from src.frontend.componentes.copia_resultado import renderizar_copia_resultado
from src.frontend.componentes.acciones_matriz import renderizar_acciones_matriz


class ResultadosDeterminante:
    """Orquesta el trabajador y publica únicamente cálculos de la captura vigente."""

    async def calcular(self, evento) -> None:
        """Calcula fuera del bucle UI y descarta respuestas después de editar o salir."""
        emisor = evento.sender
        if not self._puede_actualizar_resultados(emisor):
            return
        self._invalidar_resultado()
        solicitud = self._identificador_calculo
        revision = self._revision_captura
        captura = self._capturar()
        huella = calcular_huella(captura)
        self._activar_carga(emisor, solicitud)
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.label(textos.DETERMINANTES_CALCULANDO).props('role=status aria-live=polite')
        try:
            respuesta = await run.io_bound(ControladorDeterminante.procesar_captura, captura)
            if not self._respuesta_vigente(emisor, solicitud, revision, huella):
                return
            if respuesta.get('estado') == 'EXITO':
                self.ultimo_resultado = respuesta
                self._huella_resultado = huella
                self._registrar_exito(captura, respuesta)
            self._mostrar_resultado(respuesta)
            if respuesta.get('estado') == 'EXITO':
                with self.contenedor_resultados:
                    renderizar_acciones_matriz("determinantes", captura['datos'])
            actualizar_contexto(self)
        except Exception:
            if self._respuesta_vigente(emisor, solicitud, revision, huella):
                self._mostrar_resultado({'estado': 'ERROR', 'mensaje': textos.DETERMINANTES_ERROR})
        finally:
            self._finalizar_carga(emisor, solicitud)

    def _respuesta_vigente(self, emisor, solicitud: int, revision: int, huella: str) -> bool:
        return (self._puede_actualizar_resultados(emisor) and calculo_sigue_vigente(self, solicitud)
                and captura_sigue_vigente(self, revision, huella, self._capturar()))

    def _registrar_exito(self, captura: dict, respuesta: dict) -> None:
        self._agregar_a_historial({
            **captura, 'estado': 'DETERMINANTE_SINGULAR' if respuesta['es_singular'] else 'DETERMINANTE_CALCULADO',
            'determinante': formatear_fraccion_texto(respuesta['determinante']),
        })

    def _mostrar_resultado(self, respuesta: dict) -> None:
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            if respuesta.get('estado') == 'ERROR':
                ui.label(respuesta['mensaje']).props('role=alert').classes('distintivo-error')
                return
            mostrar_tarjeta_determinante(respuesta)
            renderizar_copia_resultado(respuesta)
            self.panel_ia.renderizar_sugerencias_en_linea()
            self.reproductor_pasos = montar_reproductor(respuesta, self.panel_ia)
            mostrar_interpretacion_determinante()
