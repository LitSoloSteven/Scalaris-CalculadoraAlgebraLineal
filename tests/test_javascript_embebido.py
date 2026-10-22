"""Cobertura de los cuerpos ejecutables auditados junto a los recursos cliente."""
from tests.comun import analizar_fuentes_javascript
from tests.comun_javascript_embebido import LectorCodigoHTML, fuentes_javascript


def test_html_conserva_codigo_cliente_clasicos_modulos_y_lineas():
    """Los código cliente externos y bloques de datos no duplican cuerpos ejecutables."""
    lector = LectorCodigoHTML()
    lector.feed('<p>Inicio</p>\n<script>function elegir() {}\n</script>\n'
                '<script type="module">const recibir = () => 1;</script>'
                '<script src="recurso.js"></script>'
                '<script type="application/json">{"dato":1}</script>')
    assert lector.fragmentos == [(2, "function elegir() {}\n"),
                                 (4, "const recibir = () => 1;")]


def test_html_no_interpreta_entidades_como_codigo():
    """El cuerpo conserva la sintaxis literal y permite fragmentación del lector."""
    lector = LectorCodigoHTML()
    lector.feed('<script>const comparar = () => "&amp;";')
    lector.feed('</script><script></script>')
    assert lector.fragmentos == [(1, 'const comparar = () => "&amp;";'), (1, "")]


def test_descubrimiento_incluye_python_pruebas_sin_leer_expectativas(tmp_path, monkeypatch):
    """Los emisores reales se miden, las cadenas de expectativas son datos."""
    monkeypatch.setattr("tests.comun_javascript_embebido.RAIZ", tmp_path)
    ruta = tmp_path / "tests/ejemplo.py"
    ruta.parent.mkdir()
    ruta.write_text('codigo = "setTimeout(() => { if (activo) actuar(); }, 1);"\n'
                    'cliente.run_javascript(codigo)\n'
                    'assert "window.funcionFicticia(" not in esperado\n', encoding="utf-8")
    fuentes = fuentes_javascript([ruta])
    assert len(fuentes) == 1
    assert fuentes[0]["contenido"].startswith("setTimeout")
    assert fuentes[0]["origen"] == "python"
    assert fuentes[0]["ruta"] == "tests/ejemplo.py"


def test_retorno_nicegui_no_agrega_funcion_sintetica():
    """El envoltorio externo de NiceGUI no altera las medidas de los manejadores."""
    fuente = {"ruta": "vista.py", "linea": 25, "origen": "python",
              "contenido": "return (() => { if (activo) return 1; return 0; })();"}
    medida = analizar_fuentes_javascript([fuente])[0]
    assert medida["linea"] == 25
    assert len(medida["funciones"]) == 1
    assert medida["funciones"][0]["complejidad"] == 2


def test_html_embebido_mide_iife_y_manejador_sin_exoneraciones():
    """Una IIFE extensa conserva sus líneas físicas y las firmas interiores."""
    cuerpo = "(() => {\n" + "void 1;\n" * 41 + "})();"
    fuente = {"ruta": "vista.html", "linea": 8, "origen": "html", "contenido": cuerpo}
    medida = analizar_fuentes_javascript([fuente])[0]
    assert medida["funciones"][0]["lineas"] == 43
    assert medida["funciones"][0]["lineas"] > 40


def test_cadena_indirecta_y_ramas_interpoladas_se_miden(tmp_path, monkeypatch):
    """Una variable intermedia o una alternativa de código no oculta funciones."""
    monkeypatch.setattr("tests.comun_javascript_embebido.RAIZ", tmp_path)
    ruta = tmp_path / "vista.py"
    ruta.write_text('comando = "(() => { if (activo) actuar(); })();" if teclado else "(() => actuar())();"\n'
                    'codigo = f"if (visible) {comando}"\n'
                    'enviado = codigo\nui.run_javascript(enviado)\n', encoding="utf-8")
    medidas = analizar_fuentes_javascript(fuentes_javascript([ruta]))
    funciones = [funcion for medida in medidas for funcion in medida["funciones"]]
    assert sorted(funcion["complejidad"] for funcion in funciones) == [1, 2]


def test_interpolacion_indirecta_conserva_firmas_y_complejidad(tmp_path, monkeypatch):
    """Las cadenas estáticas transitivas conservan funciones fuera de límite."""
    monkeypatch.setattr("tests.comun_javascript_embebido.RAIZ", tmp_path)
    ruta = tmp_path / "vista.py"
    comando = "window.f = function omitida(a,b,c,d,e,f) {" + "if (activo) actuar();" * 10 + "};"
    ruta.write_text(f'comando = {comando!r}\ncodigo = f"{{comando}}"\n'
                    'ui.run_javascript(f"{codigo}")\n', encoding="utf-8")
    funcion = analizar_fuentes_javascript(fuentes_javascript([ruta]))[0]["funciones"][0]
    assert funcion["parametros"] == 6
    assert funcion["complejidad"] == 11


def test_dato_condicional_no_textual_no_elimina_manejador(tmp_path, monkeypatch):
    """Un dato desconocido mantiene las declaraciones estáticas que lo rodean."""
    monkeypatch.setattr("tests.comun_javascript_embebido.RAIZ", tmp_path)
    ruta = tmp_path / "vista.py"
    ruta.write_text('valor = 1 if activo else 2\n'
                    'ui.run_javascript(f"((a,b,c,d,e,f) => {{ if (activo) actuar(); }})(); void {valor};")\n',
                    encoding="utf-8")
    funcion = analizar_fuentes_javascript(fuentes_javascript([ruta]))[0]["funciones"][0]
    assert funcion["parametros"] == 6
    assert funcion["complejidad"] == 2


def test_anotaciones_concatenacion_y_argumento_explicito(tmp_path, monkeypatch):
    """Las firmas anotadas y las llamadas por nombre no omiten fuentes cliente."""
    monkeypatch.setattr("tests.comun_javascript_embebido.RAIZ", tmp_path)
    ruta = tmp_path / "vista.py"
    ruta.write_text('comando: str = "function recibir(a,b,c,d,e,f) {}"\n'
                    'ui.run_javascript(code="" + comando)\n', encoding="utf-8")
    funcion = analizar_fuentes_javascript(fuentes_javascript([ruta]))[0]["funciones"][0]
    assert funcion["nombre"] == "recibir"
    assert funcion["parametros"] == 6


def test_codigo_cliente_html_emitidos_por_python_se_miden(tmp_path, monkeypatch):
    """Cabecera, cuerpo y HTML renderizado conservan código cliente embebidos ejecutables."""
    monkeypatch.setattr("tests.comun_javascript_embebido.RAIZ", tmp_path)
    ruta = tmp_path / "vista.py"
    ruta.write_text('ui.add_head_html("<script type>function cabecera() {}</script>")\n'
                    'ui.add_body_html("<script>function cuerpo() {}</script>")\n'
                    'ui.html("<script>function elemento() {}</script>")\n', encoding="utf-8")
    medidas = analizar_fuentes_javascript(fuentes_javascript([ruta]))
    assert [medida["funciones"][0]["nombre"] for medida in medidas] == ["cabecera", "cuerpo", "elemento"]


def test_ambitos_independientes_y_ciclos_no_contaminan_cadenas(tmp_path, monkeypatch):
    """Los nombres locales conservan su origen y los ciclos terminan sin evaluar."""
    monkeypatch.setattr("tests.comun_javascript_embebido.RAIZ", tmp_path)
    ruta = tmp_path / "vista.py"
    ruta.write_text('def primero():\n codigo = "function primero() {}"\n ui.run_javascript(codigo)\n'
                    'def segundo():\n codigo = "function segundo() {}"\n ui.run_javascript(f"{codigo}")\n'
                    'def ciclo():\n uno = dos\n dos = uno\n ui.run_javascript(f"void {uno}")\n', encoding="utf-8")
    medidas = analizar_fuentes_javascript(fuentes_javascript([ruta]))
    assert [funcion["nombre"] for medida in medidas for funcion in medida["funciones"]] == ["primero", "segundo"]
    assert len(medidas) == 3
