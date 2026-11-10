"""Textos compartidos de diagnósticos y sugerencias para vista, copia y explicación."""
from .presentacion import numero
from src.frontend.controladores.formato_numerico_raices import texto_intervalo

_ETAPAS = {"sintaxis": "Análisis de sintaxis", "extremos": "Evaluación de extremos",
           "estructura": "Análisis estructural", "iteracion": "Evaluación de punto medio",
           "capacidad": "Capacidad de representación numérica"}


def detalles_diagnostico(respuesta: dict) -> tuple[tuple[str, str], ...]:
    """Describe contexto y última fila válida sin recalcular ni atribuir ubicaciones evaluadas."""
    return _detalles_contexto(respuesta) + _detalles_discontinuidad(respuesta)


def _detalles_contexto(respuesta: dict) -> tuple[tuple[str, str], ...]:
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


def _detalles_discontinuidad(respuesta: dict) -> tuple[tuple[str, str], ...]:
    evidencia = (respuesta.get("diagnostico") or {}).get("evidencia_discontinuidad")
    if evidencia is None:
        return ()
    return (("Intervalo sospechoso según la traza", texto_intervalo(evidencia["intervalo"])),
            ("Ancho al inicio de la ventana", numero(evidencia["ancho_referencia"], True)),
            ("Mayor magnitud de los extremos iniciales", numero(evidencia["escala_inicial"], True)),
            ("Menor magnitud vecinal de referencia", numero(evidencia["magnitud_vecinal_referencia"], True)),
            ("Menor magnitud de los extremos finales", numero(evidencia["magnitud_vecinal_final"], True)),
            ("Menor residuo reciente", numero(evidencia["residuo_reciente_minimo"], True)))


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
