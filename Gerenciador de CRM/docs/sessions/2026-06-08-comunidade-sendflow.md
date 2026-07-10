# Sessão 2026-06-08 — Canal Comunidade (Sendflow)

## O que foi feito

### Análise da API Sendflow
- Leitura completa da documentação em `https://sendflow.pro/sendapi`
- Mapeamento das seções: Campanhas (releases), Analytics, Actions, Messages, Templates
- Descoberta chave: o endpoint `GET /sendapi/actions?type=sendMessages` entrega o count de disparos — viabiliza o KPI Receita/Disparo sem mudar o PRODUCT.md
- Rate limit identificado: 10s obrigatórios entre chamadas de listagem de ações

### Banco de dados (aplicado em produção)
- `fact_community_actions` — uma linha por ação de disparo (sendMessages) por release
- `fact_community_analytics` — entradas, saídas e cliques por release por dia
- `vw_community_daily` — view que agrega disparos, membros, cliques e receita com Receita/Disparo calculado
- Migrations aplicadas via MCP Supabase diretamente no projeto `aczvusdzfrmborvvfqib`

### Código Python criado
- `ingestion/models/sendflow_models.py` — Pydantic models (Release, Group, Analytics, Action)
- `ingestion/sources/sendflow.py` — 4 funções de fetch com throttle de 10s nas ações
- `ingestion/community_daily.py` — runner com `run_yesterday()` e `run_for_period()`, backfill desde 2026-01-01
- `ingestion/db/writers.py` — +3 funções: `upsert_community_assets`, `upsert_community_analytics`, `upsert_community_actions`, `get_sendflow_asset_map`
- `api/cron/community.py` — entry point do cron
- `api/cron/app.py` — nova rota `/api/cron/community` + backfill `/admin/backfill/community?since=`
- `vercel.json` — cron diário às 05:00 BRT (08:00 UTC)

## Bloqueio pendente

A `SENDFLOW_API_KEY` no `.env` retorna HTTP 401 da API. A chave tem 49 caracteres, está limpa (sem espaços), mas não é reconhecida pelo Sendflow.

**Ação necessária amanhã:** acessar o painel do Sendflow → Configurações → API → copiar a chave correta e atualizar o `.env`.

Após corrigir a chave:
1. Rodar: `python -m ingestion.community_daily --since 2026-01-01`
2. Verificar dados em `fact_community_actions` e `fact_community_analytics` no Supabase
3. Confirmar que `vw_community_daily` retorna dados corretos
4. Subir dashboard local para validação visual
5. Fazer push para Vercel

## Contexto técnico
- 2 releases ativas na conta Sendflow, ~300 ações totais
- Tempo estimado de backfill: ~40s (3 páginas × 10s throttle + estrutura)
- Separação total do canal wpp_campaign (Vekta): tabelas, scripts e cron independentes
