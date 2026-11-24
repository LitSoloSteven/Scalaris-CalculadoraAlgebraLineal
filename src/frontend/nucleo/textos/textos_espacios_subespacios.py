"""Mensajes, etiquetas y construcciones textuales para Espacios y subespacios."""

from .textos_espacio_vectorial import MODO_PERSONALIZADO, NOMBRE_MODO_PERSONALIZADO, VEREDICTOS

MODO_GENERADORES = "generadores"
MODO_RESTRICCIONES = "restricciones"
NOMBRES_MODOS = {
    MODO_GENERADORES: "Generadores",
    MODO_RESTRICCIONES: "Restricciones",
    MODO_PERSONALIZADO: NOMBRE_MODO_PERSONALIZADO,
}
AYUDA_MODOS = {
    MODO_GENERADORES: (
        "Define generadores columna en ℝⁿ para determinar base, dimensión, "
        "propiedades de espacio vectorial y representación geométrica."
    ),
    MODO_RESTRICCIONES: (
        "Define un sistema lineal Ax = b en ℝⁿ mediante matriz aumentada o ecuaciones "
        "para determinar si describe un subespacio, un conjunto afín o un conjunto vacío."
    ),
    MODO_PERSONALIZADO: "Define un conjunto en ℝⁿ y verifica los axiomas con operaciones polinómicas sobre ℝ.",
}

TITULO_PAGINA = "Espacios y subespacios"
ESTADO_INICIAL = "Escribe los generadores o carga el ejemplo para analizar el subespacio."
ESTADO_INICIAL_MODOS = {
    MODO_GENERADORES: ESTADO_INICIAL,
    MODO_RESTRICCIONES: "Escribe las ecuaciones de restricción o carga el ejemplo para analizar el conjunto.",
    MODO_PERSONALIZADO: "Completa el conjunto y las operaciones o carga un ejemplo.",
}
ESTADO_EDICION = "Analiza el conjunto para actualizar el resultado."
ESTADO_CALCULO = "Analizando el conjunto generado…"
ESTADO_CALCULO_MODOS = {
    MODO_GENERADORES: ESTADO_CALCULO,
    MODO_RESTRICCIONES: "Analizando el sistema de restricciones…",
    MODO_PERSONALIZADO: "Verificando los axiomas sobre ℝ…",
}
ETIQUETA_EJEMPLO = (
    "Ejemplo cargado: tres generadores en ℝ³ que generan un plano de dimensión 2."
)
ETIQUETA_EJEMPLO_RESTRICCIONES = (
    "Ejemplo cargado: plano afín en ℝ³ definido por -x1 - x2 + x3 = 1."
)

VEREDICTO_SUBESPACIO_CERO = "Subespacio cero"
SUBTITULO_SUBESPACIO_CERO = "W = {0}, con base vacía ∅ y dimensión 0."
PLANTILLA_VEREDICTO_SUBESPACIO = (
    "Es un espacio vectorial con las operaciones usuales y un subespacio de ℝ{superindice}"
)
PLANTILLA_VEREDICTO_NO_SUBESPACIO = (
    "No es espacio vectorial con las operaciones usuales ni subespacio de ℝ{superindice}"
)
VEREDICTO_CONJUNTO_VACIO = "Conjunto vacío"
SUBTITULO_CONJUNTO_VACIO = "El sistema es incompatible (W = ∅) y no contiene elementos."
PLANTILLA_HERENCIA_AXIOMAS = (
    "Por estar incluido en ℝ{superindice} con la suma y el producto por escalar usuales, "
    "el resto de los axiomas de espacio vectorial se heredan del ambiente."
)

TITULO_TEOREMA_CRITERIOS = "Criterios de subespacio (explicación del teorema)"
SUBTITULO_TEOREMA_CRITERIOS = (
    "Cada botón abre la demostración general sobre la familia capturada W = {Va : a ∈ ℝᵐ}."
)
SUBTITULO_TEOREMA_RESTRICCIONES_HOMOGENEO = (
    "Cada botón abre la demostración general sobre el núcleo homogéneo W = {x ∈ ℝⁿ : Ax = 0}."
)
SUBTITULO_TEOREMA_RESTRICCIONES_AFIN = (
    "Cada botón abre el contraejemplo explícito obtenido con la fila testigo y el punto particular p."
)
SUBTITULO_TEOREMA_RESTRICCIONES_VACIO = (
    "La ausencia del origen descarta que W = ∅ sea subespacio; suma y producto por escalar se cumplen vacuamente."
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
NOTA_CONJUNTO_VACIO = (
    "El conjunto es vacío (W = ∅); no existen vectores ni puntos que graficar."
)
NOTA_GENERA_AMBIENTE = "La base genera todo el espacio ambiente ℝ³."

ESTADO_CRITERIO_CUMPLE = "Cumple"
ESTADO_CRITERIO_NO_CUMPLE = "No cumple"
ESTADO_CRITERIO_VACUO = "Se cumple vacuamente"

MENSAJE_CAPTURA_VACIA = (
    "Escribe valores numéricos en los generadores, carga el ejemplo o introduce 0 "
    "de forma explícita para analizar el subespacio cero."
)
MENSAJE_RESTRICCIONES_VACIAS = (
    "Escribe valores numéricos en la matriz aumentada, carga el ejemplo o introduce 0 "
    "de forma explícita para analizar las restricciones."
)
MENSAJE_ECUACIONES_VACIAS = (
    "Escribe al menos una ecuación de restricción o carga el ejemplo para analizar el conjunto."
)
MENSAJE_SOLO_CONSTANTES = (
    "Incluye al menos una variable o escribe 0x1 para fijar la dimensión, por ejemplo 0x1 = 0 o 0x1 = 1."
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
EJEMPLO_RESTRICCIONES: dict[str, object] = {
    "dimension_ambiente": 3,
    "matriz_a": [["-1", "-1", "1"]],
    "vector_b": ["1"],
    "ecuaciones": "-x1 - x2 + x3 = 1",
}

CRITERIOS_TEOREMA_GENERADORES: tuple[dict[str, str], ...] = (
    {
        "clave": "origen",
        "titulo": "Contiene al vector cero",
        "estado": ESTADO_CRITERIO_CUMPLE,
        "clase_estado": "exito",
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
        "estado": ESTADO_CRITERIO_CUMPLE,
        "clase_estado": "exito",
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
        "estado": ESTADO_CRITERIO_CUMPLE,
        "clase_estado": "exito",
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


def texto_veredicto_no_subespacio(dimension_ambiente: int) -> str:
    """Devuelve el veredicto negativo unificado respecto de ℝⁿ y sus operaciones usuales."""
    return PLANTILLA_VEREDICTO_NO_SUBESPACIO.format(
        superindice=superindice_dimension(dimension_ambiente)
    )


def texto_herencia_axiomas(dimension_ambiente: int) -> str:
    """Explica la herencia del resto de axiomas desde el espacio ambiente ℝⁿ."""
    return PLANTILLA_HERENCIA_AXIOMAS.format(
        superindice=superindice_dimension(dimension_ambiente)
    )


PDF_ESTADOS_SUBESPACIOS = {
    "SUBESPACIO": "es espacio vectorial y subespacio",
    "AFIN_NO_SUBESPACIO": "conjunto afín fuera del origen (no es subespacio)",
    "VACIO_NO_SUBESPACIO": "conjunto vacío (no es subespacio)",
    "ESPACIO_VECTORIAL": VEREDICTOS[True],
    "NO_ESPACIO_VECTORIAL": VEREDICTOS[False],
    "CONJUNTO_VACIO": VEREDICTOS[False],
    "LIMITE_ARITMETICO": VEREDICTOS[None],
}
PDF_REGIONES_SUBESPACIOS = {
    "espacios_subespacios-axiomas": (
        "Comprobación de axiomas",
        "Se presenta el estado de cada axioma verificado sobre ℝ.",
    ),
    "espacios_subespacios-resumen": (
        "Clasificación y Resultado del Conjunto",
        "Se presenta el veredicto con las propiedades del conjunto o las operaciones utilizadas.",
    ),
    "espacios_subespacios-criterios": (
        "Resumen de Criterios de Subespacio",
        "Se presentan los tres criterios estructurales evaluados sobre el conjunto.",
    ),
    "espacios_subespacios-pruebas": (
        "Demostraciones y evidencia exacta",
        "Se presentan las pruebas, los certificados o los contraejemplos que respaldan las comprobaciones.",
    ),
    "espacios_subespacios-grafica": (
        "Representación Geométrica del Conjunto",
        "Se presenta la gráfica del subespacio o conjunto afín respecto del origen en tema claro.",
    ),
    "espacios_subespacios-comprobaciones": (
        "Verificaciones del Motor",
        "Se presentan las comprobaciones exactas devueltas por el motor sobre la captura vigente.",
    ),
    "espacios_subespacios-procedimiento": (
        "Paso Visible del Procedimiento",
        "Se presenta únicamente el paso visible del procedimiento, sin recorrer los demás pasos.",
    ),
}
