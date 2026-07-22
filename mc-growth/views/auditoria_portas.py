"""
views/auditoria_portas.py — a tela "A3 - Auditoria Portas".

Valida os pedidos de cada porta de entrada — foco em **Multiprodutos** e **Produto
desconhecido**, onde pode haver oportunidade escondida (SKU que merecia virar porta,
combinação comum, classificação errada). O fluxo (desenho do João):

  1. escolher a porta de entrada;
  2. ver a LISTA dos clientes daquela porta (1 linha por cliente; a estreia define a porta);
  3. clicar num cliente → abre embaixo a LINHA DO TEMPO de compras dele (produtos da 1ª
     compra, da 2ª, …, cada uma com a data e o período m+x).

Re-expõe a MESMA classificação da aba 4 (`portas.calcular_portas` → coluna `porta`); as coisas
novas são só o rótulo do MOTIVO do "Produto desconhecido" e, para **Multiprodutos** (30k clientes,
não se olham um a um), uma **tabela de combinações de linha da estreia** ranqueada — clica numa
combinação e abre os clientes dela. Nenhuma conta de dinheiro nova.
Privacidade: nunca mostra e-mail; no Comercial o `nome` do deal é o nome da PESSOA → mascarado.
Só lê. Spec: docs/specs/2026-07-16-auditoria-portas-drilldown.md
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import cascata
import dados
import portas
from coortes_ui import numero, reais
from dados import ErroDeDados

CAP_LISTA = 15000  # teto de linhas na lista (protege a UI); acima disso, pede para estreitar.


@st.cache_data(show_spinner="Lendo as portas de entrada…")
def _carregar(hoje_iso: str):
    """Lê tudo e monta a auditoria (estreias + motivo + ponte de produtos). Cacheado por dia."""
    base = dados.carregar_tudo()
    deals = dados.carregar_hubspot()
    hist = dados.carregar_itens_historico()
    mapa = dados.carregar_mapa_portas()
    aud = portas.auditar_portas(base, deals, mapa, hoje=pd.Timestamp(hoje_iso), hist=hist)
    mes_arquivo = str(deals["data_de_fechamento"].dropna().dt.to_period("M").max())
    return aud, mes_arquivo


def _pedido_visivel(nome, etapa) -> str:
    """
    Número do pedido para exibir, **sem vazar nome de pessoa**. No Comercial o `nome` é a PESSOA →
    "(Comercial)". Alguns deals Shipped (0,03%) também trazem um NOME no lugar do número → se o
    `nome` não é um número de pedido, mascara "(sem nº)". Só mostra o `#` quando é de fato um número.
    """
    if etapa != cascata.ETAPA_SHOPIFY:
        return "(Comercial)"
    chave = str(nome).lstrip("#")
    if not chave.replace(".", "").isdigit():
        return "(sem nº)"
    return "#" + chave


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.title("🔍 A3 — Auditoria das portas de entrada")
st.caption(
    "Escolha uma porta e veja os clientes que entraram por ela; clique num cliente para abrir a "
    "linha do tempo de compras dele (produtos de cada compra e quando aconteceu). Foco em "
    "**Multiprodutos** e **Produto desconhecido** — onde pode haver oportunidade não vista. Só lê."
)

coluna_botao, _ = st.columns([1, 3])
with coluna_botao:
    if st.button("🔄 Atualizar dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()

try:
    aud, mes_arquivo = _carregar(dt.date.today().isoformat())
except ErroDeDados as erro:
    st.error(str(erro))
    st.stop()

if aud.sem_dados:
    st.info(aud.avisos[0] if aud.avisos else "Sem safras fechadas para auditar.")
    st.stop()

# ---------------------------------------------------------------------------
# Controles: porta + faixa de safra + busca
# ---------------------------------------------------------------------------
opcoes = [f"{p}  ({numero(aud.n_por_porta.get(p, 0), 0)})" for p in aud.portas]
i_default = aud.portas.index(portas.PORTA_DESCONHECIDA) if portas.PORTA_DESCONHECIDA in aud.portas else 0
escolha = st.selectbox("Porta de entrada", opcoes, index=i_default)
porta_sel = aud.portas[opcoes.index(escolha)]

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    ini = st.selectbox("De (safra de estreia)", aud.safras, index=0)
with c2:
    fim = st.selectbox("Até (safra de estreia)", aud.safras, index=len(aud.safras) - 1)
with c3:
    busca = st.text_input("Buscar nº do pedido de estreia", value="").strip().lstrip("#")
ini_p, fim_p = pd.Period(ini, "M"), pd.Period(fim, "M")
if ini_p > fim_p:
    ini_p, fim_p = fim_p, ini_p

# ---------------------------------------------------------------------------
# Recorte: as estreias da porta escolhida na faixa de safra
# ---------------------------------------------------------------------------
est = aud.estreias
recorte = est[(est["porta"] == porta_sel)
              & (pd.PeriodIndex(est["safra"], freq="M") >= ini_p)
              & (pd.PeriodIndex(est["safra"], freq="M") <= fim_p)].copy()
if busca:
    recorte = recorte[recorte["nome"].astype(str).str.lstrip("#") == busca]

# Resuminho por motivo (só faz sentido no "Produto desconhecido").
if porta_sel == portas.PORTA_DESCONHECIDA and not recorte.empty:
    st.markdown("**Por que estes clientes ficaram sem porta?** (motivo da estreia)")
    vc = recorte["motivo"].value_counts()
    resumo = pd.DataFrame({"Motivo": vc.index, "Clientes": [numero(v, 0) for v in vc.values]})
    st.table(resumo.style.set_properties(subset=["Clientes"], **{"text-align": "right"}).hide(axis="index"))
    st.caption(
        "**Comercial** e **Estreia fora da base** são inerentes (outra numeração / venda cross-canal "
        "ou pré-out/2021). **Sem itens casados** e **Só brinde/sem-nome** são os **recuperáveis** — "
        "pedido Shopify no prazo que não virou porta por falta de item na base ou por SKU não mapeado."
    )

# ---------------------------------------------------------------------------
# Multiprodutos: 30k clientes não se olham um a um. Agrega pela COMBINAÇÃO de
# linhas da estreia; clicar numa combinação filtra a lista de clientes abaixo.
# ---------------------------------------------------------------------------
combo_sel = None
if porta_sel == portas.PORTA_MULTI and not busca and not recorte.empty:
    st.divider()
    st.subheader("Combinações de produtos na estreia")
    st.caption(
        "Cada linha é um conjunto de linhas de produto comprado **junto na 1ª compra**. "
        "Clique numa combinação para abrir os clientes dela (e daí o histórico de cada um)."
    )
    grp = (recorte[recorte["combo"] != ""]
           .groupby("combo")
           .agg(clientes=("valor", "size"), ticket=("valor", "mean"),
                valor_total=("valor_total", "sum"))
           .sort_values("clientes", ascending=False))
    combos_ord = grp.index.tolist()
    disp_c = pd.DataFrame({
        "combinacao": combos_ord,
        "produtos": [c.count("+") + 1 for c in combos_ord],
        "clientes": grp["clientes"].astype("int64").values,
        "ticket": grp["ticket"].astype(float).values,
        "valor_total": grp["valor_total"].astype(float).values,
    })
    ev_c = st.dataframe(
        disp_c, hide_index=True, width="stretch", height=380,
        on_select="rerun", selection_mode="single-row", key="tab_combos",
        column_config={
            "combinacao": st.column_config.TextColumn("combinação de linhas"),
            "produtos": st.column_config.NumberColumn("nº linhas", format="%d"),
            "clientes": st.column_config.NumberColumn("clientes", format="%d"),
            "ticket": st.column_config.NumberColumn("ticket médio 1ª (R$)", format="%.2f"),
            "valor_total": st.column_config.NumberColumn("valor total (R$)", format="%.2f"),
        },
    )
    st.caption(
        f"{numero(len(combos_ord), 0)} combinações distintas — as poucas primeiras concentram o volume. "
        "**nº linhas** = quantas linhas diferentes no mesmo pedido de estreia."
    )
    sel_c = ev_c.selection.rows if ev_c and ev_c.selection else []
    if not sel_c:
        st.info("👆 Clique numa combinação acima para ver os clientes dela.")
        st.stop()
    combo_sel = combos_ord[sel_c[0]]
    recorte = recorte[recorte["combo"] == combo_sel]

st.divider()
st.subheader(f"Clientes: {combo_sel}" if combo_sel else f"Clientes que entraram por: {porta_sel}")

if recorte.empty:
    st.info("Nenhum cliente nesta porta e faixa de safra (ou o nº buscado não está aqui).")
    st.stop()

# Cap de segurança: as portas grandes (ex. Camiseta, 193k) travariam a lista.
n_total = len(recorte)
if n_total > CAP_LISTA:
    recorte = recorte.sort_values("data_de_fechamento", ascending=False).head(CAP_LISTA)
    st.warning(
        f"Esta porta tem **{numero(n_total, 0)}** clientes na faixa — mostrando os **{numero(CAP_LISTA, 0)}** "
        "mais recentes. Estreite a faixa de safra para ver os demais."
    )

# ---------------------------------------------------------------------------
# Lista (1 linha por cliente) — clique numa linha para abrir a linha do tempo
# ---------------------------------------------------------------------------
recorte = recorte.sort_values("data_de_fechamento", ascending=False)
emails_ordenados = recorte.index.tolist()  # paralelo à tabela; NUNCA vai à tela (dado pessoal)

disp = pd.DataFrame({
    "data": recorte["data_de_fechamento"].dt.strftime("%d/%m/%Y"),
    "pedido": [_pedido_visivel(n, e) for n, e in zip(recorte["nome"], recorte["etapa_do_negocio"])],
    "compras": recorte["n_compras"].astype("int64"),
    "valor_1a": recorte["valor"].astype(float),
    "valor_total": recorte["valor_total"].astype(float),
    "motivo": recorte["motivo"],
})

st.write(f"**{numero(len(disp), 0)} clientes** — clique na caixinha à esquerda de uma linha para abrir as compras.")
evento = st.dataframe(
    disp,
    hide_index=True,
    width="stretch",
    height=420,
    on_select="rerun",
    selection_mode="single-row",
    key="tab_portas",
    column_config={
        "data": st.column_config.TextColumn("estreia"),
        "pedido": st.column_config.TextColumn("pedido de estreia"),
        "compras": st.column_config.NumberColumn("nº compras", format="%d"),
        "valor_1a": st.column_config.NumberColumn("valor 1ª compra (R$)", format="%.2f"),
        "valor_total": st.column_config.NumberColumn("valor total (R$)", format="%.2f"),
        "motivo": st.column_config.TextColumn("motivo (se desconhecido)"),
    },
)

# CSV da lista (sem e-mail; nome mascarado no Comercial).
csv = disp.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
st.download_button(
    "⬇️ Baixar a lista (CSV, sem e-mail)", data=csv,
    file_name=f"auditoria_portas_{porta_sel}.csv".replace(" ", "_"), mime="text/csv",
)

# ---------------------------------------------------------------------------
# Drill-down: a linha do tempo de compras do cliente clicado
# ---------------------------------------------------------------------------
st.divider()
selecao = evento.selection.rows if evento and evento.selection else []
if not selecao:
    st.caption("Clique na caixinha à esquerda de uma linha da tabela acima para ver as compras do cliente.")
    st.stop()

email_sel = emails_ordenados[selecao[0]]
tl = aud.enr[aud.enr["e_mail"] == email_sel].sort_values("data_de_fechamento")

cabecalho = disp.iloc[selecao[0]]
st.subheader(f"🧾 Compras do cliente — estreia {cabecalho['pedido']} · {cabecalho['data']}")
st.caption(
    f"{numero(len(tl), 0)} compra(s) · **m+x** = meses desde a 1ª compra (a idade da coorte). "
    "Produto sem nome/linha = SKU não mapeado (candidato a virar porta)."
)

itens = aud.itens
for i, (_, d) in enumerate(tl.iterrows(), start=1):
    nome = str(d["nome"]).lstrip("#")
    ped = _pedido_visivel(d["nome"], d["etapa_do_negocio"])
    st.markdown(
        f"**🛍️ Compra {i}** · {d['data_de_fechamento']:%d/%m/%Y} · **m+{int(d['idade'])}** · "
        f"{reais(float(d['valor']))} · {ped}"
    )
    # Regra de dinheiro (§11): só deal `Shipped` casa itens. No Comercial o `nome` é de outra
    # numeração e COLIDE com pedidos Shopify antigos → os itens que a ponte traria seriam de OUTRO
    # pedido. Não mostramos itens do Comercial (seria enganoso), como o CMV também não os casa.
    if d["etapa_do_negocio"] != cascata.ETAPA_SHOPIFY:
        st.caption("— Comercial: itens não rastreáveis (numeração à parte, não casa com a base).")
        continue
    its = itens[itens["order_name"].astype(str) == nome]
    if its.empty:
        st.caption("— Sem itens casados nesta base (item não exportado / pedido muito antigo).")
        continue
    linhas = pd.DataFrame({
        "produto": [aud.sku2nome.get(s, "—") for s in its["sku"]],
        "sku": its["sku"].astype(str).values,
        "linha": [aud.sku2linha.get(s, "— (não mapeado)") for s in its["sku"]],
        "papel": [aud.sku2papel.get(s, "desconhecido") for s in its["sku"]],
        "qtd": its["quantidade"].astype("int64").values,
    })
    st.dataframe(
        linhas, hide_index=True, width="stretch",
        column_config={
            "produto": st.column_config.TextColumn("produto"),
            "sku": st.column_config.TextColumn("SKU"),
            "linha": st.column_config.TextColumn("linha (porta)"),
            "papel": st.column_config.TextColumn("papel"),
            "qtd": st.column_config.NumberColumn("qtd", format="%d"),
        },
    )
