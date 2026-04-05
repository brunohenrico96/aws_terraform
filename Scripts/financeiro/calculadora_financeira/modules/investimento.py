"""
Módulo: Investimento e Patrimônio
Juros compostos | Aportes mensais e anuais | Multi-produto | IR | Renda passiva | Metas.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.math_engine import (
    simular_investimento,
    comparar_produtos_investimento,
    calc_prazo_para_meta,
    calc_renda_passiva,
    calc_juros_compostos,
    taxa_mensal,
    PRODUTOS_REFERENCIA,
)
from utils.charts import (
    chart_investimento_evolucao,
    chart_comparativo_produtos,
    chart_decomposicao_patrimonio,
)
from utils.formatters import brl, pct_from_decimal, meses_para_texto, MESES_PT


def render_investimento():
    st.header("📈 Simulador de Investimento e Patrimônio")
    st.caption(
        "Projeção de patrimônio com **juros compostos**, **aportes mensais e anuais**, "
        "**impacto do IR** (tabela regressiva) e **comparativo entre produtos** de renda fixa e variável."
    )

    tab_sim, tab_comp, tab_meta, tab_renda = st.tabs([
        "💰 Simulação de Carteira",
        "📊 Comparativo de Produtos",
        "🎯 Calculadora de Metas",
        "🏖️ Renda Passiva",
    ])

    # ─────────────────────────────────────────────────────────
    # TAB 1 — SIMULAÇÃO DE CARTEIRA
    # ─────────────────────────────────────────────────────────
    with tab_sim:
        with st.expander("⚙️ Parâmetros do Investimento", expanded=True):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.subheader("Capital e Aportes")
                capital_inicial = st.number_input(
                    "Capital Inicial (R$)", value=160_000.0, step=5_000.0, format="%.2f", key="inv_capital",
                    help="Saldo já disponível para investir hoje.",
                )
                aporte_mensal = st.number_input(
                    "Aporte Mensal (R$)", value=2_000.0, step=100.0, key="inv_aporte_mensal",
                    help="Valor investido mensalmente de forma regular.",
                )
                aporte_anual = st.number_input(
                    "Aporte Anual (R$)", value=12_000.0, step=1_000.0, key="inv_aporte_anual",
                    help="Valor extra investido uma vez por ano (ex: 13º salário, bônus).",
                )
                mes_aporte_anual = st.selectbox(
                    "Mês do Aporte Anual",
                    options=list(range(1, 13)),
                    format_func=lambda m: MESES_PT[m],
                    index=11,  # Dezembro
                    key="inv_mes_aporte_anual",
                )

            with c2:
                st.subheader("Taxa e Horizonte")
                produto_sel = st.selectbox(
                    "Produto de Referência",
                    ["Personalizado"] + list(PRODUTOS_REFERENCIA.keys()),
                    key="inv_produto",
                )
                if produto_sel != "Personalizado":
                    cfg = PRODUTOS_REFERENCIA[produto_sel]
                    taxa_default = cfg["valor"] if cfg["tipo"] in ("prefixado", "fii", "acoes") else 13.0
                    isento_default = cfg["isento_ir"]
                else:
                    taxa_default = 13.0
                    isento_default = False

                taxa_bruta_aa = st.number_input(
                    "Rendimento Bruto a.a. (%)", value=float(taxa_default), step=0.25, key="inv_taxa",
                    help="Taxa de rendimento bruta anual do produto escolhido.",
                )
                inflacao_aa = st.number_input(
                    "Inflação (IPCA) a.a. (%)", value=5.0, step=0.25, key="inv_inflacao",
                    help="Usada para calcular o Patrimônio Real (poder de compra futuro).",
                )
                prazo_meses = st.number_input(
                    "Prazo (meses)", value=200, step=12, min_value=12, max_value=600, key="inv_prazo",
                )
                mes_inicio = st.selectbox(
                    "Mês de Início",
                    options=list(range(1, 13)),
                    format_func=lambda m: MESES_PT[m],
                    index=3,
                    key="inv_mes_inicio",
                )

            with c3:
                st.subheader("Tributação")
                isento_ir = st.checkbox(
                    "Produto isento de IR (LCI/LCA/Poupança)?",
                    value=isento_default,
                    key="inv_isento",
                )
                st.markdown("**Tabela regressiva de IR:**")
                st.table(pd.DataFrame({
                    "Prazo": ["Até 6 meses", "6–12 meses", "12–24 meses", "Acima de 24 meses"],
                    "Alíquota": ["22,5%", "20,0%", "17,5%", "15,0%"],
                }))

        # ── CÁLCULO ──
        r = simular_investimento(
            capital_inicial=capital_inicial,
            aporte_mensal=aporte_mensal,
            aporte_anual=aporte_anual,
            mes_aporte_anual=mes_aporte_anual,
            taxa_bruta_aa_pct=taxa_bruta_aa,
            inflacao_aa_pct=inflacao_aa,
            prazo_meses=prazo_meses,
            mes_inicio=mes_inicio,
            isento_ir=isento_ir,
        )
        df = r["df"]

        # ── KPIs ──
        st.divider()
        st.subheader("📊 KPIs — Investimento")
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Capital Inicial", brl(capital_inicial))
        k2.metric("Total Aportado", brl(r["total_aportado"]))
        k3.metric("Patrimônio Final Bruto", brl(r["patrimonio_final_bruto"]))
        k4.metric("Patrimônio Final Líquido", brl(r["patrimonio_final_liquido"]),
                  delta=brl(r["patrimonio_final_liquido"] - r["total_aportado"]),
                  help="Após dedução estimada do IR.")
        k5.metric("Patrimônio Real", brl(r["patrimonio_final_real"]),
                  help="Poder de compra real, descontada a inflação acumulada.")
        k6.metric(
            "TIR Líquida a.a.",
            pct_from_decimal(r["tir_aa"]) if r["tir_aa"] else "—",
        )

        ka, kb, kc, kd = st.columns(4)
        ka.metric("Rendimentos Brutos Totais", brl(r["total_rendimentos_brutos"]))
        kb.metric("IR Estimado Total", brl(r["total_ir"]))
        kc.metric("Rentabilidade Total", f"{r['rentab_total_pct']:.1f}%")
        kd.metric("Prazo", meses_para_texto(prazo_meses))

        # ── GRÁFICOS ──
        st.divider()
        st.plotly_chart(chart_investimento_evolucao(df), use_container_width=True)

        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(
                chart_decomposicao_patrimonio(
                    r["total_aportado"],
                    r["total_rendimentos_brutos"],
                    r["total_ir"],
                ),
                use_container_width=True,
            )
        with g2:
            # Evolução de alíquota ao longo do tempo
            fig_aliq = go.Figure()
            fig_aliq.add_trace(go.Scatter(
                x=df["Mês"], y=df["Alíquota IR (%)"],
                fill="tozeroy", fillcolor="rgba(224,92,26,0.15)",
                line=dict(color="#e05c1a", width=2),
                name="Alíquota IR (%)",
            ))
            fig_aliq.update_layout(
                title="Evolução da Alíquota de IR", template="plotly_dark", height=350,
                yaxis_ticksuffix="%", hovermode="x unified",
            )
            if isento_ir:
                st.info("Produto isento de IR — não há incidência de imposto.")
            else:
                st.plotly_chart(fig_aliq, use_container_width=True)

        # ── TABELA ──
        st.divider()
        st.subheader("📅 Evolução Mensal do Patrimônio")
        col_fmt = {col: "{:,.2f}" for col in df.columns if "(R$)" in col}
        st.dataframe(df.style.format(col_fmt), use_container_width=True, height=400)
        csv = df.to_csv(index=False, sep=";", decimal=",")
        st.download_button("⬇️ Exportar CSV", csv, "investimento.csv", "text/csv")

    # ─────────────────────────────────────────────────────────
    # TAB 2 — COMPARATIVO DE PRODUTOS
    # ─────────────────────────────────────────────────────────
    with tab_comp:
        st.subheader("📊 Comparativo de Produtos de Investimento")
        st.caption("Ranking de produtos considerando IR, liquidez e retorno real.")

        with st.expander("⚙️ Parâmetros de Mercado", expanded=False):
            mc1, mc2, mc3 = st.columns(3)
            cdi_pct = mc1.number_input("CDI a.a. (%)", value=13.75, step=0.25, key="cmp_cdi")
            selic_pct = mc2.number_input("Selic a.a. (%)", value=13.75, step=0.25, key="cmp_selic")
            ipca_pct_cmp = mc3.number_input("IPCA a.a. (%)", value=5.0, step=0.25, key="cmp_ipca")

        df_comp = comparar_produtos_investimento(
            capital_inicial=capital_inicial,
            aporte_mensal=aporte_mensal,
            aporte_anual=aporte_anual,
            mes_aporte_anual=mes_aporte_anual,
            prazo_meses=prazo_meses,
            cdi_pct=cdi_pct,
            selic_pct=selic_pct,
            ipca_pct=ipca_pct_cmp,
            mes_inicio=mes_inicio,
        )

        # Tabela
        col_fmt2 = {
            "Patrimônio Final (R$)": "R$ {:,.2f}",
            "Patrimônio Real (R$)": "R$ {:,.2f}",
            "IR Total (R$)": "R$ {:,.2f}",
            "Rentab. Total (%)": "{:.1f}%",
        }
        st.dataframe(df_comp.style.format(col_fmt2), use_container_width=True, hide_index=True)

        # Gráfico de barras
        st.plotly_chart(chart_comparativo_produtos(df_comp), use_container_width=True)

        # Melhor produto
        melhor = df_comp.iloc[0]
        st.success(
            f"🏆 **Melhor resultado:** {melhor['Produto']} — "
            f"Patrimônio Final de {brl(melhor['Patrimônio Final (R$)'])} "
            f"({melhor['Rentab. Total (%)']:.1f}% de rentabilidade total)."
        )

    # ─────────────────────────────────────────────────────────
    # TAB 3 — CALCULADORA DE METAS
    # ─────────────────────────────────────────────────────────
    with tab_meta:
        st.subheader("🎯 Calculadora de Metas Financeiras")
        st.info("Em quanto tempo você atingirá seu objetivo financeiro?")

        mc1, mc2 = st.columns(2)
        with mc1:
            meta_valor = st.number_input("Meta Patrimonial (R$)", value=1_000_000.0, step=50_000.0, key="meta_valor")
            meta_capital = st.number_input("Capital Inicial (R$)", value=capital_inicial, step=5_000.0, key="meta_cap")
            meta_aporte = st.number_input("Aporte Mensal (R$)", value=aporte_mensal, step=100.0, key="meta_aporte")
            meta_taxa = st.number_input("Taxa a.a. (%)", value=taxa_bruta_aa, step=0.5, key="meta_taxa")

        prazo_meta = calc_prazo_para_meta(meta_capital, meta_aporte, meta_taxa, meta_valor)

        with mc2:
            if prazo_meta:
                st.metric("⏱️ Prazo para atingir a meta", meses_para_texto(prazo_meta))

                # Evolução até a meta
                r_meta = simular_investimento(
                    capital_inicial=meta_capital,
                    aporte_mensal=meta_aporte,
                    aporte_anual=0,
                    mes_aporte_anual=12,
                    taxa_bruta_aa_pct=meta_taxa,
                    inflacao_aa_pct=5.0,
                    prazo_meses=prazo_meta,
                )
                fig_meta = go.Figure()
                fig_meta.add_trace(go.Scatter(
                    x=r_meta["df"]["Mês"],
                    y=r_meta["df"]["Patrimônio Líquido (R$)"],
                    fill="tozeroy", fillcolor="rgba(26,173,92,0.15)",
                    line=dict(color="#1aad5c", width=2), name="Patrimônio",
                ))
                fig_meta.add_hline(y=meta_valor, line_dash="dash", line_color="gold",
                                   annotation_text=f"Meta: {brl(meta_valor)}")
                fig_meta.update_layout(
                    title="Trajetória até a Meta",
                    template="plotly_dark", height=340, yaxis_tickprefix="R$ ",
                )
                st.plotly_chart(fig_meta, use_container_width=True)
            else:
                st.error("❌ Meta inalcançável com esses parâmetros (prazo > 100 anos).")

        # Tabela de metas rápidas
        st.divider()
        st.subheader("📋 Prazo para Diferentes Metas")
        metas_rapidas = [100_000, 250_000, 500_000, 1_000_000, 2_000_000, 5_000_000]
        rows_metas = []
        for m in metas_rapidas:
            p = calc_prazo_para_meta(meta_capital, meta_aporte, meta_taxa, m)
            rows_metas.append({
                "Meta": brl(m),
                "Prazo": meses_para_texto(p) if p else "Inatingível",
                "Prazo (meses)": p or "—",
            })
        st.dataframe(pd.DataFrame(rows_metas), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────
    # TAB 4 — RENDA PASSIVA
    # ─────────────────────────────────────────────────────────
    with tab_renda:
        st.subheader("🏖️ Calculadora de Renda Passiva")
        st.caption("Descubra quanto patrimônio é necessário para viver de renda.")

        rp1, rp2 = st.columns(2)
        with rp1:
            renda_desejada = st.number_input("Renda Mensal Desejada (R$)", value=10_000.0, step=500.0, key="rp_renda")
            taxa_renda = st.number_input("Rendimento da Carteira a.a. (%)", value=taxa_bruta_aa, step=0.25, key="rp_taxa")
            inflacao_renda = st.number_input("Inflação Esperada a.a. (%)", value=inflacao_aa, step=0.25, key="rp_inflacao")

        rp_res = calc_renda_passiva(r["patrimonio_final_liquido"], taxa_renda, inflacao_renda)

        with rp2:
            st.metric("Renda Mensal Nominal (com patrimônio atual)", brl(rp_res["renda_nominal_mensal"]))
            st.metric("Renda Mensal Real (descontada inflação)", brl(rp_res["renda_real_mensal"]))

        # Patrimônio necessário para a renda desejada
        taxa_am = taxa_mensal(taxa_renda / 100)
        inflacao_am = taxa_mensal(inflacao_renda / 100)
        taxa_real_am = taxa_am - inflacao_am
        if taxa_real_am > 0:
            patrim_necessario = renda_desejada / taxa_real_am
            st.metric(
                f"💰 Patrimônio Necessário para R$ {renda_desejada:,.0f}/mês de renda real",
                brl(patrim_necessario),
            )
            prazo_necessario = calc_prazo_para_meta(capital_inicial, aporte_mensal, taxa_renda, patrim_necessario)
            if prazo_necessario:
                st.info(f"⏱️ Com seus aportes atuais, você atinge esse patrimônio em **{meses_para_texto(prazo_necessario)}**.")
        else:
            st.warning("Taxa real negativa — aumente o rendimento ou reduza a inflação.")

        # Comparativo: diferentes rendas e patrimônios necessários
        st.divider()
        st.subheader("📋 Tabela: Renda Desejada × Patrimônio Necessário")
        rendas = [3_000, 5_000, 10_000, 15_000, 20_000, 30_000, 50_000]
        rows_renda = []
        for rd in rendas:
            if taxa_real_am > 0:
                pn = rd / taxa_real_am
            else:
                pn = None
            rows_renda.append({
                "Renda Mensal Real (R$)": brl(rd),
                "Patrimônio Necessário": brl(pn) if pn else "—",
                "Prazo com Aportes Atuais": meses_para_texto(calc_prazo_para_meta(capital_inicial, aporte_mensal, taxa_renda, pn)) if pn and calc_prazo_para_meta(capital_inicial, aporte_mensal, taxa_renda, pn) else "—",
            })
        st.dataframe(pd.DataFrame(rows_renda), use_container_width=True, hide_index=True)
