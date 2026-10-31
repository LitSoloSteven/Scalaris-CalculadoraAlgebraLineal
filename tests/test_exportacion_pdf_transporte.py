"""Recuperación fragmentada de PNG y validación del manifiesto no confiable."""
import asyncio
import json

import pytest
from src.frontend import constantes
from src.frontend.componentes.exportacion_pdf.captura import capturar_regiones
from src.frontend.componentes.exportacion_pdf import captura as modulo


def _preparar_transporte(monkeypatch, manifiesto=None, truncar=False):
    contenido = 'ABCD' * 350000
    llamadas = []
    async def ejecutar(codigo, **opciones):
        """Emula el límite de mensajes conservando la secuencia de llamadas real."""
        instruccion = codigo.split('capturaPdf.')[1].removesuffix(';')
        nombre, argumentos = instruccion.split('(', 1)
        parametros = json.loads('[' + argumentos[:-1] + ']')
        llamadas.append((nombre, parametros))
        if nombre == 'preparar':
            return manifiesto if manifiesto is not None else {
                'solicitud': 1, 'capturas': [{'clave': 'matrices-resumen', 'longitud': len(contenido)}]}
        if nombre == 'leer':
            _, _, inicio, cantidad = parametros
            assert cantidad <= constantes.PDF_FRAGMENTO_CARACTERES < 999900
            return contenido[inicio:inicio + cantidad - int(truncar)]
        return True
    monkeypatch.setattr(modulo.ui, 'run_javascript', ejecutar)
    return contenido, llamadas


def test_imagen_mayor_que_un_mensaje_se_reconstruye_y_libera(monkeypatch):
    """Un PNG base64 de 1,4 MB viaja en mensajes acotados y se conserva íntegro."""
    contenido, llamadas = _preparar_transporte(monkeypatch)
    capturas = asyncio.run(capturar_regiones('resultado'))
    assert capturas == [{'clave': 'matrices-resumen', 'png': contenido}]
    assert len([nombre for nombre, _ in llamadas if nombre == 'leer']) == 6
    assert llamadas[-1] == ('liberar', [1])


@pytest.mark.parametrize('figuras', [None, [], [{}], [{'clave': 'x', 'longitud': -1}],
    [{'clave': 'x', 'longitud': True}], [{'clave': 'x', 'longitud': 100000000}],
    [{'clave': 'x', 'longitud': 4}] * 13])
def test_manifiesto_invalido_no_recupera_imagenes_y_libera(monkeypatch, figuras):
    """Los límites se comprueban antes de pedir fragmentos y la memoria cliente se retira."""
    _, llamadas = _preparar_transporte(monkeypatch, {'solicitud': 1, 'capturas': figuras})
    with pytest.raises(ValueError):
        asyncio.run(capturar_regiones('resultado'))
    assert [nombre for nombre, _ in llamadas] == ['preparar', 'liberar']


def test_fragmento_incompleto_no_se_entrega_y_libera(monkeypatch):
    """Una respuesta truncada no se convierte en una imagen parcial silenciosa."""
    _, llamadas = _preparar_transporte(monkeypatch, truncar=True)
    with pytest.raises(ValueError):
        asyncio.run(capturar_regiones('resultado'))
    assert llamadas[-1] == ('liberar', [1])
