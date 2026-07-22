# Spec — Aba "Portas de entrada" (1ª leva: produto de entrada)

> **Data:** 2026-07-15 · **Modo:** B (construção) · **Autor:** discovery João × Claude
> **Estado:** spec aprovada no discovery; **build pendente** (bloqueado pela validação do mapa SKU→linha).
> **Origem:** discovery desta sessão (`docs/sessions/2026-07-15-portas-de-entrada.md`), avaliação crítica do
> Fable, e os documentos `motor-crescimento-lucrativo-true-classic.md` + `Curso Pedrinho.md`.
> **Regra do §6 do CLAUDE.md:** spec é foto do dia. Se o rumo mudar, corrige-se por ADR, não reescrevendo aqui.

---

## 1. A decisão que a feature serve

Definir **CAC-teto / ROAS-alvo diferenciado por porta de entrada**: aceitar eficiência maior ou menor
conforme **quanto de Lucro Bruto cada porta devolve por cliente ao longo do tempo**. Hoje o João negocia
verba olhando só a 1ª compra (m+0); a tese (True Classic / Curso Pedrinho) é que **janelas maiores
justificam pisar mais fundo na mídia**, porque a recompra paga. A aba dá o argumento: *"quem entra por
Camiseta Minimal devolve R$ X de Lucro Bruto por cliente em 180 dias → posso aceitar CAC maior pra essa
porta."*

**Não** é: medir "o CAC da camiseta" (a mídia é bolo mensal, não se segmenta por produto — ver §5, coluna CAC).

## 2. Escopo

### 2.1 Entra (1ª leva)
- **Aba nova** no menu: **"4. Portas de entrada"** (`views/portas_entrada.py`). A aba Cohorts fica **intocada**.
- **Filtro de produto de entrada** + **filtro de data** no topo, valendo pras duas tabelas.
- **Tabela principal — por safra** (linhas = safra). Obedece ao **filtro de produto**: um produto → só as
  safras desse produto (estilo "Leitura A"); "todos" → coorte inteira (idêntica à Cohorts).
- **Tabela secundária — por linha de produto** (linhas = linha de produto; "Leitura B"). Obedece ao
  **filtro de data**: agrega as safras do período; mostra **todas as linhas de uma vez** pra comparar.
- **Colunas** (as duas tabelas): `1ª compra | 30D (m+0) | 60D (m+1) | 90D (m+2) | 180D (m+5) | 365D (m+11)`
  + coluna **CAC**.
- **Célula = Lucro Bruto acumulado por cliente (R$)** — cumulativo, **antes da mídia**.
- **N mínimo = 300 clientes** (ajustável na tela); abaixo → "—" com o nº de clientes ao lado.
- **Artefato novo:** mapa **SKU → linha de produto** (`docs/rascunho-sku-linha-produto.csv`), validado pelo João.

### 2.2 Fica pra depois (backlog — `docs/BACKLOG.md`)
- **Canal de entrada** e **oferta de entrada** — sem dado hoje; instrumentar a montante primeiro.
- **% de recompra 90/180d** na tela — o João prefere o LTV em Lucro Bruto.
- **Régua fully-loaded** (devolução/troca/CX/juros/criativo) — a MC/Lucro Bruto seguem **parciais**.

### 2.3 Nunca
- CAC "por produto" fingindo que a mídia inteira foi pra uma porta (inflaria o CAC — desonesto).

## 3. Definições do domínio (regras de dinheiro/dado)

### 3.1 Produto de entrada (regra PROVISÓRIA — vai pro ADR, questionar no futuro)
- **= linha de produto** (não SKU, não balde). "Camiseta Minimal" ≠ "Camiseta Fitness"; "Calça Jeans 1.0" ≠
  "2.0". Cor e tamanho da mesma linha **juntam**.
- Olha-se o **pedido de estreia** do cliente (a 1ª compra).
- **Categoria única no pedido** → aquela linha é a porta.
- **Mais de uma categoria** → porta **"Multiprodutos"**.
- 2 unidades da mesma linha (iguais ou de cores/tamanhos diferentes) → ainda é **uma** categoria.
- **Brindes removidos antes de avaliar a regra** (decisão João 2026-07-15): itens de papel `brinde` no
  mapa — **carteira, "BRINDE", Perfume, Skincare** — saem do pedido antes de decidir a porta (camiseta +
  carteira → Camiseta). Pedido que **só** tem brinde → "Produto desconhecido".
- **Sem produto identificável** → porta **"Produto desconhecido"** (linha própria, visível). Casos: estreia no
  **Comercial** (colisão de numeração, nunca casa itens), estreia **antes de out/2021** (base começa lá),
  estreia **fora do Shopify** (coorte cross-canal, pedido não está na base de itens), e **SKU sem nome
  cadastrado** (`⚠ SEM NOME`, papel `desconhecido` no mapa — 134 SKUs, 2,6% das unidades).
- ⚠ **Detalhe de build a decidir:** como o item `desconhecido` interage com a regra de categoria única —
  camiseta + item-sem-nome vira "Multiprodutos" ou "Camiseta"? (a resolver na construção; anotado.)

### 3.2 Colunas = a MESMA régua da aba Cohorts (mês-calendário)
Os rótulos "D" são **apelidos** dos meses-calendário que a Cohorts já calcula — **não** dias corridos ao pé
da letra. Assim as duas telas batem por construção (nenhum ADR de divergência).

| Coluna | = idade Cohorts | Soma (cumulativo) |
|---|---|---|
| **1ª compra** | só a estreia | apenas o pedido de estreia (sem recompra do mesmo mês) |
| **30D (m+0)** | m+0 | mês-calendário da estreia (inclui recompra do mesmo mês) |
| **60D (m+1)** | m+1 | estreia → 2º mês-calendário |
| **90D (m+2)** | m+2 | estreia → 3º mês |
| **180D (m+5)** | m+5 | estreia → 6º mês |
| **365D (m+11)** | m+11 | estreia → 12º mês |

> Honestidade registrada: "30D" é apelido de "m+0"; pra quem estreia dia 25, o m+0 cobre ~6 dias, não 30.
> O João escolheu o apelido de propósito (é o que garante "bate com a Cohorts"). Rótulo mostra os dois.

### 3.3 Célula, CAC, maturidade
- **Célula = Lucro Bruto acumulado por cliente** (antes da mídia). Reusa **`coortes.ResultadoCoortes.lucro_bruto`**
  (dono único; a MC já desconta a mídia e contaria em dobro — ADR `2026-07-14-ratio-contra-cac-usa-lucro-bruto`).
- **CAC = blended do mês** (`mídia do mês ÷ TODOS os clientes novos do mês`) — **o mesmo valor pra qualquer
  produto filtrado**. É uma **régua de comparação**, não um CAC por produto. Na tabela por produto (período),
  é o CAC blended do período, repetido em todas as linhas.
- **Safra imatura → "—"** (disciplina de "safra fechada"; a célula 365D de uma safra de mai/2026 ainda não
  viveu 12 meses → não mostra número parcial).

## 4. Fonte de dados e ponte
- **Clientes / safra / idade / CAC / Lucro Bruto:** reuso direto de `coortes.py` (mesma régua das 3 telas).
- **Produto de estreia:** ponte `hubspot.nome → itens (name) → linha de produto (mapa)`. A base de itens é
  `bases/itens_historico.csv` (colunas: `name, data_order, item_desmembrado_codigo, quantidade_final,
  item_desmembrado_nome, email`; 1,3 M linhas, out/2021→hoje; 1.144 SKUs distintos, 993 nomes).
- **Mapa SKU→linha:** **VALIDADO pelo João (2026-07-15)** → `bases/mapa_sku_linha_produto.csv` (versionado).
  Colunas: `sku, linha, papel, nome_exemplo, unidades`. **26 linhas-porta** (95,1% un), 3 baldes `brinde`
  (2,3%), `Produto desconhecido` (2,6%). O João separou versões que o nome não distinguia (Jeans 1.0×2.0,
  Social Tech Classics×Malha, Polo 1.0/2.0/Tricot, Jaqueta Essential×Westfield). Rascunho original arquivado.

## 5. Coerência (guarda)
- Com **filtro de produto = "todos"**, a tabela por safra tem de ser **idêntica** ao Lucro Bruto acumulado
  por cliente da aba Cohorts (mesmo `coortes.lucro_bruto`, mesmas colunas de idade). → **novo check no
  `checar_coerencia.py`**.
- Soma das portas (incl. Multiprodutos + Produto desconhecido) = universo total da safra (nenhum cliente some).
- O CAC exibido = o CAC da aba Cohorts pra aquela safra.

## 6. Riscos e vieses (rotular na tela)
- **N pequeno por porta** (linha de produto é fina): janelas longas de linhas pequenas têm ruído → N mínimo 300.
- **Viés cross-canal:** quem estreia fora do Shopify cai em "Produto desconhecido" (não em sua porta real).
- **Régua parcial:** Lucro Bruto sem devolução/CX/juros/criativo. A **taxa de devolução por produto** — o custo
  que mais difere entre portas — está **fora** da conta. A leitura é comparativa, não fully-loaded.
- **Regra "categoria única" descarta os multiproduto** numa caixa só — pode esconder padrões (revisar no futuro).

## 7. Sequência de build
1. **(Esta sessão)** spec + **rascunho do mapa** SKU→linha → **João valida** (resolve os ⚠ do §8 abaixo).
2. **(Próxima sessão)** construir `views/portas_entrada.py` + o motor de porta de entrada (provável
   `portas.py` reusando `coortes.py`) + check de coerência. Reiniciar o painel (watchdog não instalado).

## 8. Validação do mapa — RESOLVIDA (2026-07-15)
- **Camiseta Minimal** fica **uma linha só** (74,6% / 202 SKUs) — o João carvou dela as variantes 2.0 / gola
  alta / modal, mas manteve o núcleo junto.
- **Versões que o nome não distinguia** → o João separou **na mão** no CSV: Jeans 1.0×2.0, Social Tech
  Classics×Malha, Polo 1.0/2.0/Tricot, Jaqueta Essential×Westfield, Suéter Zíper×Classic 2026.
- **Brindes** → **BRINDE + Perfume + Skincare** todos removidos (papel `brinde`), como a carteira.
- **SEM NOME** (134 SKUs) → **"Produto desconhecido"** por ora (backlog: cadastrar nome a montante).

**Pendências residuais no backlog:** cadastrar nome dos 134 SKUs `SEM NOME`; revisitar se "Camiseta Minimal"
(74,6%) merece subdivisão; revisar o balde "Outros Produtos" (276 SKUs, 1,9%).
