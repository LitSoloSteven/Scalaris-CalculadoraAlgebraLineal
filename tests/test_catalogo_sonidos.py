"""Fuente única, límites de síntesis y registro seguro del catálogo sonoro."""
import json
import re
import runpy
from pathlib import Path

import pytest

from src.frontend.componentes.sonido import _SONIDOS
from src.frontend.recursos_vistas import seleccionar_recursos
from src.frontend.tema import _CABECERA_HTML
from tests.comun import RAIZ

_RUTA = RAIZ / 'src/frontend/recursos/catalogo_sonidos.json'
_CATALOGO = json.loads(_RUTA.read_text(encoding='utf-8'))


def test_python_y_cabecera_comparten_todos_los_perfiles():
    """Ninguna copia de nombres o parámetros diverge entre servidor y navegador."""
    bloque = re.search(r'id="scalaris-configuracion-sonidos" type="application/json">(.*?)</script>', _CABECERA_HTML)
    assert bloque
    assert json.loads(bloque[1]) == _CATALOGO
    assert _SONIDOS == frozenset(_CATALOGO['perfiles'])


@pytest.mark.parametrize('nombre,perfil', _CATALOGO['perfiles'].items())
def test_perfiles_graves_breves_y_con_limites(nombre, perfil):
    """Cada timbre acota fundamentales, filtro, ganancia, ráfagas y simultaneidad."""
    assert 90 <= perfil['inicio'] <= 330, nombre
    assert 90 <= perfil['fin'] <= 330, nombre
    assert 0 < perfil['filtro'] <= 2500
    assert _CATALOGO['ataque'] < perfil['duracion'] <= _CATALOGO['duracionRuido'] <= 0.15
    assert 0 < perfil['volumen'] <= 1 and 0 <= perfil['ruido'] <= 1
    assert perfil['onda'] in ('sine', 'triangle')
    assert 0 < perfil['intervalo'] <= _CATALOGO['intervalo']
    assert 0 < perfil['limite'] <= _CATALOGO['polifonia']


def test_firmas_de_perfiles_son_unicas():
    """Las familias no son alias del mismo sonido con nombres diferentes."""
    firmas = [json.dumps(perfil, sort_keys=True) for perfil in _CATALOGO['perfiles'].values()]
    assert len(set(firmas)) == len(firmas)


def test_asignaciones_solo_referencian_perfiles_conocidos():
    """Valida reglas ordenadas, iconos, variantes y notificaciones sin saltar omisiones."""
    asignaciones = _CATALOGO['asignaciones']
    nombres = list(asignaciones['iconos'].values()) + list(asignaciones['escritura'].values())
    nombres += list(_CATALOGO['notificaciones'].values()) + [asignaciones['generico']]
    for regla in asignaciones['selectores']:
        assert regla['selector']
        for clave, valor in regla.items():
            if clave != 'selector':
                nombres.extend(valor if isinstance(valor, list) else [valor])
    assert set(nombres) - {None} <= _SONIDOS


@pytest.mark.parametrize('vista', ['inicio', 'sistemas', 'vectores', 'matrices', 'inversa',
                                 'determinantes', 'bases', 'romanos', 'visualizador', 'leontief', 'transformaciones'])
def test_orden_de_recursos_sonoros_en_cada_vista(vista):
    """Todos los consumidores reciben la configuración y dependencias una sola vez."""
    nombres = ['catalogo_sonidos', 'sintesis_sonora', 'asignacion_sonora', 'sonido',
               'preferencia_sonido', 'interacciones_sonoras', 'sonido_escritura']
    cabecera = seleccionar_recursos(_CABECERA_HTML, vista)
    posiciones = [cabecera.index(f'/assets/js/{nombre}.js') for nombre in nombres]
    assert posiciones == sorted(posiciones)
    assert cabecera.index('scalaris-configuracion-sonidos') < posiciones[0]
    assert all(cabecera.count(f'/assets/js/{nombre}.js') == 1 for nombre in nombres)


def test_inyeccion_escapa_cierre_de_script(monkeypatch):
    """Incluso un catálogo con apertura HTML permanece dentro del bloque de datos."""
    leer = Path.read_text
    datos = {**_CATALOGO, 'muestra': '</script><script>alert(1)</script>'}
    monkeypatch.setattr(Path, 'read_text', lambda ruta, **opciones:
                        json.dumps(datos) if ruta == _RUTA else leer(ruta, **opciones))
    modulo = runpy.run_path(str(RAIZ / 'src/frontend/tema.py'))
    cabecera = modulo['_CABECERA_HTML']
    assert '</script><script>alert(1)' not in cabecera
    bloque = re.search(r'id="scalaris-configuracion-sonidos" type="application/json">(.*?)</script>', cabecera)
    assert json.loads(bloque[1]) == datos
