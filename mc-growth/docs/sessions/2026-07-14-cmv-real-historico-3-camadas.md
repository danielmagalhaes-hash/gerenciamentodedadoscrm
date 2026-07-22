# Sessão 2026-07-14 (3ª) — CMV real na história inteira (itens em 3 camadas)

**Modo:** B (construção). **Toca dinheiro (CMV).**
**Spec:** `docs/specs/2026-07-14-cmv-real-historico-3-camadas.md` ·
**ADR:** `docs/decisions/2026-07-14-cmv-real-historico-3-camadas.md`

---

## O que era o problema

O painel só sabia o **custo real** dos pedidos que cabem na janela estreita da planilha Google
(abr–jul/2026). Para todo o resto da história ele **chutava CMV = 30% da receita**. O João extraiu
do BigQuery a base de **itens de todos os pedidos** (1,3 milhão de linhas, desde out/2021) — o
chute podia virar **medição**.

## O que foi feito

Os itens de um pedido agora são resolvidos em **3 camadas**: a base histórica primeiro; a planilha
para os pedidos recentes demais (o export é uma **foto**, a planilha é a **ponta viva**); e, se não
houver itens em lugar nenhum, o 30% de sempre. A ponte ficou **direta**: o número do pedido do
HubSpot é o mesmo da base de itens (`nome` == `name`, os dois com `#`).

O custo continua vindo de **um lugar só** (`juntar_custos`) — as camadas decidem **quais itens
entram**, nunca **quanto custa** um item.

## O achado da sessão — um bug de dinheiro que era invisível

A primeira versão casou tudo por número e **junho mudou** (+R$ 1.734). Fui atrás de quais pedidos
tinham trocado de lado:

- os 37 eram **todos** `Negócio Fechado - Comercial`;
- o `nome` deles é um **número** (a doc dizia que era o nome do cliente) — de **outra numeração**;
- esse número casou com itens de pedidos Shopify de **~5 meses antes** (19 deles de outro ano).

Ou seja: a ponte direta ia colar **os itens de um pedido de janeiro num deal de junho** — custo
errado, no pedido errado, **em silêncio**. Na base inteira, 224 deals cairiam nisso.

**O código antigo não tinha o bug por sorte, não por regra:** ele passava pela aba `Vendas`, e o
Comercial não está lá. A ponte direta tirou a sorte do caminho.

**A trava:** só deal **`Shipped`** pode casar itens (`cascata.pode_casar_itens`) — que é o que o
`PRODUCT.md` sempre mandou. O contraste é gritante: `Shipped` casa com item do **mesmo dia**
(mediana 0, 99,9% em ±2 dias); Comercial, com **92 dias** de defasagem. Com a trava, junho voltou a
ser **byte-idêntico**.

## O que mudou de número

| | Antes (30% chutado) | Depois (item a item) |
|---|---|---|
| **jun/2026 (a janela que o João valida)** | R$ 2.173.703,35 | **R$ 2.173.703,35** ✅ **idêntico** |
| MC 2022 | R$ 3.031.878 | **R$ 2.292.476** (**−24,4%**) |
| MC 2023 | R$ 5.424.306 | R$ 5.389.687 (−0,6%) |
| MC 2024 | R$ 8.983.267 | R$ 8.788.118 (−2,2%) |
| MC 2025 | R$ 17.821.893 | **R$ 18.079.899** (+1,4%) |

**2022 dói:** o CMV real do ano foi **35,8%**, não 30% — o chute era otimista.

**Mas a leitura certa não é "2022 foi ruim":** o CMV real **oscila com a promoção**. Julho/2022 deu
**41,3%** (o ticket caiu para R$ 167 — queima de estoque) e a Black Friday, **40,5%**; meses
saudáveis ficam em 23–28%. **O número fixo de 30% apagava essa informação.** Por isso a direção
depende do **mês**, não do ano: a coorte de 2022-06 (cujos pedidos de estreia tinham CMV de 27,7%)
**subiu** de R$ 42,35 para R$ 50,33 de MC por cliente.

## Provas (critérios de aceite)

- ✅ **Janela atual byte-idêntica** — junho/2026, painel e aquisição: **todas as diferenças = R$ 0,00**.
  (Medido **antes de codar**: o CMV por pedido das duas fontes bate ao centavo nos 39.212 pedidos.)
- ✅ **`checar_coerencia.py` passa** — e agora roda **com** a base histórica ligada (antes ele estava
  provando o caminho degradado; corrigido).
- ✅ **O passado virou real** — jun/2025 saiu de `estimada` para `mista`; CMV do mês deixou de ser chute.
- ✅ **Degradação** — com o arquivo escondido, **todos os números voltam aos de hoje** e as 5 telas sobem.
- ✅ **5 telas** sobem no `AppTest` sem exceção.
- ✅ `.gitignore` — o arquivo (119 MB, contém e-mail) não vai para o Git.

## Ressalvas registradas (não escondidas)

- **Custo de HOJE aplicado ao passado** — o CMV de 2022 é "quanto custaria hoje", não o custo da época.
- **SKU sem custo cadastrado** → item entra como zero → CMV parcial, MC **otimista**: **6,4% das
  unidades em 2023**, 4,3% em 2024, 1,4% em 2025, 0,1% em 2026.
- **2021 continua estimado** (a base de itens começa em 21/10/2021).
- **Comercial continua estimado** — por decisão (§2 do ADR), não por falta de dado.
- **179 deals `Shipped`** (0,04%) casam com itens de mais de 30 dias de distância. Não mexi — não há
  evidência de que sejam colisões. Fica **medido**, não escondido.

## Para o João testar

`python3 -m streamlit run painel.py` → escolher **meses passados** no painel Geral. Antes vinham com
faixa amarela de "estimado"; agora vêm **reais**. E olhar a aba **3. Cohorts**: as safras antigas
mudaram (algumas para cima, outras para baixo — depende do mês ter sido de promoção ou não).

## Próximo passo sugerido

1. Levar os **137 SKUs sem custo** (e os 6,4% de 2023) ao time de Dados — é o que ainda deixa o CMV
   histórico parcial.
2. Corrigir as docs a montante que ficaram factualmente erradas (`PRODUCT.md` §3 diz que o Comercial
   grava o **nome do cliente** no campo `nome` — é **número**, e colide).
