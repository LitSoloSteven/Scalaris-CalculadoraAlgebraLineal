"""Pruebas del catálogo, las etiquetas y las tablas del reproductor compartido."""

from pathlib import Path
from fractions import Fraction
from types import SimpleNamespace
from tests.comun_renderizado import capturar_renderizado_latex

from src.backend.modelos.matriz import Matriz
from src.frontend.componentes.reproductor_pasos import (
    CATALOGO_TIPOS,
    VELOCIDADES_AUTOREPRODUCCION,
    GrupoReproductor,
    PasoReproductor,
    ReproductorPasos,
    etiqueta_variable_html,
    html_tabla_aumentada,
)
from src.frontend.componentes.reproductor_pasos import reproductor as modulo_reproductor
from src.frontend.controladores.operaciones_inversas import (
    ControladorOperacionesInversas,
)
from src.frontend.vistas.operaciones_inversas._adaptador_pasos import (
    adaptar_pasos_inversa,
)


class _ControlPrueba:
    """Control mínimo para probar la actualización del reproductor sin UI real."""

    def __init__(self, valor=None):
        """Inicializa el valor y el contador de limpiezas del control."""
        self.value = valor
        self.limpiezas = 0

    def set_text(self, texto):
        """Guarda el texto asignado por el reproductor."""
        self.texto = texto

    def set_content(self, contenido):
        """Guarda el contenido asignado por el reproductor."""
        self.contenido = contenido

    def set_value(self, valor):
        """Guarda el valor de progreso asignado por el reproductor."""
        self.value = valor

    def clear(self):
        """Cuenta las limpiezas del contenedor de cuerpo o de Glosa."""
        self.limpiezas += 1


def _crear_reproductor_prueba():
    """Crea un reproductor mínimo con controles falsos para probar navegación."""
    pasos = (
        PasoReproductor(0, "inicial", "Inicio", "Explicación inicial", 0),
        PasoReproductor(1, "final", "Resultado", "Explicación final", 1),
    )
    reproductor = ReproductorPasos.__new__(ReproductorPasos)
    reproductor.pasos = pasos
    reproductor.grupos = (
        GrupoReproductor("Inicio", "", "inicial", (0,)),
        GrupoReproductor("Final", "", "final", (1,)),
    )
    reproductor.indice_actual = 0
    reproductor.tarjeta = SimpleNamespace(is_deleted=False)
    reproductor.etiqueta_indice = _ControlPrueba()
    reproductor.etiqueta_tipo = _ControlPrueba()
    reproductor.fase = _ControlPrueba()
    reproductor.progreso = _ControlPrueba()
    reproductor.deslizador = _ControlPrueba(0)
    reproductor.explicacion = _ControlPrueba()
    reproductor.contenedor_glosa = _ControlPrueba()
    reproductor.contenedor_cuerpo = _ControlPrueba()
    reproductor.al_explicar = None
    reproductor.id_tarjeta = "pasos-tarjeta-prueba"
    pintados = []
    reproductor.renderizar_cuerpo = lambda paso, contenedor: pintados.append(
        (paso.indice, contenedor.limpiezas)
    )
    return reproductor, pintados


def test_etiqueta_variable_html_convierte_subindices_y_escapa_texto():
    """Convierte nombres con subíndice y escapa etiquetas HTML arbitrarias."""
    assert etiqueta_variable_html("x1") == "x<sub>1</sub>"
    assert etiqueta_variable_html("x_1") == "x<sub>1</sub>"
    assert etiqueta_variable_html("c_2") == "c<sub>2</sub>"
    assert etiqueta_variable_html("alpha") == "alpha"
    assert etiqueta_variable_html("<b>") == "&lt;b&gt;"


def test_tabla_aumentada_admite_bloque_derecho_de_una_columna():
    """Genera etiquetas separadas y un ancho derecho distinto al izquierdo."""
    matriz = Matriz(2, 3, [[1, 2, 5], [3, 4, 6]])
    esperado = (
        '<div class="inversa-desplazamiento"><table class="inversa-tabla"><thead><tr>'
        "<th class='fila-etiqueta'></th><th>x<sub>1</sub></th><th>x<sub>2</sub></th>"
        "<th class='separador-izquierdo'>b</th></tr></thead><tbody>"
        "<tr><th class='fila-etiqueta'>F1</th><td>1</td><td>2</td><td class=\"separador-izquierdo\">5</td></tr>"
        "<tr><th class='fila-etiqueta'>F2</th><td>3</td><td>4</td><td class=\"separador-izquierdo\">6</td></tr>"
        "</tbody></table></div>"
    )
    assert html_tabla_aumentada(matriz, 2, opciones={'etiquetas_izquierda': ("x1", "x_2"), 'etiquetas_derecha': ("b",)}) == esperado


def test_catalogo_y_hoja_nueva_definen_todos_los_tipos():
    """Comprueba que cada tipo disponible tenga estilo declarado."""
    ruta_css = Path("src/frontend/recursos/css/reproductor_pasos.css")
    estilos = ruta_css.read_text(encoding="utf-8")
    tipos_esperados = {
        "inicial", "intercambio", "pivote", "eliminacion", "normalizacion", "otro", "final",
        "planteamiento", "sustitucion", "verificacion", "operacion", "componente", "ajuste",
        "expansion", "division", "lectura", "decodificacion", "construccion", "resultado",
    }
    assert set(CATALOGO_TIPOS) == tipos_esperados
    assert all(f".pasos-etiqueta-{tipo}" in estilos for tipo in tipos_esperados)


def test_recursos_compartidos_se_enlazan_y_destello_deja_el_script_anterior():
    """Confirma la carga global de recursos y la eliminación del nombre antiguo."""
    cabecera = Path("src/frontend/recursos/plantillas/cabecera.html").read_text(encoding="utf-8")
    codigo_cliente = Path("src/frontend/recursos/js/reproductor_pasos.js").read_text(encoding="utf-8")
    codigo_matriz = Path("src/frontend/recursos/js/matriz_cuadrada.js").read_text(encoding="utf-8")
    assert "/assets/css/reproductor_pasos.css" in cabecera
    assert "/assets/js/reproductor_pasos.js" in cabecera
    assert "window.scalaris.pasos =" in codigo_cliente
    assert "revelar: function" in codigo_cliente or "revelar(id" in codigo_cliente
    assert "destellar: function" in codigo_cliente or "destellar(id" in codigo_cliente
    assert "flashStepCard" not in codigo_matriz


def test_velocidades_y_renderizado_latex_conservan_contrato(monkeypatch):
    """Comprueba los intervalos fijos y la composición segura de bloques MathJax."""
    html_renderizado, llamadas_javascript = capturar_renderizado_latex(monkeypatch, "x < 1")
    assert VELOCIDADES_AUTOREPRODUCCION == {"Lenta": 1.2, "Normal": 0.6, "Rápida": 0.2}
    assert len(html_renderizado) == 1
    assert 'class="matematicas-desplazamiento matematicas-etiqueta"' in html_renderizado[0]
    assert "$$ x &lt; 1 $$" in html_renderizado[0]
    assert len(llamadas_javascript) == 1
    assert "window.scalaris.renderizarMathJax" in llamadas_javascript[0]


def test_adaptador_inversa_preserva_grupos_datos_y_paso_final():
    """Verifica que el adaptador conserva referencias y metadatos de Glosa."""
    resultado = ControladorOperacionesInversas.procesar_inversa('{"dimension":2,"datos":[[1,2],[3,4]]}')
    pasos, grupos = adaptar_pasos_inversa(resultado)
    assert isinstance(pasos[0], PasoReproductor)
    assert isinstance(grupos[0], GrupoReproductor)
    assert pasos[-1].tipo == "final"
    assert pasos[-1].cuerpo.paso is resultado["pasos"][-1]
    assert pasos[-1].meta_explicar == {
        "tipo": resultado["pasos"][-1]["tipo"],
        "operacion": resultado["pasos"][-1]["descripcion"],
    }
    assert grupos[1].indices_pasos == (1, 2, 3)


def test_detener_elimina_temporizador_y_restaura_el_control():
    """Cancela el temporizador de una instancia sin depender de un cliente UI."""
    class TemporizadorPrueba:
        """Representa el temporizador del reproductor."""
        def __init__(self):
            self.is_deleted = False
            self.active = True

        def delete(self):
            """Retira el recurso simulado y registra su cierre."""
            self.is_deleted = True

    reproductor = ReproductorPasos.__new__(ReproductorPasos)
    reproductor.temporizador = TemporizadorPrueba()
    reproductor.boton_reproducir = SimpleNamespace(
        is_deleted=False, props=lambda valor: setattr(reproductor, "icono", valor)
    )
    temporizador = reproductor.temporizador
    reproductor.detener()
    assert temporizador.is_deleted
    assert not temporizador.active
    assert reproductor.temporizador is None
    assert reproductor.icono == "icon=play_arrow"


def test_tabla_aumentada_de_50_por_50_usa_formato_compacto():
    """Verifica una tabla aumentada de dimensión máxima y valores fraccionarios."""
    datos = [
        [Fraction(1, 2) if columna % 2 else fila + 1 for columna in range(100)]
        for fila in range(50)
    ]
    tabla = html_tabla_aumentada(Matriz(50, 100, datos), 50)
    assert 'class="inversa-tabla compacta"' in tabla
    assert 'class="inversa-fraccion"' not in tabla
    assert tabla.count("<tr") == 51


def test_ir_a_actualiza_el_estado_y_limpia_el_cuerpo(monkeypatch):
    """Comprueba la navegación acotada y el contrato de renderizado del cuerpo."""
    reproductor, pintados = _crear_reproductor_prueba()
    javascript = []
    monkeypatch.setattr(modulo_reproductor.ui, "run_javascript", javascript.append)
    reproductor.ir_a(20)
    assert reproductor.indice_actual == 1
    assert reproductor.etiqueta_indice.texto == "Paso 2 de 2"
    assert reproductor.fase.texto == "Final"
    assert reproductor.progreso.value == 1
    assert reproductor.deslizador.value == 1
    assert pintados == [(1, 1)]
    assert len(javascript) == 2
