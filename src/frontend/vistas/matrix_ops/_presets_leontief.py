"""Presets de demostracion para el Modelo de Insumo-Producto de Leontief."""
from __future__ import annotations

PRESETS_LEONTIEF = [
    {
        "nombre": "2 Sectores (simple)",
        "descripcion": "Economía de 2 sectores viable con solución entera.",
        "sectores": ["Agricultura", "Industria"],
        "C": [["0.2", "0.3"], ["0.4", "0.1"]],
        "d": ["120", "80"],
    },
    {
        "nombre": "3 Sectores",
        "descripcion": "Economía completa de 3 sectores con Hawkins-Simon ✓.",
        "sectores": ["Agricultura", "Industria", "Servicios"],
        "C": [["0.1", "0.2", "0.1"], ["0.2", "0.3", "0.2"], ["0.1", "0.1", "0.3"]],
        "d": ["100", "200", "150"],
    },
    {
        "nombre": "Inviable (H-S falla)",
        "descripcion": "Coeficientes excesivos: no satisface Hawkins-Simon.",
        "sectores": ["Sector A", "Sector B"],
        "C": [["0.8", "0.5"], ["0.6", "0.9"]],
        "d": ["50", "50"],
    },
]
