# Sessão 2026-06-12 — WPP Fluxo receita, painel UTM, Sendflow dual-key, Comunidade backfill

## O que foi feito nesta sessão

Sessão longa com seis entregas independentes, na ordem em que foram realizadas.

---

## 1. Tabela WPP Fluxo com colunas de receita e rankings simplificados

### Problema
A tabela de Detalhamento do WPP Fluxo não exibia receita. Rankings usavam lógica de mock.

### Solução
`renderWppFlowTable(key, leadsRows, revRows, color)` reescrita com:
- Colunas: Fluxo · Disparos · Receita · Receita/Disparo · % do canal
- Rankings: Top 5 por Receita e Top 5 por Receita/Disparo, calculados a partir de `vw_wpp_flow_revenue`
- View `vw_wpp_flow_revenue` usa `DISTINCT ON (utm_campaign)` para evitar contagem dupla quando múltiplas alia_campanha compartilham a mesma utm_campaign

### Migration
`20260612000036_wpp_alia_campanha_utm_and_pending_view.sql`:
- `ALTER TABLE dim_wpp_alia_campanha_mapping ADD COLUMN utm_campaign TEXT`
- Backfill de `utm_campaign` a partir de `dim_wpp_origem_mapping` via `flow_name`
- `DROP/CREATE vw_wpp_flow_revenue` com DISTINCT ON
- `CREATE vw_wpp_flow_utm_pending` (fluxos sem utm_campaign configurada)

---

## 2. Painel de conferência UTM em WPP Fluxo

### Problema
Quando um novo fluxo WPP aparece sem `utm_campaign` configurada, não havia como mapear pelo dashboard. A tab WPP Fluxo exibia aviso de dados fictícios que não era mais aplicável.

### Solução
- Substituiu `fetchWppFlowUnknown()` por `fetchWppFlowUtmPending()` consultando `vw_wpp_flow_utm_pending`
- `renderWppFlowUtmPanel(pendingRows)` exibe tabela de fluxos pendentes com campo de input por linha
- `saveWppUtmConfig(i)` chama `POST /admin/wpp-utm-config` para gravar em `dim_wpp_alia_campanha_mapping`
- `ignoreWppUtm(i)` marca a entrada como ignorada (sem utm)
- Aviso "⚠️ Dados parcialmente fictícios" removido do WPP Fluxo (dados são reais)
- Endpoint `POST /admin/wpp-utm-config` adicionado em `api/cron/app.py`

---

## 3. Sendflow com fallback entre duas API keys

### Problema
A chave primária do Sendflow estava expirada/rejeitada (401). O código anterior só tratava 403/429.

### Solução
`ingestion/sources/sendflow.py` reescrito com:
- `_KEY_ERROR_CODES = {401, 403, 429}` → troca de key imediatamente
- `_SERVER_ERROR_CODES = {500, 502, 503, 504}` → retry com backoff (3s, 7s, 15s)
- `_get_with_key_fallback(url, params)` itera pelas keys disponíveis com lógica separada por tipo de erro
- `_api_keys()` lê `SENDFLOW_API_KEY` + `SENDFLOW_API_KEY_2` (opcional) do ambiente
- Segunda key adicionada em `.env` e em `.env.example` como placeholder
- Segunda key também configurada nas variáveis da Vercel

---

## 4. Filtro de releases "meteórico" na Comunidade

### Problema
As releases do lançamento "meteórico" poluíam os dados da Comunidade WPP, que é um canal separado (não relacionado a lançamentos).

### Solução
`ingestion/community_daily.py`:
- `_IGNORED_KEYWORDS = {"meteorico"}`
- `_is_ignored_release(name)` normaliza unicode (NFD) e remove acentos antes de comparar
- Releases com "meteórico"/"METEÓRICO"/variantes são filtradas antes de qualquer upsert

---

## 5. Backfill da Comunidade a partir de 09/06

### O que foi feito
Após reativar o Sendflow (keys configuradas na Vercel), rodou backfill via endpoint:
```
POST /api/cron/sendflow_community_daily
body: {"since": "2026-06-09"}
```
Executado via `curl` após aguardar deploy da Vercel com as novas keys.
Todas as releases ativas foram processadas; releases meteórico ignoradas automaticamente.

---

## 6. "Histórico completo" no seletor de período

### Problema
Dados anteriores a 08/06 não apareciam no dashboard da Comunidade porque o período padrão era "7d". O seletor não tinha opção para ver todo o histórico.

### Solução
- Adicionada `<option value="all">Histórico completo</option>` no seletor de período
- `getDateRange('all')` retorna `{start: '2026-01-01', end: hoje}`

---

## 7. Aviso de dados fictícios reativado no WPP Campanha

No fechamento da sessão, o aviso foi restabelecido em WPP Campanha:
> ⚠️ **Dados parcialmente fictícios** — apenas **Receita** e **Sessões** são reais. Disparos, rankings e demais volumes ainda não são ingeridos da Vekta.

O aviso é gerado dinamicamente em `channelHTML()` apenas quando `key === 'wc'`.

---

## Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `dashboard-crm.html` | `renderWppFlowTable`, painel UTM WPP, opção "Histórico completo", aviso WPP Campanha |
| `api/cron/app.py` | Endpoint `POST /admin/wpp-utm-config` |
| `ingestion/sources/sendflow.py` | Reescrito com fallback dual-key |
| `ingestion/community_daily.py` | Filtro de releases meteórico via unicode |
| `.env.example` | Placeholder `SENDFLOW_API_KEY_2` |
| `supabase/migrations/20260612000036_wpp_alia_campanha_utm_and_pending_view.sql` | Nova migration |

## Commits

- `eec8893` feat: tabela WPP Fluxo com colunas de receita e rankings simplificados
- `b48e8e0` feat: painel de conferência UTM em WPP Fluxo
- `bb07e92` feat: Sendflow com fallback entre duas API keys em rate limit
- `3d21b10` fix: ignora releases meteórico na ingestão da Comunidade
- `28c6440` fix: Sendflow fallback inclui 401 (key inválida) além de 403/429
- `1dd0934` feat: adiciona opção Histórico completo no seletor de período
- `fd363b6` feat: reativa aviso de dados fictícios no WPP Campanha

## Estado do sistema ao final

| Canal | Receita | Sessões | Disparos/Volume |
|---|---|---|---|
| E-mail Fluxo | Real | Real | Real (Klaviyo) |
| E-mail Campanha | Real | Real | Real (Klaviyo) |
| WPP Fluxo | Real | Real | Real (leads_webhook Vekta) |
| Comunidade WPP | Real | Real | Real (Sendflow — duas keys ativas) |
| WPP Campanha | Real | Real | Fictícios (Vekta campanha não integrado) |
