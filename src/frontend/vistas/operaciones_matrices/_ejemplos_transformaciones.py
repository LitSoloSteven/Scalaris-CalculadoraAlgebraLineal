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
        "nombre": "Reflexion eje x",
        "descripcion": "T reflejan en el eje x. Biyectiva.",
        "matriz_transformacion": [["1", "0"], ["0", "-1"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "Proyeccion sobre eje x",
        "descripcion": "T proyecta en el eje x. No inyectiva (ker != {0}). Nucleo = span{e2}.",
        "matriz_transformacion": [["1", "0"], ["0", "0"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "Rotacion 90 deg",
        "descripcion": "T rota vectores 90 grados en sentido antihorario. Biyectiva.",
        "matriz_transformacion": [["0", "-1"], ["1", "0"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "R2 -> R3 (inyectiva)",
        "descripcion": "Embedding de R2 en R3. Inyectiva, no sobreyectiva.",
        "matriz_transformacion": [["1", "0"], ["0", "1"], ["0", "0"]],
        "nombres_variables": ["x1", "x2"],
    },
    {
        "nombre": "R3 -> R2 (sobreyectiva)",
        "descripcion": "Proyeccion de R3 en R2. Sobreyectiva, nulidad >= 1.",
        "matriz_transformacion": [["1", "0", "0"], ["0", "1", "0"]],
        "nombres_variables": ["x1", "x2", "x3"],
    },
]
