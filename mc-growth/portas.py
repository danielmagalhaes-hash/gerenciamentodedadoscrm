"""
portas.py — Portas de entrada (produto de estreia). REUSA `coortes.py` (V4).

Uma "porta de entrada" é a LINHA DE PRODUTO da 1ª compra do cliente (a estreia). A tese
(True Classic / Curso Pedrinho): janelas maiores justificam pisar mais fundo na mídia para
as portas que devolvem mais Lucro Bruto por cliente ao longo do tempo. A aba dá o argumento
para negociar CAC-teto/ROAS-alvo por porta.

NADA de verdade nova de custo ou de CAC. O dinheiro sai todo de `coortes.py`:
  - a MC de produto por deal (`mc_produto`), a safra, a idade e a régua de "novo" vêm de
    `coortes.preparar_deals_cache` — a MESMA verdade de custo das 3 telas;
  - o CAC é o **blended** do mês (mídia ÷ TODOS os novos do mês), de `coortes.calcular_coortes`;
  - a célula é o **Lucro Bruto acumulado por cliente** (antes da mídia) — o mesmo `lucro_bruto`
    da aba Cohorts (a MC já desconta a mídia; dividi-la pelo CAC contaria a mídia 2× —
    ADR 2026-07-14-ratio-contra-cac-usa-lucro-bruto).

A ÚNICA dimensão nova é `porta` por cliente. Régua parcial (Lucro Bruto sem devolução/CX/
juros/criativo). Só lê (nunca escreve). Spec `docs/specs/2026-07-15-portas-de-entrada-produto.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import cascata
import coortes
from dados import Dados

# Portas especiais (não são linha de produto).
PORTA_MULTI = "Multiprodutos"
PORTA_DESCONHECIDA = "Produto desconhecido"
PORTA_TODOS = "Todas as portas"  # o filtro "todos" da tabela principal

# Colunas de idade (apelidos "D" = mês-calendário m+x da Cohorts — spec §3.2; batem por
# construção com o triângulo de MC). A "1ª compra" é uma coluna à parte (só a estreia).
COLUNAS_IDADE: list[tuple[str, int]] = [
    ("30D (m+0)", 0),
    ("60D (m+1)", 1),
    ("90D (m+2)", 2),
    ("180D (m+5)", 5),
    ("365D (m+11)", 11),
]

N_MINIMO_PADRAO = 300

# Uma combinação de linhas (≥2) vira PORTA própria se tiver ao menos este nº de clientes de
# estreia (decisão do João, 2026-07-16; ADR 2026-07-16-combinacoes-viram-portas). Abaixo disso,
# a combinação continua no balde "Multiprodutos". Data-driven: o conjunto de portas-combo cresce
# sozinho conforme a base. Hoje promove 6 combinações (a maior: Calça Jeans 1.0 + Camiseta Minimal).
LIMIAR_COMBO_PORTA = 1000


# ---------------------------------------------------------------------------
# A ponte: pedido -> combinação de linhas, combinação -> porta, cliente -> porta
# ---------------------------------------------------------------------------
def _combo_por_pedido(dados: Dados, hist, mapa: pd.DataFrame) -> pd.Series:
    """
    `order_name` -> **combinação de linhas** de papel `porta` do pedido, texto ordenado ("A + B").
    Pedido sem nenhum item de papel `porta` fica ausente da série (vira "desconhecido" adiante).

    Regra (decisão do João, 2026-07-15): **brinde E "sem nome" são ruído** e saem antes — só os
    itens de papel `porta` contam. 1 linha → o nome da linha; ≥2 → "A + B" (a base do Multiprodutos
    e das portas-combo promovidas — ver `_porta_do_combo`).
    """
    itens = cascata.itens_por_nome(dados, hist)  # order_name, sku, quantidade (3 camadas)
    papel = mapa.set_index("sku")["papel"]
    linha = mapa.set_index("sku")["linha"]

    itens = itens.copy()
    itens["papel"] = itens["sku"].map(papel).fillna("desconhecido")
    itens["linha"] = itens["sku"].map(linha)

    so_portas = itens[itens["papel"] == "porta"]
    return so_portas.groupby("order_name")["linha"].agg(
        lambda s: " + ".join(sorted(set(s.dropna())))
    )


def _porta_do_combo(combo, promovidos: set[str]) -> str:
    """
    Combinação de linhas -> porta de entrada:
      · vazio/ausente (0 linhas `porta`)        -> "Produto desconhecido";
      · 1 linha                                  -> a própria linha;
      · ≥2 linhas e a combinação foi PROMOVIDA   -> a combinação ("A + B") vira porta própria;
      · ≥2 linhas não promovida                  -> "Multiprodutos" (a cauda).
    Promoção = a combinação tem ao menos `LIMIAR_COMBO_PORTA` clientes de estreia (decisão do João,
    2026-07-16; ADR 2026-07-16-combinacoes-viram-portas).
    """
    if not isinstance(combo, str) or combo == "":
        return PORTA_DESCONHECIDA
    if " + " not in combo:
        return combo
    return combo if combo in promovidos else PORTA_MULTI


def _estreias(enr: pd.DataFrame, com_porta: set[str]) -> pd.DataFrame:
    """
    A ESTREIA de cada cliente (1 linha por `e_mail`), indexada por `e_mail`. É o deal **mais
    antigo**; no **empate de data** (vários pedidos no mesmo dia — 0,9% dos clientes), prefere o
    que **tem produto** (≥1 linha `porta`) ao que não tem, e só então desempata pelo número.

    Por quê (correção 2026-07-16): sem essa preferência, um cliente com 4 pedidos no mesmo dia —
    3 com Camiseta, 1 sem itens — podia herdar a estreia SEM itens (o desempate era só alfabético)
    e cair em "Produto desconhecido". Agora a estreia é o pedido que de fato mostra o produto de
    entrada. `com_porta` = os `order_name` com ao menos uma linha `porta`.
    """
    e = enr.copy()
    e["_tem_porta"] = e["nome"].astype(str).isin(com_porta)
    ordem = e.sort_values(
        ["e_mail", "data_de_fechamento", "_tem_porta", "nome"],
        ascending=[True, True, False, True],   # data ↑, TEM produto primeiro, número ↑
    )
    return ordem.drop_duplicates("e_mail", keep="first").set_index("e_mail")


def _combos_promovidos(estreia: pd.DataFrame, combo_pedido: pd.Series) -> set[str]:
    """
    Combinações (≥2 linhas) com ao menos `LIMIAR_COMBO_PORTA` clientes de estreia **elegível**
    (Shipped, idade 0). Contagem **global** (toda a história fechada) — assim a porta de um cliente
    é estável em qualquer recorte de data da tela.
    """
    pode = (estreia["etapa_do_negocio"] == cascata.ETAPA_SHOPIFY) & (estreia["idade"] == 0)
    combo = estreia["nome"].map(combo_pedido).where(pode)
    multi = combo[combo.fillna("").str.contains(" + ", regex=False)]
    cnt = multi.value_counts()
    return set(cnt[cnt >= LIMIAR_COMBO_PORTA].index)


def _porta_por_cliente(estreia: pd.DataFrame, combo_pedido: pd.Series,
                       promovidos: set[str]) -> pd.Series:
    """
    `e_mail` -> porta, pela ESTREIA do cliente (ver `_estreias`). Duas travas, iguais às do CMV:
      - só deal **`Shipped`** pode casar itens (o Comercial grava número de outra numeração que
        COLIDE com pedidos antigos — `cascata.pode_casar_itens`); Comercial → "Produto desconhecido";
      - a estreia tem de ter **idade 0** (senão a 1ª compra real é anterior à base — cross-canal ou
        pré-out/2021 — e o produto de entrada é desconhecido; viés cross-canal, spec §3.1).
    A porta sai de `_porta_do_combo` sobre a combinação de linhas da estreia.
    """
    combo = estreia["nome"].map(combo_pedido)
    pode = (estreia["etapa_do_negocio"] == cascata.ETAPA_SHOPIFY) & (estreia["idade"] == 0)
    porta = combo.map(lambda c: _porta_do_combo(c, promovidos))
    return porta.where(pode, PORTA_DESCONHECIDA).fillna(PORTA_DESCONHECIDA)


# ---------------------------------------------------------------------------
# O triângulo de Lucro Bruto por cliente — ESPELHA coortes.lucro_bruto num subconjunto
# ---------------------------------------------------------------------------
def _triangulo_lb(
    enr_sub: pd.DataFrame, safras: list[str], colunas: list[int], ultimo_fechado: pd.Period,
    metrica: str = "mc_produto",
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Valor acumulado POR CLIENTE (R$/cliente) para um subconjunto de deals, reproduzindo passo a
    passo `coortes.calcular_coortes` (linhas 278-305 + máscara 366-376): N_S por safra, `metrica`
    somada por (safra, idade), ÷ N_S, cumsum na idade, e NaN onde o mês ainda não fechou.
      · `metrica="mc_produto"` (padrão) = **Lucro Bruto** acumulado (ANTES da mídia) → para o
        conjunto INTEIRO devolve exatamente `coortes.lucro_bruto`;
      · `metrica="valor"` = **Receita** acumulada (bruta, antes de qualquer custo) → devolve
        exatamente `coortes.ltv`. Nenhuma métrica desconta a mídia (o CAC entra à parte).
    """
    if enr_sub.empty:
        vazio = pd.DataFrame(np.nan, index=safras, columns=colunas)
        return vazio, pd.Series(0, index=safras, dtype="int64")

    n_clientes = enr_sub.groupby("safra")["e_mail"].nunique()
    cell_mc = enr_sub.groupby(["safra", "idade"])[metrica].sum()
    mc_pivot = cell_mc.unstack("idade").reindex(index=safras, columns=colunas).fillna(0.0)
    inc = mc_pivot.div(n_clientes.reindex(safras), axis=0)  # NaN nas safras sem cliente nesta porta
    lb = inc.cumsum(axis=1)

    # Máscara de safra fechada — idêntica ao triângulo de MC (nada de mês correndo).
    for s in safras:
        base = pd.Period(s, freq="M")
        for m in colunas:
            if base + m > ultimo_fechado:
                lb.loc[s, m] = np.nan

    return lb, n_clientes.reindex(safras).fillna(0).astype("int64")


def _lb_primeira_compra(
    enr_sub: pd.DataFrame, safras: list[str], n_clientes: pd.Series, metrica: str = "mc_produto"
) -> dict[str, float]:
    """
    Valor da 1ª compra por cliente (R$/cliente): Σ `metrica` dos deals de estreia
    (`cascata.mascara_cliente_novo` — a régua única de "novo") ÷ N_S. É a coluna "1ª compra".
    Para o conjunto inteiro devolve `coortes.lucro_bruto_primeira_compra` (`metrica="mc_produto"`)
    ou `coortes.ticket_primeira_compra` (`metrica="valor"`, a receita média do 1º pedido).
    """
    if enr_sub.empty:
        return {s: float("nan") for s in safras}
    prim = enr_sub[cascata.mascara_cliente_novo(enr_sub)]
    mc_1a = prim.groupby("safra")[metrica].sum().reindex(safras).fillna(0.0)
    out: dict[str, float] = {}
    for s in safras:
        n = int(n_clientes.get(s, 0))
        out[s] = float(mc_1a[s] / n) if n else float("nan")
    return out


# ---------------------------------------------------------------------------
# Resultado + cálculo
# ---------------------------------------------------------------------------
@dataclass
class ResultadoPortas:
    """Tudo que a aba de Portas precisa. Guarda os deals já enriquecidos + a coluna `porta`,
    para as duas tabelas (por safra e por linha) saírem de um filtro barato, sem refazer a ponte."""

    enr: pd.DataFrame                 # deals enriquecidos (mc_produto, safra, idade, real) + porta; só safras fechadas
    safras: list[str]                 # safras fechadas, em ordem cronológica (= coortes.safras)
    colunas: list[int]                # idades 0..max (= colunas de coortes.lucro_bruto)
    n_por_safra: dict[str, int]       # N_S da coorte INTEIRA (denominador do CAC blended)
    cac: dict[str, float | None]      # CAC blended por safra (= coortes.cac)
    ultimo_fechado: pd.Period
    portas: list[str]                 # portas presentes, ordenadas (linhas por tamanho; especiais no fim)
    n_por_porta: dict[str, int]       # clientes por porta (universo todo)
    frac_estimada: float
    avisos: list[str] = field(default_factory=list)

    @property
    def sem_dados(self) -> bool:
        return len(self.safras) == 0


def calcular_portas(dados: Dados, deals: pd.DataFrame, mapa: pd.DataFrame,
                    hoje=None, hist=None) -> ResultadoPortas:
    """
    Prepara os deals com a coluna `porta` (produto de estreia) e devolve o contexto para as duas
    tabelas. Reusa `coortes` para a safra/idade/CMV/CAC (uma verdade só); só acrescenta a porta.
    """
    hoje = pd.Timestamp(hoje) if hoje is not None else pd.Timestamp.today()
    ultimo_fechado = pd.Period(hoje, freq="M") - 1

    ref = coortes.calcular_coortes(dados, deals, hoje=hoje, hist=hist)
    if ref.sem_safras:
        return ResultadoPortas(
            enr=pd.DataFrame(), safras=[], colunas=[], n_por_safra={}, cac={},
            ultimo_fechado=ultimo_fechado, portas=[], n_por_porta={}, frac_estimada=0.0,
            avisos=ref.avisos or ["Sem safras fechadas para exibir."],
        )

    safras = ref.safras
    colunas = list(ref.lucro_bruto.columns)

    enr = coortes.preparar_deals_cache(dados, deals, hist=hist)
    # Só safras fechadas — o mesmo recorte que coortes.calcular_coortes faz internamente.
    enr = enr[pd.PeriodIndex(enr["safra"], freq="M") <= ultimo_fechado].copy()

    combo_pedido = _combo_por_pedido(dados, hist, mapa)
    com_porta = set(combo_pedido.index.astype(str))            # pedidos com ≥1 linha `porta`
    estreia = _estreias(enr, com_porta)                        # 1 linha/cliente (desempate: TEM produto)
    promovidos = _combos_promovidos(estreia, combo_pedido)      # combinações que viram porta própria
    porta_cliente = _porta_por_cliente(estreia, combo_pedido, promovidos)
    enr["porta"] = enr["e_mail"].map(porta_cliente).fillna(PORTA_DESCONHECIDA)

    # Ordem das portas: linhas de produto + combinações promovidas por nº de clientes (desc); as
    # especiais (Multiprodutos-cauda, Produto desconhecido) sempre no fim.
    n_por_porta = enr.groupby("porta")["e_mail"].nunique().to_dict()
    reais_ord = sorted(
        [p for p in n_por_porta if p not in (PORTA_MULTI, PORTA_DESCONHECIDA)],
        key=lambda p: n_por_porta[p], reverse=True,
    )
    especiais = [p for p in (PORTA_MULTI, PORTA_DESCONHECIDA) if p in n_por_porta]
    portas = reais_ord + especiais

    return ResultadoPortas(
        enr=enr,
        safras=safras,
        colunas=colunas,
        n_por_safra={s: int(ref.n_clientes[s]) for s in safras},
        cac=ref.cac,
        ultimo_fechado=ultimo_fechado,
        portas=portas,
        n_por_porta={p: int(n) for p, n in n_por_porta.items()},
        frac_estimada=ref.frac_estimada,
        avisos=list(ref.avisos),
    )


# ---------------------------------------------------------------------------
# As duas tabelas (números crus; a UI formata)
# ---------------------------------------------------------------------------
def tabela_por_safra(res: ResultadoPortas, porta: str,
                     metrica: str = "mc_produto") -> pd.DataFrame:
    """
    LEITURA A — uma linha por safra, obedecendo ao filtro de PRODUTO. `porta = PORTA_TODOS` →
    a coorte inteira (idêntica ao acumulado da aba Cohorts: `lucro_bruto` se `metrica="mc_produto"`,
    `ltv` se `metrica="valor"`). Colunas numéricas: `safra | n | cac | primeira | 0 | 1 | 2 | 5 | 11`
    (R$/cliente; NaN onde imatura/sem cliente).
    O CAC é sempre o BLENDED da safra (mídia ÷ TODOS os novos do mês) — nunca por produto.
    """
    sub = res.enr if porta == PORTA_TODOS else res.enr[res.enr["porta"] == porta]
    lb, n = _triangulo_lb(sub, res.safras, res.colunas, res.ultimo_fechado, metrica=metrica)
    primeira = _lb_primeira_compra(sub, res.safras, n, metrica=metrica)

    linhas = []
    for s in res.safras:
        linha = {"safra": s, "n": int(n.get(s, 0)), "cac": res.cac[s], "primeira": primeira[s]}
        for _rot, m in COLUNAS_IDADE:
            linha[m] = float(lb.loc[s, m]) if m in lb.columns else float("nan")
        linhas.append(linha)
    return pd.DataFrame(linhas)


def _cac_blended_periodo(res: ResultadoPortas, safras_range: list[str]) -> float:
    """CAC blended do período: Σ mídia dos meses ÷ Σ novos dos meses (só onde há mídia na base).
    Reconstrói a mídia do mês como cac[s]×N_S[s] — não abre nova fonte de CAC."""
    ad_total, novos_total = 0.0, 0
    for s in safras_range:
        c = res.cac[s]
        if c is None:
            continue
        n = res.n_por_safra[s]
        ad_total += c * n
        novos_total += n
    return (ad_total / novos_total) if novos_total else float("nan")


def tabela_por_linha(res: ResultadoPortas, inicio: pd.Period, fim: pd.Period,
                     n_min: int = N_MINIMO_PADRAO, metrica: str = "mc_produto") -> pd.DataFrame:
    """
    LEITURA B — uma linha por PORTA, obedecendo ao filtro de DATA. Agrega as safras cujo mês de
    estreia cai em [inicio, fim]. **Cada coluna de idade usa só as safras MADURAS para ela**
    (`safra + idade ≤ último mês fechado`) — senão as safras novas puxariam as janelas longas
    para baixo com zeros. Célula = valor acumulado por cliente do pool (Σ `metrica` até a
    idade ÷ nº de clientes elegíveis; `mc_produto` = Lucro Bruto, `valor` = Receita). Coluna com
    N elegível < `n_min` → NaN. CAC = blended do período, repetido em todas as portas (régua de
    comparação, não CAC por produto — spec §3.3).
    """
    safras_range = [s for s in res.safras if inicio <= pd.Period(s, "M") <= fim]
    cac_periodo = _cac_blended_periodo(res, safras_range)
    no_periodo = res.enr[res.enr["safra"].isin(safras_range)]

    def _pool(sub_porta: pd.DataFrame, m: int, primeira: bool) -> tuple[float, int]:
        """(valor/cliente do pool, nº de clientes ELEGÍVEIS para esta janela). O `n` é
        devolvido mesmo abaixo do mínimo, para a UI mostrar '—' (suprimido) e não '' (sem dado)."""
        eleg = [s for s in safras_range if pd.Period(s, "M") + m <= res.ultimo_fechado]
        sub = sub_porta[sub_porta["safra"].isin(eleg)]
        n = int(sub["e_mail"].nunique())
        if n < n_min:
            return float("nan"), n
        base = sub[cascata.mascara_cliente_novo(sub)] if primeira else sub[sub["idade"] <= m]
        return float(base[metrica].sum() / n), n

    linhas = []
    for porta in res.portas:
        sub_porta = no_periodo[no_periodo["porta"] == porta]
        n_porta = int(sub_porta["e_mail"].nunique())
        if n_porta == 0:
            continue
        prim_val, prim_n = _pool(sub_porta, 0, primeira=True)
        linha = {"porta": porta, "n": n_porta, "cac": cac_periodo,
                 "primeira": prim_val, "n_primeira": prim_n}
        valores = [prim_val]
        for _rot, m in COLUNAS_IDADE:
            val, n_cel = _pool(sub_porta, m, primeira=False)
            linha[m] = val
            linha[f"n_{m}"] = n_cel
            valores.append(val)
        # Porta que não passou do N mínimo em NENHUMA janela sai da tabela (pedido do João):
        # uma linha toda "—" só polui a comparação. As parciais (≥1 coluna cheia) ficam.
        if any(pd.notna(v) for v in valores):
            linhas.append(linha)

    # Ordena por nº de clientes no período (maior → menor). Os baldes catch-all
    # ("Multiprodutos", "Produto desconhecido") ficam SEMPRE no fim — não são portas
    # comparáveis, e Multiprodutos é grande o bastante para roubar o topo se entrasse no sort.
    especiais = (PORTA_MULTI, PORTA_DESCONHECIDA)
    linhas.sort(key=lambda r: (r["porta"] in especiais, -r["n"]))
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Auditoria (drill-down por cliente) — aba "A3". Só re-expõe o que já foi
# classificado (a coluna `porta` de `calcular_portas`), rotulando o PORQUÊ de
# um cliente ter caído em "Produto desconhecido". Nenhuma verdade nova de dinheiro.
# ---------------------------------------------------------------------------
# Os 4 motivos por que a estreia não virou uma porta de produto (spec 2026-07-16).
MOTIVO_COMERCIAL = "Comercial (numeração que colide)"
MOTIVO_FORA_BASE = "Estreia fora da base (cross-canal / pré-out-2021)"
MOTIVO_SEM_ITENS = "Sem itens casados na base"
MOTIVO_SO_RUIDO = "Só brinde / item sem nome"


@dataclass
class AuditoriaPortas:
    """Tudo que a aba A3 precisa para o drill-down: as estreias (1 linha/cliente, com o motivo),
    todos os deals (para a linha do tempo) e os dicionários de nome/linha/papel por SKU."""

    estreias: pd.DataFrame       # index e_mail; nome, data_de_fechamento, valor, etapa_do_negocio,
                                 # idade, safra, porta, motivo, combo, n_compras, valor_total
    enr: pd.DataFrame            # todos os deals das safras fechadas (para a linha do tempo)
    itens: pd.DataFrame          # order_name, sku, quantidade (3 camadas)
    sku2nome: dict[str, str]     # SKU -> nome do produto (de dados.itens; parcial)
    sku2linha: dict[str, str]    # SKU -> linha de produto (do mapa)
    sku2papel: dict[str, str]    # SKU -> papel (porta / brinde / desconhecido)
    portas: list[str]
    n_por_porta: dict[str, int]
    safras: list[str]
    ultimo_fechado: pd.Period
    avisos: list[str] = field(default_factory=list)

    @property
    def sem_dados(self) -> bool:
        return len(self.safras) == 0


def auditar_portas(dados: Dados, deals: pd.DataFrame, mapa: pd.DataFrame,
                   hoje=None, hist=None) -> AuditoriaPortas:
    """
    Prepara o drill-down da aba A3. Reusa `calcular_portas` (a MESMA coluna `porta` por cliente)
    e acrescenta, só para os "Produto desconhecido", o MOTIVO (por que a estreia não resolveu
    numa linha). A régua do motivo espelha `_porta_por_cliente`: Comercial (etapa ≠ Shipped) →
    idade ≠ 0 (estreia fora da base) → sem itens na base → só ruído (tem itens, nenhum é porta).
    """
    res = calcular_portas(dados, deals, mapa, hoje=hoje, hist=hist)
    if res.sem_dados:
        return AuditoriaPortas(
            estreias=pd.DataFrame(), enr=pd.DataFrame(), itens=pd.DataFrame(),
            sku2nome={}, sku2linha={}, sku2papel={}, portas=[], n_por_porta={},
            safras=[], ultimo_fechado=res.ultimo_fechado, avisos=res.avisos,
        )

    enr = res.enr
    itens = cascata.itens_por_nome(dados, hist)          # order_name, sku, quantidade
    com_itens = set(itens["order_name"].astype(str).unique())

    # Combinação de LINHAS (papel `porta`) de cada pedido — a "receita" do Multiprodutos.
    # Reusa os `itens` já lidos (não relê a base). Ex.: ("Calça Jeans 1.0", "Camiseta Minimal").
    it2 = itens[["order_name", "sku"]].copy()
    it2["papel"] = it2["sku"].map(mapa.set_index("sku")["papel"]).fillna("desconhecido")
    it2["linha"] = it2["sku"].map(mapa.set_index("sku")["linha"])
    so_portas = it2[it2["papel"] == "porta"]
    combo_por_pedido = so_portas.groupby("order_name")["linha"].agg(
        lambda s: " + ".join(sorted(set(s.dropna())))
    )
    com_porta = set(combo_por_pedido.index.astype(str))

    # Estreia = a MESMA de calcular_portas (desempate de data prefere o pedido que TEM produto),
    # para o motivo e o combo da A3 baterem com a porta da aba 4.
    estreia = _estreias(enr, com_porta)

    # Motivo — só para os desconhecidos; vazio para os resolvidos. Vetorizado (275k linhas).
    desc = estreia["porta"] == PORTA_DESCONHECIDA
    shipped = estreia["etapa_do_negocio"] == cascata.ETAPA_SHOPIFY
    idade0 = estreia["idade"] == 0
    tem_itens = estreia["nome"].astype(str).str.lstrip("#").isin(com_itens)
    motivo = pd.Series("", index=estreia.index, dtype="object")
    motivo[desc & ~shipped] = MOTIVO_COMERCIAL
    motivo[desc & shipped & ~idade0] = MOTIVO_FORA_BASE
    motivo[desc & shipped & idade0 & ~tem_itens] = MOTIVO_SEM_ITENS
    motivo[desc & shipped & idade0 & tem_itens] = MOTIVO_SO_RUIDO
    estreia["motivo"] = motivo

    # Combinação de linhas da estreia (só interessa ao Multiprodutos; "" nas demais portas).
    estreia["combo"] = estreia["nome"].astype(str).str.lstrip("#").map(combo_por_pedido).fillna("")

    # nº de compras e valor total por cliente (todas as compras, para a lista).
    agg = enr.groupby("e_mail").agg(n_compras=("nome", "size"), valor_total=("valor", "sum"))
    estreia = estreia.join(agg)

    # Nome do produto por SKU (de dados.itens; parcial — SKUs antigos podem faltar).
    sku2nome: dict[str, str] = {}
    if "descricao" in dados.itens.columns:
        dsc = dados.itens[["sku", "descricao"]].dropna()
        dsc = dsc[dsc["descricao"].astype(str).str.strip() != ""]
        sku2nome = dsc.drop_duplicates("sku").set_index("sku")["descricao"].astype(str).to_dict()

    return AuditoriaPortas(
        estreias=estreia,
        enr=enr,
        itens=itens,
        sku2nome=sku2nome,
        sku2linha=mapa.set_index("sku")["linha"].to_dict(),
        sku2papel=mapa.set_index("sku")["papel"].to_dict(),
        portas=res.portas,
        n_por_porta=res.n_por_porta,
        safras=res.safras,
        ultimo_fechado=res.ultimo_fechado,
        avisos=list(res.avisos),
    )
