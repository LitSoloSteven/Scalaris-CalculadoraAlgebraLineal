"""Auditoría de las declaraciones de movimiento de los recursos propios."""
import re
import json
import subprocess
from pathlib import Path

RECURSOS = Path(__file__).resolve().parents[1] / 'src/frontend/recursos'
PATRON_TIEMPO = re.compile(r'(?<![\w.])[+-]?\d+(?:\.\d+)?(?:ms|s)\b')
TOKENS = {'press': 200, 'release': 320, 'state': 350, 'state-exit': 260, 'panel': 450,
          'panel-exit': 340, 'view': 600, 'view-exit': 450, 'didactic': 900,
          'didactic-exit': 675, 'reduced': 120}


def _reglas_css(texto):
    texto = re.sub(r'/\*.*?\*/', '', texto, flags=re.S)
    return re.findall(r'([^{}]+)\{([^{}]*)\}', texto)


def _infraccion_declaracion(selector, propiedad, valor, es_tokens):
    if PATRON_TIEMPO.search(valor) and not (es_tokens and propiedad.startswith('--')):
        return f'{selector}: tiempo literal {propiedad}'
    if propiedad.startswith(('animation', 'transition')) and re.search(
        r'(?<![\w-])(?:ease-in(?:-out)?|linear)(?![\w-])', valor
    ):
        return f'{selector}: curva prohibida'
    if propiedad == 'transition' and re.search(r'\ball\b', valor):
        return f'{selector}: transition all'
    return _infraccion_will_change(selector, propiedad)


def _infraccion_will_change(selector, propiedad):
    if propiedad == 'will-change' and any('[data-destacada-activa]' not in parte for parte in selector.split(',')):
        return f'{selector}: will-change permanente'
    return None


def _infracciones_css(texto, es_tokens=False):
    errores = []
    for selector, cuerpo in _reglas_css(texto):
        for declaracion in cuerpo.split(';'):
            if ':' not in declaracion:
                continue
            propiedad, valor = (parte.strip() for parte in declaracion.split(':', 1))
            error = _infraccion_declaracion(selector.strip(), propiedad, valor, es_tokens)
            if error:
                errores.append(error)
    return errores


def test_css_solo_declaraciones_de_tiempo_en_tokens():
    """Busca tiempos y propiedades prohibidas en cada hoja propia."""
    for ruta in (RECURSOS / 'css').glob('*.css'):
        assert not _infracciones_css(ruta.read_text(encoding='utf-8'), ruta.name == 'tokens.css'), ruta


def test_tokens_de_duracion_en_banda():
    """Exige los tokens y valores acordados en milisegundos literales."""
    texto = (RECURSOS / 'css/tokens.css').read_text(encoding='utf-8')
    tokens = re.findall(r'(--dur-[\w-]+)\s*:\s*([^;]+);', texto)
    assert {nombre.removeprefix('--dur-') for nombre, _ in tokens} == set(TOKENS)
    for nombre, declaracion in tokens:
        assert re.fullmatch(r'\d+ms', declaracion.strip()), nombre
        valor = declaracion.strip()[:-2]
        assert int(valor) == TOKENS[nombre.removeprefix('--dur-')], nombre
        assert (0 < float(valor) <= 120) if nombre == '--dur-reduced' else (200 <= float(valor) <= 900), nombre
    for nombre, valor in {'stagger-step': 75, 'stagger-max': 600}.items():
        assert re.search(rf'--{nombre}\s*:\s*{valor}ms\s*;', texto)


def test_javascript_sin_duraciones_o_curvas_literales_en_animaciones():
    """Rechaza duraciones directas y curvas literales en JavaScript."""
    rutas = [str(ruta) for ruta in (RECURSOS / 'js').glob('*.js')]
    analizador = Path(__file__).with_name('comun_auditoria_tiempos.js')
    salida = subprocess.run(['node', '--expose-internals', str(analizador)], input=json.dumps(rutas),
                            text=True, capture_output=True, check=True, encoding='utf-8')
    assert not json.loads(salida.stdout)


def test_auditoria_detecta_regresiones():
    """Comprueba que las reglas detectan casos representativos prohibidos."""
    for css in ('a{transition: all 1s linear}', 'a{will-change: transform}', 'a{animation: x ease-in}'):
        assert _infracciones_css(css)
    assert _infracciones_css('a{animation-delay: -15ms}')
    assert _infracciones_css('a, [data-destacada-activa] b {will-change: transform}')
