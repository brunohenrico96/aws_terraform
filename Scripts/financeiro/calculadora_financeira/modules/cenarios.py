"""
Módulo: Análise de Cenários, Sensibilidade e Monte Carlo.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.math_engine import (
    simular_financiamento,
    simular_consorcio,
    simular_investimento,
    monte_carlo_investimento,
    heatmap_financiamento,
    sensibilidade_consorcio,
    taxa_mensal,
)
from utils.charts import (
    chart_heatmap,
    chart_monte_carlo,
    chart_sensibilidade_tornado,
    TEMPLATE,
    COR_INVESTIMENTO,
    COR_CONSORCIO,
    COR_FINANCIAMENTO,
)
from utils.formatters import brl, pct_from_decimal, meses_para_texto, MESES_PT


def render_cenarios():
    st.header("🔭 Análise de Cenários e Sensibilidade")
    st.caption(
        "Ferramentas quantitativas para avaliação de risco e oportunidade: "
        "**heatmaps** de sensibilidade, **Monte Carlo**, **tornado chart** e **análise what-if**."
    )

    tab_hm, tab_mc, tab_tornado, tab_whatif = st.tabs([
        "🌡️ Heatmaps de Sensibilidade",
        "🎲 Monte Carlo",
        "🌪️ Tornado Chart",
        "🔄 What-If Interativo",
    ])

    # ─────────────────────────────────────────────────────────
    # TAB 1 — HEATMAPS
    # ─────────────────────────────────────────────────────────
    with tab_hm:
        st.subheader("🌡️ Sensibilidade: 1ª Parcela × Taxa × Prazo")

        with st.expander("⚙️ Parâmetros do Heatmap", expanded=True):
            h1, h2, h3 = st.columns(3)
            hm_imovel = h1.number_input("Valor do Imóvel (R$)", value=400_000.0, step=10_000.0, key="hm_imovel")
            hm_entrada = h2.number_input("Entrada (%)", value=20.0, step=5.0, key="hm_entrada")
            hm_sistema = h3.selectbox("Sistema", ["SAC", "PRICE", "SAM"], key="hm_sistema")

        taxas = [8.0, 9.0, 10.0, 10.5, 11.0, 12.0, 13.0, 14.0]
        prazos = [120, 180, 240, 300, 360, 420]

        df_hm = heatmap_financiamento(hm_imovel, taxas, prazos, hm_entrada, hm_sistema)
        st.plotly_chart(
            chart_heatmap(df_hm, f"1ª Parcela Total (R$) — {hm_sistema} | Entrada {hm_entrada:.0f}%", colorscale="RdYlGn_r"),
            use_container_width=True,
        )

        # Heatmap de custo total (juros totais)
        st.subheader("💸 Total de Juros × Taxa × Prazo")
        dados_juros = {}
        for prazo in prazos:
            row = {}
            for taxa in taxas:
                r = simular_financiamento(
                    valor_imovel=hm_imovel,
                    entrada=hm_imovel * hm_entrada / 100,
                    prazo_meses=prazo,
                    taxa_juros_aa_pct=taxa,
                    sistema=hm_sistema,
                )
                row[f"{taxa:.1f}%"] = r["total_juros"]
            dados_juros[f"{prazo}m"] = row
        df_juros = pd.DataFrame(dados_juros).T
        st.plotly_chart(
            chart_heatmap(df_juros, f"Total de Juros (R$) — {hm_sistema}", colorscale="Reds"),
            use_container_width=True,
        )

        # Heatmap consórcio
        st.subheader("🏛️ Sensibilidade Consórcio: Total Desembolsado × INCC × Prazo")
        with st.expander("⚙️ Parâmetros Consórcio Heatmap"):
            c1hm, c2hm = st.columns(2)
            hm_carta = c1hm.number_input("Carta de Crédito (R$)", value=900_000.0, step=10_000.0, key="hm_carta")
            hm_taxa_adm = c2hm.number_input("Taxa Adm. Total (%)", value=13.0, step=0.5, key="hm_taxa_adm")

        inflacoes = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        prazos_cons = [120, 150, 180, 200, 240, 300]
        df_cons_hm = sensibilidade_consorcio(hm_carta, hm_taxa_adm, 200, inflacoes, prazos_cons)
        st.plotly_chart(
            chart_heatmap(df_cons_hm, "Total Desembolsado Consórcio (R$) × INCC × Prazo", colorscale="Blues_r"),
            use_container_width=True,
        )

    # ─────────────────────────────────────────────────────────
    # TAB 2 — MONTE CARLO
    # ─────────────────────────────────────────────────────────
    with tab_mc:
        st.subheader("🎲 Simulação de Monte Carlo — Patrimônio Futuro")
        st.caption(
            "Projeta a **distribuição de possíveis patrimônios futuros** considerando "
            "volatilidade nos retornos de mercado. Ideal para avaliar risco de portfólio."
        )

        with st.expander("⚙️ Parâmetros Monte Carlo", expanded=True):
            mc1, mc2, mc3 = st.columns(3)
            mc_capital = mc1.number_input("Capital Inicial (R$)", value=160_000.0, step=5_000.0, key="mc_cap")
            mc_aporte = mc1.number_input("Aporte Mensal (R$)", value=2_000.0, step=500.0, key="mc_aporte")
            mc_taxa = mc2.number_input("Retorno Médio a.a. (%)", value=12.0, step=0.5, key="mc_taxa")
            mc_vol = mc2.number_input(
                "Volatilidade a.a. (%)", value=8.0, step=1.0, key="mc_vol",
                help="Desvio padrão anual do retorno. Renda fixa: ~1–3%. Multimercado: 5–10%. Ações: 15–25%.",
            )
            mc_prazo = mc3.number_input("Prazo (meses)", value=120, step=12, key="mc_prazo")
            mc_n = mc3.number_input("Número de Simulações", value=500, step=100, min_value=100, max_value=5000, key="mc_n")

        with st.spinner("Rodando simulações Monte Carlo..."):
            df_mc = monte_carlo_investimento(
                capital_inicial=mc_capital,
                aporte_mensal=mc_aporte,
                taxa_media_aa=mc_taxa,
                volatilidade_aa=mc_vol,
                prazo_meses=mc_prazo,
                n_simulacoes=int(mc_n),
            )

        st.plotly_chart(chart_monte_carlo(df_mc), use_container_width=True)

        mc_final = df_mc.iloc[-1]
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("P10 (pessimista)", brl(mc_final["P10"]))
        m2.metric("P25", brl(mc_final["P25"]))
        m3.metric("P50 (mediana)", brl(mc_final["P50"]))
        m4.metric("P75", brl(mc_final["P75"]))
        m5.metric("P90 (otimista)", brl(mc_final["P90"]))

        amplitude = mc_final["P90"] - mc_final["P10"]
        st.info(
            f"📊 **Amplitude do resultado** (P90 − P10): {brl(amplitude)} | "
            f"Volatilidade: {mc_vol:.1f}% a.a. | "
            f"{int(mc_n)} simulações × {mc_prazo} meses."
        )

        # Histograma do valor final
        fig_hist = go.Figure(go.Histogram(
            x=df_mc["P50"].tolist(),
            nbinsx=50,
            marker_color=COR_INVESTIMENTO,
            opacity=0.8,
            name="Distribuição Patrimônio Final",
        ))
        final_values = np.array([mc_final["P50"]])
        fig_hist.update_layout(
            title="Distribuição do Patrimônio no Período Final",
            template=TEMPLATE, height=340,
            xaxis_tickprefix="R$ ",
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # ─────────────────────────────────────────────────────────
    # TAB 3 — TORNADO
    # ─────────────────────────────────────────────────────────
    with tab_tornado:
        st.subheader("🌪️ Tornado Chart — Análise de Sensibilidade por Variável")
        st.caption(
            "Mostra o impacto de cada variável sobre o **patrimônio final** do investimento. "
            "Cada barra representa o resultado com a variável no extremo otimista e pessimista."
        )

        with st.expander("⚙️ Parâmetros Base", expanded=True):
            tb1, tb2 = st.columns(2)
            t_capital = tb1.number_input("Capital Inicial Base (R$)", value=160_000.0, step=5_000.0, key="t_cap")
            t_aporte = tb1.number_input("Aporte Mensal Base (R$)", value=2_000.0, step=500.0, key="t_aporte")
            t_taxa = tb2.number_input("Taxa Base a.a. (%)", value=12.0, step=0.5, key="t_taxa")
            t_prazo = tb2.number_input("Prazo Base (meses)", value=120, step=12, key="t_prazo")
            t_inflacao = tb2.number_input("Inflação Base (%)", value=5.0, step=0.5, key="t_inflacao")

        def simular_pat(cap, aporte, taxa, prazo, inflacao):
            r = simular_investimento(
                capital_inicial=cap, aporte_mensal=aporte, aporte_anual=0,
                mes_aporte_anual=12, taxa_bruta_aa_pct=taxa,
                inflacao_aa_pct=inflacao, prazo_meses=prazo,
            )
            return r["patrimonio_final_liquido"]

        baseline = simular_pat(t_capital, t_aporte, t_taxa, t_prazo, t_inflacao)

        variacoes = {
            "Taxa de Juros": (
                simular_pat(t_capital, t_aporte, t_taxa * 1.3, t_prazo, t_inflacao),
                simular_pat(t_capital, t_aporte, t_taxa * 0.7, t_prazo, t_inflacao),
            ),
            "Aporte Mensal": (
                simular_pat(t_capital, t_aporte * 1.5, t_taxa, t_prazo, t_inflacao),
                simular_pat(t_capital, t_aporte * 0.5, t_taxa, t_prazo, t_inflacao),
            ),
            "Capital Inicial": (
                simular_pat(t_capital * 1.5, t_aporte, t_taxa, t_prazo, t_inflacao),
                simular_pat(t_capital * 0.5, t_aporte, t_taxa, t_prazo, t_inflacao),
            ),
            "Prazo": (
                simular_pat(t_capital, t_aporte, t_taxa, int(t_prazo * 1.25), t_inflacao),
                simular_pat(t_capital, t_aporte, t_taxa, int(t_prazo * 0.75), t_inflacao),
            ),
            "Inflação": (
                simular_pat(t_capital, t_aporte, t_taxa, t_prazo, t_inflacao * 0.5),
                simular_pat(t_capital, t_aporte, t_taxa, t_prazo, t_inflacao * 1.5),
            ),
        }

        st.metric("Patrimônio Final Base", brl(baseline))
        st.plotly_chart(
            chart_sensibilidade_tornado(variacoes, baseline, "Tornado: Impacto sobre Patrimônio Final"),
            use_container_width=True,
        )

        # Tabela de sensibilidade
        rows_t = []
        for var, (otim, pess) in variacoes.items():
            rows_t.append({
                "Variável": var,
                "Cenário Otimista": brl(otim),
                "Impacto Otimista": brl(otim - baseline),
                "Cenário Pessimista": brl(pess),
                "Impacto Pessimista": brl(pess - baseline),
            })
        st.dataframe(pd.DataFrame(rows_t), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────
    # TAB 4 — WHAT-IF INTERATIVO
    # ─────────────────────────────────────────────────────────
    with tab_whatif:
        st.subheader("🔄 Análise What-If — Simulação Paramétrica em Tempo Real")
        st.caption("Ajuste os sliders e veja o impacto imediato nos resultados.")

        wi1, wi2 = st.columns(2)

        with wi1:
            st.markdown("#### Parâmetros do Financiamento")
            wi_imovel = st.slider("Valor do Imóvel (R$ mil)", 100, 2_000, 400, 25, key="wi_imovel") * 1_000
            wi_entrada_pct = st.slider("Entrada (%)", 5, 80, 20, 5, key="wi_entrada")
            wi_taxa = st.slider("Taxa a.a. (%)", 6.0, 20.0, 10.5, 0.25, key="wi_taxa")
            wi_prazo = st.slider("Prazo (anos)", 5, 35, 30, 1, key="wi_prazo") * 12

            wi_res_sac = simular_financiamento(
                valor_imovel=wi_imovel,
                entrada=wi_imovel * wi_entrada_pct / 100,
                prazo_meses=wi_prazo,
                taxa_juros_aa_pct=wi_taxa,
                sistema="SAC",
            )
            wi_res_price = simular_financiamento(
                valor_imovel=wi_imovel,
                entrada=wi_imovel * wi_entrada_pct / 100,
                prazo_meses=wi_prazo,
                taxa_juros_aa_pct=wi_taxa,
                sistema="PRICE",
            )

            st.markdown("#### Resultados Imediatos")
            w1, w2 = st.columns(2)
            w1.metric("SAC — 1ª Parcela", brl(wi_res_sac["primeira_parcela_total"]))
            w1.metric("SAC — Total Juros", brl(wi_res_sac["total_juros"]))
            w2.metric("PRICE — Parcela Fixa", brl(wi_res_price["primeira_parcela_total"]))
            w2.metric("PRICE — Total Juros", brl(wi_res_price["total_juros"]))

        with wi2:
            st.markdown("#### Parâmetros do Consórcio")
            wi_carta = st.slider("Carta de Crédito (R$ mil)", 100, 2_000, 900, 50, key="wi_carta") * 1_000
            wi_taxa_adm = st.slider("Taxa Adm. Total (%)", 8.0, 25.0, 13.0, 0.5, key="wi_taxa_adm")
            wi_prazo_cons = st.slider("Prazo Consórcio (meses)", 60, 300, 200, 12, key="wi_prazo_cons")
            wi_lance_pct = st.slider(
                "Lance Embutido (% da Categoria)", 0.0, 80.0, 65.0, 5.0, key="wi_lance_pct",
                help="Lance calculado sobre a Categoria (Carta × (1 + Taxa Adm)).",
            )
            wi_inflacao = st.slider("INCC a.a. (%)", 2.0, 15.0, 5.0, 0.5, key="wi_inflacao_cons")

            wi_res_cons = simular_consorcio(
                carta_credito=wi_carta,
                taxa_adm_total_pct=wi_taxa_adm,
                prazo_meses=wi_prazo_cons,
                lance_embutido_pct=wi_lance_pct,   # % da CATEGORIA
                inflacao_aa_pct=wi_inflacao,
            )

            st.markdown("#### Resultados Imediatos")
            wc1, wc2 = st.columns(2)
            wc1.metric("1ª Parcela Consórcio", brl(wi_res_cons["primeira_parcela_base"]))
            wc1.metric("Crédito Disponível", brl(wi_res_cons["credito_total"]))
            wc2.metric("Total Desembolsado", brl(wi_res_cons["total_desembolsado"]))
            wc2.metric("TIR Crédito a.a.", pct_from_decimal(wi_res_cons["tir_credito_aa"]) if wi_res_cons["tir_credito_aa"] else "—")

        # Gráfico comparativo what-if
        st.divider()
        fig_wi = go.Figure()
        df_wi_sac = wi_res_sac["df"]
        df_wi_cons = wi_res_cons["df"]

        prazo_min = min(len(df_wi_sac), len(df_wi_cons))
        fig_wi.add_trace(go.Scatter(
            x=df_wi_sac["Mês"][:prazo_min],
            y=df_wi_sac["Parcela Total (R$)"][:prazo_min],
            name="Financiamento SAC", line=dict(color=COR_FINANCIAMENTO, width=2),
        ))
        fig_wi.add_trace(go.Scatter(
            x=df_wi_cons["Mês"][:prazo_min],
            y=df_wi_cons["Parcela Total (R$)"][:prazo_min],
            name="Consórcio", line=dict(color=COR_CONSORCIO, width=2),
        ))
        fig_wi.update_layout(
            title="Parcela Mensal: Financiamento SAC vs Consórcio",
            template=TEMPLATE, height=360, yaxis_tickprefix="R$ ", hovermode="x unified",
        )
        st.plotly_chart(fig_wi, use_container_width=True)
