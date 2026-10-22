"""Estado de conversión, agrupación de cifras y selección de bases."""
import asyncio

import pytest

from src.frontend.vistas.sistemas_numericos.vista_sistemas_numericos import VistaSistemasNumericos
from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.backend.utilidades.reglas_dominio import BASES_NUMERICAS


class ElementoSimulado:
    """Registra estilos y limpieza mediante la API de elementos de NiceGUI."""

    def __init__(self):
        self.estilos = []
        self.limpiado = False
        self.text = ""
        self.clases = set()

    def style(self, estilo):
        """Registra el estilo aplicado por el consumidor."""
        self.estilos.append(estilo)

    def clear(self):
        """Marca la limpieza del contenido del elemento."""
        self.limpiado = True

    def classes(self, *argumentos, **opciones):
        """Registra las clases añadidas y retiradas por NiceGUI."""
        self.clases.update(opciones.get('add', '').split())
        self.clases.difference_update(opciones.get('remove', '').split())


class EventoSimulado:
    """Expone el valor de un evento de NiceGUI."""

    def __init__(self, valor):
        self.value = valor


class PestanasSimuladas:
    """Permite consultar y establecer el valor de las pestañas."""

    def __init__(self, valor):
        self.value = valor

    def set_value(self, valor):
        """Actualiza la selección con la API de NiceGUI."""
        self.value = valor


def test_estado_inicial_de_conversion():
    """La interfaz comienza en decimal, sin resultados y con todas las bases."""
    interfaz = VistaSistemasNumericos()
    assert interfaz.base_activa == 'decimal'
    assert interfaz.base_destino == 'todas'
    assert interfaz.boton_convertir is None
    assert interfaz.tiene_resultado is False
    assert 'binario' in BASES_NUMERICAS
    assert 'octal' in BASES_NUMERICAS
    assert 'decimal' in BASES_NUMERICAS
    assert 'hexadecimal' in BASES_NUMERICAS


def test_agrupacion_de_cifras():
    """Agrupa desde la derecha sin desplazar el signo negativo."""
    interfaz = VistaSistemasNumericos()
    assert interfaz._agrupar("11111111", 4) == "1111 1111"
    assert interfaz._agrupar("101010", 4) == "10 1010"
    assert interfaz._agrupar("FF", 2) == "FF"
    assert interfaz._agrupar("1A3F", 2) == "1A 3F"
    assert interfaz._agrupar("-11111111", 4) == "-1111 1111"


def test_pasos_desde_decimal_hacia_todas_las_bases():
    """La entrada decimal genera divisiones sucesivas para las tres bases."""
    conversor = ConversorBases()
    resultado = conversor.decimal_a_todo("42", "todas")
    assert "pasos" in resultado
    pasos = resultado["pasos"]
    assert len(pasos) == 3
    for paso in pasos:
        assert paso["tipo"] == "division_sucesiva"
    destinos = [paso["base_destino"] for paso in pasos]
    assert destinos == [2, 8, 16]


def test_pasos_desde_hexadecimal_hacia_todas_las_bases():
    """La expansión hexadecimal precede las divisiones para binario y octal."""
    conversor = ConversorBases()
    resultado = conversor.hexadecimal_a_todo("2A", "todas")
    assert "pasos" in resultado
    pasos = resultado["pasos"]
    assert pasos[0]["tipo"] == "expansion_posicional"
    assert pasos[0]["base_origen"] == 16
    destinos = [paso["base_destino"] for paso in pasos[1:]]
    assert destinos == [2, 8]


def test_resultados_desincronizados_y_limpieza():
    """La desincronización señala los resultados y la limpieza los oculta."""
    interfaz = VistaSistemasNumericos()
    interfaz.tiene_resultado = True
    tarjeta = ElementoSimulado()
    interfaz.tarjetas = {'decimal': tarjeta}
    interfaz.etiqueta_bits = ElementoSimulado()
    interfaz.contenedor_bits = ElementoSimulado()
    interfaz.contenedor_pasos = ElementoSimulado()
    interfaz.etiqueta_estado = ElementoSimulado()
    interfaz._marcar_resultado_desincronizado()
    assert 'sesion-obsoleta' in tarjeta.clases
    assert 'sesion-obsoleta' in interfaz.contenedor_bits.clases
    assert 'Resultado anterior' in interfaz.etiqueta_estado.text
    assert tarjeta.estilos == [] and interfaz.contenedor_bits.estilos == []
    interfaz._limpiar_resultados()
    assert interfaz.tiene_resultado is False
    assert interfaz.resultados['decimal'] == '0'
    assert 'opacity: 0;' in tarjeta.estilos
    assert 'opacity: 0;' in interfaz.contenedor_bits.estilos


@pytest.mark.anyio
async def test_cambiar_base_destino_permite_decimal():
    """Elegir decimal conserva el valor de las pestañas sin forzar su cambio."""
    interfaz = VistaSistemasNumericos()
    assert interfaz.base_activa == 'decimal'
    interfaz.pestanas_destino = PestanasSimuladas('todas')
    interfaz._cambiar_base_destino(EventoSimulado('decimal'))
    assert interfaz.base_destino == 'decimal'
    assert interfaz.pestanas_destino.value == 'todas'
    await asyncio.sleep(0.01)
