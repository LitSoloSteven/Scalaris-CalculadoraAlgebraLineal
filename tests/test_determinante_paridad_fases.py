"""Fases y foco real de ambos métodos del determinante."""
import pytest

from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante
from src.frontend.controladores.operaciones_matrices.fases_determinante import agrupar_determinante
from src.frontend.controladores.operaciones_matrices.foco_determinante import construir_meta_determinante


@pytest.mark.parametrize("metodo", ["laplace", "lu"])
@pytest.mark.parametrize("datos", [[[2]], [[1, 2], [2, 4]], [[0, 1], [2, 3]]])
def test_fases_cubren_cada_paso_una_vez(metodo, datos):
    """Incluye orden uno, matriz singular y una matriz con intercambio."""
    resultado = ControladorDeterminante.procesar(datos, metodo)
    grupos, posiciones = agrupar_determinante(resultado)
    assert len(grupos) >= 2
    assert [indice for grupo in grupos for indice in grupo["indices_pasos"]] == list(range(len(resultado["traza"])))
    assert grupos[-1]["tipo"] == "final"
    assert all(indice in grupos[posiciones[indice]]["indices_pasos"] for indice in range(len(posiciones)))
    if metodo == "laplace":
        assert sum(grupo["tipo"] == "menor" for grupo in grupos) == len(datos) if len(datos) > 1 else len(grupos) == 2


def test_intercambio_transporta_las_dos_filas_y_su_estado_previo():
    """El foco corresponde a las instantáneas anteriores y posteriores del backend."""
    traza = ControladorDeterminante.procesar([[0, 1], [2, 3]], "lu")["traza"]
    indice = next(indice for indice, paso in enumerate(traza) if paso["tipo"] == "intercambio")
    meta = construir_meta_determinante(traza, indice)
    assert meta["filas_antes"] == {"1": ["0", "1"], "2": ["2", "3"]}
    assert meta["filas_despues"] == {"1": ["2", "3"], "2": ["0", "1"]}
    assert "columnas" in meta and "<" not in meta["operacion"]


def test_menor_incluye_coordenadas_valores_y_orden_original():
    """El contexto conserva el elemento, cofactor y matriz menor ya calculados."""
    traza = ControladorDeterminante.procesar([[1, 2], [3, 4]], "laplace")["traza"]
    meta = construir_meta_determinante(traza, 1)
    assert meta["detalle"]["fila"] == "1" and meta["detalle"]["columna"] == "1"
    assert meta["detalle"]["menor"]["datos"] == [["4"]]
    assert meta["detalle"]["elemento"] == "1"
    assert meta["detalle"]["filas_originales"] == [2]


def test_intercambio_tardio_pertenece_a_su_columna():
    """Un intercambio de la segunda columna no se incorpora a la fase anterior."""
    resultado = ControladorDeterminante.procesar([[0, 2, 1], [1, 1, 0], [2, 1, 1]], "lu")
    grupos, posiciones = agrupar_determinante(resultado)
    intercambios = [indice for indice, paso in enumerate(resultado["traza"]) if paso["tipo"] == "intercambio"]
    assert len(intercambios) == 2
    assert posiciones[intercambios[0]] != posiciones[intercambios[1]]
    assert grupos[posiciones[intercambios[1]]]["titulo"].startswith("Columna 2")
    assert "con intercambio" in grupos[posiciones[intercambios[1]]]["titulo"]
