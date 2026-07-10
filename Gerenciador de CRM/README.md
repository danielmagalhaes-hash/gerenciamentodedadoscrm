# Dashboard CRM · Minimal Club

Dashboard unificado de CRM que consolida métricas dos 5 canais de marketing da Minimal Club (e-mail fluxo, e-mail campanha, WhatsApp fluxo, WhatsApp campanha e comunidade WhatsApp) em uma única tela, com dados reais atualizados automaticamente.

---

## Estado atual do projeto

| Fase | O que é | Status |
|---|---|---|
| **Fase 1 — Frontend** | Dashboard interativo com 6 páginas e 40+ métricas (dados mockados) | ✅ Entregue e aprovado |
| **Fase 2 — Backend** | Base de dados Supabase + scripts de ingestão das fontes reais | 🔧 Em construção |
| **Fase 3 — Integração** | Substituição dos dados mock pelos dados reais no dashboard | ⏳ Pendente |

---

## O que o sistema faz (quando completo)

Scripts Python rodam a cada 30 minutos e puxam dados do Shopify, Klaviyo, Vekta, Sendflow e Google Sheets (sessões via BigQuery) para um banco centralizado no Supabase. O dashboard HTML lê esses dados via API e exibe KPIs de receita, funil, captação de leads e saúde da base — com filtros por período, canal, tipo de cliente e ativo.

Toda receita é atribuída por **last-click via UTM**: o canal do último link clicado antes da compra recebe 100% do crédito.

---

## Arquivos do projeto

### Documentação de produto
| Arquivo | Para que serve |
|---|---|
| `PRODUCT.md` | Fonte de verdade do domínio — glossário, entidades, fluxos, KPIs, escopo |
| `CLAUDE.md` | Manual de operação do agente — stack, regras, padrões de código |
| `ARCHITECTURE.md` | Mapa vivo do sistema — módulos, modelo de dados, decisões arquiteturais |

### Frontend (entregue)
| Arquivo | Para que serve |
|---|---|
| `dashboard-crm.html` | Dashboard interativo com dados mockados — abre direto no navegador |
| `docs-crm.html` | Documento executivo da entrega V1 |

### Backend (em construção)
| Pasta | Para que serve |
|---|---|
| `ingestion/sources/` | Scripts Python — um por fonte de dados (Shopify, Klaviyo, Vekta, Sendflow, Sheets) |
| `ingestion/models/` | Modelos Pydantic para validação dos dados de cada fonte |
| `ingestion/db/` | Cliente Supabase e funções de upsert nas tabelas fact_* |
| `supabase/migrations/` | SQL versionado — schema de tabelas, views e RLS |

### Referência e workflow
| Pasta | Para que serve |
|---|---|
| `docs/specs/` | Spec de cada feature antes de implementar |
| `docs/decisions/` | Decisões arquiteturais (ADRs) |
| `docs/sessions/` | Log de cada sessão de desenvolvimento |
| `prompts/` | Prompts prontos para conduzir sessões com o agente |
| `templates/` | Templates de documentos (PRODUCT, CLAUDE, ARCHITECTURE, spec, session) |
| `principios/` | Princípios de clean code, prompt engineering e context engineering |

---

## Fontes de dados

| Canal | Fonte | Frequência |
|---|---|---|
| E-mail Fluxo e Campanha | Klaviyo API | 30 min |
| WhatsApp Fluxo e Campanha | Vekta API | 30 min |
| WhatsApp Comunidade | Sendflow API | 30 min |
| Pedidos e receita | Shopify Admin API | 30 min |
| Sessões, ATC, BCO | BigQuery → Google Sheets | 1 hora |
| Metas mensais | Input manual (Supabase) | 1x por mês |

---

## Para começar (Fase 2)

```bash
# 1. Instalar dependências Python
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Preencher com as chaves de API de cada fonte

# 3. Criar projeto no Supabase e aplicar migrations
supabase db reset

# 4. Rodar ingestão manualmente
python ingestion/main.py
```

Consulte `ARCHITECTURE.md` para o modelo de dados completo e `CLAUDE.md` para as regras de desenvolvimento.

---

## Documentos essenciais para qualquer sessão de desenvolvimento

Antes de qualquer sessão, ler nesta ordem:
1. `CLAUDE.md` — regras e stack
2. `ARCHITECTURE.md` — estado atual do sistema
3. `docs/sessions/` — log da última sessão

---

*Projeto · Daniel Magalhães · Minimal Club*
