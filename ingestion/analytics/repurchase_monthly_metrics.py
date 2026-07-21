"""Série mensal das métricas de recompra, gravada em fact_repurchase_monthly_metrics.

Extensão de "Análises - Base de Dados Extras/modelo_recompra_taxas.py" (mesma lógica
de ativos/churn/reentrantes, validada com Daniel em 2026-07-13, incluindo a correção
do bug de rollforward), adaptada para:
  - ler de fact_repurchase_deals (Supabase) em vez do CSV do BigQuery
  - deduplicar por (email, closed_at) antes de calcular — a fonte tem um erro de
    automação que às vezes grava a mesma transação em duas linhas
  - sem pandas (proibido em ingestion/ pelo CLAUDE.md) — reimplementado com
    janelas de atividade por cliente + soma de prefixo, mas matematicamente
    equivalente à simulação mês a mês do script original:
    um cliente com compra no mês P conta como "ativo no fim do mês" para
    m ∈ [P, P+10] (11 meses), e essa janela se estende a cada nova compra
    dentro do período ainda ativo; se a próxima compra vier depois da janela
    fechar, abre-se uma nova janela (evento de reativação).

Nomenclatura confirmada com Daniel em 2026-07-21 (ignora termos da sessão anterior):
  clientes_ativos  = clientes que compraram nos últimos 12 meses − recentes
  taxa_repeticao    = recompra de clientes_ativos ÷ clientes_ativos
  taxa_reativacao   = compras de clientes que estavam inativos ÷ clientes_inativos
  clientes_inativos = clientes com mais de 12 meses sem comprar (contagem no fim do mês)
  clientes_em_risco_m11_m12 = clientes cujo tempo desde a última compra está em 11 ou 12 meses
"""

import logging
from collections import defaultdict
from datetime import date
from typing import Optional

from supabase import Client

logger = logging.getLogger(__name__)

RECENT_WINDOW_MONTHS = 6
CHURN_MONTHS = 12
PAGE_SIZE = 1000


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _add_months(d: date, n: int) -> date:
    idx = d.month - 1 + n
    return date(d.year + idx // 12, idx % 12 + 1, 1)


def _month_diff(a: date, b: date) -> int:
    return (a.year - b.year) * 12 + (a.month - b.month)


def _fetch_deduped_deals(sb: Client) -> list[dict]:
    """Lê fact_repurchase_deals paginado, descarta linhas sem classificação
    (is_first_purchase nulo) e deduplica por (email, closed_at)."""
    raw: list[dict] = []
    offset = 0
    while True:
        resp = (
            sb.table("fact_repurchase_deals")
            .select("id,email,closed_at,is_first_purchase")
            .not_.is_("is_first_purchase", "null")
            .order("id")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        batch = resp.data or []
        raw.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    grouped: dict[tuple[str, str], dict] = {}
    for row in raw:
        key = (row["email"], row["closed_at"])
        is_first = bool(row["is_first_purchase"])
        if key not in grouped:
            grouped[key] = {"email": row["email"], "closed_at": date.fromisoformat(row["closed_at"]), "is_first_purchase": is_first}
        else:
            grouped[key]["is_first_purchase"] = grouped[key]["is_first_purchase"] or is_first

    logger.info({"event": "repurchase_deals_fetched_for_metrics", "raw_rows": len(raw), "deduped_rows": len(grouped)})
    return list(grouped.values())


def _recalcular_primeira_compra(deals: list[dict]) -> dict[str, date]:
    """MIN(closed_at) onde is_first_purchase=True; fallback MIN(closed_at) geral."""
    first_pc: dict[str, date] = {}
    first_all: dict[str, date] = {}
    for d in deals:
        email, closed = d["email"], d["closed_at"]
        if email not in first_all or closed < first_all[email]:
            first_all[email] = closed
        if d["is_first_purchase"] and (email not in first_pc or closed < first_pc[email]):
            first_pc[email] = closed
    return {email: _month_start(first_pc.get(email, all_min)) for email, all_min in first_all.items()}


def _build_customer_purchase_months(deals: list[dict]) -> dict[str, list[date]]:
    per_email: dict[str, set] = defaultdict(set)
    for d in deals:
        per_email[d["email"]].add(_month_start(d["closed_at"]))
    return {email: sorted(months) for email, months in per_email.items()}


def _build_windows(months: list[date]) -> list[tuple[date, date]]:
    """Janelas [inicio, fim] em que o cliente conta como ativo no fim do mês.
    fim = mês_da_compra + 10 (11 meses incluindo o mês da compra); estendida por
    compras seguintes que caiam dentro da janela ainda aberta."""
    windows: list[tuple[date, date]] = []
    start = months[0]
    end = _add_months(months[0], 10)
    for m in months[1:]:
        if m <= end:
            end = _add_months(m, 10)
        else:
            windows.append((start, end))
            start = m
            end = _add_months(m, 10)
    windows.append((start, end))
    return windows


def compute_monthly_metrics(sb: Client) -> list[dict]:
    deals = _fetch_deduped_deals(sb)
    if not deals:
        return []

    first_purchase_month = _recalcular_primeira_compra(deals)
    purchase_months_by_email = _build_customer_purchase_months(deals)

    cutoff_month = _month_start(max(d["closed_at"] for d in deals))
    inicio_month = min(first_purchase_month.values())
    n_months = _month_diff(cutoff_month, inicio_month) + 1
    todos_meses = [_add_months(inicio_month, i) for i in range(n_months)]
    month_index = {m: i for i, m in enumerate(todos_meses)}

    novos_por_mes = [0] * n_months
    for fp_month in first_purchase_month.values():
        novos_por_mes[month_index[fp_month]] += 1

    ativos_diff = [0] * (n_months + CHURN_MONTHS + 2)
    churn_por_mes = [0] * n_months
    reentrantes_por_mes = [0] * n_months
    em_risco_por_mes = [0] * n_months

    for email, months in purchase_months_by_email.items():
        windows = _build_windows(months)
        for w_idx, (w_start, w_end) in enumerate(windows):
            i_start = month_index[w_start]
            i_end = _month_diff(w_end, inicio_month)
            ativos_diff[i_start] += 1
            ativos_diff[i_end + 1] -= 1

            churn_month = _add_months(w_end, 1)
            if churn_month <= cutoff_month:
                churn_por_mes[month_index[churn_month]] += 1

            if w_idx > 0:
                reentrantes_por_mes[i_start] += 1

        # "em risco M11/M12": por compra individual, olhando a próxima compra do cliente
        for i, p in enumerate(months):
            next_p: Optional[date] = months[i + 1] if i + 1 < len(months) else None
            for offset in (11, 12):
                target = _add_months(p, offset)
                if target > cutoff_month:
                    continue
                if next_p is not None and next_p <= target:
                    continue
                em_risco_por_mes[month_index[target]] += 1

    ativos_fim_mes = [0] * n_months
    running = 0
    for i in range(n_months):
        running += ativos_diff[i]
        ativos_fim_mes[i] = running

    recentes = [0] * n_months
    for i in range(n_months):
        lo = max(0, i - RECENT_WINDOW_MONTHS + 1)
        recentes[i] = sum(novos_por_mes[lo:i + 1])

    clientes_ativos = [ativos_fim_mes[i] - recentes[i] for i in range(n_months)]

    cohort_acumulado = [0] * n_months
    running_cohort = 0
    for i in range(n_months):
        running_cohort += novos_por_mes[i]
        cohort_acumulado[i] = running_cohort
    clientes_inativos = [cohort_acumulado[i] - ativos_fim_mes[i] for i in range(n_months)]

    vendas_ativos_nao_recentes = [0] * n_months
    for d in deals:
        if d["is_first_purchase"]:
            continue
        email = d["email"]
        m = _month_start(d["closed_at"])
        idx = month_index.get(m)
        if idx is None:
            continue
        meses_desde_primeira = _month_diff(m, first_purchase_month[email])
        if meses_desde_primeira > RECENT_WINDOW_MONTHS - 1:
            vendas_ativos_nao_recentes[idx] += 1

    rows = []
    for i, m in enumerate(todos_meses):
        inativos_inicio_mes = clientes_inativos[i - 1] if i > 0 else 0
        ativos_inicio_mes = ativos_fim_mes[i - 1] if i > 0 else 0
        taxa_churn = round(churn_por_mes[i] / ativos_inicio_mes, 4) if ativos_inicio_mes else None
        taxa_repeticao = round(vendas_ativos_nao_recentes[i] / clientes_ativos[i], 4) if clientes_ativos[i] else None
        taxa_reativacao = round(reentrantes_por_mes[i] / inativos_inicio_mes, 4) if inativos_inicio_mes else None
        rows.append({
            "month": m.isoformat(),
            "clientes_ativos": clientes_ativos[i],
            "clientes_recentes": recentes[i],
            "clientes_inativos": clientes_inativos[i],
            "clientes_em_risco_m11_m12": em_risco_por_mes[i],
            "clientes_novos": novos_por_mes[i],
            "clientes_reentrantes": reentrantes_por_mes[i],
            "clientes_churn": churn_por_mes[i],
            "taxa_churn": taxa_churn,
            "taxa_repeticao": taxa_repeticao,
            "compras_de_inativos": reentrantes_por_mes[i],
            "taxa_reativacao": taxa_reativacao,
        })

    logger.info({"event": "repurchase_monthly_metrics_computed", "months": len(rows)})
    return rows
