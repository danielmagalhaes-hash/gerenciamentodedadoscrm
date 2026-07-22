# ADR — Fonte dos itens (CMV): base de venda, não a NF de saída

**Data:** 2026-07-04
**Status:** Aceito
**Tema:** fonte-de-itens-venda-nao-nf

---

## 1. Contexto

O CMV do painel soma os itens de cada pedido. Descobrimos (via a Auditoria de custos) que
a base de itens **explode os kits em dobro** → CMV inflado, MC subestimada em ~R$100 mil/mês
(junho/2026). Buscando uma fonte melhor, avaliamos a **NF-e de venda** (`silver_minimal_bling_nfe_fechamento`,
aba "2.1. Itens"), que casa com a Vendas por `numeroPedidoLoja` = final do `order_id`.

Comparação em 32.462 pedidos: NF idêntica à Shopify em **91%** (inclui os dobrados), mais limpa
em 7%, maior em 2%. Além disso, a NF **corta brindes** (ex: a carteira sai em nota de bonificação
separada, ou não é faturada).

## 2. Decisão

A fonte de itens do painel é a **base de venda (Itens Shopify, gid 1246117066)** — não a NF de saída.
A venda é a fonte mais confiável do que foi de fato vendido (inclui brindes). A NF fica **parkeada**
como possível fonte de **receita fiscal** no futuro (v2+), não de itens.

O bug de dobra de kit é **a montante** (na explosão compartilhada), então **não é corrigido no painel**
(deduplicar às cegas erraria — quantidades também vêm dobradas, e há brindes/kits aninhados). O conserto
definitivo é uma **base nova construída pelo time de Dados** — orientação em
`docs/orientacao-base-itens-confiavel.md`.

## 3. Motivação

- Puxar da **venda** é mais confiável que da NF (que dobra igual e ainda corta brinde).
- A NF diverge da receita comercial por design (é o lado fiscal) — não é a fonte certa para itens.
- Corrigir na fonte (uma vez, no data lake) conserta as duas bases e todos os períodos.

## 4. Alternativas consideradas

- **Trocar itens pela NF de saída:** testada e revertida — dobra em 91% e corta brinde.
- **Deduplicar no painel:** arriscado (quantidades dobradas, kits aninhados, brindes legítimos) →
  produziria número errado com cara de certo.
- **Paliativo `SKUS_KIT_VIRTUAL`:** ativo, mas pequeno (só SKUs virtuais conhecidos; não pega a
  duplicação de componentes, que é o grosso).

## 5. Consequências

- **Positiva:** painel na fonte mais confiável; nomes de produto (99,6%) via a mesma base.
- **Negativa / aceita:** o CMV segue inflado (MC subestimada ~R$100k/mês) até o time de Dados
  entregar a base limpa. Documentado; a correção é a montante.

### O que essa decisão FECHA
> - Usar a NF de saída como fonte de itens/CMV.
> - "Consertar" o kit no painel via dedução às cegas.

## 6. Implementação

- `dados.carregar_itens` lê a base de venda (gid 1246117066) com `item_desmembrado_nome` (nomes).
- Constantes da NF (`GID_ITENS_NF`, `_NF_NATUREZAS_CONTAM`, `_NF_STATUS_INVALIDO`) permanecem no
  código, sem uso ativo, caso a NF volte a ser útil.
- Orientação ao time de Dados: `docs/orientacao-base-itens-confiavel.md`.

## 7. Revisão

- **Quando reavaliar:** quando o time de Dados entregar a base de itens limpa (puxada da venda,
  kit explodido uma vez, brindes incluídos) — aí re-liga a fonte e revalida a MC.
