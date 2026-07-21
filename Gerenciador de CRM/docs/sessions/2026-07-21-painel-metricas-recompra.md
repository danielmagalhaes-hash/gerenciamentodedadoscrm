# Sessão 2026-07-21 — Painel de Métricas de Recompra

## Contexto
Segunda fase do projeto: métricas de recompra bem estabelecidas (LTV180, arquivo de clientes ativos, taxa de repetição, taxa de churn, em risco M11/M12, inativos, taxa de reativação), com histórico desde o início de 2025 e um painel novo pra acompanhar.

## Decisão de fonte de dados
Avaliadas 3 opções (planilha manual, API Klaviyo, Shopify+HubSpot via API). Descoberto que o histórico completo (2021-2026) já existia em `fact_order_history_legacy`, e uma sessão anterior (2026-07-13) já tinha validado o modelo de churn/reativação usando um export do BigQuery ("Todos os negócios — Minimal — BQ v2.csv", tabela `silver_deals_minimal`, que já combina Shopify + comercial). Decisão final: reaproveitar esse histórico + uma planilha Google Sheets nova ("Base de Dados", atualizada de madrugada via BigQuery Connected Sheet) para a carga diária daqui pra frente — nada de construir integração nova com Shopify/HubSpot/Klaviyo.

## O que foi construído

**Banco (Supabase):**
- `fact_repurchase_deals` — base única de recompra (Shopify + comercial), separada de `fact_orders`/`fact_order_history_*`. Backfill histórico (456.803 linhas, 2021-03-18 a 2026-06-30) + carga diária da planilha (~13k linhas e crescendo)
- `fact_repurchase_monthly_metrics` — série mensal calculada em Python (não SQL), adaptando sem pandas o script já validado em 13/07 (`modelo_recompra_taxas.py`)
- 4 materialized views (`mv_repurchase_deals_dedup`, `mv_repurchase_customer_first_purchase`, `mv_repurchase_cohort_matrix`, `mv_repurchase_ltv180`) + `vw_repurchase_cohort_sizes` — refresh via RPC `refresh_repurchase_materialized_views()`

**Ingestão:**
- `ingestion/sources/repurchase_deals_sheets.py`, `ingestion/backfill/load_repurchase_deals_historico.py`, `ingestion/analytics/repurchase_monthly_metrics.py`, `ingestion/main_repurchase_deals.py`, `api/cron/repurchase.py` — cron `0 5 * * *`

**Dashboard:**
- Aba "🔁 Recompra" embutida em `dashboard-crm.html` (não página separada — pedido explícito do Daniel, mesmo padrão do Log CRM: lazy-load no primeiro clique, IIFE reusando `_sb`/`fmtInt`/`fmtPct1`/`fmtBRLfull`/`mkChart` globais)
- Conteúdo: 8 cards (7 métricas + LTV180) como foto do mês selecionado por um seletor de "Mês de referência"; seção "Evolução mensal" com seletor de métrica + gráfico único (últimos 12 meses / todo o histórico); LTV180 por safra; matriz de coortes completa (todos os meses, todos os offsets até M63) com células coloridas verde/amarelo/vermelho vs. média da coluna (meses especiais de mar/nov/dez comparam com o mesmo mês em anos anteriores, não com a média geral)

## Nomenclatura oficial (2026-07-21 — ignora termos da sessão de 13/07)
- **Clientes Ativos** = compraram nos últimos 12 meses − Recentes
- **Taxa de Repetição** = recompra de Clientes Ativos ÷ Clientes Ativos (era "tx_reativacao" na sessão anterior)
- **Taxa de Reativação** = compras de clientes que estavam Inativos ÷ Clientes Inativos (métrica nova, não existia antes)
- **Clientes Totais** (ambiguidade da sessão de 13/07) continua em aberto — não foi resolvida, é métrica diferente de Clientes Ativos

## Problemas técnicos encontrados e resolvidos
- BOM UTF-8 no início do `.env` quebrava o `supabase db push`
- Histórico do CLI de migrations dessincronizado do banco remoto (47 migrations aplicadas por fora do CLI) — aplicação passou a ser via SQL Editor / MCP do Supabase
- DELETE de 428k linhas num único statement estourava timeout — resolvido com delete por janelas de 30 dias
- Bug de paginação sem `ORDER BY` (`.range()` sem ordem estável) inflava artificialmente as duplicatas detectadas — **mesmo bug existe, não corrigido, em 3 funções de `ingestion/db/writers.py`** (ver ARCHITECTURE.md § Pontos frágeis)
- `anon` key tem `statement_timeout` mais curto que `service_role` — views com JOIN pesado precisaram virar materialized views (3 conversões: dedup+first_purchase, cohort_matrix, ltv180)
- Consulta de mais de 1000 linhas via PostgREST precisa paginação real no cliente (`.range()` sozinho não basta)
- MCP do Supabase: primeira tentativa de OAuth falhou ("Unrecognized client_id"), segunda tentativa funcionou

## Pendências pro Daniel
1. **Confirmar amanhã** (22/07) se o cron `/api/cron/repurchase` rodou com sucesso às 05h UTC — checar `cron_logs`
2. Decidir se/quando corrigir o bug de paginação em `ingestion/db/writers.py` (não urgente, não afeta recompra)
3. Resolver a ambiguidade de "Clientes Totais" da sessão de 13/07, se ainda for relevante
