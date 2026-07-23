"""
jornada_produto.py — Jornada de Produto (análise local, Modo A).

Pergunta: a partir da PORTA DE ENTRADA (produto único ou combo aprovado da 1ª compra),
o que o cliente compra na 2ª, 3ª, 4ª+ compra, e em quanto tempo isso acontece?

REUSA a lógica já validada do mc-growth para a ponte pedido->itens e para safra/idade
(nenhuma verdade nova de dado): `cascata.itens_por_nome`, `coortes.preparar_deals_cache`,
`portas._estreias` (desempate: TEM produto). A classificação de PRODUTO/COMBO do pedido,
porém, é PRÓPRIA deste módulo (decisão do Daniel, 2026-07-23) — diverge da régua de
`portas.py` em dois pontos:
  1. Carteira e Perfume (hoje misturados no SKU genérico "BRINDE" do mc-growth) entram
     como itens de 1ª classe na combinação — não são descartados como ruído.
  2. Combos não são promovidos por volume (>=1000 clientes) — só os da lista aprovada
     (`NAMED_COMBOS`) ganham rótulo próprio; o resto cai em "Multiprodutos".

REGRA DA ENTRADA: elegível quem estreou (Shopify, idade 0) com UM produto só OU com um
dos combos aprovados. "Camiseta Minimal" sozinha é ainda subdividida por QUANTIDADE
(1/4/6/10 unidades — picos reais da base; qualquer outra quantidade cai em "outras").

Este módulo só LÊ as bases locais (bases/hubspot_deals.csv, bases/itens_historico.csv,
bases/mapa_sku_linha_produto.csv) — não toca a planilha Google (não precisa de rede).
Não escreve em lugar nenhum. Saída: tabelas pandas, exportadas como CSV para
`saida_local/` (fora do painel; nada sobe para o gerenciadordecrm sem comando do Daniel).
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

import cascata
import coortes
import dados
import portas

PASTA_SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida_local")

# Quantas compras seguintes analisar (2ª, 3ª, 4ª, 5ª+). A 5ª agrega tudo dali em diante
# (a base fica esparsa depois disso).
COMPRAS_SEGUINTES = [2, 3, 4, 5]
N_MINIMO_CELULA = 30  # célula com menos clientes que isso não é reportada (ruído)

# Entrada (produto único ou combo) com menos clientes que isso é excluída da análise
# inteira — decisão do Daniel, 2026-07-23 (limpeza: cauda longa de linhas/combos raros).
N_MINIMO_ENTRADA = 1000

# ---------------------------------------------------------------------------
# Janela de recência/reativação — a MESMA definição oficial já validada com o
# Daniel em 2026-07-21 pra fact_repurchase_monthly_metrics (mensal/global);
# aqui adaptada pra uma foto de HOJE e por evento de compra (2026-07-23):
#   Recente   = 1ª compra (a entrada) há menos de RECENTE_MESES meses.
#   Ativo     = já não é recente, mas comprou de novo dentro de INATIVO_MESES
#               meses da compra anterior (a "janela" ainda está aberta).
#   Inativo   = mais de INATIVO_MESES meses sem comprar (a janela fechou).
# Uma compra que vem DEPOIS da janela fechar é um evento de REATIVAÇÃO.
# ---------------------------------------------------------------------------
RECENTE_MESES = 6
INATIVO_MESES = 11
LTV_JANELA_DIAS = 180

# ---------------------------------------------------------------------------
# Limpeza do SKU genérico "BRINDE" do mc-growth: mistura Carteira e amostras de
# Perfume. Aqui eles são produtos distintos (decisão do Daniel, 2026-07-23).
# ---------------------------------------------------------------------------
SKU_CARTEIRA = {"8301007000"}                                  # Carteira Minimal Club
SKU_PERFUME_BRINDE = {"1301002112", "1301002011", "1301002012"}  # amostras/brinde de perfume

# Sub-linhas que se juntam num nome genérico SÓ para efeito de combo (a entrada de
# produto único continua usando o nome específico — decisão do Daniel, 2026-07-23).
ALIAS_COMBO = {
    "Calça Jeans 1.0": "Jeans", "Calça Jeans 2.0": "Jeans",
    "Camisa Social Tech Classics": "Social", "Camisa Social Malha": "Social",
}

# Combos aprovados pelo Daniel (2026-07-23) — os 7 pedidos + 4 descobertos na análise
# de frequência e aprovados por ele. Qualquer outro par de linhas cai em "Multiprodutos".
NAMED_COMBOS: dict[frozenset, str] = {
    frozenset({"Camiseta Minimal", "Jeans"}): "Camiseta + Jeans",
    frozenset({"Camiseta Minimal", "Camiseta Fitness"}): "Camiseta + Camiseta Fitness",
    frozenset({"Camiseta Minimal", "Perfume"}): "Camiseta + Perfume",
    frozenset({"Camiseta Minimal", "Carteira"}): "Camiseta + Carteira",
    frozenset({"Jeans", "Calça Comfort"}): "Jeans + Comfort",
    frozenset({"Camiseta Minimal", "Calça Comfort"}): "Camiseta + Comfort",
    frozenset({"Camiseta Minimal", "Social"}): "Camiseta + Social",
    frozenset({"Camiseta Minimal", "Cueca"}): "Camiseta + Cueca",
    frozenset({"Camiseta Minimal", "Camisa Henley"}): "Camiseta + Camisa Henley",
    frozenset({"Camiseta Minimal", "Polo 2.0"}): "Camiseta + Polo 2.0",
    frozenset({"Camiseta Minimal", "Calça Alfaiataria"}): "Camiseta + Calça Alfaiataria",
}

# Quantidade de Camiseta Minimal na entrada — picos reais da base (validado 2026-07-23:
# 4un=151k pedidos, 1un=80k, 6un=14,6k, 10un=3,2k). Qualquer outra quantidade -> "outras".
BUCKETS_QUANTIDADE_CAMISETA = [1, 4, 6, 10]


def _dados_vazio() -> dados.Dados:
    """Um `Dados` com vendas/itens/custos/midia vazios — para reusar `cascata`/`coortes`
    sem tocar a planilha Google (esta análise não usa dinheiro, só produto e tempo)."""
    return dados.Dados(
        vendas=pd.DataFrame({
            "order_id": pd.Series(dtype="string"), "order_name": pd.Series(dtype="string"),
            "data": pd.Series(dtype="datetime64[ns]"), "net_revenue": pd.Series(dtype="float64"),
            "customer_type": pd.Series(dtype="string"),
        }),
        itens=pd.DataFrame({
            "order_id": pd.Series(dtype="string"), "data": pd.Series(dtype="datetime64[ns]"),
            "sku": pd.Series(dtype="string"), "quantidade": pd.Series(dtype="float64"),
            "descricao": pd.Series(dtype="string"),
        }),
        custos=pd.DataFrame({"sku": pd.Series(dtype="string"), "valor_custo": pd.Series(dtype="float64")}),
        midia=pd.DataFrame({
            "data": pd.Series(dtype="datetime64[ns]"), "fb_investimento": pd.Series(dtype="float64"),
            "google_investimento": pd.Series(dtype="float64"),
            "google_institucional_investimento": pd.Series(dtype="float64"),
            "investimento_total": pd.Series(dtype="float64"),
        }),
    )


def carregar_base():
    """Lê as 3 bases locais e devolve (dados_vazio, deals, hist, mapa)."""
    d = _dados_vazio()
    deals = dados.carregar_hubspot()
    hist = dados.carregar_itens_historico()
    mapa = dados.carregar_mapa_portas()
    return d, deals, hist, mapa


def _mapa_limpo(mapa: pd.DataFrame) -> pd.DataFrame:
    """Aplica a limpeza Carteira/Perfume no mapa SKU->linha (só neste módulo; não
    altera `bases/mapa_sku_linha_produto.csv` nem o comportamento de `portas.py`)."""
    m = mapa.copy()
    m.loc[m["sku"].isin(SKU_CARTEIRA), "linha"] = "Carteira"
    m.loc[m["sku"].isin(SKU_PERFUME_BRINDE), "linha"] = "Perfume"
    return m


def _itens_relevantes(dados_vazio, hist: pd.DataFrame, mapa: pd.DataFrame) -> pd.DataFrame:
    """
    Itens de todo pedido que contam para a classificação: papel "porta" (produto de
    verdade) OU linha "Carteira"/"Perfume" (os 2 brindes promovidos a 1ª classe pelo
    Daniel). Skincare e qualquer outro brinde continuam ruído (descartados, como antes).
    """
    itens = cascata.itens_por_nome(dados_vazio, hist).copy()
    m = _mapa_limpo(mapa).set_index("sku")
    itens["linha"] = itens["sku"].map(m["linha"])
    itens["papel"] = itens["sku"].map(m["papel"]).fillna("desconhecido")
    relevante = (itens["papel"] == "porta") | (itens["linha"].isin(["Carteira", "Perfume"]))
    return itens[relevante & itens["linha"].notna()]


def _linhas_por_pedido(itens_rel: pd.DataFrame) -> pd.Series:
    """order_name -> conjunto (frozenset) das linhas relevantes do pedido."""
    return itens_rel.groupby("order_name")["linha"].agg(lambda s: frozenset(s.dropna()))


def classificar_pedido(linhas: frozenset) -> str:
    """
    O NOME do produto/combo de um pedido, a partir do conjunto de linhas relevantes:
      - 0 linha                                  -> "Produto desconhecido"
      - 1 linha                                  -> o nome específico dela (sem alias)
      - 2+ linhas que aliasam para 1 família só   -> o nome genérico da família
        (ex.: Jeans 1.0 + Jeans 2.0 no mesmo pedido -> "Jeans")
      - exatamente 2 famílias E o par está em `NAMED_COMBOS` -> o rótulo do combo
      - qualquer outra combinação                -> "Multiprodutos"
    """
    if not linhas:
        return portas.PORTA_DESCONHECIDA
    if len(linhas) == 1:
        return next(iter(linhas))
    aliased = frozenset(ALIAS_COMBO.get(l, l) for l in linhas)
    if len(aliased) == 1:
        return next(iter(aliased))
    if len(aliased) == 2 and aliased in NAMED_COMBOS:
        return NAMED_COMBOS[aliased]
    return portas.PORTA_MULTI


def _bucket_quantidade(qtd: float) -> str:
    """Rótulo de quantidade para a entrada "Camiseta Minimal sozinha"."""
    if qtd in BUCKETS_QUANTIDADE_CAMISETA:
        return f"Camiseta Minimal ({int(qtd)} un)"
    return "Camiseta Minimal (outras qtd)"


def familia_entrada(entrada: str) -> str:
    """
    A família do PRODUTO por trás de um rótulo de entrada — para comparar com o rótulo
    da compra seguinte (`produto_pedido`, que NUNCA leva sufixo de quantidade: uma 2ª
    compra de camiseta aparece sempre como "Camiseta Minimal", não "Camiseta Minimal
    (4 un)"). Sem isso, "retenção do produto de entrada" dava 0% para as 5 entradas de
    quantidade (bug encontrado 2026-07-23: comparava a string exata, que nunca batia).
    """
    if entrada.startswith("Camiseta Minimal ("):
        return "Camiseta Minimal"
    return entrada


# Combo (rótulo) -> as linhas que o compõem — o inverso de NAMED_COMBOS.
_COMBO_POR_ROTULO: dict[str, frozenset] = {v: k for k, v in NAMED_COMBOS.items()}


def linhas_da_entrada(entrada: str) -> frozenset:
    """
    As linhas que precisam estar PRESENTES numa compra seguinte para contar como
    "comprou o mesmo produto da entrada de novo" (retenção). Solo -> 1 linha (a
    família, sem sufixo de quantidade). Combo -> as 2 linhas do combo (as duas têm
    que aparecer; pode vir mais coisa junto, isso não desconta).
    """
    fam = familia_entrada(entrada)
    return _COMBO_POR_ROTULO.get(fam, frozenset({fam}))


def montar_jornada(d, deals: pd.DataFrame, hist: pd.DataFrame, mapa: pd.DataFrame):
    """
    Devolve (enr, entrada_por_cliente, produto_pedido, linhas_pedido):
      - enr: todos os deals enriquecidos (safra, idade, e_mail, nome, data_de_fechamento, ...)
      - entrada_por_cliente: Series e_mail -> rótulo da entrada (produto único, combo
        aprovado, ou "Camiseta Minimal (N un)"), SÓ para quem é elegível (Shipped, idade 0)
      - produto_pedido: order_name -> classificação EXCLUSIVA do pedido (só usada pra
        decidir a entrada — produto único ou combo aprovado; nunca pra medir "o que
        ofertar depois", que precisa de presença, não de classificação — ver
        `afinidade_por_compra`)
      - linhas_pedido: order_name -> frozenset das linhas PRESENTES no pedido (a base
        da análise de afinidade/oferta)
    """
    enr = coortes.preparar_deals_cache(d, deals, hist=hist)

    itens_rel = _itens_relevantes(d, hist, mapa)
    linhas_pedido = _linhas_por_pedido(itens_rel)
    produto_pedido = linhas_pedido.map(classificar_pedido)

    com_porta = set(linhas_pedido.index.astype(str))
    estreia = portas._estreias(enr, com_porta)

    produto_estreia = estreia["nome"].map(produto_pedido).fillna(portas.PORTA_DESCONHECIDA)
    elegivel = (
        (estreia["etapa_do_negocio"] == cascata.ETAPA_SHOPIFY)
        & (estreia["idade"] == 0)
        & ~produto_estreia.isin([portas.PORTA_MULTI, portas.PORTA_DESCONHECIDA])
    )

    rotulo_entrada = produto_estreia.where(elegivel)

    # Camiseta Minimal sozinha: subdivide por quantidade total na entrada (1/4/6/10/outras).
    eh_so_camiseta = elegivel & (produto_estreia == "Camiseta Minimal")
    if eh_so_camiseta.any():
        qtd_camiseta = (
            itens_rel[itens_rel["linha"] == "Camiseta Minimal"]
            .groupby("order_name")["quantidade"].sum()
        )
        qtd_por_cliente = estreia.loc[eh_so_camiseta, "nome"].map(qtd_camiseta)
        rotulo_entrada.loc[eh_so_camiseta] = qtd_por_cliente.map(_bucket_quantidade)

    entrada_por_cliente = rotulo_entrada[elegivel]

    # Limpeza (decisão do Daniel, 2026-07-23): entrada com menos de N_MINIMO_ENTRADA
    # clientes some da análise inteira — não só da tela, o cliente sai do denominador.
    contagem = entrada_por_cliente.value_counts()
    validas = set(contagem[contagem >= N_MINIMO_ENTRADA].index)
    entrada_por_cliente = entrada_por_cliente[entrada_por_cliente.isin(validas)]

    return enr, entrada_por_cliente, produto_pedido, linhas_pedido


def sequenciar_compras(enr: pd.DataFrame, entrada_por_cliente: pd.Series,
                       produto_pedido: pd.Series) -> pd.DataFrame:
    """
    Uma linha por COMPRA de cada cliente elegível, com:
    e_mail, entrada (rótulo da 1ª compra), posicao (1=entrada, 2, 3, ...),
    data_de_fechamento, produto (rótulo da compra), valor, dias_desde_entrada,
    dias_desde_compra_anterior.
    """
    clientes = set(entrada_por_cliente.index)
    sub = enr[enr["e_mail"].isin(clientes)].copy()
    sub = sub.sort_values(["e_mail", "data_de_fechamento", "nome"])
    sub["posicao"] = sub.groupby("e_mail").cumcount() + 1
    sub["entrada"] = sub["e_mail"].map(entrada_por_cliente)
    sub["produto"] = sub["nome"].map(produto_pedido).fillna(portas.PORTA_DESCONHECIDA)

    primeira_data = sub.groupby("e_mail")["data_de_fechamento"].transform("min")
    sub["dias_desde_entrada"] = (sub["data_de_fechamento"] - primeira_data).dt.days
    sub["dias_desde_compra_anterior"] = (
        sub.groupby("e_mail")["data_de_fechamento"].diff().dt.days
    )
    return sub[[
        "e_mail", "entrada", "posicao", "nome", "data_de_fechamento", "produto", "valor",
        "dias_desde_entrada", "dias_desde_compra_anterior",
    ]]


def afinidade_por_compra(seq: pd.DataFrame, linhas_pedido: pd.Series,
                         entrada_por_cliente: pd.Series,
                         compras: list[int] = COMPRAS_SEGUINTES,
                         n_minimo: int = N_MINIMO_CELULA) -> pd.DataFrame:
    """
    "O que ofertar depois" — decisão do Daniel, 2026-07-23, substitui a 1ª versão
    (classificação exclusiva do pedido inteiro), que enterrava a informação real em
    "Multiprodutos"/"Produto desconhecido" toda vez que o carrinho não batia com um
    dos 11 combos aprovados.

    Aqui a pergunta é por PRESENÇA, não por classificação: cada linha (produto
    individual) que apareceu naquela compra conta — um pedido com Camiseta+Jeans soma
    tanto pra "Camiseta Minimal" quanto pra "Jeans". Por isso a % de um passo pode
    somar mais de 100% (um mesmo pedido pode aparecer em várias linhas).

    `pct_da_entrada` usa o denominador FIXO = tamanho total da entrada (mesma correção
    do bug de 2026-07-23). Uma linha extra por (entrada, compra), produto
    `"__RETENCAO__"`, guarda quantos tiveram TODAS as linhas da própria entrada de
    novo (ver `linhas_da_entrada`) — é o número do gráfico de retenção.
    """
    n_total_entrada = entrada_por_cliente.value_counts()
    s = seq[seq["posicao"].isin(compras)]

    saida = []
    for entrada, g_entrada in s.groupby("entrada"):
        n_entrada = int(n_total_entrada.get(entrada, 0))
        if n_entrada == 0:
            continue
        requeridas = linhas_da_entrada(entrada)
        for pos, g in g_entrada.groupby("posicao"):
            total = len(g)
            if total < n_minimo:
                continue
            contagem: dict[str, int] = {}
            com_todas = 0
            for nome in g["nome"]:
                presentes = linhas_pedido.get(nome, frozenset())
                for linha in presentes:
                    contagem[linha] = contagem.get(linha, 0) + 1
                # Cada linha requerida bate se estiver presente DIRETO (entrada solo,
                # nome específico: "Calça Jeans 1.0") OU se alguma linha presente
                # ALIASA pra ela (entrada combo, nome genérico: "Jeans" cobre tanto
                # "Calça Jeans 1.0" quanto "2.0"). Comparar só pelo aliasado quebrava
                # a entrada solo (bug 2026-07-23, 2ª rodada: virou tudo 0%).
                if requeridas and all(
                    r in presentes or any(ALIAS_COMBO.get(l, l) == r for l in presentes)
                    for r in requeridas
                ):
                    com_todas += 1
            for produto, n in sorted(contagem.items(), key=lambda kv: -kv[1]):
                saida.append({
                    "entrada": entrada, "compra": f"{pos}a", "produto": produto,
                    "clientes": int(n), "pct_da_entrada": float(n / n_entrada * 100),
                    "n_base_da_compra": int(total),
                })
            saida.append({
                "entrada": entrada, "compra": f"{pos}a", "produto": "__RETENCAO__",
                "clientes": int(com_todas), "pct_da_entrada": float(com_todas / n_entrada * 100),
                "n_base_da_compra": int(total),
            })
    out = pd.DataFrame(saida)
    if out.empty:
        return out
    return out.sort_values(["entrada", "compra", "clientes"], ascending=[True, True, False])


def tempo_entre_compras(seq: pd.DataFrame, compras: list[int] = COMPRAS_SEGUINTES,
                        n_minimo: int = N_MINIMO_CELULA) -> pd.DataFrame:
    """
    Por (entrada, posição), duas visões de tempo:
      - acumulado: mediana/média de dias desde a ENTRADA até essa compra;
      - entre_recompras: mediana/média de dias desde a compra ANTERIOR (gap).
    """
    s = seq[seq["posicao"].isin(compras)].copy()
    linhas = []
    for (entrada, pos), g in s.groupby(["entrada", "posicao"]):
        n = g["e_mail"].nunique()
        if n < n_minimo:
            continue
        linhas.append({
            "entrada": entrada,
            "compra": f"{pos}a",
            "clientes": int(n),
            "dias_acumulado_mediana": float(g["dias_desde_entrada"].median()),
            "dias_acumulado_media": float(g["dias_desde_entrada"].mean()),
            "dias_entre_recompras_mediana": float(g["dias_desde_compra_anterior"].median()),
            "dias_entre_recompras_media": float(g["dias_desde_compra_anterior"].mean()),
        })
    out = pd.DataFrame(linhas)
    if out.empty:
        return out
    return out.sort_values(["entrada", "compra"])


def _mes_diff(a: pd.Series, b: pd.Series) -> pd.Series:
    """Diferença em meses-calendário (a − b), mesma convenção de `coortes._preparar_deals`."""
    return (a.dt.year - b.dt.year) * 12 + (a.dt.month - b.dt.month)


def classificar_momento_compras(seq: pd.DataFrame) -> pd.DataFrame:
    """
    Devolve `seq` (posição >= 2) com 3 colunas novas — o MOMENTO de cada compra
    seguinte, olhando a data dela contra a entrada e a compra anterior do MESMO
    cliente (não o status do cliente hoje — é por evento, então um cliente pode
    ter compras em momentos diferentes ao longo da vida):

      - `meses_desde_entrada`: meses-calendário desde a 1ª compra do cliente.
      - `gap_meses`          : meses-calendário desde a compra ANTERIOR dele.
      - `momento`            : "Recente" (ainda no 1º semestre de vida) |
        "Reativação" (o gap desde a anterior é maior que `INATIVO_MESES` — a
        janela de atividade tinha fechado) | "Repetição" (o resto — comprou de
        novo dentro da janela, já fora do 1º semestre).

    Régua oficial (fact_repurchase_monthly_metrics, validada com o Daniel em
    2026-07-21): RECENTE_MESES=6, INATIVO_MESES=11. Adaptada aqui de "mensal/
    global" pra "por evento de compra" (2026-07-23).
    """
    s = seq.sort_values(["e_mail", "posicao"]).copy()
    s["data_anterior"] = s.groupby("e_mail")["data_de_fechamento"].shift(1)
    primeira_data = s.groupby("e_mail")["data_de_fechamento"].transform("min")
    s["meses_desde_entrada"] = _mes_diff(s["data_de_fechamento"], primeira_data)
    s["gap_meses"] = _mes_diff(s["data_de_fechamento"], s["data_anterior"])

    s = s[s["posicao"] >= 2].copy()
    condicoes = [s["meses_desde_entrada"] < RECENTE_MESES, s["gap_meses"] > INATIVO_MESES]
    escolhas = ["Recente", "Reativação"]
    s["momento"] = np.select(condicoes, escolhas, default="Repetição")
    return s


def status_atual_por_cliente(seq: pd.DataFrame, hoje=None) -> pd.Series:
    """
    e_mail -> status HOJE ("Recente" | "Ativo" | "Inativo"), mesma régua oficial.
    Recente = a entrada foi há menos de RECENTE_MESES meses (não importa se
    comprou de novo). Ativo = já não é recente, mas a última compra foi há até
    INATIVO_MESES meses. Inativo = mais que isso sem comprar.
    """
    hoje = pd.Timestamp(hoje) if hoje is not None else pd.Timestamp.today()
    g = seq.groupby("e_mail")["data_de_fechamento"].agg(["min", "max"])
    meses_desde_entrada = _mes_diff(pd.Series(hoje, index=g.index), g["min"])
    meses_desde_ultima = _mes_diff(pd.Series(hoje, index=g.index), g["max"])
    condicoes = [meses_desde_entrada < RECENTE_MESES, meses_desde_ultima > INATIVO_MESES]
    escolhas = ["Recente", "Inativo"]
    return pd.Series(np.select(condicoes, escolhas, default="Ativo"), index=g.index)


def ltv_por_entrada(seq: pd.DataFrame, entrada_por_cliente: pd.Series,
                    janela_dias: int = LTV_JANELA_DIAS) -> pd.DataFrame:
    """
    LTV por cliente = Σ `valor` de todas as compras dentro de `janela_dias` desde a
    entrada (inclui a própria compra de entrada). Devolve média/mediana por entrada
    — mesma base de clientes de `entrada_por_cliente` (quem não comprou de novo
    entra com o valor só da entrada, não com zero nem é excluído).
    """
    dentro = seq[seq["dias_desde_entrada"] <= janela_dias]
    ltv_cliente = dentro.groupby("e_mail")["valor"].sum()
    ltv_cliente = ltv_cliente.reindex(entrada_por_cliente.index).fillna(0.0)

    linhas = []
    for entrada, grupo in ltv_cliente.groupby(entrada_por_cliente):
        linhas.append({
            "entrada": entrada,
            "clientes": int(len(grupo)),
            f"ltv_{janela_dias}d_media": float(grupo.mean()),
            f"ltv_{janela_dias}d_mediana": float(grupo.median()),
        })
    return pd.DataFrame(linhas).sort_values("entrada")


def taxas_por_entrada(seq: pd.DataFrame, seq_momento: pd.DataFrame,
                      entrada_por_cliente: pd.Series, hoje=None) -> pd.DataFrame:
    """
    Por entrada: taxa de repetição (% da entrada com >=1 compra tipo "Repetição",
    alguma vez), taxa de reativação (% com >=1 compra tipo "Reativação", alguma
    vez), e o status ATUAL (hoje) — % recente / % ativo / % inativo.
    """
    status_hoje = status_atual_por_cliente(seq, hoje=hoje)

    clientes_repeticao = set(seq_momento.loc[seq_momento["momento"] == "Repetição", "e_mail"])
    clientes_reativacao = set(seq_momento.loc[seq_momento["momento"] == "Reativação", "e_mail"])

    linhas = []
    for entrada, clientes in entrada_por_cliente.groupby(entrada_por_cliente).groups.items():
        n = len(clientes)
        st = status_hoje.reindex(clientes)
        linhas.append({
            "entrada": entrada,
            "clientes": int(n),
            "taxa_repeticao": float(sum(1 for c in clientes if c in clientes_repeticao) / n * 100),
            "taxa_reativacao": float(sum(1 for c in clientes if c in clientes_reativacao) / n * 100),
            "pct_recente_hoje": float((st == "Recente").sum() / n * 100),
            "pct_ativo_hoje": float((st == "Ativo").sum() / n * 100),
            "pct_inativo_hoje": float((st == "Inativo").sum() / n * 100),
        })
    return pd.DataFrame(linhas).sort_values("entrada")


def afinidade_por_momento(seq_momento: pd.DataFrame, linhas_pedido: pd.Series,
                          entrada_por_cliente: pd.Series,
                          n_minimo: int = N_MINIMO_CELULA) -> pd.DataFrame:
    """
    As 3 tabelas pedidas pelo Daniel — mesma lógica de `afinidade_por_compra`, só
    que agrupada por MOMENTO da compra (Recente / Repetição / Reativação) em vez
    de posição (2ª/3ª/...): pra cada (entrada, momento), quais produtos aparecem
    nas compras daquele tipo. Denominador = clientes daquele (entrada, momento)
    especificamente (não o total da entrada — aqui a pergunta é "dado que essa
    pessoa comprou nesse momento, o que ela comprou", não "% de toda a entrada").
    """
    saida = []
    for (entrada, momento), g in seq_momento.groupby(["entrada", "momento"]):
        n_base = g["e_mail"].nunique()
        if n_base < n_minimo:
            continue
        # Um cliente pode ter VÁRIAS compras do mesmo momento (ex.: 2 "Repetição"
        # na vida dele) — conta CLIENTE distinto por produto, não evento, senão um
        # produto dá mais clientes do que a própria base (bug 2026-07-23, 3ª rodada).
        contagem: dict[str, set] = {}
        for email, nome in zip(g["e_mail"], g["nome"]):
            for linha in linhas_pedido.get(nome, frozenset()):
                contagem.setdefault(linha, set()).add(email)
        for produto, emails in sorted(contagem.items(), key=lambda kv: -len(kv[1])):
            n = len(emails)
            saida.append({
                "entrada": entrada, "momento": momento, "produto": produto,
                "clientes": int(n), "pct_do_momento": float(n / n_base * 100),
                "n_base": int(n_base),
            })
    out = pd.DataFrame(saida)
    if out.empty:
        return out
    return out.sort_values(["entrada", "momento", "clientes"], ascending=[True, True, False])


def rodar_tudo(salvar: bool = True):
    """Ponta a ponta: carrega, monta a jornada, calcula as saídas e (opcional) salva CSV."""
    d, deals, hist, mapa = carregar_base()
    enr, entrada_por_cliente, produto_pedido, linhas_pedido = montar_jornada(d, deals, hist, mapa)
    seq = sequenciar_compras(enr, entrada_por_cliente, produto_pedido)
    afinidade = afinidade_por_compra(seq, linhas_pedido, entrada_por_cliente)
    tempos = tempo_entre_compras(seq)

    seq_momento = classificar_momento_compras(seq)
    afinidade_momento = afinidade_por_momento(seq_momento, linhas_pedido, entrada_por_cliente)
    ltv = ltv_por_entrada(seq, entrada_por_cliente)
    taxas = taxas_por_entrada(seq, seq_momento, entrada_por_cliente)

    print(f"Clientes elegíveis (entrada >= {N_MINIMO_ENTRADA}): {len(entrada_por_cliente)}")
    print(f"Portas de entrada elegíveis ({entrada_por_cliente.nunique()}): {sorted(entrada_por_cliente.unique())}")
    print(f"Linhas na sequência de compras: {len(seq)}")

    if salvar:
        os.makedirs(PASTA_SAIDA, exist_ok=True)
        afinidade.to_csv(os.path.join(PASTA_SAIDA, "afinidade_produtos.csv"), index=False)
        tempos.to_csv(os.path.join(PASTA_SAIDA, "tempo_entre_compras.csv"), index=False)
        seq.to_csv(os.path.join(PASTA_SAIDA, "sequencia_compras_detalhe.csv"), index=False)
        afinidade_momento.to_csv(os.path.join(PASTA_SAIDA, "afinidade_por_momento.csv"), index=False)
        ltv.to_csv(os.path.join(PASTA_SAIDA, "ltv_por_entrada.csv"), index=False)
        taxas.to_csv(os.path.join(PASTA_SAIDA, "taxas_por_entrada.csv"), index=False)
        print(f"Salvo em {PASTA_SAIDA}")

    return afinidade, tempos, seq, afinidade_momento, ltv, taxas


if __name__ == "__main__":
    rodar_tudo()
