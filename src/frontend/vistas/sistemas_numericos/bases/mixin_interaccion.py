"""Mixin de interacción de usuario y gestión de entradas para Sistemas Numéricos."""
import asyncio
from nicegui import ui
from src.frontend.componentes.aplicacion.base.sonido import emitir_sonido, notificar
from src.backend.utilidades.validacion.reglas_dominio import BASES_NUMERICAS, validar_entrada_base
from src.frontend.controladores.compartido.sesion.sesion_matricial import actualizar_contexto, notificar_edicion


_REFERENCIA_DIGITOS = {
    'decimal': 'Dígitos válidos en decimal: 0–9 (signo opcional −).',
    'binario': 'Dígitos válidos en binario: 0 y 1 (prefijo opcional 0b, signo opcional −).',
    'octal': 'Dígitos válidos en octal: 0–7 (prefijo opcional 0o, signo opcional −).',
    'hexadecimal': 'Dígitos válidos en hexadecimal: 0–9 y A–F (prefijo opcional 0x, signo opcional −).',
}


async def _leer_portapapeles_cliente() -> dict:
    """Lee el portapapeles del navegador y distingue vacío de rechazo de permisos."""
    script = (
        "(async () => { try { "
        "if (!navigator.clipboard?.readText) return {estado: 'error'}; "
        "const texto = await navigator.clipboard.readText(); "
        "return texto && texto.trim() ? {estado: 'ok', texto: texto.trim()} : {estado: 'vacio'}; "
        "} catch { return {estado: 'error'}; } })()"
    )
    resultado = await ui.run_javascript(script, timeout=3.0)
    if isinstance(resultado, str):
        limpio = resultado.strip()
        return {'estado': 'ok', 'texto': limpio} if limpio else {'estado': 'vacio'}
    return resultado if isinstance(resultado, dict) else {'estado': 'error'}


class MixinInteraccionSistemasNumericos:
    """Maneja cambios de base, portapapeles, eventos de entrada y desincronización visual."""

    def _cambiar_base_origen(self, evento):
        if not evento.value:
            return
        self.base_activa = evento.value
        notificar_edicion(self)
        self._actualizar_referencia_digitos()
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
        notificar_edicion(self)
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

    def _actualizar_referencia_digitos(self):
        referencia = getattr(self, 'etiqueta_referencia_digitos', None)
        if referencia is not None:
            referencia.set_text(_REFERENCIA_DIGITOS.get(self.base_activa, ''))

    def _establecer_entrada(self, valor):
        self.entrada_valor.set_value(valor)
        asyncio.create_task(self._al_cambiar_entrada(None))

    async def _pegar_portapapeles(self):
        try:
            resultado = await _leer_portapapeles_cliente()
        except Exception:
            resultado = {'estado': 'error'}
        estado = resultado.get('estado')
        if estado == 'ok':
            self._establecer_entrada(resultado['texto'])
            return
        mensaje = (
            'El portapapeles está vacío. Copia un número o escríbelo directamente.'
            if estado == 'vacio'
            else 'No pudimos leer el portapapeles. Pega con Ctrl+V o escribe el número.'
        )
        self.etiqueta_error.text = mensaje
        notificar(mensaje, type='warning')

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
                notificar("No se pudo copiar", type="warning")
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

    def _notificar_entrada(self, evento):
        """Versiona y orienta la edición antes de que pueda iniciarse otra conversión."""
        notificar_edicion(self)
        self._orientar_entrada()

    async def _al_cambiar_entrada(self, evento):
        self._orientar_entrada()

    def _orientar_entrada(self):
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
                emitir_sonido('exito')
        except Exception:
            self._limpiar_resultados()
            self.etiqueta_error.text = "No se pudo convertir. Revisa el número e inténtalo de nuevo."
            emitir_sonido('error')
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
            notificar(mensaje, type='warning')
        return valido

    def _publicar_estado(self, mensaje: str) -> None:
        etiqueta = getattr(self, "etiqueta_estado", None)
        if etiqueta is not None:
            etiqueta.text = mensaje
