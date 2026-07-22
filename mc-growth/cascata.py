"""
cascata.py — regras de cálculo da Margem de Contribuição (TOCA DINHEIRO).

Recebe os dados já limpos (dados.py) e um período, e devolve a cascata tipo DRE
(de Vendas até a MC), os 5 cartões e os avisos. Toda regra aqui espelha
PRODUCT.md seção 6 e o spec seção 4 (R1..R12). Nunca mude um número sem rastrear
a coluna de origem.

Fronteira importante: a aba `Parametros` ainda NÃO existe na planilha
(ARCHITECTURE.md 3.0). Por isso os 10 percentuais moram aqui, na constante
PARAMETROS. Quando o João criar a aba, é só trocar a fonte por leitura da planilha.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from dados import Dados

# ---------------------------------------------------------------------------
# Parâmetros (%) — provisoriamente embutidos. Valores: PRODUCT.md seção 6.
# Grafia da chave conforme ARCHITECTURE.md 3.0 (aba Parametros futura).
# Cada percentual incide sobre a linha Vendas.
# ---------------------------------------------------------------------------
# Imposto sobre o investimento em FB Ads. O gasto real é o valor puro "embrutecido"
# por este imposto: fb_real = fb_investimento / (1 - IMPOSTO_FB_ADS). ADR 2026-07-03.
IMPOSTO_FB_ADS: float = 0.1215

# [CMV estimado 2026-07-14, 2ª sessão] Onde o pedido NÃO casa com a janela de itens (histórico
# + vendas do Comercial), não há custo real. Nesses pedidos o CMV é estimado em 30% da receita,
# e as deduções/custos variáveis seguem as fórmulas de sempre (sobre a receita inteira).
# Rastro do número: nos meses com itens reais, CMV/Vendas = 29,0% (mai/2026) e 28,8% (jun/2026)
# → 30% é o real levemente arredondado para cima (conservador). Substitui a "margem estimada de
# 25%" (que era um chute pessimista: implicava margem de produto de 25% onde a real é ~43%).
# Margem de produto implícita: 1 − 30,44% (deduções+custos, atualizados 2026-07-22) − 30% =
# 39,56% da receita. (Era 42,5% com a soma de 27,49% até 2026-07-22.)
# Specs `2026-07-14-interface-menu-cascata-cmv-30` e `2026-07-22-parametros-dre`.
CMV_ESTIMADO_FRACAO: float = 0.30

# A etapa do HubSpot que corresponde a um pedido Shopify de verdade — o único deal que pode
# procurar os próprios itens pelo número do pedido (ver `pode_casar_itens`).
ETAPA_SHOPIFY: str = "Shipped"

# Percentuais da DRE atualizados pelo Financeiro em 2026-07-22 (spec 2026-07-22-parametros-dre).
# `embalagem` (0,57) e `outras_deducoes` (0,00) não vieram na lista → mantidos (embalagem
# CONFIRMADA pelo João em 2026-07-22).
PARAMETROS: dict[str, float] = {
    "devolucoes": 3.32,
    "chargebacks": 0.15,
    "pis_cofins_cbs": 4.74,
    "icms_ibs": 13.73,
    "outras_deducoes": 0.0,
    "frete": 5.02,
    "embalagem": 0.57,
    "gateways": 1.37,
    "plataforma": 0.44,
    "antecipacao": 1.10,
}

# Exclusões de negócio (ADR 2026-07-02-excluir-anjosfrach): pedidos que contêm
# QUALQUER SKU com um destes prefixos saem INTEIROS da análise (Vendas, Pedidos e CMV).
PREFIXOS_SKU_EXCLUIDOS: tuple[str, ...] = ("CamiseAnjosFrach",)

# Pedidos específicos removidos por decisão pontual (mesmo ADR). Por `order_name`
# (número humano). Ex.: #501777 = pedido de receita R$0 (reposição/cortesia).
PEDIDOS_EXCLUIDOS_NOME: tuple[str, ...] = ("501777",)

# Paliativo de dobra de kit APOSENTADO em 2026-07-09: a explosão de kit foi corrigida
# na fonte (informado pelo João — a base de Itens não duplica mais o SKU virtual do kit
# junto dos componentes reais). O antigo `SKUS_KIT_VIRTUAL` removia do CMV o código de
# pacote "8301001172"; com a fonte corrigida, continuar removendo viraria subtrair custo
# legítimo → MC inflada. Por isso o filtro saiu. Se a dobra reaparecer, reintroduzir aqui.

# Grupo "Deduções": entra logo após Vendas (ordem do DRE — spec 2026-07-14).
_DEDUCOES = [
    ("pis_cofins_cbs", "PIS/COFINS + CBS"),
    ("icms_ibs", "ICMS + IBS"),
    ("devolucoes", "Devoluções"),
    ("chargebacks", "Chargebacks"),
    ("outras_deducoes", "Outras Deduções"),
]
# Grupo "Cost of Delivery": o CMV encabeça, seguido dos custos variáveis em %.
_CUSTOS_VARIAVEIS = [
    ("frete", "Frete"),
    ("embalagem", "Embalagem"),
    ("gateways", "Taxa de Gateways"),
    ("plataforma", "Valor plataforma"),
    ("antecipacao", "Despesas de antecipação"),
]


@dataclass
class LinhaDRE:
    """Uma linha da cascata. `valor` já vem com sinal (deduções/custos negativos)."""

    rotulo: str
    valor: float
    # "topo" | "grupo" (subtotal Deduções / Cost of Delivery) | "deducao" | "cmv" | "custo"
    # | "subtotal" (Lucro Bruto) | "midia" | "resultado" (MC)
    tipo: str


# ---------------------------------------------------------------------------
# A FÁBRICA DE CASCATA — a única forma do DRE no projeto (spec 2026-07-14).
# Todas as telas (Geral, Aquisição e os 3 blocos da auditoria por safra) montam a
# cascata AQUI. Antes o DRE era remontado à mão em 6 lugares e divergia a cada mudança.
#
# Os dois subtotais de grupo ("Deduções", "Cost of Delivery") são APRESENTAÇÃO: somas de
# linhas que já existem. O Lucro Bruto e a MC continuam saindo da conta, não da tabela.
# ---------------------------------------------------------------------------
def montar_cascata(
    vendas: float,
    cmv: float,
    ad_spend: float,
    parametros: dict[str, float] = PARAMETROS,
    *,
    rotulo_vendas: str = "Vendas",
    rotulo_cmv: str = "CMV",
    rotulo_lucro: str = "Lucro Bruto",
    rotulo_midia: str = "Mídia Paga",
    rotulo_mc: str = "Margem de Contribuição",
    com_midia: bool = True,
    cmv_estimado: float = 0.0,
) -> tuple[list[LinhaDRE], float, float]:
    """
    Monta a cascata padrão e devolve `(linhas, lucro_bruto, mc)`.

    Vendas → (−) Deduções [5 linhas] → (−) Cost of Delivery [CMV + 5 linhas] → (=) Lucro
    Bruto → (−) Mídia Paga → (=) Margem de Contribuição.

    - Deduções e custos variáveis (%) incidem sobre a **receita inteira** (`vendas`).
    - `cmv` é o CMV TOTAL da tela (real item a item + a parte estimada em 30%, quando houver).
      `cmv_estimado` é só quanto dele veio da estimativa — usado para marcar a linha com ⚠️.
    - `com_midia=False` (ex.: cascata de recompra, que não carrega mídia): não sai a linha de
      mídia nem o subtotal de Lucro Bruto — o resultado É o lucro bruto.
    """

    def valor_pct(chave: str) -> float:
        return vendas * parametros.get(chave, 0.0) / 100.0

    deducoes = [(rotulo, -valor_pct(chave)) for chave, rotulo in _DEDUCOES]
    custos = [(rotulo, -valor_pct(chave)) for chave, rotulo in _CUSTOS_VARIAVEIS]
    total_deducoes = sum(v for _r, v in deducoes)
    total_delivery = -cmv + sum(v for _r, v in custos)

    lucro_bruto = vendas + total_deducoes + total_delivery
    mc = lucro_bruto - ad_spend if com_midia else lucro_bruto

    # A linha do CMV avisa quando parte dela é estimada (nunca finge precisão que não tem).
    rot_cmv = rotulo_cmv
    if cmv_estimado > 0 and cmv > 0:
        fatia = cmv_estimado / cmv * 100
        rot_cmv = f"{rotulo_cmv} ⚠️ ({fatia:.0f}% estimado a {CMV_ESTIMADO_FRACAO * 100:.0f}%)"

    linhas: list[LinhaDRE] = [LinhaDRE(rotulo_vendas, vendas, "topo")]
    linhas.append(LinhaDRE("Deduções", total_deducoes, "grupo"))
    linhas += [LinhaDRE(rotulo, valor, "deducao") for rotulo, valor in deducoes]
    linhas.append(LinhaDRE("Cost of Delivery", total_delivery, "grupo"))
    linhas.append(LinhaDRE(rot_cmv, -cmv, "cmv"))
    linhas += [LinhaDRE(rotulo, valor, "custo") for rotulo, valor in custos]
    if com_midia:
        linhas.append(LinhaDRE(rotulo_lucro, lucro_bruto, "subtotal"))
        linhas.append(LinhaDRE(rotulo_midia, -ad_spend, "midia"))
    linhas.append(LinhaDRE(rotulo_mc, mc, "resultado"))
    return linhas, lucro_bruto, mc


@dataclass
class Resultado:
    """Tudo que o painel precisa desenhar para um período."""

    # Cartões
    vendas: float
    ad_spend: float
    roas: float | None         # ROAS Shopify = Vendas ÷ Ad Spend. None quando não há mídia
    ticket_medio: float | None  # None quando não há pedidos
    pedidos: int
    # Cascata
    cmv: float
    lucro_bruto: float
    mc: float
    linhas: list[LinhaDRE]
    # Alertas / guardas defensivas
    unidades_sem_custo: float = 0.0
    skus_sem_custo: int = 0
    skus_faltantes: list[tuple[str, float]] = field(default_factory=list)  # (sku, unidades)
    pedidos_excluidos: int = 0  # pedidos AnjosFrach removidos no período (ADR 2026-07-02)
    avisos: list[str] = field(default_factory=list)
    # [rebase HubSpot 2026-07-14] parte sem itens (histórico + Comercial): CMV estimado em 30%
    rotulo_confianca: str = "real"   # "real" | "estimada" | "mista"
    vendas_estimada: float = 0.0     # Σ valor dos deals sem itens (CMV não pôde ser real)
    pedidos_estimados: int = 0
    cmv_estimado: float = 0.0        # quanto do CMV veio da estimativa de 30% (para marcar ⚠️)

    @property
    def sem_dados(self) -> bool:
        """Período sem nenhum movimento (vendas, pedidos e mídia zerados)."""
        return self.pedidos == 0 and self.vendas == 0 and self.ad_spend == 0


def _no_periodo(df: pd.DataFrame, inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DataFrame:
    """Filtra pela coluna `data` no intervalo [inicio, fim], ambos inclusive."""
    dentro = df["data"].notna() & (df["data"] >= inicio) & (df["data"] <= fim)
    return df[dentro]


def _pedidos_excluidos(itens: pd.DataFrame) -> set:
    """order_id de todo pedido que contém algum SKU dos prefixos excluídos (ADR 2026-07-02)."""
    if not PREFIXOS_SKU_EXCLUIDOS:
        return set()
    tem_sku_excluido = itens["sku"].str.startswith(PREFIXOS_SKU_EXCLUIDOS, na=False)
    return set(itens.loc[tem_sku_excluido, "order_id"])


def _recorte_pedidos(dados: Dados, inicio, fim):
    """
    O recorte de pedidos/itens do período — a MESMA base que o painel e a auditoria usam.
    Aplica exclusões (AnjosFrach + pontuais) e a regra "Vendas é a fonte de verdade".

    A aba Vendas decide quais pedidos existem (só Shopify, só PAID). A aba Itens tem
    pedidos de OUTROS canais que NÃO entram — por isso os itens são recortados pelos
    order_id presentes na Vendas do período. Devolve (vendas_p, itens_p, midia_p, nº excluídos).
    """
    inicio = pd.Timestamp(inicio).normalize()
    fim = pd.Timestamp(fim).normalize()

    midia_p = _no_periodo(dados.midia, inicio, fim)
    excluidos = _pedidos_excluidos(dados.itens)
    vendas_bruto = _no_periodo(dados.vendas, inicio, fim)
    a_excluir = (
        vendas_bruto["order_id"].isin(excluidos)
        | vendas_bruto["order_name"].isin(PEDIDOS_EXCLUIDOS_NOME)
    )
    vendas_p = vendas_bruto[~a_excluir]
    itens_p = dados.itens[dados.itens["order_id"].isin(vendas_p["order_id"].unique())]
    return vendas_p, itens_p, midia_p, int(a_excluir.sum())


# ---------------------------------------------------------------------------
# Receita de custo — a ÚNICA verdade de CMV do projeto (uma só junção Itens×Custos).
# O CMV do painel, da aquisição, da auditoria E da coorte (V4) sai toda daqui, para
# que nunca discordem sobre o custo de um pedido — inclusive as correções locais do
# João (custos_extra.csv já vêm embutidas em `dados.custos`). ADR 2026-07-10-v4-arquitetura.
# ---------------------------------------------------------------------------
def juntar_custos(itens: pd.DataFrame, custos: pd.DataFrame) -> pd.DataFrame:
    """
    Junta Itens × Custos pelo `sku` (left join) e acrescenta 3 colunas:
      - `valor_custo`: custo unitário do SKU (NaN se o SKU não tem custo cadastrado);
      - `sem_custo`  : True quando falta custo (custo 0 = faltando, não grátis — R5);
      - `custo_linha`: `valor_custo × quantidade`, com o faltante virando 0 (não some).
    O CMV de um recorte é a soma de `custo_linha`; itens sem custo entram como 0 e
    aparecem no alerta. Inclui brindes (têm custo). Não filtra período — recorte é do chamador.
    """
    juncao = itens.merge(custos, on="sku", how="left")
    juncao["sem_custo"] = juncao["valor_custo"].isna()
    juncao["custo_linha"] = (juncao["valor_custo"] * juncao["quantidade"]).fillna(0.0)
    return juncao


def cmv_por_pedido(itens: pd.DataFrame, custos: pd.DataFrame) -> pd.DataFrame:
    """
    CMV agregado por `order_id` (mesma receita de custo do painel — `juntar_custos`).
    Devolve um DataFrame indexado por `order_id` com: `cmv`, `n_itens`, `n_sem_custo`.
    É o helper que a coorte (V4) usa para o CMV real de cada pedido casado (ponte pelo
    número do pedido), garantindo que o custo bata com a Auditoria/painel.
    """
    juncao = juntar_custos(itens, custos)
    return juncao.groupby("order_id").agg(
        cmv=("custo_linha", "sum"),
        n_itens=("sku", "count"),
        n_sem_custo=("sem_custo", "sum"),
    )


# ---------------------------------------------------------------------------
# A janela de itens — a fronteira entre o CMV real e o estimado (30%).
# Dentro dela o pedido casa com a aba Vendas/Itens e tem custo item a item; fora, não há
# itens (histórico + vendas do Comercial) e o CMV é estimado. ADR 2026-07-14.
# ---------------------------------------------------------------------------
def _janela_vendas(dados: Dados):
    """(vmin, vmax) das datas da aba Vendas — a fronteira do que é 'real'."""
    d = dados.vendas["data"].dropna()
    if d.empty:
        return None, None
    return d.min().normalize(), d.max().normalize()


# ---------------------------------------------------------------------------
# RESOLUÇÃO DE ITENS EM 3 CAMADAS (spec 2026-07-14 `cmv-real-historico-3-camadas`).
# De onde saem os itens de um pedido, nesta ordem:
#   1ª  base histórica local (`bases/itens_historico.csv`) — 2021-10 → data do export;
#   2ª  aba `Itens` da planilha (ao vivo) — só para os pedidos que o export ainda não viu;
#   3ª  nenhuma  → CMV estimado em 30% da receita (quem aplica são os chamadores).
# A 2ª camada NÃO é redundante: o export é uma FOTO; o pedido de amanhã só existe na planilha.
# Tudo aqui só decide QUAIS linhas de item entram — o custo continua saindo de `juntar_custos`
# (a única verdade de custo do projeto, CLAUDE.md §11).
# ---------------------------------------------------------------------------
COLUNAS_ITEM = ["order_name", "data", "sku", "quantidade"]


def itens_por_nome(dados: Dados, hist=None) -> pd.DataFrame:
    """
    Os itens de todo pedido, indexados pelo **número humano** do pedido (`order_name`) — a
    chave que o HubSpot também usa. Junta as duas camadas: o histórico manda; a planilha só
    entra para os pedidos que o histórico não tem (os recentes demais para o export).

    Na camada da planilha vale a regra de sempre: a aba `Vendas` é a fonte de verdade dos
    pedidos (a `Itens` traz outros canais) — item sem pedido na Vendas não entra (ADR 2026-07-02).
    """
    id2name = dados.vendas.drop_duplicates("order_id").set_index("order_id")["order_name"]
    planilha = dados.itens.copy()
    planilha["order_name"] = planilha["order_id"].map(id2name)
    planilha = planilha.loc[planilha["order_name"].notna(), COLUNAS_ITEM]

    if hist is None or hist.empty:
        return planilha.reset_index(drop=True)

    ja_no_historico = planilha["order_name"].isin(set(hist["order_name"]))
    return pd.concat(
        [hist[COLUNAS_ITEM], planilha[~ja_no_historico]], ignore_index=True
    )


def pode_casar_itens(deals) -> pd.Series:
    """
    Quais deals têm o **direito** de procurar itens pelo número do pedido: só os `Shipped`
    (os pedidos Shopify). O `Negócio Fechado - Comercial` **nunca** casa — é estimado sempre
    (PRODUCT.md §3), e é uma trava de dinheiro, não burocracia:

    o Comercial grava no campo `nome` um número de **outra numeração**, que COLIDE com números
    de pedido Shopify antigos. Medido em 2026-07-14: 224 deals Comerciais casariam por número
    com itens de pedidos **~92 dias mais velhos** (mediana) — em junho/2026 seriam 37 deals
    herdando o CMV de pedidos de janeiro. Os `Shipped`, esses, casam com o item do MESMO dia
    (mediana 0 dias; 99,9% dentro de ±2 dias). Sem esta trava, o painel colaria custo errado
    em pedido errado — e em silêncio.
    """
    return deals["etapa_do_negocio"] == ETAPA_SHOPIFY


def nomes_com_cmv_real(dados: Dados, itens_nome: pd.DataFrame) -> set:
    """
    Os pedidos cujo CMV é **real** (não estimado): os que têm itens resolvidos **mais** os que
    estão na aba `Vendas`.

    O segundo grupo parece estranho, mas preserva o comportamento de sempre: um punhado de
    pedidos da janela atual existe na `Vendas` e **não tem itens** (resíduo conhecido, ~0,78%).
    Eles sempre entraram como CMV **zero** (real), não como estimados — mudar isso agora moveria
    o número que o João valida hoje. Fora da janela, quem não tem item cai no estimado (30%).
    """
    return set(itens_nome["order_name"].dropna()) | set(dados.vendas["order_name"].dropna())


def _nomes_excluidos(dados: Dados, itens_nome: pd.DataFrame | None = None) -> set:
    """
    Números de pedido fora da análise (AnjosFrach + pontuais, ADR 2026-07-02), varridos na
    **união** das duas bases de itens — antes só a planilha era varrida, então um AnjosFrach
    antigo passaria batido. Medido em 2026-07-14: os 29 pedidos AnjosFrach são todos de
    2026-05/06 e a planilha já os excluía — impacto hoje: **zero**. É blindagem, não mudança.
    """
    ids = _pedidos_excluidos(dados.itens)
    nomes = set(dados.vendas.loc[dados.vendas["order_id"].isin(ids), "order_name"])
    if itens_nome is not None and PREFIXOS_SKU_EXCLUIDOS:
        tem_excluido = itens_nome["sku"].str.startswith(PREFIXOS_SKU_EXCLUIDOS, na=False)
        nomes |= set(itens_nome.loc[tem_excluido, "order_name"])
    return nomes | set(PEDIDOS_EXCLUIDOS_NOME)


def cmv_por_nome(dados: Dados, hist=None, itens_nome: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    CMV real agregado por **número do pedido** (`order_name`) — o par do `cmv_por_pedido`
    (que é por `order_id`), agora sobre as 3 camadas. Índice: `order_name`; colunas: `cmv`,
    `n_itens`, `n_sem_custo`. Passa por `juntar_custos`: mesma verdade de custo do painel.
    """
    if itens_nome is None:
        itens_nome = itens_por_nome(dados, hist)
    juncao = juntar_custos(itens_nome, dados.custos)
    return juncao.groupby("order_name").agg(
        cmv=("custo_linha", "sum"),
        n_itens=("sku", "count"),
        n_sem_custo=("sem_custo", "sum"),
    )


# ---------------------------------------------------------------------------
# Núcleo DEALS-BASED (unificação HubSpot 2026-07-14): Vendas = Σ `valor` por
# data_de_fechamento; CMV REAL via ponte (nome→pedido→Itens→Custos) na janela de itens,
# senão CMV estimado em 30% da receita. Bate com o filtro direto da base. ADR 2026-07-14 §5-bis.
# ---------------------------------------------------------------------------
def mascara_cliente_novo(deals) -> pd.Series:
    """
    Quais deals são de **cliente novo** — a régua ÚNICA do projeto (decisão do João, 2026-07-14).
    TODA tela que separa novo × recompra chama esta função. Nunca escrever a regra de novo.

    Regra: o **carimbo `tipo_de_venda` do HubSpot** (`Primeira Compra`) **E** o pedido cai no
    **mês em que o cliente estreou** (`data_primeira_compra`) — a idade 0 da coorte.

    Por que o segundo pedaço: o HubSpot **se contradiz**. Em junho/2026, 5 pedidos vinham
    carimbados `Primeira Compra` num mês diferente do mês de estreia do próprio cliente. Com só
    o carimbo, a aba Aquisição (que olha o PERÍODO) e a coorte (que olha a TURMA) nunca fechavam
    — divergiam em R$ 3.628. **Quando os dois campos brigam, a data de estreia manda**: assim as
    telas batem ao centavo e a coorte continua cross-canal.

    Ressalva registrada (não corrigimos — é da fonte): o carimbo também erra para o outro lado —
    59 pedidos que eram a 1ª compra do cliente vinham marcados `Recompra`, e o mesmo cliente
    aparece carimbado "Primeira Compra" 2× no mesmo mês (57 casos em junho).
    """
    carimbado = deals["tipo_de_venda"] == CLIENTE_NOVO
    mes_deal = deals["data_de_fechamento"].dt.to_period("M")
    mes_estreia = deals["data_primeira_compra"].dt.to_period("M")
    return carimbado & (mes_deal == mes_estreia)


def _cascata_de_deals(dados: Dados, deals, inicio, fim, novos_only: bool = False, hist=None) -> dict:
    """Agrega os deals do período (por fechamento) para montar a cascata: Σvalor, CMV real
    (parte casada) e Σvalor não-casado (parte estimada). Reusa a receita de custo do painel.

    [2026-07-14] O CMV real vem das 3 camadas (`itens_por_nome`): base histórica → planilha →
    estimado. Antes, só a janela da planilha tinha custo real; agora a história inteira tem."""
    inicio = pd.Timestamp(inicio).normalize()
    fim = pd.Timestamp(fim).normalize()
    if novos_only:
        deals = deals[mascara_cliente_novo(deals)]  # régua única de "novo": o carimbo do HubSpot
    dp = deals[(deals["data_de_fechamento"] >= inicio) & (deals["data_de_fechamento"] <= fim)].copy()

    itens_nome = itens_por_nome(dados, hist)

    # Exclusões de negócio (AnjosFrach + pontuais) por número de pedido (ADR 2026-07-02).
    antes = len(dp)
    dp = dp[~dp["nome"].isin(_nomes_excluidos(dados, itens_nome))]
    pedidos_excluidos = antes - len(dp)

    # Casado = deal `Shipped` (só ele pode casar — `pode_casar_itens`) cujo pedido tem CMV real
    # (itens resolvidos, ou está na Vendas sem itens = CMV 0). O Comercial fica sempre estimado.
    reais = nomes_com_cmv_real(dados, itens_nome)
    matched = pode_casar_itens(dp) & dp["nome"].isin(reais)
    dp["real"] = matched

    vendas = float(dp["valor"].fillna(0.0).sum())
    pedidos = int(len(dp))
    vendas_matched = float(dp.loc[matched, "valor"].fillna(0.0).sum())
    vendas_unmatched = vendas - vendas_matched

    # CMV REAL dos pedidos casados no período (mesma receita de custo do painel).
    nomes = set(dp.loc[matched, "nome"].dropna())
    itens_casados = itens_nome[itens_nome["order_name"].isin(nomes)]
    juncao = juntar_custos(itens_casados, dados.custos)
    cmv = float(juncao["custo_linha"].sum())
    sem_custo = juncao[juncao["sem_custo"]]
    unidades_sem_custo = float(sem_custo["quantidade"].sum())
    skus_sem_custo = int(sem_custo.loc[sem_custo["sku"].str.strip() != "", "sku"].nunique())
    faltantes = (
        sem_custo[sem_custo["sku"].str.strip() != ""].groupby("sku")["quantidade"].sum()
        .sort_values(ascending=False)
    )
    skus_faltantes = [(sku, float(un)) for sku, un in faltantes.items()]

    return {
        "vendas": vendas, "pedidos": pedidos,
        "vendas_matched": vendas_matched, "vendas_unmatched": vendas_unmatched,
        "cmv": cmv, "unidades_sem_custo": unidades_sem_custo, "skus_sem_custo": skus_sem_custo,
        "skus_faltantes": skus_faltantes, "pedidos_excluidos": pedidos_excluidos, "df": dp,
    }


def _ad_spend_periodo(dados: Dados, inicio, fim) -> float:
    """Ad Spend do período (mídia da aba, gross-up do FB) — igual ao painel."""
    midia_p = _no_periodo(dados.midia, pd.Timestamp(inicio).normalize(), pd.Timestamp(fim).normalize())
    fb_real = midia_p["fb_investimento"].sum() / (1 - IMPOSTO_FB_ADS)
    return float(
        fb_real
        + midia_p["google_investimento"].sum()
        + midia_p["google_institucional_investimento"].sum()
    )


def _rotulo(vendas_matched: float, vendas_unmatched: float) -> str:
    if vendas_unmatched > 0 and vendas_matched > 0:
        return "mista"
    if vendas_unmatched > 0:
        return "estimada"
    return "real"


def _calcular_por_deals(dados: Dados, deals, inicio, fim, parametros, hist=None) -> Resultado:
    """Painel geral deals-based: Vendas = Σ`valor`; CMV real (item a item) nos pedidos casados
    + 30% da receita sem itens; deduções sobre a receita inteira. ADR 2026-07-14 (+ CMV 30%)."""
    agg = _cascata_de_deals(dados, deals, inicio, fim, hist=hist)
    vendas, pedidos = agg["vendas"], agg["pedidos"]
    vm, vu = agg["vendas_matched"], agg["vendas_unmatched"]
    ad_spend = _ad_spend_periodo(dados, inicio, fim)

    cmv_estimado = CMV_ESTIMADO_FRACAO * vu   # pedidos sem itens: custo estimado (spec 2026-07-14)
    cmv = agg["cmv"] + cmv_estimado

    linhas, lucro_bruto, mc = montar_cascata(
        vendas, cmv, ad_spend, parametros, cmv_estimado=cmv_estimado
    )
    ticket = vendas / pedidos if pedidos > 0 else None
    roas = vendas / ad_spend if ad_spend > 0 else None

    return Resultado(
        vendas=vendas, ad_spend=ad_spend, roas=roas, ticket_medio=ticket, pedidos=pedidos,
        cmv=cmv, lucro_bruto=lucro_bruto, mc=mc, linhas=linhas,
        unidades_sem_custo=agg["unidades_sem_custo"], skus_sem_custo=agg["skus_sem_custo"],
        skus_faltantes=agg["skus_faltantes"], pedidos_excluidos=agg["pedidos_excluidos"],
        avisos=[], rotulo_confianca=_rotulo(vm, vu), vendas_estimada=vu,
        pedidos_estimados=int((~agg["df"]["real"]).sum()),
        cmv_estimado=cmv_estimado,
    )


def _calcular_aquisicao_por_deals(dados: Dados, deals, inicio, fim, parametros, hist=None) -> "ResultadoAquisicao":
    """Aquisição deals-based: **novo = carimbo `tipo_de_venda` do HubSpot** (`mascara_cliente_novo`
    — a MESMA régua do bloco de novos da coorte). Vendas-novos = Σ`valor`. CMV real (3 camadas);
    estimado (30%) onde não há itens. Mídia INTEIRA. ADR 2026-07-14 + spec CMV 30%."""
    agg = _cascata_de_deals(dados, deals, inicio, fim, novos_only=True, hist=hist)
    vendas_novos, pedidos_novos = agg["vendas"], agg["pedidos"]
    vm, vu = agg["vendas_matched"], agg["vendas_unmatched"]
    ad_spend = _ad_spend_periodo(dados, inicio, fim)

    cmv_estimado = CMV_ESTIMADO_FRACAO * vu
    cmv_novos = agg["cmv"] + cmv_estimado

    linhas, lucro_bruto_novos, mc_novos = montar_cascata(
        vendas_novos, cmv_novos, ad_spend, parametros,
        rotulo_vendas="Vendas-novos", rotulo_cmv="CMV-novos",
        rotulo_lucro="Lucro Bruto-novos", rotulo_midia="Mídia Paga (inteira)",
        rotulo_mc="MC-novos", cmv_estimado=cmv_estimado,
    )
    cac = ad_spend / pedidos_novos if pedidos_novos > 0 else None
    aroas = vendas_novos / ad_spend if ad_spend > 0 else None
    ticket = vendas_novos / pedidos_novos if pedidos_novos > 0 else None

    # Contagens das 3 faixas (pelo carimbo, no período, com as mesmas exclusões). Deal sem
    # carimbo (ou com rótulo inesperado) cai em "sem classificação" — não vira novo nem recompra.
    ini = pd.Timestamp(inicio).normalize(); fi = pd.Timestamp(fim).normalize()
    excl_names = _nomes_excluidos(dados, itens_por_nome(dados, hist))
    dp_all = deals[(deals["data_de_fechamento"] >= ini) & (deals["data_de_fechamento"] <= fi)]
    dp_all = dp_all[~dp_all["nome"].isin(excl_names)]
    pedidos_total = int(len(dp_all))
    pedidos_recompra = int((dp_all["tipo_de_venda"] == CLIENTE_RECOMPRA).sum())
    pedidos_sem_classif = pedidos_total - pedidos_novos - pedidos_recompra

    return ResultadoAquisicao(
        mc_novos=mc_novos, vendas_novos=vendas_novos, pedidos_novos=pedidos_novos,
        cac=cac, aroas=aroas, ticket_medio=ticket,
        cmv_novos=cmv_novos, lucro_bruto_novos=lucro_bruto_novos,
        ad_spend=ad_spend, linhas=linhas, pedidos_total=pedidos_total,
        pedidos_recompra=pedidos_recompra, pedidos_sem_classificacao=pedidos_sem_classif,
        amarra=True, unidades_sem_custo=agg["unidades_sem_custo"], skus_sem_custo=agg["skus_sem_custo"],
        avisos=[], rotulo_confianca=_rotulo(vm, vu), vendas_novos_estimada=vu,
        pedidos_novos_estimados=int((~agg["df"]["real"]).sum()),
        cmv_estimado=cmv_estimado,
    )


def calcular(
    dados: Dados,
    inicio,
    fim,
    parametros: dict[str, float] = PARAMETROS,
    deals=None,
    hist=None,
) -> Resultado:
    """
    Monta a cascata da MC para o período [inicio, fim].

    `inicio`/`fim` podem ser date ou Timestamp; são normalizados para o dia todo.

    `deals` (opcional, HubSpot — rebase 2026-07-14): destrava o **histórico**. Sem ele, o
    resultado é idêntico ao de sempre (só a janela de itens da planilha). Com ele, a parte do
    período que cai **fora** da janela de itens entra com o **CMV estimado em 30% da receita**
    (as deduções/custos % incidem normal) — logo margem de produto de 42,5% do `valor`.

    `hist` (opcional, base histórica de itens — spec 2026-07-14 `cmv-real-historico-3-camadas`):
    dá **CMV real (item a item) à história inteira** (2021-10 → hoje). Sem ele, só a janela da
    planilha tem custo real e o resto fica no estimado de 30% (comportamento anterior — é a
    degradação prevista quando o arquivo não existe).

    [Unificação 2026-07-14] Com `deals`, o motor é **deals-based** (Vendas = Σ`valor` por data de
    fechamento; CMV real item a item, estimado a 30% onde não há itens) — bate com o filtro direto
    da base. Sem `deals` (CSV ausente), cai no motor antigo (planilha/`net_revenue`), como fallback.
    """
    if deals is not None:
        return _calcular_por_deals(dados, deals, inicio, fim, parametros, hist=hist)

    vendas_p, itens_p, midia_p, pedidos_excluidos_periodo = _recorte_pedidos(dados, inicio, fim)

    avisos: list[str] = []

    # --- Cartões base -------------------------------------------------------
    # R2: Vendas = Σ net_revenue. R3: Pedidos = order_id distintos.
    vendas = float(vendas_p["net_revenue"].sum())
    pedidos = int(vendas_p["order_id"].nunique())

    # Guarda defensiva (ARCHITECTURE.md 6): Base 1 deveria ter 1 linha por pedido.
    if len(vendas_p) != pedidos:
        avisos.append(
            f"A aba Vendas tem {len(vendas_p)} linhas para {pedidos} pedidos distintos "
            "no período (possível duplicidade). Vendas somou todas as linhas; "
            "Pedidos usou os distintos."
        )

    # R4: Ticket médio = Vendas ÷ Pedidos (None se não há pedidos).
    ticket_medio = vendas / pedidos if pedidos > 0 else None

    # --- CMV (R5, R11) ------------------------------------------------------
    # itens_p já vem restrito aos pedidos que existem na Vendas do período (só Shopify).
    # Mesma receita de custo do painel/auditoria/coorte (juntar_custos): CMV = Σ custo_linha.
    juncao = juntar_custos(itens_p, dados.custos)
    cmv = float(juncao["custo_linha"].sum())

    sem_custo = juncao[juncao["sem_custo"]]
    unidades_sem_custo = float(sem_custo["quantidade"].sum())
    skus_sem_custo = int(sem_custo["sku"].nunique())

    # Lista (sku, unidades) dos faltantes, para o editor de custos do painel.
    # SKU em branco fica de fora (não há chave para custear — R4 do spec do editor).
    faltantes = (
        sem_custo[sem_custo["sku"].str.strip() != ""]
        .groupby("sku")["quantidade"]
        .sum()
        .sort_values(ascending=False)
    )
    skus_faltantes = [(sku, float(un)) for sku, un in faltantes.items()]

    # --- Ad Spend (R8) e ROAS Shopify (R10) --------------------------------
    # FB Ads é "embrutecido" pelo imposto (gross-up): o investimento real inclui o
    # imposto de IMPOSTO_FB_ADS pago ao investir. Google não leva imposto (ADR 2026-07-03).
    fb_real = midia_p["fb_investimento"].sum() / (1 - IMPOSTO_FB_ADS)
    ad_spend = float(
        fb_real
        + midia_p["google_investimento"].sum()
        + midia_p["google_institucional_investimento"].sum()
    )
    # --- Cascata (R6, R7, R9) — a fábrica única do DRE ----------------------
    # Sem `deals` não existe parte estimada: a aba Vendas é toda "real" (tem itens).
    linhas, lucro_bruto, mc = montar_cascata(vendas, cmv, ad_spend, parametros)
    roas = vendas / ad_spend if ad_spend > 0 else None

    return Resultado(
        vendas=vendas,
        ad_spend=ad_spend,
        roas=roas,
        ticket_medio=ticket_medio,
        pedidos=pedidos,
        cmv=cmv,
        lucro_bruto=lucro_bruto,
        mc=mc,
        linhas=linhas,
        unidades_sem_custo=unidades_sem_custo,
        skus_sem_custo=skus_sem_custo,
        skus_faltantes=skus_faltantes,
        pedidos_excluidos=pedidos_excluidos_periodo,
        avisos=avisos,
        rotulo_confianca="real",
    )


# ---------------------------------------------------------------------------
# Aba de aquisição — MC de clientes novos (V2, spec 2026-07-09)
# ---------------------------------------------------------------------------
# O carimbo nativo da Shopify (Vendas.customer_type). Match sensível a acento/maiúscula:
# a grafia é confirmada na fonte. Tudo que não for um destes dois = "sem classificação".
CLIENTE_NOVO = "Primeira Compra"
CLIENTE_RECOMPRA = "Recompra"


@dataclass
class ResultadoAquisicao:
    """Tudo que a aba de aquisição precisa desenhar para um período (só clientes novos)."""

    # Cartões (6, spec 2026-07-14): Vendas-novos · Ad Spend · aROAS · Ticket Médio · Pedidos · CAC
    mc_novos: float
    vendas_novos: float
    pedidos_novos: int
    cac: float | None      # Ad Spend total ÷ Pedidos-novos. None se não há pedidos novos
    aroas: float | None    # Vendas-novos ÷ Ad Spend total. None se não há mídia
    ticket_medio: float | None  # Vendas-novos ÷ Pedidos-novos. None se não há pedidos novos
    # Mini-cascata de novos
    cmv_novos: float
    lucro_bruto_novos: float
    ad_spend: float        # mídia INTEIRA do período (convenção 100% mídia → novos)
    linhas: list[LinhaDRE]
    # Amarração das 3 faixas (guarda silenciosa) — em contagem de pedidos
    pedidos_total: int
    pedidos_recompra: int
    pedidos_sem_classificacao: int
    amarra: bool
    # Alertas de custo entre os novos (herda o alerta da V1)
    unidades_sem_custo: float = 0.0
    skus_sem_custo: int = 0
    avisos: list[str] = field(default_factory=list)
    # [rebase HubSpot 2026-07-14] parte sem itens (CMV estimado em 30%)
    rotulo_confianca: str = "real"   # "real" | "estimada" | "mista"
    vendas_novos_estimada: float = 0.0
    pedidos_novos_estimados: int = 0
    cmv_estimado: float = 0.0

    @property
    def sem_dados(self) -> bool:
        """Período sem nenhum movimento (nenhum pedido real/estimado e sem mídia)."""
        return self.pedidos_total == 0 and self.pedidos_novos_estimados == 0 and self.ad_spend == 0


def calcular_aquisicao(
    dados: Dados,
    inicio,
    fim,
    parametros: dict[str, float] = PARAMETROS,
    deals=None,
    hist=None,
) -> ResultadoAquisicao:
    """
    Monta a MC de clientes novos (aba de aquisição) para o período [inicio, fim].

    Reusa EXATAMENTE o recorte do painel (`_recorte_pedidos`): só Shopify/PAID, com as
    exclusões AnjosFrach/pontuais, itens restritos aos pedidos da Vendas. Depois parte
    os pedidos por `customer_type` e calcula a cascata só sobre os `Primeira Compra`.
    A mídia entra INTEIRA (convenção 100% mídia → novos). Espelha PRODUCT.md 6 (V2) e
    a spec 2026-07-09 (R1..R13). Nunca mude um número sem rastrear a coluna de origem.

    [Unificação 2026-07-14] Com `deals`, motor **deals-based** (novos = `Primeira Compra`;
    Vendas-novos = Σ`valor` por fechamento — bate com a base; CMV real item a item, 30% onde não
    há itens). Sem `deals`, cai no motor antigo (Vendas/`customer_type`), como fallback.
    `hist` = base histórica de itens (CMV real na história inteira; sem ela, só a janela atual).
    """
    if deals is not None:
        return _calcular_aquisicao_por_deals(dados, deals, inicio, fim, parametros, hist=hist)

    vendas_p, itens_p, midia_p, _excluidos = _recorte_pedidos(dados, inicio, fim)
    avisos: list[str] = []

    # --- Partição por tipo_de_venda do HubSpot (decisão 2026-07-14) --------
    # "Novo" passa a ser a 1ª compra na Minimal (cross-canal, HubSpot `tipo_de_venda`), não o
    # carimbo do Shopify (`customer_type`). Assim a aba bate com o filtro direto da base (menos
    # o ~1% de net_revenue vs valor). A régua vem do deal (ponte nome→order_name); pedido sem
    # deal casado cai no `customer_type` do Shopify (melhor disponível). Sem `deals` → tudo pelo
    # carimbo Shopify (comportamento anterior; degrada gracioso).
    carimbo = vendas_p["customer_type"].astype("string").fillna("").str.strip()
    if deals is not None and "nome" in getattr(deals, "columns", []):
        tv = (
            deals.dropna(subset=["nome"]).drop_duplicates("nome", keep="first")
            .set_index("nome")["tipo_de_venda"]
        )
        tipo = vendas_p["order_name"].map(tv).astype("string")
        tipo = tipo.where(tipo.notna() & (tipo.str.strip() != ""), carimbo)  # fallback Shopify
    else:
        tipo = carimbo
    eh_novo = tipo == CLIENTE_NOVO
    eh_recompra = tipo == CLIENTE_RECOMPRA
    eh_sem_classif = ~eh_novo & ~eh_recompra  # vazio OU rótulo inesperado

    rotulo_inesperado = eh_sem_classif & (tipo.fillna("") != "")
    if int(rotulo_inesperado.sum()) > 0:
        rotulos = ", ".join(sorted(tipo[rotulo_inesperado].dropna().unique()))
        avisos.append(
            f"{int(rotulo_inesperado.sum())} pedido(s) com tipo de venda desconhecido "
            f"({rotulos}) — tratados como sem classificação."
        )

    vendas_novos_df = vendas_p[eh_novo]

    # --- Contagens e amarração (R4, R8) ------------------------------------
    pedidos_total = int(vendas_p["order_id"].nunique())
    pedidos_novos = int(vendas_novos_df["order_id"].nunique())
    pedidos_recompra = int(vendas_p.loc[eh_recompra, "order_id"].nunique())
    pedidos_sem_classif = int(vendas_p.loc[eh_sem_classif, "order_id"].nunique())
    amarra = (pedidos_novos + pedidos_recompra + pedidos_sem_classif) == pedidos_total
    if not amarra:
        avisos.append(
            "As faixas de cliente não somam o total de pedidos (checagem interna) — "
            "possível duplicidade de linha na aba Vendas."
        )

    # --- Vendas-novos (R3) --------------------------------------------------
    vendas_novos = float(vendas_novos_df["net_revenue"].sum())

    # --- CMV-novos (R5) — só itens dos pedidos novos, mesma junção do painel ----
    ids_novos = vendas_novos_df["order_id"].unique()
    itens_novos = itens_p[itens_p["order_id"].isin(ids_novos)]
    juncao = juntar_custos(itens_novos, dados.custos)
    cmv_novos = float(juncao["custo_linha"].sum())
    sem_custo = juncao[juncao["sem_custo"]]
    unidades_sem_custo = float(sem_custo["quantidade"].sum())
    skus_sem_custo = int(sem_custo.loc[sem_custo["sku"].str.strip() != "", "sku"].nunique())

    # --- Ad Spend total (R9) — mídia INTEIRA, idêntico ao painel -----------
    fb_real = midia_p["fb_investimento"].sum() / (1 - IMPOSTO_FB_ADS)
    ad_spend = float(
        fb_real
        + midia_p["google_investimento"].sum()
        + midia_p["google_institucional_investimento"].sum()
    )

    # --- Cascata de novos (R6, R10) — a fábrica única do DRE ---------------
    # Sem `deals` não existe parte estimada (a aba Vendas tem itens).
    linhas, lucro_bruto_novos, mc_novos = montar_cascata(
        vendas_novos, cmv_novos, ad_spend, parametros,
        rotulo_vendas="Vendas-novos", rotulo_cmv="CMV-novos",
        rotulo_lucro="Lucro Bruto-novos", rotulo_midia="Mídia Paga (inteira)",
        rotulo_mc="MC-novos",
    )

    # --- CAC (R11), aROAS (R12) e Ticket Médio ------------------------------
    cac = ad_spend / pedidos_novos if pedidos_novos > 0 else None
    aroas = vendas_novos / ad_spend if ad_spend > 0 else None
    ticket = vendas_novos / pedidos_novos if pedidos_novos > 0 else None

    return ResultadoAquisicao(
        mc_novos=mc_novos,
        vendas_novos=vendas_novos,
        pedidos_novos=pedidos_novos,
        cac=cac,
        aroas=aroas,
        ticket_medio=ticket,
        cmv_novos=cmv_novos,
        lucro_bruto_novos=lucro_bruto_novos,
        ad_spend=ad_spend,
        linhas=linhas,
        pedidos_total=pedidos_total,
        pedidos_recompra=pedidos_recompra,
        pedidos_sem_classificacao=pedidos_sem_classif,
        amarra=amarra,
        unidades_sem_custo=unidades_sem_custo,
        skus_sem_custo=skus_sem_custo,
        avisos=avisos,
        rotulo_confianca="real",
    )


# ---------------------------------------------------------------------------
# Auditoria de custos por pedido (spec 2026-07-04)
# ---------------------------------------------------------------------------
# Faixa "normal" de custo sobre a receita (custo %). Fora dela, marca como suspeito.
# Heurística ampla e ajustável — só para orientar o olho, não é regra de negócio.
FAIXA_CUSTO_PCT: tuple[float, float] = (10.0, 60.0)


@dataclass
class DetalhePedidos:
    """Duas visões consistentes com o CMV do painel, para a auditoria."""

    por_pedido: pd.DataFrame  # order_id, order_name, data, valor, custo, custo_pct, n_itens, n_sem_custo, flag
    por_item: pd.DataFrame    # order_id, sku, descricao, quantidade, custo_unit, custo_linha, sem_custo


def detalhar_pedidos(dados: Dados, inicio, fim, descricoes: dict[str, str] | None = None) -> DetalhePedidos:
    """
    Detalha, pedido a pedido, o custo (CMV) — mesma base do painel. Para a auditoria.
    `descricoes` é o dicionário SKU->nome (opcional; se ausente, mostra o código).
    """
    vendas_p, itens_p, _midia, _excl = _recorte_pedidos(dados, inicio, fim)
    descricoes = descricoes or {}

    # Itens com custo (mesma junção/receita de custo do painel — juntar_custos).
    itens = juntar_custos(itens_p, dados.custos)
    itens["custo_unit"] = itens["valor_custo"]
    # Nome do produto: vem da própria base de Itens (item_desmembrado_nome). O dict
    # `descricoes` é só reserva para eventuais SKUs sem nome na base.
    if "descricao" not in itens.columns:
        itens["descricao"] = ""
    itens["descricao"] = itens["descricao"].astype("string").fillna("")
    if descricoes:
        vazio = itens["descricao"].str.strip() == ""
        itens.loc[vazio, "descricao"] = itens.loc[vazio, "sku"].map(descricoes).fillna("")

    por_item = itens[
        ["order_id", "sku", "descricao", "quantidade", "custo_unit", "custo_linha", "sem_custo"]
    ].copy()

    # Agregado por pedido (custo, contagens).
    agg = itens.groupby("order_id").agg(
        custo=("custo_linha", "sum"),
        n_itens=("sku", "count"),
        n_sem_custo=("sem_custo", "sum"),
    )

    # Receita e dados do pedido vêm da Vendas (fonte de verdade).
    ped = vendas_p.groupby("order_id").agg(
        order_name=("order_name", "first"),
        data=("data", "first"),
        valor=("net_revenue", "sum"),
    )
    por_pedido = ped.join(agg, how="left").reset_index()
    por_pedido["custo"] = por_pedido["custo"].fillna(0.0)
    por_pedido["n_itens"] = por_pedido["n_itens"].fillna(0).astype(int)
    por_pedido["n_sem_custo"] = por_pedido["n_sem_custo"].fillna(0).astype(int)

    # custo % da receita (vazio se receita 0).
    por_pedido["custo_pct"] = por_pedido.apply(
        lambda r: (r["custo"] / r["valor"] * 100) if r["valor"] else float("nan"), axis=1
    )

    # Marca suspeitos: sem custo, ou custo % fora da faixa.
    faixa_min, faixa_max = FAIXA_CUSTO_PCT

    def _flag(r) -> str:
        if r["n_sem_custo"] > 0:
            return "sem custo"
        p = r["custo_pct"]
        if pd.notna(p) and p > faixa_max:
            return "custo alto"
        if pd.notna(p) and r["valor"] > 0 and p < faixa_min:
            return "custo baixo"
        return ""

    por_pedido["flag"] = por_pedido.apply(_flag, axis=1)
    por_pedido = por_pedido.sort_values("data")
    return DetalhePedidos(por_pedido=por_pedido, por_item=por_item)
