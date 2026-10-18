"""Caracterización de idioma, comentarios y duplicación sin ejecutar código auditado."""
import ast

from tests.comun_duplicacion import duplicaciones_python
from tests.comun_idioma import declaraciones_propias, ingles_propio
from tests.comun_transversal import analizar_fuentes_cliente


def _fuente_cliente(codigo, ruta='muestra.js'):
    return {'ruta': ruta, 'contenido': codigo, 'origen': 'archivo', 'linea': 1}


def test_detector_reconoce_locales_y_parametros_ingleses():
    """Incluye nombres propios ordinarios que no contienen solver ni matrix."""
    arbol = ast.parse('def procesar(payload):\n status = payload\n self.fingerprint = status')
    conflictos = {nombre for nombre, _ in declaraciones_propias(arbol) if ingles_propio(nombre, 'muestra.py')}
    assert conflictos == {'payload', 'status', 'fingerprint'}


def test_detector_reconoce_abreviaturas_ajenas_y_cripticas():
    """Las abreviaturas propias no se confunden con nombres impuestos por bibliotecas."""
    nombres = {'a_fmt', 'grupo_idx', 'p_val', 'mat_aug', 'temp', 'chip', 'MSJ_SECRETO_DEV_INSEGURO'}
    assert all(ingles_propio(nombre, 'muestra.py') for nombre in nombres)


def test_contratos_externos_no_exoneran_nombres_propios_parecidos():
    """La excepción de rutas no permite usar method en cualquier módulo."""
    assert not ingles_propio('method', 'src/frontend/rutas.py')
    assert ingles_propio('method', 'src/frontend/controladores/ejemplo.py') == {'method'}
    arbol = ast.parse('self.text = "interno"\nself.etiqueta_error.text = "externo"')
    assert list(declaraciones_propias(arbol)) == [('text', 1)]


def test_detector_encuentra_cinco_lineas_con_locales_renombrados():
    """Los cambios de nombre no ocultan una segunda aparición de la misma lógica."""
    primera = 'def uno(datos):\n valor = datos[0]\n doble = valor*2\n valor = doble+1\n doble = valor-1\n return doble'
    segunda = primera.replace('uno', 'dos').replace('valor', 'elemento').replace('doble', 'resultado')
    fuentes = {'primero.py': primera, 'segundo.py': segunda}
    assert duplicaciones_python(fuentes) == [[('primero.py', 2, 6), ('segundo.py', 2, 6)]]
    assert fuentes == {'primero.py': primera, 'segundo.py': segunda}


def test_detector_conserva_constantes_y_atributos():
    """Cambiar un límite o la propiedad consultada evita una equivalencia falsa."""
    primera = 'def uno(datos):\n valor = datos.texto\n doble = valor*2\n valor = doble+1\n doble = valor-1\n return doble'
    assert not duplicaciones_python({'a.py': primera, 'b.py': primera.replace('*2', '*3')})
    assert not duplicaciones_python({'a.py': primera, 'b.py': primera.replace('.texto', '.valor')})


def test_detector_no_confunde_booleano_con_entero():
    """Los valores verdadero y 1 no son la misma constante del lenguaje."""
    primera = 'def uno(datos):\n valor = True\n datos.append(valor)\n datos.append(0)\n datos.append(2)\n return datos'
    assert not duplicaciones_python({'a.py': primera, 'b.py': primera.replace('True', '1')})


def test_campos_de_contrato_sin_valor_no_son_logica_copiada():
    """Las declaraciones de tipos con campos diferentes no simulan un bloque ejecutable."""
    codigo = 'class Datos:\n primero: str\n segundo: str\n tercero: str\n cuarto: str\n quinto: str\n sexto: str'
    assert not duplicaciones_python({'datos.py': codigo})


def test_analizador_cliente_incluye_desestructuracion_y_capturas():
    """Incluye funciones, parámetros, variables y excepciones de JavaScript."""
    codigo = 'function procesar({payload}) { try { const [status] = payload; } catch(error) {} }'
    analisis = analizar_fuentes_cliente([_fuente_cliente(codigo)])
    nombres = {dato['nombre'] for dato in analisis['resultados'][0]['nombres']}
    assert nombres == {'procesar', 'payload', 'status', 'error'}


def test_analizador_cliente_detecta_duplicados_y_comentarios_reales():
    """Una cadena con aspecto de comentario no se confunde con comentario de código."""
    codigo = '// Motivo real\nconst cadena="// TODO: dato";\nfunction uno(){\n const valor=1;\n console.log(valor);\n console.log(2);\n console.log(3);\n return valor;\n}'
    analisis = analizar_fuentes_cliente([_fuente_cliente(codigo), _fuente_cliente(codigo, 'otra.js')])
    assert analisis['duplicaciones']
    assert [comentario['value'] for comentario in analisis['resultados'][0]['comentarios']] == [' Motivo real']
