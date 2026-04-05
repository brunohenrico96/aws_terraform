"""
Módulo: Comparação Estratégica
Consórcio vs Financiamento vs Alugar + Investir
Análise de patrimônio, custo total, break-even e recomendações.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.math_engine import (
    simular_consorcio,
    simular_financiamento,
    simular_alugar_investir,
    taxa_mensal,
)
from utils.charts import (
    chart_fluxo_caixa_mensal,
    COR_CONSORCIO,
    COR_FINANCIAMENTO,
    COR_INVESTIMENTO,
    COR_ALUGUEL,
    COR_DESTAQUE,
    TEMPLATE,
)
from utils.formatters import brl, pct_from_decimal, meses_para_texto, MESES_PT


def render_comparacao():
    st.header("⚖️ Comparação Estratégica: Consórcio vs Financiamento vs Alugar+Investir")
    st.caption(
        "Análise side-by-side dos três principais caminhos para aquisição de imóvel. "
        "Todos os cenários partem do **mesmo bem**, **mesmo recurso próprio** e **mesmo prazo**."
    )

    # ─────────────────────────────────────────────────────────
    # INPUTS GLOBAIS
    # ─────────────────────────────────────────────────────────
    with st.expander("⚙️ Premissas Comuns e Específicas", expanded=True):
        st.subheader("Premissas Comuns")
        p1, p2, p3, p4 = st.columns(4)
        valor_bem = p1.number_input("Valor do Bem (R$)", value=400_000.0, step=10_000.0, key="cmp_bem")
        recurso_proprio = p2.number_input("Recurso Próprio / Entrada (R$)", value=160_000.0, step=5_000.0, key="cmp_rec_proprio")
        prazo_meses = p3.number_input("Prazo (meses)", value=200, step=12, min_value=12, max_value=420, key="cmp_prazo")
        inflacao_aa = p4.number_input("Inflação / INCC a.a. (%)", value=5.0, step=0.5, key="cmp_inflacao")

        p5, p6, p7 = st.columns(3)
        taxa_invest = p5.number_input("Rendimento Investimento a.a. (%)", value=12.0, step=0.5, key="cmp_invest_taxa",
                                       help="Taxa de retorno do portfólio de investimentos (cenário Alugar+Investir).")
        aporte_mensal_extra = p6.number_input("Aporte Mensal Extra (R$)", value=2_000.0, step=500.0, key="cmp_aporte_mensal",
                                               help="Aporte adicional além do custo de moradia, investido mensalmente.")
        aporte_anual_extra = p7.number_input("Aporte Anual Extra (R$)", value=12_000.0, step=1_000.0, key="cmp_aporte_anual")
        mes_inicio = st.selectbox("Mês de Início", list(range(1, 13)), format_func=lambda m: MESES_PT[m],
                                   index=3, key="cmp_mes_inicio")

        st.divider()
        st.subheader("Parâmetros Específicos")
        cs1, cs2, cs3 = st.columns(3)

        with cs1:
            st.markdown("**🏛️ Consórcio**")
            taxa_adm = st.number_input("Taxa Adm. Total (%)", value=13.0, step=0.5, key="cmp_taxa_adm")
            carta = st.number_input("Carta de Crédito (R$)", value=900_000.0, step=10_000.0, key="cmp_carta")
            categoria_cmp = carta * (1 + taxa_adm / 100)
            st.caption(f"Categoria: {brl(categoria_cmp)}")
            lance_emb_pct = st.slider(
                "Lance Embutido (% da Categoria)", 0.0, 80.0, 65.0, 0.5, key="cmp_lance_emb",
                help="Lance calculado sobre a Categoria (Carta × (1 + Taxa Adm)).",
            )
            st.info(f"Lance Emb.: {brl(categoria_cmp * lance_emb_pct / 100)} ({lance_emb_pct:.1f}% da categoria)")
            mes_reajuste = st.selectbox("Mês do Reajuste", list(range(1, 13)), format_func=lambda m: MESES_PT[m],
                                         index=6, key="cmp_mes_reajuste")

        with cs2:
            st.markdown("**🏦 Financiamento**")
            taxa_fin = st.number_input("Taxa de Juros a.a. (%)", value=10.5, step=0.25, key="cmp_taxa_fin")
            sistema_fin = st.selectbox("Sistema", ["SAC", "PRICE", "SAM"], key="cmp_sistema")
            fgts = st.number_input("FGTS (R$)", value=0.0, step=1_000.0, key="cmp_fgts")

        with cs3:
            st.markdown("**🏠 Aluguel**")
            aluguel_inicial = st.number_input("Aluguel Inicial (R$/mês)", value=2_000.0, step=100.0, key="cmp_aluguel")
            apreciacao_bem = st.number_input("Apreciação do Bem a.a. (%)", value=5.0, step=0.5, key="cmp_apreciacao")

    # ─────────────────────────────────────────────────────────
    # CÁLCULOS
    # ─────────────────────────────────────────────────────────
    r_cons = simular_consorcio(
        carta_credito=carta,
        taxa_adm_total_pct=taxa_adm,
        prazo_meses=prazo_meses,
        lance_embutido_pct=lance_emb_pct,   # % da CATEGORIA
        recurso_proprio=recurso_proprio,
        inflacao_aa_pct=inflacao_aa,
        mes_reajuste=mes_reajuste,
        mes_inicio=mes_inicio,
        apreciacao_bem_aa_pct=apreciacao_bem,
    )

    r_fin = simular_financiamento(
        valor_imovel=valor_bem,
        entrada=recurso_proprio,
        prazo_meses=prazo_meses,
        taxa_juros_aa_pct=taxa_fin,
        sistema=sistema_fin,
        fgts=fgts,
        apreciacao_aa_pct=apreciacao_bem,
    )

    r_alug = simular_alugar_investir(
        aluguel_inicial=aluguel_inicial,
        inflacao_aa_pct=inflacao_aa,
        capital_inicial=recurso_proprio,
        aporte_mensal=aporte_mensal_extra,
        aporte_anual=aporte_anual_extra,
        mes_aporte_anual=12,
        taxa_invest_aa_pct=taxa_invest,
        prazo_meses=prazo_meses,
        mes_inicio=mes_inicio,
        parcela_alternativa_mensal=r_cons["primeira_parcela_base"],
    )

    df_cons = r_cons["df"]
    df_fin = r_fin["df"]
    df_alug = r_alug["df"]

    # ─────────────────────────────────────────────────────────
    # PAINEL DE KPIs COMPARATIVOS
    # ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Painel Comparativo de KPIs")

    kc, kf, ka = st.columns(3)

    with kc:
        st.markdown(f"### 🏛️ Consórcio")
        st.metric("1ª Parcela", brl(r_cons["primeira_parcela_base"]))
        st.metric("Total Desembolsado", brl(r_cons["total_desembolsado"]))
        st.metric("Crédito Obtido", brl(r_cons["credito_total"]))
        st.metric("TIR Crédito a.a.", pct_from_decimal(r_cons["tir_credito_aa"]) if r_cons["tir_credito_aa"] else "—")
        st.metric("TIR Projeto a.a.", pct_from_decimal(r_cons["tir_projeto_aa"]) if r_cons["tir_projeto_aa"] else "—")
        st.metric("Bem Futuro (apreciado)", brl(r_cons["bem_futuro"]))

    with kf:
        st.markdown(f"### 🏦 Financiamento ({sistema_fin})")
        st.metric("1ª Parcela", brl(r_fin["primeira_parcela_total"]))
        st.metric("Total Desembolsado", brl(r_fin["total_pago"]))
        st.metric("Financiamento Obtido", brl(r_fin["saldo_financiado"]))
        st.metric("CET a.a.", pct_from_decimal(r_fin["tir_aa"]) if r_fin["tir_aa"] else "—")
        st.metric("TIR Projeto a.a.", pct_from_decimal(r_fin["tir_proj_aa"]) if r_fin["tir_proj_aa"] else "—")
        st.metric("Bem Futuro (apreciado)", brl(r_fin["bem_futuro"]))

    with ka:
        st.markdown(f"### 📈 Alugar + Investir")
        st.metric("Aluguel Inicial", brl(aluguel_inicial))
        st.metric("Total Pago em Aluguel", brl(r_alug["total_aluguel"]))
        st.metric("Capital Investido", brl(recurso_proprio))
        st.metric("Rendimento Invest. a.a.", f"{taxa_invest:.1f}%")
        st.metric("Patrimônio Final Líquido", brl(r_alug["patrimonio_final_liquido"]))
        st.metric("Patrimônio Real Final", brl(r_alug["patrimonio_final_real"]))

    # ─────────────────────────────────────────────────────────
    # GRÁFICOS COMPARATIVOS
    # ─────────────────────────────────────────────────────────
    st.divider()

    # Fluxo de caixa mensal
    st.plotly_chart(
        chart_fluxo_caixa_mensal(df_cons, df_fin, df_alug),
        use_container_width=True,
    )

    # Patrimônio acumulado
    # Consórcio: equity = valor bem - saldo devedor (cresce à medida que o SD cai)
    df_cons["Equity (R$)"] = valor_bem * (1 + apreciacao_bem / 100) ** (df_cons["Mês"] / 12) - df_cons["Saldo Devedor (R$)"]
    # Financiamento: equity = bem apreciado - saldo devedor
    df_fin["Equity (R$)"] = valor_bem * (1 + apreciacao_bem / 100) ** (df_fin["Mês"] / 12) - df_fin["Saldo Final (R$)"]

    fig_pat = go.Figure()
    fig_pat.add_trace(go.Scatter(
        x=df_cons["Mês"], y=df_cons["Equity (R$)"],
        name="🏛️ Consórcio (Equity)", line=dict(color=COR_CONSORCIO, width=2.5),
    ))
    fig_pat.add_trace(go.Scatter(
        x=df_fin["Mês"], y=df_fin["Equity (R$)"],
        name=f"🏦 Financiamento {sistema_fin} (Equity)", line=dict(color=COR_FINANCIAMENTO, width=2.5),
    ))
    fig_pat.add_trace(go.Scatter(
        x=df_alug["Mês"], y=df_alug["Patrimônio Líquido (R$)"],
        name="📈 Alugar+Investir (Portfólio)", line=dict(color=COR_INVESTIMENTO, width=2.5),
    ))
    fig_pat.update_layout(
        title="Evolução do Patrimônio / Equity Comparativa — 3 Cenários",
        template=TEMPLATE, height=460, yaxis_tickprefix="R$ ", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_pat, use_container_width=True)

    # Desembolso acumulado
    df_cons["Desembolso Acum. (R$)"] = df_cons["Parcela Total (R$)"].cumsum() + recurso_proprio
    df_fin["Desembolso Acum. (R$)"] = df_fin["Parcela Total (R$)"].cumsum() + recurso_proprio
    df_alug["Desembolso Acum. (R$)"] = df_alug["Aluguel Pago (R$)"].cumsum()

    fig_desp = go.Figure()
    fig_desp.add_trace(go.Scatter(
        x=df_cons["Mês"], y=df_cons["Desembolso Acum. (R$)"],
        name="🏛️ Consórcio", line=dict(color=COR_CONSORCIO, width=2),
    ))
    fig_desp.add_trace(go.Scatter(
        x=df_fin["Mês"], y=df_fin["Desembolso Acum. (R$)"],
        name=f"🏦 Financiamento {sistema_fin}", line=dict(color=COR_FINANCIAMENTO, width=2),
    ))
    fig_desp.add_trace(go.Scatter(
        x=df_alug["Mês"], y=df_alug["Desembolso Acum. (R$)"],
        name="🏠 Aluguel", line=dict(color=COR_ALUGUEL, width=2, dash="dash"),
    ))
    fig_desp.update_layout(
        title="Desembolso Acumulado — Comparativo",
        template=TEMPLATE, height=400, yaxis_tickprefix="R$ ", hovermode="x unified",
    )
    st.plotly_chart(fig_desp, use_container_width=True)

    # ─────────────────────────────────────────────────────────
    # ANÁLISE DE BREAK-EVEN
    # ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📍 Análise de Break-Even")

    # Break-even Consórcio vs Financiamento (quem tem menor custo acumulado em cada mês)
    meses_comuns = min(len(df_cons), len(df_fin))
    breakeven_cons_fin = None
    for i in range(meses_comuns):
        if df_cons["Desembolso Acum. (R$)"].iloc[i] < df_fin["Desembolso Acum. (R$)"].iloc[i]:
            breakeven_cons_fin = i + 1
            break

    # Break-even Alugar+Investir vs Consórcio (quando portfólio supera equity)
    meses_comuns2 = min(len(df_cons), len(df_alug))
    breakeven_alug_cons = None
    for i in range(meses_comuns2):
        if df_alug["Patrimônio Líquido (R$)"].iloc[i] > df_cons["Equity (R$)"].iloc[i]:
            breakeven_alug_cons = i + 1
            break

    be1, be2 = st.columns(2)
    if breakeven_cons_fin:
        be1.info(
            f"🏛️ vs 🏦 — O consórcio se torna mais barato que o financiamento "
            f"a partir do **mês {breakeven_cons_fin}** ({meses_para_texto(breakeven_cons_fin)})."
        )
    else:
        be1.warning("🏛️ vs 🏦 — Financiamento permanece mais barato ao longo de todo o período.")

    if breakeven_alug_cons:
        be2.info(
            f"📈 vs 🏛️ — O portfólio de Alugar+Investir supera o equity do consórcio "
            f"a partir do **mês {breakeven_alug_cons}** ({meses_para_texto(breakeven_alug_cons)})."
        )
    else:
        be2.warning("📈 vs 🏛️ — O equity do consórcio permanece superior ao portfólio ao longo de todo o período.")

    # ─────────────────────────────────────────────────────────
    # RECOMENDAÇÃO AUTOMÁTICA
    # ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🤖 Recomendação Baseada em Dados")

    patrimonio_cons_final = df_cons["Equity (R$)"].iloc[-1] if len(df_cons) > 0 else 0
    patrimonio_fin_final = df_fin["Equity (R$)"].iloc[-1] if len(df_fin) > 0 else 0
    patrimonio_alug_final = r_alug["patrimonio_final_liquido"]

    ranking = sorted([
        ("🏛️ Consórcio", patrimonio_cons_final, r_cons["total_desembolsado"]),
        (f"🏦 Financiamento {sistema_fin}", patrimonio_fin_final, r_fin["total_pago"]),
        ("📈 Alugar + Investir", patrimonio_alug_final, r_alug["total_aluguel"]),
    ], key=lambda x: x[1], reverse=True)

    st.markdown(f"""
**Ranking por Patrimônio Final gerado:**

| # | Cenário | Patrimônio Final | Total Desembolsado |
|---|---|---|---|
| 🥇 | {ranking[0][0]} | {brl(ranking[0][1])} | {brl(ranking[0][2])} |
| 🥈 | {ranking[1][0]} | {brl(ranking[1][1])} | {brl(ranking[1][2])} |
| 🥉 | {ranking[2][0]} | {brl(ranking[2][1])} | {brl(ranking[2][2])} |
    """)

    # Texto de recomendação
    vencedor = ranking[0][0]
    if "Consórcio" in vencedor:
        rec = (
            "O **Consórcio** apresenta o melhor retorno patrimonial neste cenário, "
            "especialmente por conta do lance embutido que reduz o saldo devedor e das parcelas "
            "que crescem com a inflação mas partem de um nível baixo. Indicado para quem tem "
            "flexibilidade de prazo e não precisa da chave imediatamente."
        )
    elif "Financiamento" in vencedor:
        rec = (
            f"O **Financiamento ({sistema_fin})** lidera em patrimônio final, "
            "pois a alavancagem sobre o imóvel (que se aprecia) supera o custo dos juros. "
            "Indicado para quem precisa do imóvel agora e tem capacidade de pagar parcelas maiores."
        )
    else:
        rec = (
            "**Alugar e Investir** gera o maior patrimônio no período, "
            "pois o capital empregado no portfólio cresce mais rápido do que o custo do aluguel "
            "e a apreciação do bem. Indicado para quem tem disciplina de investimento e "
            "flexibilidade de moradia."
        )

    st.success(f"💡 {rec}")

    with st.expander("📌 Premissas e Limitações da Análise"):
        st.markdown("""
- **Consórcio**: contemplação assumida no primeiro mês. Atrasos na contemplação reduzem o benefício.
- **Financiamento**: juros nominais, sem IPCA-atualização (ex. financiamentos pré-fixados).
- **Alugar+Investir**: assume rendimento constante do portfólio (sem volatilidade de mercado).
- Todos os cenários usam o **mesmo prazo** e **mesmo recurso próprio** para comparação justa.
- Custos com escritura, ITBI, corretagem e reforma não estão incluídos (somam ~5% do imóvel).
- A apreciação do imóvel é linear e histórica — rentabilidade passada não garante futuro.
        """)
