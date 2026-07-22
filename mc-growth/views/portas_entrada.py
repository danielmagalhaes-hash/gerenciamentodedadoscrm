"""
Aba "4. Portas de entrada" (produto de estreia) — página anexa ao painel.

Uma PORTA DE ENTRADA é a linha de produto da 1ª compra do cliente. A aba mostra quanto de
**Lucro Bruto acumulado por cliente** (antes da mídia) cada porta devolve ao longo do tempo —
para negociar CAC-teto/ROAS-alvo diferenciado por porta (quem devolve mais em 180/365 dias
justifica pisar mais fundo na mídia).

Duas tabelas:
  · **Por safra** (obedece ao filtro de PRODUTO): um produto → só as safras dele; "todos" →
    idêntica ao Lucro Bruto acumulado da aba Cohorts.
  · **Por linha de produto** (obedece ao filtro de DATA): todas as portas de uma vez, para
    comparar — cada janela usa só as safras maduras para ela.

Célula = Lucro Bruto/cliente (NÃO a MC — a MC já desconta a mídia). CAC = blended do mês (a
mesma régua para qualquer produto). Régua PARCIAL: sem devolução/CX/juros/criativo.
Vocabulário: MC/Lucro Bruto, nunca "lucro líquido". Só lê. Reusa `coortes.py` (uma verdade de custo).

Spec: docs/specs/2026-07-15-portas-de-entrada-produto.md
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import dados
import portas
from coortes_ui import numero, pct, ratio, reais, verde_gradiente
from dados import ErroDeDados

ROTULOS = [rot for rot, _m in portas.COLUNAS_IDADE]
IDADES = [m for _rot, m in portas.COLUNAS_IDADE]


@st.cache_data(show_spinner="Lendo portas de entrada…")
def _carregar(hoje_iso: str):
    """Lê tudo (planilha + HubSpot + histórico + mapa) e monta as portas. Cacheado por dia."""
    base = dados.carregar_tudo()
    deals = dados.carregar_hubspot()
    hist = dados.carregar_itens_historico()
    mapa = dados.carregar_mapa_portas()
    res = portas.calcular_portas(base, deals, mapa, hoje=pd.Timestamp(hoje_iso), hist=hist)
    mes_arquivo = str(deals["data_de_fechamento"].dropna().dt.to_period("M").max())
    return res, mes_arquivo


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.title("🚪 Portas de entrada — quanto cada produto de estreia devolve")
st.caption(
    "A **porta de entrada** é a linha de produto da 1ª compra do cliente. Cada célula é o valor "
    "**acumulado por cliente** até aquela idade — **Lucro Bruto** (antes da mídia) ou **Receita** "
    "(bruta), à sua escolha —, a mesma régua da aba Cohorts. Portas que devolvem mais em "
    "180/365 dias aguentam um CAC maior."
)

coluna_botao, _ = st.columns([1, 3])
with coluna_botao:
    if st.button("🔄 Atualizar dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()

try:
    res, mes_arquivo = _carregar(dt.date.today().isoformat())
except ErroDeDados as erro:
    st.error(str(erro))
    st.stop()

if res.sem_dados:
    st.info(res.avisos[0] if res.avisos else "Sem safras fechadas para exibir.")
    st.stop()

if pd.Period(mes_arquivo, "M") < res.ultimo_fechado:
    st.warning(
        f"⚠️ O arquivo do HubSpot vai até **{mes_arquivo}**; o último mês fechado é "
        f"**{res.ultimo_fechado}**. Rode a atualização mensal para incluí-lo."
    )

# Seletor de MÉTRICA — troca o conteúdo das duas tabelas entre Lucro Bruto (mc_produto) e
# Receita (valor). É a MESMA verdade da aba Cohorts: "todos" reproduz `coortes.lucro_bruto`
# (LB) ou `coortes.ltv` (Receita) ao centavo. Não recalcula nada — só troca a coluna somada.
METRICA_LB = "Lucro Bruto (antes da mídia)"
METRICA_RECEITA = "Receita (bruta)"
metrica_escolha = st.radio(
    "Métrica das tabelas", [METRICA_LB, METRICA_RECEITA], horizontal=True,
    help="Lucro Bruto = receita − deduções − CMV, antes da mídia (régua parcial). "
         "Receita = o valor cheio do pedido (bruto, antes de qualquer custo).",
)
eh_receita = metrica_escolha == METRICA_RECEITA
COL_METRICA = "valor" if eh_receita else "mc_produto"
TERMO = "Receita" if eh_receita else "Lucro Bruto"
TERMO_CELL = "Receita acumulada por cliente" if eh_receita else "Lucro Bruto acumulado por cliente"

if eh_receita:
    st.info(
        "**Receita bruta por cliente.** O valor cheio do pedido (inclui frete), **antes de "
        "qualquer custo** — nem CMV, nem deduções, nem mídia. É o LTV bruto da aba Cohorts, "
        "fatiado por porta. Leitura **comparativa** entre portas. *(Custo/CMV estimado não afeta "
        "a receita — o `valor` é o mesmo real em toda a história.)*"
    )
else:
    st.info(
        "**Lucro Bruto PARCIAL por cliente.** Antes da mídia, mas **sem** devolução, CX, juros de "
        "estoque nem criativo — e a **taxa de devolução por produto** (o custo que mais difere entre "
        f"portas) fica **de fora**. **{pct(res.frac_estimada)} das células têm CMV estimado** (30% da "
        "receita, onde não há itens). Leitura **comparativa** entre portas, não fully-loaded."
    )
for aviso in res.avisos:
    st.warning(aviso)

# ---------------------------------------------------------------------------
# Controles
# ---------------------------------------------------------------------------
c1, c2 = st.columns([1, 1])
with c1:
    n_min = st.number_input(
        "N mínimo de clientes (abaixo → “—”)", min_value=1, max_value=5000,
        value=portas.N_MINIMO_PADRAO, step=50,
    )
with c2:
    st.metric("Clientes classificados", numero(sum(res.n_por_porta.values()), 0))

# Switch de leitura das células (vale para as DUAS tabelas). "Valor total" = Lucro Bruto
# acumulado por cliente (R$). "Aumento vs 1ª compra" = o mesmo número dividido pela 1ª compra
# da própria linha (base = 1,00×) — quantas vezes o cliente já devolveu o pedido de entrada.
# É só uma lente sobre os mesmos números; não recalcula nada.
MODO_TOTAL = "Valor total (R$)"
MODO_MULTIPLO = "Aumento vs 1ª compra (×)"
modo = st.radio(
    "Leitura das células", [MODO_TOTAL, MODO_MULTIPLO], horizontal=True,
    help=f"Aumento vs 1ª compra = {TERMO} acumulado ÷ o da 1ª compra da linha. A 1ª compra "
         "é a base (1,00×); 1,58× = o cliente devolveu 58% a mais do que na entrada.",
)
eh_multiplo = modo == MODO_MULTIPLO
_nota_modo = (
    f"**Modo aumento (×):** cada célula é o {TERMO} acumulado **÷ o da 1ª compra** da própria "
    "linha (a 1ª compra é a base, 1,00×); 1,58× = o cliente já devolveu 58% a mais que na entrada. "
    if eh_multiplo else ""
)


def _num_exibir(valor: float, primeira: float) -> float:
    """O número que vai à tela/gradiente. No modo múltiplo, divide pela 1ª compra da linha
    (base 1,00×); NaN se a base não presta (≤ 0) — não dá para medir aumento sobre zero/prejuízo."""
    if not eh_multiplo:
        return valor
    if pd.isna(valor) or pd.isna(primeira) or primeira <= 0:
        return float("nan")
    return valor / primeira


def _fmt(num: float) -> str:
    """R$ no modo total, ×N no modo múltiplo. NaN vira '' (a supressão por N mínimo é à parte)."""
    if pd.isna(num):
        return ""
    return ratio(num) if eh_multiplo else reais(num)


def _matriz_estilo(numericos: dict[str, pd.Series]):
    """Verde por coluna (mais escuro = Lucro Bruto maior), comparando dentro da mesma janela —
    a leitura da tabela é 'qual porta/safra devolve mais nesta idade'. Reusa `verde_gradiente`."""
    def _estilo(coluna: pd.Series):
        serie = numericos.get(coluna.name)
        if serie is None or not serie.notna().any():
            return ["" for _ in coluna]
        mn, mx = float(serie.min()), float(serie.max())
        return [verde_gradiente(serie.iloc[i], mn, mx) for i in range(len(coluna))]
    return _estilo


def _celula(valor: float, n: int, primeira: float) -> str:
    """Célula da tabela por safra. “—” se a turma é pequena demais (N < mínimo) ou se, no modo
    múltiplo, falta base; "" se imatura. Senão, R$ ou ×N conforme o switch."""
    if n < n_min:
        return "—"
    if pd.isna(valor):
        return ""
    num = _num_exibir(valor, primeira)
    if eh_multiplo and pd.isna(num):
        return "—"
    return _fmt(num)


# ---------------------------------------------------------------------------
# Tabela PRINCIPAL — por safra (obedece ao filtro de PRODUTO)
# ---------------------------------------------------------------------------
st.divider()
_sufixo = "aumento sobre a 1ª compra (×)" if eh_multiplo else TERMO_CELL
st.header(f"Por safra — {_sufixo}")

portas_opcoes = [portas.PORTA_TODOS] + [
    f"{p}  ({numero(res.n_por_porta[p], 0)})" for p in res.portas
]
escolha = st.selectbox("Porta de entrada (filtro de produto)", portas_opcoes, index=0)
porta_sel = portas.PORTA_TODOS if escolha == portas_opcoes[0] else res.portas[portas_opcoes.index(escolha) - 1]

tab = portas.tabela_por_safra(res, porta_sel, metrica=COL_METRICA)
tab = tab[tab["n"] > 0]                       # só safras onde a porta teve cliente
ordem_s = list(reversed(tab["safra"].tolist()))  # mais recente no topo
tab = tab.set_index("safra")

linhas, numericos = [], {rot: [] for rot in ["1ª compra"] + ROTULOS}
for s in ordem_s:
    n = int(tab.loc[s, "n"])
    p = tab.loc[s, "primeira"]  # a 1ª compra da linha = base do múltiplo
    linha = {
        "Cohort": s,
        "Clientes": numero(n, 0),
        "CAC": reais(tab.loc[s, "cac"]) if tab.loc[s, "cac"] is not None else "—",
        "1ª compra": _celula(p, n, p),
    }
    numericos["1ª compra"].append(_num_exibir(p, p) if n >= n_min else float("nan"))
    for rot, m in portas.COLUNAS_IDADE:
        linha[rot] = _celula(tab.loc[s, m], n, p)
        numericos[rot].append(_num_exibir(tab.loc[s, m], p) if n >= n_min else float("nan"))
    linhas.append(linha)

df_princ = pd.DataFrame(linhas)
num_princ = {k: pd.Series(v, index=range(len(ordem_s))) for k, v in numericos.items()}
cols_valor = ["1ª compra"] + ROTULOS
st.table(
    df_princ.style
    .apply(_matriz_estilo(num_princ), subset=cols_valor, axis=0)
    .set_properties(subset=["Clientes", "CAC"], **{"text-align": "right"})
    .hide(axis="index")
)
_fonte_cohorts = "a Receita acumulada (LTV) da aba **Cohorts**" if eh_receita else \
    "o Lucro Bruto acumulado da aba **Cohorts**"
st.caption(
    _nota_modo +
    f"**1ª compra** = {TERMO} do 1º pedido por cliente. **30D…365D** são apelidos dos meses "
    f"m+0…m+11 da Cohorts (batem por construção) — {TERMO} acumulado por cliente até aquela "
    "idade. **CAC** = mídia do mês ÷ TODOS os novos do mês (blended — nunca por produto). Verde "
    "mais escuro = devolveu mais **dentro da coluna**. “—” = turma abaixo do N mínimo; célula "
    f"vazia = mês ainda não fechou. Com **“Todas as portas”**, esta tabela é {_fonte_cohorts}, "
    "ao centavo."
)

# ---------------------------------------------------------------------------
# Tabela SECUNDÁRIA — por linha de produto (obedece ao filtro de DATA)
# ---------------------------------------------------------------------------
st.divider()
st.header(f"Por linha de produto — {_sufixo}")

st.info(
    "👉 **Leia esta tabela por COLUNA, não por linha.** Cada coluna (30D, 60D, 90D…) serve para "
    "comparar as portas **entre si** naquela janela.\n\n"
    "Ao ler uma linha da esquerda para a direita, um número pode ficar **menor que o da coluna "
    "anterior** — e isso **não** significa que alguém gastou menos. Cada coluna conta um **grupo "
    "diferente de clientes**: quanto mais longa a janela, **menos gente entra na conta** (só quem "
    "já existe há tempo suficiente para ter vivido aquele período). "
    "Para ver **a mesma turma crescendo mês a mês** (sempre subindo), use a tabela **por safra**, "
    "logo acima."
)
with st.expander("🔎 Um exemplo de por que uma coluna pode “cair”"):
    st.markdown(
        "Digamos que a porta **Calça Jeans 2.0** mostre **R$ 148 no 30D** e **R$ 146 no 60D** — "
        "parece que encolheu.\n\n"
        "**Não encolheu.** A turma que entrou no **último mês** teve uma 1ª compra forte e **conta "
        "no 30D**. Mas ela **ainda não completou os 2 meses** que o 60D exige, então **sai da conta "
        "do 60D**. Sem essa turma boa, a **média** do 60D fica um tiquinho menor.\n\n"
        "Ou seja: **ninguém gastou menos** — mudou apenas **quem está sendo contado** em cada coluna. "
        "A coluna **Clientes** mostra o total da porta no período; o número por trás de cada janela "
        "é sempre **igual ou menor** que esse total, encolhendo conforme a janela aumenta."
    )

d1, d2 = st.columns([1, 1])
i_default = max(0, len(res.safras) - 12)
with d1:
    ini = st.selectbox("De (safra)", res.safras, index=i_default)
with d2:
    fim = st.selectbox("Até (safra)", res.safras, index=len(res.safras) - 1)
ini_p, fim_p = pd.Period(ini, "M"), pd.Period(fim, "M")
if ini_p > fim_p:
    ini_p, fim_p = fim_p, ini_p

tab_l = portas.tabela_por_linha(res, ini_p, fim_p, n_min=int(n_min), metrica=COL_METRICA)
if tab_l.empty:
    st.info("Nenhuma porta atingiu o N mínimo no período escolhido.")
else:
    def _celula_linha(valor: float, n_cel: int, primeira: float) -> str:
        """“—” = janela abaixo do N mínimo (ou sem base no modo múltiplo); "" = sem safra madura."""
        if pd.isna(valor):
            return "—" if n_cel > 0 else ""
        num = _num_exibir(valor, primeira)
        if eh_multiplo and pd.isna(num):
            return "—"
        return _fmt(num)

    linhas_l, numericos_l = [], {rot: [] for rot in ["1ª compra"] + ROTULOS}
    for _i, r in tab_l.iterrows():
        n = int(r["n"])
        p = r["primeira"]  # base do múltiplo (1ª compra da porta no período)
        linha = {
            "Porta de entrada": r["porta"],
            "Clientes": numero(n, 0),
            "CAC": reais(r["cac"]) if pd.notna(r["cac"]) else "—",
            "1ª compra": _celula_linha(p, int(r["n_primeira"]), p),
        }
        numericos_l["1ª compra"].append(_num_exibir(p, p))
        for rot, m in portas.COLUNAS_IDADE:
            linha[rot] = _celula_linha(r[m], int(r[f"n_{m}"]), p)
            numericos_l[rot].append(_num_exibir(r[m], p))
        linhas_l.append(linha)

    df_sec = pd.DataFrame(linhas_l)
    num_sec = {k: pd.Series(v, index=range(len(df_sec))) for k, v in numericos_l.items()}
    st.table(
        df_sec.style
        .apply(_matriz_estilo(num_sec), subset=cols_valor, axis=0)
        .set_properties(subset=["Clientes", "CAC"], **{"text-align": "right"})
        .hide(axis="index")
    )
    st.caption(
        _nota_modo +
        f"Safras de **{ini_p}** a **{fim_p}**, ordenadas por nº de clientes. Uma célula “—” é uma "
        "janela abaixo do N mínimo; **portas que não passam do mínimo em nenhuma janela saem da "
        "tabela** (turma pequena demais para ler). **CAC** = blended do período (mídia total ÷ "
        "novos totais), igual para todas as portas: é régua de comparação, **não** CAC por produto. "
        "Verde mais escuro = porta que devolve mais **naquela janela**."
    )

st.divider()
st.caption(
    "A porta de entrada = a linha de produto do pedido de estreia (brindes e itens sem nome "
    "cadastrado saem antes; 1 linha → essa porta, >1 → “Multiprodutos”, nenhuma → “Produto "
    "desconhecido”, que inclui estreias no Comercial e fora do Shopify). Fonte: HubSpot + planilha "
    "+ base histórica de itens + `bases/mapa_sku_linha_produto.csv`. Só leitura."
)
