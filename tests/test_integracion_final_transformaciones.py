"""Recorridos completos de límites, recuperación y desmontaje de transformaciones."""
import asyncio

import pytest
from nicegui import run, ui

from src.frontend.controladores.operaciones_matrices.contexto_modelos import capturar_modelo
from src.frontend.vistas.operaciones_matrices.carga_modelos import cargar_captura_modelo
from tests.comun_construccion_vistas import construir_pagina

FRACCION_LARGA = "1/" + "9" * 200
CASOS = (
    ([["2"]], ["1/3"], ["2/3"], 0),
    ([["1", "2"], ["2", "4"]], ["2", "-1"], ["0", "0"], 1),
    ([["0", "0"], ["0", "0"]], ["0", "0"], ["0", "0"], 1),
    ([["1", "0"], ["0", "1"], ["1", "1"]], ["1/3", "2/7"], ["1/3", "2/7", "13/21"], 2),
    ([["1", "0"], ["0", "1"]], [FRACCION_LARGA, "2"], [FRACCION_LARGA, "2"], 1),
    ([[str(int(fila == columna)) for columna in range(8)] for fila in range(8)],
     ["1/3"] * 8, ["1/3"] * 8, 0),
)


@pytest.mark.parametrize("matriz,vector,esperado,graficas", CASOS)
def test_resultado_sesion_y_documento_corresponden_en_limites(monkeypatch, matriz, vector, esperado, graficas):
    """Los valores exactos llegan a resultado, historial y PDF sin recortar dimensiones."""
    async def comprobar(vista, cliente):
        """Ejecuta el recorrido real y restaura su captura después de invalidar el cálculo."""
        cargar_captura_modelo(vista, {"matriz_transformacion": matriz, "vector_original": vector, "tipo_objeto": "punto"})
        await vista._analizar(vista.boton_calcular)
        resultado = vista.ultimo_resultado
        assert resultado["vector_transformado"]["exacta"] == esperado
        assert resultado["verificacion"] is True
        assert len(vista.reproductor_pasos.pasos) == 2 * len(matriz) + 3
        assert sum(isinstance(elemento, ui.plotly) for elemento in vista.contenedor_resultados.descendants()) == graficas
        control = vista.actualizar_exportacion_pdf.__self__
        captura = capturar_modelo(vista)
        assert control.enlace.entrada_documental() == captura == vista.historial[0]["captura"]
        testigo = control.enlace.testigo()
        vista.entradas_vector_original[0].set_value("7")
        assert not control.enlace.comprobar(testigo, resultado)
        control.abrir()
        assert control.dialogo is None
        cargar_captura_modelo(vista, captura)
        assert capturar_modelo(vista) == captura and vista.ultimo_resultado is None
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


@pytest.mark.parametrize("fallar", [False, True])
def test_desmontaje_descarta_trabajador_pendiente_y_su_error(monkeypatch, fallar):
    """Desmontar impide publicar incluso si el trabajador acaba con una excepción."""
    async def comprobar(vista, cliente):
        """Retiene el trabajador mientras se retira el estado de la vista."""
        cargar_captura_modelo(vista, {"matriz_transformacion": [["1"]], "vector_original": ["2"]})
        iniciado, continuar = asyncio.Event(), asyncio.Event()

        async def trabajar(funcion, *argumentos):
            """Devuelve un cálculo o un error después de liberar la espera controlada."""
            iniciado.set()
            await continuar.wait()
            if fallar:
                raise RuntimeError("detalle privado del trabajador")
            return funcion(*argumentos)

        monkeypatch.setattr(run, "io_bound", trabajar)
        tarea = asyncio.create_task(vista._analizar(vista.boton_calcular))
        await iniciado.wait()
        vista._desmontar_modelo()
        continuar.set()
        await tarea
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        assert vista.reproductor_pasos is None and vista.reproductor_aplicacion is None
        assert not vista.historial and not vista._calculando
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_recalcular_reemplaza_controles_y_acota_historial(monkeypatch):
    """Recalcular no retiene tarjetas ni temporizadores y limita la memoria de sesión."""
    async def comprobar(vista, cliente):
        """Alterna el tipo de objeto y comprueba el ciclo de vida de doce resultados."""
        cargar_captura_modelo(vista, {"matriz_transformacion": [["1"]], "vector_original": ["2"]})
        reproductores = []
        for indice in range(12):
            vista.selector_tipo_objeto.set_value("punto" if indice % 2 else "vector")
            await vista._analizar(vista.boton_calcular)
            reproductores.append(vista.reproductor_pasos)
        assert len(vista.historial) == 5
        assert all(reproductor.tarjeta.is_deleted for reproductor in reproductores[:-1])
        assert all(reproductor.temporizador is None for reproductor in reproductores[:-1])
        assert not reproductores[-1].tarjeta.is_deleted
        vista.limpiar_todo()
        assert reproductores[-1].tarjeta.is_deleted
        assert vista.obtener_contexto_ia().resultado is None
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
