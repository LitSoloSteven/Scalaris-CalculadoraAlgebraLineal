"""Ejemplos de demostracion para el Modelo de Insumo-Producto de Leontief."""
from __future__ import annotations

EJEMPLOS_LEONTIEF = [
    {
        "nombre": "2 Sectores (simple)",
        "descripcion": "Economía de 2 sectores viable con solución entera.",
        "nombres_sectores": ["Agricultura", "Industria"],
        "matriz_coeficientes": [["0.2", "0.3"], ["0.4", "0.1"]],
        "vector_demanda": ["120", "80"],
    },
    {
        "nombre": "3 Sectores",
        "descripcion": "Economía completa de 3 sectores con Hawkins-Simon ✓.",
        "nombres_sectores": ["Agricultura", "Industria", "Servicios"],
        "matriz_coeficientes": [["0.1", "0.2", "0.1"], ["0.2", "0.3", "0.2"], ["0.1", "0.1", "0.3"]],
        "vector_demanda": ["100", "200", "150"],
    },
    {
        "nombre": "Inviable (H-S falla)",
        "descripcion": "Coeficientes excesivos: no satisface Hawkins-Simon.",
        "nombres_sectores": ["Sector A", "Sector B"],
        "matriz_coeficientes": [["0.8", "0.5"], ["0.6", "0.9"]],
        "vector_demanda": ["50", "50"],
    },
]
