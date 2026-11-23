"""Mensajes, etiquetas y construcciones textuales para Espacios y subespacios."""

MODO_GENERADORES = "generadores"
NOMBRES_MODOS = {
    MODO_GENERADORES: "Generadores",
}
AYUDA_MODOS = {
    MODO_GENERADORES: (
        "Define generadores columna en ℝⁿ para determinar base, dimensión, "
        "propiedades de espacio vectorial y representación geométrica."
    ),
}

TITULO_PAGINA = "Espacios y subespacios"
ESTADO_INICIAL = "Escribe los generadores o carga el ejemplo para analizar el subespacio."
ESTADO_EDICION = "Analiza el conjunto para actualizar el resultado."
ESTADO_CALCULO = "Analizando el conjunto generado…"
ETIQUETA_EJEMPLO = (
    "Ejemplo cargado: tres generadores en ℝ³ que generan un plano de dimensión 2."
)

VEREDICTO_SUBESPACIO_CERO = "Subespacio cero"
SUBTITULO_SUBESPACIO_CERO = "W = {0}, con base vacía ∅ y dimensión 0."
PLANTILLA_VEREDICTO_SUBESPACIO = (
    "Es un espacio vectorial con las operaciones usuales y un subespacio de ℝ{superindice}"
)
PLANTILLA_HERENCIA_AXIOMAS = (
    "Por estar incluido en ℝ{superindice} con la suma y el producto por escalar usuales, "
    "el resto de los axiomas de espacio vectorial se heredan del ambiente."
)

TITULO_TEOREMA_CRITERIOS = "Criterios de subespacio (explicación del teorema)"
SUBTITULO_TEOREMA_CRITERIOS = (
    "Cada botón abre la demostración general sobre la familia capturada W = {Va : a ∈ ℝᵐ}."
)
TITULO_VERIFICACION_MOTOR = "Verificaciones del cálculo del motor"
NOTA_DIMENSION_SUPERIOR = (
    "La representación geométrica se limita a tres coordenadas; el resultado algebraico "
    "exacto permanece completo en el espacio ambiente."
)
NOTA_GRAFICA_NO_DISPONIBLE = (
    "La gráfica no está disponible porque las coordenadas no admiten una escala visual fiable; "
    "se conserva el resultado algebraico exacto."
)
NOTA_GENERA_AMBIENTE = "La base genera todo el espacio ambiente ℝ³."

MENSAJE_CAPTURA_VACIA = (
    "Escribe valores numéricos en los generadores, carga el ejemplo o introduce 0 "
    "de forma explícita para analizar el subespacio cero."
)
PLANTILLA_COMPONENTE_VACIA = (
    "Completa la componente {componente} del vector {etiqueta}; si vale cero, escribe 0."
)
MENSAJE_CALCULO_NO_VERIFICADO = (
    "No se pudo verificar el análisis exacto del conjunto. Revisa la entrada o inténtalo de nuevo."
)

EJEMPLO_GENERADORES: dict[str, list[str]] = {
    "v_1": ["1", "0", "1"],
    "v_2": ["0", "1", "1"],
    "v_3": ["1", "1", "2"],
}

CRITERIOS_TEOREMA_GENERADORES: tuple[dict[str, str], ...] = (
    {
        "clave": "origen",
        "titulo": "Contiene al vector cero",
        "estado": "Cumple",
        "origen": "teorema",
        "resumen": (
            "Con coeficientes todos nulos (a = 0 en ℝᵐ), la combinación lineal "
            "produce el vector cero del ambiente."
        ),
        "formula_latex": r"V\mathbf{0} = \mathbf{0} \in W",
    },
    {
        "clave": "suma",
        "titulo": "Cerrado bajo la suma",
        "estado": "Cumple",
        "origen": "teorema",
        "resumen": (
            "La suma de dos combinaciones lineales de los mismos generadores "
            "se agrupa en otra combinación lineal de ellos."
        ),
        "formula_latex": r"V\mathbf{a} + V\mathbf{c} = V(\mathbf{a} + \mathbf{c}) \in W",
    },
    {
        "clave": "escalar",
        "titulo": "Cerrado bajo el producto por escalar",
        "estado": "Cumple",
        "origen": "teorema",
        "resumen": (
            "Multiplicar una combinación lineal por un escalar real escala sus "
            "coeficientes y permanece dentro de W."
        ),
        "formula_latex": r"\lambda(V\mathbf{a}) = V(\lambda\mathbf{a}) \in W",
    },
)

_SUPERINDICES = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def superindice_dimension(dimension: int) -> str:
    """Convierte un entero positivo de dimensión en dígitos en superíndice."""
    return str(dimension).translate(_SUPERINDICES)


def texto_veredicto_subespacio(dimension_ambiente: int) -> str:
    """Devuelve el veredicto unificado de espacio vectorial y subespacio en ℝⁿ."""
    return PLANTILLA_VEREDICTO_SUBESPACIO.format(
        superindice=superindice_dimension(dimension_ambiente)
    )


def texto_herencia_axiomas(dimension_ambiente: int) -> str:
    """Explica la herencia del resto de axiomas desde el espacio ambiente ℝⁿ."""
    return PLANTILLA_HERENCIA_AXIOMAS.format(
        superindice=superindice_dimension(dimension_ambiente)
    )
