"""
views/auditoria_cohort.py — a tela "A2 - Auditoria MC Cohort".

Abre a CASCATA da MC de um cohort: de onde vem cada real que o triângulo mostra. Três blocos:
A) MC dos novos (a 1ª compra de cada cliente, com a mídia inteira), B) MC de recompra (as
compras seguintes, sem mídia) e C) o total (× por cliente). Re-expõe a MESMA `mc_produto` do
triângulo — não recalcula nada —, e a reconciliação com a célula da aba Cohorts aparece na tela.

Saiu da aba Cohorts em 2026-07-14 (pedido do João): lá ficam as tabelas de leitura; aqui, a
ferramenta de conferência. Só lê (nunca escreve).
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import cascata
import ui
from coortes_ui import (COR_NEGATIVA, COR_POSITIVA, auditar, carregar_e_calcular, numero,
                        pct, reais)
from dados import ErroDeDados

st.title("🔍 A2 — Auditoria da MC por cohort")
st.caption(
    "Confira de onde vem a MC de um cohort: a receita e os descontos que entraram, real × "
    "estimado. A cascata re-expõe o mesmo número do triângulo da aba Cohorts (reconciliação "
    "no fim). MC, nunca 'lucro'."
)

coluna_botao, _ = st.columns([1, 3])
with coluna_botao:
    if st.button("🔄 Atualizar dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()

try:
    resultado, _mes_arquivo = carregar_e_calcular(dt.date.today().isoformat())
except ErroDeDados as erro:
    st.error(str(erro))
    st.stop()

if resultado.sem_safras:
    st.info("Sem safras fechadas para auditar.")
    st.stop()

safra_sel = st.selectbox(
    "Cohort a auditar", list(reversed(resultado.safras)), index=0,
    help="A turma que fez a 1ª compra neste mês (cross-canal, do HubSpot).",
)


def _tabela_cascata(linhas, vendas_base, cor_resultado):
    """Cascata no MESMO formato das outras abas — desenhada pela peça compartilhada (ui.py)."""
    ui.tabela_dre(
        [cascata.LinhaDRE(rot, val, tipo) for rot, val, tipo in linhas],
        vendas_base, reais, numero, cor_resultado=cor_resultado, titulo_pct="% de Vendas",
    )


# Horizonte: quantos meses de recompra entrar (padrão = último mês fechado da safra).
det0 = auditar(safra_sel, dt.date.today().isoformat())  # horizonte cheio (p/ saber o teto)
ate = det0.idade_max_fechada
if det0.idade_max_fechada > 0:
    ate = st.slider(
        "Analisar recompra até o mês da turma (horizonte)", 0, det0.idade_max_fechada,
        value=det0.idade_max_fechada,
        help="m+0 = só o mês de entrada; aumentar inclui as recompras dos meses seguintes.",
    )
det = auditar(safra_sel, dt.date.today().isoformat(), ate)

for aviso in det.avisos:
    if "Midia não cobre" in aviso:
        st.warning(aviso)

cor_res = COR_POSITIVA if (pd.notna(det.mc_total_cliente) and det.mc_total_cliente >= 0) else COR_NEGATIVA

st.caption(
    f"Cohort **{safra_sel}** · **{numero(det.n_clientes, 0)} clientes** · analisando de **m+0** "
    f"a **m+{det.ate_idade}** (a turma tem {det.idade_max_fechada + 1} mês(es) fechado(s))."
)

# =====================================================================
# BLOCO A — MC dos NOVOS (1ª compra), cascata completa igual às outras abas
# =====================================================================
st.markdown("**A) MC dos novos** — a 1ª compra de cada cliente da turma (com a mídia inteira)")
_tabela_cascata(det.cascata_novos, det.vendas_novos, cor_res)
st.caption(
    f"{numero(det.n_novos, 0)} clientes novos. É a **aquisição**: a 1ª compra menos a mídia "
    "inteira do mês. ⚠️ Não é igual à aba **Aquisição** — lá 'novo' é o carimbo do Shopify; "
    "aqui é quem fez a **1ª compra na Minimal** (régua da coorte, cross-canal)."
)

# =====================================================================
# BLOCO B — MC de RECOMPRA (compras seguintes), agrupada, sem mídia
# =====================================================================
st.markdown("**B) MC de recompra** — as compras seguintes da mesma turma (sem mídia nova)")
_tabela_cascata(det.cascata_recompra, det.vendas_recompra, cor_res)
st.caption(
    f"{numero(det.n_recompra, 0)} pedidos de recompra (de m+0 a m+{det.ate_idade}). A mídia "
    "**não** entra aqui — o custo de trazer o cliente já foi cobrado no bloco A."
)

# =====================================================================
# BLOCO C — MC TOTAL da turma (novos + recompra) e por cliente
# =====================================================================
st.markdown("**C) MC total da turma** — novos + recompra")
linhas_c = [
    ("MC dos novos", det.mc_novos, "subtotal"),
    ("MC de recompra", det.mc_recompra, "subtotal"),
    ("MC total da turma", det.mc_total, "resultado"),
]
tab_c = pd.DataFrame({
    "Linha": [r for r, _v, _t in linhas_c],
    "Total da turma": [reais(v) for _r, v, _t in linhas_c],
    "Por cliente": [reais(v / det.n_clientes if det.n_clientes else float("nan"))
                    for _r, v, _t in linhas_c],
})
tipos_c = [t for _r, _v, t in linhas_c]
ESTILO_C = {
    "subtotal": "background-color:#dbeafe; color:#1e3a8a; font-weight:700",
    "resultado": f"background-color:{cor_res}; color:#ffffff; font-weight:700",
}
st.table(
    tab_c.style.apply(lambda ln: [ESTILO_C.get(tipos_c[ln.name], "")] * len(ln), axis=1)
    .set_properties(subset=["Total da turma", "Por cliente"], **{"text-align": "right"})
    .hide(axis="index")
)

# Reconciliação com o triângulo (no MESMO horizonte)
tri = resultado.mc_acumulada.loc[safra_sel, det.ate_idade] if det.ate_idade in resultado.mc_acumulada.columns else float("nan")
bate = pd.notna(tri) and abs(det.mc_total_cliente - tri) < 1e-4
st.markdown(
    f"➡️ **MC total por cliente = {reais(det.mc_total_cliente)}** — é o valor da célula "
    f"**m+{det.ate_idade}** da safra no triângulo ({reais(tri) if pd.notna(tri) else '—'}) "
    + ("✅ bate." if bate else "⚠️ **não bate** — investigar.")
)

# --- Visão avançada: mês a mês (opcional) + export ----------------------
if st.checkbox("Ver a formação mês a mês (avançado)", value=False):
    pid = det.por_idade.copy()
    disp = pd.DataFrame({
        "Idade": pid["idade"],
        "Pedidos": pid["deals"].map(lambda x: numero(x, 0)),
        "% medido": pid["%real"].map(lambda x: pct(x) if pd.notna(x) else "—"),
        "Receita (total)": pid["receita"].map(reais),
        "Deduções (total)": pid["deducoes"].map(reais),
        "CMV (total)": pid["cmv"].map(reais),
        "Margem de produto (total)": pid["lucro_bruto"].map(reais),
        "Mídia (total)": pid["midia"].map(reais),
        "MC no mês / cliente": pid["mc_incr_cliente"].map(reais),
        "MC acumulada / cliente": pid["mc_acum_cliente"].map(reais),
    })
    st.dataframe(disp, hide_index=True, width="stretch")
    st.caption("Uma linha por idade da turma; a última coluna vai somando até virar a MC/cliente.")

csv = det.deals_export.to_csv(index=False).encode("utf-8")
st.download_button(
    f"⬇️ Baixar os {numero(det.n_deals, 0)} pedidos do cohort {safra_sel} (CSV, sem e-mail)",
    data=csv,
    file_name=f"coorte_{safra_sel}_pedidos.csv",
    mime="text/csv",
)
st.caption(
    "1 linha por pedido (chave = número do pedido, liga na planilha) · colunas: pedido, safra, "
    "idade, tipo, ramo (medido/estimado), receita, cmv, mc_produto. Sem e-mail (dado pessoal)."
)
