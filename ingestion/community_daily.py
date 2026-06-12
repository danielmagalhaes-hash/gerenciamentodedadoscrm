"""
Ingestão diária de métricas da Comunidade WhatsApp (Sendflow).

Grava em:
  dim_assets              ← releases (campanhas) do Sendflow
  fact_community_actions  ← ações de disparo por release
  fact_community_analytics ← entradas, saídas e cliques por release por dia

Modos de uso:
  python -m ingestion.community_daily              # D-2 a D-1 (cron normal)
  python -m ingestion.community_daily --backfill   # histórico desde 2026-01-01
  python -m ingestion.community_daily --since 2026-01-01  # data inicial customizada
"""

import argparse
import logging
import sys
import unicodedata
from datetime import date, timedelta

from dotenv import load_dotenv

from ingestion.db import writers
from ingestion.db.client import get_supabase_client
from ingestion.sources.sendflow import (
    fetch_release_actions,
    fetch_release_analytics,
    fetch_release_groups,
    fetch_releases,
)

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

BACKFILL_START = date(2026, 1, 1)

# Releases cujo nome contém estas strings (após normalização) são ignoradas
_IGNORED_KEYWORDS = {"meteorico"}


def _is_ignored_release(name: str) -> bool:
    """Retorna True para releases que nunca devem ser ingeridas (ex: Meteórico)."""
    normalized = unicodedata.normalize("NFD", name.lower())
    ascii_name = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return any(kw in ascii_name for kw in _IGNORED_KEYWORDS)


def run_for_period(
    date_from: date,
    date_to: date,
    release_id_filter: str | None = None,
) -> None:
    logger.info({
        "event": "community_run_start",
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "release_id_filter": release_id_filter,
    })

    sb = get_supabase_client()
    channel_ids = writers.get_channel_ids(sb)
    channel_id = channel_ids["wpp_community"]

    # 1. Sync de estrutura: releases → dim_assets (ignora releases meteórico)
    releases = fetch_releases()
    active_releases = [r for r in releases if not _is_ignored_release(r.name)]
    ignored = [r.name for r in releases if _is_ignored_release(r.name)]
    if ignored:
        logger.info({"event": "community_releases_ignored", "names": ignored})
    writers.upsert_community_assets(sb, active_releases, channel_ids)
    releases = active_releases
    if release_id_filter:
        releases = [r for r in releases if r.id == release_id_filter]
        if not releases:
            raise ValueError(f"release_id não encontrado: '{release_id_filter}'")

    # Mapa release_id → asset_uuid após upsert
    asset_map = writers.get_sendflow_asset_map(sb)

    total_analytics = 0
    total_actions = 0

    for release in releases:
        # Analytics inclui releases arquivadas (histórico preservado)
        try:
            analytics = fetch_release_analytics(release.id)
            groups = fetch_release_groups(release.id)
            total_members = sum(g.participants_amount for g in groups)
            count = writers.upsert_community_analytics(
                sb=sb,
                release_id=release.id,
                asset_id=asset_map.get(release.id),
                channel_id=channel_id,
                analytics=analytics,
                total_members=total_members,
                since=date_from,
                until=date_to,
            )
            total_analytics += count
        except Exception as e:
            # Erro na release não interrompe as demais (retry já foi tentado no cliente).
            logger.warning({
                "event": "community_analytics_error",
                "release_id": release.id,
                "error": str(e),
            })
            continue

        # Ações de disparo no período
        if not release.archived:
            try:
                actions = fetch_release_actions(
                    release.id, since=date_from, until=date_to
                )
                count = writers.upsert_community_actions(
                    sb, actions, asset_map, channel_id
                )
                total_actions += count
            except Exception as e:
                # 403 ou qualquer erro na API de ações não derruba o cron:
                # analytics e outras releases continuam sendo processadas.
                logger.warning({
                    "event": "community_actions_error",
                    "release_id": release.id,
                    "error": str(e),
                })

    logger.info({
        "event": "community_run_done",
        "analytics_rows": total_analytics,
        "action_rows": total_actions,
    })


def run_yesterday() -> None:
    """Rebusca D-2 a D-1 para recuperar automaticamente falhas do dia anterior."""
    two_days_ago = date.today() - timedelta(days=2)
    yesterday = date.today() - timedelta(days=1)
    run_for_period(two_days_ago, yesterday)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingestão de métricas da comunidade Sendflow"
    )
    parser.add_argument(
        "--backfill", action="store_true",
        help=f"Carrega histórico completo desde {BACKFILL_START}",
    )
    parser.add_argument(
        "--since", type=str, default=None,
        help="Data inicial customizada (YYYY-MM-DD) — carrega até ontem",
    )
    parser.add_argument(
        "--release-id", type=str, default=None,
        help="Limita a execução a uma única release (ID do Sendflow)",
    )
    args = parser.parse_args()

    date_to = date.today() - timedelta(days=1)
    release_id_filter = args.release_id or None

    if args.backfill:
        run_for_period(BACKFILL_START, date_to, release_id_filter)
    elif args.since:
        run_for_period(date.fromisoformat(args.since), date_to, release_id_filter)
    else:
        run_yesterday()


if __name__ == "__main__":
    main()
