"""Textos compartidos de diagnósticos y sugerencias para vista, copia y explicación."""
from .presentacion import numero

_ETAPAS = {"sintaxis": "Análisis de sintaxis", "extremos": "Evaluación de extremos",
           "estructura": "Análisis estructural", "iteracion": "Evaluación de punto medio",
           "capacidad": "Capacidad de representación numérica"}


def detalles_diagnostico(respuesta: dict) -> tuple[tuple[str, str], ...]:
    """Describe contexto y última fila válida sin recalcular ni atribuir ubicaciones evaluadas."""
    contexto = respuesta.get("contexto_fallo")
    diagnostico = respuesta.get("diagnostico") or {}
    if contexto is None:
        if diagnostico.get("origen") == "estructura":
            return (("Diagnóstico estructural", diagnostico["mensaje"]),
                    ("Ubicación", "Restricción en el intervalo; no es una abscisa evaluada."))
        return ()
    datos = (("Etapa del fallo", _ETAPAS.get(contexto["etapa"], contexto["etapa"])),
             ("Código del diagnóstico", respuesta["codigo_diagnostico"]))
    if contexto.get("x_fallo") is not None:
        datos += (("Abscisa evaluada con fallo", numero(contexto["x_fallo"], True)),)
    else:
        datos += (("Abscisa evaluada con fallo", "No corresponde a una evaluación puntual."),)
    intervalo = contexto.get("intervalo_valido")
    if intervalo is not None:
        datos += (("Último intervalo con extremos válidos", texto_intervalo(intervalo)),)
    datos += _evaluaciones_extremos(contexto.get("extremos", ()))
    filas = respuesta.get("iteraciones", ())
    datos += (("Filas válidas conservadas", str(len(filas))),)
    if filas:
        ultima = filas[-1]
        datos += (("Última muestra válida c", numero(ultima["c"], True)),
                  ("Último valor válido f(c)", numero(ultima["f_c"], True)))
    return datos


def texto_intervalo(intervalo) -> str:
    """Formatea dos extremos del dominio con sus cifras internas, sin truncar valores."""
    return f"[{numero(intervalo[0], True)}, {numero(intervalo[1], True)}]"


def texto_sugerencia(sugerencia: dict) -> str:
    """Expone la propuesta del dominio sin convertirla en un cálculo aplicado."""
    mensaje = sugerencia["mensaje"]
    if "intervalo" in sugerencia:
        mensaje += " Intervalo sugerido: " + texto_intervalo(sugerencia["intervalo"]) + "."
    return mensaje


def _evaluaciones_extremos(evaluaciones) -> tuple[tuple[str, str], ...]:
    datos = ()
    for evaluacion in evaluaciones:
        etiqueta = "Extremo evaluado x = " + numero(evaluacion["abscisa"], True)
        valor = evaluacion["mensaje"] if evaluacion["codigo"] else "f(x) = " + numero(evaluacion["valor"], True)
        datos += ((etiqueta, valor),)
    return datos
