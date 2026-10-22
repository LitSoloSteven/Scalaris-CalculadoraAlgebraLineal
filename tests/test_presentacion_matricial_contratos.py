"""Contratos de estilos estrechos, limites y nombres de las vistas matriciales."""
from pathlib import Path

from src.backend.utilidades.estado_captura import opciones_transferencia_sistema
from src.frontend.controladores.operaciones_inversas.vista_previa import preparar_presentacion_previa
from tests.comun import RAIZ


def test_disposicion_estrecha_conserva_numeros_y_dialogos():
    """El CSS permite encoger a 320 px y contiene numeros y dialogos de confirmacion."""
    css = (RAIZ / 'src/frontend/recursos/css/vistas_sesion_matricial.css').read_text(encoding='utf-8')
    assert 'width: min(100%, 24rem)' in css
    assert 'min-width: 0' in css
    assert 'overflow-wrap: anywhere;' in css
    assert 'font-variant-numeric: tabular-nums' in css
    assert '@media (max-width: 400px)' in css
    assert 'prefers-reduced-motion: reduce' in css
    for paquete in ('sistemas_lineales', 'operaciones_inversas'):
        archivos = (RAIZ / 'src/frontend/vistas' / paquete).glob('vista_*.py')
        assert any('sesion-vista' in archivo.read_text(encoding='utf-8') for archivo in archivos)


def test_destinos_transferencia_dependen_de_dimensiones_del_dominio():
    """Los sistemas vacios, rectangulares y grandes no publican destinos incompatibles."""
    assert opciones_transferencia_sistema([]) == {'inversa': False, 'visualizador': False}
    assert opciones_transferencia_sistema([['1', '2']]) == {'inversa': False, 'visualizador': True}
    assert opciones_transferencia_sistema([['1', '0'], ['0', '1']]) == {'inversa': True, 'visualizador': True}
    datos = [['0'] * 50 for indice in range(50)]
    assert preparar_presentacion_previa(datos, 50) == {'estado': 'limite', 'mensaje': 'Vista previa disponible hasta 8×8.'}


def test_paquetes_canonicos_sin_fachadas_inglesas():
    """Los nombres ingleses retirados carecen de archivo o paquete fuente."""
    raiz = RAIZ / 'src/frontend/vistas'
    for nombre in ('hub', 'linear_systems', 'inverse_ops'):
        assert not (raiz / nombre).exists()
    for paquete in ('inicio', 'sistemas_lineales', 'operaciones_inversas'):
        assert (raiz / paquete).is_dir()
        assert not list((raiz / paquete).glob('view_*.py'))
        assert not list((raiz / paquete).glob('*_mixin.py'))
