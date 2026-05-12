# PRD — Backend do Dashboard CRM Minimal Club
**Versão:** 1.0  
**Data:** 2026-05-12  
**Autor:** Daniel Magalhães + Claude  
**Status:** Em elaboração  

---

## Como ler este documento

Este PRD foi escrito para quem não é técnico. Cada seção explica **o que vamos construir**, **por que**, e — mais importante — **o que você, Daniel, precisa fazer ou me fornecer** em cada etapa. Você não precisa entender tudo de uma vez. Vamos trabalhar passo a passo, um bloco por vez.

---

## 1. Contexto e Objetivo

Hoje o dashboard (`dashboard-crm.html`) existe com dados falsos (mockados). O objetivo agora é ligar esse dashboard a dados reais, que vivem em ferramentas como Shopify, Klaviyo, Vekta e Sendflow.

Para isso vamos:
1. Criar a base de dados no **Supabase** (um banco de dados na nuvem, gratuito para começar)
2. Conectar as fontes de dados a essa base
3. Substituir os dados falsos do HTML pelos dados reais vindos do Supabase

O resultado final: um dashboard que atualiza automaticamente todo dia, com dados reais, com o mesmo visual que você já aprovou.

---

## 2. O que este sistema PODE fazer (Escopo V1)

### 2.1 Páginas e métricas contempladas

| Página | O que vai mostrar com dados reais |
|--------|-----------------------------------|
| Resumo CRM | Faturamento total, compras, ticket médio, RPS, conversão, 1ª compra vs recompra, ranking de canais, captação de leads, funil, pace vs meta, saúde do e-mail |
| E-mail Fluxo | KPIs do canal, funil, receita/inscrito, tabela de fluxos com drill-down por e-mail, ranking |
| E-mail Campanha | KPIs do canal, funil, receita/disparo, tabela de campanhas, ranking |
| WhatsApp Fluxo | KPIs do canal, funil, receita/inscrito, tabela de fluxos com drill-down por template, ranking |
| WhatsApp Campanha | KPIs do canal, funil, receita/disparo, tabela de campanhas com templates, ranking |
| Comunidade WhatsApp | KPIs do canal, funil, receita/disparo, tabela de mensagens, ranking |

### 2.2 Filtros que vão funcionar

- Período (D-1, 7 dias, MTD, Mês anterior, 30 dias)
- Comparativo (Dia vs dia anterior / Mês vs mês anterior)
- Canal (todos os 5 canais)
- Tipo de cliente (Todos / 1ª Compra / Recompra)
- Fluxo/Campanha (por ativo individual)

### 2.3 Atribuição de receita

Toda receita é atribuída por **last-click via UTM**. Isso significa: quem recebeu o último clique de CRM antes da compra leva o crédito. A soma dos 5 canais deve ser igual à receita CRM total do Shopify.

---

## 3. O que este sistema NÃO PODE fazer (Fora do Escopo V1)

Estas funcionalidades foram deliberadamente excluídas da versão 1. Elas podem entrar em versões futuras.

| O que não entra | Por quê |
|-----------------|---------|
| Saúde da base WhatsApp (Quality Rating, bloqueios, opt-out Meta) | Acesso ao Meta Business Manager ainda não está configurado |
| CAC, LTV, ROAS | Custos por canal ainda não estão disponíveis de forma estruturada |
| Análise de Coorte | Complexidade de implementação não justifica no V1 |
| Qualidade de lead comercial e tempo de ciclo | Dados do comercial não estão integrados |
| Aba "Sem Atribuição" | UTMs não reconhecidas serão tratadas manualmente em V2 |
| Engajamento da Comunidade | Sendflow não expõe dados de engajamento por API |
| Recompra / retenção detalhada (coorte) | Fora do escopo V1 |

---

## 4. Regras de Governança

Estas são as regras que definem como os dados se comportam no sistema. Ninguém pode mudá-las sem revisar toda a base de dados.

### 4.1 Atribuição de Receita
- **Regra:** Last-click UTM. Um pedido recebe atribuição ao canal cujo link foi o último clicado antes da compra.
- **Impacto:** Um pedido só pode pertencer a UM canal. A soma dos 5 canais = receita CRM total.
- **Pedidos sem UTM de CRM:** Não são atribuídos a nenhum canal e ficam fora do painel V1.

### 4.2 Padrão de UTMs
Para que a atribuição funcione, todos os links enviados por CRM precisam ter UTMs no padrão abaixo:

| Canal | utm_source | utm_medium |
|-------|------------|------------|
| E-mail Fluxo | `email` | `flow` |
| E-mail Campanha | `email` | `campaign` |
| WhatsApp Fluxo | `whatsapp` | `flow` |
| WhatsApp Campanha | `whatsapp` | `campaign` |
| Comunidade WhatsApp | `community` | (qualquer) |

> **Importante:** Se os links não estiverem com UTMs nesse padrão, a receita não vai aparecer no dashboard. Isso precisa ser auditado antes de ligar o sistema.

### 4.3 Tipo de Cliente (1ª Compra vs Recompra)
- **Regra:** Um pedido é de "1ª Compra" quando o campo `orders_count` do cliente no Shopify é igual a 1. É "Recompra" quando maior que 1.
- **Fonte:** Shopify API (campo `customer.orders_count` no pedido).

### 4.4 Métricas calculadas — definições fixas
| Métrica | Fórmula | Jamais mudar sem revisar o banco |
|---------|---------|----------------------------------|
| RPS | Faturamento ÷ Sessões | Sim |
| Conversão | Compras ÷ Sessões | Sim |
| Ticket Médio | Faturamento ÷ Compras | Sim |
| CTOR | Cliques ÷ Aberturas (não cliques ÷ envios) | Sim |
| Receita/Inscrito | Faturamento do canal ÷ Inscritos ativos | Sim |
| Receita/Disparo | Faturamento do canal ÷ Disparos | Sim |
| Cobertura (WA) | Disparos ÷ Inscritos | Sim |

### 4.5 Cadência de atualização
- O dashboard é de **leitura diária** (operação lê toda manhã).
- Os dados devem ser atualizados **uma vez por dia**, preferencialmente entre 3h e 6h da manhã.
- Qualquer dado mais recente que D-1 pode estar incompleto e não deve ser exibido.

### 4.6 Fonte oficial por dado

| Dado | Fonte oficial | Obs |
|------|--------------|-----|
| Pedidos e receita | Shopify | Via API ou exportação |
| Sessões, ATC, BCO | Looker Studio (GA4) | Exportação manual ou via API |
| E-mail (envios, aberturas, cliques, bounces) | Klaviyo | Via API oficial |
| Formulários e popups (visualizações, inscritos) | Klaviyo Forms API | Via API oficial |
| WhatsApp Fluxo e Campanha (disparos, respostas) | Vekta + n8n | Via API Vekta ou planilha n8n |
| Comunidade (participantes, entradas, saídas) | Sendflow | Via API ou exportação |
| Inscritos WhatsApp | Hubspot (hoje) → Klaviyo (migração planejada) | Após migração, trocar fonte para Klaviyo |
| Metas mensais | Input manual (você insere no Supabase) | Planilha ou formulário simples |

---

## 5. Fontes de Dados — Detalhamento fiel ao `Métricas Gerenciamento v2.xlsx`

Esta seção lista exatamente de onde vem cada dado que aparece no dashboard. Foi extraída do arquivo Excel de métricas.

### 5.1 Shopify
**O que precisamos buscar:**
- Pedidos (orders): data, valor, canal UTM (source + medium + campaign), ID do cliente
- Clientes (customers): `orders_count` (para saber se é 1ª compra ou recompra)

**Métricas que dependem disso:**
- Faturamento CRM (todos os canais)
- Compras (todos os canais)
- Ticket Médio
- Receita 1ª Compra e Receita Recompra
- Conversão (precisa cruzar com sessões do GA4)

**O que você precisa me fornecer:**
> Acesso à API do Shopify (Admin API Key e Password). Para pegar isso: vá em Configurações → Aplicativos → Aplicativos e canais de vendas → Desenvolver aplicativos → Crie um app com permissões de leitura de `orders` e `customers`.

---

### 5.2 Klaviyo — E-mails (Fluxos e Campanhas)
**O que precisamos buscar:**
- Fluxos: nome, e-mails dentro do fluxo, envios, aberturas, cliques, bounces, spam, unsubscribes
- Campanhas: nome, envios, aberturas, cliques, bounces, spam, unsubscribes
- Base ativa: segmento "Engajados 90 dias" (contagem de perfis)

**Métricas que dependem disso:**
- Taxa de Abertura
- CTOR (Cliques ÷ Aberturas)
- Taxa de Entrega, Bounce Rate, Spam Complaint Rate, Opt-out Rate
- Base Ativa 90d
- Receita/Envio, Receita/Inscrito

**O que você precisa me fornecer:**
> API Key do Klaviyo (nível: Full Access ou pelo menos Read-only). Para pegar: vá em Klaviyo → Account → Settings → API Keys → Create Private API Key.

---

### 5.3 Klaviyo — Formulários e Popups (Captação de Leads)
**O que precisamos buscar:**
- Por formulário: nome, visualizações, inscrições por dia

**Métricas que dependem disso:**
- Leads novos por dia (total e por fonte)
- Taxa de Cadastro por ativo
- Visualizações totais

**O que você precisa me fornecer:**
> Mesma API Key do Klaviyo do item 5.2.

> **Ação adicional sua:** Confirmar que os formulários estão com nomes padronizados (ex.: "Popup Home", "Form Footer", "Landing Coleção SS25"). O nome precisa indicar o tipo e o local.

---

### 5.4 Looker Studio / Google Analytics 4 (GA4)
**O que precisamos buscar:**
- Por canal (filtrado por UTM): Sessões, Add to Cart (ATC), Begin Checkout (BCO)
- Esses dados alimentam o funil em todas as páginas

**Métricas que dependem disso:**
- RPS (precisa das sessões)
- Conversão (precisa das sessões)
- Taxas do funil (Sessão→ATC, ATC→BCO, BCO→Compra)

**O que você precisa me fornecer:**
> Duas opções — me diga qual prefere:
> - **Opção A (manual, mais simples para começar):** Você exporta os dados do Looker em CSV toda semana e eu te ajudo a importar no Supabase.
> - **Opção B (automático, mais complexo):** Conectamos a API do Google Analytics 4. Para isso você precisa de acesso ao Google Cloud Project que está vinculado à propriedade GA4.

---

### 5.5 Vekta + n8n (WhatsApp Fluxo e Campanha)
**O que precisamos buscar:**
- Por fluxo e por template: disparos, respostas (Acessar), Destravar Objeção, Leads passados ao Comercial
- Por campanha e por template: disparos, respostas, Destravar Objeção, Leads passados ao Comercial

**Métricas que dependem disso:**
- Taxa de Resposta
- Cobertura (Disparos ÷ Inscritos)
- Retenção da IA (Taxa de Handoff)
- CTR das mensagens
- Receita/Inscrito e Receita/Disparo (WA)

**O que você precisa me fornecer:**
> - Credenciais da API do Vekta (se houver API disponível) OU
> - Exportação manual dos dados do Vekta em CSV OU
> - Acesso ao n8n (URL e API key) para criar uma rota de exportação automática
>
> **Nota importante:** O Spread foi descontinuado como fonte de dados — o Vekta é a fonte oficial. Se ainda houver dados no Spread que precisam ser migrados, me avise.

---

### 5.6 Sendflow (Comunidade WhatsApp)
**O que precisamos buscar:**
- Participantes totais (snapshot diário)
- Entradas e saídas (30 dias)
- Por mensagem: nome da mensagem, data do disparo, quantidade de disparos

**Métricas que dependem disso:**
- Crescimento líquido da Comunidade
- Receita/Participante
- Receita/Disparo (Comunidade)
- Ranking de mensagens

**O que você precisa me fornecer:**
> - Verificar se o Sendflow tem API ou exportação de dados. Me diga: você consegue acessar algum relatório de dados no Sendflow? Se sim, me mostre como ele aparece (print ou descrição).
> - Se não houver API: vamos criar um processo de input manual mensal.

---

### 5.7 Hubspot (Inscritos WhatsApp — temporário)
**O que precisamos buscar:**
- Contagem de inscritos ativos por fluxo de WhatsApp

**Nota:** Esta fonte é temporária. Após a migração para Klaviyo, o Hubspot deixa de ser necessário para esta métrica.

**O que você precisa me fornecer:**
> - Confirmar: a migração do Hubspot para Klaviyo (para inscritos de WhatsApp) já tem data prevista?
> - Se ainda for Hubspot: API Key do Hubspot ou exportação manual dos contatos por lista/fluxo.

---

### 5.8 Metas Mensais (Input Manual)
**O que precisamos buscar:**
- Meta de Receita 1ª Compra (mensal)
- Meta de Receita Recompra (mensal)
- Meta de Receita Total CRM (mensal)

**Métricas que dependem disso:**
- % atingido do mês (pace)
- Projeção de fechamento
- Status do pace (acima/abaixo da meta)

**O que você precisa me fornecer:**
> Nada de API aqui — você vai inserir as metas manualmente no Supabase todo começo de mês. Vou criar uma tabela simples para isso, e posso também criar um formulário web básico para facilitar.

---

## 6. Arquitetura do Sistema

```
[Shopify]      ──────────────────────────────────────┐
[Klaviyo]      ──────────────────────────────────────┤
[Vekta/n8n]    ─────► [Processo de ingestão diária]  ─► [Supabase (PostgreSQL)] ─► [Dashboard HTML]
[Sendflow]     ──────────────────────────────────────┤
[GA4/Looker]   ──────────────────────────────────────┘
[Metas]        ─────► [Input manual no Supabase]
```

### O Supabase faz:
- Armazena todos os dados brutos (tabelas `fact_*`)
- Calcula as métricas derivadas (views `vw_*`)
- Expõe os dados via API REST para o dashboard
- Guarda as metas mensais

### O Dashboard HTML faz:
- Busca dados do Supabase via API (substitui os dados falsos atuais)
- Aplica os filtros de período, canal, tipo de cliente e ativo
- Renderiza os gráficos e tabelas com os dados reais

---

## 7. Modelo de Dados — Tabelas no Supabase

### 7.1 Tabelas de Dimensão (dados de referência, mudam pouco)

| Tabela | O que guarda | Exemplo |
|--------|-------------|---------|
| `dim_channels` | Os 5 canais do CRM | id, nome ("E-mail Fluxo"), slug ("ef"), cor, utm_source, utm_medium |
| `dim_assets` | Fluxos e campanhas por canal | id, canal_id, nome ("Carrinho Abandonado"), tipo ("fluxo"), ativo |
| `dim_email_messages` | E-mails individuais dentro de fluxos | id, ativo_id, subject_line, posição no fluxo |
| `dim_wpp_templates` | Templates dentro de fluxos/campanhas WA | id, ativo_id, conteúdo (preview), posição |
| `dim_forms` | Formulários e popups Klaviyo | id, nome, tipo (popup/formulário/embed), posicionamento |

### 7.2 Tabelas de Fatos (dados que chegam todo dia)

| Tabela | O que guarda | Fonte | Granularidade |
|--------|-------------|-------|---------------|
| `fact_orders` | Pedidos com UTM e tipo de cliente | Shopify | 1 linha por pedido |
| `fact_sessions` | Sessões, ATC, BCO por canal e dia | GA4/Looker | 1 linha por canal por dia |
| `fact_email_sends` | Envios, aberturas, cliques, bounces por e-mail e dia | Klaviyo | 1 linha por e-mail por dia |
| `fact_wpp_sends` | Disparos, respostas, leads por template e dia | Vekta/n8n | 1 linha por template por dia |
| `fact_community_members` | Participantes, entradas, saídas por dia | Sendflow | 1 linha por dia |
| `fact_community_sends` | Disparos de mensagens da Comunidade | Sendflow | 1 linha por mensagem |
| `fact_lead_captures` | Visualizações e inscrições por formulário e dia | Klaviyo Forms | 1 linha por form por dia |
| `fact_email_health` | Saúde da base (bounce, spam, opt-out, base ativa) por canal | Klaviyo | 1 linha por canal por dia |
| `fact_monthly_goals` | Metas mensais de receita | Input manual | 1 linha por mês |

### 7.3 Views calculadas (Supabase cria automaticamente)

| View | O que calcula | Usada em |
|------|--------------|---------|
| `vw_crm_daily_summary` | Faturamento, compras, sessões, conversão, TKM, RPS por canal e dia | Todos os gráficos de série temporal |
| `vw_channel_kpis` | KPIs agregados por canal e período | Cards de KPI no topo de cada página |
| `vw_asset_performance` | Performance completa por fluxo/campanha | Tabelas de detalhamento |
| `vw_funnel_crm` | Sessões → ATC → BCO → Compras por canal | Funil |
| `vw_leads_daily` | Leads por dia por fonte de captação | Gráfico de captação |
| `vw_pace_vs_goals` | % atingido, projeção, status | Gauge de pace |
| `vw_email_health` | Entregabilidade da base de e-mail | Bloco de saúde |

---

## 8. Plano de Execução — Passo a Passo

Este é o roteiro que vamos seguir juntos. Cada etapa tem o que você precisa fazer, o que eu preciso de você, e o que acontece depois.

---

### ETAPA 1 — Criar a conta e o projeto no Supabase
**Responsável:** Você  
**Estimativa:** 20 minutos

**O que fazer:**
1. Acesse [supabase.com](https://supabase.com) e crie uma conta gratuita (pode usar seu e-mail da Minimal Club)
2. Clique em "New Project"
3. Nome do projeto: `minimal-club-crm`
4. Senha do banco: crie uma senha forte e **guarde em local seguro** (você vai precisar depois)
5. Região: `South America (São Paulo)` — garante menor latência
6. Clique em "Create new project" e aguarde ~2 minutos

**O que você me fornece:**
- A `URL do projeto` (formato: `https://xyzxyzxyz.supabase.co`)
- A `anon/public key` (fica em Settings → API)
- Confirmar que o projeto foi criado com sucesso (print da tela ou descrição)

**O que acontece depois:** Eu crio todas as tabelas e views automaticamente para você.

---

### ETAPA 2 — Criar a estrutura do banco (tabelas e views)
**Responsável:** Claude (eu faço, você só aprova)  
**Estimativa:** 1 hora de trabalho meu, sem esforço da sua parte

**O que acontece:** Com o projeto criado, eu vou gerar os scripts SQL que criam todas as tabelas listadas na seção 7. Você vai colar esses scripts no Supabase (em SQL Editor) e executar. Vou te guiar clique a clique.

**O que você precisa fazer:** Nada nesta etapa além de aguardar. Quando eu terminar, te mando o script pronto com instruções de onde colar.

---

### ETAPA 3 — Auditoria de UTMs no Shopify
**Responsável:** Você + Eu  
**Estimativa:** 1 reunião ou troca de mensagens

**O que fazer:**
1. No Shopify, exporte os últimos 30 dias de pedidos em CSV (Pedidos → Exportar)
2. Me envie esse arquivo (ou me mostre uma amostra de 10-20 linhas)
3. Vou verificar se os campos `utm_source` e `utm_medium` estão preenchidos e no padrão correto
4. Se houver inconsistências, te dou uma lista do que precisa ser corrigido nas UTMs dos links

**O que você me fornece:** Exportação de pedidos do Shopify em CSV (pode tirar os valores financeiros se quiser, o que importa são as colunas de UTM e o campo `orders_count` do cliente).

---

### ETAPA 4 — Conectar o Shopify ao Supabase
**Responsável:** Claude (com suas credenciais)  
**Estimativa:** 2-3 horas

**O que você precisa fazer:**
1. Criar um "Custom App" no Shopify com permissão de leitura de pedidos e clientes
2. Me passar o `API Key`, `API Secret` e `Access Token` gerados
3. Confirmar o nome da loja Shopify (ex.: `minimal-club.myshopify.com`)

**O que acontece depois:** Eu crio o script de importação que puxa os pedidos para o Supabase. Vamos rodar a primeira carga histórica (últimos 90 dias) e depois configurar a atualização diária.

---

### ETAPA 5 — Conectar o Klaviyo ao Supabase
**Responsável:** Claude (com suas credenciais)  
**Estimativa:** 2-3 horas

**O que você precisa fazer:**
1. No Klaviyo: Account → Settings → API Keys → Create Private API Key (Read-only)
2. Me passar a API Key gerada
3. Me confirmar: os fluxos de e-mail estão organizados com nomes claros no Klaviyo? (Me diga os nomes dos principais fluxos que você quer ver no dashboard)

**O que acontece depois:** Eu crio o script que puxa fluxos, campanhas, métricas de envio e dados de formulários para o Supabase.

---

### ETAPA 6 — Conectar os dados de Sessões (GA4/Looker)
**Responsável:** Você + Claude  
**Estimativa:** 1-2 horas (depende do acesso)

**Você escolhe o caminho:**

**Caminho A — Manual (para começar rápido):**
- Você exporta do Looker Studio uma planilha com sessões, ATC e BCO por canal e dia (últimos 90 dias)
- Me manda o arquivo, eu importo e mostro o formato correto para exportações futuras
- Desvantagem: vai precisar exportar semanalmente

**Caminho B — Automático via API GA4:**
- Você me dá acesso à propriedade GA4 (vai precisar ir no Google Analytics → Admin → Gerenciamento de acesso à propriedade e me adicionar como Viewer)
- Eu crio uma integração automática
- Vantagem: não precisa de intervenção manual

**Me diga qual caminho prefere.**

---

### ETAPA 7 — Conectar Vekta/n8n ao Supabase
**Responsável:** Você + Claude  
**Estimativa:** 2-4 horas (depende de como o Vekta expõe os dados)

**O que você precisa fazer:**
1. Verificar no Vekta se há uma API disponível (geralmente em Configurações ou Integrações)
2. Me dizer: você tem acesso ao n8n? Se sim, me mostra a URL e o login
3. Se não houver API: o Vekta permite exportar dados em CSV? Me mostra como

**O que acontece depois:** Definimos juntos o melhor jeito de puxar disparos, respostas e leads do WhatsApp para o Supabase.

---

### ETAPA 8 — Conectar Sendflow (Comunidade) ao Supabase
**Responsável:** Você + Claude  
**Estimativa:** 1-2 horas

**O que você precisa fazer:**
1. Verificar no Sendflow se há API ou exportação de dados
2. Me mostrar como os dados aparecem no Sendflow (print de tela ou descrição)

**O que acontece depois:** Criamos o processo de importação (automático ou manual).

---

### ETAPA 9 — Inserir as Metas Mensais no Supabase
**Responsável:** Você  
**Estimativa:** 10 minutos por mês

**O que fazer:** Vou criar uma interface simples (pode ser uma planilha Google conectada ou um formulário web) onde você insere as 3 metas todo começo de mês:
- Meta Receita 1ª Compra
- Meta Receita Recompra  
- Meta Total CRM

**O que você precisa me dizer:** Qual a meta de maio de 2026 para cada uma? Quero já inserir os primeiros dados.

---

### ETAPA 10 — Conectar o Dashboard HTML ao Supabase
**Responsável:** Claude  
**Estimativa:** 4-8 horas

**O que acontece:** Eu substituo os dados falsos do `dashboard-crm.html` pelos dados reais vindos do Supabase. O visual permanece 100% idêntico ao que você já aprovou. Apenas os números mudam.

**O que você faz:** Revisa o dashboard com dados reais e confirma que tudo está correto. Fazemos esse passo juntos — você olha e me diz se algum número parece estranho.

---

### ETAPA 11 — Configurar atualização automática diária
**Responsável:** Claude  
**Estimativa:** 2 horas

**O que acontece:** Configuramos um processo que roda todo dia de madrugada e atualiza todos os dados no Supabase automaticamente. Quando você abrir o dashboard de manhã, os dados de ontem já vão estar lá.

**Ferramenta provável:** n8n (se já tiver acesso) ou um script simples no servidor.

---

## 9. O que precisamos decidir antes de começar

Antes da Etapa 1, me responda:

1. **GA4/Looker:** Prefere Caminho A (manual, mais simples) ou Caminho B (automático via API)?

2. **Vekta:** Você tem acesso ao painel do Vekta? O que consegue ver lá?

3. **Sendflow:** O Sendflow tem API ou só interface web?

4. **Hubspot → Klaviyo:** A migração dos inscritos de WhatsApp já tem data? Ou ainda vai demorar?

5. **Metas de maio/2026:** Quais são as metas mensais de receita para este mês? (1ª compra, recompra e total)

---

## 10. Perguntas Frequentes (para quem está começando)

**O que é Supabase?**  
É um serviço de banco de dados na nuvem. Pense nele como uma planilha muito poderosa que fica sempre online, que vários sistemas podem acessar ao mesmo tempo, e que faz cálculos automaticamente.

**Preciso saber programar?**  
Não. Eu escrevo todos os scripts e te digo exatamente onde colar e o que clicar. Você só precisa ter acesso às ferramentas e me passar as credenciais com segurança.

**É seguro passar credenciais para o Claude?**  
Boas práticas: nunca me passe senhas pessoais. Para APIs (Shopify, Klaviyo, etc.), crie chaves de acesso com permissão **somente leitura** (read-only). Assim, mesmo que as chaves fossem expostas, ninguém poderia alterar seus dados.

**Quanto custa o Supabase?**  
O plano gratuito (Free Tier) suporta até 500MB de dados e 50.000 linhas por tabela — mais que suficiente para começar. Quando crescer, o plano pago é US$ 25/mês.

**Quando o dashboard vai estar pronto com dados reais?**  
Depende de quanto tempo levaremos para coletar os acessos. Se tudo correr bem: entre 2 e 4 semanas trabalhando passo a passo.

---

## 11. Próxima ação imediata

**Você faz agora:**
1. Leia as perguntas da seção 9 e me responda uma por uma.
2. Enquanto isso, vá ao Shopify e ao Klaviyo para verificar se consegue criar as chaves de API (não precisa criar ainda, só verificar se tem acesso).

**Eu faço em paralelo:**
- Preparo os scripts SQL de criação das tabelas para estar pronto assim que o projeto Supabase for criado.

---

*Este documento é vivo e será atualizado conforme avançarmos. Cada etapa concluída será marcada como ✅.*
