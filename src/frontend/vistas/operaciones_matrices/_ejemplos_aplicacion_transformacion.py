"""Ejemplos de matrices y coordenadas para explorar su aplicación exacta."""
EJEMPLOS_APLICACION = [
    {
        "nombre": "Identidad",
        "descripcion": "Conserva las coordenadas (3, 2).",
        "matriz_transformacion": [["1", "0"], ["0", "1"]],
        "vector_original": ["3", "2"],
    },
    {
        "nombre": "Escala",
        "descripcion": "Duplica la primera componente y triplica la segunda: (6, 6).",
        "matriz_transformacion": [["2", "0"], ["0", "3"]],
        "vector_original": ["3", "2"],
    },
    {
        "nombre": "Reflexión en eje x",
        "descripcion": "Invierte la segunda componente: (3, -2).",
        "matriz_transformacion": [["1", "0"], ["0", "-1"]],
        "vector_original": ["3", "2"],
    },
    {
        "nombre": "Rotación de 90°",
        "descripcion": "Gira en sentido antihorario con resultado exacto (-2, 3).",
        "matriz_transformacion": [["0", "-1"], ["1", "0"]],
        "vector_original": ["3", "2"],
    },
    {
        "nombre": "Fracciones",
        "descripcion": "Aplica A a (1/2, 1/3) y obtiene (4/3, 3/2).",
        "matriz_transformacion": [["2", "1"], ["1", "3"]],
        "vector_original": ["1/2", "1/3"],
    },
]
