# Spec — CMV real na história inteira (resolução de itens em 3 camadas)

> **Data:** 2026-07-14 (3ª sessão do dia) · **Modo B (construção)** · **TOCA DINHEIRO (CMV).**
> **Objetivo:** o CMV deixa de ser estimado em 30% no passado e passa a ser **real (item a item)**
> de **2022-01 até hoje**, usando a base histórica de itens que o João extraiu do BigQuery.
> Isto é a **"Opção 1"** que a ADR `2026-07-10-v4-arquitetura-mvp-coortes` deixou parkeada como
> "versão seguinte". Ela chegou.

---

## 0. Em uma frase

Hoje o painel só sabe o custo real dos pedidos que cabem na janela estreita da planilha Google
(abr–jul/2026) e **chuta 30% de CMV** para todo o resto da história. A base nova traz os itens de
**todos os pedidos desde 2021-10** — então o chute vira **medição**, e as três telas (Geral,
Aquisição, Cohorts) passam a mostrar MC **real** em qualquer mês.

---

## 1. A base nova (medida antes de codar, não assumida)

Arquivo: `bases/bq-results-20260714-171049-1784049063098.csv` → **renomear para
`bases/itens_historico.csv`** (nome estável; o `bq-results-...` muda a cada export).

| O que | Medido |
|---|---|
| Linhas | **1.296.047** (só o cabeçalho + 6 colunas) |
| Período | **2021-10-21 → 2026-07-14** |
| Pedidos distintos | **495.000** |
| SKUs distintos | 1.144 |
| Memória (4 colunas do dinheiro, dtypes enxutos) | **62 MB** |
| Buracos | 2.164 linhas com `sku` vazio (viram "sem custo", entram no alerta); 0 `name` nulo; 0 quantidade nula |

**Cabeçalho real (confirmado):** `name, data_order, item_desmembrado_codigo, quantidade_final,
item_desmembrado_nome, email`.

**Descoberta que o prompt não previa:** o `name` da base de itens **também vem com `#`**
(`#7877`) — igual ao `nome` do HubSpot. O `lstrip("#")` vale **dos dois lados**, não só do HubSpot.

**Não lemos o `email`** (dado pessoal, não serve ao CMV) — fica de fora já na leitura (`usecols`).

---

## 2. As 3 camadas (a regra nova)

Para cada pedido, o custo é o **primeiro** que existir:

| Camada | Fonte | Chave | Quando pega |
|---|---|---|---|
| **1ª — primária** | `bases/itens_historico.csv` | `name` (nº do pedido) | 2021-10 → data do export |
| **2ª — fallback** | aba `Itens` da planilha (ao vivo) | `order_name → order_id → itens` | pedidos **novos demais** para o export estático |
| **3ª — último recurso** | nenhuma | — | **CMV = 30% da receita** (`CMV_ESTIMADO_FRACAO`, ADR `2026-07-14-cmv-estimado-30-por-cento`), marcado ⚠️ |

A 2ª camada **não é redundante**: o export é uma **foto** (parou em 14/07). Amanhã entram pedidos
que existem na planilha e **não** no arquivo — é exatamente esse buraco que ela tapa. Sem ela, o
pedido de amanhã cairia no chute de 30%.

**Sobre a ponte (o prompt pediu para avaliar):** com o `name` na base histórica, a camada 1 casa
**direto** (`hubspot.nome == itens_historico.name` — um pulo). Mas o **bridge antigo continua
existindo**, agora só a serviço da **camada 2**: a aba `Itens` da planilha **não tem** a coluna
`name` (só `order_id`), então para ela a volta `order_name → order_id → itens` é **obrigatória**.
Conclusão: o bridge não é apagado, é **rebaixado** a fallback.

---

## 3. O que NÃO pode quebrar — e a prova de que não quebra

**A janela atual tem que ficar byte-idêntica.** Isto é uma pré-condição, não uma esperança — então
foi **medida antes de escrever código**, comparando o CMV por pedido das duas fontes na janela de
sobreposição (abr–jul/2026):

```
pedidos na planilha (janela):        39.212
  presentes no histórico:            39.212   (100%)
  ausentes no histórico:                  0
max |diferença| por pedido:      R$ 0,000000
Σ |diferença|:                   R$ 0,00
CMV total planilha:              R$ 6.452.808,69
CMV total histórico:             R$ 6.452.808,69   ← ao centavo
```

As duas bases são **o mesmo pipeline** (a planilha é uma janela da mesma tabela silver). Por isso a
ordem das camadas ("histórico primeiro") **é segura**: trocar a fonte na janela atual não move um
centavo. Se elas divergissem, a byte-identidade venceria e o histórico entraria só **fora** da
janela — não foi preciso.

**Exclusões (AnjosFrach, ADR 2026-07-02):** passam a ser calculadas sobre a **união** das duas
bases de itens (antes: só a planilha). Medido: os pedidos AnjosFrach existem **só em 2026-05/06**
(29 pedidos) e a planilha **já excluía os 29**. Pedidos novos que só o histórico enxerga: **0**.
Ou seja, a mudança é **correta e de impacto nulo hoje** — e blinda o dia em que aparecer um
AnjosFrach antigo.

---

## 4. Impacto no dinheiro (o que muda de número)

O CMV real medido por ano, contra o chute de 30%:

| Ano | Receita casada | CMV real | **CMV % receita** | vs. o chute de 30% |
|---|---|---|---|---|
| 2022 | R$ 12,77 M | R$ 4,57 M | **35,8%** | ⬆️ pior — **a MC de 2022 vai CAIR** |
| 2023 | R$ 25,47 M | R$ 7,68 M | **30,1%** | ≈ igual |
| 2024 | R$ 43,12 M | R$ 13,13 M | **30,4%** | ≈ igual |
| 2025 | R$ 78,27 M | R$ 23,22 M | **29,7%** | ligeiramente melhor |
| 2026 | R$ 47,00 M | R$ 13,79 M | **29,3%** | ligeiramente melhor |

**Duas leituras honestas disso:**
1. O 30% da ADR de hoje de manhã **se confirmou como uma boa estimativa** para 2023→2026 (o real é
   29,3–30,4%). O painel não vai dar um pulo — vai **ganhar precisão**.
2. **2022 é a exceção e vai para o vermelho relativo:** o CMV real era **35,8%**, quase 6 pontos
   pior que o chute. As safras de 2022 nas coortes vão mostrar **menos MC** do que mostram hoje.
   Isso não é um bug — é o chute otimista sendo corrigido pela medição.
   *(Ressalva: parte disso pode ser o "custo de hoje aplicado ao passado" — ver §6.)*

**Nenhuma dobra de kit no histórico.** A dobra (ADR 2026-07-09) apareceria como CMV/receita de
50–60%; o medido é 29–36% em toda a série. O export do BQ **já vem com a correção da fonte**.

---

## 5. Cobertura (o "real" é real mesmo?)

**Cobertura da ponte** (deals do HubSpot que acham seus itens):

| Ano | % deals casados | % receita casada |
|---|---|---|
| 2021 | 0,3% | 0,3% ← a base de itens só começa em **2021-10-21** |
| 2022 | 98,0% | 97,0% |
| 2023 | 98,2% | 96,8% |
| 2024 | 98,3% | 97,4% |
| 2025 | 99,3% | 99,0% |
| 2026 | 99,5% | 99,2% |

**2021 continua estimado em 30%** (13.980 deals) — a base histórica não vai tão longe. Os ~1–3% que
não casam em cada ano (e o "Comercial", que grava o nome do cliente no lugar do nº do pedido) também
seguem estimados. **A camada 3 não morre — ela encolhe.**

**Cobertura de custo por SKU** (o SKU do pedido existe na tabela de Custos de hoje?):

| Ano | Unidades | % unidades **sem** custo |
|---|---|---|
| 2022 | 153.367 | 1,7% |
| 2023 | 260.940 | **6,4%** |
| 2024 | 401.091 | **4,3%** |
| 2025 | 623.459 | 1,4% |
| 2026 | 329.540 | 0,1% |

Onde falta custo, o item entra **como zero** (regra de sempre: custo 0 = faltando, vira alerta, não
some) → o CMV daquele pedido fica **parcial** e a MC, **otimista**. Em 2023, 6,4% das unidades. Isso
vai para a tela como aviso, não some no meio da conta.

---

## 6. Ressalvas do "real" (rotular, não fingir precisão)

1. **Custo de HOJE aplicado ao passado.** A tabela de Custos é a atual. O CMV de 2022 é
   *"quanto custaria hoje o que foi vendido em 2022"*, não o custo da época. É a mesma convenção que
   o painel já usa — mas no passado ela **pesa mais**. Provável parte da alta de 2022 (35,8%).
2. **SKU antigo/descontinuado** pode não estar na tabela → cobertura parcial (§5).
3. **A base é uma foto** (14/07). O João re-extrai quando quiser; até lá, a camada 2 cobre a ponta.
4. **Nada disto é fechamento contábil** (vale desde a V1).

---

## 7. Como fica o código (o mínimo necessário)

| Onde | O quê |
|---|---|
| `dados.py` | **`carregar_itens_historico()`** — lê o CSV local, 4 colunas, dtypes enxutos, `lstrip("#")`, data sem hora. Arquivo ausente → devolve **vazio** (não levanta erro). |
| `cascata.py` | **`cmv_por_nome(dados, hist)`** — a resolução das 3 camadas num só lugar: monta a tabela de itens por **número do pedido** (histórico ∪ planilha-para-quem-falta) e passa por **`juntar_custos`** — *a única verdade de custo do projeto, intocada*. Devolve CMV + alertas por `order_name`. |
| `cascata.py` | `_cascata_de_deals` e `_pedidos_excluidos` passam a consultar `cmv_por_nome` / a união. |
| `coortes.py` | `_mc_produto_por_deal` troca o bridge por `cmv_por_nome`. **Mesma fórmula de MC** — só o CMV fica real onde antes era chute. |
| `views/*` | **Nada.** As telas não mudam; só os números que já mostram ficam reais. Os rótulos `real/estimada/mista` que já existem passam a dizer "real" muito mais vezes. |
| `.gitignore` | **`itens_historico.csv`** (119 MB + contém e-mail). |

**Não** se cria uma segunda lógica de custo. `juntar_custos` continua sendo o único lugar que sabe
multiplicar quantidade por custo.

**Memória/velocidade:** o arquivo é lido **uma vez** (`st.cache_data`), só 4 colunas (62 MB), e é
imediatamente **reduzido** a um índice `pedido → CMV` (495 mil linhas) que é o que o cálculo usa.

---

## 8. Critérios de aceite (o que eu tenho que provar no fim)

- **CA1 — Byte-identidade da janela atual.** Junho/2026 no painel Geral: MC **R$ 2.173.703**
  (idêntica ao valor de hoje, ao centavo). Aquisição de junho: Vendas-novos **R$ 4.361.515,03**,
  MC-novos **R$ 452.861,30**, 8.180 pedidos. **Diferença exigida: R$ 0,00.**
- **CA2 — Amarração preservada.** MC real por pedido == Lucro Bruto do painel (max |dif| = 0);
  reconciliação coorte ↔ triângulo exata em todas as safras.
- **CA3 — O passado vira real.** Um mês histórico (ex.: 2025-06) sai do rótulo "estimada" para
  "real"; o CMV daquele mês passa a ser item a item.
- **CA4 — Degradação.** Renomeando `itens_historico.csv`, o painel **continua subindo** e volta
  exatamente ao comportamento de hoje (planilha na 2ª camada, 30% na 3ª).
- **CA5 — As 4 telas sobem** no `AppTest` sem exceção.
- **CA6 — Cobertura reportada** (a % de unidades sem custo por ano não fica escondida).

---

## 9. O QUE A CONSTRUÇÃO DESCOBRIU (a spec estava incompleta)

### 9.1 A ponte direta por número tinha uma armadilha — **colisão de numeração**

A primeira versão do código casou `HubSpot.nome == itens.name` para **todo** deal. Resultado: a
janela atual **mudou** (junho: MC 2.173.703 → 2.175.437, +R$ 1.734) — o CA1 falhou na hora. Fui
atrás de **quais** pedidos tinham trocado de lado, e o achado é sério:

- os 37 pedidos que "viraram reais" em junho eram **todos** `Negócio Fechado - Comercial`;
- o `nome` deles é um número (`423658`), **não** o nome do cliente (a documentação dizia que era);
- esse número casou com itens de pedidos Shopify de **~5 meses antes** (defasagem de 155 a 168
  dias; 19 dos 37 casaram com itens de **outro ano**).

Não é o mesmo pedido: é **outra numeração que colide** com a do Shopify. Sem trava, o painel
coleria os itens de um pedido de janeiro num deal de junho — **custo errado no pedido errado, em
silêncio**. Na base inteira: **224 deals Comerciais** cairiam nessa armadilha (defasagem mediana
de 92 dias).

**Por que o código antigo não tinha o bug:** ele casava via aba `Vendas`, e o Comercial não está
na `Vendas`. Escapava **por sorte**, não por regra. A ponte direta tirou a sorte do caminho.

**A trava (`cascata.pode_casar_itens`):** só deal **`Shipped`** pode procurar itens pelo número.
Comercial = **sempre estimado (30%)** — que é exatamente o que o `PRODUCT.md` §3 já mandava. Prova
do contraste: os `Shipped` casam com o item do **mesmo dia** (defasagem mediana **0**, 99,9% dentro
de ±2 dias); o Comercial, com **92 dias** de defasagem. Com a trava, junho voltou a ser
**byte-idêntico**.

### 9.2 Impacto medido no painel (ano fechado) — o que muda de verdade

| Ano | Vendas | MC antes (30% chutado) | MC depois (item a item) | Diferença |
|---|---|---|---|---|
| 2022 | R$ 13,16 M | R$ 3.031.878 | **R$ 2.292.476** | **−R$ 739.402 (−24,4%)** |
| 2023 | R$ 26,32 M | R$ 5.424.306 | R$ 5.389.687 | −R$ 34.619 (−0,6%) |
| 2024 | R$ 44,25 M | R$ 8.983.267 | R$ 8.788.118 | −R$ 195.149 (−2,2%) |
| 2025 | R$ 79,06 M | R$ 17.821.893 | **R$ 18.079.899** | +R$ 258.006 (+1,4%) |
| jun/2026 (janela) | — | R$ 2.173.703 | **R$ 2.173.703** | **R$ 0,00** ✅ |

### 9.3 O 30% fixo escondia os meses de promoção

O CMV real **oscila muito** mês a mês — e a oscilação tem significado de negócio:

| Mês | Ticket | CMV % |
|---|---|---|
| 2022-05 | R$ 357 | 27,5% |
| **2022-07** | **R$ 167** | **41,3%** ← queima de estoque (ticket despenca) |
| **2022-11** | R$ 351 | **40,5%** ← Black Friday |
| 2023-04 | R$ 423 | 23,0% |

É isto que puxa 2022 para 35,8% no ano — **não** uma piora geral, mas **meses de promoção**. Um
número fixo de 30% apagava essa informação. **Consequência para a coorte:** safras de meses
saudáveis **sobem** (a de 2022-06, cujos pedidos de estreia tinham CMV de **27,7%**, subiu de
R$ 42,35 para R$ 50,33 de MC/cliente no m+0), e safras de meses de queima **caem**. A direção
depende do mês — não há um "efeito 2022" único.

---

## 10. Fora de escopo (uma coisa por vez)

- Mudar a régua de "cliente novo", a fórmula das deduções, ou o 30% (segue valendo na camada 3).
- Recalcular o custo *da época* (custo histórico por SKU) — não existe base para isso.
- Trazer 2021 para o real (a base de itens não alcança).
- Mexer nas telas.
