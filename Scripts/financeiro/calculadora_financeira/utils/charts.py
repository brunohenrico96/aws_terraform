"""
Biblioteca de gráficos Plotly para o Motor Financeiro Institucional.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

# ─── Paleta corporativa ───────────────────────────────────────
COR_CONSORCIO = "#1a6db5"
COR_FINANCIAMENTO = "#e05c1a"
COR_INVESTIMENTO = "#1aad5c"
COR_ALUGUEL = "#8e44ad"
COR_NEUTRO = "#6c757d"
COR_DESTAQUE = "#f0b429"

TEMPLATE = "plotly_dark"
FONT_FAMILY = "Inter, sans-serif"


def _layout_base(title: str, height: int = 420) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=16, family=FONT_FAMILY)),
        template=TEMPLATE,
        height=height,
        margin=dict(l=40, r=20, t=60, b=40),
        font=dict(family=FONT_FAMILY, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )


# ─────────────────────────────────────────────────────────────
# CONSÓRCIO
# ─────────────────────────────────────────────────────────────

def chart_consorcio_evolucao(df: pd.DataFrame) -> go.Figure:
    """Saldo devedor e parcela mensal ao longo do tempo."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df["Mês"], y=df["Saldo Devedor (R$)"],
            name="Saldo Devedor", fill="tozeroy",
            fillcolor="rgba(26,109,181,0.15)",
            line=dict(color=COR_CONSORCIO, width=2),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=df["Mês"], y=df["Parcela Total (R$)"],
            name="Parcela Total", mode="lines",
            line=dict(color=COR_DESTAQUE, width=2, dash="dot"),
        ),
        secondary_y=True,
    )

    # Marca os meses de reajuste
    reajustes = df[df["Reajuste?"] == "✅"]
    if not reajustes.empty:
        fig.add_trace(
            go.Scatter(
                x=reajustes["Mês"], y=reajustes["Saldo Devedor (R$)"],
                name="Reajuste Anual", mode="markers",
                marker=dict(symbol="diamond", size=9, color=COR_DESTAQUE),
            ),
            secondary_y=False,
        )

    fig.update_layout(**_layout_base("Evolução do Consórcio: Saldo Devedor e Parcela"))
    fig.update_yaxes(title_text="Saldo Devedor (R$)", secondary_y=False, tickprefix="R$ ")
    fig.update_yaxes(title_text="Parcela (R$)", secondary_y=True, tickprefix="R$ ")
    return fig


def chart_composicao_desembolso_consorcio(resultados: dict) -> go.Figure:
    """Gráfico de pizza com composição do desembolso total."""
    labels = ["Parcelas Base", "Fundo de Reserva", "Seguros", "Recurso Próprio", "Lance Próprio"]
    values = [
        resultados["total_parcelas_base"],
        resultados["total_fundo_reserva"],
        resultados["total_seguro"],
        resultados.get("recurso_proprio", 0),
        resultados.get("lance_proprio", 0),
    ]
    colors = [COR_CONSORCIO, COR_DESTAQUE, COR_NEUTRO, COR_INVESTIMENTO, COR_ALUGUEL]

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.45,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hovertemplate="%{label}<br>R$ %{value:,.2f}<extra></extra>",
    ))
    fig.update_layout(**_layout_base("Composição do Desembolso Total — Consórcio", height=380))
    return fig


# ─────────────────────────────────────────────────────────────
# FINANCIAMENTO
# ─────────────────────────────────────────────────────────────

def chart_financiamento_amortizacao(df: pd.DataFrame, sistema: str = "SAC") -> go.Figure:
    """Stacked bar: amortização + juros + seguros + admin por mês."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["Mês"], y=df["Amortização (R$)"],
        name="Amortização", marker_color=COR_FINANCIAMENTO, opacity=0.9,
    ))
    fig.add_trace(go.Bar(
        x=df["Mês"], y=df["Juros (R$)"],
        name="Juros", marker_color=COR_DESTAQUE, opacity=0.9,
    ))
    fig.add_trace(go.Bar(
        x=df["Mês"], y=df["Seguro MIP (R$)"] + df["Seguro DFI (R$)"],
        name="Seguros", marker_color=COR_NEUTRO, opacity=0.85,
    ))

    fig.update_layout(
        barmode="stack",
        **_layout_base(f"Composição da Parcela — Sistema {sistema}", height=440),
    )
    fig.update_yaxes(tickprefix="R$ ")
    return fig


def chart_financiamento_saldo(df: pd.DataFrame) -> go.Figure:
    """Evolução do saldo devedor no financiamento."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["Saldo Devedor (R$)"],
        name="Saldo Devedor", fill="tozeroy",
        fillcolor="rgba(224,92,26,0.15)",
        line=dict(color=COR_FINANCIAMENTO, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["Saldo Final (R$)"],
        name="Saldo Final", line=dict(color=COR_DESTAQUE, width=1.5, dash="dot"),
    ))
    fig.update_layout(**_layout_base("Evolução do Saldo Devedor — Financiamento"))
    fig.update_yaxes(tickprefix="R$ ")
    return fig


def chart_comparativo_sistemas(df_sac: pd.DataFrame, df_price: pd.DataFrame) -> go.Figure:
    """Compara parcela total SAC vs PRICE ao longo do tempo."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sac["Mês"], y=df_sac["Parcela Total (R$)"],
        name="SAC", line=dict(color=COR_FINANCIAMENTO, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df_price["Mês"], y=df_price["Parcela Total (R$)"],
        name="PRICE", line=dict(color=COR_DESTAQUE, width=2, dash="dash"),
    ))
    fig.update_layout(**_layout_base("SAC vs PRICE — Evolução da Parcela"))
    fig.update_yaxes(tickprefix="R$ ")
    return fig


# ─────────────────────────────────────────────────────────────
# INVESTIMENTO
# ─────────────────────────────────────────────────────────────

def chart_investimento_evolucao(df: pd.DataFrame) -> go.Figure:
    """Evolução do patrimônio (bruto, líquido e real)."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["Patrimônio Bruto (R$)"],
        name="Patrimônio Bruto", line=dict(color=COR_NEUTRO, width=1.5, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["Patrimônio Líquido (R$)"],
        name="Patrimônio Líquido (após IR)", fill="tozeroy",
        fillcolor="rgba(26,173,92,0.15)",
        line=dict(color=COR_INVESTIMENTO, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["Patrimônio Real (R$)"],
        name="Patrimônio Real (poder de compra)",
        line=dict(color=COR_DESTAQUE, width=2, dash="dash"),
    ))

    # Marcadores de aporte anual
    aportes_anuais = df[df["Aporte Anual (R$)"] > 0]
    if not aportes_anuais.empty:
        fig.add_trace(go.Scatter(
            x=aportes_anuais["Mês"], y=aportes_anuais["Patrimônio Líquido (R$)"],
            name="Aporte Anual", mode="markers",
            marker=dict(symbol="triangle-up", size=10, color=COR_DESTAQUE),
        ))

    fig.update_layout(**_layout_base("Evolução do Patrimônio de Investimento"))
    fig.update_yaxes(tickprefix="R$ ")
    return fig


def chart_comparativo_produtos(df_produtos: pd.DataFrame) -> go.Figure:
    """Comparativo de patrimônio final por produto de investimento."""
    fig = go.Figure(go.Bar(
        x=df_produtos["Produto"],
        y=df_produtos["Patrimônio Final (R$)"],
        text=[f"R$ {v:,.0f}" for v in df_produtos["Patrimônio Final (R$)"]],
        textposition="outside",
        marker=dict(
            color=df_produtos["Patrimônio Final (R$)"],
            colorscale="Blues",
            showscale=False,
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Patrimônio Final: R$ %{y:,.2f}<extra></extra>"
        ),
    ))
    fig.update_layout(
        **_layout_base("Comparativo de Produtos de Investimento — Patrimônio Final", height=460),
        xaxis_tickangle=-30,
    )
    fig.update_yaxes(tickprefix="R$ ")
    return fig


def chart_decomposicao_patrimonio(
    total_aportado: float,
    rendimentos_brutos: float,
    ir_total: float,
) -> go.Figure:
    """Funil/waterfall: aportado → rendimentos → IR → líquido."""
    patrimonio_liquido = total_aportado + rendimentos_brutos - ir_total
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Total Aportado", "Rendimentos Brutos", "IR (estimado)", "Patrimônio Líquido"],
        y=[total_aportado, rendimentos_brutos, -ir_total, 0],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": COR_ALUGUEL}},
        increasing={"marker": {"color": COR_INVESTIMENTO}},
        totals={"marker": {"color": COR_CONSORCIO}},
        texttemplate="R$ %{y:,.0f}",
        textposition="outside",
    ))
    fig.update_layout(**_layout_base("Decomposição do Patrimônio Final", height=380))
    return fig


# ─────────────────────────────────────────────────────────────
# COMPARAÇÃO ESTRATÉGICA
# ─────────────────────────────────────────────────────────────

def chart_comparacao_patrimonio(
    df_cons: pd.DataFrame,
    df_finan: pd.DataFrame,
    df_aluguel: pd.DataFrame,
) -> go.Figure:
    """Evolução patrimonial comparativa dos 3 cenários."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_cons["Mês"],
        y=df_cons.get("Patrimônio Acumulado (R$)", df_cons.get("Saldo Devedor (R$)", 0) * -1 + df_cons["Saldo Devedor (R$)"].max()),
        name="🏛️ Consórcio", line=dict(color=COR_CONSORCIO, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=df_finan["Mês"],
        y=df_finan.get("Equity (R$)", df_finan["Saldo Devedor (R$)"].max() - df_finan["Saldo Devedor (R$)"]),
        name="🏦 Financiamento (SAC)", line=dict(color=COR_FINANCIAMENTO, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=df_aluguel["Mês"],
        y=df_aluguel["Patrimônio Líquido (R$)"],
        name="📈 Alugar + Investir", line=dict(color=COR_INVESTIMENTO, width=2.5),
    ))

    fig.update_layout(**_layout_base("Evolução Patrimonial Comparativa — 3 Cenários", height=480))
    fig.update_yaxes(tickprefix="R$ ")
    return fig


def chart_comparacao_barras(dados: dict) -> go.Figure:
    """Barras agrupadas para métricas chave dos 3 cenários."""
    cenarios = list(dados.keys())
    metricas = {
        "Total Desembolsado": [dados[c].get("total_desembolsado", 0) for c in cenarios],
        "Patrimônio Final": [dados[c].get("patrimonio_final", 0) for c in cenarios],
    }
    colors_desembolso = [COR_FINANCIAMENTO, COR_CONSORCIO, COR_ALUGUEL]
    colors_patrim = [COR_INVESTIMENTO, COR_DESTAQUE, COR_NEUTRO]

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Total Desembolsado (R$)", "Patrimônio Final (R$)"))

    for i, (cenario, cores) in enumerate(zip(cenarios, zip(colors_desembolso, colors_patrim))):
        fig.add_trace(go.Bar(
            name=cenario,
            x=[cenario],
            y=[metricas["Total Desembolsado"][i]],
            marker_color=cores[0],
            showlegend=(i == 0),
        ), row=1, col=1)
        fig.add_trace(go.Bar(
            name=cenario,
            x=[cenario],
            y=[metricas["Patrimônio Final"][i]],
            marker_color=cores[1],
            showlegend=False,
        ), row=1, col=2)

    fig.update_layout(**_layout_base("Comparativo de Métricas Financeiras", height=420))
    fig.update_yaxes(tickprefix="R$ ")
    return fig


def chart_fluxo_caixa_mensal(
    df_cons: pd.DataFrame,
    df_finan: pd.DataFrame,
    df_aluguel: pd.DataFrame,
) -> go.Figure:
    """Compara o desembolso mensal dos 3 cenários ao longo do tempo."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_cons["Mês"], y=df_cons["Parcela Total (R$)"],
        name="🏛️ Consórcio", line=dict(color=COR_CONSORCIO, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df_finan["Mês"], y=df_finan["Parcela Total (R$)"],
        name="🏦 Financiamento", line=dict(color=COR_FINANCIAMENTO, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df_aluguel["Mês"], y=df_aluguel["Aluguel Pago (R$)"],
        name="🏠 Aluguel", line=dict(color=COR_ALUGUEL, width=2, dash="dash"),
    ))

    fig.update_layout(**_layout_base("Fluxo de Caixa Mensal — Comparativo", height=420))
    fig.update_yaxes(tickprefix="R$ ")
    return fig


# ─────────────────────────────────────────────────────────────
# CENÁRIOS E SENSIBILIDADE
# ─────────────────────────────────────────────────────────────

def chart_heatmap(df: pd.DataFrame, title: str, colorscale: str = "Blues") -> go.Figure:
    """Gera heatmap genérico a partir de um DataFrame pivotado."""
    z_values = df.values
    z_text = [[f"R$ {v:,.0f}" for v in row] for row in z_values]

    fig = go.Figure(go.Heatmap(
        z=z_values,
        x=df.columns.tolist(),
        y=df.index.tolist(),
        text=z_text,
        texttemplate="%{text}",
        colorscale=colorscale,
        hovertemplate="Prazo: %{y}<br>Taxa: %{x}<br>Valor: R$ %{z:,.2f}<extra></extra>",
    ))
    fig.update_layout(**_layout_base(title, height=480))
    return fig


def chart_monte_carlo(df: pd.DataFrame, titulo: str = "Monte Carlo — Patrimônio Futuro") -> go.Figure:
    """Fan chart de percentis do Monte Carlo."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["P90"], name="P90 (otimista)",
        line=dict(color="rgba(26,173,92,0.4)", width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["P10"], name="P10 (pessimista)",
        fill="tonexty", fillcolor="rgba(26,173,92,0.15)",
        line=dict(color="rgba(26,173,92,0.4)", width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["P75"], name="P75",
        line=dict(color="rgba(26,173,92,0.6)", width=1, dash="dot"), showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["P25"], name="P25",
        line=dict(color="rgba(26,173,92,0.6)", width=1, dash="dot"), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=df["Mês"], y=df["P50"], name="Mediana (P50)",
        line=dict(color=COR_INVESTIMENTO, width=2.5),
    ))

    fig.update_layout(**_layout_base(titulo, height=460))
    fig.update_yaxes(tickprefix="R$ ")
    return fig


def chart_sensibilidade_tornado(variaveis: dict, baseline: float, titulo: str = "Análise de Sensibilidade") -> go.Figure:
    """Tornado chart: impacto de variáveis no resultado final."""
    nomes = list(variaveis.keys())
    impactos_pos = [v[0] - baseline for v in variaveis.values()]
    impactos_neg = [v[1] - baseline for v in variaveis.values()]

    ordem = sorted(range(len(nomes)), key=lambda i: abs(impactos_pos[i] - impactos_neg[i]), reverse=True)
    nomes = [nomes[i] for i in ordem]
    impactos_pos = [impactos_pos[i] for i in ordem]
    impactos_neg = [impactos_neg[i] for i in ordem]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=nomes, x=impactos_pos, orientation="h",
        name="Cenário Otimista", marker_color=COR_INVESTIMENTO, opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        y=nomes, x=impactos_neg, orientation="h",
        name="Cenário Pessimista", marker_color=COR_FINANCIAMENTO, opacity=0.85,
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.5)
    fig.update_layout(**_layout_base(titulo, height=max(300, len(nomes) * 50 + 100)), barmode="overlay")
    fig.update_xaxes(tickprefix="R$ ")
    return fig


def chart_gauge(value: float, min_val: float, max_val: float, title: str, threshold_good: float, threshold_bad: float) -> go.Figure:
    """Gauge meter para KPI."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"size": 14}},
        gauge={
            "axis": {"range": [min_val, max_val]},
            "bar": {"color": COR_CONSORCIO},
            "steps": [
                {"range": [min_val, threshold_bad], "color": "rgba(224,92,26,0.3)"},
                {"range": [threshold_bad, threshold_good], "color": "rgba(240,180,41,0.3)"},
                {"range": [threshold_good, max_val], "color": "rgba(26,173,92,0.3)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.75,
                "value": value,
            },
        },
    ))
    fig.update_layout(
        template=TEMPLATE,
        height=260,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family=FONT_FAMILY),
    )
    return fig
