"""Coherencia de estado, criterio, unidades y copias con los datos del motor."""
import pytest

from src.frontend.controladores.biseccion.captura_criterio import preparar_entrada, texto_condicion, texto_estimacion
from src.frontend.controladores.biseccion.controlador import resolver_captura
from src.frontend.controladores.biseccion.presentacion import construir_pasos
from src.frontend.controladores.biseccion.presentacion_criterio import metricas_resumen, texto_resumen, titulo_estado
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


@pytest.mark.parametrize("tipo,parametro,titulo", [
    ("decimales", 2, "Convergió por precisión decimal"),
    ("ancho", ".01", "Convergió por ancho absoluto"),
    ("relativo", "1", "Convergió por error relativo aproximado"),
    ("residuo", ".1", "Convergió por residuo"),
    ("iteraciones", "3", "3 iteraciones completadas"),
])
def test_estado_y_copia_indican_criterio_efectivo(tipo, parametro, titulo):
    """El encabezado y el texto copiable distinguen conteo de convergencia por tolerancia."""
    respuesta = resolver_captura(captura_criterio(tipo, parametro))
    assert titulo_estado(respuesta) == titulo
    texto = texto_resumen(respuesta, 8)
    assert texto.startswith(titulo)
    assert "Criterio solicitado:" in texto
    assert "Condición solicitada:" in texto
    assert "Umbral:" in texto
    assert "Métrica final (" in texto
    assert respuesta["unidad_criterio"] in texto


@pytest.mark.parametrize("expresion,intervalo,titulo", [
    ("x-1", (1, 2), "Cero evaluado en un extremo, sin iteraciones"),
    ("x-1.5", (1, 2), "Cero evaluado en un punto medio"),
    ("1/x", (-1, 1), "Singularidad identificada"),
    ("x**2+1", (-1, 1), "Sin cambio de signo"),
    ("sin(x)", (1e16, 1e16 + 4), "Límite de precisión"),
])
def test_estado_excepcional_prevalece_sobre_solicitud(expresion, intervalo, titulo):
    """Pedir iteraciones fijas no oculta un cero, singularidad, falta de signo o límite flotante."""
    captura = {**captura_criterio("iteraciones", 20), "expresion": expresion,
               "extremo_izquierdo": intervalo[0], "extremo_derecho": intervalo[1]}
    assert titulo_estado(resolver_captura(captura)) == titulo


def test_residuo_no_muestra_tolerancia_decimal_como_umbral():
    """La presentación usa el umbral del criterio y conserva sus unidades separadas de la cota en x."""
    respuesta = resolver_captura(captura_criterio("residuo", ".1"))
    metricas = dict(metricas_resumen(respuesta))
    assert metricas["Umbral"].endswith("unidades de f(x)")
    assert float(metricas["Umbral"].split()[0]) == respuesta["umbral"] == .1
    assert "Tolerancia E" not in metricas
    assert float(metricas["Métrica final (unidades de f(x))"]) == respuesta["metrica_final"]


def test_condicion_conserva_las_cifras_del_parametro():
    """La condición no redondea un porcentaje preciso a un umbral distinto."""
    captura = captura_criterio("relativo", "1.000000000001")
    assert "1.000000000001" in texto_condicion(captura)


@pytest.mark.parametrize("tipo", ["decimales", "iteraciones"])
def test_texto_fraccionario_no_se_acepta_por_redondeo_a_entero(tipo):
    """La conversión léxica preserva una parte fraccionaria que float perdería antes de validar."""
    with pytest.raises(ValueError, match="entero"):
        preparar_entrada(captura_criterio(tipo, "2.0000000000000000001"))


@pytest.mark.parametrize("parametro", ["0e99999999999999999999999999", "1e-100000000000000000000"])
def test_exponente_extremo_mantiene_error_controlado_en_guias_y_resolucion(parametro):
    """La excepción de Decimal se traduce sin propagarse por el formulario ni el controlador."""
    captura = captura_criterio("iteraciones", parametro)
    assert resolver_captura(captura)["estado"] == "ERROR"
    assert "entero" in texto_condicion(captura)
    assert "entero" in texto_estimacion(captura)


def test_estimacion_avisa_si_supera_limite():
    """La guía previa no promete completar una precisión fuera del presupuesto elegido."""
    captura = {**captura_criterio("decimales", 6), "limite_iteraciones": 2}
    texto = texto_estimacion(captura)
    assert "Filas previstas: 21" in texto
    assert "superan" in texto


@pytest.mark.parametrize("tipo,parametro", [("relativo", 1), ("residuo", .1), ("iteraciones", 3)])
def test_procedimiento_no_inventa_particion_al_cerrar(tipo, parametro):
    """El paso final de los nuevos criterios explica el cierre en vez de conservar otro intervalo."""
    respuesta = resolver_captura(captura_criterio(tipo, parametro))
    pasos, _ = construir_pasos(respuesta)
    assert "sin realizar otra partición" in pasos[-2].explicacion
    assert "solo el criterio elegido" in pasos[-1].explicacion


def test_formato_invalido_no_descarta_resultado_y_glosa_recibe_criterio(monkeypatch):
    """Una preferencia visual inválida se informa sin borrar el cálculo ni su contexto pedagógico."""
    async def comprobar(vista):
        """Conserva la identidad de resultado y contrasta los metadatos de Glosa."""
        vista.cargar_captura(captura_criterio("residuo", ".1"))
        await vista.resolver()
        resultado = vista.ultimo_resultado
        vista.formato.set_value(None)
        assert vista.ultimo_resultado is resultado
        assert vista.error_formato.text
        contexto = vista.obtener_contexto_ia()
        assert contexto.resultado["criterio_solicitado"] == resultado["criterio_solicitado"]
        assert contexto.resultado["unidad_criterio"] == "unidades de f(x)"
    ejecutar_escenario(monkeypatch, comprobar)
