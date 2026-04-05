"""Formatadores de valores para exibição na UI."""

from __future__ import annotations
from typing import Optional


def brl(value: float, decimals: int = 2) -> str:
    """Formata valor em Reais brasileiros."""
    if value is None:
        return "—"
    return f"R$ {value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: Optional[float], decimals: int = 2, multiply: bool = False) -> str:
    """Formata porcentagem."""
    if value is None or (isinstance(value, float) and (value != value)):
        return "—"
    v = value * 100 if multiply else value
    return f"{v:.{decimals}f}%"


def pct_from_decimal(value: Optional[float], decimals: int = 2) -> str:
    """Converte decimal (0.05) → '5.00%'."""
    return pct(value * 100 if value is not None else None, decimals)


def meses_para_texto(meses: int) -> str:
    """Converte meses em texto legível."""
    anos = meses // 12
    m = meses % 12
    partes = []
    if anos > 0:
        partes.append(f"{anos} ano{'s' if anos > 1 else ''}")
    if m > 0:
        partes.append(f"{m} mês{'es' if m > 1 else ''}")
    return " e ".join(partes) if partes else "0 meses"


def delta_brl(value: float, reference: float, invert: bool = False) -> str:
    """Calcula delta em R$ para uso em st.metric delta."""
    d = value - reference
    if invert:
        d = -d
    return f"R$ {d:+,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}
