"""
Aba de aquisição — MC de clientes novos (página anexa ao painel).

Responde a uma pergunta: a aquisição de clientes novos gera Margem de Contribuição
positiva JÁ NA PRIMEIRA COMPRA? Lê o carimbo nativo da Shopify (Vendas.customer_type),
separa os pedidos de "Primeira Compra" e calcula, só sobre eles, a cascata de MC —
descontando a mídia INTEIRA do período (convenção 100% mídia → novos).

Mostra: herói MC-novos (verde ≥ 0 / vermelho < 0 = a linha do zero), 5 cartões
(MC-novos · Vendas-novos · Pedidos-novos · CAC · aROAS) e a mini-cascata de novos.
Vocabulário: MC, nunca "lucro". Só lê (nunca escreve).

Usa o MESMO recorte e o MESMO cache do painel (cascata._recorte_pedidos via
cascata.calcular_aquisicao), então as faixas amarram com o total do painel.
Spec: docs/specs/2026-07-09-v2-aba-aquisicao.md
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import cascata
import dados
import ui
from dados import ErroDeDados



# ---------------------------------------------------------------------------
# Formatação em português (R$ 1.234,56) — mesmo padrão do painel
# ---------------------------------------------------------------------------
def reais(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def numero(valor: float, casas: int = 2) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(show_spinner="Lendo a planilha…")
def carregar() -> dados.Dados:
    return dados.carregar_tudo()


@st.cache_data(show_spinner=False)
def carregar_deals():
    """Base HubSpot (destrava meses históricos). Ausente → None (só a janela real)."""
    try:
        return dados.carregar_hubspot()
    except ErroDeDados:
        return None


@st.cache_data(show_spinner="Lendo o histórico de itens…")
def carregar_hist():
    """Base histórica de itens → CMV real na história inteira. Ausente → vazia (30% estimado)."""
    return dados.carregar_itens_historico()


# ---------------------------------------------------------------------------
# Cabeçalho e controles
# ---------------------------------------------------------------------------
st.title("🎯 Aquisição — MC de clientes novos (Shopify)")
st.caption(
    "A aquisição de clientes novos se paga já na 1ª compra? Toda a mídia do período pesa "
    "sobre os clientes novos (convenção 100% mídia → novos). MC, nunca 'lucro'."
)

hoje = dt.date.today()
primeiro_do_mes = hoje.replace(day=1)

coluna_periodo, coluna_botao = st.columns([3, 1])
with coluna_periodo:
    periodo = st.date_input(
        "Período (dias fechados; padrão: este mês até agora)",
        value=(primeiro_do_mes, hoje),
        format="DD/MM/YYYY",
    )
with coluna_botao:
    st.write("")
    st.write("")
    if st.button("🔄 Atualizar dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()

if isinstance(periodo, (tuple, list)):
    if len(periodo) != 2:
        st.info("Escolha a data final do período.")
        st.stop()
    inicio, fim = periodo
else:
    inicio = fim = periodo

# ---------------------------------------------------------------------------
# Carrega e calcula (erros de leitura viram mensagem, não tela quebrada)
# ---------------------------------------------------------------------------
try:
    base = carregar()
except ErroDeDados as erro:
    st.error(str(erro))
    st.stop()

resultado = cascata.calcular_aquisicao(
    base, inicio, fim, deals=carregar_deals(), hist=carregar_hist()
)

st.caption(f"Período: {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}")

if resultado.sem_dados:
    st.info("Sem dados no período.")
    st.stop()

# Sem itens não há custo real → o CMV entra estimado em 30% (spec 2026-07-14).
if resultado.rotulo_confianca == "estimada":
    st.warning(
        "📊 **Mês histórico — MC-novos parcial estimada.** Sem itens, o **CMV é estimado em 30% "
        "da receita** (as deduções seguem as fórmulas de sempre), e 'novo' é a 1ª compra na "
        "Minimal (HubSpot, cross-canal), não o carimbo do Shopify. Leia como **tendência**."
    )
elif resultado.rotulo_confianca == "mista":
    st.warning(
        f"📊 **Período misto.** Parte com custo real (janela de itens) + "
        f"**{reais(resultado.vendas_novos_estimada)}** de venda-novos histórica com **CMV "
        "estimado (30%)** — veja a marca ⚠️ na linha do CMV."
    )

# ---------------------------------------------------------------------------
# Barra de alertas
# ---------------------------------------------------------------------------
if resultado.skus_sem_custo > 0:
    st.warning(
        f"⚠️ {numero(resultado.unidades_sem_custo, 0)} itens de clientes novos sem custo "
        f"cadastrado ({resultado.skus_sem_custo} SKUs) — a MC-novos pode estar "
        "superestimada. Corrija os custos na página do painel (seção 🏷️)."
    )
for aviso in resultado.avisos:
    st.warning(aviso)

# ---------------------------------------------------------------------------
# Herói — a MC-novos (a linha do zero: verde ≥ 0, vermelho < 0)
# ---------------------------------------------------------------------------
COR_POSITIVA = "#1f7a3d"  # verde (mesma da MC do painel)
COR_NEGATIVA = "#b91c1c"  # vermelho
cor_mc = COR_POSITIVA if resultado.mc_novos >= 0 else COR_NEGATIVA
veredito = (
    "a aquisição se paga na 1ª compra"
    if resultado.mc_novos >= 0
    else "a aquisição NÃO se paga na 1ª compra (pode se pagar na recompra — V4)"
)
st.markdown(
    f"<div style='text-align:center; padding:0.5rem 0;'>"
    f"<div style='font-size:1rem; color:gray;'>MC de clientes novos (MC-novos)</div>"
    f"<div style='font-size:3.2rem; font-weight:700; line-height:1.1; color:{cor_mc};'>"
    f"{reais(resultado.mc_novos)}</div>"
    f"<div style='font-size:0.9rem; color:gray;'>Lucro Bruto-novos − Mídia paga (inteira)  ·  "
    f"{reais(resultado.lucro_bruto_novos)} − {reais(resultado.ad_spend)}</div>"
    f"<div style='font-size:0.9rem; color:{cor_mc}; font-weight:600;'>{veredito}</div>"
    f"</div>",
    unsafe_allow_html=True,
)

st.divider()

# ---------------------------------------------------------------------------
# 6 cartões (ordem pedida pelo João, spec 2026-07-14). A MC-novos não repete aqui:
# ela já é o número-herói acima.
# ---------------------------------------------------------------------------
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Vendas novos clientes", reais(resultado.vendas_novos))
c2.metric("Ad Spend", reais(resultado.ad_spend))
c3.metric("aROAS Shopify", numero(resultado.aroas) if resultado.aroas is not None else "—")
c4.metric("Ticket Médio", reais(resultado.ticket_medio) if resultado.ticket_medio is not None else "—")
c5.metric("nº Pedidos", numero(resultado.pedidos_novos, 0))
c6.metric("CAC", reais(resultado.cac) if resultado.cac is not None else "—")

# Notas das bordas (divisões indefinidas) — nunca "∞" nem "grátis".
if resultado.pedidos_novos == 0:
    st.caption("CAC e Ticket Médio —: sem clientes novos no período.")
if resultado.ad_spend == 0:
    st.caption("aROAS —: sem mídia no período.")

st.divider()

# ---------------------------------------------------------------------------
# Mini-cascata de novos (DRE) — como a MC-novos se formou
# ---------------------------------------------------------------------------
st.subheader("Cascata de clientes novos — de Vendas-novos até a MC-novos")

ui.tabela_dre(
    resultado.linhas, resultado.vendas_novos, reais, numero,
    cor_resultado=cor_mc, titulo_pct="% de Vendas-novos",
)

st.caption(
    "Deduções e custos variáveis (%) incidem sobre a Vendas-novos, com os mesmos "
    "parâmetros do painel. A mídia entra INTEIRA (convenção 100% mídia → novos). "
    "Onde o pedido não tem itens, o CMV entra estimado em 30% da receita (linha marcada ⚠️)."
)
