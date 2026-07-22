# ADR — CMV real na história inteira: itens em 3 camadas, e só `Shipped` casa

- **Data:** 2026-07-14 (3ª sessão)
- **Status:** aceita, construída e verificada
- **Contexto:** Modo B (construção). **Toca dinheiro (CMV).**
- **Spec:** `docs/specs/2026-07-14-cmv-real-historico-3-camadas.md`

---

## Contexto

Até hoje o painel só tinha o custo real dos pedidos que cabem na janela estreita da planilha
Google (abr–jul/2026) e **estimava CMV = 30% da receita** em todo o resto da história
(ADR `2026-07-14-cmv-estimado-30-por-cento`). A ADR `2026-07-10-v4-arquitetura-mvp-coortes` já
previa a saída — a "Opção 1", parkeada: puxar os **itens históricos** do BigQuery para um arquivo
local, como se fez com o HubSpot. O João extraiu a base (1,3 milhão de linhas, 2021-10 → 2026-07-14)
e ela chegou.

## Decisão

### 1. Os itens de um pedido são resolvidos em **3 camadas**, nesta ordem

1. **`bases/itens_historico.csv`** (local, export do BigQuery) — a história inteira;
2. **aba `Itens` da planilha** (ao vivo) — só os pedidos que o export ainda não viu (ele é uma
   **foto**; o pedido de amanhã só existe na planilha). **Não é redundância — é a ponta viva.**
3. **nada** → **CMV = 30% da receita** (a regra de sempre), marcado ⚠️.

A camada 1 é **primária e segura**: medido antes de codar, o CMV por pedido das duas fontes é
**idêntico ao centavo** nos 39.212 pedidos da janela de sobreposição (max |dif| = **R$ 0,000000**)
— são o mesmo pipeline. Por isso trocar a fonte não move o número que o João valida.

### 2. **Só o deal `Shipped` pode casar itens.** O Comercial é **sempre** estimado.

`cascata.pode_casar_itens`. **Esta é a parte não-óbvia, e é uma trava de dinheiro.**

Descobriu-se na construção que o `Negócio Fechado - Comercial` grava no campo `nome` um **número
de outra numeração** (não o nome do cliente, como a doc dizia) — e esse número **colide** com
números de pedido Shopify **antigos**. Medido:

| | Defasagem entre a data do deal e a data dos itens que ele casa |
|---|---|
| `Shipped` (legítimo) | mediana **0 dias**; 99,9% dentro de ±2 dias |
| Comercial (colisão) | mediana **92 dias**; em junho/2026, 37 deals casaram com itens de **janeiro** |

Sem a trava, o painel colaria **custo errado em pedido errado, em silêncio** (224 deals Comerciais
na base inteira). O código antigo não tinha o bug porque casava via aba `Vendas`, onde o Comercial
não existe — escapava **por sorte, não por regra**. A ponte direta tirou a sorte do caminho; a
trava põe a regra no lugar dela. É também o que o `PRODUCT.md` §3 sempre mandou.

### 3. O custo continua com **um dono só**

`cascata.juntar_custos` (CLAUDE.md §11). As camadas decidem **quais linhas de item entram**; nunca
**quanto custa** um item. `cmv_por_nome` é o irmão de `cmv_por_pedido` (por número em vez de `gid`).

### 4. As exclusões (AnjosFrach) passam a varrer a **união** das duas bases

Antes só a planilha era varrida. Medido: os 29 pedidos AnjosFrach são todos de 2026-05/06 e a
planilha **já os excluía** — impacto **zero** hoje. É blindagem para o dia em que aparecer um antigo.

## Consequências

**O que melhora**
- CMV **real (item a item)** de **2022-01 até hoje** — 98% a 99,5% dos pedidos casam por ano.
- O painel, a aquisição e as coortes ganham precisão **sem** mudar de régua (a mesma receita de custo).
- A oscilação real do CMV volta a aparecer: **julho/2022 = 41,3%** (queima: ticket cai a R$ 167) e
  **novembro/2022 = 40,5%** (Black Friday), contra 23–28% em meses saudáveis. **O 30% fixo apagava
  os meses de promoção** — essa informação estava sendo jogada fora.

**O que dói (e é honesto)**
- **A MC de 2022 cai 24,4%** (R$ 3,03 M → R$ 2,29 M): o CMV real do ano foi **35,8%**, não 30%. O
  chute era otimista. 2023 (−0,6%) e 2024 (−2,2%) quase não mudam; **2025 sobe 1,4%**.
- **A direção depende do mês, não do ano:** a coorte 2022-06 (cujos pedidos de estreia tinham CMV de
  27,7%) **subiu** de R$ 42,35 para R$ 50,33 de MC/cliente. Safras de meses de queima caem.

**O que continua estimado (a 3ª camada não morre, encolhe)**
- **2021 inteiro** (13.980 deals) — a base de itens só começa em **2021-10-21**.
- Todo o **Comercial** (por decisão, §2) e os ~1–3% de `Shipped` que não casam.

**Ressalvas do "real" (rotuladas, não escondidas)**
- **Custo de HOJE aplicado ao passado** — o CMV de 2022 é "quanto custaria hoje o que se vendeu lá",
  não o custo da época. Provavelmente parte da alta de 2022.
- **SKU sem custo cadastrado** → item entra como zero → CMV **parcial** e MC **otimista**:
  **6,4% das unidades em 2023**, 4,3% em 2024, 1,4% em 2025, 0,1% em 2026.
- A base é uma **foto** (14/07/2026); re-extrair quando quiser.

## O que isto impede no futuro

- Tratar o `nome` do Comercial como número de pedido (é outra numeração — **colide**).
- Casar itens por número sem perguntar a etapa do deal.
- Criar uma segunda lógica de custo fora de `juntar_custos`.
- Depender do arquivo: ausente, o painel **volta exatamente ao comportamento de hoje** (provado).

## Alternativas descartadas

- **Manter a planilha como camada 1 dentro da janela** (para garantir byte-identidade): desnecessário
  — as duas fontes são idênticas ao centavo; seria uma regra arbitrária a manter para sempre.
- **Guarda de data no `Shipped`** (recusar item com defasagem > 30 dias): 179 casos em 442 mil
  (0,04%). Não aplicado — mexeria em número sem evidência de que são colisões. **Anotado como
  resíduo medido**, não como dívida escondida.

## Como reverter

Apagar/renomear `bases/itens_historico.csv`. O painel volta ao comportamento anterior (planilha na
2ª camada, 30% na 3ª) — **provado**: com o arquivo escondido, todos os números voltam aos de hoje e
as 5 telas sobem.
