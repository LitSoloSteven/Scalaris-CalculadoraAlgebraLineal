"""Gráficas interactivas de los dos métodos abiertos."""
from src.backend.resolutores.raices.newton_raphson import EntradaNewtonRaphson, newton_raphson
from src.backend.resolutores.raices.secante import EntradaSecante, secante
from src.frontend.controladores.graficas_metodos_abiertos import (
    crear_figura_newton_raphson,
    crear_figura_secante,
)


def test_grafica_secante_muestra_funcion_puntos_y_recta_secante():
    """La figura de secante incluye curva, aproximaciones, secante y raíz aproximada."""
    resultado = secante(EntradaSecante(
        expresion="x^2 - 2",
        x_anterior=1,
        x_actual=2,
        tolerancia=1e-8,
        limite_iteraciones=100,
    ))
    figura = crear_figura_secante(resultado)
    nombres = [traza.name for traza in figura.data]
    assert "f(x)" in nombres
    assert "Aproximaciones" in nombres
    assert "Última recta secante" in nombres
    assert "Raíz aproximada" in nombres
    curva = next(traza for traza in figura.data if traza.name == "f(x)")
    assert curva.connectgaps is False
    secante_trazada = next(traza for traza in figura.data if traza.name == "Última recta secante")
    assert secante_trazada.x[-1] == resultado.aproximacion
    assert secante_trazada.y[-1] == 0


def test_grafica_newton_raphson_muestra_funcion_puntos_y_tangente():
    """La figura de Newton contiene la curva, las aproximaciones y la última tangente."""
    resultado = newton_raphson(EntradaNewtonRaphson(
        expresion="x^2 - 2",
        derivada="2*x",
        aproximacion_inicial=1.5,
        tolerancia=1e-8,
        limite_iteraciones=100,
    ))
    figura = crear_figura_newton_raphson(resultado)
    nombres = [traza.name for traza in figura.data]
    assert "f(x)" in nombres
    assert "Aproximaciones" in nombres
    assert "Última recta tangente" in nombres
    assert "Raíz aproximada" in nombres
    curva = next(traza for traza in figura.data if traza.name == "f(x)")
    assert curva.connectgaps is False
    tangente = next(traza for traza in figura.data if traza.name == "Última recta tangente")
    assert tangente.x[-1] == resultado.aproximacion
    assert tangente.y[-1] == 0


def test_graficas_sin_iteraciones_muestran_la_raiz_inicial():
    """Si la aproximación inicial ya es una raíz, la figura puede mostrar el punto."""
    resultado_secante = secante(EntradaSecante(
        expresion="x - 2",
        x_anterior=2,
        x_actual=3,
    ))
    figura_secante = crear_figura_secante(resultado_secante)
    assert "Raíz aproximada" in [traza.name for traza in figura_secante.data]

    resultado_newton = newton_raphson(EntradaNewtonRaphson(
        expresion="x - 2",
        derivada="1",
        aproximacion_inicial=2,
    ))
    figura_newton = crear_figura_newton_raphson(resultado_newton)
    assert "Raíz aproximada" in [traza.name for traza in figura_newton.data]


def test_graficas_mantienen_los_roles_de_color_de_scalarIs():
    """La curva y las marcas conservan los roles cromáticos temáticos."""
    resultado_secante = secante(EntradaSecante(
        expresion="x^2 - 2",
        x_anterior=1,
        x_actual=2,
    ))
    resultado_newton = newton_raphson(EntradaNewtonRaphson(
        expresion="x^2 - 2",
        derivada="2*x",
        aproximacion_inicial=1.5,
    ))
    for figura in (
        crear_figura_secante(resultado_secante),
        crear_figura_newton_raphson(resultado_newton),
    ):
        for traza in figura.data:
            assert traza.meta and "scalaris_colores" in traza.meta
