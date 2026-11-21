"""Integración, derivación y presentación de integrales en los métodos numéricos."""

import math

import pytest

from src.backend.excepciones import ErrorDominio
from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.errores_numericos import ErrorCapacidadNumerica, ErrorSingularidad
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar_constante_real
from src.backend.resolutores.raices.metodos_abiertos import EntradaMetodoAbierto, newton
from src.backend.resolutores.raices.metodos_abiertos.derivada_simbolica import derivar_expresion
from src.frontend.controladores.formato_funcion_real import formatear_expresion


@pytest.mark.parametrize(("expresion", "esperado"), [
    ("∫(t²,t,0,x)", 8 / 3),
    ("∫(t²,t,x,0)", -8 / 3),
    ("∫(1÷0,t,x,x)", 0),
    ("2∫(t,t,0,x)", 4),
    ("∫(1/√(t),t,0,1)", 2),
    ("∫(1/√(1−t),t,0,1)", 2),
    ("∫(ln(t),t,0,1)", -1),
    ("∫(1/√(abs(t)),t,−1,1)", 4),
    ("∫(1e-308,t,−1e308,1e308)", 2),
    ("∫(exp(−t),t,0,+∞)", 1),
    ("∫(exp(t),t,−∞,0)", 1),
    ("∫(exp(−t)/√(t),t,0,∞)", math.sqrt(math.pi)),
    ("∫(exp(−t²),t,−1e8,∞)", math.sqrt(math.pi)),
    ("∫(exp(−t²),t,−∞,1e8)", math.sqrt(math.pi)),
    ("∫(exp(−t²),t,∞,−∞)", -math.sqrt(math.pi)),
    ("∫(1/(1+t²),t,−∞,∞)", math.pi),
    ("∫(t×∫(t,t,0,t),t,0,x)", 2),
    ("∑(i,1,2,∫(i,i,0,i))", 2.5),
    ("∫(∑(i,1,2,i×t),t,0,x)", 6),
])
def test_evalua_integrales_orientadas(expresion, esperado):
    """Cubre singularidades integrables, ambos infinitos y alcance local."""
    assert compilar(expresion)(2) == pytest.approx(esperado, rel=1e-9, abs=1e-11)


@pytest.mark.parametrize("expresion", [
    "∞", "∞+1", "∫(∞,t,0,1)", "∫(t,t,0,∞−1)", "∫(t,t,∞,+∞)",
    "∫(t,t,0,t)", "∫(t,t,0)", "∫(t,x,0,1)", "∫(t,e,0,1)", "∫(t,t²,0,1)",
    "∫(f(t),t,0,1)", "∫(t,t,0,1)+t",
])
def test_rechaza_sintaxis_y_variables_fuera_de_alcance(expresion):
    """Solo permite infinito como límite y exige una variable local válida."""
    with pytest.raises(ValueError):
        compilar(expresion)


def test_perfil_real_rechaza_ambos_simbolos():
    """La gramática para extremos y valores iniciales sigue admitiendo solo constantes."""
    for expresion in ("∫(t,t,0,1)", "∞"):
        with pytest.raises(ValueError):
            evaluar_constante_real(expresion)


@pytest.mark.parametrize("expresion", [
    "∫(1,t,0,∞)", "∫(1/t,t,−1,1)", "∫(1/(t−0.1),t,−1,1)", "∫(t/(1+t²),t,−∞,∞)",
    "∫(1e-80,t,0,∞)", "∫(1e-80/t,t,−1,1)",
])
def test_rechaza_divergencia_sin_cancelar_lados(expresion):
    """El valor principal por simetría no se acepta como integral convergente."""
    with pytest.raises((ErrorCapacidadNumerica, ErrorDominio)):
        compilar(expresion)(0)


def test_presupuesto_es_compartido_y_se_reinicia_en_cada_evaluacion():
    """Varias evaluaciones cortas funcionan y las integrales anidadas agotan el presupuesto común."""
    funcion = compilar("∫(∫(∫(1,r,0,s),s,0,t),t,0,x)")
    with pytest.raises(ErrorCapacidadNumerica) as error:
        funcion(1)
    assert error.value.codigo == "INTEGRAL_PRESUPUESTO_AGOTADO"
    assert funcion(0) == 0


def test_cola_no_acepta_un_integrando_constante_redondeado_a_cero():
    """Un subdesbordamiento dependiente de x no demuestra decaimiento de la cola."""
    with pytest.raises(ErrorCapacidadNumerica) as error:
        compilar("∫(exp(−x),t,0,∞)")(1000)
    assert error.value.codigo == "SUBDESBORDAMIENTO"


@pytest.mark.parametrize(("expresion", "esperado"), [
    ("∫(x×t,t,x,x²)", 34),
    ("∫(t,t,x,0)", -2),
    ("∫(exp(−t)×x,t,x,∞)", -math.exp(-2)),
    ("∫(x×exp(−t²),t,−∞,∞)", math.sqrt(math.pi)),
    ("∫(∫(t+u,u,0,1),t,0,x)", 2.5),
    ("(∫(t²,t,0,x))′", 4),
])
def test_deriva_por_leibniz(expresion, esperado):
    """Los límites móviles y la derivada parcial contribuyen a f'(x)."""
    assert compilar(derivar_expresion(expresion))(2) == pytest.approx(esperado, rel=1e-9)


def test_derivada_conserva_el_dominio_de_la_integral_original():
    """Una integral divergente no adquiere dominio por simplificación simbólica."""
    with pytest.raises(ErrorCapacidadNumerica):
        compilar(derivar_expresion("x+∫(1,t,0,∞)"))(2)


def test_primas_conservan_la_unidad_angular():
    """En grados, derivar la integral conserva el factor de conversión en su integrando."""
    expresion = "(∫(sin(x)×t,t,0,2))′"
    assert compilar(expresion, unidad_angular="grados")(60) == pytest.approx(math.pi / 180)


@pytest.mark.parametrize("expresion", ["sin(∫(90°,t,0,1))", "sin(∫(90,t,0,180°/π))"])
def test_unidad_explicita_de_integral_proviene_del_integrando(expresion):
    """Los grados del integrando afectan al resultado y los del límite solo al intervalo."""
    assert compilar(expresion, unidad_angular="grados")(0) == pytest.approx(1)


def test_proyeccion_latex_de_extremos_integrando_y_diferencial():
    """La vista previa agrupa sumas del integrando y presenta el infinito con su signo."""
    formula = formatear_expresion("∫(t+x,t,−∞,x)")
    assert formula["latex"] == r"f(x) = \int_{-\infty}^{x} \left(t + x\right)\,\mathrm{d}t"
    derivada = formatear_expresion(derivar_expresion("∫(x×t,t,0,1)"))
    assert derivada["latex"] == r"f(x) = \int_{0}^{1} t\,\mathrm{d}t"


def test_dominio_de_x_no_confunde_el_integrando_con_los_limites():
    """El intervalo de búsqueda exterior sí aplica a los límites móviles."""
    comprobar_dominio_intervalo("∫(1/√(t),t,0,x)", (0, 4))
    with pytest.raises(ErrorSingularidad):
        comprobar_dominio_intervalo("∫(t,t,0,1/x)", (-1, 1))


def test_resuelve_funciones_con_integrales_en_metodos_cerrados_y_abiertos():
    """Los motores usan el mismo evaluador de funciones y Newton aplica Leibniz."""
    cerrada = biseccion(EntradaBiseccion("∫(1/√(t),t,0,x)−2", 0, 4, 8))
    abierta = newton(EntradaMetodoAbierto(
        metodo="newton", expresion="∫(t,t,0,x)−2", x0=1.0, tolerancia=1e-8,
    ))
    assert cerrada.aproximacion == pytest.approx(1.0, abs=1e-8)
    assert abierta.estado == "EXITO"
    assert abierta.raiz == pytest.approx(2.0, abs=1e-8)
