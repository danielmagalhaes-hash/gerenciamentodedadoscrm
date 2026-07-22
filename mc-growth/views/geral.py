"""
views/geral.py — a tela "1. Geral" (Painel de MC).

Desenha: número-herói da MC, 5 cartões, cascata tipo DRE, filtro de período e a
barra de alertas. Só lê (nunca escreve). Regras vêm de cascata.py; dados de dados.py.

Chamada pelo menu em painel.py (não rodar direto).
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
# Formatação em português (R$ 1.234,56)
# ---------------------------------------------------------------------------
def reais(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def numero(valor: float, casas: int = 2) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# Leitura da planilha (cacheada; o botão "Atualizar" limpa o cache)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Lendo a planilha…")
def carregar() -> dados.Dados:
    return dados.carregar_tudo()


@st.cache_data(show_spinner=False)
def carregar_deals():
    """Base HubSpot (para destravar meses históricos). Ausente → None (só a janela real)."""
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
st.title("📈 Margem de Contribuição — Minimal Club (Shopify)")

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
    st.write("")  # empurra o botão para alinhar com o seletor
    st.write("")
    if st.button("🔄 Atualizar dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()

# O date_input pode devolver uma data só enquanto o João escolhe o intervalo.
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

resultado = cascata.calcular(base, inicio, fim, deals=carregar_deals(), hist=carregar_hist())

st.caption(f"Período: {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}")

if resultado.sem_dados:
    st.info("Sem dados no período.")
    st.stop()

# Rótulo de confiança: sem itens não há custo real → o CMV entra estimado em 30% (spec 2026-07-14).
if resultado.rotulo_confianca == "estimada":
    st.warning(
        "📊 **Mês histórico — MC parcial estimada.** Sem itens para o custo real, o **CMV é "
        "estimado em 30% da receita** (as deduções seguem as fórmulas de sempre). Leia como "
        "**tendência**, não como fechamento. O mês atual (com itens) é real."
    )
elif resultado.rotulo_confianca == "mista":
    st.warning(
        f"📊 **Período misto.** Parte na janela de itens tem **custo real**; "
        f"**{reais(resultado.vendas_estimada)}** de venda histórica entra com **CMV estimado "
        "(30%)** — veja a marca ⚠️ na linha do CMV."
    )

# ---------------------------------------------------------------------------
# Barra de alertas
# ---------------------------------------------------------------------------
if resultado.skus_sem_custo > 0:
    st.warning(
        f"⚠️ {numero(resultado.unidades_sem_custo, 0)} itens vendidos sem custo cadastrado "
        f"({resultado.skus_sem_custo} SKUs) — a MC pode estar superestimada. "
        "Corrija abaixo em '🏷️ Corrigir custos faltantes'."
    )

# --- Editor de custos faltantes (grava num arquivo local, não na planilha) ---
if resultado.skus_faltantes:
    with st.expander(f"🏷️ Corrigir custos faltantes ({len(resultado.skus_faltantes)} SKU)"):
        st.caption(
            "Digite o custo unitário (R$) de cada SKU e clique em Salvar. As correções "
            "ficam num arquivo local seu (`custos_extra.csv`) e valem por cima da base — "
            "o painel não altera a planilha compartilhada. Custo 0 é válido."
        )
        overrides_atuais = dados.ler_custos_extra()
        tabela_faltantes = pd.DataFrame(
            [
                {
                    "SKU": sku,
                    "unidades": int(unidades),
                    "custo (R$)": overrides_atuais.get(sku, None),
                }
                for sku, unidades in resultado.skus_faltantes
            ]
        )
        editado = st.data_editor(
            tabela_faltantes,
            hide_index=True,
            disabled=["SKU", "unidades"],
            column_config={
                "custo (R$)": st.column_config.NumberColumn(
                    "custo (R$)", min_value=0.0, step=0.01, format="%.2f"
                )
            },
            key="editor_custos",
        )
        if st.button("💾 Salvar custos"):
            novos = {
                linha["SKU"]: float(linha["custo (R$)"])
                for _, linha in editado.iterrows()
                if pd.notna(linha["custo (R$)"])
            }
            if novos:
                combinado = {**overrides_atuais, **novos}
                dados.salvar_custos_extra(combinado)
                st.cache_data.clear()
                st.success(f"{len(novos)} custo(s) salvo(s). Recalculando…")
                st.rerun()
            else:
                st.info("Nenhum custo preenchido para salvar.")
if resultado.ad_spend == 0 and resultado.vendas > 0:
    st.warning("Sem gasto de mídia no período — ROAS não calculado.")
for aviso in resultado.avisos:
    st.warning(aviso)
if resultado.pedidos_excluidos > 0:
    st.caption(
        f"ℹ️ {resultado.pedidos_excluidos} pedido(s) excluído(s) da análise por "
        "decisão de negócio (AnjosFrach e pedidos pontuais — ADR 2026-07-02)."
    )

# ---------------------------------------------------------------------------
# Herói — a MC
# ---------------------------------------------------------------------------
st.markdown(
    f"<div style='text-align:center; padding:0.5rem 0;'>"
    f"<div style='font-size:1rem; color:gray;'>Margem de Contribuição</div>"
    f"<div style='font-size:3.2rem; font-weight:700; line-height:1.1;'>{reais(resultado.mc)}</div>"
    f"<div style='font-size:0.9rem; color:gray;'>Lucro Bruto − Mídia paga  ·  "
    f"{reais(resultado.lucro_bruto)} − {reais(resultado.ad_spend)}</div>"
    f"</div>",
    unsafe_allow_html=True,
)

st.divider()

# ---------------------------------------------------------------------------
# 5 cartões
# ---------------------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Vendas", reais(resultado.vendas))
c2.metric("Ad Spend", reais(resultado.ad_spend))
c3.metric("ROAS Shopify", numero(resultado.roas) if resultado.roas is not None else "—")
c4.metric("Ticket médio", reais(resultado.ticket_medio) if resultado.ticket_medio is not None else "—")
c5.metric("Pedidos", numero(resultado.pedidos, 0))

st.divider()

# ---------------------------------------------------------------------------
# Cascata tipo DRE
# ---------------------------------------------------------------------------
st.subheader("Cascata (DRE) — de Vendas até a MC")

ui.tabela_dre(resultado.linhas, resultado.vendas, reais, numero)

st.caption(
    "Parâmetros de custo (%) embutidos no código (aba `Parametros` ainda não existe). "
    "Fonte dos dados: planilha Google única, só leitura."
)
