"""Acción única para exportar un resultado vigente desde cualquier herramienta."""
import copy

from nicegui import run, ui
from src.frontend import textos
from src.frontend.componentes.sonido import emitir_sonido
from src.frontend.controladores.exportacion_pdf.documento import generar_pdf
from src.frontend.controladores.exportacion_pdf.portada import nombre_archivo
from src.frontend.controladores.exportacion_pdf.vigencia import EnlacePDF
from .captura import capturar_regiones
from .dialogo import DialogoPortada
from .indicador import crear_indicador, cargar_indicador
from .secuencia import preparar_secuencia


class ExportacionPDF:
    """Coordina captura y trabajador; descarta resultados obsoletos o diálogos cancelados."""

    def __init__(self, herramienta: str, resultado: dict, enlace: EnlacePDF):
        self.herramienta = herramienta
        self.resultado = resultado
        self.enlace = enlace
        self.ocupado = False
        self.dialogo = None
        self.boton = ui.button(textos.PDF_EXPORTAR, icon='picture_as_pdf', color=None,
                               on_click=self.abrir).classes('boton-discreto pdf-control').props(
                                   f'ripple=false data-pdf-excluir aria-label="{textos.PDF_EXPORTAR}"')
        with self.boton:
            self.indicador = crear_indicador()
        self.actualizar()

    def actualizar(self) -> None:
        """Retira el botón cuando el resultado pierde su huella o deja de estar montado."""
        if not self.boton.is_deleted:
            self.boton.set_visibility(self.enlace.vigente(self.resultado))

    def abrir(self) -> None:
        """Abre una portada reutilizable solo si el resultado sigue vigente."""
        self.actualizar()
        if self.ocupado or not self.enlace.vigente(self.resultado):
            return
        if self.dialogo is None:
            self.dialogo = DialogoPortada(self.generar, self.boton)
        self.dialogo.abrir()

    async def generar(self) -> None:
        """Valida portada y genera en trabajador; publica solo si el testigo sigue vigente."""
        if self.ocupado:
            return
        portada = self.dialogo.validar()
        if portada is None:
            return
        if not self.enlace.vigente(self.resultado):
            self.dialogo.estado.set_text(textos.PDF_ERROR_OBSOLETO)
            return
        testigo = self.enlace.testigo()
        self._cargar(True)
        try:
            with preparar_secuencia(self.herramienta, self.enlace):
                await self._exportar(portada, testigo)
        except Exception:
            if self._dialogo_abierto():
                self.dialogo.estado.set_text(textos.PDF_ERROR_GENERACION)
        finally:
            portada.clear()
            self._cargar(False)

    def _pausar_procedimiento(self) -> None:
        reproductor = (getattr(self.enlace.vista, 'reproductor_pasos', None)
                       or getattr(self.enlace.vista, 'reproductor', None))
        if reproductor is not None:
            reproductor.pausar()

    async def _exportar(self, portada: dict, testigo: tuple) -> None:
        self._pausar_procedimiento()
        emitir_sonido('exportar_inicio')
        self.dialogo.estado.set_text(textos.PDF_CAPTURANDO)
        try:
            capturas = await capturar_regiones(self.enlace.raiz)
        except ValueError:
            if self._dialogo_abierto():
                self.dialogo.estado.set_text(textos.PDF_ERROR_CAPTURA)
            return
        if not self._puede_entregar(testigo):
            return
        self.dialogo.estado.set_text(textos.PDF_GENERANDO)
        try:
            documento, reducida = await run.io_bound(generar_pdf, self.herramienta, portada,
                                                     copy.deepcopy(self.resultado), capturas)
        except ValueError as error:
            if self._dialogo_abierto():
                permitidos = (textos.PDF_ERROR_IMAGEN, textos.PDF_ERROR_GLIFOS)
                self.dialogo.estado.set_text(str(error) if str(error) in permitidos else textos.PDF_ERROR_GENERACION)
            return
        if self._puede_entregar(testigo):
            ui.download(documento, filename=nombre_archivo(self.herramienta, portada['fecha']), media_type='application/pdf')
            self.dialogo.estado.set_text(textos.PDF_AVISO_REDUCCION if reducida else '')
            emitir_sonido('exportar')

    def _dialogo_abierto(self) -> bool:
        return not self.dialogo.dialogo.is_deleted and self.dialogo.dialogo.value

    def _puede_entregar(self, testigo: tuple) -> bool:
        if not self._dialogo_abierto():
            return False
        if self.enlace.comprobar(testigo, self.resultado):
            return True
        self.dialogo.estado.set_text(textos.PDF_ERROR_OBSOLETO)
        return False

    def _cargar(self, ocupado: bool) -> None:
        self.ocupado = ocupado
        if not self.boton.is_deleted:
            self.boton.set_enabled(not ocupado)
            cargar_indicador(self.indicador, ocupado)
        if not self.dialogo.dialogo.is_deleted:
            self.dialogo.cargar(ocupado)


def renderizar_boton_pdf(herramienta: str, resultado: dict, enlace: EnlacePDF) -> ExportacionPDF:
    """Monta el componente compartido y devuelve su control de actualización de vigencia."""
    return ExportacionPDF(herramienta, resultado, enlace)
