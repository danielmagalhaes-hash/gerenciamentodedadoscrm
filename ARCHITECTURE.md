# ARCHITECTURE.md — Dashboard CRM · Minimal Club

> Mapa vivo do sistema. Lido em TODA sessão. Atualizado ao FIM de toda sessão.
> Última atualização: 2026-06-08

---

## 1. Visão geral em 1 página

O sistema é composto por três partes que se encaixam como esteiras de uma fábrica.

**Parte 1 — Ingestão (esteira de entrada):** Scripts Python são executados automaticamente via **Vercel Cron Jobs**. Cada cron é responsável por uma fonte: Shopify a cada 35 minutos, Google Sheets a cada hora, E-mail Fluxo todo dia às 04:00 BRT, E-mail Campanha às 00:30 BRT, Formulários às 06:00 BRT. Os resultados de cada execução são registrados na tabela `cron_logs`. Para recuperação de dados perdidos existe o endpoint `/admin/backfill/<job>` acessível via browser. Os dados de sessão (GA4 via BigQuery) chegam por um caminho diferente: uma planilha Google Sheets atualizada de hora em hora recebe o export do BigQuery, e o script Python a lê via CSV público.

**Parte 2 — Banco de dados (coração do sistema):** O Supabase (PostgreSQL) armazena tudo. Tabelas de dimensão guardam referências estáticas (canais, ativos, formulários). Tabelas de fatos acumulam os dados diários de cada fonte. Views calculadas combinam essas tabelas e entregam os KPIs prontos — receita por canal, funil, leads, saúde da base — sem que o frontend precise fazer nenhum cálculo.

**Parte 3 — Dashboard (esteira de saída):** O arquivo `dashboard-crm.html` — com layout e visual aprovados — conecta ao Supabase via `supabase-js`. Cada seção lê a view ou tabela correspondente diretamente. O acesso é protegido por autenticação server-side via Flask + JWT Supabase (cookie `sb_token`). **AUTH_ENABLED está temporariamente em False** — reativar em breve. O dashboard está deployado na Vercel em **`gerenciadorcrm.vercel.app`** (projeto `gerenciamentodedadoscrmoficial`).

O resultado: dados de Shopify, Klaviyo e GA4 aparecem unificados num único painel, atualizados automaticamente. Vekta (WhatsApp) e Sendflow (Comunidade) ainda sem integração — aguardam Fase 2.

---

## 2. Diagrama de módulos

### Módulos ativos em produção

#### ingestion-shopify
- **Responsabilidade:** Buscar pedidos pagos do Shopify e gravá-los em `fact_orders`
- **Entry point:** `api/cron/revenue.py` → `ingestion/main.py:run_smart_shopify_ingestion()`
- **Fontes:** `ingestion/sources/shopify.py`, `ingestion/models/shopify_models.py`
- **Cron:** `*/35 * * * *` — a cada 35 minutos
- **Estado:** ✅ ativo — 103 execuções ok nos últimos 7 dias

#### ingestion-sessions
- **Responsabilidade:** Ler CSV do Google Sheets (export BigQuery) e gravar em `fact_sessions` e `fact_sessions_utm`
- **Entry point:** `api/cron/sessions.py` → `ingestion/main.py:run_sheets_ingestion()`
- **Fontes:** `ingestion/sources/google_sheets.py`, `ingestion/models/sheets_models.py`
- **Cron:** `10 * * * *` — a cada hora aos :10
- **Estado:** ✅ ativo

#### ingestion-email-structure
- **Responsabilidade:** Sincronizar estrutura de fluxos ativos (fluxos + e-mails individuais) do Klaviyo para `dim_assets` e `dim_asset_items`
- **Entry point:** `api/cron/email_structure.py` → `ingestion/flow_structure_daily.py:run_structure_sync()`
- **Fontes:** `ingestion/sources/klaviyo_structure_sync.py`
- **Cron:** `0 6 * * *` — todo dia às 03:00 BRT (06:00 UTC) — 1h antes do email_flow
- **maxDuration:** 600s
- **Por que existe:** elimina ~500 chamadas GET de estrutura do cron email_flow, que causavam 429s e timeout na Vercel
- **Estado:** ✅ ativo

#### ingestion-email-flow
- **Responsabilidade:** Buscar métricas diárias de e-mails de fluxos Klaviyo e gravar em `flow_email_metrics`
- **Entry point:** `api/cron/email_flow.py` → `ingestion/flow_metrics_daily.py:run_yesterday()`
- **Fontes:** `ingestion/sources/klaviyo_flow_metrics.py`
- **Cron:** `0 7 * * *` — todo dia às 04:00 BRT (07:00 UTC)
- **Lookback:** D-2 a D-1 (recupera automaticamente se falhou no dia anterior)
- **maxDuration:** 900s (atualizado de 800s)
- **Estratégia de chamadas:** por fluxo × 3 métricas com `by=['$message']` — ~99 POSTs por execução (~75s). Versão anterior fazia 1 POST por mensagem × 3 métricas (~1.566 chamadas, causava timeout)
- **Depende de:** cron `email_structure` ter rodado antes para popular `dim_asset_items`
- **Estado:** ✅ ativo

#### ingestion-email-campaign
- **Responsabilidade:** Buscar métricas diárias de campanhas Klaviyo e gravar em `campaign_email_metrics`
- **Entry point:** `api/cron/email_campaign.py` → `ingestion/campaign_metrics_daily.py:run_yesterday()`
- **Fontes:** `ingestion/sources/klaviyo_campaign_metrics.py`
- **Cron:** `30 3 * * *` — todo dia às 00:30 BRT (03:30 UTC)
- **Lookback:** D-2 a D-1
- **Estado:** ✅ ativo

#### ingestion-forms
- **Responsabilidade:** Buscar métricas de formulários + saúde da base Klaviyo → `fact_lead_captures`, `dim_forms`, `fact_email_health`
- **Entry point:** `api/cron/forms.py` → `ingestion/main.py:run_forms_ingestion()`
- **Fontes:** `ingestion/sources/klaviyo.py` (fetch_forms, fetch_active_base_count, fetch_form_metrics_since)
- **Cron:** `0 9 * * *` — todo dia às 06:00 BRT (09:00 UTC)
- **Lookback:** sempre rebusca D-1 completo (dados Klaviyo têm lag de ~24h)
- **Estado:** ✅ ativo

#### vercel-crons
- **Responsabilidade:** Orquestrar e executar todos os crons automaticamente
- **Configuração:** `vercel.json` — 5 crons + routing + maxDuration
- **Projeto Vercel:** `gerenciamentodedadoscrmoficial` → `gerenciadorcrm.vercel.app`
- **Estado:** ✅ ativo

#### backfill-admin
- **Responsabilidade:** Permitir recuperação manual de dados perdidos via browser
- **Entry point:** `api/cron/app.py` rota `/admin/backfill/<job>`
- **Jobs disponíveis:** `email_structure`, `email_flow`, `email_campaign`, `sessions`, `forms`, `revenue`
- **Parâmetros:** `?since=YYYY-MM-DD`, `?until=YYYY-MM-DD`
- **Exemplo:** `https://gerenciadorcrm.vercel.app/admin/backfill/email_flow?since=2026-06-02`
- **Estado:** ✅ ativo (acessível enquanto AUTH_ENABLED=False)

#### supabase-schema
- **Responsabilidade:** Definir e versionar schema do banco via migrations SQL
- **Localização:** `supabase/migrations/` — 32 migrations aplicadas
- **Estado:** ✅ ativo

#### dashboard-frontend
- **Responsabilidade:** Renderizar dados do Supabase no dashboard HTML
- **Arquivo:** `dashboard-crm.html`
- **Lê:** views `vw_*` exclusivamente — incluindo `vw_flow_email_assets` e `vw_flow_email_items` para E-mail Fluxo, `fact_orders` para receita por fluxo
- **Estado:** ✅ ativo

### Módulos planejados (Fase 2)

#### ingestion-vekta (não iniciado)
- **Responsabilidade:** Buscar métricas de WhatsApp Fluxo e Campanha → `fact_wpp_sends`
- **Bloqueio:** confirmar se Vekta tem API pública

#### ingestion-sendflow (não iniciado)
- **Responsabilidade:** Buscar dados da Comunidade WhatsApp → `fact_community_members`, `fact_community_sends`
- **Bloqueio:** confirmar acesso à API Sendflow

### Diagrama (ASCII)

```
[Shopify API]    ──→ [Cron: revenue, a cada 35min]           ──┐
[Google Sheets]  ──→ [Cron: sessions, a cada 1h]             ──┤
[Klaviyo API]    ──→ [Cron: email_structure, 03:00 BRT] ──→ dim_assets/dim_asset_items
                 ──→ [Cron: email_flow, 04:00 BRT] (lê ↑ do banco) ──┤→ [Supabase PostgreSQL]
                 ──→ [Cron: email_campaign, 00:30 BRT]       ──┤    │
                 ──→ [Cron: forms, 06:00 BRT]                ──┘    │ [views vw_*]
                                                                      │ [tabelas diretas]
[Input manual]   ──────────────────────────────────────────────→ [fact_monthly_goals]
[Admin backfill] ──→ [/admin/backfill/<job>]                 ──→     │
                                                                      ↓
                                                            [api/cron/app.py Flask]
                                                            (auth JWT Supabase — temp. desativado)
                                                                      │
                                                                      ↓
                                                            [dashboard-crm.html]
                                                            (supabase-js lê views e tabelas)
```

---

## 3. Entidades e modelo de dados

### Tabelas em produção com dados ativos

#### dim_channels
Tabela de referência dos 5 canais. Criada uma vez, raramente alterada.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| name | text | Ex: "E-mail Fluxo" |
| slug | text | Ex: "email_flow" — UNIQUE |
| utm_source | text | Ex: "email" |
| utm_medium | text | Ex: "flow" — null para Comunidade |
| primary_kpi | text | "receita_inscrito" ou "receita_disparo" |
| created_at | timestamptz | — |

- **Slugs canônicos (nunca mudam sem ADR):** `email_flow`, `email_campaign`, `wpp_flow`, `wpp_campaign`, `wpp_community`
- **RLS:** SELECT para anon; sem escrita externa

---

#### dim_assets
Ativos pai: fluxos e campanhas sincronizados das ferramentas de origem.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| external_id | text | ID no Klaviyo/Vekta/Sendflow |
| channel_id | uuid | FK → dim_channels |
| name | text | Nome na ferramenta de origem |
| type | text | "flow" ou "campaign" |
| is_active | boolean | false = desativado na ferramenta |
| source_tool | text | "klaviyo" \| "vekta" \| "sendflow" |
| created_at / updated_at / ingested_at | timestamptz | — |

- **Índices:** `(external_id, source_tool)` UNIQUE
- **RLS:** SELECT anon; INSERT/UPDATE service_role

---

#### dim_asset_items
Ativos filho: e-mails individuais dentro de fluxos/campanhas.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| external_id | text | ID na ferramenta de origem |
| asset_id | uuid | FK → dim_assets |
| name | text | Subject line ou preview do template |
| type | text | "email" ou "wpp_template" |
| position | integer | Posição no fluxo (1, 2, 3…) |
| created_at / updated_at / ingested_at | timestamptz | — |

- **Índices:** `(external_id, type)` UNIQUE

---

#### dim_forms
Formulários e popups de captação de leads do Klaviyo.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| external_id | text | Klaviyo Form ID — UNIQUE |
| name | text | Nome do formulário |
| type | text | "popup" \| "form" \| "embed" |
| position | text | Ex: "Home", "Footer" |
| is_active | boolean | — |
| created_at / ingested_at | timestamptz | — |

---

#### fact_orders
Pedidos pagos do Shopify com atribuição de canal por UTM.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| order_id | text | Shopify Order ID — UNIQUE |
| order_date | date | Data do pedido |
| revenue_brl | numeric(12,2) | Valor em reais |
| attributed_channel_id | uuid | FK → dim_channels — null se sem UTM de CRM |
| utm_source / utm_medium / utm_campaign / utm_term / utm_content | text | Valores brutos da UTM |
| shopify_customer_id | text | ID do cliente |
| is_first_purchase | boolean | true se orders_count = 1 |
| ingested_at | timestamptz | — |

- **Invariante:** `revenue_brl > 0`; pedidos sem UTM de CRM ficam com `attributed_channel_id = null`

---

#### fact_sessions
Sessões, ATC e BCO por canal por dia — origem: Google Sheets / BigQuery.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| date | date | — |
| channel_id | uuid | FK → dim_channels |
| sessions | integer | — |
| add_to_cart | integer | ATC |
| begin_checkout | integer | BCO |
| orders | integer | Compras atribuídas |
| revenue_brl | numeric | Receita atribuída |
| ingested_at | timestamptz | — |

- **Índices:** `(date, channel_id)` UNIQUE

---

#### fact_sessions_utm
Versão granular de `fact_sessions` — quebrada por UTM completa. Alimentada pelo cron de sessões. **Reservada para Fase 3 (mapeamento de UTMs)** — não consumida atualmente.

---

#### flow_email_metrics
Métricas diárias por e-mail individual de fluxo Klaviyo — **tabela principal do E-mail Fluxo**.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| flow_id | text | ID do fluxo no Klaviyo |
| flow_name | text | Nome do fluxo |
| message_id | text | ID da flow-message |
| message_name | text | Nome da mensagem |
| data | date | Data da métrica |
| email_enviado | integer | Disparos |
| email_aberto | integer | Aberturas |
| email_clicado | integer | Cliques |
| updated_at | timestamptz | — |

- **Índices:** `(message_id, data)` UNIQUE
- **Lida por:** dashboard direto + `vw_email_channel_daily`

---

#### campaign_email_metrics
Métricas diárias por campanha Klaviyo — **tabela principal do E-mail Campanha**. Estrutura idêntica a `flow_email_metrics`.

- **Lida por:** `vw_campaign_email_metrics`

---

#### flow_utm_config
Mapeamento de `flow_name` → `utm_campaign` para atribuição de receita por fluxo.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| flow_name | text | Join com flow_email_metrics |
| utm_campaign | text | Valor de utm_campaign nos links |

- **Lida por:** dashboard (cálculo de receita por fluxo)

---

#### fact_lead_captures
Performance de formulários e popups por dia — origem: Klaviyo Forms API.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| date | date | — |
| form_id | uuid | FK → dim_forms |
| impressions | integer | Visualizações |
| submissions | integer | Inscrições |
| ingested_at | timestamptz | — |

- **Índices:** `(date, form_id)` UNIQUE
- **Lida por:** `vw_leads_daily`, `vw_form_performance`

---

#### fact_email_health
Saúde da base de e-mail por canal — origem: Klaviyo API (segmento Engaged 90d).

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| date | date | — |
| channel_id | uuid | FK → dim_channels (apenas e-mail) |
| active_base_count | integer | Engajados 90d |
| delivery_rate / bounce_rate / spam_complaint_rate / opt_out_rate | numeric | Taxas |
| ingested_at | timestamptz | — |

- **Estado:** dados gravados pelo cron `forms` — **ainda não conectada ao dashboard** (dashboard usa mock). Próxima versão substituirá o mock por `vw_email_health`.

---

#### cron_logs
Registro de execuções dos cron jobs — usado pelo banner de alertas no dashboard.

| Coluna | Tipo | Notas |
|---|---|---|
| id | uuid | PK |
| job | text | revenue, sessions, email_flow, email_campaign, forms |
| status | text | "ok" ou "error" |
| message | text | Mensagem de erro |
| ran_at | timestamptz | Timestamp da execução |

---

### Tabelas para fases futuras (vazias)

| Tabela | Fase | Aguarda |
|---|---|---|
| `fact_wpp_sends` | 2 | Integração Vekta |
| `fact_wpp_subscribers` | 2 | Integração Vekta |
| `fact_community_members` | 2 | Integração Sendflow |
| `fact_community_sends` | 2 | Integração Sendflow |
| `fact_monthly_goals` | 2 | Input manual das metas (estrutura pronta, dashboard tem placeholder) |
| `dim_utm_mappings` | 3 | Classificação manual de UTMs não reconhecidas |
| `flow_utm_pending` | 3 | Processamento de UTMs pendentes (dashboard já escreve, nada processa) |

---

### Views em produção

| View | O que entrega | Lida por |
|---|---|---|
| `vw_channel_daily` | Receita, compras, sessões, conversão, TKM, RPS por canal e dia | Dashboard (Resumo + todas as abas de canal) |
| `vw_revenue_first_repeat` | Receita por (data, tipo) — 1ª compra vs recompra | Dashboard (gráfico diário 1ª vs Recompra) |
| `vw_revenue_by_channel_type` | Receita por (data, canal, tipo) | Dashboard (filtro Tipo de Cliente) |
| `vw_leads_daily` | Leads por dia por formulário | Dashboard (Captação de Leads) |
| `vw_form_performance` | Performance acumulada por formulário | Dashboard (tabela Formulários e Popups) |
| `vw_email_channel_daily` | Disparos, aberturas, cliques por canal de e-mail por dia | Dashboard (Métricas específicas E-mail Fluxo/Campanha) |
| `vw_campaign_email_metrics` | Performance por campanha com receita atribuída | Dashboard (tabela E-mail Campanha) |
| `vw_flow_email_assets` | Disparos/aberturas/cliques por `(flow_id, flow_name, data)` + `utm_campaign` via JOIN com `flow_utm_config` | Dashboard (Detalhamento por Fluxo, Rankings, Receita/Inscrito) |
| `vw_flow_email_items` | Disparos/aberturas/cliques por `(message_id, message_name, data)` — para drill-down por e-mail dentro do fluxo | Dashboard (tabela de e-mails ao clicar num fluxo, cálculo de inscritos) |

### Views prontas mas não conectadas ao dashboard (próxima versão)

| View | O que entrega | Quando conectar |
|---|---|---|
| `vw_email_health` | Saúde da base (entregabilidade, base ativa) | Quando substituir o mock de saúde da base no Resumo CRM |
| `vw_pace_vs_goals` | % atingido, projeção de fechamento vs meta | Quando `fact_monthly_goals` for preenchida |

### Funções do banco

| Função | Tipo | Uso |
|---|---|---|
| `rls_auto_enable` | utilitário | Ativa RLS automaticamente em novas tabelas |
| `fn_check_wpp_subscriber_asset` | trigger | Validação de subscribers WhatsApp — ativa quando Fase 2 entrar |

---

## 4. Fluxos de dados

### Fluxo 1 — Cron de receita (Shopify, a cada 35min)

1. **Trigger:** Vercel Cron → `GET /api/cron/revenue`
2. **Executa:** `run_smart_shopify_ingestion()` — busca pedidos desde MAX(order_date) - 2 dias
3. **Validações:** apenas `financial_status = "paid"`; UTM mapeada para `channel_id`
4. **Grava:** upsert em `fact_orders` por `order_id`
5. **Log:** `cron_logs` com status ok/error

---

### Fluxo 2 — Cron de sessões (Google Sheets, horário)

1. **Trigger:** Vercel Cron → `GET /api/cron/sessions`
2. **Executa:** `run_sheets_ingestion()` — lê CSV completo de `GOOGLE_SHEETS_CSV_URL`
3. **Validações:** colunas obrigatórias, parse de data BR, tipos Pydantic
4. **Grava:** upsert em `fact_sessions` + `fact_sessions_utm` por `(date, channel_id)`
5. **Log:** `cron_logs`

---

### Fluxo 3a — Cron de estrutura de fluxos (Klaviyo, diário às 03h BRT)

1. **Trigger:** Vercel Cron → `GET /api/cron/email_structure`
2. **Executa:** `run_structure_sync()` — busca fluxos ativos e seus e-mails individuais
3. **Processo:** lista fluxos `status=live` → para cada fluxo, busca flow-actions → flow-messages
4. **Grava:** upsert em `dim_assets` (fluxos) e `dim_asset_items` (e-mails) por `external_id`
5. **Duração:** ~8-10 minutos — maxDuration: 600s

### Fluxo 3b — Cron de e-mail fluxo (Klaviyo, diário às 04h BRT)

1. **Trigger:** Vercel Cron → `GET /api/cron/email_flow`
2. **Executa:** `run_yesterday()` — busca D-2 a D-1
3. **Processo:** lê estrutura de `dim_assets` + `dim_asset_items` (zero chamadas GET ao Klaviyo) → agrupa mensagens por fluxo → para cada fluxo × 3 métricas, chama `metric-aggregates` com `by=['$message']` recebendo breakdown de todas as mensagens numa chamada
4. **Grava:** upsert em `flow_email_metrics` por `(message_id, data)`
5. **Duração:** ~75s (~99 chamadas POST) — maxDuration: 900s

---

### Fluxo 4 — Cron de e-mail campanha (Klaviyo, diário às 00h30 BRT)

1. **Trigger:** Vercel Cron → `GET /api/cron/email_campaign`
2. **Executa:** `run_yesterday()` — busca D-2 a D-1
3. **Grava:** upsert em `campaign_email_metrics` por `(message_id, data)`

---

### Fluxo 5 — Cron de formulários (Klaviyo, diário às 06h BRT)

1. **Trigger:** Vercel Cron → `GET /api/cron/forms`
2. **Executa:** `run_forms_ingestion()` — sempre rebusca desde D-1 (corrige parciais do Klaviyo)
3. **Grava:** `dim_forms` + `fact_lead_captures` + `fact_email_health`

---

### Fluxo 6 — Consulta ao dashboard (tempo real, sob demanda)

1. **Trigger:** usuário abre `gerenciadorcrm.vercel.app` ou aplica filtro
2. **Auth:** Flask verifica cookie `sb_token` (temporariamente desativado)
3. **Queries:** `supabase-js` consulta views e tabelas com filtros de data e channel_slug
4. **Renderização:** JavaScript recebe JSON e renderiza — sem cálculo de KPI no frontend

---

### Fluxo 7 — Backfill manual (sob demanda)

1. **Trigger:** abrir URL no browser → `GET /admin/backfill/<job>?since=YYYY-MM-DD`
2. **Executa:** a função de ingestão correspondente com a data informada
3. **Exemplos de uso:**
   - `/admin/backfill/email_flow?since=2026-06-02` — recupera dia específico
   - `/admin/backfill/forms?since=2026-06-02` — corrige dados parciais
   - `/admin/backfill/sessions` — refaz última leitura do Sheets
4. **Log:** registra em `cron_logs` ao terminar

---

## 5. Decisões arquiteturais já tomadas

| Data | Decisão | Por quê | Impede no futuro |
|---|---|---|---|
| 2026-05-14 | Atribuição last-click via UTM | Única regra implementável com os dados disponíveis | Atribuição multi-touch exige refatoração de `fact_orders` e views |
| 2026-05-14 | Frontend em HTML puro (sem framework) | Dashboard aprovado; sem motivo para reescrever | Funcionalidades avançadas exigirão framework |
| 2026-05-14 | BigQuery → Google Sheets → Supabase para sessões | Acesso direto ao BigQuery indisponível na V1 | Migração para BigQuery direto exige service account |
| 2026-05-14 | Apenas pedidos pagos no sistema | Bases da Minimal Club só expõem pedidos pagos | Reembolsos exigirão campo `status` em `fact_orders` |
| 2026-05-26 | Railway removido — ingestão via Edge Function | Scheduler no Railway ficou instável | — |
| 2026-06-01 | Migração para Vercel Cron Jobs | Crons nativos da Vercel; sem servidor externo; logs em `cron_logs` | Muitas fontes simultâneas podem exigir Vercel Queues |
| 2026-06-01 | Autenticação server-side via Flask + JWT Supabase | Dashboard interno; cookie `sb_token` | Usuários externos exigiriam Supabase Auth flow completo |
| 2026-06-01 | `flow_email_metrics` separada de `fact_email_sends` | Granularidade de flow-message × dia; evita mistura com campanhas | Unificação futura exige migration |
| 2026-06-03 | Dashboard consulta `vw_flow_email_assets` e `vw_flow_email_items` (views) em vez de `flow_email_metrics` direto | Queries diretas à tabela via supabase-js retornavam array vazio no browser; views (security definer) contornam o problema. Segue R11. | Queries diretas a `flow_email_metrics` via anon key são instáveis — sempre usar view |
| 2026-06-03 | Crons com lookback D-2 a D-1 | Auto-recuperação: se cron falhar um dia, a próxima execução recupera automaticamente | — |
| 2026-06-05 | Estrutura de fluxos cacheada em `dim_assets`/`dim_asset_items` via cron separado | Eliminação de ~500 chamadas GET/dia que causavam 429s e timeout no cron email_flow | Novas métricas de fluxo exigem atualização do cron email_structure |
| 2026-06-08 | email_flow usa `by=['$message']` por fluxo (não por mensagem) | Reduz ~1.566 para ~99 POSTs; execução de ~15min para ~75s; resolve timeout Vercel | — |
| 2026-06-03 | Endpoint `/admin/backfill/<job>` para recuperação manual | Permite backfill via browser sem precisar de CRON_SECRET ou CLI | Requer AUTH_ENABLED=True para segurança em produção |

---

## 6. Pontos frágeis conhecidos

### Google Sheets como intermediário de sessões
- **Risco:** mudança no nome de coluna da planilha quebra a ingestão silenciosamente
- **Sinal de falha:** dashboard sem dados de Sessões/RPS/Conversão; banner vermelho
- **Plano:** aceitar na V1; migrar para BigQuery API direto na V2

### Cron de e-mail fluxo — volume de chamadas API
- **Risco:** se novos fluxos forem criados, o número de chamadas POST aumenta proporcionalmente (~3 por fluxo)
- **Sinal de falha:** ausência de log em `cron_logs` para `email_flow`; ou `email_flow` logando "no_flow_messages_in_db" (indica que `email_structure` falhou antes)
- **Mitigação aplicada (2026-06-05):** estrutura cacheada em `dim_assets`/`dim_asset_items` — elimina ~500 chamadas GET por execução
- **Mitigação aplicada (2026-06-08):** por fluxo com `by=['$message']` — reduz de ~1.566 para ~99 POSTs; execução caiu de ~15min para ~75s; resolve o timeout que causou falhas desde 05/06

### Cron de estrutura de fluxos — risco de timeout na Vercel
- **Risco:** localmenteo cron email_structure levou ~499s (dentro do limite de 600s), mas com mais 429s pode ultrapassar
- **Sinal de falha:** `email_flow` logando "no_flow_messages_in_db" mesmo com `email_structure` aparentemente executando
- **Monitoramento:** verificar duração real nos logs da Vercel se os 429s se tornarem mais frequentes

### AUTH_ENABLED=False temporariamente
- **Risco:** dashboard e endpoint `/admin/backfill/*` acessíveis publicamente
- **Plano:** reativar assim que as contas de acesso forem criadas (endpoint `/auth/create-user` disponível)

### UTMs inconsistentes nos links de CRM
- **Risco:** pedidos sem UTM ficam fora do dashboard (`attributed_channel_id = null`)
- **Plano:** auditar todos os links ativos antes de qualquer análise de atribuição

### fact_email_health não conectada ao dashboard
- **Risco:** dados de saúde da base são coletados mas não exibidos (dashboard usa valores hardcoded)
- **Plano:** substituir mock por `vw_email_health` na próxima versão

---

## 7. Inventário de arquivos críticos

| Caminho | Responsabilidade | Quem deve mexer |
|---|---|---|
| `dashboard-crm.html` | Dashboard visual — fonte única de verdade do frontend | Apenas substituição de dados/lógica; HTML/CSS estrutural intocável |
| `api/cron/app.py` | Flask: serve dashboard + auth + 6 endpoints de cron + admin backfill | Claude ao adicionar rota ou cron |
| `api/cron/email_structure.py` | Entry point do cron email_structure (maxDuration: 600s) | Claude ao ajustar throttle |
| `api/cron/email_flow.py` | Entry point do cron email_flow (maxDuration: 900s) | Claude ao ajustar janela ou throttle |
| `api/cron/email_campaign.py` | Entry point do cron email_campaign | Claude ao ajustar janela |
| `api/cron/revenue.py` | Entry point do cron de receita Shopify | — |
| `api/cron/sessions.py` | Entry point do cron de sessões | — |
| `api/cron/forms.py` | Entry point do cron de formulários | — |
| `ingestion/db/writers.py` | Todas as funções de upsert no Supabase | Claude com cuidado — afeta todas as fontes |
| `ingestion/flow_metrics_daily.py` | Runner do email_flow — lê estrutura do banco via `get_flow_message_structure` | Claude ao ajustar lookback ou throttle |
| `ingestion/flow_structure_daily.py` | Runner do email_structure — sincroniza dim_assets/dim_asset_items | Claude ao ajustar throttle |
| `ingestion/campaign_metrics_daily.py` | Runner do email_campaign | Claude ao ajustar lookback |
| `ingestion/main.py` | Entry points: shopify, sessions, forms | Claude ao ajustar janelas |
| `ingestion/sources/klaviyo_flow_metrics.py` | Lógica de busca de métricas via Klaviyo metric-aggregates API — lê estrutura do banco | Claude com cuidado — throttle sensível |
| `ingestion/sources/klaviyo_structure_sync.py` | Lógica de sincronização de estrutura de fluxos (dim_assets + dim_asset_items) | Claude ao ajustar throttle |
| `supabase/migrations/` | Schema do banco versionado | NUNCA editar migration já aplicada — sempre criar nova |
| `vercel.json` | Crons, routing, maxDuration | Claude ao adicionar cron ou ajustar timeout |
| `.env` | Credenciais reais | Apenas Daniel — Claude nunca lê nem commita |
| `PRODUCT.md` | Fonte de verdade do domínio | Claude + Daniel quando produto muda |
| `CLAUDE.md` | Regras de operação do agente | Claude + Daniel quando convenções mudam |
