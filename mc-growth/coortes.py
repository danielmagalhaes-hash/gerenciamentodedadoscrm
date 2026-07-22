"""
coortes.py — coortes de recompra (V4, TOCA DINHEIRO).

Segue a mesma TURMA de clientes ao longo dos meses: agrupa por SAFRA (mês da 1ª
compra, cross-canal, vindo do HubSpot) e acumula a Margem de Contribuição POR CLIENTE
conforme a turma envelhece (m+0, m+1, …). A mídia inteira do mês pesa no m+0 (o CAC
da safra); a recompra vai somando adiante. Cruzar o zero = a turma se pagou.

MVP (Opção 2 — ADR 2026-07-10-v4-arquitetura-mvp-coortes): a MC de produto é REAL só
onde o pedido do HubSpot casa com a `Vendas`/`Itens` da janela atual (ponte pelo número
do pedido, reusando a MESMA receita de custo do painel — cascata.cmv_por_pedido); fora
dela, o CMV é ESTIMADO em 30% da receita (as deduções/custos % incidem normal) → margem
de produto de 42,5% do valor. Cada célula é marcada real/estimada. Rótulo honesto:
"MC parcial" (não desconta CX, juros de estoque nem criativo — fora desta versão).

Toda regra aqui espelha a spec 2026-07-10-v4-coortes-recompra §4 (R1..R16) e o
PRODUCT.md V4 §6. Vocabulário: MC, nunca "lucro". Nunca mude um número sem rastrear a
coluna de origem. Não escreve em lugar nenhum (só leitura).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import cascata
from dados import Dados

# A partir de 2026-01-01 o investimento em FB Ads passou a ter imposto de 12,15%
# (ADR 2026-07-03). Antes disso não havia — a Ad Spend histórica é a soma crua.
_MES_IMPOSTO_FB = pd.Period("2026-01", freq="M")
# Fator de gross-up do FB: fb × IMPOSTO/(1−IMPOSTO). Somado ao investimento_total (cru),
# reproduz EXATAMENTE a Ad Spend do painel para 2026 (fb/(1−IMPOSTO)+google+inst — R6).
_FATOR_IMPOSTO_FB = cascata.IMPOSTO_FB_ADS / (1 - cascata.IMPOSTO_FB_ADS)

# [CMV estimado 2026-07-14] Fora da janela de itens não há custo real: o CMV do deal é
# estimado em 30% da receita (cascata.CMV_ESTIMADO_FRACAO) e as deduções/custos variáveis
# incidem normalmente. Logo a margem de produto estimada = 1 − 27,49% − 30% = 42,5% do valor
# (antes eram 25% diretos — chute pessimista; o real medido é ~43%).
# Spec `2026-07-14-interface-menu-cascata-cmv-30`.

# Janela fixa da recompra (spec R13). Fixa para as safras serem comparáveis entre si.
JANELA_RECOMPRA_DIAS = 90

# Soma das deduções + custos variáveis (%) do painel, como fração — incide sobre a
# receita no ramo real (mesma base do Lucro Bruto do painel).
_FRACAO_DEDUCOES = sum(cascata.PARAMETROS.values()) / 100.0


@dataclass
class ResultadoCoortes:
    """Tudo que a aba de coortes precisa desenhar. Só safras FECHADAS entram."""

    # Triângulo (índice = safra "AAAA-MM"; colunas = idade 0..max)
    mc_acumulada: pd.DataFrame  # MC acumulada por cliente (R$/cliente); NaN onde não fechada
    real: pd.DataFrame          # bool: True = célula sem nenhum deal estimado (peso normal)
    # Por safra
    safras: list[str]                     # safras fechadas, em ordem cronológica
    n_clientes: dict[str, int]            # N_S (clientes distintos por safra)
    cac: dict[str, float | None]          # Ad Spend(mês) ÷ N_S; None se a Midia não cobre o mês
    payback: dict[str, int | None]        # menor m com MC acumulada ≥ 0; None se não cruzou
    mc_ate_hoje: dict[str, float]         # MC acumulada na maior idade fechada (LTV até agora)
    recompra_90d: dict[str, float]        # fração da safra com ≥1 recompra Shopify em 90 dias
    recompra_madura: dict[str, bool]      # a janela de 90d da safra já fechou?
    # Contexto / alertas
    ultimo_mes_fechado: str
    janela_real: tuple[pd.Timestamp, pd.Timestamp] | None  # datas do ramo real (Vendas)
    frac_estimada: float                  # fração de deals estimados (leitura honesta do MVP)
    total_clientes: int                   # Σ N_S (sanidade)
    safras_sem_midia: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    # [2026-07-14] Irmãs do triângulo — mesma turma, outras lentes:
    ltv: pd.DataFrame = field(default_factory=pd.DataFrame)          # receita acumulada / cliente
    mc_absoluta: pd.DataFrame = field(default_factory=pd.DataFrame)  # MC acumulada em R$ cheios
    ticket_primeira_compra: dict[str, float] = field(default_factory=dict)  # valor médio do 1º pedido
    mc_primeira_compra: dict[str, float] = field(default_factory=dict)      # MC do 1º pedido − CAC
    # [2026-07-14] LUCRO BRUTO acumulado por cliente = a MC ANTES da mídia (o `mc_produto` cru).
    # Existe porque o ratio contra o CAC tem de usá-lo: dividir a MC (que JÁ desconta a mídia)
    # pelo CAC contaria a mídia DUAS vezes. Identidade garantida: lucro_bruto = mc_acumulada + CAC.
    lucro_bruto: pd.DataFrame = field(default_factory=pd.DataFrame)         # R$/cliente, sem mídia
    lucro_bruto_primeira_compra: dict[str, float] = field(default_factory=dict)  # 1º pedido, sem mídia

    @property
    def sem_safras(self) -> bool:
        return len(self.safras) == 0


def _ad_spend_por_mes(midia: pd.DataFrame) -> dict[pd.Period, float]:
    """
    Ad Spend por mês-calendário (R6), com imposto condicional:
      - mês ≥ 2026-01: investimento_total + fb_investimento × IMPOSTO/(1−IMPOSTO);
      - mês  < 2026-01: investimento_total (não havia imposto).
    Base = a aba `Midia` estendida (investimento_total cru). Meses fora da cobertura
    da aba simplesmente não aparecem no dicionário (→ CAC "—" na safra — R7).
    """
    m = midia.dropna(subset=["data"]).copy()
    m["mes"] = m["data"].dt.to_period("M")
    g = m.groupby("mes").agg(
        inv=("investimento_total", "sum"),
        fb=("fb_investimento", "sum"),
    )
    ad: dict[pd.Period, float] = {}
    for mes, linha in g.iterrows():
        base = float(linha["inv"]) if pd.notna(linha["inv"]) else 0.0
        if mes >= _MES_IMPOSTO_FB:
            base += float(linha["fb"]) * _FATOR_IMPOSTO_FB
        ad[mes] = base
    return ad


def _mc_produto_por_deal(dados: Dados, deals: pd.DataFrame, hist=None) -> pd.DataFrame:
    """
    Acrescenta a `deals` duas colunas: `mc_produto` (MC de produto antes da mídia) e
    `real` (True = o pedido tem itens → CMV real; False = CMV estimado em 30%).

    [2026-07-14 — spec `cmv-real-historico-3-camadas`] O ramo real deixou de ser só a janela da
    planilha: os itens vêm das **3 camadas** (`cascata.itens_por_nome`) — base histórica (2021-10
    → hoje), planilha para os pedidos recentes demais, e nada → estimado. A ponte é **direta**
    pelo número do pedido (`HubSpot.nome == itens.order_name`), sem a volta pela `Vendas`.
    O custo continua saindo de `cascata.juntar_custos` — a única verdade de custo (CLAUDE.md §11).
    """
    itens_nome = cascata.itens_por_nome(dados, hist)
    cmv_tab = cascata.cmv_por_nome(dados, itens_nome=itens_nome)  # order_name -> cmv, ...

    # Pedido "real" = deal `Shipped` (só ele pode casar — `cascata.pode_casar_itens`) que tem
    # itens resolvidos, ou está na aba Vendas sem itens (resíduo aceito, CMV 0 — o mesmo critério
    # do painel). O Comercial nunca casa (colisão de numeração) → estimado em 30%.
    reais = cascata.nomes_com_cmv_real(dados, itens_nome)
    eh_real = cascata.pode_casar_itens(deals) & deals["nome"].isin(reais)
    # Pedido real sem itens (o resíduo da Vendas) entra com CMV 0; o não-real fica NaN (→ estimado).
    cmv_real = deals["nome"].map(cmv_tab["cmv"]).fillna(0.0).where(eh_real)

    janela = (
        (dados.vendas["data"].min(), dados.vendas["data"].max())
        if len(dados.vendas) and dados.vendas["data"].notna().any()
        else None
    )

    # Receita = `valor` do HubSpot em AMBOS os ramos (unificação 2026-07-14 — igual ao painel).
    # O que muda é o CUSTO: ramo real usa o CMV item a item; ramo estimado usa 30% da receita.
    # As deduções/custos variáveis (%) incidem igual nos dois ramos (spec 2026-07-14).
    valor = deals["valor"].fillna(0.0)
    cmv_deal = cmv_real.where(eh_real, cascata.CMV_ESTIMADO_FRACAO * valor)
    mc_produto = valor - valor * _FRACAO_DEDUCOES - cmv_deal

    out = deals.copy()
    out["mc_produto"] = mc_produto
    out["real"] = eh_real.to_numpy()
    # Peças cruas para a auditoria: o CMV do deal (real onde casou, estimado onde não) e a
    # parte só-real (NaN no estimado). A receita é o próprio `valor` nos dois ramos.
    out["cmv_deal"] = cmv_deal
    out["cmv_real"] = cmv_real.where(eh_real)
    return out, janela


def _recompra_90d(deals: pd.DataFrame) -> pd.Series:
    """
    Fração de cada safra com ≥1 recompra Shopify (deal `Shipped`) em até 90 dias da 1ª
    compra (R13). Janela fixa. Denominador = N_S (clientes distintos da safra).
    """
    ship = deals[deals["etapa_do_negocio"] == "Shipped"].dropna(
        subset=["data_de_fechamento", "data_primeira_compra"]
    )
    delta = (ship["data_de_fechamento"] - ship["data_primeira_compra"]).dt.days
    recomprou = (delta > 0) & (delta <= JANELA_RECOMPRA_DIAS)
    por_cliente = recomprou.groupby(ship["e_mail"]).any()

    # Cada cliente pertence a uma safra (1ª compra única). Junta safra do cliente.
    safra_cliente = deals.groupby("e_mail")["safra"].first()
    tabela = pd.DataFrame({"safra": safra_cliente})
    tabela["recompra"] = por_cliente.reindex(tabela.index).fillna(False)
    return tabela.groupby("safra")["recompra"].mean()


def _preparar_deals(dados: Dados, deals: pd.DataFrame, hist=None):
    """
    Enriquecimento por deal COMPARTILHADO entre o triângulo (`calcular_coortes`) e a
    auditoria (`detalhar_safra`) — uma só verdade. Devolve (deals_enriquecidos, janela_real,
    avisos), com as colunas: `mc_produto`, `real`, `cmv_real`, `safra` e `idade` (receita = `valor`).

    Faz: (1) MC de produto por deal (ramo real via ponte, senão estimado); (2) ancora
    safra E idade na 1ª compra REAL do cliente (mínimo por `e_mail` — um cliente = uma safra;
    corrige a deriva do HubSpot); (3) calcula a idade da coorte da diferença de meses-calendário
    (NÃO usa `meses_desde_primeira_compra`, que é a idade do cliente no export — achado 2026-07-10).
    """
    avisos: list[str] = []

    # Exclusões de negócio (ADR 2026-07-02): pedidos AnjosFrach e os pontuais saem INTEIROS da
    # análise — no painel já saíam; aqui não saíam (achado 2026-07-14), e a coorte contava uns
    # reais a mais que a Aquisição. Agora as duas telas contam exatamente os mesmos pedidos.
    excl_ids = cascata._pedidos_excluidos(dados.itens)
    excl_nomes = set(dados.vendas.loc[dados.vendas["order_id"].isin(excl_ids), "order_name"])
    excl_nomes |= set(cascata.PEDIDOS_EXCLUIDOS_NOME)
    n_antes = len(deals)
    deals = deals[~deals["nome"].isin(excl_nomes)]
    if n_antes - len(deals) > 0:
        avisos.append(
            f"{n_antes - len(deals)} pedido(s) excluído(s) da coorte por decisão de negócio "
            "(AnjosFrach e pontuais — ADR 2026-07-02), como no painel."
        )

    deals, janela_real = _mc_produto_por_deal(dados, deals, hist=hist)
    deals = deals.copy()

    # UM CLIENTE = UMA SAFRA (PRODUCT.md §3). O pipeline do HubSpot pode reescrever a
    # `data_primeira_compra` de um cliente entre deals (merge de contatos — a "deriva" da
    # spec §8). Ancoramos safra E idade na 1ª compra REAL do cliente (o mínimo entre os
    # deals dele), para que ΣN_S = clientes distintos e a idade seja consistente.
    prim_cliente = deals.groupby("e_mail")["data_primeira_compra"].transform("min")
    n_derivou = int((prim_cliente != deals["data_primeira_compra"]).sum())
    deals["data_primeira_compra"] = prim_cliente
    deals["safra"] = prim_cliente.dt.to_period("M").astype("string")
    if n_derivou:
        avisos.append(
            f"{n_derivou} deal(s) tinham `data_primeira_compra` divergente do mínimo do "
            "cliente (deriva do HubSpot) — ancorados na 1ª compra real do cliente."
        )

    # IDADE DA COORTE (m+0, m+1, …) = diferença em meses-CALENDÁRIO entre a data do pedido
    # e a 1ª compra. ATENÇÃO (achado 2026-07-10, contraria a spec §3.3/R4): o campo
    # `meses_desde_primeira_compra` do HubSpot NÃO é a idade do deal — é a idade do CLIENTE
    # no momento do export (constante em TODOS os deals do cliente). Usá-lo empilharia a
    # turma inteira numa única idade. A idade certa se calcula das duas datas.
    fech, prim = deals["data_de_fechamento"], deals["data_primeira_compra"]
    idade = (fech.dt.year - prim.dt.year) * 12 + (fech.dt.month - prim.dt.month)
    n_sem_data = int(fech.isna().sum())
    n_negativa = int((idade < 0).sum())
    deals["idade"] = idade
    deals = deals[deals["idade"].notna() & (deals["idade"] >= 0)].copy()
    deals["idade"] = deals["idade"].astype("int64")
    if n_sem_data:
        avisos.append(f"{n_sem_data} deal(s) sem data de fechamento — fora do triângulo.")
    if n_negativa:
        avisos.append(
            f"{n_negativa} deal(s) com data anterior à 1ª compra (inconsistência) — fora do triângulo."
        )
    return deals, janela_real, avisos


def calcular_coortes(dados: Dados, deals: pd.DataFrame, hoje=None, hist=None) -> ResultadoCoortes:
    """
    Monta o triângulo de coortes (safra × idade → MC acumulada por cliente) a partir dos
    deals do HubSpot (`dados.carregar_hubspot`) e das abas do painel (para o CMV real e a
    mídia). `hoje` (date/Timestamp) define a régua de safra fechada; padrão = hoje.

    Regras: spec §4 (R1..R16). Só entram células de mês-calendário JÁ ENCERRADO (R11).
    """
    hoje = pd.Timestamp(hoje) if hoje is not None else pd.Timestamp.today()
    ultimo_fechado = pd.Period(hoje, freq="M") - 1  # último mês inteiro que já terminou
    avisos: list[str] = []

    if deals.empty:
        return ResultadoCoortes(
            mc_acumulada=pd.DataFrame(), real=pd.DataFrame(), safras=[], n_clientes={},
            cac={}, payback={}, mc_ate_hoje={}, recompra_90d={}, recompra_madura={},
            ultimo_mes_fechado=str(ultimo_fechado), janela_real=None, frac_estimada=0.0,
            total_clientes=0, avisos=["Base de coortes vazia."],
        )

    # --- Enriquecimento por deal (compartilhado com a auditoria) -----------
    deals, janela_real, avisos_prep = _preparar_deals(dados, deals, hist=hist)
    avisos.extend(avisos_prep)

    # --- Safras fechadas: a 1ª compra tem de estar num mês já encerrado -----
    deals["safra_periodo"] = pd.PeriodIndex(deals["safra"], freq="M")
    deals = deals[deals["safra_periodo"] <= ultimo_fechado]
    if deals.empty:
        return ResultadoCoortes(
            mc_acumulada=pd.DataFrame(), real=pd.DataFrame(), safras=[], n_clientes={},
            cac={}, payback={}, mc_ate_hoje={}, recompra_90d={}, recompra_madura={},
            ultimo_mes_fechado=str(ultimo_fechado), janela_real=janela_real,
            frac_estimada=0.0, total_clientes=0, avisos=["Sem safras fechadas para exibir."],
        )

    # --- N_S por safra e Ad Spend por mês ----------------------------------
    n_clientes = deals.groupby("safra")["e_mail"].nunique()
    ad_por_mes = _ad_spend_por_mes(dados.midia)

    # --- Célula (safra, idade): soma da MC de produto + contagem real/estimada
    cell = deals.groupby(["safra", "idade"]).agg(
        mc=("mc_produto", "sum"),
        n_deals=("mc_produto", "size"),
        n_real=("real", "sum"),
    )
    cell["n_est"] = cell["n_deals"] - cell["n_real"]

    safras = sorted(n_clientes.index)
    max_idade = int(deals["idade"].max())
    colunas = list(range(0, max_idade + 1))

    # Pivôs alinhados (safra × idade). Idade ausente = 0 incremental / 0 deal.
    mc_pivot = cell["mc"].unstack("idade").reindex(index=safras, columns=colunas).fillna(0.0)
    nest_pivot = cell["n_est"].unstack("idade").reindex(index=safras, columns=colunas).fillna(0)
    ndeals_pivot = cell["n_deals"].unstack("idade").reindex(index=safras, columns=colunas).fillna(0)

    # --- MC incremental por cliente; CAC no m+0 ----------------------------
    inc = mc_pivot.div(n_clientes.reindex(safras), axis=0)

    # LUCRO BRUTO acumulado por cliente = o MESMO acumulado, ANTES de descontar a mídia. É o
    # numerador honesto do ratio contra o CAC (a MC já tem a mídia dentro → dividi-la pelo CAC
    # contaria a mídia duas vezes). Tirado daqui, de `inc` ainda cru, e não somando o CAC de
    # volta depois: dinheiro tem um dono só.
    lucro_bruto = inc.cumsum(axis=1)

    cac: dict[str, float | None] = {}
    safras_sem_midia: list[str] = []
    for safra in safras:
        mes = pd.Period(safra, freq="M")
        ad = ad_por_mes.get(mes)
        n_s = int(n_clientes[safra])
        if ad is None:
            cac[safra] = None
            safras_sem_midia.append(safra)
        else:
            cac[safra] = ad / n_s if n_s else None
            inc.loc[safra, 0] = inc.loc[safra, 0] - (ad / n_s if n_s else 0.0)

    # --- MC acumulada por cliente (cumsum na idade) ------------------------
    acum = inc.cumsum(axis=1)

    # --- Tabela de RECEITA (2026-07-14): LTV = receita acumulada POR CLIENTE ---
    # É a irmã bruta do triângulo: mesma turma, mesma idade, mas ANTES de qualquer custo.
    rec_cell = deals.groupby(["safra", "idade"])["valor"].sum()
    rec_pivot = rec_cell.unstack("idade").reindex(index=safras, columns=colunas).fillna(0.0)
    ltv = rec_pivot.div(n_clientes.reindex(safras), axis=0).cumsum(axis=1)

    # --- Triângulo em REAIS CHEIOS (MC absoluta da turma) ---------------------
    # Mesma conta do triângulo por cliente, sem dividir por N: mostra o volume que a safra
    # devolveu (turmas de tamanhos diferentes não se comparam — é leitura de tamanho, não de
    # eficiência).
    mc_abs_inc = mc_pivot.copy()
    for safra in safras:
        ad = ad_por_mes.get(pd.Period(safra, freq="M"))
        if ad is not None:
            mc_abs_inc.loc[safra, 0] = mc_abs_inc.loc[safra, 0] - ad
    mc_absoluta = mc_abs_inc.cumsum(axis=1)

    # --- A 1ª compra da turma (a "porta de entrada") --------------------------
    # Régua de "novo" = o carimbo `tipo_de_venda` do HubSpot (decisão do João, 2026-07-14) — a
    # MESMA da aba Aquisição. Ticket da 1ª compra = valor médio desses pedidos por cliente;
    # MC da 1ª compra = a margem deles JÁ descontada a mídia inteira do mês — logo é o m+0 SEM
    # as recompras que caíram no mesmo mês de entrada.
    primeiras = deals[cascata.mascara_cliente_novo(deals)]
    valor_1a = primeiras.groupby("safra")["valor"].sum().reindex(safras).fillna(0.0)
    mc_1a = primeiras.groupby("safra")["mc_produto"].sum().reindex(safras).fillna(0.0)
    ticket_primeira_compra: dict[str, float] = {}
    mc_primeira_compra: dict[str, float] = {}
    lucro_bruto_primeira_compra: dict[str, float] = {}
    for safra in safras:
        n_s = int(n_clientes[safra])
        ad = ad_por_mes.get(pd.Period(safra, freq="M")) or 0.0
        ticket_primeira_compra[safra] = float(valor_1a[safra] / n_s) if n_s else float("nan")
        mc_primeira_compra[safra] = float((mc_1a[safra] - ad) / n_s) if n_s else float("nan")
        # o MESMO 1º pedido, sem tirar a mídia (é o que se divide pelo CAC)
        lucro_bruto_primeira_compra[safra] = float(mc_1a[safra] / n_s) if n_s else float("nan")

    # --- Célula real vs estimada: real quando a MAIORIA dos deals casou (CMV real).
    # A base é bimodal — safras na janela de itens vêm ~99% reais; as antigas, 100%
    # estimadas (CMV a 30%). Uma dúzia de deals não-casados não pinta a célula inteira
    # de estimada (spec CA5). Célula sem deal (0 contribuição) conta como real (nada estimado).
    frac_est = nest_pivot.where(ndeals_pivot > 0).div(ndeals_pivot.where(ndeals_pivot > 0))
    real_flag = (frac_est <= 0.5) | (ndeals_pivot == 0)

    # --- Máscara de safra fechada: célula (safra, m) só se safra+m já terminou
    # Vale para os três triângulos (MC/cliente, MC absoluta e LTV) — nada de mês correndo.
    for safra in safras:
        base_mes = pd.Period(safra, freq="M")
        for m in colunas:
            if base_mes + m > ultimo_fechado:
                acum.loc[safra, m] = np.nan
                ltv.loc[safra, m] = np.nan
                mc_absoluta.loc[safra, m] = np.nan
                lucro_bruto.loc[safra, m] = np.nan
                real_flag.loc[safra, m] = False

    # --- Payback e MC até hoje por safra -----------------------------------
    payback: dict[str, int | None] = {}
    mc_ate_hoje: dict[str, float] = {}
    for safra in safras:
        serie = acum.loc[safra].dropna()
        mc_ate_hoje[safra] = float(serie.iloc[-1]) if len(serie) else float("nan")
        cruzou = serie[serie >= 0]
        payback[safra] = int(cruzou.index[0]) if len(cruzou) else None

    # --- Recompra em 90 dias -----------------------------------------------
    recompra = _recompra_90d(deals).reindex(safras).fillna(0.0)
    recompra_90d = {s: float(recompra[s]) for s in safras}
    # A janela de 90d de uma safra só "fecha" quando passam 90 dias do fim do mês da safra.
    recompra_madura = {
        s: (pd.Period(s, freq="M").end_time + pd.Timedelta(days=JANELA_RECOMPRA_DIAS)) <= hoje
        for s in safras
    }

    # --- Fração estimada (leitura honesta do MVP) --------------------------
    total_deals = int(cell["n_deals"].sum())
    total_est = int(cell["n_est"].sum())
    frac_estimada = (total_est / total_deals) if total_deals else 0.0

    if safras_sem_midia:
        avisos.append(
            f"{len(safras_sem_midia)} safra(s) sem mídia na aba `Midia` "
            f"(CAC '—'): {', '.join(safras_sem_midia[:6])}"
            + (" …" if len(safras_sem_midia) > 6 else "")
        )

    return ResultadoCoortes(
        mc_acumulada=acum,
        real=real_flag,
        safras=safras,
        n_clientes={s: int(n_clientes[s]) for s in safras},
        cac=cac,
        payback=payback,
        mc_ate_hoje=mc_ate_hoje,
        recompra_90d=recompra_90d,
        recompra_madura=recompra_madura,
        ultimo_mes_fechado=str(ultimo_fechado),
        janela_real=janela_real,
        frac_estimada=frac_estimada,
        total_clientes=int(n_clientes.sum()),
        safras_sem_midia=safras_sem_midia,
        avisos=avisos,
        ltv=ltv,
        mc_absoluta=mc_absoluta,
        lucro_bruto=lucro_bruto,
        lucro_bruto_primeira_compra=lucro_bruto_primeira_compra,
        ticket_primeira_compra=ticket_primeira_compra,
        mc_primeira_compra=mc_primeira_compra,
    )


# ---------------------------------------------------------------------------
# Auditoria por safra (spec 2026-07-10-v4-auditoria-por-safra) — abre a cascata
# (Receita → deduções → CMV → Lucro Bruto → mídia → MC) de UMA safra, para o João
# conferir se a receita e os descontos que entraram estão certos. NÃO recalcula a MC:
# só RE-EXPRESSA a mesma `mc_produto` do triângulo (mesma `_preparar_deals`).
# ---------------------------------------------------------------------------
@dataclass
class DetalheSafra:
    """
    A cascata de uma safra, aberta em TRÊS blocos (redesenho 2026-07-13, pedido do João):
      A) **MC dos novos** (1ª compra da safra) — cascata COMPLETA igual à aba Aquisição
         (Vendas → deduções abertas → CMV → Lucro Bruto → − mídia inteira → MC-novos).
      B) **MC de recompra** (compras seguintes da turma) — agrupada (Vendas → deduções % →
         CMV → MC-recompra), SEM mídia (a mídia é custo de aquisição, já no bloco A).
      C) **MC total** = MC-novos + MC-recompra, e ÷ N = MC total por cliente (o nº do triângulo).
    Depende do **horizonte** (`ate_idade`): quantos meses de recompra entram. Não recalcula a MC —
    só re-expressa a mesma `mc_produto`, partida por `tipo_de_venda`.
    """

    safra: str
    n_clientes: int
    idade_max_fechada: int               # último mês fechado da safra (teto do horizonte)
    ate_idade: int                       # horizonte analisado (m+0..ate_idade)
    # Bloco A — MC dos novos (cascata igual à V2). Lista (rótulo, valor c/ sinal, tipo p/ estilo).
    cascata_novos: list[tuple[str, float, str]]
    vendas_novos: float
    mc_novos: float
    media_total: float | None
    # Bloco B — MC de recompra (agrupada)
    cascata_recompra: list[tuple[str, float, str]]
    vendas_recompra: float
    mc_recompra: float
    # Bloco C — total
    mc_total: float
    mc_total_cliente: float              # bate com mc_acumulada[safra, ate_idade] do triângulo
    # contagens / detalhe
    n_novos: int
    n_recompra: int
    n_deals: int
    n_reais: int
    por_idade: pd.DataFrame
    deals_export: pd.DataFrame
    avisos: list[str] = field(default_factory=list)


def preparar_deals_cache(dados: Dados, deals: pd.DataFrame, hist=None) -> pd.DataFrame:
    """Enriquecimento pesado (ponte + safra + idade), para a UI cachear 1× e reusar por safra."""
    enr, _janela, _avisos = _preparar_deals(dados, deals, hist=hist)
    return enr


def detalhar_safra(dados: Dados, deals: pd.DataFrame, safra: str, hoje=None,
                   ate_idade: int | None = None, enr: pd.DataFrame | None = None) -> DetalheSafra:
    """
    Abre a cascata da MC de UMA safra em blocos **novos × recompra × total** (só idades fechadas,
    até `ate_idade`). Reusa `_preparar_deals` — a mesma `mc_produto` do triângulo —, então a
    auditoria e a curva nunca discordam: `mc_total_cliente` = `mc_acumulada[safra, ate_idade]`.

    Partição: **novos** = deals com `tipo_de_venda == "Primeira Compra"` (a 1ª compra, idade 0);
    **recompra** = o resto (compras seguintes, qualquer idade). A mídia inteira do mês entra só no
    bloco dos novos (é o custo de aquisição). Os dois blocos usam a MESMA cascata das outras abas
    (cascata.montar_cascata); onde o pedido não tem itens, o CMV entra estimado (30%) e a linha
    do CMV vem marcada com ⚠️.
    """
    hoje = pd.Timestamp(hoje) if hoje is not None else pd.Timestamp.today()
    ultimo_fechado = pd.Period(hoje, freq="M") - 1
    if enr is None:
        enr, _janela, avisos = _preparar_deals(dados, deals, hist=hist)
    else:
        avisos = []

    base_mes = pd.Period(safra, freq="M")
    idade_max = max((ultimo_fechado - base_mes).n, 0)  # último mês fechado da safra
    ate = idade_max if ate_idade is None else max(0, min(int(ate_idade), idade_max))

    # N_S = clientes distintos da safra INTEIRA (R3) — o mesmo denominador do triângulo.
    todos_safra = enr[enr["safra"] == safra]
    N = int(todos_safra["e_mail"].nunique())
    # A cascata soma as idades fechadas ATÉ o horizonte (a MC/cliente divide pelo N_S inteiro).
    sub = todos_safra[todos_safra["idade"] <= ate].copy()
    ad_map = _ad_spend_por_mes(dados.midia)
    media_total = ad_map.get(base_mes)  # None se a Midia não cobre o mês
    media = float(media_total) if media_total is not None else 0.0

    # NOVOS = o carimbo `tipo_de_venda` do HubSpot (decisão do João, 2026-07-14) — a MESMA régua
    # da aba Aquisição, para as duas telas não discordarem. RECOMPRA = o resto.
    sub = sub.sort_values(["e_mail", "idade", "data_de_fechamento"])
    novos_mask = cascata.mascara_cliente_novo(sub)
    P = cascata.PARAMETROS

    def _partes(bloco: pd.DataFrame):
        """(receita, CMV total do bloco, quanto do CMV é estimado a 30%)."""
        vendas = float(bloco["valor"].fillna(0.0).sum())   # receita = valor (unificação 2026-07-14)
        cmv = float(bloco["cmv_deal"].fillna(0.0).sum())   # real onde casou; 30% onde não
        cmv_est = float(bloco.loc[~bloco["real"], "cmv_deal"].fillna(0.0).sum())
        return vendas, cmv, cmv_est

    # --- Bloco A: MC dos novos — cascata completa (a mesma fábrica das outras abas) ---
    nv = sub[novos_mask]
    v_nov, cmv_nov, cmv_est_nov = _partes(nv)
    linhas_nov, lb_nov, mc_novos = cascata.montar_cascata(
        v_nov, cmv_nov, media, P,
        rotulo_vendas="Vendas-novos (1ª compra)", rotulo_cmv="CMV-novos",
        rotulo_lucro="Lucro Bruto-novos", rotulo_midia="Mídia Paga (inteira)",
        rotulo_mc="MC-novos", cmv_estimado=cmv_est_nov,
    )
    cascata_novos = [(l.rotulo, l.valor, l.tipo) for l in linhas_nov]

    # --- Bloco B: MC de recompra — mesma cascata, SEM mídia (é custo de aquisição) ---
    rc = sub[~novos_mask]
    v_rec, cmv_rec, cmv_est_rec = _partes(rc)
    linhas_rec, _lb_rec, mc_recompra = cascata.montar_cascata(
        v_rec, cmv_rec, 0.0, P,
        rotulo_vendas="Vendas-recompra", rotulo_cmv="CMV-recompra",
        rotulo_mc="MC-recompra", com_midia=False, cmv_estimado=cmv_est_rec,
    )
    cascata_recompra = [(l.rotulo, l.valor, l.tipo) for l in linhas_rec]

    # --- Bloco C: total ----------------------------------------------------
    mc_total = mc_novos + mc_recompra
    mc_total_cliente = (mc_total / N) if N else float("nan")

    # --- Cascata por idade (m+0..ate), acumulando por cliente ---------------
    linhas_idade = []
    acum_cliente = 0.0
    for m in range(0, ate + 1):
        g = sub[sub["idade"] == m]
        gr = g[g["real"]]
        # Receita e CMV do mês inteiro (real + estimado a 30%) — mesma conta da cascata.
        rec_m = float(g["valor"].fillna(0.0).sum())
        cmv_m = float(g["cmv_deal"].fillna(0.0).sum())
        ded_m = rec_m * _FRACAO_DEDUCOES
        mcp_m = float(g["mc_produto"].sum())   # = rec_m − ded_m − cmv_m
        med_m = media if m == 0 else 0.0
        incr_cli = ((mcp_m - med_m) / N) if N else float("nan")
        acum_cliente += incr_cli
        n_g = int(len(g))
        linhas_idade.append({
            "idade": f"m+{m}",
            "deals": n_g,
            "%real": (float(gr.shape[0]) / n_g) if n_g else float("nan"),
            "receita": rec_m,
            "deducoes": -ded_m,
            "cmv": -cmv_m,
            "lucro_bruto": mcp_m,
            "midia": -med_m,
            "mc_incr_cliente": incr_cli,
            "mc_acum_cliente": acum_cliente,
        })
    por_idade = pd.DataFrame(linhas_idade)

    # --- Export por deal (SEM e-mail — PRODUCT §8; o número do pedido é a chave) ---
    deals_export = pd.DataFrame({
        "pedido": sub["nome"],
        "safra": sub["safra"],
        "idade": sub["idade"],
        "tipo_de_venda": sub["tipo_de_venda"],
        "etapa": sub["etapa_do_negocio"],
        "ramo": np.where(sub["real"].to_numpy(), "medido", "estimado"),
        "receita": sub["valor"],  # receita = valor em ambos os ramos (unificação 2026-07-14)
        "cmv": sub["cmv_deal"],   # real onde casou com os itens; 30% da receita onde não
        "mc_produto": sub["mc_produto"],
    }).sort_values(["idade", "pedido"]).reset_index(drop=True)

    if media_total is None:
        avisos.append(f"Safra {safra}: a aba Midia não cobre o mês — mídia tratada como 0 (CAC '—').")

    return DetalheSafra(
        safra=safra,
        n_clientes=N,
        idade_max_fechada=idade_max,
        ate_idade=ate,
        cascata_novos=cascata_novos,
        vendas_novos=v_nov,
        mc_novos=mc_novos,
        media_total=media_total,
        cascata_recompra=cascata_recompra,
        vendas_recompra=v_rec,
        mc_recompra=mc_recompra,
        mc_total=mc_total,
        mc_total_cliente=mc_total_cliente,
        n_novos=int(novos_mask.sum()),
        n_recompra=int((~novos_mask).sum()),
        n_deals=int(len(sub)),
        n_reais=int(sub["real"].sum()),
        por_idade=por_idade,
        deals_export=deals_export,
        avisos=avisos,
    )
