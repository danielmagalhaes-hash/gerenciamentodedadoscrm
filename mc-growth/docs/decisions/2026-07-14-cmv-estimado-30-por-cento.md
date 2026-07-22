# ADR — Onde falta custo, o CMV é estimado em 30% da receita (e não "margem de 25%")

- **Data:** 2026-07-14 (2ª sessão do dia)
- **Status:** aceita e implementada
- **Decisor:** João
- **Spec:** `docs/specs/2026-07-14-interface-menu-cascata-cmv-30.md`
- **Substitui:** a "margem estimada de 25%" do ADR `2026-07-14-rebase-geral-aquisicao-hubspot`
  e do ADR `2026-07-10-v4-arquitetura-mvp-coortes`.

---

## Contexto

O painel só tem **custo real** (item a item) para os pedidos que caem na **janela de itens** da
planilha (hoje 23/04–14/07/2026). Fora dela — todo o histórico (2021→mar/2026) e as vendas do
time **Comercial** (que nunca casam, porque gravam o nome do cliente no lugar do número do
pedido) — não há itens, e portanto não há CMV.

Até aqui, esses pedidos entravam com uma **margem de produto estimada em 25% da receita**,
direto, sem abrir deduções. Isso governava **os meses históricos** do painel/aquisição e **92,5%
das células** do triângulo de coortes.

## Problema

Os 25% eram um **chute**, e um chute pessimista. Medindo os meses em que há itens de verdade:

| Mês (real) | CMV / Vendas | Lucro Bruto / Vendas |
|---|---|---|
| 2026-05 | 29,0% | 42,8% |
| 2026-06 | 28,8% | 43,0% |

Ou seja: a margem de produto real é ~**43%**, não 25%. A estimativa antiga **subestimava a MC
histórica em ~17,5 pontos de receita** — safras antigas apareciam no vermelho por artefato da
estimativa, não por fato.

## Decisão

Onde não há itens, **estimar o CMV em 30% da receita** e deixar **todas as outras linhas seguirem
as fórmulas de sempre** (deduções e custos variáveis em %, sobre a receita inteira).

```
CMV        = CMV real (pedidos com itens) + 0,30 × receita sem itens
Deduções   = Vendas × 17,92%
Cost of Delivery = CMV + Vendas × 9,57%
Lucro Bruto = Vendas − Deduções − Cost of Delivery
```

Margem de produto implícita da parte estimada: **1 − 27,49% − 30% = 42,5%** da receita.

Consequências de forma:
- A linha **"Margem estimada (25%)"** deixa de existir na cascata. A única linha provisória passa a
  ser o **CMV**, marcado com **⚠️ "X% estimado a 30%"** quando parte dele vem da estimativa.
- Vale igual nas 3 telas (Geral, Aquisição, Cohorts) — a mesma constante
  (`cascata.CMV_ESTIMADO_FRACAO`) governa as três.

## Por que 30% e não 29%

Os 29% medidos são a média de dois meses de uma janela curta. Arredondar **para cima** deixa a
estimativa **conservadora** (CMV maior → MC menor): se errar, erra para o lado que não anima
gastar mídia a mais. Decisão do João.

## Consequências (assumidas com o número na mão)

- **Meses históricos e coortes antigas SOBEM.** Junho/2026 (quase todo real) subiu só
  **+R$ 21.535** (de R$ 2.152.168 para R$ 2.173.703, +1,0%) — o efeito veio dos 1,48% de receita
  não-casada (o Comercial). Nos meses 100% históricos o efeito é grande: o Lucro Bruto sai de 25%
  para **42,5%** da receita.
- **A janela real não muda em nada** (lá o CMV é item a item, e a estimativa não é acionada).
- **Não é precisão nova, é um chute melhor.** A estimativa segue marcada na tela. A cura de
  verdade é a **Opção 1** (itens históricos do BigQuery → CMV real ano-a-ano desde 2022), que
  aposenta esta constante.

## Alternativas descartadas

- **Manter os 25%:** conhecidamente errado (mede-se 43% no real) e enviesa a decisão de mídia para
  baixo nas coortes.
- **Usar 29% (o real medido):** mira o centro em vez da borda de baixo; o João preferiu o
  conservador.
- **Estimar por safra/ano** (um CMV% por época): mais fiel, mas não há dado para calibrar fora da
  janela — seria inventar precisão. Fica para a Opção 1, que resolve com custo real.
