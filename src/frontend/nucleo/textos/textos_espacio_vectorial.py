"""Textos del análisis de espacios con operaciones polinómicas."""

MODO_PERSONALIZADO = "operaciones_personalizadas"
NOMBRE_MODO_PERSONALIZADO = "Operaciones personalizadas"
NOMBRES_OPERACIONES = {"suma": "Suma", "producto_escalar": "Producto por escalar"}
VEREDICTOS = {
    True: "Es espacio vectorial",
    False: "No es espacio vectorial",
    None: "No se pudo verificar",
}
ESTADOS_AXIOMA = {
    "CUMPLE": "Cumple",
    "NO_CUMPLE": "No cumple",
    "NO_VERIFICADO": "No verificado",
}
NOMBRES_AXIOMAS = {
    "CIERRE_SUMA": "Cierre bajo la suma",
    "CIERRE_ESCALAR": "Cierre bajo el producto por escalar",
    "CONMUTATIVIDAD_SUMA": "Conmutatividad de la suma",
    "ASOCIATIVIDAD_SUMA": "Asociatividad de la suma",
    "NEUTRO_SUMA": "Neutro aditivo",
    "INVERSO_SUMA": "Inverso aditivo",
    "IDENTIDAD_ESCALAR": "Identidad del escalar",
    "ASOCIATIVIDAD_ESCALAR": "Asociatividad del producto por escalar",
    "DISTRIBUTIVIDAD_VECTORES": "Distributividad sobre la suma de vectores",
    "DISTRIBUTIVIDAD_ESCALARES": "Distributividad sobre la suma de escalares",
}
