"""Vista principal del Conversor de Sistemas Numéricos en Scalaris."""
from nicegui import ui
from src.frontend.componentes.captura.ecuaciones.limpieza_captura import crear_boton_limpieza
from src.frontend.vistas.sistemas_numericos.compartido.limpieza_numerica import MixinLimpiezaBases
from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.backend.utilidades.validacion.reglas_dominio import BASES_NUMERICAS, validar_entrada_base
from src.frontend.componentes.aplicacion.controles.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.aplicacion.base.simbolos import habilitar_simbolos
from src.frontend.navegacion import ruta_de
from src.frontend.componentes.glosa.panel.panel_ia import PanelIA
from src.frontend.controladores.compartido.sesion.captura_contexto import capturar_bases
from .mixin_interaccion import MixinInteraccionSistemasNumericos
from .mixin_renderizado import MixinRenderizadoSistemasNumericos


class VistaSistemasNumericos(MixinLimpiezaBases, MixinInteraccionSistemasNumericos, MixinRenderizadoSistemasNumericos):
    """Controlador de vista modular para conversión de bases numéricas."""

    def __init__(self):
        self.conversor = ConversorBases()
        self.base_activa = 'decimal'
        self.base_destino = 'todas'
        self.tarea_espera = None
        self.resultados = {'decimal': '0', 'binario': '0', 'octal': '0', 'hexadecimal': '0'}
        self.contenedor_bits = None
        self.contenedor_pasos = None
        self.tarjetas = {}
        self.etiquetas_valores = {}
        self.boton_convertir = None
        self.tiene_resultado = False

    def _renderizar_entrada_valor(self) -> None:
        """Renderiza el campo de entrada numérico y botón de pegar."""
        with ui.column().classes('w-full gap-1'):
            with ui.row().classes('w-full relative'):
                self.entrada_valor = ui.input(placeholder='0').classes(
                    'w-full matriz-entrada numericos-entrada numericos-entrada-base'
                )
                self.entrada_valor.props('autocomplete="off" spellcheck="false" aria-label="Número de entrada"')
                habilitar_simbolos(self.entrada_valor, "base")
                self.entrada_valor.on_value_change(self._notificar_entrada)
                self.entrada_valor.on('keydown.enter', self._convertir_boton)

                with ui.row().classes('absolute right-4 top-1/2 -translate-y-1/2'):
                    ui.button(
                        icon='content_paste', on_click=self._pegar_portapapeles, color=None
                    ).classes('boton-icono p-0 texto-secundario').props(
                        'ripple=false aria-label="Pegar desde el portapapeles" title="Pegar desde el portapapeles"'
                    )

            self.etiqueta_error = ui.label('').classes('fuente-pequena numericos-error').props('role="alert"')

    def _renderizar_seccion_destacada(self) -> None:
        """Renderiza la columna principal con base origen, entrada y acciones."""
        with ui.column().classes('w-full panel-tarjeta p-6 gap-5'):
            ui.html('Conversor de bases', tag='h1').classes('text-2xl font-bold texto-principal m-0')

            with ui.column().classes('w-full gap-2'):
                ui.label('Base origen').classes('text-sm font-semibold texto-secundario')
                with ui.tabs().classes(
                    'pestanas-controles pestanas-metodo pestanas-anchas numericos-pestanas w-full'
                ).props('no-caps aria-label="Base origen"') as self.pestanas_origen:
                    ui.tab('decimal', label='Dec')
                    ui.tab('binario', label='Bin')
                    ui.tab('octal', label='Oct')
                    ui.tab('hexadecimal', label='Hex')

            self._renderizar_entrada_valor()

            with ui.row().classes('w-full gap-4 mt-1 flex-wrap numericos-acciones-base'):
                crear_boton_limpieza(self, lambda: not self.boton_convertir.is_deleted,
                                      lambda: [self.entrada_valor])
                self.boton_convertir = ui.button(
                    'Convertir', on_click=self._convertir_boton, color=None
                ).classes('boton-principal flex-[2] min-w-[140px] py-3 text-lg font-bold whitespace-nowrap').props('no-caps')

            self.contenedor_sugerencias = ui.column().classes('w-full mt-1')

    def _renderizar_panel_auxiliar(self) -> None:
        """Renderiza la columna auxiliar con base destino, dígitos válidos y ejemplos."""
        with ui.column().classes('w-full panel-tarjeta p-6 gap-5'):
            with ui.column().classes('w-full gap-2'):
                ui.label('Base destino').classes('text-sm font-semibold texto-secundario')
                with ui.tabs().classes(
                    'pestanas-controles pestanas-metodo pestanas-anchas numericos-pestanas w-full'
                ).props('no-caps aria-label="Base destino"') as self.pestanas_destino:
                    ui.tab('todas', label='Todas')
                    ui.tab('decimal', label='Dec')
                    ui.tab('binario', label='Bin')
                    ui.tab('octal', label='Oct')
                    ui.tab('hexadecimal', label='Hex')

            with ui.column().classes('w-full gap-1 numericos-referencia'):
                ui.label('Referencia de dígitos').classes('text-xs font-semibold texto-secundario')
                self.etiqueta_referencia_digitos = ui.label('').classes('text-sm texto-principal')

            with ui.column().classes('w-full gap-2'):
                ui.label('Ejemplos rápidos:').classes('text-sm texto-secundario')
                self.contenedor_ejemplos = ui.row().classes('gap-2 flex-wrap')

            with ui.row().classes('w-full justify-between items-center gap-2 flex-wrap'):
                self.etiqueta_bits = ui.label('').classes('text-sm font-mono texto-secundario font-bold')
                self.contenedor_bits = ui.row().classes('gap-1 items-center flex-wrap')

    def _renderizar_cuadricula_resultados(self) -> None:
        """Renderiza las cuatro tarjetas de resultados (Dec, Hex, Bin, Oct)."""
        with ui.element('div').classes('disposicion-cuadricula-dos').props('data-pdf-captura=bases-resultado'):
            self._crear_tarjeta_resultado('decimal', 'Decimal', '10')
            self._crear_tarjeta_resultado('hexadecimal', 'Hexadecimal', '16')
            self._crear_tarjeta_resultado('binario', 'Binario', '2')
            self._crear_tarjeta_resultado('octal', 'Octal', '8')

    def construir(self):
        """Construye la interfaz completa de usuario para conversor de bases."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de('bases'))

        with ui.column().classes('w-full max-w-6xl mx-auto q-pa-md mt-6 vista-raiz disposicion-herramienta'):
            with ui.element('div').classes('disposicion-captura-fila'):
                self._renderizar_seccion_destacada()
                self._renderizar_panel_auxiliar()
            with ui.column().classes('disposicion-resultados gap-4'):
                self.etiqueta_estado = ui.label("Ingresa un número y pulsa Convertir.").props('role="status" aria-live="polite"')
                self.contenedor_exportacion_pdf = ui.column().classes('w-full min-w-0')
                with self.contenedor_exportacion_pdf:
                    self._renderizar_cuadricula_resultados()
                    self.contenedor_pasos = ui.column().classes('w-full gap-4 mt-6 hidden').props(
                        'data-pdf-captura=bases-procedimiento')
                    self.contenedor_acciones_pdf = ui.column().classes('w-full')

        self.pestanas_origen.on_value_change(self._cambiar_base_origen)
        self.pestanas_destino.on_value_change(self._cambiar_base_destino)
        self.pestanas_origen.set_value('decimal')
        self.pestanas_destino.set_value('todas')

        self.panel_ia.construir()
        self._actualizar_ejemplos()

    def obtener_contexto_ia(self):
        """Devuelve el contexto de entrada y el resultado vigente para el asistente."""
        from src.ai.contexto.contexto import ContextoIA, EstadoContexto, sanear_cadena_usuario
        from src.ai.huellas import esta_desactualizado
        valor = getattr(getattr(self, 'entrada_valor', None), 'value', None)
        if not valor:
            return ContextoIA("bases", "Conversor de bases", "Conversión", {}, estado=EstadoContexto(vacio=True))

        base_origen = getattr(getattr(self, 'pestanas_origen', None), 'value', self.base_activa)
        base_destino = getattr(getattr(self, 'pestanas_destino', None), 'value', self.base_destino)

        contexto = ContextoIA(
            "bases",
            "Conversor de bases",
            f"{base_origen} a {base_destino}",
            {
                "valor_entrada": sanear_cadena_usuario(valor, 64),
                "base_origen": base_origen,
                "base_destino": base_destino
            }
        )

        entrada_actual = capturar_bases(self, valor)
        contexto.desactualizado = esta_desactualizado(entrada_actual, getattr(self, '_huella_resultado', None))

        if getattr(self, 'tiene_resultado', False):
            if contexto.desactualizado:
                contexto.resultado = None
            else:
                contexto.resultado = {
                    "estado": "EXITO",
                    "resultados": self.resultados.copy()
                }
        elif getattr(getattr(self, 'etiqueta_error', None), 'text', None):
            contexto.resultado = {
                "estado": "ERROR",
                "mensaje": self.etiqueta_error.text
            }

        return contexto

    def obtener_senales_ia(self):
        """Devuelve señales de entrada, error y resultado para elegir sugerencias."""
        from src.frontend.presentacion.sugerencias import Senales, CeldaInvalida
        try:
            estado = "sin_resultado"
            banderas = set()
            invalida = None

            valor = self.entrada_valor.value.strip() if getattr(self, 'entrada_valor', None) and self.entrada_valor.value else ""
            if valor:
                if not validar_entrada_base(valor, BASES_NUMERICAS[self.base_activa])[0]:
                    invalida = CeldaInvalida(etiqueta="el número")

            if getattr(self, 'tiene_resultado', False) and not getattr(self.obtener_contexto_ia(), 'desactualizado', True):
                estado = "resultado"

                resultado = getattr(self, 'resultados_completos', {})
                pasos = resultado.get("pasos", [])

                banderas.update(_banderas_conversion(pasos))

            return Senales(herramienta="bases", estado=estado, banderas=frozenset(banderas), invalida=invalida)
        except Exception:
            return None


def _banderas_conversion(pasos):
    """Identifica divisiones sucesivas y conversiones que incluyen hexadecimal."""
    banderas = set()
    if any(panel.get("tipo") == "division_sucesiva" for panel in pasos):
        banderas.add("division")
    if any(panel.get("base_destino") == 16 or panel.get("base_origen") == 16 for panel in pasos):
        banderas.add("hexadecimal")
    return banderas
