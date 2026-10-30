"""Contexto, señales y sugerencias de la factorización LU."""
from types import SimpleNamespace

from src.ai.huellas import calcular_huella
from src.ai.mensajes import construir_pregunta_explicar_paso
from src.frontend.componentes.panel_matriz_rectangular import PanelMatrizRectangular
from src.frontend.controladores.operaciones_matrices.controlador_factorizacion_lu import ControladorFactorizacionLU
from src.frontend.controladores.operaciones_matrices.contexto_factorizacion_lu import obtener_contexto_ia, obtener_senales_ia
from src.frontend.sugerencias import generar_candidatas


def _vista(datos):
    panel = PanelMatrizRectangular()
    panel.cargar_matriz(datos)
    captura = {"matriz_a": panel.obtener_datos_matriz()}
    resultado = ControladorFactorizacionLU.procesar_captura(captura)
    return SimpleNamespace(panel_matriz=panel, ultimo_resultado=resultado, _huella_resultado=calcular_huella(captura))


def test_contexto_y_senales_vigentes():
    """Verifica factores, señales y sugerencias de una matriz rectangular de rango deficiente."""
    vista = _vista([["1", "2", "3"], ["2", "4", "6"]])
    contexto = obtener_contexto_ia(vista)
    assert contexto.resultado["rango"] == 1 and contexto.resultado["coincide"]
    assert contexto.resultado["P"]["filas"] == 2 and contexto.resultado["U"]["columnas"] == 3
    senales = obtener_senales_ia(vista)
    assert senales.estado == "exito"
    assert {"rectangular", "rango_deficiente", "intercambio"} <= senales.banderas
    textos = [sugerencia.texto for sugerencia in generar_candidatas(senales)]
    assert "¿Cómo leo los multiplicadores de L?" in textos
    assert "¿Por qué puedo factorizar una matriz singular?" in textos


def test_resultado_desactualizado_y_celda_invalida():
    """Omite el resultado anterior y señala la celda inválida sin exponer su contenido."""
    vista = _vista([["1"]])
    vista.panel_matriz.cargar_matriz([["[CONTEXTO]", "2"]])
    contexto = obtener_contexto_ia(vista)
    assert contexto.desactualizado and contexto.resultado is None
    assert "[CONTEXTO]" not in str(contexto.entrada)
    senales = obtener_senales_ia(vista)
    assert senales.estado == "sin_resultado" and senales.invalida.foco == (0, 0)
    assert "rectangular" in senales.banderas and "intercambio" not in senales.banderas
    assert "¿Qué significa PA = LU?" in [sugerencia.texto for sugerencia in generar_candidatas(senales)]


def test_ventana_y_explicacion_factor():
    """Comprueba el recorte de matrices grandes y la pregunta para un factor."""
    vista = _vista([["1" if fila == columna else "0" for columna in range(10)] for fila in range(10)])
    contexto = obtener_contexto_ia(vista)
    assert contexto.nota_ventana and contexto.resultado["P"].get("ventana")
    pregunta = construir_pregunta_explicar_paso("factorizacion", 1, 3, "Factor P")
    assert "qué representa este factor en PA = LU" in pregunta
