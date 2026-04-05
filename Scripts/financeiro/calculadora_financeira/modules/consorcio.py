"""
Módulo: Consórcio Imobiliário / Auto / Serviços
Lógica alinhada com práticas de mercado Ademicon / Bradesco Consórcios.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from utils.math_engine import simular_consorcio, calc_custo_efetivo_total
from utils.charts import (
    chart_consorcio_evolucao,
    chart_composicao_desembolso_consorcio,
)
from utils.formatters import brl, pct_from_decimal, meses_para_texto, MESES_PT


def render_consorcio():
    st.header("🏛️ Simulador de Consórcio")
    st.caption(
        "Motor financeiro alinhado com as práticas de mercado: **Ademicon**, "
        "**Bradesco Consórcios** e demais administradoras regulamentadas pelo BACEN."
    )

    # ── INPUTS ──────────────────────────────────────────────
    with st.expander("⚙️ Parâmetros do Consórcio", expanded=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.subheader("Carta de Crédito")
            carta = st.number_input("Valor da Carta (R$)", value=900_000.0, step=10_000.0, format="%.2f", key="cons_carta")
            taxa_adm = st.number_input("Taxa de Adm. Total (%)", value=13.0, step=0.5, min_value=0.0, max_value=30.0, key="cons_taxa_adm",
                                        help="Taxa total cobrada ao longo do contrato. Média mercado: 10–18%.")
            prazo = st.number_input("Prazo (meses)", value=200, step=12, min_value=12, max_value=300, key="cons_prazo")
            tipo_bem = st.selectbox("Tipo de Bem", ["Imóvel", "Automóvel", "Serviços / Outros"], key="cons_tipo_bem")

        with c2:
            st.subheader("Lance e Recursos")

            # Categoria calculada em tempo real para exibir referência ao usuário
            categoria_preview = carta * (1 + taxa_adm / 100)
            st.caption(f"**Categoria** = Carta × (1 + Taxa Adm) = **{brl(categoria_preview)}**")

            tipo_lance = st.selectbox(
                "Tipo de Lance",
                ["Sem Lance", "Lance Embutido", "Lance Próprio", "Lance Misto (Embutido + Próprio)"],
                key="cons_tipo_lance",
            )

            # Lance Embutido em % da CATEGORIA
            lance_emb_pct = 0.0
            lance_proprio = 0.0

            if tipo_lance == "Lance Embutido":
                lance_emb_pct = st.slider(
                    "Lance Embutido (% da Categoria)", 0.0, 80.0, 65.0, 0.5,
                    key="cons_lance_emb_pct",
                    help="O lance embutido é calculado sobre a Categoria (Carta + Taxa Adm), não sobre a carta bruta.",
                )
                lance_val_preview = categoria_preview * lance_emb_pct / 100
                st.info(f"Lance Embutido: **{brl(lance_val_preview)}** ({lance_emb_pct:.1f}% da categoria)")
            elif tipo_lance == "Lance Próprio":
                lance_proprio = st.number_input(
                    "Lance Próprio (R$)", value=0.0, step=5_000.0, key="cons_lance_proprio",
                    help="Recurso próprio usado como lance — não sai da carta.",
                )
            elif tipo_lance == "Lance Misto (Embutido + Próprio)":
                lance_emb_pct = st.slider(
                    "Lance Embutido (% da Categoria)", 0.0, 80.0, 40.0, 0.5,
                    key="cons_lance_emb_misto_pct",
                    help="O lance embutido é calculado sobre a Categoria (Carta + Taxa Adm).",
                )
                lance_val_preview = categoria_preview * lance_emb_pct / 100
                lance_proprio = st.number_input(
                    "Lance Próprio Adicional (R$)", value=0.0, step=5_000.0, key="cons_lance_proprio_misto",
                )
                st.info(f"Lance Emb: {brl(lance_val_preview)} + Próprio: {brl(lance_proprio)} = **{brl(lance_val_preview + lance_proprio)}**")

            recurso_proprio = st.number_input(
                "Recurso Próprio (complemento do bem — R$)",
                value=160_000.0, step=5_000.0, key="cons_rec_proprio",
                help="Valor do seu bolso que complementa o crédito líquido para aquisição do bem.",
            )

        with c3:
            st.subheader("Indexação e Adicionais")
            inflacao_aa = st.number_input(
                "INCC / IPCA / Inflação Anual (%)",
                value=5.0, step=0.5, min_value=0.0, max_value=25.0, key="cons_inflacao",
                help="Índice de reajuste anual do consórcio. INCC para imóveis, IPCA/IGP-M para outros.",
            )
            mes_reajuste = st.selectbox(
                "Mês de Reajuste Anual",
                options=list(range(1, 13)),
                format_func=lambda m: MESES_PT[m],
                index=6,  # Julho
                key="cons_mes_reajuste",
                help="Mês do ano em que o saldo devedor é reajustado pelo índice escolhido.",
            )
            mes_inicio = st.selectbox(
                "Mês de Início da Simulação",
                options=list(range(1, 13)),
                format_func=lambda m: MESES_PT[m],
                index=3,  # Abril
                key="cons_mes_inicio",
            )
            fundo_reserva = st.number_input(
                "Fundo de Reserva (% sobre parcela)",
                value=0.0, step=0.1, min_value=0.0, max_value=5.0, key="cons_fundo_res",
                help="Taxa cobrada mensalmente para cobrir inadimplência do grupo.",
            )
            seguro_pct_aa = st.number_input(
                "Seguro de Vida (% da carta a.a.)",
                value=0.0, step=0.01, min_value=0.0, max_value=2.0, key="cons_seguro",
                help="Seguro de vida vinculado ao consórcio, calculado sobre a carta.",
            )
            apreciacao_bem = st.number_input(
                "Apreciação do Bem a.a. (%)",
                value=5.0, step=0.5, key="cons_apreciacao",
                help="Taxa de valorização esperada do imóvel/bem. Usada no cálculo da TIR do projeto.",
            )

    # ── CÁLCULO ─────────────────────────────────────────────
    r = simular_consorcio(
        carta_credito=carta,
        taxa_adm_total_pct=taxa_adm,
        prazo_meses=prazo,
        lance_embutido_pct=lance_emb_pct,       # % da CATEGORIA
        lance_proprio=lance_proprio,
        recurso_proprio=recurso_proprio,
        inflacao_aa_pct=inflacao_aa,
        mes_reajuste=mes_reajuste,
        mes_inicio=mes_inicio,
        fundo_reserva_pct=fundo_reserva,
        seguro_pct_aa=seguro_pct_aa,
        apreciacao_bem_aa_pct=apreciacao_bem,
    )
    df = r["df"]

    # ── PAINEL DE VALIDAÇÃO ──────────────────────────────────
    st.divider()
    st.subheader("📋 Validação de Crédito e Garantia")

    va, vb, vc, vd = st.columns(4)
    va.metric("Categoria (Carta + Adm.)", brl(r["categoria"]))
    vb.metric("Saldo Devedor Inicial", brl(r["devedor_inicial"]))
    vc.metric("Crédito Líquido (Retirar)", brl(r["retirar"]))
    vd.metric("Crédito Total p/ o Bem", brl(r["credito_total"]))

    ve, vf, vg, vh = st.columns(4)
    ve.metric("Bem Necessário (110% SD)", brl(r["bem_necessario_garantia"]))
    vf.metric("Bem Futuro (apreciado)", brl(r["bem_futuro"]))

    if r["aprovado_garantia"]:
        vg.success("✅ Garantia Aprovada")
        vh.info(f"Margem de segurança: {brl(r['credito_total'] - r['bem_necessario_garantia'])}")
    else:
        vg.error("❌ Garantia Insuficiente")
        vh.warning(f"Déficit: {brl(r['bem_necessario_garantia'] - r['credito_total'])}")

    # ── KPIs PRINCIPAIS ─────────────────────────────────────
    st.divider()
    st.subheader("📊 KPIs — Consórcio")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("1ª Parcela Base", brl(r["primeira_parcela_base"]))
    k2.metric("Última Parcela Base", brl(r["ultima_parcela_base"]),
              delta=brl(r["ultima_parcela_base"] - r["primeira_parcela_base"]),
              delta_color="inverse")
    k3.metric("Total Parcelas", brl(r["total_parcelas_base"]))
    k4.metric("Total Desembolsado", brl(r["total_desembolsado"]))
    k5.metric(
        "TIR Crédito a.a.",
        pct_from_decimal(r["tir_credito_aa"]) if r["tir_credito_aa"] else "—",
        help="Custo efetivo do consórcio como instrumento de financiamento do crédito líquido.",
    )
    k6.metric(
        "TIR Projeto a.a.",
        pct_from_decimal(r["tir_projeto_aa"]) if r["tir_projeto_aa"] else "—",
        help="Retorno do projeto incluindo apreciação do bem e desembolso de recurso próprio.",
    )

    # ── GRÁFICOS ────────────────────────────────────────────
    st.divider()
    g1, g2 = st.columns([2, 1])
    with g1:
        st.plotly_chart(chart_consorcio_evolucao(df), use_container_width=True)
    with g2:
        st.plotly_chart(chart_composicao_desembolso_consorcio({**r, "recurso_proprio": recurso_proprio}), use_container_width=True)

    # ── ANÁLISE COMPARATIVA DE LANCE ────────────────────────
    st.divider()
    st.subheader("🎯 Simulação de Cenários de Lance")

    # Cenários de lance expressos como % da CATEGORIA
    categoria_val = r["categoria"]
    lancamentos = {
        "Sem Lance":         {"pct_emb": 0.0,  "lance_prop": 0.0},
        "Lance Emb. 20% cat": {"pct_emb": 20.0, "lance_prop": 0.0},
        "Lance Emb. 40% cat": {"pct_emb": 40.0, "lance_prop": 0.0},
        "Lance Emb. 60% cat": {"pct_emb": 60.0, "lance_prop": 0.0},
        "Lance Emb. 70% cat": {"pct_emb": 70.0, "lance_prop": 0.0},
        "Lance Atual":       {"pct_emb": lance_emb_pct, "lance_prop": lance_proprio},
    }
    rows = []
    for nome, cfg in lancamentos.items():
        res = simular_consorcio(
            carta_credito=carta,
            taxa_adm_total_pct=taxa_adm,
            prazo_meses=prazo,
            lance_embutido_pct=cfg["pct_emb"],
            lance_proprio=cfg["lance_prop"],
            recurso_proprio=recurso_proprio,
            inflacao_aa_pct=inflacao_aa,
            mes_reajuste=mes_reajuste,
            mes_inicio=mes_inicio,
        )
        lance_abs = categoria_val * cfg["pct_emb"] / 100
        rows.append({
            "Cenário": nome,
            "Lance Emb. (% cat)": f"{cfg['pct_emb']:.1f}%",
            "Lance Emb. (R$)": brl(lance_abs),
            "Lance Próprio": brl(cfg["lance_prop"]),
            "1ª Parcela (R$)": brl(res["primeira_parcela_base"]),
            "Crédito p/ Bem": brl(res["credito_total"]),
            "Total Desembolsado": brl(res["total_desembolsado"]),
            "TIR Crédito a.a.": pct_from_decimal(res["tir_credito_aa"]) if res["tir_credito_aa"] else "—",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── TABELA MENSAL ────────────────────────────────────────
    st.divider()
    st.subheader("📅 Tabela Mensal Detalhada")

    col_fmt = {
        "Parcela Base (R$)": "{:,.2f}",
        "Fundo Reserva (R$)": "{:,.2f}",
        "Seguro (R$)": "{:,.2f}",
        "Parcela Total (R$)": "{:,.2f}",
        "Saldo Devedor (R$)": "{:,.2f}",
    }
    st.dataframe(
        df.style.format(col_fmt),
        use_container_width=True,
        height=420,
    )

    # ── DOWNLOAD ─────────────────────────────────────────────
    csv = df.to_csv(index=False, sep=";", decimal=",")
    st.download_button(
        "⬇️ Exportar CSV",
        data=csv,
        file_name="simulacao_consorcio.csv",
        mime="text/csv",
    )

    # ── GLOSSÁRIO ────────────────────────────────────────────
    with st.expander("📖 Glossário e Metodologia"):
        st.markdown("""
| Termo | Definição |
|---|---|
| **Carta de Crédito** | Valor nominal da carta contratada junto à administradora. |
| **Categoria** | `Carta × (1 + Taxa Adm Total)` — valor total que o grupo arrecadará ao longo do prazo. |
| **Lance Embutido** | `Categoria × % lance` — parte da própria carta usada como lance. **Referência: % da Categoria**, não da carta. |
| **Saldo Devedor** | `Categoria − Lance − Parcelas Pagas` — o que ainda resta pagar à administradora. |
| **Parcela Base** | `Saldo Devedor Inicial / Prazo` — recalculada a cada reajuste anual. |
| **Reajuste Anual** | `Parcela Nova = Parcela × (1 + inflação)` e `SD = Parcela Nova × Meses Restantes`. Aplicado no mês aniversário do grupo. |
| **Retirar** | `Carta − Lance Embutido` — crédito líquido disponível após o lance. |
| **Crédito Total** | `Retirar + Recurso Próprio` — valor disponível para aquisição do bem. |
| **TIR Crédito** | IRR do fluxo `[+Retirar, −p1, −p2, ...]` — custo efetivo do consórcio como instrumento de crédito. |
| **TIR Projeto** | IRR incluindo apreciação do bem — retorno sobre o capital próprio investido. |
| **Garantia 110%** | O bem dado em garantia deve valer ≥ 110% do saldo devedor atual (exigência das administradoras). |
        """)
