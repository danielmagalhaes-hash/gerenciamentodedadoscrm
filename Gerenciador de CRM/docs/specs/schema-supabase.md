# Spec — Schema do Banco de Dados (Supabase)

> Descreve o COMPORTAMENTO da feature antes de implementar. Densa o suficiente para servir de checkpoint sem ler código.

---

## 1. Resumo em 1 parágrafo

Esta feature cria a estrutura completa do banco de dados no Supabase — todas as gavetas (tabelas) e relatórios calculados (views) que o restante do sistema vai usar. Nenhum dado real é inserido aqui; apenas a planta baixa é construída. Ao final, o banco estará pronto para receber dados das fontes (Shopify, Klaviyo, Vekta, Sendflow, Google Sheets) e o dashboard poderá consultá-lo via API. Inclui uma tabela de mapeamento de UTMs (`dim_utm_mappings`) que serve de dicionário de tradução entre os valores de UTM dos links e os canais/ativos do CRM — base necessária para o sistema de classificação de UTMs que será construído no frontend na Fase 3.

---

## 2. Comportamento funcional

### 2.1 Caminho feliz
1. Desenvolvedor executa `supabase db reset` no ambiente local
2. Supabase aplica as migrations em ordem cronológica
3. Todas as tabelas, views, índices e políticas de acesso são criados sem erro
4. `dim_channels` já vem populada com os 5 canais (inserido na própria migration)
5. Desenvolvedor verifica no painel do Supabase que as tabelas existem com as colunas corretas
6. Testa que a `anon key` consegue SELECT em tabelas e views, mas não consegue INSERT/UPDATE/DELETE
7. Testa que a `service_role_key` consegue fazer upsert em todas as tabelas de fato

### 2.2 Caminhos alternativos
- **Migration falha no meio:** Supabase reverte a migration com erro; as anteriores permanecem; desenvolvedor corrige o SQL e roda novamente
- **Tabela já existe (re-run):** migrations usam `IF NOT EXISTS` — rodar duas vezes não gera erro

### 2.3 Casos de erro
| Quando | O que acontece | Como recupera |
|---|---|---|
| SQL com erro de sintaxe | Migration falha com linha e coluna do erro | Corrigir o SQL e rodar `supabase db reset` |
| FK inválida (tabela referenciada não existe) | Falha apontando tabela e coluna | Verificar ordem de criação: dimensão antes de fato |
| Política RLS incorreta | Dashboard retorna erro 403 | Revisar políticas e re-aplicar |

---

## 3. Dados envolvidos

### 3.1 Tabelas criadas

**Dimensão (referência estática — mudam pouco):**

| Tabela | O que guarda |
|---|---|
| `dim_channels` | Os 5 canais com slugs, UTMs e KPI principal — populada na migration |
| `dim_assets` | Ativos pai: fluxos e campanhas por canal |
| `dim_asset_items` | Ativos filho: e-mails individuais e templates de WhatsApp |
| `dim_forms` | Formulários e popups de captação do Klaviyo |
| `dim_utm_mappings` | Dicionário de UTMs: traduz utm_source + utm_medium + utm_campaign para canal e ativo |

**Fato (dados que chegam a cada ingestão):**

| Tabela | O que guarda | Chave de upsert |
|---|---|---|
| `fact_orders` | Pedidos pagos com atribuição de canal | `order_id` |
| `fact_sessions` | Sessões, ATC, BCO por canal por dia | `(date, channel_id)` |
| `fact_email_sends` | Métricas de e-mail por item de ativo por dia | `(date, asset_item_id)` |
| `fact_wpp_sends` | Métricas de WhatsApp por template por dia | `(date, asset_item_id)` |
| `fact_wpp_subscribers` | Inscritos por fluxo de WhatsApp por dia | `(date, asset_id)` |
| `fact_community_members` | Snapshot diário de participantes da Comunidade | `date` |
| `fact_community_sends` | Disparos de mensagens da Comunidade | `external_id` |
| `fact_lead_captures` | Performance de formulários e popups por dia | `(date, form_id)` |
| `fact_email_health` | Saúde da base de e-mail por canal por dia | `(date, channel_id)` |
| `fact_monthly_goals` | Metas mensais de receita | `month` |

**Views (relatórios calculados — filtro de período passado na query):**

| View | O que calcula |
|---|---|
| `vw_crm_daily_summary` | Receita, compras, sessões, conversão, TKM, RPS por canal e dia |
| `vw_channel_kpis` | KPIs agregados por canal — filtro de período via WHERE |
| `vw_asset_performance` | Performance completa por fluxo/campanha (ativo pai) |
| `vw_funnel_crm` | Funil Sessões → ATC → BCO → Compras por canal |
| `vw_leads_daily` | Leads por dia por formulário |
| `vw_pace_vs_goals` | % atingido, projeção de fechamento, status vs meta |
| `vw_email_health` | Saúde da base de e-mail por canal |

### 3.2 Campos novos em relação ao ARCHITECTURE.md

**`fact_orders` — campo adicional:**
| Campo | Tipo | Default | Motivo |
|---|---|---|---|
| `data_source` | text | `'shopify'` | Origem do dado: `'shopify'` (>= 23/04/2025) ou `'bigquery'` (< 23/04/2025) |

**`fact_wpp_subscribers` — tabela nova:**
| Coluna | Tipo | Obrigatório | Notas |
|---|---|---|---|
| id | uuid | sim | PK |
| date | date | sim | Data do snapshot |
| asset_id | uuid | sim | FK → dim_assets (apenas fluxos WA) |
| subscribers_count | integer | sim | Total de inscritos no fluxo nessa data |
| source_tool | text | sim | `'hubspot'` ou `'klaviyo'` |
| ingested_at | timestamptz | sim | Último sync |

**`dim_utm_mappings` — tabela nova:**
| Coluna | Tipo | Obrigatório | Notas |
|---|---|---|---|
| id | uuid | sim | PK |
| utm_source | text | sim | Valor exato da UTM (ex: `'email'`) |
| utm_medium | text | sim | Valor exato da UTM (ex: `'flow'`) |
| utm_campaign | text | não | Valor exato — null = vale para qualquer campanha desse source+medium |
| channel_id | uuid | sim | FK → dim_channels — canal ao qual essa UTM pertence |
| asset_id | uuid | não | FK → dim_assets — ativo específico (opcional) |
| is_mapped | boolean | sim | `true` = mapeado pelo Daniel; `false` = detectado automaticamente, aguardando classificação |
| created_at | timestamptz | sim | — |
| mapped_at | timestamptz | não | Quando Daniel classificou |
| UNIQUE | `(utm_source, utm_medium, utm_campaign)` | — | Evita duplicata de mapeamento |

### 3.3 Migrations necessárias

1. **001 — Tabelas de dimensão**
   - Cria `dim_channels`, `dim_assets`, `dim_asset_items`, `dim_forms`, `dim_utm_mappings`
   - Popula `dim_channels` com os 5 canais fixos
   - Popula `dim_utm_mappings` com os mapeamentos padrão (`is_mapped = true`):

   | utm_source | utm_medium | utm_campaign | canal |
   |---|---|---|---|
   | `email` | `flow` | null | E-mail Fluxo |
   | `email` | `campaign` | null | E-mail Campanha |
   | `whatsapp` | `flow` | null | WhatsApp Fluxo |
   | `whatsapp` | `campaign` | null | WhatsApp Campanha |
   | `community` | null | null | WhatsApp Comunidade |

   > `utm_campaign = null` significa que qualquer campanha com aquele `source + medium` é automaticamente atribuída ao canal correspondente. UTMs com `utm_campaign` específico e desconhecido entram com `is_mapped = false` para classificação manual.

   - Reversível: sim

2. **002 — Tabelas de fato**
   - Cria todas as `fact_*` incluindo `fact_wpp_subscribers`
   - Reversível: sim

3. **003 — Índices e constraints**
   - Índices de performance e constraints UNIQUE e CHECK
   - Reversível: sim

4. **004 — Políticas RLS**
   - Habilita RLS em todas as tabelas
   - SELECT para `anon` em tudo; INSERT/UPDATE para `service_role` nas fact_* e dim_*
   - Reversível: sim

5. **005 — Views**
   - Cria todas as `vw_*`
   - Reversível: sim

---

## 4. Regras de negócio explícitas

- **R1.** Todo pedido em `fact_orders` com `order_date < 2025-04-23` tem `data_source = 'bigquery'`. Todo pedido com `order_date >= 2025-04-23` tem `data_source = 'shopify'`. O campo nunca pode ser nulo.

- **R2.** `fact_orders.attributed_channel_id` pode ser nulo — pedidos sem UTM de CRM mapeada ficam com `attributed_channel_id = null` e não aparecem nos KPIs por canal, mas permanecem na tabela para auditoria.

- **R3.** `fact_orders.revenue_brl` deve ser maior que zero. Apenas pedidos pagos entram no banco.

- **R4.** `dim_channels` é populada com exatamente 5 registros fixos na migration e nunca alterada por ingestão. Slugs canônicos: `email_flow`, `email_campaign`, `wpp_flow`, `wpp_campaign`, `wpp_community`.

- **R5.** `dim_assets.type` aceita apenas `'flow'` ou `'campaign'`. `dim_asset_items.type` aceita apenas `'email'` ou `'wpp_template'`.

- **R6.** `fact_wpp_subscribers` só aceita registros com `asset_id` de ativo do tipo `'flow'` em canal `wpp_flow`. Campanhas de WhatsApp não têm inscritos.

- **R7.** `fact_monthly_goals.goal_total_brl` deve ser igual a `goal_first_purchase_brl + goal_repurchase_brl`. Verificado por constraint CHECK.

- **R8.** `fact_sessions`: `sessions >= add_to_cart >= begin_checkout >= 0`. Verificado por constraint CHECK.

- **R9.** A `anon key` nunca executa escrita. Toda escrita usa exclusivamente a `service_role_key` via Python.

- **R10.** `dim_utm_mappings`: quando o sistema de ingestão encontra uma UTM desconhecida, insere um registro com `is_mapped = false`. Apenas registros com `is_mapped = true` são usados para atribuição de receita. Registros `is_mapped = false` aguardam classificação pelo Daniel no frontend (Fase 3).

- **R11.** Todas as colunas de timestamp são `timestamptz` armazenadas em UTC.

---

## 5. UI/UX

Esta feature é exclusivamente de banco de dados — sem interface de usuário nesta fase.

### 5.4 Permissões no banco

| Papel | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| `anon` (dashboard HTML) | ✅ todas as tabelas e views | ❌ | ❌ | ❌ |
| `service_role` (Python) | ✅ | ✅ fact_* e dim_* | ✅ fact_* e dim_* | ❌ |

---

## 6. Casos de borda específicos desta feature

| Caso | Comportamento esperado |
|---|---|
| Ingestão roda duas vezes para o mesmo período | Upsert por chave única — sem duplicata; segundo run sobrescreve o primeiro |
| Pedido com `order_date = 2025-04-23` exato | `data_source = 'shopify'` (a regra é `>= 23/04`) |
| Pedido com UTM desconhecida | `attributed_channel_id = null`; UTM inserida em `dim_utm_mappings` com `is_mapped = false` |
| UTM desconhecida aparece duas vezes | Constraint UNIQUE em `dim_utm_mappings` evita duplicata — segunda tentativa é ignorada com upsert |
| Meta inserida com total errado | Banco rejeita por constraint CHECK (R7) |
| View consultada sem filtro de data | Retorna todo o histórico desde jan/2025 sem erro — dashboard sempre deve passar filtro |
| `fact_wpp_subscribers` com `asset_id` de campanha | Banco rejeita por constraint (R6) |
| Migration rodada em banco que já tem as tabelas | `IF NOT EXISTS` — sem erro, idempotente |

---

## 7. Critérios de aceite testáveis

- [ ] **CA1.** Após `supabase db reset`, todas as 11 tabelas e 7 views existem sem erro.
- [ ] **CA2.** `dim_channels` tem exatamente 5 registros com os slugs canônicos corretos.
- [ ] **CA3.** `dim_utm_mappings` tem os mapeamentos padrão pré-populados (email/flow, email/campaign, whatsapp/flow, whatsapp/campaign, community).
- [ ] **CA4.** SELECT com `anon key` em `fact_orders` retorna dados sem erro 403.
- [ ] **CA5.** INSERT com `anon key` em `fact_orders` retorna erro 403.
- [ ] **CA6.** Upsert com `service_role_key` em `fact_orders` com dados válidos é aceito.
- [ ] **CA7.** INSERT em `fact_monthly_goals` com `goal_total ≠ goal_first + goal_repurchase` retorna erro de constraint.
- [ ] **CA8.** INSERT em `fact_sessions` com `add_to_cart > sessions` retorna erro de constraint.
- [ ] **CA9.** INSERT em `fact_wpp_subscribers` com `asset_id` de campanha retorna erro.
- [ ] **CA10.** Dois upserts seguidos com mesma `(date, channel_id)` em `fact_sessions` resultam em 1 registro.
- [ ] **CA11.** INSERT duplicado em `dim_utm_mappings` com mesma combinação `(utm_source, utm_medium, utm_campaign)` é rejeitado por constraint UNIQUE.
- [ ] **CA12.** View `vw_crm_daily_summary` retorna resultado sem erro quando consultada com filtro de data.

---

## 8. Riscos e impactos

### Módulos que dependem desta feature
- Todos os módulos `ingestion-*` — dependem das tabelas `fact_*` existirem
- `dashboard-frontend` — depende das views `vw_*` existirem
- Feature de UTM mapping (Fase 3) — depende da tabela `dim_utm_mappings` existir com estrutura correta

### Reversibilidade
- **Reversível: sim** — banco ainda está vazio; todas as migrations podem ser revertidas com DROP sem perda de dados

### Dado em produção afetado
- Nenhum — esta é a primeira migration; banco está vazio
