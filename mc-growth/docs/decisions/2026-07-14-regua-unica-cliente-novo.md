# ADR — Régua única de "cliente novo" (carimbo do HubSpot + mês da estreia)

- **Data:** 2026-07-14 (3ª rodada da sessão)
- **Status:** aceita e implementada
- **Decisor:** João
- **Regra-mãe que este ADR instaura:** **todas as telas usam as mesmas definições; os valores têm
  de bater.** Divergência só com ordem explícita, rótulo na tela e ADR. Ver `CLAUDE.md` §11 e
  `ARCHITECTURE.md` §5-bis.

## Contexto

O João viu a aba **Aquisição** e a **A2 (auditoria da coorte)** com números diferentes para
junho/2026. As duas leem a **mesma base** (`hubspot_deals.csv`) — o que divergia era a **régua de
"cliente novo"**: a Aquisição usava o **carimbo** `tipo_de_venda`; a coorte derivava a 1ª compra
(o primeiro pedido de cada cliente). Diferença: R$ 10.818 (0,25%).

O João pediu: **usar a definição do HubSpot (o carimbo)** — e, mais importante, **acabar com a
divergência**: *"os valores têm que bater"*.

## O nó: a fonte se contradiz

O HubSpot tem **dois campos que discordam entre si**:
- `tipo_de_venda` (carimbo por pedido: `Primeira Compra` / `Recompra`);
- `data_primeira_compra` (quando o cliente estreou, cross-canal).

Em junho/2026, **5 pedidos** vinham carimbados `Primeira Compra` num mês **diferente** do mês de
estreia do próprio cliente. Enquanto os dois campos mandarem, a aba Aquisição (que olha o
**período**) e a coorte (que olha a **turma**) **nunca fecham** — divergiam em R$ 3.628.

*(O carimbo erra também para o outro lado: 59 pedidos que eram a 1ª compra do cliente vinham
marcados `Recompra`, e o mesmo cliente aparece carimbado "Primeira Compra" 2× no mesmo mês em 57
casos. Registrado, não corrigido — o conserto é a montante, no HubSpot.)*

## Decisão

**Cliente novo = pedido carimbado `Primeira Compra` E no mês em que o cliente estreou**
(`cascata.mascara_cliente_novo`). Ou seja: **o carimbo define**, mas **quando ele contradiz a data
de estreia, a data manda**.

Vale em **todas** as telas que separam novo × recompra: aba **Aquisição**, **bloco de novos da
A2**, coluna **"MC primeira compra"** da aba Cohorts.

## Consequências

- **Aquisição e A2 batem ao centavo** (junho/2026): Vendas-novos **R$ 4.357.887,48**, MC-novos
  **R$ 451.297,38**, **8.175 pedidos** — diferença **R$ 0,00** (provado por `checar_coerencia.py`).
- **Vendas-novos de junho cai 0,08%** (R$ 4.361.515 → R$ 4.357.887): os 5 pedidos contraditórios
  passam a contar como recompra.
- A coorte segue **cross-canal** (a estreia continua sendo a `data_primeira_compra`).
- **O painel geral não muda** (não usa novo × recompra).
- **Guarda automático:** `checar_coerencia.py` falha se as telas voltarem a divergir.
- **Junto:** a coorte passou a aplicar as **exclusões de negócio** (AnjosFrach/pontuais — ADR
  2026-07-02) que só o painel aplicava.

## Alternativas descartadas

- **Só o carimbo, sem cruzar com a estreia:** era o pedido literal do João, mas **mantinha a
  divergência** (R$ 3.628) entre as telas — contraria a regra-mãe que ele mesmo instaurou.
- **"É o 1º pedido do cliente" (derivada):** corrige os erros do carimbo, mas **ignora a definição
  da fonte** — o João pediu explicitamente para usar a do HubSpot.
- **Ancorar a safra no carimbo** (safra = mês do pedido carimbado): faria as telas baterem, mas
  **destruiria a coorte cross-canal** (a estreia via TikTok/assinatura sumiria).
