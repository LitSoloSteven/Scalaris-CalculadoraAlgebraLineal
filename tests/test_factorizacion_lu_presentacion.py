"""Contratos del procedimiento y de los ejemplos de factorización LU."""
from src.frontend.controladores.operaciones_matrices.controlador_factorizacion_lu import ControladorFactorizacionLU
from src.frontend.vistas.operaciones_matrices._ejemplos_factorizacion_lu import EJEMPLOS_FACTORIZACION_LU
from src.frontend.vistas.operaciones_matrices._presentacion_factorizacion_lu import adaptar_traza_factorizacion_lu


def test_ejemplos_y_traza():
    """Comprueba ejemplos reales, conservación del orden y pertenencia única de pasos."""
    for indice, ejemplo in enumerate(EJEMPLOS_FACTORIZACION_LU):
        resultado = ControladorFactorizacionLU.procesar_captura({"matriz_a": ejemplo["datos"]})
        assert resultado["estado"] == "EXITO" and resultado["comprobacion"]["coincide"]
        intercambio = any(paso["tipo"] == "intercambio" for paso in resultado["traza"])
        if indice in (0, 1):
            assert intercambio == (indice == 1)
        if indice == 2:
            assert resultado["rango"] < min(resultado["filas"], resultado["columnas"])
        if indice == 3:
            assert resultado["filas"] != resultado["columnas"]
        pasos, grupos = adaptar_traza_factorizacion_lu(resultado)
        assert [paso.descripcion for paso in pasos] == [paso["descripcion"] for paso in resultado["traza"]]
        assert [valor for grupo in grupos for valor in grupo.indices_pasos] == list(range(len(pasos)))
        assert all(paso.meta_explicar["tipo"] == {"resultado": "factorizacion", "operacion": "verificacion"}.get(paso.tipo, paso.tipo) for paso in pasos)
