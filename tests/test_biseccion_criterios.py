"""Comportamiento de los cinco criterios y prioridad de las salidas excepcionales."""
import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada


def _resolver(criterio, expresion="x**2-2", intervalo=(1, 2), limite=100, decimales=4):
    return biseccion(EntradaBiseccion(expresion, *intervalo, decimales, limite,
                                    criterio=CriterioParada(*criterio)))


@pytest.mark.parametrize("criterio,filas,estado", [
    (("relativo", 1), 7, "EXITO"), (("ancho", .01), 8, "EXITO"),
    (("decimales", 2), 8, "EXITO"), (("residuo", .1), 4, "EXITO"),
    (("iteraciones", 3), 3, "ITERACIONES_COMPLETADAS"),
])
def test_cada_criterio_cierra_en_su_primera_fila(criterio, filas, estado):
    """La aproximación, el intervalo y las métricas pertenecen a la última fila evaluada."""
    resultado = _resolver(criterio)
    ultima = resultado.iteraciones[-1]
    assert len(resultado.iteraciones) == filas
    assert resultado.estado == estado
    assert resultado.aproximacion == ultima.c
    assert resultado.intervalo_final == (ultima.extremo_izquierdo, ultima.extremo_derecho)
    assert resultado.metricas["residuo_final"] == ultima.residuo
    assert resultado.criterio_solicitado == CriterioParada(*criterio)
    assert resultado.umbral == float(resultado.criterio_solicitado.umbral)


@pytest.mark.parametrize("criterio,filas", [
    (("relativo", 1), 7), (("residuo", .1), 4), (("iteraciones", 10), 10),
])
def test_el_ancho_decimal_inactivo_no_adelanta_la_parada(criterio, filas):
    """Un d visual permisivo no se combina mediante OR con el criterio elegido."""
    resultado = _resolver(criterio, decimales=0)
    assert len(resultado.iteraciones) == filas
    assert resultado.iteraciones[1].ancho < resultado.error_absoluto


@pytest.mark.parametrize("criterio,filas", [
    (("ancho", .125), 5), (("residuo", .25), 3), (("relativo", 20), 3),
])
def test_igualdad_con_el_umbral_no_satisface_la_condicion(criterio, filas):
    """Una métrica igual al umbral requiere continuar antes de cumplir la desigualdad estricta."""
    assert len(_resolver(criterio).iteraciones) == filas


def test_el_porcentaje_redondeado_no_decide_la_parada():
    """Una cifra mostrada como .55 por ciento aún puede superar un umbral de .552."""
    resultado = _resolver(("relativo", .552))
    penultima = resultado.iteraciones[-2]
    assert len(resultado.iteraciones) == 8
    assert penultima.error_relativo == "0.55%"
    assert penultima.error_relativo_valor > .552
    assert resultado.metrica_final < .552


@pytest.mark.parametrize("intervalo,expresion", [((1, 2), "x**2-2"), ((-1, 1), "x-.2")])
def test_relativo_indefinido_no_se_convierte_en_cero(intervalo, expresion):
    """La primera fila y el punto medio cero carecen de porcentaje aunque el umbral sea amplio."""
    resultado = _resolver(("relativo", 1000), expresion, intervalo)
    assert resultado.iteraciones[0].error_relativo_valor is None
    assert len(resultado.iteraciones) == 2


@pytest.mark.parametrize("expresion,filas", [("x-1", 0), ("x-1.5", 1)])
def test_cero_evaluado_termina_antes_del_numero_fijo(expresion, filas):
    """Los ceros de extremos y medios conservan su motivo aproximado y prevalecen sobre n."""
    resultado = _resolver(("iteraciones", 20), expresion)
    assert len(resultado.iteraciones) == filas
    assert resultado.estado == "EXITO"
    assert resultado.codigo_diagnostico == "CERO_EVALUADO"
    assert "no certifica exactitud simbólica" in resultado.mensaje
    assert resultado.metrica_final == filas


def test_conteo_fijo_completado_no_es_convergencia_por_tolerancia():
    """Completar n en el límite de seguridad sigue siendo un cierre ordinario de conteo."""
    resultado = _resolver(("iteraciones", 2), limite=2)
    assert resultado.estado == "ITERACIONES_COMPLETADAS"
    assert resultado.motivo_parada == "iteraciones_completadas"
    assert resultado.metrica_final == 2
    assert resultado.iteraciones[-1].ancho > resultado.error_absoluto


def test_estancamiento_prevalece_sobre_conteo_fijo():
    """Un medio sin avance detiene la ejecución antes de consumir las filas solicitadas."""
    resultado = _resolver(("iteraciones", 20), "sin(x)", (1e16, 1e16 + 4))
    assert resultado.estado == "PRECISION_NO_ALCANZADA"
    assert resultado.motivo_parada == "estancamiento"
    assert len(resultado.iteraciones) == 2


def test_relativo_cerca_de_cero_no_cambia_automaticamente_a_ancho():
    """Acercarse a cero puede agotar el límite aunque el intervalo absoluto sea diminuto."""
    resultado = _resolver(("relativo", 1), "x", (-1, 2))
    assert resultado.motivo_parada == "limite_iteraciones"
    assert len(resultado.iteraciones) == 100
    assert resultado.criterio_solicitado.tipo == "relativo"
    assert resultado.metrica_final >= 1


def test_signos_de_funcion_pequena_no_dependen_del_producto():
    """Las evaluaciones opuestas subnormales para un producto conservan el encierro válido."""
    resultado = _resolver(("ancho", .01), "1e-200*(x-1)", (0, 3))
    assert resultado.estado == "EXITO"
    assert resultado.iteraciones[-1].ancho < .01
    assert resultado.intervalo_final[0] <= 1 <= resultado.intervalo_final[1]


def test_error_de_evaluacion_conserva_el_criterio_solicitado():
    """El criterio y su unidad siguen disponibles cuando una evaluación impide iterar."""
    resultado = _resolver(("residuo", .01), "1/sin(x)", (-1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.aproximacion is None
    assert resultado.criterio_solicitado == CriterioParada("residuo", .01)
    assert resultado.unidad_criterio == "unidades de f(x)"


def test_decimal_explicito_y_captura_antigua_coinciden():
    """El contrato antiguo conserva su secuencia, motivo y tolerancia exacta."""
    antiguo = biseccion(EntradaBiseccion("x**2-2", 1, 2, 2))
    explicito = _resolver(("decimales", 2))
    assert antiguo.iteraciones == explicito.iteraciones
    assert antiguo.motivo_parada == explicito.motivo_parada == "ancho_menor_que_E"
    assert antiguo.error_absoluto == explicito.error_absoluto
