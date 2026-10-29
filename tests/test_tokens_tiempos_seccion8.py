"""Comprueba los valores de los tokens comunes de movimiento."""
import re
from pathlib import Path


def test_tokens_de_movimiento_coinciden_con_las_bandas():
    """Las duraciones y retardos se definen una vez como milisegundos literales."""
    contenido = Path('src/frontend/recursos/css/tokens.css').read_text(encoding='utf-8')
    esperados = {
        'dur-press': 200, 'dur-release': 320, 'dur-state': 350, 'dur-state-exit': 260,
        'dur-panel': 450, 'dur-panel-exit': 340, 'dur-view': 600, 'dur-view-exit': 450,
        'dur-didactic': 900, 'dur-didactic-exit': 675, 'dur-reduced': 120,
        'stagger-step': 75, 'stagger-max': 600,
    }
    for nombre, valor in esperados.items():
        declaraciones = re.findall(rf'--{re.escape(nombre)}\s*:\s*([^;]+);', contenido)
        assert declaraciones == [f'{valor}ms'], nombre
