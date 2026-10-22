"""Mixin de renderizado de tarjetas, bits y procedimientos para Sistemas Numéricos."""
import asyncio
from nicegui import ui
from src.backend.resolutores.sistemas_numericos.pasos_didacticos import desglosar_bits
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from src.frontend.controladores.captura_contexto import capturar_bases
from .mixin_procedimiento import MixinProcedimientoSistemasNumericos


class MixinRenderizadoSistemasNumericos(MixinProcedimientoSistemasNumericos):
    """Maneja la creación de tarjetas de resultado, cálculo de conversión, bits y pasos detallados."""

    def _crear_tarjeta_resultado(self, identificador_base, titulo, subindice):
        with ui.column().classes('panel-tarjeta p-5 relative overflow-hidden').classes("numericos-tarjeta-conversion") as tarjeta:
            self.tarjetas[identificador_base] = tarjeta

            with ui.row().classes('w-full justify-between items-center mb-2 gap-2 flex-wrap'):
                with ui.row().classes('items-center gap-2'):
                    ui.html(f'<span class="font-bold texto-secundario">{titulo}</span><sub class="font-bold ml-1 text-xs">{subindice}</sub>')
                    distintivo = ui.label('ENTRADA ACTUAL').classes('distintivo-exito text-[10px] font-bold px-2 py-0.5')
                    distintivo.bind_visibility_from(self, 'base_activa', backward=lambda valor: valor == identificador_base)

                with ui.row().classes('gap-2'):
                    ui.button(
                        icon='swap_vert',
                        on_click=lambda evento, base=identificador_base: self._intercambiar_base(base),
                        color=None
                    ).classes('boton-discreto w-8 h-8 p-0 texto-secundario').props('ripple=false aria-label="Usar como entrada"').tooltip('Usar como entrada')
                    ui.button(
                        icon='content_copy',
                        on_click=lambda evento, base=identificador_base: self._copiar_resultado(base, evento.sender),
                        color=None
                    ).classes('boton-discreto w-8 h-8 p-0 texto-secundario').props('ripple=false aria-label="Copiar"').tooltip('Copiar')

            self.etiquetas_valores[identificador_base] = ui.label('0').classes(
                'text-2xl font-mono texto-principal break-all tracking-wide '
            ).bind_text_from(self.resultados, identificador_base)

    def _actualizar_estado_exitoso(self, valor_crudo: str, resultado: dict, revelar_tarjetas: bool) -> None:
        """Actualiza diccionarios de resultados, renderizado de bits y contexto IA."""
        self.resultados['decimal'] = f"{int(resultado['decimal']):,}".replace(',', ' ')
        self.resultados['binario'] = self._agrupar(resultado['binario'], 4)
        self.resultados['octal'] = resultado['octal']
        self.resultados['hexadecimal'] = self._agrupar(resultado['hexadecimal'], 2)

        self.resultados_completos = resultado
        self.tiene_resultado = True

        self._renderizar_bits(resultado['binario'].replace('-', ''))
        self._aplicar_opacidad_tarjetas(revelar=revelar_tarjetas)
        self._restaurar_vigencia_resultados()
        self._mostrar_procedimiento()

        from src.ai.huellas import calcular_huella
        entrada = capturar_bases(self, valor_crudo)
        self._huella_resultado = calcular_huella(entrada)
        actualizar_contexto(self)

        if getattr(self, 'panel_ia', None) and getattr(self, 'contenedor_sugerencias', None):
            self.contenedor_sugerencias.clear()
            with self.contenedor_sugerencias:
                self.panel_ia.renderizar_sugerencias_en_linea()

    async def _ejecutar_conversion(self, valor, inmediato=False, revelar_tarjetas=True):
        revision = getattr(self, '_revision_captura', 0)
        try:
            if not inmediato:
                await asyncio.sleep(0.15)
            if revision != getattr(self, '_revision_captura', 0):
                return False
            if not valor.strip():
                self._limpiar_resultados()
                return False

            valor_crudo = valor
            valor_convertido = valor.upper() if self.base_activa == 'hexadecimal' else valor
            metodo = getattr(self.conversor, f"{self.base_activa}_a_todo")
            resultado = metodo(valor_convertido, self.base_destino)

            if resultado["estado"] == "ERROR":
                self._limpiar_resultados()
                self.etiqueta_error.text = resultado["mensaje"]
                return False

            self._actualizar_estado_exitoso(valor_crudo, resultado, revelar_tarjetas)
            return True
        except asyncio.CancelledError:
            raise

    def _agrupar(self, cadena, tamano_grupo):
        signo = "-" if cadena.startswith("-") else ""
        cifras = cadena.lstrip("-")
        grupos = [cifras[max(i - tamano_grupo, 0):i] for i in range(len(cifras), 0, -tamano_grupo)]
        return signo + " ".join(reversed(grupos))

    def _limpiar_resultados(self):
        reproductor = getattr(self, "reproductor", None)
        if reproductor is not None and hasattr(reproductor, "detener"):
            reproductor.detener()
        self.tiene_resultado = False
        for base in ['decimal', 'binario', 'octal', 'hexadecimal']:
            self.resultados[base] = '0'
        for tarjeta in self.tarjetas.values():
            tarjeta.style('opacity: 0;')
        self.etiqueta_bits.text = ''
        self.contenedor_bits.clear()
        if self.contenedor_bits:
            self.contenedor_bits.style('opacity: 0;')
        self.contenedor_pasos.classes('hidden')
        if getattr(self, 'contenedor_sugerencias', None):
            self.contenedor_sugerencias.clear()

    def _renderizar_bits(self, cadena_binaria):
        self.contenedor_bits.clear()
        cantidad_bits = len(cadena_binaria)
        self.etiqueta_bits.text = f"{cantidad_bits} BITS"

        if cantidad_bits > 32:
            return

        with self.contenedor_bits:
            for dato in desglosar_bits(cadena_binaria):
                color = 'bg-[var(--accent)]' if dato["bit"] == '1' else 'bg-[var(--border-input)]'
                ui.element("div").classes(f"w-4 h-4 rounded-sm {color}").props(
                    f'title="2^{dato["exponente"]} = {dato["peso"]}"'
                )
