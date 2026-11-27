"""Ejemplos de demostracion geometrica para Transformaciones Lineales."""
from __future__ import annotations

EJEMPLOS_TRANSFORMACIONES = [
    {
        "nombre": "Identidad 2D",
        "descripcion": "T(x)=x. Biyectiva, rango=2, nulidad=0.",
        "matriz_transformacion": [["1", "0"], ["0", "1"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "Reflexión eje x",
        "descripcion": "T refleja en el eje x. Biyectiva.",
        "matriz_transformacion": [["1", "0"], ["0", "-1"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "Proyección sobre eje x",
        "descripcion": "T proyecta en el eje x. No inyectiva (ker != {0}). Núcleo = span{e2}.",
        "matriz_transformacion": [["1", "0"], ["0", "0"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "Rotación 90°",
        "descripcion": "T rota vectores 90 grados en sentido antihorario. Biyectiva.",
        "matriz_transformacion": [["0", "-1"], ["1", "0"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "ℝ² → ℝ³ (inyectiva)",
        "descripcion": "Inmersión de ℝ² en ℝ³. Inyectiva, no sobreyectiva.",
        "matriz_transformacion": [["1", "0"], ["0", "1"], ["0", "0"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "ℝ³ → ℝ² (sobreyectiva)",
        "descripcion": "Proyección de ℝ³ en ℝ². Sobreyectiva, nulidad >= 1.",
        "matriz_transformacion": [["1", "0", "0"], ["0", "1", "0"]],
        "nombres_variables": ["x1", "x2", "x3"],
    },
]
