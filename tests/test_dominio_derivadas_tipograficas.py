"""Dominio y presupuesto durante el desarrollo de las derivadas tipográficas."""

import pytest

from src.backend.excepciones import ErrorDominio
from src.backend.resolutores.raices.funcion_real.evaluacion.evaluador_funcion import compilar
from src.backend.resolutores.raices.metodos_abiertos import derivar_expresion
from src.frontend.controladores.formato_funcion_real import formatear_expresion


@pytest.mark.parametrize(("texto", "fuera_de_dominio"), [
    ("√(−1)′", 0), ("(ln(x)−ln(x))″", -1), ("√(x)″", 0),
])
def test_derivadas_conservan_el_dominio_del_operando(texto, fuera_de_dominio):
    """Evita raíces procedentes de simplificar un operando indefinido."""
    with pytest.raises(ErrorDominio):
        compilar(texto)(fuera_de_dominio)


def test_derivada_de_prima_admite_serializacion_y_vista_previa():
    """La derivación sucesiva conserva el dominio y renderiza el resultado matemático."""
    texto = derivar_expresion("(ln(x)-ln(x))′")
    assert compilar(texto)(1) == pytest.approx(0)
    with pytest.raises(ErrorDominio):
        compilar(texto)(-1)
    assert "dominio_derivada" not in formatear_expresion(texto)["latex"]


def test_derivada_segunda_de_potencias_anidadas_respeta_presupuesto():
    """Detiene el desarrollo de una derivada grande con el error controlado del AST."""
    texto = "(" + "(" * 25 + "x" + ")^2" * 25 + ")″"
    with pytest.raises(ValueError, match="demasiadas operaciones"):
        compilar(texto)
