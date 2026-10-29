"""Auditoría de las declaraciones de movimiento de los recursos propios."""
import re
from pathlib import Path

RECURSOS = Path(__file__).resolve().parents[1] / 'src/frontend/recursos'
PATRON_TIEMPO = re.compile(r'(?<![\w.-])\d+(?:\.\d+)?(?:ms|s)\b')
PATRON_LITERAL_JS = re.compile(r'''["']?(?:duration|delay)["']?\s*[:=]\s*[+-]?\d|cubic-bezier\s*\(''', re.I)


def _reglas_css(texto):
    texto = re.sub(r'/\*.*?\*/', '', texto, flags=re.S)
    return re.findall(r'([^{}]+)\{([^{}]*)\}', texto)


def _infracciones_css(texto, es_tokens=False):
    errores = []
    for selector, cuerpo in _reglas_css(texto):
        for declaracion in cuerpo.split(';'):
            if ':' not in declaracion:
                continue
            propiedad, valor = (parte.strip() for parte in declaracion.split(':', 1))
            if PATRON_TIEMPO.search(valor) and not (es_tokens and propiedad.startswith('--')):
                errores.append(f'{selector.strip()}: tiempo literal {propiedad}')
            if propiedad.startswith(('animation', 'transition')) and re.search(
                r'(?<![\w-])(?:ease-in(?:-out)?|linear)(?![\w-])', valor
            ):
                errores.append(f'{selector.strip()}: curva prohibida')
            if propiedad == 'transition' and re.search(r'\ball\b', valor):
                errores.append(f'{selector.strip()}: transition all')
            if propiedad == 'will-change' and '[data-destacada-activa]' not in selector:
                errores.append(f'{selector.strip()}: will-change permanente')
    return errores


def test_css_solo_declaraciones_de_tiempo_en_tokens():
    for ruta in (RECURSOS / 'css').glob('*.css'):
        assert not _infracciones_css(ruta.read_text(encoding='utf-8'), ruta.name == 'tokens.css'), ruta


def test_tokens_de_duracion_en_banda():
    texto = (RECURSOS / 'css/tokens.css').read_text(encoding='utf-8')
    tokens = re.findall(r'(--dur-[\w-]+)\s*:\s*([^;]+);', texto)
    assert tokens
    for nombre, declaracion in tokens:
        assert re.fullmatch(r'\d+ms', declaracion.strip()), nombre
        valor = declaracion.strip()[:-2]
        assert (0 < float(valor) <= 120) if nombre == '--dur-reduced' else (200 <= float(valor) <= 900), nombre


def test_javascript_sin_duraciones_o_curvas_literales_en_animaciones():
    for ruta in (RECURSOS / 'js').glob('*.js'):
        texto = ruta.read_text(encoding='utf-8')
        assert not PATRON_LITERAL_JS.search(texto), ruta


def test_auditoria_detecta_regresiones():
    for css in ('a{transition: all 1s linear}', 'a{will-change: transform}', 'a{animation: x ease-in}'):
        assert _infracciones_css(css)
    for javascript in ('{duration: 180}', '{delay: 20}', "easing: 'cubic-bezier(0,0,0,1)'"):
        assert PATRON_LITERAL_JS.search(javascript)
