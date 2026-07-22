"""
Aba de coortes de recompra (V4 — página anexa ao painel).

Segue a mesma TURMA de clientes ao longo dos meses: agrupa por SAFRA (mês da 1ª compra,
cross-canal, do HubSpot) e acumula a Margem de Contribuição POR CLIENTE conforme a turma
envelhece (m+0, m+1, …). A mídia inteira do mês pesa no m+0 (o CAC da safra); a recompra
soma adiante. Cruzar o zero = a turma se pagou.

Mostra: o cabeçalho de KPIs da safra escolhida (payback, CAC, MC/cliente até hoje, recompra
em 90 dias), a tabela de RECEITA por cohort (LTV = receita acumulada por cliente), o triângulo
de MC por cliente e o mesmo triângulo em reais cheios (MC absoluta). A cascata de uma safra
(de onde vem cada real) mora na aba A2 - Auditoria MC Cohort.
Rótulo honesto: "MC parcial" — no MVP a MC é REAL só na janela de itens
atual (abr–jul/2026); fora dela o CMV é ESTIMADO em 30% da receita. Não desconta CX, juros
de estoque nem criativo.
Vocabulário: MC, nunca "lucro". Só lê (nunca escreve).

Fonte nova: bases/hubspot_deals.csv (arquivo local, atualizado 1×/mês pelo João).
Spec: docs/specs/2026-07-10-v4-coortes-recompra.md
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import dados
from coortes_ui import (
    COR_NEGATIVA,
    COR_POSITIVA,
    carregar_e_calcular,
    numero,
    pct,
    ratio,
    reais,
    verde_gradiente,
)
from dados import ErroDeDados


# ---------------------------------------------------------------------------
# Cabeçalho e controles
# ---------------------------------------------------------------------------
st.title("📈 Coortes de recompra — cada safra se pagou?")
st.caption(
    "Cada cohort é a turma que fez a 1ª compra num mês (cross-canal, do HubSpot). As tabelas "
    "acumulam receita e MC por cliente conforme a turma envelhece; a mídia inteira do mês pesa "
    "no m+0. Cruzar o zero = a turma se pagou. MC, nunca 'lucro'."
)

coluna_botao, _ = st.columns([1, 3])
with coluna_botao:
    if st.button("🔄 Atualizar dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------------------------------
# Carrega e calcula (erros de leitura viram mensagem, não tela quebrada).
# A ausência do CSV do HubSpot NÃO derruba as outras abas (elas nem o leem).
# ---------------------------------------------------------------------------
try:
    resultado, mes_arquivo = carregar_e_calcular(dt.date.today().isoformat())
except ErroDeDados as erro:
    st.error(str(erro))
    st.stop()

if resultado.sem_safras:
    st.info(resultado.avisos[0] if resultado.avisos else "Sem safras fechadas para exibir.")
    st.stop()

# ---------------------------------------------------------------------------
# Faixa de "arquivo velho": o CSV não cobre o último mês fechado (spec 2.3)
# ---------------------------------------------------------------------------
if pd.Period(mes_arquivo, "M") < pd.Period(resultado.ultimo_mes_fechado, "M"):
    st.warning(
        f"⚠️ O arquivo de coortes vai até **{mes_arquivo}**; o último mês fechado é "
        f"**{resultado.ultimo_mes_fechado}**. Rode a atualização mensal do HubSpot para "
        "incluí-lo. A tela desenha com o que há."
    )

# ---------------------------------------------------------------------------
# Barra de notas (MC parcial + alertas)
# ---------------------------------------------------------------------------
st.info(
    "**MC parcial por cliente.** Não desconta CX, juros de estoque nem criativo (fora "
    f"desta versão), e **{pct(resultado.frac_estimada)} das células são estimadas** "
    "(sem itens para o custo real → CMV estimado em 30% da receita — marcadas com *). A linha do zero "
    "cruza mais cedo do que a MC cheia cruzaria."
)
for aviso in resultado.avisos:
    st.warning(aviso)

# ---------------------------------------------------------------------------
# Seletor de safra (padrão: a safra fechada mais recente)
# ---------------------------------------------------------------------------
safras_desc = list(reversed(resultado.safras))  # mais recente primeiro
col_sel, col_qtd = st.columns([1, 1])
with col_sel:
    safra_sel = st.selectbox("Cohort em foco (KPIs do cabeçalho)", safras_desc, index=0)
with col_qtd:
    n_curva = st.slider(
        "Quantos cohorts mostrar nas tabelas", 3, min(36, len(resultado.safras)),
        value=min(12, len(resultado.safras)),
    )

# ---------------------------------------------------------------------------
# Cabeçalho de KPIs da safra selecionada
# ---------------------------------------------------------------------------
cac_s = resultado.cac[safra_sel]
pay_s = resultado.payback[safra_sel]
mc_s = resultado.mc_ate_hoje[safra_sel]
rec_s = resultado.recompra_90d[safra_sel]
cor_mc = COR_POSITIVA if (pd.notna(mc_s) and mc_s >= 0) else COR_NEGATIVA

st.subheader(f"Cohort {safra_sel} · {numero(resultado.n_clientes[safra_sel], 0)} clientes")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Payback (meses até se pagar)", f"m+{pay_s}" if pay_s is not None else "—")
k2.metric("CAC (mídia ÷ clientes)", reais(cac_s) if cac_s is not None else "—")
k3.markdown(
    f"<div style='font-size:0.85rem;color:gray'>MC parcial/cliente até hoje</div>"
    f"<div style='font-size:1.6rem;font-weight:700;color:{cor_mc}'>"
    f"{reais(mc_s) if pd.notna(mc_s) else '—'}</div>",
    unsafe_allow_html=True,
)
k4.metric("Recompra em 90 dias", pct(rec_s))

notas_kpi = []
if pay_s is None:
    notas_kpi.append("Payback —: a turma ainda não cruzou o zero (ou é imatura); não extrapolamos.")
if cac_s is None:
    notas_kpi.append("CAC —: a aba Midia não cobre o mês desta safra.")
if not resultado.recompra_madura.get(safra_sel, True):
    notas_kpi.append("Recompra em 90 dias: a janela de 90 dias desta safra ainda não fechou — número provisório.")
for n in notas_kpi:
    st.caption(n)

st.divider()

# ---------------------------------------------------------------------------
# Tabela 1 — RECEITA por cohort (a irmã BRUTA do triângulo: antes de qualquer custo)
# Cohort | Novos Clientes | CAC | Receita 1ª Compra | LTV m+0 | LTV m+1 | …
#   Receita 1ª Compra = valor médio do 1º pedido do cliente.
#   LTV m+x = receita acumulada da turma até a idade x ÷ nº de clientes.
# ---------------------------------------------------------------------------
st.header("LTV e CAC por Cohort (Receita)")
st.subheader("Receita por cohort — LTV (receita acumulada por cliente)")

safras_mostrar = resultado.safras[-n_curva:]
ordem = list(reversed(safras_mostrar))  # mais recente no topo

ltv_tri = resultado.ltv.loc[safras_mostrar].dropna(axis=1, how="all")
idades_ltv = list(ltv_tri.columns)

linhas_rec = []
for s in ordem:
    linha = {
        "Cohort": s,
        "Novos Clientes": numero(resultado.n_clientes[s], 0),
        "CAC": reais(resultado.cac[s]) if resultado.cac[s] is not None else "—",
        "Receita 1ª Compra": reais(resultado.ticket_primeira_compra[s]),
    }
    for m in idades_ltv:
        v = resultado.ltv.loc[s, m]
        linha[f"LTV m+{m}"] = "" if pd.isna(v) else reais(v)
    linhas_rec.append(linha)

tab_rec = pd.DataFrame(linhas_rec)
st.table(
    tab_rec.style
    .set_properties(subset=[c for c in tab_rec.columns if c != "Cohort"], **{"text-align": "right"})
    .hide(axis="index")
)
st.caption(
    "**Receita 1ª Compra** = valor médio do primeiro pedido do cliente. **LTV m+x** = receita "
    "acumulada da turma até aquela idade, dividida pelo nº de clientes — é RECEITA BRUTA (antes "
    "de impostos, CMV, frete e mídia). Compare com o triângulo abaixo: lá é o que SOBRA."
)


# ---------------------------------------------------------------------------
# Tabelas de RATIO (múltiplos do CAC) — só apresentação: dividem números que já existem.
# CAC ausente (a aba Midia não cobre o mês) ou zero → a linha vira "—" (nunca divide por nada).
# Spec: docs/specs/2026-07-14-coortes-titulos-e-ratios.md
# ---------------------------------------------------------------------------
def _sobre_o_cac(valor: float, safra: str) -> float:
    cac_safra = resultado.cac[safra]
    if cac_safra is None or cac_safra == 0 or pd.isna(valor):
        return float("nan")
    return valor / cac_safra


def _matriz_ratio(triangulo: pd.DataFrame, idades: list[int]) -> pd.DataFrame:
    """O triângulo dividido pelo CAC de cada safra (mesma forma, em múltiplos)."""
    return pd.DataFrame(
        {m: [_sobre_o_cac(triangulo.loc[s, m], s) for s in ordem] for m in idades},
        index=ordem,
    )


def _estilo_por_coluna(numericos: dict[str, pd.Series], limiar: float = 0.0):
    """
    Verde mais escuro = ratio maior, com a escala de **cada coluna** (pedido do João): o m+7 se
    compara com os outros m+7, não com o m+0 (senão as idades novas nasceriam sempre claras, e a
    comparação ENTRE cohorts — que é o ponto da tabela — ficaria invisível).
    `numericos` mapeia o nome da coluna na tela → os ratios daquela coluna, na ordem das linhas.
    """
    def _estilo(coluna: pd.Series):
        serie = numericos[coluna.name]
        if not serie.notna().any():
            return ["" for _ in ordem]
        minimo, maximo = float(serie.min()), float(serie.max())
        return [verde_gradiente(serie[s], minimo, maximo, limiar) for s in ordem]

    return _estilo


# --- Tabela 1-b — LTV ÷ CAC (quantas vezes a turma devolveu o CAC em RECEITA) ---------------
st.subheader("LTV ÷ CAC — quantas vezes o cohort devolveu o CAC (em receita)")

ratios_ltv = _matriz_ratio(resultado.ltv, idades_ltv)

linhas_ltv_cac = []
for s in ordem:
    linha = {
        "Cohort": s,
        "Novos Clientes": numero(resultado.n_clientes[s], 0),
        "CAC": reais(resultado.cac[s]) if resultado.cac[s] is not None else "—",
        "Receita 1ª Compra": ratio(_sobre_o_cac(resultado.ticket_primeira_compra[s], s)),
    }
    for m in idades_ltv:
        v = ratios_ltv.loc[s, m]
        linha[f"LTV m+{m}"] = "" if (pd.isna(v) and pd.isna(resultado.ltv.loc[s, m])) else ratio(v)
    linhas_ltv_cac.append(linha)

tab_ltv_cac = pd.DataFrame(linhas_ltv_cac)
cols_ltv_idade = [f"LTV m+{m}" for m in idades_ltv]
# A coluna da 1ª compra também é um ratio → também entra no gradiente (com a escala DELA).
ratio_ticket = pd.Series(
    {s: _sobre_o_cac(resultado.ticket_primeira_compra[s], s) for s in ordem}
)
numericos_ltv = {"Receita 1ª Compra": ratio_ticket}
numericos_ltv.update({f"LTV m+{m}": ratios_ltv[m] for m in idades_ltv})

st.table(
    tab_ltv_cac.style
    .apply(_estilo_por_coluna(numericos_ltv), subset=["Receita 1ª Compra"] + cols_ltv_idade, axis=0)
    .set_properties(subset=["Novos Clientes", "CAC"], **{"text-align": "right"})
    .hide(axis="index")
)
st.caption(
    "A mesma tabela de cima, **dividida pelo CAC**: `2,95×` = para cada R\\$ 1 de mídia gasto para "
    "trazer a turma, ela devolveu R\\$ 2,95 de **receita bruta** até aquela idade. O verde compara "
    "**dentro de cada coluna** (o m+7 de um cohort contra o m+7 dos outros) — mais escuro = "
    "múltiplo maior. **Não é lucro** — é receita antes de impostos, CMV, frete e da própria "
    "mídia; o que SOBRA está no triângulo de MC, abaixo. Cohort sem mídia na base aparece como "
    "\"—\" (não dividimos por nada)."
)

st.divider()

# ---------------------------------------------------------------------------
# Tabela 2 — Triângulo de coortes (MC parcial acumulada POR CLIENTE)
# Cohort | Clientes | CAC | MC primeira compra | m+0 | m+1 | …
#   MC primeira compra = margem do 1º pedido do cliente JÁ descontada a mídia (decisão do
#   João): é o m+0 SEM as recompras que caíram no mesmo mês de entrada.
# Verde ≥ 0 / vermelho < 0 (a linha do zero); célula estimada em itálico com *
# ---------------------------------------------------------------------------
st.header("LTV MC e CAC por cohort (Margem de contribuição)")
st.subheader("Triângulo de coortes — MC por cliente")

tri = resultado.mc_acumulada.loc[safras_mostrar].dropna(axis=1, how="all")
idade_cols = list(tri.columns)

linhas_tab = []
for s in ordem:
    linha = {
        "Cohort": s,
        "Clientes": numero(resultado.n_clientes[s], 0),
        "CAC": reais(resultado.cac[s]) if resultado.cac[s] is not None else "—",
        "MC primeira compra": reais(resultado.mc_primeira_compra[s]),
    }
    for m in idade_cols:
        v = resultado.mc_acumulada.loc[s, m]
        if pd.isna(v):
            linha[f"m+{m}"] = ""
        else:
            marca = "" if bool(resultado.real.loc[s, m]) else " *"
            linha[f"m+{m}"] = reais(v) + marca
    linhas_tab.append(linha)

tabela = pd.DataFrame(linhas_tab)
cols_idade_nome = [f"m+{m}" for m in idade_cols]


def _estilo_por_sinal(triangulo):
    """Pinta a célula pelo SINAL (verde ≥ 0 / vermelho < 0); itálico quando estimada."""
    def _estilo(coluna: pd.Series):
        m = int(coluna.name.split("+")[1])
        estilos = []
        for safra in tabela["Cohort"]:
            v = triangulo.loc[safra, m]
            if pd.isna(v):
                estilos.append("")
                continue
            cor = COR_POSITIVA if v >= 0 else COR_NEGATIVA
            css = f"background-color:{cor}; color:#ffffff; text-align:right"
            if not bool(resultado.real.loc[safra, m]):
                css += "; font-style:italic"
            estilos.append(css)
        return estilos
    return _estilo


st.table(
    tabela.style
    .apply(_estilo_por_sinal(resultado.mc_acumulada), subset=cols_idade_nome, axis=0)
    .set_properties(subset=["Clientes", "CAC", "MC primeira compra"], **{"text-align": "right"})
    .hide(axis="index")
)
st.caption(
    "**MC primeira compra** = a margem do 1º pedido do cliente, já descontada a mídia inteira "
    "do mês (o CAC) — é o m+0 *sem* as recompras que caíram no mesmo mês de entrada. Cada célula "
    "m+x = MC parcial acumulada por cliente até aquela idade. **Verde** = a turma já se pagou "
    "(≥ 0); **vermelho** = ainda no vermelho. Célula em *itálico com \\**\\* = CMV estimado em 30% "
    "(fora da janela de itens). Colunas param onde o mês ainda não fechou (safra fechada)."
)

st.divider()

# ---------------------------------------------------------------------------
# Tabela 2-b — LUCRO BRUTO por cliente ÷ CAC (o triângulo acima, ANTES da mídia, em múltiplos)
# NÃO é a MC ÷ CAC: a MC já tem a mídia descontada, então dividi-la pelo CAC contaria a mídia
# DUAS vezes (uma no numerador, outra no denominador) — achado do João, 2026-07-14. O numerador
# certo é o Lucro Bruto (`resultado.lucro_bruto`, dono em coortes.py).
# A linha do empate aqui é **1,00×** (a turma devolveu o que custou trazê-la), não zero.
# ---------------------------------------------------------------------------
st.subheader("Lucro Bruto por cliente ÷ CAC — quantas vezes a turma pagou a própria mídia")

ratios_lb = _matriz_ratio(resultado.lucro_bruto, idade_cols)

linhas_lb_cac = []
for s in ordem:
    linha = {
        "Cohort": s,
        "Clientes": numero(resultado.n_clientes[s], 0),
        "CAC": reais(resultado.cac[s]) if resultado.cac[s] is not None else "—",
        "LB primeira compra": ratio(_sobre_o_cac(resultado.lucro_bruto_primeira_compra[s], s)),
    }
    for m in idade_cols:
        v = ratios_lb.loc[s, m]
        if pd.isna(v) and pd.isna(resultado.lucro_bruto.loc[s, m]):
            linha[f"m+{m}"] = ""
        else:
            marca = "" if bool(resultado.real.loc[s, m]) else " *"
            linha[f"m+{m}"] = ratio(v) + (marca if pd.notna(v) else "")
    linhas_lb_cac.append(linha)

tab_lb_cac = pd.DataFrame(linhas_lb_cac)
ratio_lb_primeira = pd.Series(
    {s: _sobre_o_cac(resultado.lucro_bruto_primeira_compra[s], s) for s in ordem}
)
numericos_lb = {"LB primeira compra": ratio_lb_primeira}
numericos_lb.update({f"m+{m}": ratios_lb[m] for m in idade_cols})

st.table(
    tab_lb_cac.style
    .apply(
        _estilo_por_coluna(numericos_lb, limiar=1.0),
        subset=["LB primeira compra"] + cols_idade_nome,
        axis=0,
    )
    .set_properties(subset=["Clientes", "CAC"], **{"text-align": "right"})
    .hide(axis="index")
)
st.caption(
    "**Lucro Bruto** (o que a turma gerou **antes** da mídia) **÷ CAC**. É o triângulo de cima "
    "*com a mídia de volta* — porque a MC já desconta a mídia, e dividi-la pelo CAC contaria a "
    "**mídia duas vezes**. Aqui o empate é **`1,00×`**: a turma devolveu exatamente o que custou "
    "trazê-la (é o mesmo payback do triângulo acima). `1,40×` = gerou 40% a mais do que custou; "
    "**número em vermelho (< 1,00×) = ainda não pagou a própria mídia**. Verde mais escuro = "
    "múltiplo maior, comparando **dentro de cada coluna**. Célula com \\**\\* = CMV estimado em 30%."
)

st.divider()

# ---------------------------------------------------------------------------
# Tabela 3 — o MESMO triângulo em REAIS CHEIOS (MC absoluta da turma)
# Mede TAMANHO (quanto a safra devolveu), não eficiência. Turmas de tamanhos diferentes
# não se comparam entre si — para isso serve o triângulo por cliente, acima.
# ---------------------------------------------------------------------------
st.subheader("Triângulo de coortes — MC absoluta (R$ da turma inteira)")

linhas_abs = []
for s in ordem:
    linha = {
        "Cohort": s,
        "Clientes": numero(resultado.n_clientes[s], 0),
        # Em reais cheios da turma (o resto da tabela também é) = MC/cliente × nº de clientes.
        "MC Primeira Compra": reais(resultado.mc_primeira_compra[s] * resultado.n_clientes[s]),
    }
    for m in idade_cols:
        v = resultado.mc_absoluta.loc[s, m]
        if pd.isna(v):
            linha[f"m+{m}"] = ""
        else:
            marca = "" if bool(resultado.real.loc[s, m]) else " *"
            linha[f"m+{m}"] = reais(v) + marca
    linhas_abs.append(linha)

tabela_abs = pd.DataFrame(linhas_abs)
st.table(
    tabela_abs.style
    .apply(_estilo_por_sinal(resultado.mc_absoluta), subset=cols_idade_nome, axis=0)
    .set_properties(subset=["Clientes", "MC Primeira Compra"], **{"text-align": "right"})
    .hide(axis="index")
)
st.caption(
    "A mesma conta do triângulo acima, **sem dividir pelo nº de clientes**: quanto a turma "
    "inteira devolveu, em reais (a **MC Primeira Compra** aqui também é o total da turma, já "
    "com a mídia). Mede **tamanho**, não eficiência — turmas grandes ganham das pequenas mesmo "
    "sendo piores por cliente. Para comparar cohorts, use o de cima."
)

st.divider()
st.caption(
    "Fonte: HubSpot (arquivo local) + planilha Google, só leitura. Para abrir a cascata de uma "
    "safra (de onde vem cada real), veja a aba **A2 - Auditoria MC Cohort**."
)
