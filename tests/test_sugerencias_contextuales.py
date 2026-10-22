import pytest

from src.frontend.sugerencias import (
    Senales,
    CeldaInvalida,
    Sugerencia,
    generar_candidatas,
    seleccionar_sugerencias,
    sugerir,
    primera_celda_invalida,
    glosa_configurada,
)

def test_sugerencias_limitadas_incluyen_especificas():
    """La selección respeta el límite e incluye sugerencias específicas."""
    # Senales con celda inválida y estado
    senales = Senales(
        herramienta="sistemas",
        estado="infinita",
        banderas=frozenset(["mas_ecuaciones_que_incognitas"]),
        invalida=CeldaInvalida("A[1,1]", (0, 0))
    )
    # incluir_especificas=True (por defecto)
    candidatas_con_especifica = generar_candidatas(senales)
    # Nota: invalida sólo genera candidato si estado == "sin_resultado" según el catálogo de sugerencias.py
    # Probemos con estado == "sin_resultado" para verificar incluir_especificas
    senales_vacias = Senales(
        herramienta="sistemas",
        estado="sin_resultado",
        invalida=CeldaInvalida("A[1,1]", (0, 0))
    )
    sugerencias_completas = sugerir(senales_vacias, limite=3, incluir_especificas=True)
    assert any(s.rol == "especifica" for s in sugerencias_completas)
    assert len(sugerencias_completas) <= 3
    
    sugerencias_sin_especifica = sugerir(senales_vacias, limite=3, incluir_especificas=False)
    assert not any(s.rol == "especifica" for s in sugerencias_sin_especifica)

def test_sugerencias_priorizan_estado_y_senal():
    """Estado y señales determinan el orden de sugerencias."""
    # Verificamos la función seleccionar_sugerencias que ordena specific > estado > flag
    candidatas = [
        Sugerencia(identificador="flag1", texto="Flag 1", rol="bandera"),
        Sugerencia(identificador="flag2", texto="Flag 2", rol="bandera"),
        Sugerencia(identificador="state1", texto="State 1", rol="estado"),
        Sugerencia(identificador="state2", texto="State 2", rol="estado"),
        Sugerencia(identificador="state3", texto="State 3", rol="estado"),
        Sugerencia(identificador="spec1", texto="Spec 1", rol="especifica"),
    ]
    # seleccionar_sugerencias toma specific primero, luego hasta 2 states, luego 1 flag, etc.
    seleccionadas = seleccionar_sugerencias(candidatas, limite=4)
    roles = [s.rol for s in seleccionadas]
    assert roles[0] == "especifica"
    assert roles[1] == "estado"
    assert roles[2] == "estado"
    assert roles[3] == "bandera"

def test_primera_celda_invalida():
    """El análisis identifica la primera coordenada inválida."""
    # items = iterable de (etiqueta, valor, foco|None)
    elementos_validos = [
        ("A[1,1]", "1/2", (0, 0)),
        ("A[1,2]", "0", (0, 1)),
        ("A[2,1]", "-3.5", (1, 0)),
    ]
    assert primera_celda_invalida(elementos_validos) is None
    
    elementos_con_invalidos = [
        ("A[1,1]", "1/2", (0, 0)),
        ("A[1,2]", "abc", (0, 1)),
        ("A[2,1]", "xyz", (1, 0)),
    ]
    res = primera_celda_invalida(elementos_con_invalidos)
    assert res is not None
    assert res.etiqueta == "A[1,2]"
    assert res.foco == (0, 1)

def test_sugerencias_sistemas_soluciones_infinitas():
    """El sistema indeterminado obtiene las sugerencias correspondientes."""
    senales = Senales(herramienta="sistemas", estado="infinita", banderas=frozenset())
    sugerencias = sugerir(senales)
    identificadores = [s.identificador for s in sugerencias]
    assert "sistemas.infinita.porque" in identificadores or "sistemas.infinita.libre" in identificadores

def test_sugerencias_matrices_producto_exitoso():
    """El resultado matricial sugiere explicaciones del producto."""
    senales = Senales(herramienta="matrices", estado="exito", banderas=frozenset(["contiene_producto"]))
    sugerencias = sugerir(senales)
    identificadores = [s.identificador for s in sugerencias]
    assert "matrices.bandera.producto" in identificadores

def test_sugerencias_bases_resultado_con_division():
    """La conversión con divisiones obtiene su sugerencia específica."""
    senales = Senales(herramienta="bases", estado="resultado", banderas=frozenset(["division"]))
    sugerencias = sugerir(senales)
    identificadores = [s.identificador for s in sugerencias]
    assert "bases.division" in identificadores

def test_sugerencias_inversa_singular():
    """La singularidad ofrece orientación sobre la ausencia de inversa."""
    senales = Senales(herramienta="inversa", estado="singular", banderas=frozenset())
    sugerencias = sugerir(senales)
    identificadores = [s.identificador for s in sugerencias]
    assert "inversa.singular.porque" in identificadores or "inversa.singular.determinante" in identificadores

def test_sugerencias_romanos_resta_cero():
    """La resta no representable recibe una sugerencia de error."""
    senales = Senales(herramienta="romanos", estado="error", banderas=frozenset(["error_resta_cero"]))
    sugerencias = sugerir(senales)
    identificadores = [s.identificador for s in sugerencias]
    assert "romanos.error.cero" in identificadores
