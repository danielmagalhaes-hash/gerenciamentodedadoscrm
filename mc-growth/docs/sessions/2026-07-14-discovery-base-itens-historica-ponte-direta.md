# Sessão 2026-07-14 — discovery-base-itens-historica-ponte-direta

> Log da sessão. Não é resumo de commit — é o "porquê" e o "o que vem depois".
> Sessão de **descoberta/planejamento (Modo A)** — **nenhum código foi alterado**.

---

## Objetivo da sessão

Descobrir como puxar a **base histórica de itens** do BigQuery para calcular **CMV real
ano-a-ano** (Opção 1 do roadmap) e se ela **cruza** com a base de deals do HubSpot — e
montar o prompt para o João levar a construção a outro chat.

---

## O que foi feito

- Localizei a origem da base de itens no BigQuery: `moon-ventures-data-lake.prod_silver.silver_minimal_shopify_pedidos_products` (mesmo projeto/dataset da query do HubSpot, `silver_deals_minimal`).
- Escrevi a **query de export** da base de itens inteira (colunas que o painel já sabe ler + `name`).
- Confirmei, com **dado real**, que as duas bases (HubSpot deals × Shopify itens) **cruzam direto** — ver "Problemas/achados".
- Expliquei ao João que o **custo NÃO está em nenhuma das duas bases** — CMV real = itens (base) × custo (tabela de Custos por SKU, já no painel), com as 2 estrelinhas de sempre (custo de hoje aplicado ao passado; cobertura de SKU antigo).
- Escrevi o **prompt para o outro chat** implementar o CMV em 3 camadas (base histórica → planilha MC Growth → estima 30%). O João vai levar esse prompt + a base `bq-results-20260714-171049-1784049063098` (renomear para `bases/itens_historico.csv`).

---

## Decisões tomadas

### Ponte HubSpot × itens = coluna `name` (direto, sem passar pela Vendas)
- **Decisão:** para a base histórica, casar `hubspot.nome` (número do pedido, com `lstrip("#")`) direto com `itens.name`. Dispensa a volta pela aba Vendas que o código faz hoje (`nome → Vendas.order_name → Vendas.order_id → Itens.id`).
- **Por quê:** a base de itens **tem** o número humano do pedido na coluna `name` (não só o `id`/gid). Provado no dado (ver abaixo).
- **Descartado:** Caminho B (usar a base Vendas como tradutora) — desnecessário, já que o `name` existe na própria base de itens.
- **ADR criado?** Não (a decisão de arquitetura será fechada no chat da construção, com spec/ADR próprios). Registrado aqui e na `ARCHITECTURE.md` §3 como achado de dado.

### CMV em 3 camadas (definido pelo João, será construído no outro chat)
- **Decisão:** resolver a fonte dos itens de cada pedido em ordem: **(1)** base histórica `bases/itens_historico.csv`; **(2)** planilha MC Growth (aba Itens, janela ao vivo); **(3)** estima CMV = 30% da receita (regra já existente, `cascata.CMV_ESTIMADO_FRACAO`).
- **Por quê:** estende o CMV real para (quase) toda a história sem quebrar a janela atual; a planilha cobre pedidos muito recentes ainda fora do export estático; 30% é a rede final.
- **ADR criado?** Não nesta sessão — sai no chat da construção.

---

## Problemas encontrados

### Confirmar a chave de junção entre as duas bases silver
- **Descrição:** não estava documentado se a base de itens tinha o número humano do pedido (para casar com o `nome` do HubSpot) ou só o `gid`.
- **Causa raiz:** a aba Itens da planilha só traz `id` (gid); o schema completo da tabela silver não estava no projeto.
- **Solução aplicada:** o João trouxe amostras das duas bases. O pedido **510969** aparece nas duas e bate em **3 campos** ao mesmo tempo: `nome`/`name` = 510969, e-mail = gbcmelo@yahoo.com.br, `valor`/`total_price` = 836,84. Junção confirmada pela coluna `name`.
- **Status:** resolvido.

---

## Estado do projeto agora

### Funcionando
- Tudo como estava no início da sessão (nenhum código tocado). Painel/V2/V4 intactos.

### Quebrado / incompleto
- A construção do CMV histórico em 3 camadas **não foi feita** — só o prompt. Roda no outro chat.

---

## Próximo passo

1. **Outro chat:** implementar o CMV em 3 camadas com o prompt entregue; começa por spec (mexe em dinheiro).
2. **Antes de puxar a base inteira:** rodar a query de **cobertura de custo por ano** (quantos % dos SKUs antigos existem na tabela de Custos de hoje) — decide se o "CMV real de 2022" é real ou meio-real. (Precisa saber se a tabela de Custos está no BigQuery ou só na planilha.)
3. **Decidir** se a 2ª camada (planilha) é mesmo necessária ou se a base histórica já cobre tudo.

---

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** nota em §3 (pontes de junção) registrando que a base silver de itens carrega `name` (número humano) → ponte direta `hubspot.nome ↔ itens.name`, dispensando a Vendas; e nota do início da Opção 1 (base histórica de itens).
- **`CLAUDE.md`:** não mudou.
- **`docs/decisions/`:** nenhum (ADR sairá no chat da construção).
- **`docs/specs/`:** nenhum (spec sairá no chat da construção).
- **`PRODUCT.md`:** não mudou.
