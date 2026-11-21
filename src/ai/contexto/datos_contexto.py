"""Datos del ejercicio y del paso enfocado que se comparten con Glosa."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CapturaPaso:
    """Agrupa las filas, columnas y detalle opcional de un paso enfocado."""

    filas_antes: dict[str, list[str]] = field(default_factory=dict)
    filas_despues: dict[str, list[str]] = field(default_factory=dict)
    columnas: tuple[int, int] | None = None
    detalle: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "filas_antes", self.filas_antes or {})
        object.__setattr__(self, "filas_despues", self.filas_despues or {})


@dataclass(frozen=True)
class ReferenciaPaso:
    """Identifica un paso y conserva su captura para la explicación pedagógica."""

    indice: int = 0
    total: int = 0
    tipo: str = ""
    operacion: str = ""
    captura: CapturaPaso = field(default_factory=CapturaPaso)


@dataclass
class EstadoContexto:
    """Agrupa resultado, foco, nota y estado de vigencia del ejercicio."""

    resultado: dict[str, Any] | None = None
    foco: ReferenciaPaso | None = None
    nota_ventana: str | None = None
    desactualizado: bool = False
    vacio: bool = False


@dataclass
class ContextoIA:
    """Describe la herramienta y sus entradas con un estado agrupado independiente."""

    herramienta: str = ""
    vista: str = ""
    etiqueta: str = ""
    entrada: dict[str, Any] = field(default_factory=dict)
    estado: EstadoContexto = field(default_factory=EstadoContexto)

    def __post_init__(self) -> None:
        if self.entrada is None:
            self.entrada = {}

    @property
    def resultado(self) -> dict[str, Any] | None:
        """Devuelve el resultado vigente del ejercicio."""
        return self.estado.resultado

    @resultado.setter
    def resultado(self, valor: dict[str, Any] | None) -> None:
        """Actualiza el resultado sin modificar las entradas."""
        self.estado.resultado = valor

    @property
    def foco(self) -> ReferenciaPaso | None:
        """Devuelve el paso seleccionado para explicación."""
        return self.estado.foco

    @foco.setter
    def foco(self, valor: ReferenciaPaso | None) -> None:
        """Sustituye la referencia al paso seleccionado."""
        self.estado.foco = valor

    @property
    def nota_ventana(self) -> str | None:
        """Devuelve la nota sobre la parte visible de las entradas."""
        return self.estado.nota_ventana

    @nota_ventana.setter
    def nota_ventana(self, valor: str | None) -> None:
        """Actualiza la nota de recorte visible."""
        self.estado.nota_ventana = valor

    @property
    def desactualizado(self) -> bool:
        """Indica si el resultado corresponde a entradas anteriores."""
        return self.estado.desactualizado

    @desactualizado.setter
    def desactualizado(self, valor: bool) -> None:
        """Registra la vigencia del resultado."""
        self.estado.desactualizado = valor

    @property
    def vacio(self) -> bool:
        """Indica si hay un ejercicio disponible para adjuntar."""
        return self.estado.vacio

    @vacio.setter
    def vacio(self, valor: bool) -> None:
        """Actualiza la disponibilidad del ejercicio."""
        self.estado.vacio = valor
