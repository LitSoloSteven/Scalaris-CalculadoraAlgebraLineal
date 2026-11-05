"""Verifica la sincronización del modo examen en la vista montada."""
from nicegui import ui

from src.frontend.componentes.copia_resultado import texto_resultado_copiable
from src.frontend.controladores.biseccion.salidas_biseccion import COLUMNAS_EXAMEN
from src.frontend.vistas.biseccion import resumen_criterio
from src.frontend.vistas.biseccion.vista_biseccion import VistaBiseccion
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def _interruptores(vista) -> list:
    return [elemento for elemento in vista.contenedor_resultados.descendants()
            if isinstance(elemento, ui.switch) and elemento.text == "Modo examen"]


def _tabla(vista) -> ui.table:
    return next(elemento for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.table))


def _comprobar_fila(vista, fila: dict, copia: str) -> None:
    reproductor = vista.reproductor_pasos
    reproductor.ir_a(int(fila["i"]), autoreproduccion=True)
    etiquetas = {elemento.text for elemento in reproductor.contenedor_cuerpo.descendants()
                 if isinstance(elemento, ui.label) and elemento.parent_slot.parent.visible}
    for clave, etiqueta in COLUMNAS_EXAMEN:
        assert f"{etiqueta}: {fila[clave]}" in etiquetas
    assert "\t".join((fila["i"], *(fila[clave] for clave, _ in COLUMNAS_EXAMEN))) in copia


def _capturar_copias(monkeypatch) -> list[str]:
    copias = []
    monkeypatch.setattr(resumen_criterio, "renderizar_copia_resultado",
                        lambda generar: copias.append(texto_resultado_copiable(generar())))
    return copias


def _comprobar_modo_oculto(reproductor, tabla: ui.table, copia: str) -> None:
    assert "signo_examen" not in tabla.rows[0] and "Modo examen" not in copia
    assert not any(elemento.parent_slot.parent.visible for elemento in reproductor.contenedor_cuerpo.descendants()
                   if isinstance(elemento, ui.label) and elemento.text.startswith("Acción ejecutada"))


def test_modo_examen_sincroniza_tabla_paso_y_copia_sin_invalidar(monkeypatch):
    """El cambio conserva captura, resultado, navegación y formato numérico."""
    copias = _capturar_copias(monkeypatch)

    async def _comprobar(vista):
        vista.cargar_captura(captura_criterio("iteraciones", 3))
        await vista.resolver()
        examen, = _interruptores(vista)
        tabla = _tabla(vista)
        respuesta, revision = vista.ultimo_resultado, vista._revision_captura
        reproductor = vista.reproductor_pasos
        reproductor.ir_a(1, autoreproduccion=True)
        _comprobar_modo_oculto(reproductor, tabla, copias[-1])
        examen.set_value(True)
        assert vista.reproductor_pasos is reproductor and reproductor.indice_actual == 1
        assert vista.ultimo_resultado is respuesta and vista._revision_captura == revision
        assert "modo_examen" not in vista.capturar() and len(vista.historial) == 1
        assert tabla.rows[0]["accion_examen"] == "b = c"
        assert tabla.rows[1]["accion_examen"] == "a = c"
        assert tabla.rows[-1]["accion_examen"].startswith("Detener.")
        for fila in tabla.rows:
            _comprobar_fila(vista, fila, copias[-1])
        vista.formato.set_value(6)
        assert "x ≈ 1.375000" in copias[-1] and "Modo examen" in copias[-1]
        assert copias[-1].startswith("Resultado:\n3 iteraciones completadas")
        examen.set_value(False)
        _comprobar_modo_oculto(reproductor, tabla, copias[-1])

    ejecutar_escenario(monkeypatch, _comprobar)


def test_preferencia_de_vista_persiste_al_recuperar_captura(monkeypatch):
    """Restaurar un reciente invalida el cálculo anterior y conserva la preferencia local."""
    async def _comprobar(vista):
        vista.cargar_captura(captura_criterio())
        await vista.resolver()
        anterior, = _interruptores(vista)
        anterior.set_value(True)
        vista.cargar_captura(vista.historial[0]["captura"])
        assert anterior.is_deleted and vista.ultimo_resultado is None and not _interruptores(vista)
        await vista.resolver()
        nuevo, = _interruptores(vista)
        assert nuevo.value and not VistaBiseccion().modo_examen
        assert "signo_examen" in _tabla(vista).rows[-1]
        vista.cargar_captura({"expresion": "x", "extremo_izquierdo": "0", "extremo_derecho": "1"})
        await vista.resolver()
        assert vista.ultimo_resultado["motivo_parada"] == "raiz_exacta"
        assert vista.modo_examen and not _interruptores(vista)

    ejecutar_escenario(monkeypatch, _comprobar)


def test_error_parcial_conserva_accion_y_fallo_en_el_procedimiento(monkeypatch):
    """Una evaluación inválida conserva la partición válida sin inventar otra fila."""
    copias = _capturar_copias(monkeypatch)

    async def _comprobar(vista):
        vista.cargar_captura({"expresion": "1/(x*x-.0625)", "extremo_izquierdo": "0", "extremo_derecho": "1"})
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "ERROR" and "muestra" not in vista.ultimo_resultado
        examen, = _interruptores(vista)
        examen.set_value(True)
        fila, = _tabla(vista).rows
        assert fila["accion_examen"] == "b = c"
        _comprobar_fila(vista, fila, copias[-1])
        assert "La evaluación falló en x = 0.25" in vista.reproductor_pasos.pasos[-1].explicacion
        assert copias[-1].startswith("Resultado:\nError de entrada o evaluación")
        assert "0.25" in copias[-1]

    ejecutar_escenario(monkeypatch, _comprobar)
