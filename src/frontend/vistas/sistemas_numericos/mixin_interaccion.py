"""Mixin de interacción de usuario y gestión de entradas para Sistemas Numéricos."""
import asyncio
from nicegui import ui
from src.backend.utilidades.reglas_dominio import BASES_NUMERICAS, validar_entrada_base
from src.frontend.controladores.sesion_matricial import actualizar_contexto


class MixinInteraccionSistemasNumericos:
    """Maneja cambios de base, portapapeles, eventos de entrada y desincronización visual."""

    def _cambiar_base_origen(self, evento):
        if not evento.value:
            return
        self.base_activa = evento.value
        self._actualizar_ejemplos()
        actualizar_contexto(self)
        if hasattr(self, 'entrada_valor'):
            try:
                asyncio.create_task(self._al_cambiar_entrada(None))
            except RuntimeError:
                pass

    def _cambiar_base_destino(self, evento):
        if not evento.value:
            return
        self.base_destino = evento.value
        actualizar_contexto(self)
        if not hasattr(self, 'entrada_valor'):
            return
        self._programar_cambio_destino()

    def _programar_cambio_destino(self):
        """Programa la actualización de entrada o resultado tras cambiar la base destino."""
        if self.tiene_resultado:
            self._aplicar_opacidad_tarjetas(revelar=False)
            valor = self.entrada_valor.value or ''
            if valor.strip():
                try:
                    asyncio.create_task(self._ejecutar_conversion(valor, inmediato=True, revelar_tarjetas=False))
                except RuntimeError:
                    pass
        else:
            try:
                asyncio.create_task(self._al_cambiar_entrada(None))
            except RuntimeError:
                pass

    def _actualizar_ejemplos(self):
        self.contenedor_ejemplos.clear()
        ejemplos = {
            'hexadecimal': ['FF', '1A', 'A5'],
            'decimal': ['255', '42', '128'],
            'binario': ['11111111', '101010', '10000000'],
            'octal': ['377', '52', '200']
        }.get(self.base_activa, [])

        with self.contenedor_ejemplos:
            for ejemplo in ejemplos:
                ui.button(
                    ejemplo,
                    on_click=lambda evento, valor=ejemplo: self._establecer_entrada(valor),
                    color=None
                ).classes('boton-discreto py-0 px-3 min-h-0 text-xs font-mono').props('ripple=false')

    def _establecer_entrada(self, valor):
        self.entrada_valor.set_value(valor)
        asyncio.create_task(self._al_cambiar_entrada(None))

    async def _pegar_portapapeles(self):
        try:
            valor = await ui.run_javascript('navigator.clipboard.readText()', timeout=15)
            if valor:
                self._establecer_entrada(valor.strip())
        except Exception:
            self.etiqueta_error.text = "Error al pegar: permiso denegado o portapapeles vacío."

    async def _copiar_resultado(self, identificador_base, boton):
        valor = self.resultados.get(identificador_base, '').replace(' ', '')
        if not valor:
            return
        try:
            exito = await ui.run_javascript(
                f'navigator.clipboard.writeText("{valor}").then(() => true).catch(() => false)',
                timeout=2.0
            )
            if not exito:
                ui.notify("No se pudo copiar", type="warning")
                return
        except Exception:
            pass

        boton.props('icon=check color=positive')

        def restablecer_icono():
            """Restablece el icono del botón tras confirmar la copia."""
            boton.props(remove='color')
            boton.props('icon=content_copy')

        ui.timer(2.0, restablecer_icono, once=True)

    def _intercambiar_base(self, nueva_base):
        if nueva_base == self.base_activa:
            return
        valor = self.resultados.get(nueva_base, '').replace(' ', '')
        self.pestanas_origen.set_value(nueva_base)
        self._establecer_entrada(valor)

    async def _al_cambiar_entrada(self, evento):
        valor = self.entrada_valor.value or ''

        valido, mensaje = validar_entrada_base(valor, BASES_NUMERICAS[self.base_activa])
        self.etiqueta_error.text = '' if valido or not valor else mensaje
        if self.tiene_resultado:
            self._marcar_resultado_desincronizado()
        actualizar_contexto(self)

    def _marcar_resultado_desincronizado(self):
        """Señala resultados anteriores con un borde y un aviso, conservando su legibilidad."""
        for tarjeta in self.tarjetas.values():
            tarjeta.classes(add='sesion-obsoleta')
        if self.contenedor_bits:
            self.contenedor_bits.classes(add='sesion-obsoleta')
        self._publicar_estado('Resultado anterior. Los datos cambiaron; pulsa Convertir para actualizarlo.')

    def _restaurar_vigencia_resultados(self):
        """Retira la señal de obsolescencia tras cualquier conversión exitosa."""
        for elemento in [*self.tarjetas.values(), self.contenedor_bits]:
            if elemento is not None:
                elemento.classes(remove='sesion-obsoleta')
        self._publicar_estado('Conversión lista.')

    def _aplicar_opacidad_tarjetas(self, revelar=True):
        for base, tarjeta in self.tarjetas.items():
            if revelar:
                tarjeta.style('opacity: 1;')

            if base in self.etiquetas_valores:
                self.etiquetas_valores[base].style('opacity: 1;')
        if self.contenedor_bits:
            self.contenedor_bits.style('opacity: 1;')

    async def _convertir_boton(self, evento=None):
        if getattr(self, "_calculando", False):
            return
        revision = getattr(self, '_revision_captura', 0)
        boton = self.boton_convertir
        valor = self.entrada_valor.value or ''
        if not self._validar_conversion(valor):
            return
        self._calculando = True
        self._publicar_estado("Convirtiendo…")
        if boton:
            boton.props("loading")
        try:
            await asyncio.sleep(0)
            if revision != getattr(self, '_revision_captura', 0):
                return
            if await self._ejecutar_conversion(valor, inmediato=True, revelar_tarjetas=False):
                self._aplicar_opacidad_tarjetas(revelar=True)
        except Exception:
            self._limpiar_resultados()
            self.etiqueta_error.text = "No se pudo convertir. Revisa el número e inténtalo de nuevo."
        finally:
            self._finalizar_conversion(boton, revision)

    def _finalizar_conversion(self, boton, revision: int) -> None:
        self._calculando = False
        if revision == getattr(self, '_revision_captura', 0):
            self._publicar_estado("Conversión lista." if self.tiene_resultado else "Revisa el número y vuelve a convertir.")
        if boton:
            boton.props(remove="loading")

    def _validar_conversion(self, valor: str) -> bool:
        valido, mensaje = validar_entrada_base(valor, BASES_NUMERICAS[self.base_activa])
        if not valido:
            self.etiqueta_error.text = mensaje
            if self.tiene_resultado:
                self._limpiar_resultados()
            ui.notify(mensaje, type='warning')
        return valido

    def _publicar_estado(self, mensaje: str) -> None:
        etiqueta = getattr(self, "etiqueta_estado", None)
        if etiqueta is not None:
            etiqueta.text = mensaje
