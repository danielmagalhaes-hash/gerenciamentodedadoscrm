# ADR — CMV conta apenas itens de pedidos presentes na aba Vendas

**Data:** 2026-07-02
**Status:** Aceito
**Tema:** cmv-so-pedidos-da-aba-vendas

---

## 1. Contexto

Ao rodar o painel pela primeira vez com dados reais, um diagnóstico de amarração
apontou que, em junho/2026, **877 pedidos apareciam na aba `Itens` sem venda casada
na aba `Vendas`** — trazendo R$176k de CMV (6,37% do custo do mês) que inflava o
custo e subestimava a Margem de Contribuição.

A investigação separou esses 877 em dois grupos: 137 existiam na `Vendas` mas com
pagamento em outro mês (efeito de borda de data), e 740 não existiam na `Vendas` em
mês nenhum.

O João esclareceu a causa (informação de domínio que não estava nos documentos):
a aba `Itens` contém pedidos de **outros canais de venda** (B2B, TikTok Shop,
Mercado Livre, Assinatura), além do Shopify. A v1 é **só Shopify**. E, mais
importante, definiu a regra-mãe: **a origem de quais pedidos existem deve vir
sempre da aba `Vendas`.**

---

## 2. Decisão

A aba `Vendas` é a **fonte de verdade** de quais pedidos entram no painel. O CMV
passa a contar **apenas os itens de pedidos cujo `order_id` está na aba `Vendas`
do período**. O período de cada pedido é decidido pela data de pagamento da
`Vendas` — não pela data própria da aba `Itens`.

Na prática (`cascata.py`): em vez de filtrar `Itens` pela sua própria data, filtramos
`Itens` pelos `order_id` presentes na `Vendas` do período, e só então cruzamos com
os custos.

---

## 3. Motivação

- **Escopo da v1 é só Shopify** (PRODUCT.md 7.1). Itens de B2B/TikTok/ML/Assinatura
  não podem entrar no custo de um painel que só mostra a receita Shopify.
- **Coerência receita×custo:** contar custo de pedido sem a receita correspondente
  quebra a lógica da Margem de Contribuição (custo sem venda).
- Respeita o mantra "nunca produzir número sem rastrear a fonte": agora todo item do
  CMV pertence a um pedido que também gerou Vendas.
- Resolve de brinde o efeito de borda de data (os 137 de maio): o mês do pedido
  passa a ser o mês do pagamento na `Vendas`.

---

## 4. Alternativas consideradas

### Alternativa A: filtrar `Itens` pela própria data (como estava)
- **Descrição:** somar o CMV de todo item cuja `data_order` cai no período.
- **Prós:** simples; não precisa cruzar com a lista de pedidos da Vendas.
- **Contras:** inclui outros canais e desalinha receita×custo nas bordas de mês.
- **Por que foi descartada:** infla o CMV (R$176k em junho) e viola o escopo Shopify.

### Alternativa B: usar a base de Itens como fonte única de Vendas também
- **Descrição:** derivar receita e custo da mesma base de itens.
- **Prós:** uma fonte só, sem desencontro.
- **Contras:** a base de Itens mistura canais e não traz `net_revenue`; exigiria
  recalcular receita de forma diferente do relatório nativo.
- **Por que foi descartada:** contraria a regra do João (Vendas é a fonte de verdade)
  e o alinhamento pretendido com o Financeiro.

---

## 5. Consequências

### Positivas
- MC correta para o canal Shopify (junho: R$1,99M em vez de R$1,83M).
- Todo item do CMV pertence a um pedido real de venda (0 órfãos).
- Bordas de mês deixam de vazar custo entre períodos.

### Negativas
- Pedidos que estão na `Vendas` mas **não** têm itens na `Itens` (junho: 136, ~0,78%
  das Vendas) seguem sem CMV — geram receita sem custo. Aceito na v1 (impacto pequeno).
- O cálculo agora depende de a `Vendas` estar completa e correta; se um pedido pago
  Shopify faltar na `Vendas`, o custo dele some junto.

### O que essa decisão FECHA
> - Tratar a aba `Itens` como fonte independente de "o que foi vendido".
> - Somar CMV de qualquer canal que não seja Shopify enquanto a v1 for só-Shopify.
> - Quando os outros canais entrarem (v2+), a lógica de "quais pedidos contam" terá
>   de crescer junto com uma fonte de Vendas por canal — não basta usar a `Itens`.

---

## 6. Implementação

- **Onde se materializa no código:** `cascata.py`, função `calcular` — `itens_p` passou
  a ser `dados.itens` filtrado por `order_id ∈ Vendas do período`.
- **Migration/refactor necessário:** não (leitura pura; só mudou a regra de filtro).
- **Regra a adicionar no CLAUDE.md:** não (coberto por este ADR e pelo PRODUCT.md).
- **Atualização no ARCHITECTURE.md (seção 5 e ponto frágil 1):** feita.

---

## 7. Revisão

- **Quando reavaliar:** quando entrar o 2º canal de venda (v2+), ou se o alinhamento
  com o Financeiro exigir tratar devoluções/frete a partir do dado real.
- **Sob que condições reverter:** se a `Vendas` se mostrar incompleta a ponto de perder
  pedidos Shopify pagos — aí a fonte de verdade precisaria ser revista, não a regra.
