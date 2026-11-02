"""Balance económico y explicación del ejemplo precargado de dos sectores."""
import asyncio
from fractions import Fraction

from nicegui import ui

from src.frontend.vistas.operaciones_matrices._ejemplos_leontief import EJEMPLOS_LEONTIEF
from tests.comun_construccion_vistas import construir_pagina


def test_ejemplo_economico_conserva_balance_y_explicacion_exactos(monkeypatch):
    """Comprueba captura, balance y textos del ejemplo usando la vista y el dominio reales."""
    async def comprobar(vista, cliente):
        """Carga los controles reales y contrasta la producción con el balance racional."""
        ejemplo = EJEMPLOS_LEONTIEF[0]
        vista._cargar_ejemplo(ejemplo)
        await vista._calcular(ui.button("Calcular"))
        resultado = vista.ultimo_resultado
        assert resultado["estado"] == "EXITO"
        assert resultado["vector_produccion"] == ["220", "560/3"]
        assert resultado["vector_demanda"] == ["120", "80"]
        assert resultado["determinante_leontief"] == "3/5"
        assert resultado["hawkins_simon"]["es_economicamente_viable"] is True
        assert vista.historial[0]["captura"]["matriz_coeficientes"] == ejemplo["matriz_coeficientes"]
        _comprobar_balance(resultado)
        _comprobar_explicacion(vista, ejemplo, resultado)
    asyncio.run(construir_pagina(monkeypatch, "leontief", comprobar))


def _comprobar_balance(resultado: dict) -> None:
    produccion_agricola, produccion_industrial = map(Fraction, resultado["vector_produccion"])
    assert Fraction(4, 5) * produccion_agricola - Fraction(3, 10) * produccion_industrial == 120
    assert -Fraction(2, 5) * produccion_agricola + Fraction(9, 10) * produccion_industrial == 80
    consumo = [fila["consumo_intermedio"] for fila in resultado["analisis_sectorial"]]
    assert consumo == ["100", "320/3"]
    for fila in resultado["analisis_sectorial"]:
        assert Fraction(fila["produccion_total"]) - Fraction(fila["consumo_intermedio"]) == Fraction(fila["demanda_final"])


def _comprobar_explicacion(vista, ejemplo: dict, resultado: dict) -> None:
    elementos = list(vista.contenedor_resultados.descendants())
    etiquetas = {elemento.text for elemento in elementos if isinstance(elemento, ui.label)}
    contenido = "\n".join(elemento.content for elemento in elementos if isinstance(elemento, ui.html))
    assert {"Agricultura", "Industria", "Análisis Sectorial", "100", "320/3"} <= etiquetas
    assert "Producción total: 220" in contenido and "Producción total: 560/3" in contenido
    assert "Demanda final: <b>120</b>" in contenido and "Demanda final: <b>80</b>" in contenido
    assert all(valor in ejemplo["descripcion"] for valor in resultado["vector_produccion"])
    comprobacion = [paso for paso in resultado["traza_comprobacion"] if "(I-C)x=d" in paso["descripcion"]]
    assert len(comprobacion) == 4
    assert comprobacion[-1]["descripcion"] == "Comprobacion exacta de (I-C)x=d: coincide"
