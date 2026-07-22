"""
Auditoria de custos por pedido (página anexa ao painel).

Lista os pedidos do período com valor, custo (CMV) e custo % da receita; marca os
suspeitos (sem custo / margem fora da faixa); abre um pedido para ver item a item
(SKU · descrição · qtd · custo unit · custo linha); e exporta em CSV.

Usa o MESMO recorte do painel (cascata._recorte_pedidos), então os totais batem com a MC.
Spec: docs/specs/2026-07-04-auditoria-custos-por-pedido.md
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import cascata
import dados
from dados import ErroDeDados



def reais(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(show_spinner="Lendo a planilha…")
def carregar() -> dados.Dados:
    return dados.carregar_tudo()


st.title("🔍 Auditoria de custos por pedido")
st.caption(
    "Confira, pedido a pedido, se o custo estimado (CMV) faz sentido. A soma bate com o "
    "CMV do painel (mesmo recorte, mesmas exclusões)."
)

# --- Período ---------------------------------------------------------------
hoje = dt.date.today()
periodo = st.date_input(
    "Período", value=(hoje.replace(day=1), hoje), format="DD/MM/YYYY"
)
if isinstance(periodo, (tuple, list)):
    if len(periodo) != 2:
        st.info("Escolha a data final do período.")
        st.stop()
    inicio, fim = periodo
else:
    inicio = fim = periodo

# --- Carrega e detalha -----------------------------------------------------
try:
    base = carregar()
except ErroDeDados as erro:
    st.error(str(erro))
    st.stop()

det = cascata.detalhar_pedidos(base, inicio, fim)
pp = det.por_pedido

if pp.empty:
    st.info("Sem pedidos no período.")
    st.stop()

# --- Resumo ----------------------------------------------------------------
n_suspeitos = int((pp["flag"] != "").sum())
cobertura_nome = (
    100 * (det.por_item["descricao"].str.strip() != "").mean() if len(det.por_item) else 0
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pedidos", f"{len(pp):,}".replace(",", "."))
c2.metric("Suspeitos", f"{n_suspeitos:,}".replace(",", "."))
c3.metric("CMV total", reais(pp["custo"].sum()))
c4.metric("Nomes cobertos", f"{cobertura_nome:.0f}%")

# --- Filtro ----------------------------------------------------------------
so_suspeitos = st.checkbox(
    f"Mostrar só suspeitos ({n_suspeitos}) — sem custo ou margem fora da faixa"
)
tabela = pp[pp["flag"] != ""] if so_suspeitos else pp

# --- Tabela por pedido -----------------------------------------------------
disp = tabela[["data", "order_name", "n_itens", "valor", "custo", "custo_pct", "flag", "order_id"]].copy()
disp["data"] = disp["data"].dt.strftime("%d/%m/%Y")
disp["order_name"] = "#" + disp["order_name"].astype("string")
# Chave que liga Vendas × Itens: o número final do order_id (gid://shopify/Order/<NÚMERO>).
disp["chave"] = disp["order_id"].astype("string").str.split("/").str[-1]

st.write(f"**{len(disp):,}".replace(",", ".") + " pedidos** — clique numa linha para ver os itens.")
evento = st.dataframe(
    disp,
    hide_index=True,
    width="stretch",
    height=420,
    on_select="rerun",
    selection_mode="single-row",
    key="tab_pedidos",
    column_order=["data", "order_name", "chave", "n_itens", "valor", "custo", "custo_pct", "flag"],
    column_config={
        "data": st.column_config.TextColumn("data"),
        "order_name": st.column_config.TextColumn("pedido"),
        "chave": st.column_config.TextColumn("id pedido (chave)"),
        "n_itens": st.column_config.NumberColumn("itens", format="%d"),
        "valor": st.column_config.NumberColumn("valor (R$)", format="%.2f"),
        "custo": st.column_config.NumberColumn("custo (R$)", format="%.2f"),
        "custo_pct": st.column_config.NumberColumn("custo %", format="%.1f"),
        "flag": st.column_config.TextColumn("⚠"),
    },
)

# --- Ver os itens de um pedido: por busca OU por clique na tabela -----------
st.subheader("Ver os itens de um pedido")
busca = st.text_input(
    "Digite o nº do pedido (ex: 469417) — ou clique na caixinha à esquerda de uma linha da tabela acima.",
    value="",
).strip().lstrip("#")

oid = None
titulo = None
if busca:
    alvo = pp[pp["order_name"].astype("string") == busca]
    if alvo.empty:
        st.info(f"Pedido {busca} não encontrado neste período.")
    else:
        oid = alvo.iloc[0]["order_id"]
        titulo = f"#{busca}  ·  {alvo.iloc[0]['data']:%d/%m/%Y}"
else:
    selecao = evento.selection.rows if evento and evento.selection else []
    if selecao:
        linha = disp.iloc[selecao[0]]
        oid = linha["order_id"]
        titulo = f"{linha['order_name']}  ·  {linha['data']}"

if oid is not None:
    st.markdown(f"**Itens do pedido {titulo}**")
    itens = det.por_item[det.por_item["order_id"] == oid].copy()
    itens["descricao"] = itens["descricao"].replace("", "—")
    st.dataframe(
        itens[["sku", "descricao", "quantidade", "custo_unit", "custo_linha"]],
        hide_index=True,
        width="stretch",
        column_config={
            "sku": st.column_config.TextColumn("SKU"),
            "descricao": st.column_config.TextColumn("descrição"),
            "quantidade": st.column_config.NumberColumn("qtd", format="%d"),
            "custo_unit": st.column_config.NumberColumn("custo unit (R$)", format="%.2f"),
            "custo_linha": st.column_config.NumberColumn("custo linha (R$)", format="%.2f"),
        },
    )
    if bool(itens["sem_custo"].any()):
        n = int(itens["sem_custo"].sum())
        st.warning(
            f"{n} item(ns) deste pedido está(ão) sem custo cadastrado (contam como 0). "
            "Corrija na página do painel, seção 🏷️."
        )
elif not busca:
    st.caption("Digite um número acima, ou clique na caixinha à esquerda de uma linha da tabela.")

# --- Exportar --------------------------------------------------------------
export = tabela[["data", "order_name", "order_id", "n_itens", "valor", "custo", "custo_pct", "flag"]].copy()
export["data"] = export["data"].dt.strftime("%d/%m/%Y")
export["chave"] = export["order_id"].astype("string").str.split("/").str[-1]
export = export[["data", "order_name", "chave", "n_itens", "valor", "custo", "custo_pct", "flag"]]
csv = export.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
st.download_button(
    "⬇️ Exportar CSV (para Sheets/Excel)",
    data=csv,
    file_name="auditoria_custos.csv",
    mime="text/csv",
)
