# Orientação — base confiável de itens por pedido (para CMV)

**Para:** time de Dados / Data Lake (quem mantém as silvers de pedidos e a explosão de kits).
**De:** João (Growth) — projeto MC Growth (painel de Margem de Contribuição).
**Data:** 2026-07-04.
**Objetivo:** ter uma base de **itens por pedido** confiável, para calcular o **custo da mercadoria vendida (CMV)** corretamente. Hoje as bases disponíveis contam os itens dos kits **em dobro**, o que infla o CMV e subestima a margem em ~R$100 mil/mês.

---

## 1. Para que serve

O painel calcula a Margem de Contribuição do canal Shopify. O CMV é `custo do SKU × quantidade`, somando os itens de cada pedido. Para isso, precisamos, **por pedido**, dos **itens físicos que compõem a venda** — com o kit explodido corretamente nos seus componentes.

## 2. Qual base usar como fonte — **puxar da VENDA, não da NF de saída**

Testamos duas fontes; **nenhuma serve hoje**:

- **Itens Shopify (silver de pedidos):** explode o kit **em dobro**.
- **NF-e de venda (`silver_minimal_bling_nfe_fechamento`):** também dobra na maioria (~91% dos pedidos igual à Shopify) **e** ainda corta o **brinde** (ex: a carteira sai numa nota de bonificação separada, ou não é faturada).

**Decisão / requisito:** a base confiável deve ser construída **a partir da venda** (os itens que o cliente comprou no pedido), **não** a partir da saída fiscal (NF). A venda é a fonte mais confiável do que de fato foi vendido — inclusive brindes.

## 3. O problema, em detalhe (a explosão de kit dobra)

Ao desmembrar (explodir) os kits em seus componentes, a base duplica itens. Um kit de 5 itens vira ~10. Dois sabores, às vezes juntos:

1. **SKU virtual do kit fica junto dos componentes.** O código intermediário do kit (ex: `8301001172`, que representa "4 camisetas") permanece como linha **ao lado** das camisetas individuais já explodidas. O intermediário deveria sumir; só os componentes-folha ficam.
2. **Componentes repetidos.** O mesmo SKU aparece em **2 linhas** no mesmo pedido (ex: a Carteira `8301007000`, ou camisetas), em vez de 1 linha por SKU com a quantidade somada.

### Exemplos reais (abril/2026)

**#469395** (order id `6936646418684`) — kit "Compre 3 e leve 4 + Carteira":
- Shopify: 4 camisetas + carteira = **5 itens**. Base: **10** (soma de qtd), com o SKU virtual `8301001172` + carteira em 2 linhas. CMV **R$347,78** (deveria ser ~R$165).

**#469583** (order id `6937714884860`) — mesmo tipo de kit:
- Base Shopify: **10 itens** (Azul 2, Branca 2, Preta 3, Verde 1, Carteira 2) — dobrado, e ainda com um **Verde que a venda não tinha**. CMV **R$334,78** (deveria ser ~R$166).
- NF-e do mesmo pedido: 4 camisetas, **sem a carteira** (brinde cortado). Também errado, por outro motivo.

## 4. Como a base confiável deveria ficar

**Grão:** 1 linha por `(pedido, SKU-componente-folha)`.

**Regras de construção:**
1. **Fonte = a venda** (o pedido e seus itens), não a NF de saída.
2. **Explodir o kit até a folha:** cada kit vira apenas seus **componentes físicos finais**. **Não** emitir o SKU virtual/intermediário do kit junto dos componentes.
3. **Uma linha por SKU no pedido:** agrupar por `(pedido, SKU)` e **somar a quantidade** — sem linhas repetidas.
4. **Incluir os brindes** (o item grátis do "leve 4", a carteira, etc.) — eles têm custo e devem constar. Não depender da NF para isso.
5. A **soma das quantidades** dos componentes deve bater com o esperado do kit (ex: "4 + carteira" → 5 unidades, **não 10**).

**Colunas mínimas necessárias:**
| Coluna | Descrição |
|---|---|
| `order_id` (ou `numeroPedidoLoja`) | chave do pedido — casa com a venda Shopify (`gid://shopify/Order/<n>` ou o número `<n>`) |
| `sku` (`item_desmembrado_codigo`) | SKU do componente físico final |
| `quantidade` | quantidade daquele SKU no pedido (já somada) |
| `nome` (`item_desmembrado_nome`) | nome do produto (para auditoria) |

## 5. Como identificar o que está dobrando (para o conserto)

- **SKUs virtuais/intermediários:** códigos que aparecem como `item_original_codigo` (origem de explosão, `tipo_explosao = kit_desmembrado`, origem ≠ componente) **e também** como `item_desmembrado_codigo`. São os "nós do meio" da árvore — devem ser descartados após explodir até a folha.
- **Componentes repetidos:** pares `(pedido, item_desmembrado_codigo)` com mais de uma linha.

## 6. Como validar o conserto

Depois de gerar a base, conferir:
- **#469395** → 5 itens, CMV ≈ R$165 (era R$347,78).
- **#469583** → 5 itens (4 camisetas + carteira), CMV ≈ R$166 (era R$334,78).
- **Regra geral:** nenhum pedido deve ter o mesmo SKU em 2 linhas; a soma das quantidades por pedido deve bater com os produtos vendidos.
- O painel MC Growth tem uma **Auditoria de custos** que lista pedidos com custo % anormal — ela deve "esvaziar" bastante depois do conserto (hoje ~1.824 pedidos/junho suspeitos por dobra).

---

**Resumo do pedido:** uma base de itens por pedido, **construída a partir da venda**, com o **kit explodido corretamente uma vez** (componentes-folha, brindes incluídos, sem duplicar), 1 linha por `(pedido, SKU)`. Isso corrige o CMV e a margem de vez.
