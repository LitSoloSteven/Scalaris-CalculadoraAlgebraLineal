"""Contraste calculado de superficies, estados y figuras de todos los temas."""
from pathlib import Path
import asyncio

import pytest

from src.frontend.tema import (
    PALETAS_POR_TEMA, COLORES_SOLUCION_POR_TEMA,
    COLORES_TEXTO_GRAFICOS, COLORES_CUADRICULA_GRAFICOS, OPACIDAD_PLANOS,
)
from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos
from tests.comun_estilos import analizar_tokens, hexadecimal_a_rgb, razon_contraste
from tests.comun_construccion_vistas import construir_pagina


TEMAS = analizar_tokens('src/frontend/recursos/css/tokens.css')
SUPERFICIES = ['bg-page', 'bg-panel', 'bg-elevated', 'input-bg', 'accent-soft', 'bg-calc-btn']
TEXTOS = ['text-main', 'text-sec', 'text-placeholder', 'accent', 'error', 'success', 'warning']
DISTINTIVOS = [('badge-err-text', 'badge-err-bg'), ('badge-suc-text', 'badge-suc-bg'),
               ('badge-warn-text', 'badge-warn-bg'), ('btn-primary-text', 'btn-primary-bg')]
PASOS = [('accent', 'accent-soft'), ('accent', 'bg-elevated')]


def _contraste(frente, fondo):
    return razon_contraste(hexadecimal_a_rgb(frente), hexadecimal_a_rgb(fondo))


def _componer(frente, fondo, opacidad):
    return tuple(primer * opacidad + segundo * (1 - opacidad)
                 for primer, segundo in zip(hexadecimal_a_rgb(frente), hexadecimal_a_rgb(fondo)))


@pytest.mark.parametrize('tema', TEMAS)
@pytest.mark.parametrize('frente', TEXTOS)
@pytest.mark.parametrize('fondo', SUPERFICIES)
def test_texto_normal_en_todas_las_superficies(tema, frente, fondo):
    """La comparación usa el cociente sin redondear, incluido texto de estados."""
    tokens = TEMAS[tema]
    assert _contraste(tokens['--' + frente], tokens['--' + fondo]) >= 4.5


@pytest.mark.parametrize('tema', TEMAS)
@pytest.mark.parametrize('frente,fondo', DISTINTIVOS + PASOS)
def test_distintivos_y_familias_de_pasos(tema, frente, fondo):
    """Todos los pares usados por las etiquetas conservan legibilidad normal."""
    tokens = TEMAS[tema]
    assert _contraste(tokens['--' + frente], tokens['--' + fondo]) >= 4.5


@pytest.mark.parametrize('tema', TEMAS)
@pytest.mark.parametrize('fondo', SUPERFICIES)
def test_foco_en_todas_las_superficies(tema, fondo):
    """El anillo se distingue también de entradas y superficies elevadas."""
    tokens = TEMAS[tema]
    assert _contraste(tokens['--focus-ring'], tokens['--' + fondo]) >= 3


@pytest.mark.parametrize('tema', TEMAS)
@pytest.mark.parametrize('fondo', ['bg-page', 'bg-panel', 'bg-elevated'])
def test_trazas_ejes_rejillas_y_transparencias(tema, fondo):
    """Compone planos y solución antes de aplicar la transferencia WCAG sRGB."""
    superficie = TEMAS[tema]['--' + fondo]
    colores = PALETAS_POR_TEMA[tema]
    for color in colores + [COLORES_SOLUCION_POR_TEMA[tema], COLORES_TEXTO_GRAFICOS[tema],
                            COLORES_CUADRICULA_GRAFICOS[tema]]:
        assert _contraste(color, superficie) >= 3
    for color in colores:
        compuesto = _componer(color, superficie, OPACIDAD_PLANOS)
        assert razon_contraste(compuesto, hexadecimal_a_rgb(superficie)) >= 3
    solucion = _componer(COLORES_SOLUCION_POR_TEMA[tema], superficie, 0.95)
    assert razon_contraste(solucion, hexadecimal_a_rgb(superficie)) >= 3


@pytest.mark.parametrize('tema', TEMAS)
def test_figura_exporta_rejilla_y_opacidad_medidas(tema):
    """Los valores verificados se aplican a las figuras reales, también en tres dimensiones."""
    resultado = {'numero_variables': 3, 'ecuaciones': [
        {'indice': 1, 'tipo': 'plano', 'coeficientes': [1, 1, 1], 'objetivo': 1},
    ]}
    figura = construir_figura_rectas_planos(resultado, tema=tema)
    assert figura.data[0].opacity == OPACIDAD_PLANOS
    assert figura.layout.scene.xaxis.gridcolor == COLORES_CUADRICULA_GRAFICOS[tema]
    assert figura.layout.xaxis.gridcolor == COLORES_CUADRICULA_GRAFICOS[tema]


def test_bases_obsoletas_siguen_visibles_y_anuncian_actualizacion(monkeypatch):
    """La edición conserva cifras, muestra aviso textual y retira el borde al recalcular."""
    async def comprobar(vista, cliente):
        """Ejercita edición y recálculo automático dentro del cliente real."""
        await vista._ejecutar_conversion('42', inmediato=True)
        anteriores = vista.resultados.copy()
        vista._marcar_resultado_desincronizado()
        assert vista.resultados == anteriores
        assert 'Resultado anterior' in vista.etiqueta_estado.text
        for tarjeta in vista.tarjetas.values():
            assert 'sesion-obsoleta' in tarjeta._classes
            assert tarjeta._style['opacity'] == '1'
        vista._aplicar_opacidad_tarjetas(revelar=False)
        assert all('sesion-obsoleta' in tarjeta._classes for tarjeta in vista.tarjetas.values())
        await vista._ejecutar_conversion('43', inmediato=True, revelar_tarjetas=False)
        assert all('sesion-obsoleta' not in tarjeta._classes for tarjeta in vista.tarjetas.values())
        assert all(etiqueta._style['opacity'] == '1' for etiqueta in vista.etiquetas_valores.values())
        assert vista.resultados['decimal'] == '43'
        assert vista.etiqueta_estado.text == 'Conversión lista.'

    asyncio.run(construir_pagina(monkeypatch, 'bases', comprobar))


def test_inversa_anuncia_obsolescencia_sin_duplicar_aviso(monkeypatch):
    """Ediciones sucesivas mantienen un solo aviso accesible en resultados anteriores."""
    async def comprobar(vista, cliente):
        """Comprueba la identidad y el texto del aviso entre ediciones."""
        vista.ultimo_resultado = {'estado': 'EXITO'}
        vista._al_cambiar_matriz()
        aviso = vista._aviso_resultado_obsoleto
        vista._al_cambiar_matriz()
        assert vista._aviso_resultado_obsoleto is aviso
        assert aviso._props['role'] == 'status'
        assert 'Resultado anterior' in aviso.text

    asyncio.run(construir_pagina(monkeypatch, 'inversa', comprobar))


def test_opacidades_estables_no_reducen_textos_y_marcadores():
    """Se protegen placeholders y estados que antes componían dos atenuaciones."""
    carpeta = Path('src/frontend/recursos/css')
    entradas = (carpeta / 'componentes_entradas.css').read_text(encoding='utf-8')
    glosa = (carpeta / 'vistas_glosa_componentes.css').read_text(encoding='utf-8')
    assert 'opacity: 0.6' not in entradas + glosa
    assert 'opacity: 0.5' not in entradas + glosa
    base = (carpeta / 'base.css').read_text(encoding='utf-8')
    assert 'html .q-field--float .q-field__native::placeholder' in base
    assert '.sesion-obsoleta {' in base
    assert 'html .glosa-sugerencia[disabled]' in base
