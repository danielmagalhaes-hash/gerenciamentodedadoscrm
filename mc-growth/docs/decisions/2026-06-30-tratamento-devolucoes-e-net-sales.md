# ADR — Tratamento de devoluções e definição de "Vendas" (net_sales) na cascata de MC

**Data:** 2026-06-30
**Status:** Em discussão (aguardando alinhamento com o Financeiro)
**Tema:** tratamento-devolucoes-net-sales

---

## 1. Contexto

A linha de topo da cascata de Margem de Contribuição usa a fórmula de relatório
nativa da Shopify, definida pelo João durante o discovery:

```
receita_final = net_sales − returns + shipping_charges
WHERE order_payment_status = 'paid'
  AND sales_channel != 'TikTok'
```

Surgiram dois pontos de risco durante a entrevista:

1. **Devoluções possivelmente contadas em duplicidade (ou triplicidade).**
   Pela definição da Shopify, `net_sales` = vendas brutas − descontos − devoluções,
   ou seja, as devoluções **já estão descontadas** dentro de `net_sales`. A fórmula
   ainda faz `− returns` novamente, e a cascata de MC tem uma **linha separada de
   "Devoluções"**. Há risco de a mesma devolução ser subtraída 2x ou 3x, fazendo o
   resultado final ficar menor que a realidade.

2. **Descontos/cupons embutidos no topo.** Como `net_sales` já remove descontos, a
   cascata não tem linha separada de "Descontos". Isso é uma escolha implícita que
   precisa ser confirmada com o Financeiro (se um dia quisermos enxergar cupons como
   linha própria, a fórmula do topo muda).

O João optou, conscientemente, por **manter as fórmulas como estão por enquanto**,
porque é o formato do relatório nativo da Shopify e precisa ser alinhado com o
Financeiro antes de qualquer ajuste.

---

## 2. Decisão

**Provisória:** manter a fórmula da Shopify como está
(`net_sales − returns + shipping_charges`, `paid`, excluindo TikTok) para o v1,
**sem** travar o modelo. A decisão definitiva sobre a duplicidade de devoluções fica
**pendente de alinhamento com o Financeiro**.

---

## 3. Motivação

- Fidelidade ao relatório que o time já usa hoje (Shopify nativo) evita divergência
  inicial de números enquanto o entendimento com o Financeiro não acontece.
- Evita travar o discovery numa questão contábil que não é o João quem decide sozinho.

---

## 4. Alternativas consideradas

### Alternativa A: Vendas líquida — apagar a linha "Devoluções"
- **Descrição:** topo = `net_sales` (já sem devoluções); remover a linha "Devoluções" da cascata.
- **Prós:** elimina a contagem dupla; mais simples.
- **Contras:** perde a visibilidade das devoluções como linha própria no painel.

### Alternativa B: Vendas bruta — manter "Devoluções" como linha
- **Descrição:** topo = vendas brutas + frete; manter "Devoluções" como linha separada e **remover** o `− returns` da fórmula do topo.
- **Prós:** enxerga devoluções no painel sem duplicar.
- **Contras:** exige reconstruir o número fora do formato nativo da Shopify.

---

## 5. Consequências

### Positivas
- Time começa a ver MC diária rápido, com base no relatório que já conhece.

### Negativas / riscos aceitos temporariamente
- **A MC exibida pode estar subestimada** enquanto a duplicidade de devoluções não for resolvida.
- Risco de o número do dashboard **não bater** com o fechamento do Financeiro — e isso precisa ser comunicado a quem olhar o painel, para não minar a confiança na ferramenta.

### O que essa decisão FECHA
> Nada de forma irreversível — é provisória de propósito. Mas enquanto durar, o número de MC **não deve ser tratado como verdade contábil**, apenas como indicador de gestão.

---

## 6. Implementação

- **Onde se materializa:** na query/fonte que alimenta a linha "Vendas" e a linha "Devoluções".
- **Regra a adicionar no CLAUDE.md:** quando for construir, marcar que a fórmula de Vendas é "modelo Shopify provisório, pendente de validação com Financeiro".
- **Atualização no ARCHITECTURE.md:** pendente (ainda não existe).

---

## 7. Revisão

- **Quando reavaliar:** assim que o João alinhar com o time Financeiro como devolução,
  PIS/COFINS+CBS e ICMS+IBS devem entrar na conta. Reavaliar **antes** de apresentar a
  MC como número oficial para o CEO/lideranças.
- **Sob que condições reverter:** se o número do dashboard divergir materialmente do
  fechamento mensal do Financeiro.
