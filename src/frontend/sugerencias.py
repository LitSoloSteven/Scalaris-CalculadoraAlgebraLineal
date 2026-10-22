"""Lógica de selección y emisión de sugerencias contextuales proactivas para Glosa."""
from dataclasses import dataclass, field
import os
from typing import Any

from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend import banderas
from src.frontend.catalogo_sugerencias import CATALOGO_SUGERENCIAS


@dataclass(frozen=True)
class CeldaInvalida:
    """Representa una celda con valor no numérico o inválido en la matriz."""

    etiqueta: str
    foco: tuple[int, int] | None = None


@dataclass(frozen=True)
class Senales:
    """Señales de estado de la herramienta activa emitidas hacia Glosa."""

    herramienta: str
    estado: str
    banderas: frozenset[str] = field(default_factory=frozenset)
    invalida: CeldaInvalida | None = None


@dataclass(frozen=True)
class Sugerencia:
    """Sugerencia lista para presentarse como cápsula interactiva."""

    identificador: str
    texto: str
    rol: str
    foco: tuple[int, int] | None = None


def glosa_configurada() -> bool:
    """Verifica si la clave de API para OpenRouter está configurada en el entorno."""
    return bool(os.getenv("OPENROUTER_API_KEY", "").strip())


def primera_celda_invalida(elementos: Any) -> CeldaInvalida | None:
    """Localiza la primera celda con entrada numérica inválida o no parseable."""
    celda = ValidadorMatriz.primera_celda_invalida(elementos)
    return CeldaInvalida(etiqueta=celda["etiqueta"], foco=celda["foco"]) if celda else None


def sugerencias_activas() -> bool:
    """Indica si el modo proactivo y el panel lateral de Glosa están activos."""
    return banderas.panel_lateral_habilitado() and banderas.proactivo_habilitado()


def _es_bandera_valida(herramienta: str, nombre_bandera: str, estado: str) -> bool:
    """Comprueba restricciones adicionales entre herramienta, bandera y estado."""
    if herramienta == "matrices" and nombre_bandera == "contiene_producto":
        return estado == "exito"
    if herramienta == "bases":
        return estado == "resultado"
    if herramienta == "romanos":
        return estado in ("exito", "error")
    return True


def _coincide_disparador(disparador: str, senales: Senales) -> bool:
    """Evalúa si el disparador coincide con el estado o banderas activos."""
    if disparador == senales.estado:
        return True
    if disparador.startswith("bandera_"):
        nombre_bandera = disparador[8:]
        if nombre_bandera in senales.banderas:
            return _es_bandera_valida(senales.herramienta, nombre_bandera, senales.estado)
    return False


def generar_candidatas(senales: Senales | None) -> list[Sugerencia]:
    """Genera la lista de todas las sugerencias candidatas para las señales dadas."""
    if not senales:
        return []

    candidatas: list[Sugerencia] = []

    if senales.estado == "sin_resultado" and senales.invalida:
        etiqueta = senales.invalida.etiqueta
        if len(etiqueta) > 24:
            etiqueta = etiqueta[:23] + "…"
        candidatas.append(
            Sugerencia(
                identificador=f"{senales.herramienta}.invalida",
                texto=f"¿Por qué {etiqueta} no es válido?",
                rol="especifica",
                foco=senales.invalida.foco,
            )
        )

    for herramienta, disparador, identificador, texto, rol in CATALOGO_SUGERENCIAS:
        if herramienta != senales.herramienta:
            continue
        if _coincide_disparador(disparador, senales):
            candidatas.append(Sugerencia(identificador=identificador, texto=texto, rol=rol))

    return candidatas


def seleccionar_sugerencias(candidatas: list[Sugerencia], limite: int) -> list[Sugerencia]:
    """Prioriza cápsulas específicas, de estado y de bandera, en ese orden, hasta el límite."""
    especificas = [candidata for candidata in candidatas if candidata.rol == "especifica"]
    estados = [candidata for candidata in candidatas if candidata.rol == "estado"]
    banderas = [candidata for candidata in candidatas if candidata.rol == "bandera"]

    seleccionadas: list[Sugerencia] = []
    seleccionadas.extend(especificas)

    prioridades = estados[:2] + banderas[:1] + estados[2:] + banderas[1:]
    for candidata in prioridades:
        if candidata not in seleccionadas:
            seleccionadas.append(candidata)

    return seleccionadas[:limite]


def sugerir(
    senales: Senales | None,
    *,
    limite: int = 3,
    incluir_especificas: bool = True,
) -> list[Sugerencia]:
    """Genera las mejores sugerencias a mostrar según las señales actuales de la vista."""
    candidatas = generar_candidatas(senales)
    if not incluir_especificas:
        candidatas = [candidata for candidata in candidatas if candidata.rol != "especifica"]
    return seleccionar_sugerencias(candidatas, limite)
