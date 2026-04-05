"""
Módulo: Financiamento Imobiliário
Sistemas SAC | PRICE | SAM — FGTS — Amortização Antecipada — Portabilidade.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.graph_objects as go

from utils.math_engine import (
    simular_financiamento,
    simular_portabilidade,
    taxa_mensal,
    taxa_anual,
)
from utils.charts import (
    chart_financiamento_amortizacao,
    chart_financiamento_saldo,
    chart_comparativo_sistemas,
)
from utils.formatters import brl, pct_from_decimal, meses_para_texto


def render_financiamento():
    st.header("🏦 Simulador de Financiamento Imobiliário")
    st.caption(
        "Sistemas **SAC** (amortização constante), **PRICE** (parcela constante) e "
        "**SAM** (sistema de amortização misto — utilizado pela Caixa Econômica Federal). "
        "Inclui seguros MIP/DFI, FGTS e amortização antecipada."
    )

    tab_principal, tab_comparar, tab_portab = st.tabs([
        "📊 Simulação Principal",
        "⚖️ Comparar SAC vs PRICE",
        "🔄 Portabilidade de Crédito",
    ])

    # ─────────────────────────────────────────────────────────
    # TAB 1 — SIMULAÇÃO PRINCIPAL
    # ─────────────────────────────────────────────────────────
    with tab_principal:
        with st.expander("⚙️ Parâmetros do Financiamento", expanded=True):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.subheader("Imóvel e Entrada")
                valor_imovel = st.number_input("Valor do Imóvel (R$)", value=400_000.0, step=10_000.0, format="%.2f", key="fin_imovel")
                entrada_pct = st.slider("Entrada (%)", 0.0, 80.0, 20.0, 1.0, key="fin_entrada_pct")
                entrada_val = valor_imovel * entrada_pct / 100
                st.info(f"Entrada: {brl(entrada_val)}")
                fgts = st.number_input("FGTS utilizado (R$)", value=0.0, step=1_000.0, key="fin_fgts",
                                        help="FGTS pode ser usado para complementar entrada ou amortizar saldo.")
                saldo_financiado = max(valor_imovel - entrada_val - fgts, 0)
                st.metric("Saldo Financiado", brl(saldo_financiado))

            with c2:
                st.subheader("Condições do Financiamento")
                prazo = st.number_input("Prazo (meses)", value=360, step=12, min_value=12, max_value=420, key="fin_prazo")
                taxa_aa = st.number_input(
                    "Taxa de Juros a.a. (%)", value=10.5, step=0.25, min_value=0.1, max_value=30.0, key="fin_taxa",
                    help="CET (Custo Efetivo Total) ou taxa de juros nominal. Ex: Caixa/Minha Casa = 8–10%, SBPE = 10–12%.",
                )
                sistema = st.selectbox("Sistema de Amortização", ["SAC", "PRICE", "SAM"], key="fin_sistema")
                taxa_admin_mensal = st.number_input(
                    "Taxa de Administração (R$/mês)", value=25.0, step=5.0, key="fin_admin",
                    help="Taxa fixa cobrada mensalmente pelo banco (ex: R$ 25/mês).",
                )

            with c3:
                st.subheader("Seguros e Amortização Extra")
                seg_mip = st.number_input(
                    "Seguro MIP (% a.a. sobre SD)", value=0.30, step=0.01, min_value=0.0, max_value=3.0, key="fin_mip",
                    help="Seguro de Morte e Invalidez Permanente. Calculado sobre o saldo devedor mensal.",
                )
                seg_dfi = st.number_input(
                    "Seguro DFI (% a.a. sobre SD)", value=0.03, step=0.01, min_value=0.0, max_value=1.0, key="fin_dfi",
                    help="Seguro de Danos Físicos ao Imóvel.",
                )
                apreciacao = st.number_input("Apreciação do Imóvel a.a. (%)", value=5.0, step=0.5, key="fin_apreciacao")
                st.divider()
                st.markdown("**Amortização Antecipada**")
                amort_mes_inicio = st.number_input(
                    "Iniciar amortização extra a partir do mês", value=0, step=1, min_value=0, key="fin_amort_mes",
                    help="0 = sem amortização extra.",
                )
                amort_extra = st.number_input(
                    "Valor da amortização extra (R$/mês)", value=0.0, step=500.0, key="fin_amort_extra",
                ) if amort_mes_inicio > 0 else 0.0

        # ── CÁLCULO ──
        r = simular_financiamento(
            valor_imovel=valor_imovel,
            entrada=entrada_val,
            prazo_meses=prazo,
            taxa_juros_aa_pct=taxa_aa,
            sistema=sistema,
            fgts=fgts,
            seguro_mip_pct_aa=seg_mip,
            seguro_dfi_pct_aa=seg_dfi,
            taxa_admin_mensal=taxa_admin_mensal,
            apreciacao_aa_pct=apreciacao,
            amort_extra_mes=amort_mes_inicio,
            amort_extra_valor=amort_extra,
        )
        df = r["df"]

        # ── KPIs ──
        st.divider()
        st.subheader("📊 KPIs — Financiamento")
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Saldo Financiado", brl(r["saldo_financiado"]))
        k2.metric("1ª Parcela Total", brl(r["primeira_parcela_total"]))
        k3.metric("Última Parcela Total", brl(r["ultima_parcela_total"]),
                  delta=brl(r["ultima_parcela_total"] - r["primeira_parcela_total"]))
        k4.metric("Total Pago", brl(r["total_pago"]))
        k5.metric(
            "CET a.a. (TIR)",
            pct_from_decimal(r["tir_aa"]) if r["tir_aa"] else "—",
            help="Custo Efetivo Total anual, inclui juros, seguros e taxas.",
        )
        k6.metric(
            "TIR Projeto a.a.",
            pct_from_decimal(r["tir_proj_aa"]) if r["tir_proj_aa"] else "—",
            help="Retorno do projeto incluindo apreciação do imóvel.",
        )

        ka, kb, kc, kd = st.columns(4)
        ka.metric("Total de Juros", brl(r["total_juros"]))
        kb.metric("Total de Seguros", brl(r["total_seguros"]))
        kc.metric("Total Adm.", brl(r["total_admin"]))
        kd.metric("Prazo Real (meses)", meses_para_texto(r["prazo_real_meses"]))

        # ── GRÁFICOS ──
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(chart_financiamento_amortizacao(df, sistema), use_container_width=True)
        with g2:
            st.plotly_chart(chart_financiamento_saldo(df), use_container_width=True)

        # ── TABELA ──
        st.divider()
        st.subheader("📅 Tabela de Amortização Detalhada")
        col_fmt = {col: "{:,.2f}" for col in df.columns if "(R$)" in col}
        st.dataframe(df.style.format(col_fmt), use_container_width=True, height=400)
        csv = df.to_csv(index=False, sep=";", decimal=",")
        st.download_button("⬇️ Exportar CSV", csv, "financiamento.csv", "text/csv")

    # ─────────────────────────────────────────────────────────
    # TAB 2 — COMPARAR SAC vs PRICE
    # ─────────────────────────────────────────────────────────
    with tab_comparar:
        st.subheader("⚖️ SAC vs PRICE vs SAM — Comparação Detalhada")
        st.info(
            "Os parâmetros do imóvel, taxa e prazo são reaproveitados da aba principal. "
            "Ajuste-os lá para atualizar esta comparação."
        )

        sistemas = ["SAC", "PRICE", "SAM"]
        resultados = {}
        dfs_sistemas = {}

        for s in sistemas:
            res = simular_financiamento(
                valor_imovel=valor_imovel,
                entrada=entrada_val,
                prazo_meses=prazo,
                taxa_juros_aa_pct=taxa_aa,
                sistema=s,
                fgts=fgts,
                seguro_mip_pct_aa=seg_mip,
                seguro_dfi_pct_aa=seg_dfi,
                taxa_admin_mensal=taxa_admin_mensal,
            )
            resultados[s] = res
            dfs_sistemas[s] = res["df"]

        # Tabela comparativa
        comp = []
        for s in sistemas:
            res = resultados[s]
            comp.append({
                "Sistema": s,
                "1ª Parcela Total": brl(res["primeira_parcela_total"]),
                "Última Parcela Total": brl(res["ultima_parcela_total"]),
                "Total Juros": brl(res["total_juros"]),
                "Total Seguros": brl(res["total_seguros"]),
                "Total Pago": brl(res["total_pago"]),
                "CET a.a.": pct_from_decimal(res["tir_aa"]) if res["tir_aa"] else "—",
            })
        st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True)

        # Gráfico comparativo de parcelas
        if len(dfs_sistemas) >= 2:
            st.plotly_chart(
                chart_comparativo_sistemas(dfs_sistemas["SAC"], dfs_sistemas["PRICE"]),
                use_container_width=True,
            )

        # Gráfico empilhado: juros acumulados por sistema
        fig_jur = go.Figure()
        for s, color in zip(sistemas, ["#1a6db5", "#e05c1a", "#1aad5c"]):
            df_s = dfs_sistemas[s]
            fig_jur.add_trace(go.Scatter(
                x=df_s["Mês"],
                y=df_s["Juros (R$)"].cumsum(),
                name=s,
                line=dict(color=color, width=2),
            ))
        fig_jur.update_layout(
            title="Juros Acumulados por Sistema",
            template="plotly_dark",
            height=380,
            yaxis_tickprefix="R$ ",
            hovermode="x unified",
        )
        st.plotly_chart(fig_jur, use_container_width=True)

        with st.expander("📖 Diferenças entre os sistemas"):
            st.markdown("""
| Sistema | Amortização | Parcela | Ideal para |
|---|---|---|---|
| **SAC** | Constante | Decrescente | Quem pode pagar mais no início e quer pagar menos juros totais |
| **PRICE** | Crescente | Constante | Quem precisa de previsibilidade de caixa |
| **SAM** | Misto | Levemente decrescente | Equilíbrio entre SAC e PRICE (Caixa Econômica Federal) |

**Regra geral:** SAC paga **menos juros no total** que PRICE, mas a primeira parcela é maior.
            """)

    # ─────────────────────────────────────────────────────────
    # TAB 3 — PORTABILIDADE
    # ─────────────────────────────────────────────────────────
    with tab_portab:
        st.subheader("🔄 Simulador de Portabilidade de Crédito Imobiliário")
        st.info(
            "A portabilidade permite transferir seu financiamento para outro banco com taxa menor, "
            "mantendo o prazo e o saldo devedor atual."
        )

        pc1, pc2 = st.columns(2)
        with pc1:
            sd_atual = st.number_input("Saldo Devedor Atual (R$)", value=350_000.0, step=5_000.0, key="port_sd")
            taxa_atual = st.number_input("Taxa Atual a.a. (%)", value=11.5, step=0.25, key="port_taxa_atual")
            prazo_rest = st.number_input("Prazo Restante (meses)", value=300, step=12, key="port_prazo")
        with pc2:
            taxa_nova = st.number_input("Nova Taxa a.a. (%)", value=9.5, step=0.25, key="port_taxa_nova")
            custo_port = st.number_input(
                "Custo da Portabilidade (R$)", value=3_000.0, step=500.0, key="port_custo",
                help="Custos cartorários, avaliação do imóvel, IOF etc.",
            )

        if taxa_nova >= taxa_atual:
            st.warning("⚠️ A nova taxa deve ser menor que a atual para a portabilidade fazer sentido.")
        else:
            p = simular_portabilidade(sd_atual, taxa_atual, taxa_nova, prazo_rest, custo_port)

            pa, pb, pc, pd_ = st.columns(4)
            pa.metric("Parcela Atual (estimada)", brl(p["pmt_atual"]))
            pb.metric("Nova Parcela (estimada)", brl(p["pmt_nova"]),
                      delta=brl(p["pmt_nova"] - p["pmt_atual"]), delta_color="inverse")
            pc.metric("Economia Mensal", brl(p["economia_mensal"]))
            pd_.metric("Economia Total Líquida", brl(p["economia_total"]))

            if p["payback_meses"] is not None:
                st.success(
                    f"✅ Os custos da portabilidade se pagam em **{p['payback_meses']:.1f} meses** "
                    f"({meses_para_texto(int(p['payback_meses']))}). "
                    f"A partir daí, economia pura de {brl(p['economia_mensal'])}/mês."
                )
