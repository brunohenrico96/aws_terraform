"""
Motor Financeiro Institucional — v2.0
Plataforma de simulação para Consórcio | Financiamento | Investimento

Arquitetura:
  app.py              → Ponto de entrada, navegação e dashboard executivo
  utils/math_engine   → Motor matemático financeiro
  utils/charts        → Visualizações Plotly
  utils/formatters    → Formatadores de moeda e percentual
  modules/consorcio   → Módulo completo de consórcio
  modules/financiamento → Módulo completo de financiamento
  modules/investimento → Módulo de investimento e patrimônio
  modules/comparacao  → Comparação estratégica dos 3 cenários
  modules/cenarios    → Sensibilidade, Monte Carlo e What-If
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.math_engine import (
    simular_consorcio,
    simular_financiamento,
    simular_investimento,
    taxa_mensal,
)
from utils.formatters import brl, pct_from_decimal
from utils.charts import (
    COR_CONSORCIO, COR_FINANCIAMENTO, COR_INVESTIMENTO,
    COR_DESTAQUE, TEMPLATE,
)
from modules.consorcio import render_consorcio
from modules.financiamento import render_financiamento
from modules.investimento import render_investimento
from modules.comparacao import render_comparacao
from modules.cenarios import render_cenarios


# ─────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Motor Financeiro Institucional",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.bcb.gov.br",
        "Report a bug": None,
        "About": (
            "**Motor Financeiro Institucional v2.0**\n\n"
            "Plataforma de simulação financeira para consórcio, financiamento e investimento.\n"
            "Desenvolvida para análise institucional — Bradesco | Ademicon."
        ),
    },
)

# CSS customizado para aparência institucional
st.markdown("""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #0d1f3c 100%);
    }
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        font-weight: 700;
    }
    /* Cabeçalho */
    .main-header {
        background: linear-gradient(135deg, #0a1628 0%, #1a3a6b 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 5px solid #f0b429;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.8rem;
    }
    .main-header p {
        color: #a0aec0;
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
    }
    /* Cards de KPI no dashboard */
    .kpi-card {
        background: #1a2744;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #2d4a8a;
        text-align: center;
    }
    /* Separadores */
    hr { border-color: #2d4a8a !important; }
    /* Tabs */
    [data-testid="stTab"] {
        font-size: 0.95rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SIDEBAR — NAVEGAÇÃO E QUICK-CONFIG
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-size:2.5rem">💼</div>
        <div style="color:#f0b429; font-weight:700; font-size:1.1rem">Motor Financeiro</div>
        <div style="color:#a0aec0; font-size:0.8rem">Versão 2.0 — Institucional</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    pagina = st.radio(
        "Navegação",
        [
            "🏠 Dashboard Executivo",
            "🏛️ Consórcio",
            "🏦 Financiamento",
            "📈 Investimento",
            "⚖️ Comparação Estratégica",
            "🔭 Cenários & Sensibilidade",
        ],
        key="nav_pagina",
    )

    st.divider()
    st.markdown("### 🌍 Indicadores de Mercado")
    selic_ref = st.number_input("Selic a.a. (%)", value=13.75, step=0.25, key="g_selic",
                                 help="Taxa Selic atual — atualizada pelo BACEN.")
    cdi_ref = st.number_input("CDI a.a. (%)", value=13.75, step=0.25, key="g_cdi")
    ipca_ref = st.number_input("IPCA a.a. (%)", value=5.0, step=0.25, key="g_ipca")
    incc_ref = st.number_input("INCC a.a. (%)", value=5.5, step=0.25, key="g_incc",
                                help="Índice Nacional de Custo da Construção — usado em consórcios de imóvel.")

    st.divider()
    st.caption(
        "📌 Os indicadores de mercado acima são referências globais. "
        "Cada módulo permite ajuste fino independente."
    )
    st.caption("🔒 Dados processados localmente — sem envio a servidores externos.")


# ─────────────────────────────────────────────────────────────
# ROTEAMENTO
# ─────────────────────────────────────────────────────────────
if pagina == "🏛️ Consórcio":
    render_consorcio()

elif pagina == "🏦 Financiamento":
    render_financiamento()

elif pagina == "📈 Investimento":
    render_investimento()

elif pagina == "⚖️ Comparação Estratégica":
    render_comparacao()

elif pagina == "🔭 Cenários & Sensibilidade":
    render_cenarios()

else:
    # ─────────────────────────────────────────────────────────
    # DASHBOARD EXECUTIVO
    # ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="main-header">
        <h1>💼 Motor Financeiro Institucional</h1>
        <p>Plataforma de simulação para <strong>Consórcio</strong> | <strong>Financiamento Imobiliário</strong> | <strong>Investimento e Patrimônio</strong></p>
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        "Configure os parâmetros rápidos abaixo para uma visão geral comparativa. "
        "Use o menu lateral para análises detalhadas de cada módulo."
    )

    # ── Parâmetros rápidos ──
    with st.expander("⚙️ Quick Config — Parâmetros para o Dashboard", expanded=True):
        d1, d2, d3, d4 = st.columns(4)
        d_bem = d1.number_input("Valor do Bem (R$)", value=400_000.0, step=10_000.0, key="d_bem")
        d_entrada = d2.number_input("Recurso Próprio / Entrada (R$)", value=160_000.0, step=5_000.0, key="d_entrada")
        d_prazo = d3.number_input("Prazo (meses)", value=200, step=12, key="d_prazo")
        d_taxa_fin = d4.number_input("Taxa Financiamento a.a. (%)", value=10.5, step=0.25, key="d_taxa_fin")

        d5, d6, d7, d8 = st.columns(4)
        d_carta = d5.number_input("Carta de Crédito (R$)", value=900_000.0, step=10_000.0, key="d_carta")
        d_taxa_adm = d6.number_input("Taxa Adm. Consórcio (%)", value=13.0, step=0.5, key="d_taxa_adm")
        d_lance_emb_pct = d7.number_input(
            "Lance Embutido (% da Categoria)", value=65.0, step=1.0, key="d_lance_emb_pct",
            help="categoria = carta × (1 + taxa_adm). Lance = % da categoria.",
        )
        d_taxa_invest = d8.number_input("Rendimento Invest. a.a. (%)", value=12.0, step=0.5, key="d_taxa_invest")

        d9, d10, d11 = st.columns(3)
        d_inflacao = d9.number_input("Inflação a.a. (%)", value=5.0, step=0.25, key="d_inflacao")
        d_aporte_m = d10.number_input("Aporte Mensal Invest. (R$)", value=2_000.0, step=500.0, key="d_aporte_m")
        d_aporte_a = d11.number_input("Aporte Anual Invest. (R$)", value=12_000.0, step=1_000.0, key="d_aporte_a")

    # ── Cálculos do dashboard ──
    r_cons_d = simular_consorcio(
        carta_credito=d_carta,
        taxa_adm_total_pct=d_taxa_adm,
        prazo_meses=d_prazo,
        lance_embutido_pct=d_lance_emb_pct,   # % da CATEGORIA
        recurso_proprio=d_entrada,
        inflacao_aa_pct=d_inflacao,
    )

    r_fin_d = simular_financiamento(
        valor_imovel=d_bem,
        entrada=d_entrada,
        prazo_meses=d_prazo,
        taxa_juros_aa_pct=d_taxa_fin,
        sistema="SAC",
    )

    r_inv_d = simular_investimento(
        capital_inicial=d_entrada,
        aporte_mensal=d_aporte_m,
        aporte_anual=d_aporte_a,
        mes_aporte_anual=12,
        taxa_bruta_aa_pct=d_taxa_invest,
        inflacao_aa_pct=d_inflacao,
        prazo_meses=d_prazo,
    )

    # ── KPIs Summary ──
    st.divider()
    st.subheader("📊 Painel de KPIs Comparativo")

    col_c, col_f, col_i = st.columns(3)

    with col_c:
        st.markdown(
            f"<div style='background:#0a1628;border-left:4px solid {COR_CONSORCIO};"
            f"border-radius:8px;padding:1rem;'><h4 style='color:{COR_CONSORCIO};margin:0'>🏛️ Consórcio</h4></div>",
            unsafe_allow_html=True,
        )
        st.metric("1ª Parcela Base", brl(r_cons_d["primeira_parcela_base"]))
        st.metric("Total Desembolsado", brl(r_cons_d["total_desembolsado"]))
        st.metric("Crédito p/ o Bem", brl(r_cons_d["credito_total"]))
        st.metric("TIR Crédito a.a.", pct_from_decimal(r_cons_d["tir_credito_aa"]) if r_cons_d["tir_credito_aa"] else "—")

    with col_f:
        st.markdown(
            f"<div style='background:#0a1628;border-left:4px solid {COR_FINANCIAMENTO};"
            f"border-radius:8px;padding:1rem;'><h4 style='color:{COR_FINANCIAMENTO};margin:0'>🏦 Financiamento SAC</h4></div>",
            unsafe_allow_html=True,
        )
        st.metric("1ª Parcela Total", brl(r_fin_d["primeira_parcela_total"]))
        st.metric("Total Desembolsado", brl(r_fin_d["total_pago"]))
        st.metric("Financiamento Obtido", brl(r_fin_d["saldo_financiado"]))
        st.metric("CET a.a.", pct_from_decimal(r_fin_d["tir_aa"]) if r_fin_d["tir_aa"] else "—")

    with col_i:
        st.markdown(
            f"<div style='background:#0a1628;border-left:4px solid {COR_INVESTIMENTO};"
            f"border-radius:8px;padding:1rem;'><h4 style='color:{COR_INVESTIMENTO};margin:0'>📈 Investimento</h4></div>",
            unsafe_allow_html=True,
        )
        st.metric("Capital Inicial", brl(d_entrada))
        st.metric("Total Aportado", brl(r_inv_d["total_aportado"]))
        st.metric("Patrimônio Final Líq.", brl(r_inv_d["patrimonio_final_liquido"]))
        st.metric("Patrimônio Real Final", brl(r_inv_d["patrimonio_final_real"]))

    # ── Gráfico Panorâmico ──
    st.divider()
    st.subheader("📈 Panorama: Parcelas e Evolução Patrimonial")

    df_cons_d = r_cons_d["df"]
    df_fin_d = r_fin_d["df"]
    df_inv_d = r_inv_d["df"]

    g1, g2 = st.columns(2)

    with g1:
        fig_parc = go.Figure()
        fig_parc.add_trace(go.Scatter(
            x=df_cons_d["Mês"], y=df_cons_d["Parcela Total (R$)"],
            name="Consórcio", line=dict(color=COR_CONSORCIO, width=2),
        ))
        fig_parc.add_trace(go.Scatter(
            x=df_fin_d["Mês"], y=df_fin_d["Parcela Total (R$)"],
            name="Financiamento SAC", line=dict(color=COR_FINANCIAMENTO, width=2),
        ))
        fig_parc.update_layout(
            title="Parcela Mensal: Consórcio vs Financiamento",
            template=TEMPLATE, height=380,
            yaxis_tickprefix="R$ ", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_parc, use_container_width=True)

    with g2:
        # Equity Consórcio (bem apreciado - saldo devedor)
        apreciacao_d = 5.0 / 100
        df_cons_d["Equity (R$)"] = (
            d_bem * (1 + apreciacao_d) ** (df_cons_d["Mês"] / 12)
            - df_cons_d["Saldo Devedor (R$)"]
        )

        fig_pat = go.Figure()
        fig_pat.add_trace(go.Scatter(
            x=df_cons_d["Mês"], y=df_cons_d["Equity (R$)"],
            name="Equity Consórcio", line=dict(color=COR_CONSORCIO, width=2),
        ))
        fig_pat.add_trace(go.Scatter(
            x=df_inv_d["Mês"], y=df_inv_d["Patrimônio Líquido (R$)"],
            name="Portfólio de Investimento",
            fill="tozeroy", fillcolor="rgba(26,173,92,0.1)",
            line=dict(color=COR_INVESTIMENTO, width=2),
        ))
        fig_pat.update_layout(
            title="Evolução Patrimonial Comparativa",
            template=TEMPLATE, height=380,
            yaxis_tickprefix="R$ ", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_pat, use_container_width=True)

    # ── Indicadores de Mercado ──
    st.divider()
    st.subheader("🌍 Indicadores de Mercado de Referência")

    mi1, mi2, mi3, mi4, mi5, mi6 = st.columns(6)
    mi1.metric("Selic", f"{selic_ref:.2f}%", help="Taxa básica de juros (COPOM)")
    mi2.metric("CDI", f"{cdi_ref:.2f}%", help="Certificado de Depósito Interbancário")
    mi3.metric("IPCA", f"{ipca_ref:.2f}%", help="Índice de Preços ao Consumidor Amplo")
    mi4.metric("INCC", f"{incc_ref:.2f}%", help="Índice Nacional de Custo da Construção")
    mi5.metric("CDI × 110%", f"{cdi_ref * 1.10:.2f}%", help="CDB padrão de bancos de 2ª linha")
    mi6.metric("Real Selic", f"{selic_ref - ipca_ref:.2f}%", help="Retorno real = Selic − IPCA")

    # ── Cards de navegação ──
    st.divider()
    st.subheader("🗺️ Explore os Módulos")

    nav1, nav2, nav3, nav4, nav5 = st.columns(5)
    modules_info = [
        ("🏛️", "Consórcio", "Simulação completa com lance, reajuste anual, TIR e comparativo de cenários.", COR_CONSORCIO),
        ("🏦", "Financiamento", "SAC, PRICE e SAM com seguros, FGTS, amortização extra e portabilidade.", COR_FINANCIAMENTO),
        ("📈", "Investimento", "Aportes mensais e anuais, multi-produto, IR, metas e renda passiva.", COR_INVESTIMENTO),
        ("⚖️", "Comparação", "Side-by-side dos 3 cenários com análise de break-even e recomendação.", COR_DESTAQUE),
        ("🔭", "Cenários", "Heatmaps, Monte Carlo, Tornado Chart e análise What-If em tempo real.", "#8e44ad"),
    ]

    for col, (icon, titulo, desc, cor) in zip([nav1, nav2, nav3, nav4, nav5], modules_info):
        col.markdown(
            f"""<div style="background:#0d1f3c;border:1px solid {cor};border-radius:10px;
            padding:1rem;text-align:center;min-height:160px;">
            <div style="font-size:2rem">{icon}</div>
            <div style="color:{cor};font-weight:700;font-size:1rem;margin:0.3rem 0">{titulo}</div>
            <div style="color:#a0aec0;font-size:0.8rem">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Rodapé ──
    st.divider()
    st.markdown("""
    <div style="text-align:center;color:#4a5568;font-size:0.8rem;padding:1rem">
        <strong>Motor Financeiro Institucional v2.0</strong> &nbsp;|&nbsp;
        Dados processados localmente &nbsp;|&nbsp;
        Regulamentação: Resolução BACEN 35/2021 &nbsp;|&nbsp;
        ABAC — Associação Brasileira de Administradoras de Consórcios &nbsp;|&nbsp;
        Metodologia: CET (BACEN), ABNT NBR 15480
    </div>
    """, unsafe_allow_html=True)
