"""
Motor Matemático Financeiro — Versão Institucional
Cobre: Consórcio | Financiamento | Investimento | Comparação
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import numpy_financial as npf
import pandas as pd


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def taxa_mensal(taxa_anual: float) -> float:
    """Converte taxa anual (decimal) em taxa mensal equivalente."""
    return (1 + taxa_anual) ** (1 / 12) - 1


def taxa_anual(taxa_mensal_val: float) -> float:
    """Converte taxa mensal (decimal) em taxa anual equivalente."""
    return (1 + taxa_mensal_val) ** 12 - 1


def safe_irr(cash_flows: list[float]) -> Optional[float]:
    """Calcula IRR com tratamento de erro."""
    try:
        irr = npf.irr(cash_flows)
        if irr is None or np.isnan(irr) or np.isinf(irr):
            return None
        return float(irr)
    except Exception:
        return None


def safe_npv(rate_monthly: float, cash_flows: list[float]) -> float:
    """Calcula NPV (VPL)."""
    try:
        return float(npf.npv(rate_monthly, cash_flows))
    except Exception:
        return 0.0


def aliquota_ir_renda_fixa(dias: int) -> float:
    """Tabela regressiva de IR para renda fixa."""
    if dias <= 180:
        return 0.225
    elif dias <= 360:
        return 0.200
    elif dias <= 720:
        return 0.175
    else:
        return 0.150


def iof_renda_fixa(dias: int) -> float:
    """IOF regressivo para renda fixa (dia 1 = 96%, dia 30 = 0%)."""
    tabela = [
        96, 93, 90, 86, 83, 80, 76, 73, 70, 66,
        63, 60, 56, 53, 50, 46, 43, 40, 36, 33,
        30, 26, 23, 20, 16, 13, 10, 6, 3, 0
    ]
    if dias <= 0:
        return 0.96
    if dias >= 30:
        return 0.0
    return tabela[dias - 1] / 100


# ─────────────────────────────────────────────────────────────
# CONSÓRCIO
# ─────────────────────────────────────────────────────────────

def simular_consorcio(
    carta_credito: float,
    taxa_adm_total_pct: float,
    prazo_meses: int,
    lance_embutido_pct: float = 0.0,   # % da CATEGORIA (não da carta)
    lance_proprio: float = 0.0,
    recurso_proprio: float = 0.0,
    inflacao_aa_pct: float = 5.0,
    mes_reajuste: int = 7,
    mes_inicio: int = 4,
    fundo_reserva_pct: float = 0.0,
    seguro_pct_aa: float = 0.0,
    apreciacao_bem_aa_pct: float = 5.0,
    mes_contemplacao: int = 1,
) -> dict:
    """
    Simula um consórcio completo.

    Fórmulas conforme prática de mercado (Ademicon / Bradesco Consórcios):

        categoria       = carta × (1 + taxa_adm_total)
        lance_embutido  = categoria × lance_embutido_pct / 100
        saldo_devedor   = categoria − lance_embutido − lance_próprio − parcelas_pagas
        parcela_base    = saldo_devedor_inicial / prazo_meses
        reajuste_anual  → parcela = parcela × (1 + inflação)
                          SD      = parcela_nova × meses_restantes
        retirar         = carta − lance_embutido   (crédito líquido da carta)
        crédito_total   = retirar + recurso_próprio (valor disponível para o bem)

    TIR Crédito : IRR([+retirar, −p1, −p2, ...])       custo efetivo do crédito
    TIR Projeto : IRR([−rec_proprio, −p1, ..., +bem])   retorno sobre capital próprio
    """
    inflacao_aa = inflacao_aa_pct / 100
    taxa_adm = taxa_adm_total_pct / 100
    seguro_aa = seguro_pct_aa / 100
    apreciacao_aa = apreciacao_bem_aa_pct / 100

    # ── Grandezas iniciais ──
    categoria = carta_credito * (1 + taxa_adm)
    lance_embutido = categoria * lance_embutido_pct / 100   # % da CATEGORIA
    devedor_inicial = categoria - lance_embutido - lance_proprio
    retirar = carta_credito - lance_embutido          # crédito líquido da carta
    credito_total = retirar + recurso_proprio          # valor total para o bem
    bem_necessario_garantia = devedor_inicial * 1.10   # 110% do saldo devedor
    aprovado_garantia = credito_total >= bem_necessario_garantia

    # ── Simulação mensal ──
    sd = devedor_inicial
    meses_restantes = prazo_meses
    historico = []
    cf_credito = [+retirar]            # TIR custo de crédito: recebe retirar no t=0
    cf_projeto = [-recurso_proprio]    # TIR do projeto: desembolsa recurso próprio

    total_parcelas_base = 0.0
    total_fundo_reserva = 0.0
    total_seguro = 0.0

    parcela_atual = devedor_inicial / prazo_meses if prazo_meses > 0 else 0

    for i in range(prazo_meses):
        mes_seq = i + 1
        mes_cal = ((mes_inicio - 1 + i) % 12) + 1

        # Reajuste anual (exceto no 1º mês):
        #   parcela_nova = parcela × (1 + inflação)
        #   SD ajustado  = parcela_nova × meses_restantes
        is_reajuste = (mes_cal == mes_reajuste) and (i > 0)
        if is_reajuste:
            parcela_atual = parcela_atual * (1 + inflacao_aa)
            sd = parcela_atual * meses_restantes

        fr = parcela_atual * fundo_reserva_pct / 100
        seg = carta_credito * seguro_aa / 12
        parcela_total_mes = parcela_atual + fr + seg

        total_parcelas_base += parcela_atual
        total_fundo_reserva += fr
        total_seguro += seg

        cf_credito.append(-parcela_total_mes)
        cf_projeto.append(-parcela_total_mes)

        sd -= parcela_atual
        meses_restantes -= 1

        historico.append({
            "Mês": mes_seq,
            "Mês Calendário": mes_cal,
            "Parcela Base (R$)": parcela_atual,
            "Fundo Reserva (R$)": fr,
            "Seguro (R$)": seg,
            "Parcela Total (R$)": parcela_total_mes,
            "Saldo Devedor (R$)": max(sd, 0),
            "Reajuste?": "✅" if is_reajuste else "",
        })

    # ── Bem futuro (para TIR do projeto) ──
    anos = prazo_meses / 12
    bem_futuro = credito_total * (1 + apreciacao_aa) ** anos
    cf_projeto[-1] += bem_futuro  # valor do bem no final

    # ── TIRs ──
    tir_credito_am = safe_irr(cf_credito)
    tir_credito_aa = taxa_anual(tir_credito_am) if tir_credito_am else None

    tir_projeto_am = safe_irr(cf_projeto)
    tir_projeto_aa = taxa_anual(tir_projeto_am) if tir_projeto_am else None

    df = pd.DataFrame(historico)

    total_desembolsado = recurso_proprio + lance_proprio + total_parcelas_base + total_fundo_reserva + total_seguro

    return {
        # Grandezas
        "categoria": categoria,
        "lance_embutido": lance_embutido,
        "lance_proprio": lance_proprio,
        "devedor_inicial": devedor_inicial,
        "retirar": retirar,
        "credito_total": credito_total,
        "bem_necessario_garantia": bem_necessario_garantia,
        "aprovado_garantia": aprovado_garantia,
        # Parcelas
        "primeira_parcela_base": df["Parcela Base (R$)"].iloc[0] if len(df) > 0 else 0,
        "ultima_parcela_base": df["Parcela Base (R$)"].iloc[-1] if len(df) > 0 else 0,
        "primeira_parcela_total": df["Parcela Total (R$)"].iloc[0] if len(df) > 0 else 0,
        # Totais
        "total_parcelas_base": total_parcelas_base,
        "total_fundo_reserva": total_fundo_reserva,
        "total_seguro": total_seguro,
        "total_desembolsado": total_desembolsado,
        "bem_futuro": bem_futuro,
        # TIRs
        "tir_credito_am": tir_credito_am,
        "tir_credito_aa": tir_credito_aa,
        "tir_projeto_am": tir_projeto_am,
        "tir_projeto_aa": tir_projeto_aa,
        # Tabela
        "df": df,
    }


# ─────────────────────────────────────────────────────────────
# FINANCIAMENTO — SAC / PRICE / SAM
# ─────────────────────────────────────────────────────────────

def simular_financiamento(
    valor_imovel: float,
    entrada: float,
    prazo_meses: int,
    taxa_juros_aa_pct: float,
    sistema: str = "SAC",           # "SAC" | "PRICE" | "SAM"
    fgts: float = 0.0,              # FGTS usado na entrada
    seguro_mip_pct_aa: float = 0.30,# MIP (morte e invalidez)
    seguro_dfi_pct_aa: float = 0.03,# DFI (danos físicos)
    taxa_admin_mensal: float = 25.0,# Taxa de administração bancária (R$/mês)
    apreciacao_aa_pct: float = 5.0,
    amort_extra_mes: int = 0,       # Mês para início de amortização extra
    amort_extra_valor: float = 0.0, # Valor da amortização extra mensal
) -> dict:
    """
    Simula financiamento imobiliário (SAC, PRICE ou SAM).
    Retorna métricas e DataFrame mensal.

    SAC  — amortização constante, juros decrescentes
    PRICE — parcela constante, amortização crescente
    SAM  — média aritmética entre SAC e PRICE (Caixa)
    """
    taxa_aa = taxa_juros_aa_pct / 100
    taxa_am = taxa_mensal(taxa_aa)
    saldo_financiado = valor_imovel - entrada - fgts

    mip_am = seguro_mip_pct_aa / 100 / 12
    dfi_am = seguro_dfi_pct_aa / 100 / 12

    historico = []
    # CET = custo efetivo do crédito: recebe o saldo financiado, paga as parcelas
    cf_cet = [saldo_financiado]
    # TIR projeto: desembolsa entrada, paga parcelas, recebe bem no final
    cf_proj = [-entrada]

    saldo = saldo_financiado
    total_pago = entrada
    total_juros = 0.0
    total_seguros = 0.0
    total_admin = 0.0

    # Pré-calcula parcela PRICE (constante)
    if sistema == "PRICE" and taxa_am > 0:
        parcela_price = npf.pmt(taxa_am, prazo_meses, -saldo_financiado)
    elif sistema == "PRICE":
        parcela_price = saldo_financiado / prazo_meses
    else:
        parcela_price = 0

    for i in range(prazo_meses):
        mes_seq = i + 1
        meses_rest = prazo_meses - i

        juros = saldo * taxa_am

        if sistema == "SAC":
            amort = saldo_financiado / prazo_meses
        elif sistema == "PRICE":
            amort = parcela_price - juros
        else:  # SAM
            amort_sac = saldo_financiado / prazo_meses
            amort_price = parcela_price - juros if taxa_am > 0 else saldo / meses_rest
            amort = (amort_sac + amort_price) / 2

        # Amortização extra
        amort_extra = amort_extra_valor if (amort_extra_mes > 0 and mes_seq >= amort_extra_mes) else 0
        amort_extra = min(amort_extra, max(saldo - amort, 0))

        parcela_base = amort + juros
        seg_mip = saldo * mip_am
        seg_dfi = saldo * dfi_am
        parcela_total = parcela_base + seg_mip + seg_dfi + taxa_admin_mensal

        saldo_antes = saldo
        saldo = max(saldo - amort - amort_extra, 0)

        total_pago += parcela_total
        total_juros += juros
        total_seguros += seg_mip + seg_dfi
        total_admin += taxa_admin_mensal

        cf_cet.append(-parcela_total)
        cf_proj.append(-parcela_total)

        historico.append({
            "Mês": mes_seq,
            "Saldo Devedor (R$)": saldo_antes,
            "Amortização (R$)": amort,
            "Amort. Extra (R$)": amort_extra,
            "Juros (R$)": juros,
            "Seguro MIP (R$)": seg_mip,
            "Seguro DFI (R$)": seg_dfi,
            "Tx. Adm (R$)": taxa_admin_mensal,
            "Parcela Total (R$)": parcela_total,
            "Saldo Final (R$)": saldo,
        })

        if saldo <= 0:
            break

    df = pd.DataFrame(historico)
    prazo_real = len(df)

    # CET: TIR do financiamento (custo efetivo do crédito)
    tir_am = safe_irr(cf_cet[:prazo_real + 1])
    tir_aa = taxa_anual(tir_am) if tir_am else None

    # TIR do projeto (incluindo apreciação do bem no último período)
    bem_fut = valor_imovel * (1 + apreciacao_aa_pct / 100) ** (prazo_real / 12)
    cf_proj_final = cf_proj[:prazo_real + 1]
    cf_proj_final[-1] += bem_fut
    tir_proj_am = safe_irr(cf_proj_final)
    tir_proj_aa = taxa_anual(tir_proj_am) if tir_proj_am else None

    return {
        "saldo_financiado": saldo_financiado,
        "sistema": sistema,
        "prazo_real_meses": prazo_real,
        "primeira_parcela_total": df["Parcela Total (R$)"].iloc[0],
        "ultima_parcela_total": df["Parcela Total (R$)"].iloc[-1],
        "total_pago": total_pago,
        "total_juros": total_juros,
        "total_seguros": total_seguros,
        "total_admin": total_admin,
        "bem_futuro": bem_fut,
        "tir_am": tir_am,
        "tir_aa": tir_aa,
        "tir_proj_am": tir_proj_am,
        "tir_proj_aa": tir_proj_aa,
        "df": df,
    }


def simular_portabilidade(
    saldo_devedor_atual: float,
    taxa_atual_aa_pct: float,
    taxa_nova_aa_pct: float,
    prazo_restante: int,
    custo_portabilidade: float = 0.0,
) -> dict:
    """Calcula a economia com portabilidade de crédito imobiliário."""
    taxa_atual_am = taxa_mensal(taxa_atual_aa_pct / 100)
    taxa_nova_am = taxa_mensal(taxa_nova_aa_pct / 100)

    pmt_atual = npf.pmt(taxa_atual_am, prazo_restante, -saldo_devedor_atual)
    pmt_nova = npf.pmt(taxa_nova_am, prazo_restante, -saldo_devedor_atual)

    economia_mensal = pmt_atual - pmt_nova
    economia_total = economia_mensal * prazo_restante - custo_portabilidade
    payback_meses = custo_portabilidade / economia_mensal if economia_mensal > 0 else None

    return {
        "pmt_atual": pmt_atual,
        "pmt_nova": pmt_nova,
        "economia_mensal": economia_mensal,
        "economia_total": economia_total,
        "payback_meses": payback_meses,
    }


# ─────────────────────────────────────────────────────────────
# INVESTIMENTO
# ─────────────────────────────────────────────────────────────

PRODUTOS_REFERENCIA = {
    "CDB 110% CDI":       {"tipo": "cdi_pct",      "valor": 110, "isento_ir": False},
    "LCI/LCA 90% CDI":    {"tipo": "cdi_pct",      "valor": 90,  "isento_ir": True},
    "Tesouro Selic":      {"tipo": "selic_pct",     "valor": 100, "isento_ir": False},
    "Tesouro IPCA+ 6%":   {"tipo": "ipca_mais",     "valor": 6.0, "isento_ir": False},
    "CDB Prefixado 13%":  {"tipo": "prefixado",     "valor": 13,  "isento_ir": False},
    "Poupança":           {"tipo": "poupanca",      "valor": 0,   "isento_ir": True},
    "FII (IFIX médio)":   {"tipo": "fii",           "valor": 10,  "isento_ir": True},
    "Ações (IBOV médio)": {"tipo": "acoes",         "valor": 14,  "isento_ir": False},
}


def simular_investimento(
    capital_inicial: float,
    aporte_mensal: float,
    aporte_anual: float,
    mes_aporte_anual: int,
    taxa_bruta_aa_pct: float,
    inflacao_aa_pct: float,
    prazo_meses: int,
    mes_inicio: int = 4,
    isento_ir: bool = False,
    produto: str = "CDB 110% CDI",
) -> dict:
    """
    Simula evolução de carteira de investimento com aportes mensais e anuais.

    Parâmetros:
        capital_inicial    — saldo inicial (R$)
        aporte_mensal      — aporte mensal regular (R$)
        aporte_anual       — aporte extra anual (R$), ex: 13º salário
        mes_aporte_anual   — mês do calendário para o aporte anual (1-12)
        taxa_bruta_aa_pct  — rendimento bruto anual (%)
        inflacao_aa_pct    — inflação anual (%)
        prazo_meses        — horizonte (meses)
        mes_inicio         — mês do calendário de início (1-12)
        isento_ir          — True para LCI/LCA/Poupança (sem IR)
    """
    taxa_bruta_aa = taxa_bruta_aa_pct / 100
    taxa_bruta_am = taxa_mensal(taxa_bruta_aa)
    inflacao_aa = inflacao_aa_pct / 100
    inflacao_am = taxa_mensal(inflacao_aa)

    patrimonio = capital_inicial
    aporte_total_investido = capital_inicial
    total_rendimentos = 0.0
    historico = []

    for i in range(prazo_meses):
        mes_seq = i + 1
        mes_cal = ((mes_inicio - 1 + i) % 12) + 1
        dias_corridos = mes_seq * 30

        rendimento_bruto = patrimonio * taxa_bruta_am
        total_rendimentos += rendimento_bruto
        patrimonio += rendimento_bruto

        # Aportes
        patrimonio += aporte_mensal
        aporte_total_investido += aporte_mensal

        aporte_extra = 0.0
        if mes_cal == mes_aporte_anual and aporte_anual > 0:
            patrimonio += aporte_anual
            aporte_extra = aporte_anual
            aporte_total_investido += aporte_anual

        # IR (incide sobre o rendimento total no resgate)
        aliquota = 0.0 if isento_ir else aliquota_ir_renda_fixa(dias_corridos)
        rendimentos_acumulados = patrimonio - aporte_total_investido
        ir_estimado = max(rendimentos_acumulados * aliquota, 0)
        patrimonio_liquido = patrimonio - ir_estimado

        # Patrimônio real (corrigido pela inflação)
        fator_deflacao = (1 + inflacao_aa) ** (mes_seq / 12)
        patrimonio_real = patrimonio_liquido / fator_deflacao

        historico.append({
            "Mês": mes_seq,
            "Mês Calendário": mes_cal,
            "Aporte Mensal (R$)": aporte_mensal,
            "Aporte Anual (R$)": aporte_extra,
            "Rendimento Bruto (R$)": rendimento_bruto,
            "Patrimônio Bruto (R$)": patrimonio,
            "IR Estimado (R$)": ir_estimado,
            "Patrimônio Líquido (R$)": patrimonio_liquido,
            "Patrimônio Real (R$)": patrimonio_real,
            "Alíquota IR (%)": aliquota * 100,
        })

    df = pd.DataFrame(historico)

    total_aportado = aporte_total_investido
    patrimonio_final = df["Patrimônio Líquido (R$)"].iloc[-1]
    patrimonio_real_final = df["Patrimônio Real (R$)"].iloc[-1]
    total_ir = df["IR Estimado (R$)"].iloc[-1]
    rentab_total = (patrimonio_final / total_aportado - 1) * 100 if total_aportado > 0 else 0

    # TIR mensal e anual (retorno do investidor)
    cf_inv = [-capital_inicial]
    for row in historico:
        cf_inv.append(row["Aporte Mensal (R$)"] + row["Aporte Anual (R$)"])
    cf_inv[-1] += patrimonio_final  # recebe o patrimônio no final
    cf_inv = [-capital_inicial] + [-(aporte_mensal + h["Aporte Anual (R$)"]) for h in historico]
    cf_inv[-1] += patrimonio_final

    tir_am = safe_irr(cf_inv)
    tir_aa = taxa_anual(tir_am) if tir_am else None

    return {
        "capital_inicial": capital_inicial,
        "total_aportado": total_aportado,
        "total_rendimentos_brutos": total_rendimentos,
        "total_ir": total_ir,
        "patrimonio_final_bruto": patrimonio,
        "patrimonio_final_liquido": patrimonio_final,
        "patrimonio_final_real": patrimonio_real_final,
        "rentab_total_pct": rentab_total,
        "tir_am": tir_am,
        "tir_aa": tir_aa,
        "df": df,
    }


def comparar_produtos_investimento(
    capital_inicial: float,
    aporte_mensal: float,
    aporte_anual: float,
    mes_aporte_anual: int,
    prazo_meses: int,
    cdi_pct: float = 13.75,
    selic_pct: float = 13.75,
    ipca_pct: float = 5.0,
    mes_inicio: int = 4,
) -> pd.DataFrame:
    """Compara múltiplos produtos de investimento."""
    resultados = []
    for nome, cfg in PRODUTOS_REFERENCIA.items():
        tipo = cfg["tipo"]
        isento = cfg["isento_ir"]

        if tipo == "cdi_pct":
            taxa_bruta = cdi_pct * cfg["valor"] / 100
        elif tipo == "selic_pct":
            taxa_bruta = selic_pct * cfg["valor"] / 100
        elif tipo == "ipca_mais":
            taxa_bruta = ipca_pct + cfg["valor"]
        elif tipo == "prefixado":
            taxa_bruta = cfg["valor"]
        elif tipo == "poupanca":
            taxa_bruta = min(selic_pct * 0.70, 6.17) if selic_pct > 8.5 else selic_pct * 0.70
        elif tipo == "fii":
            taxa_bruta = cfg["valor"]
        elif tipo == "acoes":
            taxa_bruta = cfg["valor"]
        else:
            taxa_bruta = cfg["valor"]

        r = simular_investimento(
            capital_inicial=capital_inicial,
            aporte_mensal=aporte_mensal,
            aporte_anual=aporte_anual,
            mes_aporte_anual=mes_aporte_anual,
            taxa_bruta_aa_pct=taxa_bruta,
            inflacao_aa_pct=ipca_pct,
            prazo_meses=prazo_meses,
            mes_inicio=mes_inicio,
            isento_ir=isento,
        )
        resultados.append({
            "Produto": nome,
            "Taxa Bruta a.a. (%)": round(taxa_bruta, 2),
            "Isento IR": "Sim" if isento else "Não",
            "Patrimônio Final (R$)": r["patrimonio_final_liquido"],
            "Patrimônio Real (R$)": r["patrimonio_final_real"],
            "IR Total (R$)": r["total_ir"],
            "Rentab. Total (%)": r["rentab_total_pct"],
        })

    df = pd.DataFrame(resultados).sort_values("Patrimônio Final (R$)", ascending=False)
    return df


# ─────────────────────────────────────────────────────────────
# COMPARAÇÃO ESTRATÉGICA
# ─────────────────────────────────────────────────────────────

def simular_alugar_investir(
    aluguel_inicial: float,
    inflacao_aa_pct: float,
    capital_inicial: float,
    aporte_mensal: float,
    aporte_anual: float,
    mes_aporte_anual: int,
    taxa_invest_aa_pct: float,
    prazo_meses: int,
    mes_inicio: int = 4,
    parcela_alternativa_mensal: float = 0.0,
    isento_ir: bool = False,
) -> dict:
    """
    Simula o cenário 'Alugar + Investir':
    - Paga aluguel (reajustado anualmente pela inflação)
    - Investe o capital inicial + aportes mensais e anuais
    - A diferença entre a parcela alternativa e o aluguel também é investida
    """
    inflacao_aa = inflacao_aa_pct / 100
    inflacao_am = taxa_mensal(inflacao_aa)
    taxa_am = taxa_mensal(taxa_invest_aa_pct / 100)

    patrimonio = capital_inicial
    aporte_total = capital_inicial
    aluguel_vigente = aluguel_inicial
    total_aluguel = 0.0
    historico = []

    for i in range(prazo_meses):
        mes_seq = i + 1
        mes_cal = ((mes_inicio - 1 + i) % 12) + 1

        # Reajuste anual do aluguel
        if mes_cal == mes_inicio and i > 0:
            aluguel_vigente *= (1 + inflacao_aa)

        # Diferença entre parcela alternativa e aluguel (investida)
        diferenca = max(parcela_alternativa_mensal - aluguel_vigente, 0)
        aporte_efetivo = aporte_mensal + diferenca

        patrimonio *= (1 + taxa_am)
        patrimonio += aporte_efetivo
        aporte_total += aporte_efetivo
        total_aluguel += aluguel_vigente

        aporte_extra = 0.0
        if mes_cal == mes_aporte_anual and aporte_anual > 0:
            patrimonio += aporte_anual
            aporte_extra = aporte_anual
            aporte_total += aporte_anual

        # IR estimado (simplificado)
        rendimentos = patrimonio - aporte_total
        dias = mes_seq * 30
        aliquota = 0.0 if isento_ir else aliquota_ir_renda_fixa(dias)
        ir = max(rendimentos * aliquota, 0)
        patrimonio_liq = patrimonio - ir

        fator_defl = (1 + inflacao_aa) ** (mes_seq / 12)

        historico.append({
            "Mês": mes_seq,
            "Aluguel Pago (R$)": aluguel_vigente,
            "Aporte Efetivo (R$)": aporte_efetivo,
            "Aporte Anual (R$)": aporte_extra,
            "Patrimônio Bruto (R$)": patrimonio,
            "Patrimônio Líquido (R$)": patrimonio_liq,
            "Patrimônio Real (R$)": patrimonio_liq / fator_defl,
        })

    df = pd.DataFrame(historico)
    return {
        "total_aluguel": total_aluguel,
        "patrimonio_final_liquido": df["Patrimônio Líquido (R$)"].iloc[-1],
        "patrimonio_final_real": df["Patrimônio Real (R$)"].iloc[-1],
        "df": df,
    }


# ─────────────────────────────────────────────────────────────
# ANÁLISE DE SENSIBILIDADE
# ─────────────────────────────────────────────────────────────

def heatmap_financiamento(
    valor_imovel: float,
    taxas_aa: list[float],
    prazos_meses: list[int],
    entrada_pct: float = 20.0,
    sistema: str = "SAC",
) -> pd.DataFrame:
    """Gera heatmap: primeira parcela em função de taxa × prazo."""
    resultados = {}
    entrada = valor_imovel * entrada_pct / 100

    for prazo in prazos_meses:
        row = {}
        for taxa in taxas_aa:
            r = simular_financiamento(
                valor_imovel=valor_imovel,
                entrada=entrada,
                prazo_meses=prazo,
                taxa_juros_aa_pct=taxa,
                sistema=sistema,
            )
            row[f"{taxa:.1f}%"] = r["primeira_parcela_total"]
        resultados[f"{prazo}m"] = row

    return pd.DataFrame(resultados).T


def monte_carlo_investimento(
    capital_inicial: float,
    aporte_mensal: float,
    taxa_media_aa: float,
    volatilidade_aa: float,
    prazo_meses: int,
    n_simulacoes: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Monte Carlo para patrimônio final de investimento.
    Retorna DataFrame com percentis por mês.
    """
    rng = np.random.default_rng(seed)
    taxa_media_am = taxa_mensal(taxa_media_aa / 100)
    vol_am = (volatilidade_aa / 100) / math.sqrt(12)

    trajetorias = np.zeros((n_simulacoes, prazo_meses))

    for sim in range(n_simulacoes):
        pat = capital_inicial
        for mes in range(prazo_meses):
            retorno = rng.normal(taxa_media_am, vol_am)
            pat = pat * (1 + retorno) + aporte_mensal
            trajetorias[sim, mes] = pat

    df = pd.DataFrame({
        "Mês": range(1, prazo_meses + 1),
        "P10": np.percentile(trajetorias, 10, axis=0),
        "P25": np.percentile(trajetorias, 25, axis=0),
        "P50": np.percentile(trajetorias, 50, axis=0),
        "P75": np.percentile(trajetorias, 75, axis=0),
        "P90": np.percentile(trajetorias, 90, axis=0),
    })
    return df


def sensibilidade_consorcio(
    carta_base: float,
    taxa_adm_pct: float,
    prazo_base: int,
    inflacoes: list[float],
    prazos: list[int],
    lance_embutido_pct: float = 0.0,   # % da categoria
    recurso_proprio: float = 0.0,
) -> pd.DataFrame:
    """Heatmap: total desembolsado em função de inflação × prazo."""
    dados = {}
    for prazo in prazos:
        row = {}
        for inf in inflacoes:
            r = simular_consorcio(
                carta_credito=carta_base,
                taxa_adm_total_pct=taxa_adm_pct,
                prazo_meses=prazo,
                lance_embutido_pct=lance_embutido_pct,
                recurso_proprio=recurso_proprio,
                inflacao_aa_pct=inf,
            )
            row[f"INCC {inf:.1f}%"] = r["total_desembolsado"]
        dados[f"{prazo}m"] = row
    return pd.DataFrame(dados).T


# ─────────────────────────────────────────────────────────────
# CALCULADORAS AUXILIARES
# ─────────────────────────────────────────────────────────────

def calc_juros_compostos(
    capital: float,
    taxa_am: float,
    n_meses: int,
    aporte_mensal: float = 0,
) -> float:
    """Montante com juros compostos e aportes mensais."""
    montante = capital * (1 + taxa_am) ** n_meses
    if taxa_am > 0 and aporte_mensal > 0:
        montante += aporte_mensal * (((1 + taxa_am) ** n_meses - 1) / taxa_am)
    elif aporte_mensal > 0:
        montante += aporte_mensal * n_meses
    return montante


def calc_prazo_para_meta(
    capital_inicial: float,
    aporte_mensal: float,
    taxa_aa_pct: float,
    meta: float,
) -> Optional[int]:
    """Calcula em quantos meses atingirá a meta de patrimônio."""
    taxa_am = taxa_mensal(taxa_aa_pct / 100)
    pat = capital_inicial
    for mes in range(1, 1201):
        pat = pat * (1 + taxa_am) + aporte_mensal
        if pat >= meta:
            return mes
    return None


def calc_renda_passiva(
    patrimonio: float,
    taxa_aa_pct: float,
    inflacao_aa_pct: float,
) -> dict:
    """Calcula renda passiva mensal (nominal e real) para um patrimônio."""
    taxa_am = taxa_mensal(taxa_aa_pct / 100)
    inflacao_am = taxa_mensal(inflacao_aa_pct / 100)
    renda_nominal = patrimonio * taxa_am
    renda_real = patrimonio * (taxa_am - inflacao_am)
    return {
        "renda_nominal_mensal": renda_nominal,
        "renda_real_mensal": max(renda_real, 0),
        "renda_nominal_anual": renda_nominal * 12,
        "renda_real_anual": max(renda_real * 12, 0),
    }


def calc_equivalencia_aluguel(
    valor_imovel: float,
    taxa_invest_aa_pct: float,
    custo_oportunidade: bool = True,
) -> float:
    """
    Calcula o aluguel justo (break-even) de um imóvel.
    Yield médio histórico de imóveis no Brasil: ~5-7% a.a.
    """
    yield_aa = taxa_mensal(taxa_invest_aa_pct / 100) * 12
    return valor_imovel * yield_aa / 12


def calc_custo_efetivo_total(
    parcelas: list[float],
    capital_liberado: float,
    outros_custos: float = 0.0,
) -> Optional[float]:
    """
    Calcula o CET (Custo Efetivo Total) de uma operação de crédito.
    cash_flows = [+capital_liberado, -p1, -p2, ..., -pn - outros_custos]
    """
    cfs = [capital_liberado - outros_custos] + [-p for p in parcelas]
    tir_am = safe_irr(cfs)
    if tir_am is None:
        return None
    return taxa_anual(tir_am)
