"""Navegación de la traza más larga admitida en la captura."""
from src.backend.resolutores.raices.limites_raices import LIMITE_ITERACIONES_MAXIMO
from src.frontend.componentes.tabla_iteraciones import FILAS_POR_PAGINA
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


def test_ultima_fila_del_limite_conserva_precision_paso_y_nodo(monkeypatch):
    """Muestra solo la última página y mantiene su fila al inspeccionar cifras completas."""
    async def comprobar(vista):
        maximo = LIMITE_ITERACIONES_MAXIMO
        vista.cargar_captura(captura_regla_falsa(
            expresion="x^10-1", extremo_izquierdo="0", limite_iteraciones=str(maximo),
            criterio={"tipo": "iteraciones", "parametro": str(maximo)},
        ))
        await vista.resolver()
        detalle = vista.detalle_procedimiento
        filas = vista.ultimo_resultado["iteraciones"]
        grafica = detalle.grafica
        assert len(filas) == maximo and len(detalle.tabla.tabla.rows) == FILAS_POR_PAGINA

        detalle.reproductor.ir_a(maximo)
        corta = detalle.tabla.tabla.rows[-1]["aproximacion"]
        detalle.tabla.precision.set_value(True)
        ultima = detalle.tabla.tabla.rows[-1]
        assert 0 < len(detalle.tabla.tabla.rows) <= FILAS_POR_PAGINA
        assert ultima["i"] == str(maximo) and ultima["aproximacion"] != corta
        assert float(ultima["aproximacion"]) == filas[-1]["aproximacion"]
        assert detalle.tabla.tabla.selected == [ultima]
        assert detalle.fila_activa is filas[-1] and detalle.grafica is grafica

    ejecutar_escenario(monkeypatch, comprobar)
