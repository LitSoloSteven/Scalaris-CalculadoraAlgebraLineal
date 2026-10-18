"""Contraste WCAG de texto, estados y foco en los tres temas."""
import pytest
from tests.comun_estilos import analizar_tokens, hexadecimal_a_rgb, razon_contraste

RUTA_CSS = 'src/frontend/recursos/css/tokens.css'

PARES = [
    ('text-main', 'bg-page', 4.5),
    ('text-main', 'bg-panel', 4.5),
    ('text-main', 'bg-elevated', 4.5),
    ('text-main', 'input-bg', 4.5),
    ('text-sec', 'bg-page', 4.5),
    ('text-sec', 'bg-panel', 4.5),
    ('text-sec', 'bg-elevated', 4.5),
    ('text-sec', 'input-bg', 4.5),
    ('text-placeholder', 'input-bg', 4.5),
    ('accent', 'bg-page', 4.5),
    ('accent', 'bg-panel', 4.5),
    ('accent', 'bg-elevated', 4.5),
    ('accent', 'accent-soft', 4.5),
    ('btn-primary-text', 'btn-primary-bg', 4.5),
    ('badge-err-text', 'badge-err-bg', 4.5),
    ('badge-suc-text', 'badge-suc-bg', 4.5),
    ('badge-warn-text', 'badge-warn-bg', 4.5),
    ('error', 'bg-panel', 3.0),
    ('success', 'bg-panel', 3.0),
    ('warning', 'bg-panel', 3.0),
    ('focus-ring', 'bg-page', 3.0),
]

TEMAS = ['papel', 'marea', 'medianoche']

@pytest.mark.parametrize('nombre_tema', TEMAS)
@pytest.mark.parametrize('frente,fondo,umbral', PARES)
def test_contraste_texto_estados_y_foco(nombre_tema, frente, fondo, umbral):
    """Cada par conserva su umbral WCAG en cada tema."""
    temas = analizar_tokens(RUTA_CSS, pasadas=1, exigir_cierre=False)
    t = temas[nombre_tema]
    hexadecimal_frente = t.get(f'--{frente}')
    hexadecimal_fondo = t.get(f'--{fondo}')
    assert hexadecimal_frente, f"Token --{frente} no encontrado en tema {nombre_tema}"
    assert hexadecimal_fondo, f"Token --{fondo} no encontrado en tema {nombre_tema}"

    rgb_frente = hexadecimal_a_rgb(hexadecimal_frente, limpiar_espacios=False)
    rgb_fondo = hexadecimal_a_rgb(hexadecimal_fondo, limpiar_espacios=False)
    contraste = razon_contraste(rgb_frente, rgb_fondo)
    assert contraste >= umbral, (
        f"Contraste insuficiente en {nombre_tema}: {frente} ({hexadecimal_frente}) sobre {fondo} ({hexadecimal_fondo}) = "
        f"{contraste:.2f}:1 (requerido >= {umbral}:1)"
    )
