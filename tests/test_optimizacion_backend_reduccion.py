"""Contratos completos de eventos y aislamiento de los estados de eliminación."""
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.reduccion import ReductorFilas
from src.backend.resolutores.sistemas_lineales.pasos_reduccion import RegistroPasosSistema
from src.backend.resolutores.operaciones_matrices.pasos_determinante import RegistroPasosDeterminante


@pytest.mark.parametrize("estrategia", ["parcial", "primer_no_nulo", "sin_intercambios"])
def test_reduccion_conserva_eventos_y_valores_exactos(estrategia):
    """Una eliminación y dos normalizaciones mantienen los tipos, coordenadas y valores históricos."""
    matriz = Matriz(2, 3, [[2, 0, 2], [1, 3, 4]])
    eventos = []

    def registrar(tipo, estado, datos):
        """Captura un estado propio para comprobar el contrato completo de cada evento."""
        eventos.append((tipo, estado.clonar(), dict(datos)))

    opciones = ConfiguracionReduccion(reduccion_completa=True, estrategia_pivote=estrategia)
    resultado = ReductorFilas(matriz, 2, opciones, registrar).reducir()
    assert set(resultado) == {"matriz_reducida", "rango", "columnas_pivote", "intercambios",
                              "multiplicadores", "pivote_bloqueado"}
    assert [tipo for tipo, _, _ in eventos] == ["inicial", "pivote", "eliminacion", "pivote",
                                               "normalizacion", "normalizacion"]
    assert eventos[2][2] == {"fila": 1, "fila_pivote": 0, "columna": 0, "factor": Fraction(1, 2)}
    assert type(eventos[2][2]["factor"]) is Fraction
    assert eventos[2][1].datos == [[2, 0, 2], [Fraction(0), Fraction(3), Fraction(3)]]
    assert all(type(valor) is Fraction for valor in eventos[2][1].datos[1])
    assert resultado["matriz_reducida"].datos == [[Fraction(1), Fraction(0), Fraction(1)],
                                                [Fraction(0), Fraction(1), Fraction(1)]]
    assert resultado["columnas_pivote"] == [0, 1]
    assert resultado["rango"] == 2 and resultado["intercambios"] == 0
    assert resultado["multiplicadores"] == [] and resultado["pivote_bloqueado"] is None
    assert matriz.datos == [[2, 0, 2], [1, 3, 4]]


def test_registros_conservan_claves_textos_y_copias_mutables_independientes():
    """Modificar matriz de entrada o un paso no afecta las otras instantáneas de los registros."""
    matriz = Matriz(2, 2, [[2, 0], [1, 3]])
    sistema = RegistroPasosSistema(True)
    determinante = RegistroPasosDeterminante()
    for registro in (sistema, determinante):
        registro.registrar("inicial", matriz, {})
        registro.registrar("inicial", matriz, {})
    assert set(sistema.pasos[0]) == {"descripcion", "matriz"}
    assert sistema.pasos[0]["descripcion"] == "Matriz inicial aumentada [A|b]:"
    assert set(determinante.traza[0]) == {"tipo", "descripcion", "explicacion", "matriz", "operacion"}
    assert determinante.pasos == ["Matriz inicial A", "Matriz inicial A"]
    assert determinante.traza[0]["tipo"] == "inicial" and determinante.traza[0]["operacion"] == {}
    for pasos in (sistema.pasos, determinante.traza):
        assert type(pasos[0]["matriz"]) is Matriz
        pasos[0]["matriz"].establecer(0, 0, 99)
        assert pasos[1]["matriz"].obtener(0, 0) == 2
    matriz.establecer(1, 1, 88)
    assert sistema.pasos[1]["matriz"].obtener(1, 1) == 3
    assert determinante.traza[1]["matriz"].obtener(1, 1) == 3


def test_eliminacion_conserva_conversion_binaria_de_flotantes_no_reconstruidos():
    """Los flotantes fuera de reconstrucción racional mantienen la conversión exacta de Fraction."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    matriz.datos[0][1] = 1e-15
    reductor = ReductorFilas(matriz, 2, ConfiguracionReduccion())
    origen = [Fraction(valor) for valor in reductor.matriz.datos[0]]
    destino = [Fraction(valor) for valor in reductor.matriz.datos[1]]
    factor = Fraction(destino[0]) / Fraction(origen[0])
    esperado = [valor - factor * pivote for valor, pivote in zip(destino, origen)]
    reductor._eliminar_destino(1, 0, 0)
    assert reductor.matriz.datos[1] == esperado
    assert all(type(valor) is Fraction for valor in reductor.matriz.datos[1])
