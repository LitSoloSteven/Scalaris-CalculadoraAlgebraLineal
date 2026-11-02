"""Validación de campos, fechas españolas, nombres seguros y glifos base."""
import pytest

from src.frontend import constantes as limites
from src.frontend.controladores.exportacion_pdf.glifos import texto_admitido
from src.frontend.controladores.exportacion_pdf.portada import validar_portada, fecha_espanola, nombre_archivo
from tests.comun_exportacion_pdf import PORTADA


def test_portada_normaliza_sin_mutar_y_no_acepta_vacios():
    """Devuelve una copia normalizada y errores orientativos separados por campo."""
    datos = {**PORTADA, 'nombre': '  Ana de Prueba  '}
    portada, errores = validar_portada(datos)
    assert not errores and portada['nombre'] == PORTADA['nombre']
    assert datos['nombre'].startswith('  ')
    _, errores = validar_portada({})
    assert set(errores) == {'nombre', 'fecha', 'docente', 'grupo'}
    assert 'Escribe tu nombre completo' in errores['nombre']


@pytest.mark.parametrize('campo,valor', [
    ('nombre', 'a' * (limites.PDF_MAXIMO_NOMBRE + 1)),
    ('docente', 'a' * (limites.PDF_MAXIMO_DOCENTE + 1)),
    ('grupo', 'a' * (limites.PDF_MAXIMO_GRUPO + 1)), ('grupo', 'A-12'),
    ('grupo', 'A 12'), ('nombre', 'Ana\x00'), ('nombre', 'Ana ⁻¹'),
    ('docente', None), ('fecha', '2026-02-30'), ('fecha', '2026-1-1'),
    ('fecha', '0000-01-01'), ('fecha', None),
])
def test_campos_invalidos_se_senalan_sin_exponer_su_valor(campo, valor):
    """Los límites, fechas imposibles, controles y símbolos generan errores por campo."""
    _, errores = validar_portada({**PORTADA, campo: valor})
    assert campo in errores
    if isinstance(valor, str) and len(valor) > 3:
        assert valor not in errores[campo]


def test_fecha_espanola_independiente_del_locale():
    """Nombra los doce meses y admite el día bisiesto según el calendario real."""
    assert fecha_espanola('2026-10-15') == '15 de octubre de 2026'
    assert fecha_espanola('2024-02-29') == '29 de febrero de 2024'
    assert fecha_espanola('2026-12-01') == '1 de diciembre de 2026'
    with pytest.raises(ValueError):
        fecha_espanola('2026-02-29')


@pytest.mark.parametrize('herramienta', ['Sistemas de ecuaciones', '../../Matríz\\inversa', '☃', 'x' * 200])
def test_nombre_archivo_ascii_sin_rutas(herramienta):
    """La descarga conserva un prefijo fijo y fecha ISO sin separadores de ruta."""
    nombre = nombre_archivo(herramienta, PORTADA['fecha'])
    assert nombre.isascii() and nombre.startswith('Scalaris_') and nombre.endswith('_2026-10-15.pdf')
    assert '/' not in nombre and '\\' not in nombre and '..' not in nombre
    assert len(nombre) <= len('Scalaris__2026-10-15.pdf') + limites.PDF_MAXIMO_IDENTIFICADOR_ARCHIVO


def test_cobertura_times_y_texto_con_marcado_literal():
    """Las letras españolas y metacaracteres son representables; los superíndices ausentes no."""
    assert texto_admitido('Álgebra, Muñoz & <Ana> × ≈') is False
    assert texto_admitido('Álgebra, Muñoz & <Ana> ×')
    assert not texto_admitido('⁻¹')
    assert not validar_portada({**PORTADA, 'nombre': '<b>Ana & Sol</b>'})[1]
