"""Foco explicable e historial de aplicación sin tráfico de IA."""
import asyncio
import copy

from src.frontend.componentes.panel_ia import _recopilar_contexto_didactico
from src.frontend.controladores.operaciones_matrices.contexto_modelos import capturar_modelo
from src.frontend.vistas.operaciones_matrices.carga_modelos import cargar_captura_modelo
from src.frontend.vistas.operaciones_matrices._ejemplos_aplicacion_transformacion import EJEMPLOS_APLICACION
from tests.comun_construccion_vistas import construir_pagina


def test_explicacion_recibe_paso_y_resultado_y_editar_limpia_foco(monkeypatch):
    """La acción envía los metadatos vigentes y una edición retira la explicación anterior."""
    async def comprobar(vista, cliente):
        """Aísla el envío al panel manteniendo captura, navegación e historial reales."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        await vista._analizar(vista.boton_calcular)
        reproductor = vista.reproductor_aplicacion
        recibidos = []
        monkeypatch.setattr(vista.panel_ia, "disparar_explicacion_paso", recibidos.append)
        reproductor.ir_a(2)
        reproductor.al_explicar(reproductor.pasos[2])
        assert recibidos[0]["indice"] == 3 and recibidos[0]["total"] == 7
        assert recibidos[0]["detalle"]["formula"] == reproductor.pasos[2].cuerpo.latex
        contexto = _recopilar_contexto_didactico(vista, recibidos[0])
        assert "4/3" in contexto and "3/2" in contexto and "formula" in contexto
        vista.panel_ia.establecer_foco_explicacion(recibidos[0])
        captura = copy.deepcopy(vista.historial[0]["captura"])
        vista.entradas_vector_original[0].set_value("7")
        assert vista.panel_ia.foco_explicacion is None
        assert reproductor.tarjeta.is_deleted
        assert vista.historial[0]["captura"] == captura
        cargar_captura_modelo(vista, captura)
        assert capturar_modelo(vista) == captura and vista.ultimo_resultado is None
        await vista._analizar(vista.boton_calcular)
        assert vista.obtener_contexto_ia().resultado["vector_transformado"] == ["4/3", "3/2"]
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
