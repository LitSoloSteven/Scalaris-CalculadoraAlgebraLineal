"""Formato de magnitudes y pasos a partir de la traza del motor."""
from src.backend.resolutores.raices.contrato_biseccion import ESTADO_DISCONTINUIDAD
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from .catalogo_criterios import condicion_criterio

COLUMNAS = (
    ("i", "i"), ("extremo_izquierdo", "a"), ("extremo_derecho", "b"),
    ("c", "c"), ("f_a", "f(a)"), ("f_b", "f(b)"), ("f_c", "f(c)"),
    ("ancho", "Ancho"), ("cota", "Cota en x"), ("residuo", "|f(c)|"),
    ("error_relativo", "Error relativo %"),
)
MOTIVOS = {
    "ancho_menor_que_E": "Ancho del intervalo menor que E",
    "raiz_exacta": "Evaluación igual a cero (aritmética aproximada)",
    "limite_iteraciones": "Límite de iteraciones; precisión no alcanzada",
    "estancamiento": "Límite de representación numérica; precisión no alcanzada",
}


def numero(valor, completo: bool = False) -> str:
    """Formatea números con hasta 17 cifras para inspección, sin alterar el cálculo."""
    if valor is None:
        return "No disponible"
    return format(valor, ".17g" if completo else ".9g") if isinstance(valor, float) else str(valor)


def filas_tabla(respuesta: dict, completo: bool = False) -> list[dict]:
    """Entrega filas de texto con todas las métricas originales de la traza."""
    return [{clave: valor_columna(fila, clave, completo) for clave, _ in COLUMNAS}
            for fila in respuesta["iteraciones"]]


def valor_columna(fila: dict, clave: str, completo: bool = False) -> str:
    """Devuelve una métrica legible; en inspección usa el porcentaje numérico del motor."""
    relativo = fila.get("error_relativo_valor")
    if clave == "error_relativo" and completo and relativo is not None:
        return numero(relativo, True) + "%"
    return numero(fila[clave], completo)


def motivo(respuesta: dict) -> str:
    """Traduce el motivo de parada conservando el mensaje para estados sin traza."""
    diagnostico = respuesta.get("diagnostico") or {}
    return MOTIVOS.get(respuesta.get("motivo_parada"), diagnostico.get("mensaje_parada", respuesta["mensaje"]))


def construir_pasos(respuesta: dict) -> tuple[tuple, tuple]:
    """Adapta la traza al reproductor común, con planteamiento y cierre incluso sin iteraciones."""
    entrada = respuesta["entrada"]
    descripcion = f"f(x) = {entrada['expresion']} en [{numero(entrada['extremo_izquierdo'])}, {numero(entrada['extremo_derecho'])}]"
    criterio = respuesta.get("criterio_solicitado")
    explicacion_inicial = "La garantía requiere continuidad en todo el intervalo y cambio de signo, salvo raíz en un extremo."
    explicacion_inicial += f" Unidad trigonométrica: {entrada.get('unidad_angular', 'radianes')}."
    if criterio:
        explicacion_inicial += " " + condicion_criterio(criterio["tipo"], criterio["parametro"])
    pasos = [PasoReproductor(0, "planteamiento", descripcion, explicacion_inicial, cuerpo=None)]
    for fila in respuesta["iteraciones"]:
        explicacion = _explicar_iteracion(fila, respuesta)
        pasos.append(PasoReproductor(len(pasos), "division", f"Iteración {fila['i']}: c = (a + b) / 2 = {numero(fila['c'])}",
                     explicacion, 1, fila, "Bisección"))
    pasos.append(_paso_final(respuesta, len(pasos)))
    total = len(pasos)
    pasos = [PasoReproductor(**{**paso.__dict__, "meta_explicar": {
        "indice": paso.indice + 1, "total": total, "tipo": paso.tipo,
        "operacion": paso.descripcion, "detalle": {"explicacion": paso.explicacion, "iteracion": paso.cuerpo},
    }}) for paso in pasos]
    grupos = (GrupoReproductor("Planteamiento", "Intervalo y continuidad", "planteamiento", (0,)),
              GrupoReproductor("Partición del intervalo", "Puntos medios y selección", "division", tuple(range(1, total - 1))),
              GrupoReproductor("Cierre", pasos[-1].descripcion, "final", (total - 1,)))
    return tuple(pasos), grupos


def _explicar_iteracion(fila: dict, respuesta: dict) -> str:
    if fila is respuesta["iteraciones"][-1] and respuesta["estado"] == ESTADO_DISCONTINUIDAD:
        return "Se registra la última muestra. El punto medio queda provisional por la sospecha de discontinuidad."
    if fila["f_c"] == 0:
        return "f(c) se evaluó como cero. El motor detiene la partición en este punto."
    if fila is respuesta["iteraciones"][-1] and respuesta["motivo_parada"] == "ancho_menor_que_E":
        return "El ancho ya es menor que E. Se devuelve el punto medio de este intervalo."
    if fila is respuesta["iteraciones"][-1] and respuesta["motivo_parada"] in {
            "relativo_menor_que_porcentaje", "residuo_menor_que_delta", "iteraciones_completadas"}:
        return motivo(respuesta) + " Se devuelve el punto medio sin realizar otra partición."
    return fila["explicacion"]


def _paso_final(respuesta: dict, indice: int) -> PasoReproductor:
    if respuesta["estado"] == "ERROR":
        contexto = respuesta.get("contexto_fallo") or {}
        abscisa = contexto.get("x_fallo")
        detalle = "Se conservan las filas válidas anteriores al fallo."
        if abscisa is not None:
            detalle = f"La evaluación falló en x = {numero(abscisa, True)}. " + detalle
        return PasoReproductor(indice, "final", respuesta["mensaje"], detalle, 2)
    if respuesta["estado"] == ESTADO_DISCONTINUIDAD:
        return PasoReproductor(indice, "final", respuesta["mensaje"],
                              motivo(respuesta) + " El punto medio queda como aproximación provisional.", 2)
    return PasoReproductor(indice, "final", motivo(respuesta),
                          "La cota en x depende del intervalo y la continuidad. El residuo no es una cota del error en x; "
                          "solo el criterio elegido determina la parada ordinaria.", 2)
