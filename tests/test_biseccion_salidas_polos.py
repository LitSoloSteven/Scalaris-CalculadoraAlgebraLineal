"""Consumo coherente de restricciones de dominio en gráfica, resumen y contexto."""
import json

import pytest

from src.frontend.controladores.biseccion import muestreo
from src.frontend.controladores.biseccion.controlador import calcular_presentacion, resolver_captura
from src.frontend.controladores.biseccion.presentacion import construir_pasos
from src.frontend.controladores.biseccion.presentacion_criterio import texto_resumen, titulo_estado
from src.frontend.controladores.biseccion.vista_previa import preparar_vista_previa
from src.frontend.vistas.biseccion.figura import crear_figura_previa
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


@pytest.mark.parametrize("unidad,intervalo", [("radianes", (1, 2)), ("grados", (89, 91))])
def test_error_estructural_en_resumen_y_procedimiento(unidad, intervalo):
    """El error no inventa aproximación, filas ni abscisa evaluada en sus salidas textuales."""
    captura = {**captura_criterio(), "expresion": "tan(x)", "unidad_angular": unidad,
               "extremo_izquierdo": intervalo[0], "extremo_derecho": intervalo[1]}
    motor = resolver_captura(captura)
    respuesta = calcular_presentacion(captura)
    assert respuesta == motor and respuesta["estado"] == "ERROR"
    assert titulo_estado(respuesta) == "Singularidad identificada"
    texto = texto_resumen(respuesta, 4)
    assert respuesta["mensaje"] in texto and "SINGULARIDAD_DETECTADA" in texto
    assert "No corresponde a una evaluación puntual" in texto
    assert "x ≈" not in texto
    pasos, _ = construir_pasos(respuesta)
    assert len(pasos) == 2 and pasos[-1].descripcion == respuesta["mensaje"]
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("expresion,intervalo,unidad", [
    ("tan(x)", (1, 2), "radianes"),
    ("tan(x)", (89, 91), "grados"),
    ("1e-200*tan(x)", (1, 2), "radianes"),
    ("tan(1000*x)", (0, 1), "radianes"),
    ("1/(x-.1234567)", (-1, 1), "radianes"),
])
def test_grafica_no_une_segmentos_con_restriccion(expresion, intervalo, unidad):
    """Incluso sin salto grande o con varios polos entre muestras se cortan todos los segmentos restringidos."""
    respuesta = preparar_vista_previa({"expresion": expresion, "x_min": intervalo[0],
                                      "x_max": intervalo[1], "unidad_angular": unidad})
    muestra = respuesta["muestra"]
    figura = crear_figura_previa(respuesta)
    assert muestra["huecos"] and figura.data[0].connectgaps is False
    assert figura.layout.hovermode is False
    for indice in range(1, len(muestra["x"])):
        if muestra["y"][indice - 1] is not None and muestra["y"][indice] is not None:
            muestreo.comprobar_dominio_intervalo(expresion, tuple(muestra["x"][indice - 1:indice + 1]),
                                               unidad_angular=unidad)
    json.dumps(respuesta, allow_nan=False)


def test_presupuesto_grafico_sin_evaluaciones_auxiliares(monkeypatch):
    """El análisis de 400 segmentos conserva exactamente 401 evaluaciones de la función."""
    evaluadas, comprobadas = [], []
    def evaluar_registrada(funcion, abscisa):
        """Cuenta muestras antes de devolver la evaluación lineal."""
        evaluadas.append(abscisa)
        return funcion(abscisa)
    def comprobar_registrada(expresion, intervalo, **opciones):
        """Registra análisis estructurales sin evaluar la función."""
        comprobadas.append(intervalo)
    monkeypatch.setattr(muestreo, "evaluar", evaluar_registrada)
    monkeypatch.setattr(muestreo, "comprobar_dominio_intervalo", comprobar_registrada)
    respuesta = preparar_vista_previa({"expresion": "x", "x_min": -1, "x_max": 1})
    assert len(evaluadas) == muestreo.MUESTRAS_GRAFICA == 401
    assert len(comprobadas) == 400 and not respuesta["muestra"]["huecos"]


def test_cero_extremo_y_contexto_con_polo_conservan_veredicto(monkeypatch):
    """La vista conserva el cero válido, el aviso estructural y el hueco como datos separados."""
    async def comprobar(vista):
        """Publica el resultado y verifica su representación sin solicitar respuestas de IA."""
        vista.cargar_captura({**captura_criterio(), "expresion": "x*tan(x)",
                             "extremo_izquierdo": 0, "extremo_derecho": 2})
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        contexto = vista.obtener_contexto_ia().resultado
        assert contexto["estado"] == respuesta["estado"] == "EXITO"
        assert respuesta["aproximacion"] == 0 and respuesta["muestra"]["huecos"]
        assert contexto["codigo_diagnostico"] == "CERO_EVALUADO"
        assert contexto["diagnostico"]["codigo"] == "SINGULARIDAD_DETECTADA"
        assert contexto["advertencias"] == respuesta["advertencias"]
        assert contexto["aviso_grafica"] == respuesta["aviso_grafica"]
        assert contexto["advertencias"][0] in texto_resumen(respuesta, 4)
    ejecutar_escenario(monkeypatch, comprobar)
