"""Adaptación de la traza exacta, el teorema y las verificaciones al reproductor."""
from __future__ import annotations

from fractions import Fraction
import html

from nicegui import ui

from src.frontend.componentes.reproductor_pasos.formato.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.formato.html_tablas import html_tabla_aumentada
from src.frontend.componentes.reproductor_pasos.interfaz.reproductor import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.nucleo.modelo import GrupoReproductor, PasoReproductor
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    TITULO_VERIFICACION_MOTOR,
    VEREDICTO_SUBESPACIO_CERO,
)

_LIMITE_FRACCION_TABLA = 4000
_AYUDA_REPRODUCTOR = (
    "Las fases separan la reducción de columnas, la lectura de la base, "
    "la demostración del teorema y las verificaciones numéricas del motor.",
)
_LEYENDA_TIPOS = (
    "inicial", "intercambio", "pivote", "eliminacion",
    "normalizacion", "final", "planteamiento", "verificacion",
)


class _MatrizTabla:
    """Adaptador de matriz serializada que conserva racionales extensos sin desbordar."""

    def __init__(self, datos_matriz: dict) -> None:
        self.filas = int(datos_matriz["filas"])
        self.columnas = int(datos_matriz["columnas"])
        self._celdas = tuple(
            tuple(_convertir_celda_tabla(celda) for celda in fila)
            for fila in datos_matriz["datos"]
        )

    def obtener(self, fila: int, columna: int):
        """Devuelve el valor de la celda listo para formatear en la tabla."""
        return self._celdas[fila][columna]


def _convertir_celda_tabla(celda: object) -> Fraction | str:
    texto = str(celda)
    if len(texto) > _LIMITE_FRACCION_TABLA:
        return texto
    try:
        return Fraction(texto)
    except (ValueError, ZeroDivisionError):
        return texto


def crear_reproductor_subespacios(resultado: dict) -> tuple[ReproductorPasos, dict[str, int]]:
    """Construye el reproductor completo y devuelve los índices de cada criterio."""
    pasos: list[PasoReproductor] = []
    grupos: list[GrupoReproductor] = []
    _agregar_grupo_reduccion(resultado, pasos, grupos)
    _agregar_grupo_base(resultado, pasos, grupos)
    indices_criterios = _agregar_grupo_teorema(resultado, pasos, grupos)
    _agregar_grupo_verificaciones(resultado, pasos, grupos)
    total = len(pasos)
    pasos_completos = tuple(_completar_total_paso(paso, total) for paso in pasos)
    reproductor = ReproductorPasos(
        pasos_completos,
        tuple(grupos),
        _renderizar_cuerpo_paso,
        "espacios-subespacios",
        {"sin_movimiento": True, "lineas_ayuda": _AYUDA_REPRODUCTOR, "tipos_leyenda": _LEYENDA_TIPOS},
    )
    return reproductor, indices_criterios


def _completar_total_paso(paso: PasoReproductor, total: int) -> PasoReproductor:
    metadatos = dict(paso.meta_explicar or {})
    metadatos["total"] = total
    return PasoReproductor(
        indice=paso.indice, tipo=paso.tipo, descripcion=paso.descripcion, explicacion=paso.explicacion,
        indice_grupo=paso.indice_grupo, cuerpo=paso.cuerpo, etiqueta_tipo=paso.etiqueta_tipo, meta_explicar=metadatos,
    )


def _agregar_grupo_reduccion(
    resultado: dict, pasos: list[PasoReproductor], grupos: list[GrupoReproductor]
) -> None:
    traza = resultado.get("pasos") or ()
    if not traza:
        return
    etiquetas = tuple(resultado.get("etiquetas_generadores") or ())
    indice_grupo = len(grupos)
    indices = []
    for evento in traza:
        indice = len(pasos)
        indices.append(indice)
        pasos.append(_crear_paso_reduccion(evento, etiquetas, indice, indice_grupo))
    grupos.append(GrupoReproductor(
        titulo="Planteamiento y reducción de generadores", resumen=f"{len(indices)} pasos",
        tipo="eliminacion", indices_pasos=tuple(indices),
    ))


def _crear_paso_reduccion(
    evento: dict, etiquetas: tuple[str, ...], indice: int, indice_grupo: int
) -> PasoReproductor:
    tipo = str(evento.get("tipo") or "otro")
    datos = evento.get("datos") or {}
    descripcion, explicacion = _describir_evento_reduccion(tipo, datos)
    tabla = _tabla_evento_reduccion(evento.get("matriz"), etiquetas, tipo, datos)
    metadatos = {"indice": indice + 1, "tipo": tipo, "operacion": descripcion, "origen": "reduccion"}
    return PasoReproductor(
        indice=indice, tipo=tipo, descripcion=descripcion, explicacion=explicacion,
        indice_grupo=indice_grupo, cuerpo=("tabla", tabla), meta_explicar=metadatos,
    )


def _describir_evento_reduccion(tipo: str, datos: dict) -> tuple[str, str]:
    fila = int(datos.get("fila", 0)) + 1
    if tipo == "inicial":
        return "Matriz de generadores V", "Cada generador capturado forma una columna de la matriz V."
    if tipo == "intercambio":
        otra = int(datos.get("seleccionada", 0)) + 1
        return f"Intercambio F{fila} ↔ F{otra}", "Permutamos filas para ubicar un pivote distinto de cero."
    if tipo == "pivote":
        columna = int(datos.get("columna", 0)) + 1
        return f"Pivote en fila {fila}, columna {columna}", "Seleccionamos este pivote para reducir las filas restantes."
    if tipo == "eliminacion":
        fila_pivote = int(datos.get("fila_pivote", 0)) + 1
        return f"Eliminación en F{fila}", f"Anulamos la entrada en F{fila} usando la fila pivote F{fila_pivote}."
    if tipo == "normalizacion":
        return f"Normalización de F{fila}", "Dividimos la fila por su pivote para dejar 1 principal."
    return "Operación de reducción", "Aplicamos una transformación elemental por filas."


def _tabla_evento_reduccion(
    matriz: dict | None, etiquetas: tuple[str, ...], tipo: str, datos: dict
) -> str:
    if not matriz:
        return ""
    adaptador = _MatrizTabla(matriz)
    pivote = (datos["fila"], datos["columna"]) if tipo == "pivote" and "fila" in datos and "columna" in datos else None
    intercambio = (datos["fila"], datos["seleccionada"]) if tipo == "intercambio" and "fila" in datos else ()
    cambiadas = (datos["fila"],) if tipo in ("eliminacion", "normalizacion") and "fila" in datos else ()
    return html_tabla_aumentada(adaptador, adaptador.columnas, {
        "etiquetas_izquierda": etiquetas, "etiquetas_derecha": (),
        "pivote": pivote, "filas_intercambio": intercambio, "filas_cambiadas": cambiadas,
    })


def _agregar_grupo_base(
    resultado: dict, pasos: list[PasoReproductor], grupos: list[GrupoReproductor]
) -> None:
    indice = len(pasos)
    indice_grupo = len(grupos)
    es_cero = bool(resultado.get("es_subespacio_cero"))
    descripcion = "Base vacía del subespacio cero" if es_cero else "Lectura de la base en las columnas originales"
    explicacion = (
        "No hay columnas pivote porque todos los generadores son nulos."
        if es_cero
        else "Los pivotes de la matriz reducida señalan qué columnas originales integran la base."
    )
    pasos.append(PasoReproductor(
        indice=indice, tipo="final", etiqueta_tipo="Base", descripcion=descripcion,
        explicacion=explicacion, indice_grupo=indice_grupo, cuerpo=("base", resultado),
        meta_explicar={"indice": indice + 1, "tipo": "final", "operacion": descripcion, "origen": "base"},
    ))
    grupos.append(GrupoReproductor(
        titulo="Lectura de la base y dependencias", resumen="1 paso", tipo="final", indices_pasos=(indice,),
    ))


def _agregar_grupo_teorema(
    resultado: dict, pasos: list[PasoReproductor], grupos: list[GrupoReproductor]
) -> dict[str, int]:
    criterios = resultado.get("criterios") or ()
    indice_grupo = len(grupos)
    indices_criterios: dict[str, int] = {}
    indices_pasos: list[int] = []
    for criterio in criterios:
        indice = len(pasos)
        indices_pasos.append(indice)
        indices_criterios[criterio["clave"]] = indice
        herencia = resultado.get("herencia_axiomas", "") if criterio["clave"] == "escalar" else ""
        pasos.append(PasoReproductor(
            indice=indice, tipo="planteamiento", etiqueta_tipo="Teorema",
            descripcion=f"Explicación del teorema: {criterio['titulo']}", explicacion=criterio["resumen"],
            indice_grupo=indice_grupo, cuerpo=("teorema", criterio, herencia),
            meta_explicar={"indice": indice + 1, "tipo": "planteamiento", "operacion": criterio["titulo"], "origen": "teorema"},
        ))
    if indices_pasos:
        grupos.append(GrupoReproductor(
            titulo="Demostración del teorema (operaciones usuales)",
            resumen=f"{len(indices_pasos)} criterios", tipo="planteamiento", indices_pasos=tuple(indices_pasos),
        ))
    return indices_criterios


def _agregar_grupo_verificaciones(
    resultado: dict, pasos: list[PasoReproductor], grupos: list[GrupoReproductor]
) -> None:
    comprobaciones = resultado.get("comprobaciones") or ()
    if not comprobaciones:
        return
    indice = len(pasos)
    indice_grupo = len(grupos)
    pasos.append(PasoReproductor(
        indice=indice, tipo="verificacion", etiqueta_tipo="Motor",
        descripcion=TITULO_VERIFICACION_MOTOR,
        explicacion="Resultados de consistencia exacta devueltos por el motor sobre la matriz capturada.",
        indice_grupo=indice_grupo, cuerpo=("motor", comprobaciones),
        meta_explicar={"indice": indice + 1, "tipo": "verificacion", "operacion": TITULO_VERIFICACION_MOTOR, "origen": "motor"},
    ))
    grupos.append(GrupoReproductor(
        titulo=TITULO_VERIFICACION_MOTOR, resumen="1 resumen", tipo="verificacion", indices_pasos=(indice,),
    ))


def _renderizar_cuerpo_paso(paso: PasoReproductor, contenedor) -> None:
    cuerpo = paso.cuerpo
    if not isinstance(cuerpo, tuple):
        return
    clase = cuerpo[0]
    with contenedor, ui.column().classes("w-full gap-3"):
        if clase == "tabla" and cuerpo[1]:
            ui.html(cuerpo[1]).classes("w-full")
        elif clase == "base":
            _renderizar_cuerpo_base(cuerpo[1])
        elif clase == "teorema":
            _renderizar_cuerpo_teorema(cuerpo[1], cuerpo[2])
        elif clase == "motor":
            _renderizar_cuerpo_motor(cuerpo[1])


def _renderizar_tabla_resumen(titulo: str, matriz: dict | None, etiquetas: tuple[str, ...]) -> None:
    if not matriz:
        return
    adaptador = _MatrizTabla(matriz)
    ui.label(titulo).classes("text-sm font-semibold texto-principal")
    ui.html(html_tabla_aumentada(adaptador, adaptador.columnas, {
        "etiquetas_izquierda": etiquetas, "etiquetas_derecha": (),
    })).classes("w-full")


def _renderizar_cuerpo_base(resultado: dict) -> None:
    etiquetas = tuple(resultado.get("etiquetas_generadores") or ())
    _renderizar_tabla_resumen("Forma escalonada reducida (columnas pivote)", resultado.get("matriz_reducida"), etiquetas)
    if resultado.get("es_subespacio_cero"):
        ui.label(f"{VEREDICTO_SUBESPACIO_CERO}: W = {{0}} y base vacía ∅.").classes("texto-principal text-sm")
        return
    _renderizar_tabla_resumen("Matriz original de generadores", resultado.get("matriz_original"), etiquetas)
    base_etiquetas = ", ".join(resultado.get("etiquetas_generadores_base") or ())
    ui.label(f"Base extraída de la matriz original: {base_etiquetas}").classes("subespacios-numero texto-principal text-sm font-semibold")
    for dependencia in resultado.get("dependencias") or ():
        if dependencia.get("respaldada") and dependencia.get("latex"):
            renderizar_latex(dependencia["latex"], vigilar_region=True)
        else:
            ui.label(dependencia["texto"]).classes("subespacios-numero texto-secundario text-sm")


def _renderizar_cuerpo_teorema(criterio: dict, herencia: str) -> None:
    ui.label("Explicación del teorema (operaciones usuales)").classes("text-xs font-semibold texto-secundario uppercase")
    ui.label(criterio["resumen"]).classes("texto-principal text-sm")
    renderizar_latex(criterio["formula_latex"], vigilar_region=True)
    if herencia:
        ui.label(herencia).classes("texto-secundario text-sm")


def _renderizar_cuerpo_motor(comprobaciones: tuple[dict, ...]) -> None:
    ui.label("Verificaciones del cálculo del motor sobre los generadores capturados:").classes("texto-secundario text-sm")
    for elemento in comprobaciones:
        estado = "Cumple" if elemento.get("coincide") else "Error"
        ui.label(f"{estado}: {html.unescape(elemento.get('detalle', ''))}").classes("subespacios-numero texto-principal text-sm")
