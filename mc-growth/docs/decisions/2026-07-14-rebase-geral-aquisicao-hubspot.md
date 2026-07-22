# ADR — Re-base do painel geral e da aquisição no HubSpot (janela atual idêntica, história estimada)

**Data:** 2026-07-14
**Status:** Aceito (build nesta sessão)
**Tema:** rebase-geral-aquisicao-hubspot

> Complementa os ADRs da V4 (`2026-07-10-v4-*`). Estende a fonte HubSpot — hoje só na aba de
> coortes — para o **painel geral (V1)** e a **aquisição (V2)**, destravando **história** sem
> perder a precisão da janela atual.

## 1. Contexto

O painel geral e a aquisição leem a **aba Vendas** da planilha, que cobre só **abr–jul/2026**. Por
isso não dá para ver a MC de um mês passado. A base **HubSpot** (`hubspot_deals.csv`) cobre
**2021→hoje** e já está no projeto (fonte da V4). A ponte `nome → Vendas.order_name` casa **99,7%**
na janela atual. O João decidiu (2026-07-14) re-basear **as duas** telas no HubSpot para destravar
história e unificar a fonte — **mas mantendo a janela atual idêntica** (onde há itens reais).

## 2. Decisão

1. **Roteador pela borda da janela de Vendas `[vmin, vmax]`** (hoje abr23–jul13/2026):
   - Período **dentro** da janela → **motor real (planilha)**: a lógica de hoje, **inalterada**
     (`net_revenue`, CMV real via Itens×Custos, deduções abertas, exclusões AnjosFrach/pontuais,
     `customer_type` para novos). **Os números da janela NÃO mudam.**
   - Período **fora** da janela → **motor estimado (HubSpot)**: Vendas = Σ `valor`; margem de produto
     = **0,25 × valor** (deduções embutidas nos 25%, sem linhas abertas); novos por `tipo_de_venda`
     (cross-canal); universo **Shipped + Comercial**; mídia da aba `Midia` (2021+, imposto FB só ≥2026-01).
   - Período que **cruza** a borda → **misto** (real na parte de dentro + estimado na de fora).
2. **Rótulo de confiança** no resultado: **real** / **parcial (estimada)** / **mista**.
3. **Degradação graciosa:** se o `hubspot_deals.csv` faltar, as duas telas voltam ao comportamento de
   hoje (só a janela real) — **não quebram** (mantém a invariante da V4).
4. **Reuso de uma verdade de custo:** o motor real segue usando `cascata.juntar_custos`; o estimado
   usa 0,25×valor (mesmo mecanismo da coorte). Nenhuma verdade de custo nova.

## 3. Motivação

- **História sem mentir precisão:** onde há itens (janela atual) a MC é real; onde não há, é estimada
  e **marcada** — o painel não finge precisão que não tem (mesma filosofia da V4).
- **Janela idêntica = risco baixo:** o número que o João valida todo dia (junho R$ 2,05M) não se move,
  porque dentro da janela nada muda (o HubSpot é ignorado ali).
- **Fonte única de fato:** as três telas passam a poder olhar o mesmo histórico do HubSpot.

## 4. Alternativas consideradas

- **Trocar tudo pro HubSpot (inclusive a janela atual):** mais consistente, mas os números atuais se
  deslocam (valor vs net_revenue +1,1%; +Comercial; tipo_de_venda vs customer_type). **Rejeitada** pelo
  João — quer a janela atual idêntica.
- **Só re-basear a aquisição:** menor, mas não destrava história no painel geral. **Rejeitada** — quer
  as duas.
- **Boundary por casamento (matched/unmatched) em vez de por data:** faria junho ≠ hoje (os ~0,3%
  não-casados entrariam como estimado). **Rejeitada** — a borda é por **data** (dentro da janela,
  ignora o HubSpot) para garantir o idêntico.

## 5. Consequências

### Positivas
- Painel geral e aquisição passam a mostrar **qualquer mês** (2021→hoje).
- Janela atual **byte-idêntica** ao de hoje; V1/V2 sem regressão.
- Sem credencial nova (lê o mesmo arquivo local).

### Negativas / limites
- **História é MC parcial (25%)** — lê-se como tendência, não como fechamento (marcado na tela).
- **Exclusões AnjosFrach/pontuais** não se aplicam à história (sem itens) — aceito.
- **Deduções não abrem** na parte estimada (embutidas nos 25%).
- **"Novo" muda de régua** na história (cross-canal), como na coorte — a aquisição histórica não é
  comparável 1:1 com a janela atual (carimbo Shopify). Rotulado.

### O que fecha
- Trocar a janela atual de fonte (fica planilha/real).
- Duas verdades de custo (segue uma só: juntar_custos no real, 0,25×valor no estimado).

## 5-bis. Atualização (mesma data) — unificação total no `valor` do HubSpot

Depois de ver que a aba divergia da base filtrada (o João filtra `tipo_de_venda`, Σ`valor`, por
`data_de_fechamento`), o João decidiu **unificar tudo no HubSpot**, revertendo o "janela atual
idêntica":

- **Receita = `valor` do HubSpot** (não `net_revenue`), **período por `data_de_fechamento`** (não
  `processed_at`). Medido: `valor` é **sempre ≥ `net`** (2/3 idênticos; 1/3 maior, +R$19 méd;
  agregado +1,1%) — a diferença é **frete**, que entra no `valor` do HubSpot e não na coluna de
  `net_revenue` do Shopify. O João aceita (frete é receita legítima; o painel já subtrai o custo de
  frete). Consequência: **os números do painel/aquisição mudam** (~1-2%) e passam a **bater com a base**.
- **Custo por item (CMV) segue REAL** via a ponte `nome→pedido→Itens→Custos` na janela atual — não
  depende da receita ser valor ou net. Fora da janela, estimado 25%. Foi a **condição do João** para
  unificar ("se der pra pegar o custo por item, unifica") — e dá.
- **Painel e aquisição viram deals-based**: universo = deals por `data_de_fechamento`; Vendas = Σ`valor`;
  parte casada (janela de itens) com **CMV real** + deduções abertas; parte não-casada estimada 25%.
- **Fallback:** `deals=None` (CSV ausente) → volta ao motor antigo (Vendas/net), para não quebrar.
- **Coorte:** por ora mantém o net na parte real (é per-cliente, item à parte); alinhar depois se preciso.

Isso **substitui** o roteador "borda da janela" da decisão original (§2) pelo modelo deals-based —
que naturalmente dá o mesmo efeito (real na janela, estimado fora), mas com `valor`+`fechamento`.

## 6. Revisão
- Reavaliar quando a **Opção 1** (itens reais ano-a-ano do BigQuery) entrar: aí a história deixa de ser
  estimada e o roteador some (tudo real). Este ADR é a ponte até lá.
