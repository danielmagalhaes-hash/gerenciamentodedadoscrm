# ADR — Excluir da análise os pedidos com camisetas AnjosFrach

**Data:** 2026-07-02
**Status:** Aceito
**Tema:** excluir-anjosfrach

---

## 1. Contexto

Ao listar os SKUs vendidos sem custo cadastrado (junho/2026), 13 dos 16 SKUs eram
variações de uma mesma linha, `CamiseAnjosFrach01..13` (~234 unidades). Eram o maior
bloco do alerta "SKU sem custo".

O João classificou essas camisetas como **fora do escopo da análise de Margem de
Contribuição** e pediu para removê-las. Duas escolhas foram feitas com ele
(via pergunta direta): remover o **pedido inteiro** (não só a linha da camiseta) e
tornar a exclusão **permanente no painel** (não uma análise pontual).

Impacto medido em junho/2026: 22 pedidos, R$19.701 de Vendas (0,24%), dos quais 21
eram "puros" (só AnjosFrach) e 1 misto (AnjosFrach + outros produtos).

---

## 2. Decisão

Todo pedido que contenha **qualquer SKU com prefixo `CamiseAnjosFrach`** é removido
**inteiro** da análise — de Vendas, Pedidos e CMV — em todos os períodos. A regra vale
permanentemente no cálculo (`cascata.py`) e o painel mostra na tela quantos pedidos
foram excluídos no período (nada de exclusão silenciosa).

---

## 3. Motivação

- O João é a fonte de verdade do domínio; ele definiu que essas camisetas não fazem
  parte da MC que o painel deve medir.
- Remover o pedido inteiro (e não só a linha) foi a escolha dele — mais simples e, como
  21 dos 22 pedidos eram "puros", o efeito colateral sobre outros produtos é mínimo
  (1 pedido misto, ~R$2,9k).
- Some do alerta a maior fonte de "SKU sem custo" (16 → 3 SKUs), deixando o alerta
  focado no que realmente precisa de custo cadastrado.

---

## 4. Alternativas consideradas

### Alternativa A: remover só a linha da camiseta (manter o resto do pedido)
- **Prós:** preserva a receita/custo dos outros produtos no pedido misto.
- **Contras:** mais código; ganho ínfimo (1 pedido misto).
- **Por que foi descartada:** o João optou por "pedido inteiro".

### Alternativa B: apenas cadastrar o custo dessas camisetas
- **Prós:** mantém tudo na análise.
- **Contras:** contraria a decisão de que elas estão fora do escopo da MC.
- **Por que foi descartada:** o João quer as camisetas fora, não custeadas.

### Alternativa C: exclusão pontual (só uma análise, sem mudar o painel)
- **Por que foi descartada:** o João quer a regra valendo sempre.

---

## 5. Consequências

### Positivas
- MC do painel reflete o escopo que o João quer (junho: R$1.976.324).
- Alerta de SKU sem custo fica limpo (16 → 3 SKUs).
- Transparente: o painel informa quantos pedidos foram excluídos.

### Negativas
- As Vendas do painel passam a divergir de propósito do total Shopify bruto
  (−R$19,7k em junho). É intencional, mas precisa ser lembrado ao conferir com o Financeiro.
- No pedido misto, a receita/custo dos outros produtos também sai.

### O que essa decisão FECHA
> - Tratar AnjosFrach como venda normal na MC enquanto a regra existir.
> - Se um dia quiserem essas camisetas de volta, é só esvaziar `PREFIXOS_SKU_EXCLUIDOS`
>   em `cascata.py` — a regra é centralizada num único ponto.

---

## 6. Implementação

- **Onde se materializa no código:** `cascata.py` — constante `PREFIXOS_SKU_EXCLUIDOS`,
  função `_pedidos_excluidos`, e o filtro de `vendas_p` em `calcular`. `painel.py` mostra
  a contagem de excluídos.
- **Migration/refactor necessário:** não.
- **Regra a adicionar no CLAUDE.md:** não (coberto por este ADR + PRODUCT.md/spec).
- **Atualização no ARCHITECTURE.md (seção 5):** feita.

---

## 7. Revisão

- **Quando reavaliar:** se as camisetas AnjosFrach voltarem ao escopo, ou se surgir outra
  linha a excluir (aí é só somar o prefixo).
- **Sob que condições reverter:** esvaziar `PREFIXOS_SKU_EXCLUIDOS`.

---

## 8. Adendo (2026-07-02) — exclusão de pedido pontual (#501777)

Além da exclusão por SKU, o mesmo mecanismo passou a suportar exclusão de **pedidos
específicos por número humano** (`cascata.PEDIDOS_EXCLUIDOS_NOME`).

- **Caso:** o pedido **#501777** — receita R$0, 1 item com SKU em branco (qtd 8) —
  identificado como reposição/cortesia. O João pediu para ignorá-lo.
- **Investigação:** existem ~248 pedidos de receita R$0 no histórico (~32/mês), a maioria
  com itens (custo sem receita). Medido em junho: uma regra geral "ignorar todo R$0"
  daria MC +R$3.813 e −32 pedidos.
- **Decisão (via pergunta direta):** **NÃO** criar regra geral para R$0 — pode haver
  promo 100%-off legítima que se quer contar. Excluir **apenas o #501777**.
- **Implementação:** `PEDIDOS_EXCLUIDOS_NOME = ("501777",)`; o filtro em `calcular` remove
  por `order_name` além do filtro por SKU. Impacto junho: Pedidos 14024→14023; unidades
  sem custo 160→152 (some o SKU em branco); MC inalterada (pedido R$0, itens custo 0).
- **Reversível:** remover o número da tupla.
