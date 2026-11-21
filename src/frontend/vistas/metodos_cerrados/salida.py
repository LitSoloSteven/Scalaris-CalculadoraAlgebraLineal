"""Resumen, traza paginada y navegación sincronizada de la solución."""
from nicegui import ui

from src.frontend.componentes.reproductor_pasos import ReproductorPasos, renderizar_latex
from src.frontend.componentes.raices.resultados.informe_continuidad_raices import mostrar_informe_continuidad
from src.frontend.componentes.raices.resultados.tabla_raices_seleccionable import FormatoTablaRaices, TablaRaicesSeleccionable
from src.frontend.controladores.biseccion import presentacion as presentacion_biseccion
from src.frontend.controladores.biseccion.formulas_procedimiento import formulas_iteracion as formulas_biseccion
from src.frontend.controladores.biseccion.salidas_biseccion import COLUMNAS_EXAMEN, datos_examen
from src.frontend.controladores.formato_funcion_real import formatear_expresion
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION, METODOS
from src.frontend.controladores.regla_falsa.formulas_procedimiento import formulas_iteracion as formulas_regla_falsa
from src.frontend.controladores.regla_falsa.pasos import construir_pasos
from src.frontend.controladores.regla_falsa.pasos_ampliados import construir_pasos_configurados
from src.frontend.controladores.regla_falsa.tabla import COLUMNAS, filas_tabla
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from src.frontend.vistas.biseccion.modo_examen import crear_interruptor_examen, mostrar_accion_examen as examen_biseccion
from src.frontend.vistas.biseccion.resumen_criterio import mostrar_resumen
from src.frontend.vistas.regla_falsa.modo_examen import mostrar_accion_examen
from src.frontend.vistas.regla_falsa.resultado import mostrar_resultado
from src.frontend.vistas.regla_falsa.sugerencias import mostrar_sugerencias
from .contexto import opciones_glosa


class SalidaMetodosCerrados:
    """Mantiene la selección de fila, el reproductor y las marcas de la gráfica en sincronía."""

    def __init__(self, vista):
        self.vista = vista
        self.reproductor = self.tabla = self.fila = self.datos = None

    def mostrar(self, datos: dict, *, puntero: bool = False, velocidad: str | None = None) -> None:
        """Presenta el resultado completo y el procedimiento si hay una entrada interpretable."""
        self.datos = datos
        respuesta = datos["resultado"]
        biseccion = datos["metodo"] == BISECCION
        with self.vista.contenedor_resultados:
            self._mostrar_candidato(datos)
            if biseccion:
                self.vista.interruptor_examen = crear_interruptor_examen(self.vista) if respuesta.get("iteraciones") else None
                mostrar_resumen(self.vista, respuesta, self.vista.interruptor_examen,
                                puntero=puntero, candidato=self.vista.candidato_activo)
            else:
                mostrar_resultado(self.vista, respuesta, datos.get("ampliado"), candidato=self.vista.candidato_activo)
                if self.vista.candidato_activo is None:
                    mostrar_sugerencias(self.vista, datos)
            if datos["aviso_grafica"]:
                ui.label(datos["aviso_grafica"]).classes("text-sm texto-advertencia")
        if respuesta.get("entrada") or not biseccion:
            self._montar_traza(datos, velocidad)
        else:
            self.vista.grafica.mostrar(datos)

    def _mostrar_candidato(self, datos: dict) -> None:
        candidato = self.vista.candidato_activo
        if candidato is None:
            return
        ui.label(f"Resultado de {candidato}").classes("text-lg font-semibold texto-principal")
        informe = datos.get("informe_continuidad")
        if informe is not None and not datos["resultado"].get("informe_continuidad"):
            mostrar_informe_continuidad(informe, "texto-principal")

    def retirar(self) -> None:
        """Detiene la reproducción antes de eliminar los controles del resultado anterior."""
        if self.reproductor is not None:
            self.reproductor.detener()
        self.reproductor = self.tabla = self.fila = self.datos = None
        self.vista.contenedor_resultados.clear()
        self.vista.contenedor_procedimiento.clear()

    def _montar_traza(self, datos: dict, velocidad: str | None) -> None:
        respuesta = datos["resultado"]
        pasos, grupos = _pasos(datos)
        opciones = {"sin_movimiento": True, "titulo": "Procedimiento de " + METODOS[datos["metodo"]]}
        opciones.update(opciones_glosa(self, datos, pasos))
        self.reproductor = ReproductorPasos(
            pasos, grupos, lambda paso, contenedor: self._mostrar_paso(datos, paso, contenedor),
            "metodos-cerrados", opciones,
        )
        if velocidad is not None:
            self.reproductor.velocidad = velocidad
        if respuesta.get("iteraciones") or datos["metodo"] != BISECCION:
            self._montar_tabla(datos)
        with self.vista.contenedor_procedimiento:
            self.reproductor.construir()

    def _montar_tabla(self, datos: dict) -> None:
        respuesta = datos["resultado"]
        examen = self.vista.interruptor_examen
        biseccion = datos["metodo"] == BISECCION
        preparar = (lambda filas, completo: _filas_biseccion(filas, completo, examen, respuesta["estado"])) if biseccion else (
            lambda filas, completo: (COLUMNAS, filas_tabla(filas, completo)))
        formato = FormatoTablaRaices(
            "Elige una fila para ver sus datos en la gráfica y el procedimiento.",
            "Tabla de iteraciones con desplazamiento horizontal", "metodos-cerrados-tabla", preparar,
        )
        preferencias = (examen,) if biseccion and examen is not None else ()
        with self.vista.contenedor_resultados:
            self.tabla = TablaRaicesSeleccionable(
                respuesta["iteraciones"], self.reproductor.ir_a, formato, preferencias=preferencias,
            )
            self.tabla.construir()

    def _mostrar_paso(self, datos: dict, paso, contenedor) -> None:
        if self.datos is not datos:
            return
        self.fila = paso.cuerpo
        self.vista.grafica.mostrar(datos, self.fila, inicial=paso.tipo == "planteamiento")
        if self.tabla is not None:
            self.tabla.seleccionar(self.fila)
        with contenedor:
            _renderizar_paso(datos, paso, self.vista.interruptor_examen)
        self.vista.panel_ia.limpiar_foco_explicacion()
        self.vista.panel_ia.limpiar_contexto()
        actualizar_contexto(self.vista)


def _filas_biseccion(filas: tuple, completo: bool, examen, estado: str) -> tuple:
    columnas = presentacion_biseccion.COLUMNAS
    valores = presentacion_biseccion.filas_tabla({"iteraciones": filas}, completo)
    if examen is not None and examen.value:
        columnas += COLUMNAS_EXAMEN
        for visible, original in zip(valores, filas):
            visible.update(datos_examen(original, estado))
    return columnas, valores


def _pasos(datos: dict) -> tuple:
    respuesta = datos["resultado"]
    if datos["metodo"] == BISECCION:
        return presentacion_biseccion.construir_pasos(respuesta)
    ampliado = datos.get("ampliado")
    if ampliado is not None:
        return construir_pasos_configurados({**ampliado, "resultado": respuesta})
    return construir_pasos(respuesta)


def _renderizar_paso(datos: dict, paso, examen) -> None:
    if paso.cuerpo is None:
        entrada = datos["resultado"].get("entrada")
        if paso.tipo == "planteamiento" and entrada:
            _renderizar_expresion(entrada["expresion"])
        return
    biseccion = datos["metodo"] == BISECCION
    formulas = formulas_biseccion if biseccion else formulas_regla_falsa
    for formula in formulas(paso.cuerpo):
        renderizar_latex(formula, vigilar_region=True)
    if examen is not None:
        if biseccion:
            examen_biseccion(examen, paso.cuerpo, datos["resultado"]["estado"])
        else:
            mostrar_accion_examen(examen, paso.cuerpo, datos["resultado"])


def _renderizar_expresion(expresion: str) -> None:
    try:
        formula = formatear_expresion(expresion)["latex"]
    except ValueError:
        return
    renderizar_latex(formula, vigilar_region=True)
