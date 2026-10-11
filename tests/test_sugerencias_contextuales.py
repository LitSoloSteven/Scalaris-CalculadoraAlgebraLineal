import pytest

from src.frontend.suggestions import (
    Signals,
    InvalidCell,
    Suggestion,
    candidates,
    select_chips,
    suggest,
    first_invalid_cell,
    glosa_configured,
)

def test_sugerencias_limitadas_incluyen_especificas():
    """La selección respeta el límite e incluye sugerencias específicas."""
    # Signals con celda inválida y estado
    sig = Signals(
        tool="sistemas",
        state="infinite",
        flags=frozenset(["m_gt_n"]),
        invalid=InvalidCell("A[1,1]", (0, 0))
    )
    # include_specific=True (por defecto)
    cands_with_spec = candidates(sig)
    # Nota: invalid sólo genera candidato si state == "none" según el catálogo de suggestions.py
    # Probemos con state == "none" para verificar include_specific
    sig_none = Signals(
        tool="sistemas",
        state="none",
        invalid=InvalidCell("A[1,1]", (0, 0))
    )
    suggs_full = suggest(sig_none, limit=3, include_specific=True)
    assert any(s.role == "specific" for s in suggs_full)
    assert len(suggs_full) <= 3
    
    suggs_no_spec = suggest(sig_none, limit=3, include_specific=False)
    assert not any(s.role == "specific" for s in suggs_no_spec)

def test_sugerencias_priorizan_estado_y_senal():
    """Estado y señales determinan el orden de sugerencias."""
    # Verificamos la función select_chips que ordena specific > state > flag
    cands = [
        Suggestion(id="flag1", text="Flag 1", role="flag"),
        Suggestion(id="flag2", text="Flag 2", role="flag"),
        Suggestion(id="state1", text="State 1", role="state"),
        Suggestion(id="state2", text="State 2", role="state"),
        Suggestion(id="state3", text="State 3", role="state"),
        Suggestion(id="spec1", text="Spec 1", role="specific"),
    ]
    # select_chips toma specific primero, luego hasta 2 states, luego 1 flag, etc.
    selected = select_chips(cands, limit=4)
    roles = [s.role for s in selected]
    assert roles[0] == "specific"
    assert roles[1] == "state"
    assert roles[2] == "state"
    assert roles[3] == "flag"

def test_primera_celda_invalida():
    """El análisis identifica la primera coordenada inválida."""
    # items = iterable de (label, valor, focus|None)
    items_valid = [
        ("A[1,1]", "1/2", (0, 0)),
        ("A[1,2]", "0", (0, 1)),
        ("A[2,1]", "-3.5", (1, 0)),
    ]
    assert first_invalid_cell(items_valid) is None
    
    items_with_invalid = [
        ("A[1,1]", "1/2", (0, 0)),
        ("A[1,2]", "abc", (0, 1)),
        ("A[2,1]", "xyz", (1, 0)),
    ]
    res = first_invalid_cell(items_with_invalid)
    assert res is not None
    assert res.label == "A[1,2]"
    assert res.focus == (0, 1)

def test_sugerencias_sistemas_soluciones_infinitas():
    """El sistema indeterminado obtiene las sugerencias correspondientes."""
    sig = Signals(tool="sistemas", state="infinite", flags=frozenset())
    suggs = suggest(sig)
    ids = [s.id for s in suggs]
    assert "sistemas.inf.porque" in ids or "sistemas.inf.libre" in ids

def test_sugerencias_matrices_producto_exitoso():
    """El resultado matricial sugiere explicaciones del producto."""
    sig = Signals(tool="matrices", state="ok", flags=frozenset(["has_product"]))
    suggs = suggest(sig)
    ids = [s.id for s in suggs]
    assert "matrices.flag.ab" in ids

def test_sugerencias_bases_resultado_con_division():
    """La conversión con divisiones obtiene su sugerencia específica."""
    sig = Signals(tool="bases", state="result", flags=frozenset(["division"]))
    suggs = suggest(sig)
    ids = [s.id for s in suggs]
    assert "bases.div" in ids

def test_sugerencias_inversa_singular():
    """La singularidad ofrece orientación sobre la ausencia de inversa."""
    sig = Signals(tool="inversa", state="singular", flags=frozenset())
    suggs = suggest(sig)
    ids = [s.id for s in suggs]
    assert "inversa.sing.porque" in ids or "inversa.sing.det" in ids

def test_sugerencias_romanos_resta_cero():
    """La resta no representable recibe una sugerencia de error."""
    sig = Signals(tool="romanos", state="error", flags=frozenset(["err_sub_zero"]))
    suggs = suggest(sig)
    ids = [s.id for s in suggs]
    assert "romanos.err.cero" in ids
