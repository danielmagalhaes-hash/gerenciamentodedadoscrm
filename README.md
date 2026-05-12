# Dashboard CRM · Minimal Club

Pasta de entrega do projeto **Dashboard CRM V1**. Front-end concluído (mockado), documentação executiva pronta para revisão com gestão e mapeamento técnico das fontes de dados para a próxima fase (back-end no Supabase).

---

## 📁 Conteúdo da pasta

| Arquivo | Para que serve | Quem usa |
|---|---|---|
| `dashboard-crm.html` | Dashboard interativo, navegável, com dados mockados realistas. Roda em qualquer navegador, offline, sem dependência. | Gestão + operação CRM |
| `docs-crm.html` | Documento executivo da entrega — contexto, decisões, métricas, arquitetura e próximos passos. Tem botão pra abrir o dashboard. | Gestor (apresentação) |
| `Métricas Gerenciamento v2.xlsx` | Mapeamento técnico de todas as métricas do dashboard: nome, tipo (dado/função), fórmula, granularidade, fonte de dados e objetivo. Base para construção do back-end. | Time de dados / engenharia |
| `Métricas Gerenciamento - original.xlsx` | Versão original enviada antes da análise. Mantida para referência histórica. | Histórico |
| `build_planilha.py` | Script Python que gera o `Métricas Gerenciamento v2.xlsx`. Permite reproduzir/editar a planilha programaticamente. | Time de dados |

---

## 🎯 O que esse projeto resolve

**Dor:** múltiplos ativos de CRM (e-mail, WhatsApp, comunidade) sem visibilidade unificada de quais puxam receita e quais precisam de ajuste. Bases isoladas, sem padronização.

**Solução V1:** dashboard único, leitura diária, com 6 páginas (1 resumo + 5 canais), 40+ métricas padronizadas, filtros globais e drill-down nos ativos.

---

## 🧱 Estrutura do dashboard

**Página 1 — Resumo CRM**
KPIs Topline · Receita 1ª Compra vs Recompra · Faturamento por canal · Eficiência por canal (Sessões, Conversão, TKM, RPS) · Evolução temporal · Captação de Leads · Formulários e Popups · Funil CRM · Pace do mês · Saúde da Base (e-mail).

**Páginas 2 a 6 — Por canal**
E-mail Fluxo · E-mail Campanha · WhatsApp Fluxo · WhatsApp Campanha · Comunidade WhatsApp.
Cada uma com: KPIs do canal · Funil · Receita/Inscrito ou /Disparo diário · Métricas específicas · Saúde da Base (quando aplicável) · Detalhamento por ativo (com drill-down) · Rankings.

**Filtros globais:** Período · Comparativo (dia/mês) · Canal · Tipo de Cliente (1ª/Recompra) · Fluxo/Campanha.

---

## ✅ Decisões críticas tomadas

| Métrica | Antes | Agora |
|---|---|---|
| RPS | TKM / Conversão (errado) | TKM × Conversão = Faturamento/Sessões |
| CTR dos E-mails | Cliques/Abertos | Renomeado para **CTOR** |
| Funil entre canais | Etapas inconsistentes | Padronizado: Sessões → ATC → BCO → Compras nos 5 canais |
| Atribuição | Não definida | **Last-click via UTM** (soma dos 5 canais = Receita CRM total) |

**KPI principal por canal:**
- E-mail Fluxo → Receita / Inscrito
- E-mail Campanha → Receita / Disparo
- WhatsApp Fluxo → Receita / Inscrito
- WhatsApp Campanha → Receita / Disparo
- Comunidade WhatsApp → Receita / Disparo

---

## 🔌 Fontes de dados (para próxima fase)

Arquitetura alvo: **Supabase** como base centralizada, consolidando:

- **Shopify** — compras, faturamento, customer.orders_count (1ª vs recompra)
- **Klaviyo** — e-mail (envios, abertos, cliques, base), Klaviyo Forms (popups e formulários), API para saúde da base
- **Vekta + n8n** — WhatsApp (disparos, respostas, destravar objeção, handoff IA→comercial)
- **Hubspot** → **Klaviyo** (migração planejada de inscritos WhatsApp Fluxo)
- **Sendflow** — Comunidade WhatsApp (participantes, entradas, saídas, disparos)
- **Looker (GA4)** — sessões, ATC, BCO, atribuição por UTM
- **Input mensal** — metas

Detalhamento completo por métrica na planilha `Métricas Gerenciamento v2.xlsx`.

---

## 🚫 Fora do escopo V1

- CAC / LTV / ROAS por canal *(Fase 2 — nova página)*
- Saúde da Base WhatsApp *(depende de acesso à Meta Business Manager)*
- Recompra / Coorte / Tempo entre compras *(retenção — não é a dor atual)*
- Qualidade de lead comercial / Tempo de ciclo *(foco é receita CRM)*
- Aba "Sem Atribuição" para UTMs órfãs *(próximo passo)*
- Engajamento da Comunidade *(Sendflow não expõe + não prioritário)*

---

## 🗺️ Próximos passos

1. **Validar o front-end** com gestão e operação
2. **Modelar schema do Supabase** espelhando a planilha v2
3. **Conectar fontes** via APIs (Klaviyo, Shopify, Vekta, Sendflow, Looker)
4. **Padronizar UTMs** e implementar atribuição last-click
5. **Substituir mockados** pelos dados reais do Supabase
6. **Fase 2** — CAC / LTV / ROAS

---

## 🛠️ Como abrir os arquivos

- **`dashboard-crm.html` / `docs-crm.html`** — duplo clique, abre no navegador padrão. Funciona offline.
- **`Métricas Gerenciamento v2.xlsx`** — Excel, Google Sheets ou LibreOffice.
- **`build_planilha.py`** — Python 3 com `openpyxl` instalado. Edita o script e roda `python build_planilha.py` para regenerar a planilha.

---

## 📩 Como compartilhar

**Com o gestor (para aprovação):**
- Enviar `docs-crm.html` + `dashboard-crm.html` juntos (zip ou anexos no e-mail)
- Ou publicar online via [tiiny.host](https://tiiny.host) (drag & drop, sem cadastro) ou Netlify Drop

**Com o time de dados:**
- Compartilhar `Métricas Gerenciamento v2.xlsx` e `build_planilha.py`

---

*Projeto · Daniel Magalhães · Minimal Club*
