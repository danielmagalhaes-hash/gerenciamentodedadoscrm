# MC Growth — Painel de Margem de Contribuição · **V4 (Coortes de recompra)**

> Documento de produto. Fonte de verdade do **domínio** e do **comportamento esperado**. Lido por todos os outros documentos. Atualizado quando o produto muda.
>
> **V1 gerado na Fase 0 (Discovery), 2026-06-30/07-01.** **V2 (Aquisição) por handoff em 2026-07-09.** **V4 (Coortes) gerado por discovery profunda em 2026-07-10** (`docs/sessions/2026-07-10-discovery-v4-coortes.md`). Base: `docs/ROADMAP.md` (V4) + o V2 arquivado em `docs/product-history/PRODUCT-v2.md`.
>
> **Por que pula de V2 → V4:** a **V3 do roadmap (custo cheio real por pedido)** foi **esvaziada** pelo João em 2026-07-10 — os custos seguem em % (da DRE) e os 3 custos novos (CX, juros de estoque, criativo) ficam pra depois. Sem custo real por pedido, a V3 não destravava decisão nova. O número da versão segue o roadmap.
>
> **Como ler as marcas:** **[HERDADO]** = já existe (V1/V2), não muda. **[NOVO]** = entra na V4. A V4 gira toda em torno de uma virada: **o painel deixa de olhar um período fechado e passa a seguir a mesma _turma de clientes_ ao longo dos meses — para saber se a aquisição de cada safra se pagou, e em quanto tempo.**

---

## 1. Visão e proposta de valor

**Em uma frase:**
- **[HERDADO]** um painel diário que mostra a **Margem de Contribuição (MC)** da Minimal Club no Shopify (V1), e uma **aba de aquisição** que diz se o cliente novo se paga na 1ª compra (V2).
- **[NOVO]** e, numa **aba dedicada de coortes**, mostra **quanto de Margem de Contribuição cada _safra_ de clientes novos devolve, acumulada por cliente, ao longo dos meses** — para decidir **acelerar ou segurar a aquisição**.

**Para quem, qual problema, como resolve:**
A V2 respondeu "o cliente novo se paga **na 1ª compra**?" — uma régua conservadora, só o primeiro toque. Mas a decisão de **quanto gastar de mídia** depende do que vem **depois** da porta de entrada: se a turma que entrou em março volta e compra de novo, ela pode se pagar no mês 3 mesmo tendo entrado no vermelho. A V4 acrescenta essa dimensão do **tempo**: agrupa os clientes pela **safra** (o mês da 1ª compra), acompanha a **MC acumulada por cliente** de cada safra mês a mês, e desenha a **curva de payback** — o momento em que a turma cruza o zero e passa a dar contribuição líquida. Com isso o João lê a tendência ("as safras novas estão se pagando **mais rápido** que as antigas → a aquisição está ficando mais eficiente → acelera") e decide o botão da mídia com base no **retorno no tempo**, não só no primeiro pedido.

**O que este produto NÃO é:**
- **[HERDADO]** Não é fechamento contábil; não é BI/ERP; não é tempo real; **cobre só Shopify** (não B2B fora do Shopify, TikTok Shop, assinatura, Mercado Livre).
- **[HERDADO] Não mede "lucro".** Mede **Margem de Contribuição** (depois dos custos variáveis, inclusive mídia; antes do fixo). **"Lucro" é sinônimo proibido de MC neste projeto.**
- **[NOVO] Não dá o veredito automático.** A V4 **mostra a curva**; ela não diz sozinha "acelere" ou "freie" — a régua calibrada (alvos de payback/CAC, modulador de estoque) é a **V5**, parkeada. Aqui o julgamento é do João, lendo a tendência.
- **[NOVO] Não prevê o futuro de uma safra.** Só mostra os meses **já fechados** de cada turma. Uma safra nova tem poucos pontos; a V4 **não extrapola** a curva pra frente.
- **[NOVO] Não é "todos os canais".** A coorte usa a 1ª compra **cross-canal** (HubSpot), mas a MC e a mídia contadas são **só do Shopify**. A versão que soma TikTok/assinatura na conta é um momento futuro (ver §8, o viés aceito).

---

## 2. Usuários e papéis

### João (gestão de growth) — único usuário — **[HERDADO]**
- **Contexto:** opera o crescimento da Minimal; entende lógica avançada, vocabulário de dev em construção. Só computador (desktop).
- **Objetivos no sistema:** abrir o painel e ver a MC do período (V1); ver se o cliente novo se paga na 1ª compra (V2); **[NOVO]** abrir a aba de coortes pra ver se cada safra se paga no tempo e decidir acelerar/segurar a mídia.
- **Frequência de uso:** diária (a leitura de coorte é mais semanal/mensal, mas mora no mesmo painel).

### CEO e lideranças — **fora do escopo** — **[HERDADO]**
- Consultariam ≥1x/semana, só leitura. Login multiusuário segue fora. A aba de coortes é, junto com a de aquisição, a tela que a diretoria vai querer um dia — registrado, não construído.

---

## 3. Glossário do domínio

> **[HERDADO]** vêm da V1/V2 e valem idênticos. **[NOVO]** é o vocabulário da V4.

### Margem de Contribuição (MC) — **[HERDADO]**
O que sobra das Vendas depois dos custos e deduções **variáveis**, incluindo a mídia paga. **NÃO confundir com** lucro líquido (depois do fixo), margem bruta isolada, nem fechamento do Financeiro.

### Vendas / CMV / SKU / Kit / Mídia paga (Ad Spend) / ROAS — **[HERDADO]**
Idênticos ao V1/V2 (detalhe no `PRODUCT-v2.md` e no `ARCHITECTURE.md`). **Ad Spend** = `fb_investimento/(1−0,1215) + google_investimento + google_institucional_investimento`.

### `customer_type` (carimbo nativo do Shopify) — **[HERDADO, mas rebaixado na V4]**
A etiqueta `Primeira Compra`/`Recompra` que a Shopify põe no pedido (base da V2). **Na V4 ela deixa de ser a fonte de verdade de novo×recompra** — quem manda passa a ser o HubSpot (abaixo). As duas definições **divergem** (uma é "novo no Shopify", a outra "novo na Minimal"); alinhar a V2 ao HubSpot é um item comprometido à parte (§7.2).

---

### Coorte / Safra — **[NOVO]**
- **Definição:** o conjunto de clientes cuja **1ª compra** (na vida, em qualquer canal) caiu num **determinado mês**. A "turma de março/2026" = todos que estrearam em março. Uso "safra" e "coorte" como **sinônimos**.
- **Exemplo:** alguém cuja `data_primeira_compra = 2026-05-03` pertence à **safra de maio/2026**, para sempre.
- **Relações:** cada cliente pertence a **exatamente uma** safra (só há uma 1ª compra por cliente). É a linha da tabela e a linha da curva.
- **NÃO confundir com:** "período" (o painel V1 soma um mês de pedidos; a coorte segue uma turma por vários meses). Nem com "clientes ativos no mês".

### Cliente — **[NOVO]** (a entidade que a V2 não tinha)
- **Definição:** uma pessoa que dura no tempo, identificada pelo **`e_mail`** no HubSpot. É o que "cola" a compra de janeiro à recompra de março da mesma pessoa.
- **NÃO confundir com:** "pedido" (a V1/V2 contam pedidos; a V4 conta clientes). Nem com o `customer_type` do Shopify (que é por pedido, não uma identidade que anda no tempo).

### `Shipped` + `Negócio Fechado - Comercial` (o recorte da base HubSpot) — **[NOVO]**
- **Definição:** os **dois** valores de `etapa_do_negocio` que compõem o universo da coorte (decisão 2026-07-10, medido na base real).
  - **`Shipped`** (≈98,8%) = pedidos Shopify que **casam com a aba `Vendas`** pelo número do pedido (mesmo universo da V1/V2; inclui o "Comercial Varejo" que vendedores lançam no Shopify) → **CMV real** onde há itens.
  - **`Negócio Fechado - Comercial`** (≈1,2%) = vendas do time comercial. **[CORREÇÃO 2026-07-14]** ~~gravam o **nome do cliente** no campo `nome`~~ — **não**: gravam um **número de outra numeração**, que **COLIDE** com números de pedido Shopify **antigos** (medido: casaria com itens de pedidos ~92 dias mais velhos). Por isso o Comercial **nunca** pode casar itens pelo número (`cascata.pode_casar_itens`) e entra **sempre com o CMV estimado (30%)**, marcado como tal. Quase todas Recompra de clientes de 2021. ADR `2026-07-14-cmv-real-historico-3-camadas`.
  - Ambos **excluem** TikTok e assinatura. O universo da coorte é, assim, levemente **maior** que o da V1/V2 (que é só a `Vendas`) — a coorte é uma visão de **valor do cliente** que inclui a compra comercial.
- **NÃO confundir com:** `dealstage='shipped'` (minúsculo, o estágio cru) nem com `tipo_de_venda` (a flag Primeira Compra/Recompra, outra coluna).

### Cascata (DRE) — formato único — **[ATUALIZADO 2026-07-14]**
Toda tela que mostra a cascata usa a **mesma forma**: `Vendas → (−) **Deduções** [PIS/COFINS+CBS, ICMS+IBS, Devoluções, Chargebacks, Outras] → (−) **Cost of Delivery** [CMV, Frete, Embalagem, Taxa de Gateways, Valor plataforma, Despesas de antecipação] → (=) Lucro Bruto → (−) Mídia Paga → (=) Margem de Contribuição`. Os dois subtotais de grupo (cinza) são **soma das linhas abaixo** — apresentação, não mudam número.

### MC acumulada por cliente — **[NOVO]** (a métrica-herói da V4)
- **Definição:** para uma safra, a soma da MC que ela gerou até um certo mês de idade, **dividida pelo tamanho da turma** (número de clientes). A mídia inteira do mês de aquisição pesa no **mês 0**.
- **Exemplo (ilustrativo):** turma de março, mês 0 = −R$120/cliente (o 1º pedido não cobriu o CAC); mês 3 = +R$15/cliente (a recompra pagou e passou).
- **Relações:** é o eixo Y da curva e o corpo da tabela. Cruzar o **zero** = a turma se pagou.
- **NÃO confundir com:** MC **total** da safra (não normalizada — turmas de tamanhos diferentes não se comparam). Nem com "lucro por cliente".

### Curva de payback — **[NOVO]**
- **Definição:** o gráfico da MC acumulada por cliente (eixo Y) contra os **meses desde a 1ª compra** (eixo X), uma linha por safra. Nasce no negativo (mês 0 = margem do 1º pedido − CAC) e **sobe** conforme a recompra entra.
- **Relações:** o ponto onde cruza o zero é o **payback** (meses até se pagar).

### Mês da safra (m+0, m+1, …) — **[NOVO]**
- **Definição:** a **idade** da turma, em meses desde a 1ª compra. `m+0` = o mês da 1ª compra; `m+1` = o mês seguinte; etc.
- **[CORREÇÃO 2026-07-10]** ~~Vem pronto da coluna `meses_desde_primeira_compra`.~~ **NÃO** — descobriu-se na construção que esse campo do HubSpot é a **idade do CLIENTE no export** (constante em todos os deals do cliente), **não** a idade do deal. A idade da coorte é **calculada** da diferença em **meses-calendário** entre `data_de_fechamento` e a 1ª compra real do cliente. Ver `ARCHITECTURE.md` §6.

### CAC por safra — **[NOVO]** (reenquadra o CAC da V2)
- **Definição:** a mídia do mês de aquisição da safra, dividida pelo tamanho da turma. É o "mergulho inicial" — quão fundo no vermelho a turma começa.
- **Fórmula:** `CAC_safra = Ad Spend do mês-calendário da safra ÷ nº de clientes da safra`.
- **Relações:** é a **2ª coluna** da tabela e o tamanho do buraco no mês 0.
- **NÃO confundir com:** o CAC da V2 (que dividia a mídia de um período pelos novos **daquele período**; aqui é por **safra**).

### Recompra em 90 dias — **[NOVO]**
- **Definição:** o percentual da safra que fez **pelo menos mais uma compra Shopify em até 90 dias** da 1ª compra. Janela **fixa** (não "até hoje") pra as safras serem **comparáveis** entre si.
- **NÃO confundir com:** "taxa de recompra acumulada" (que infla nas safras velhas, que tiveram mais tempo). Na tela, o rótulo é **sempre explícito** ("recompra em 90 dias"), nunca um "%" solto.

### `data_primeira_compra` (cross-canal) — **[NOVO]**
- **Definição:** o campo do HubSpot com a data da 1ª compra do cliente **em qualquer canal** (Shopify + TikTok + assinatura). É o que define a safra.
- **NÃO confundir com:** "1ª compra no Shopify". Como é cross-canal, um cliente que estreou no TikTok em 2023 e só comprou Shopify em 2026 cai na **safra de 2023** — origem do **viés aceito** (§8).

### CMV estimado (30%) — **[NOVO; substitui a "margem estimada de 25%" em 2026-07-14]**
- **Definição:** para os pedidos **sem itens** (histórico fora da janela atual + vendas do time Comercial), não há custo real: o **CMV é estimado em 30% da receita** e **todas as outras linhas seguem as fórmulas de sempre** (deduções e custos variáveis em %, sobre a receita inteira). A linha do CMV vem **marcada com ⚠️** na tela.
- **De onde vem o 30%:** medido nos meses com itens reais — CMV/Vendas = **29,0%** (mai/2026) e **28,8%** (jun/2026); arredondado **para cima** (conservador).
- **Margem de produto implícita:** `1 − 27,49% − 30% = **42,5%** da receita` (o real medido é ~43%).
- **NÃO confundir com** a regra antiga ("margem de produto = 25% da receita, direto"), um chute pessimista que **subestimava a MC histórica em ~17,5 pontos de receita**. ADR `2026-07-14-cmv-estimado-30-por-cento`.

### Safra fechada — **[NOVO]**
- **Definição:** uma célula (safra, mês de idade) só aparece quando o **mês-calendário correspondente já terminou**. A turma de junho só ganha o `m+0` quando junho fecha (começo de julho); o `m+1` só no começo de agosto. Mesma disciplina de "período fechado" do resto do painel — nada de mês correndo.

---

## 4. Entidades do negócio

### Cliente — **[NOVO]**
- **Atributos:** `e_mail` (chave), `data_primeira_compra`, safra (derivada), lista de deals `Shipped`.
- **Ciclo de vida:** "nasce" na 1ª compra (define a safra, imutável); "vive" a cada recompra Shopify. Não some.
- **Quem cria/edita:** o HubSpot (via `e_mail`). **Quem consulta:** o painel (só lê).

### Deal `Shipped` (≈ Pedido Shopify na base HubSpot) — **[NOVO fonte]**
- **Atributos usados:** `id`, `e_mail` (cliente), `nome` (= número do pedido, casa com `Vendas.order_name`), `valor` (**a receita** — decidido 2026-07-14: `valor` ≥ `net_revenue`, a diferença é frete, aceita; §8), `data_de_fechamento` (data), `tipo_de_venda` (Primeira Compra/Recompra), `data_primeira_compra`, `meses_desde_primeira_compra` (⚠️ idade do **cliente** no export, **não** do deal — não serve de idade da coorte; ver §3), `etapa_do_negocio` (=`Shipped`).
- **Relação com o painel:** a ponte `nome` → `Vendas.order_name` → `Vendas.order_id` → `Itens.order_id` → `Custos.sku` leva ao **CMV real** de cada pedido.

### Coorte — **[NOVO]** (entidade derivada)
- Uma safra = uma coleção de Clientes agrupados por mês de `data_primeira_compra`. Atributos: tamanho (nº de clientes), CAC, e a série da MC acumulada por cliente por mês de idade.

### Pedido / Item / Tabela de custo / Gasto de mídia — **[HERDADO]**
- Inalterados. O CMV vem da base de Itens × Custos como na V1. A mídia vem da aba `Midia`.

---

## 5. Fluxos principais

### Fluxo A — Atualização diária dos dados — **[HERDADO]**
Automático. **[NOVO]** a base do HubSpot (`silver_deals_minimal`) entra como nova fonte; a `data_primeira_compra` (âncora da safra) vem pronta do pipeline — mas a **idade** (m+0, m+1, …) é **calculada** no painel, **não** vem do campo `meses_desde_primeira_compra` (que é a idade do cliente no export; ver §3).

### Fluxo B / C — Abrir a aba de MC / Editar custos — **[HERDADO]** (não mudam).

### Fluxo D — Abrir a aba de aquisição (V2) — **[HERDADO]**
Não muda na V4. (Um dia será re-baseado no HubSpot pra bater com a V4 — §7.2.)

### Fluxo E — Abrir a aba de coortes — **[NOVO]**
- **Quem dispara:** João.
- **Pré-condições:** base HubSpot `Shipped` disponível (chave `e_mail`, `data_primeira_compra`); base de itens acessível para o CMV real (2022→hoje); mídia por mês; **dados de arquitetura resolvidos** (ler o histórico do BQ — §8).
- **Passos:**
  1. João abre a aba de coortes.
  2. O painel monta, para cada **safra** (mês de 1ª compra), a série de **MC acumulada por cliente** por mês de idade (m+0, m+1, …), com a mídia da safra no m+0 e a recompra somando adiante.
  3. Mostra as **duas figuras**: a **tabela/triângulo** (todas as safras: `Safra | CAC | m+0 | m+1 | …`) e a **curva** (últimas 12 safras por padrão, ampliável).
  4. João escolhe uma safra no **seletor** → os **KPIs de cabeçalho** (payback, CAC, LTV até hoje, recompra em 90 dias) passam a ser daquela safra, e ela é **destacada** na curva.
- **Pós-condições:** João lê se cada safra se pagou e em quanto tempo, e se a tendência entre safras melhora ou piora.
- **Divergências:**
  - **Safra ainda imatura** → mostra só os meses fechados; **payback = "—"** enquanto a curva não cruzou o zero (não inventa).
  - **Pedido sem CMV real** (SKU sem custo, ou sem itens) → o **CMV entra estimado em 30%** / herda o alerta de SKU sem custo, **marcado como provisório** (⚠️ na linha do CMV).
  - **Cliente que estreou fora do Shopify** → o mês 0 dele no Shopify pode vir vazio e o CAC fica levemente otimista (o **viés aceito** — §8).

---

## 6. KPIs e regras de cálculo

> **[HERDADO]** a cascata DRE (V1) e os 5 KPIs da aquisição (V2) seguem idênticos. Abaixo, **[NOVO]**, os KPIs da aba de coortes. Notação: safra **S** = mês da 1ª compra; **N_S** = nº de clientes da safra; idade **m** = meses desde a 1ª compra.

### MC acumulada por cliente — **[NOVO]** (herói)
**Mede:** quanto de MC a safra S devolveu por cliente, somada até a idade m.
**Fórmula (soletrada):**
- MC de produto de um deal — **uma fórmula só**; o que muda é de onde vem o CMV *(atualizado 2026-07-14)*:
  - `MC de produto = valor − (deduções % sobre valor) − CMV_do_pedido`;
  - **CMV real** quando o pedido casa com a base de itens (ponte até Itens×Custos);
  - **CMV estimado = 0,30 × valor** quando não há itens (histórico + Comercial) → margem de produto de **42,5% do valor**. A linha do CMV leva ⚠️ na tela.
- `MC_incremental(S, m) = [ Σ MC de produto dos deals Shipped da safra S com idade m ] ÷ N_S`, e no **m=0** subtrai também `Ad Spend(mês-calendário S) ÷ N_S`.
- `MC acumulada por cliente(S, m) = Σ_{k=0..m} MC_incremental(S, k)`.
**Unidade:** R$/cliente. **Frequência:** por safra fechada.
**Normal:** cruzou o zero (verde) — a turma se pagou. **Alerta:** ainda abaixo do zero (vermelho).

### CAC por safra — **[NOVO]**
**Fórmula:** `CAC_S = Ad Spend(mês-calendário S) ÷ N_S`. **Unidade:** R$/cliente. É a 2ª coluna da tabela e o mergulho do m+0.
**Borda:** N_S = 0 → não há safra (não aparece).

### Meses até se pagar (payback) — **[NOVO]**
**Fórmula:** o menor **m** em que `MC acumulada por cliente(S, m) ≥ 0`. **Unidade:** meses.
**Borda:** se a safra ainda não cruzou o zero (ou é imatura) → **"—"** (nunca extrapola).

### MC acumulada por cliente até hoje (LTV até agora) — **[NOVO]**
**Fórmula:** `MC acumulada por cliente(S, m*)`, onde **m*** = a maior idade **fechada** da safra. **Unidade:** R$/cliente.

### Recompra em 90 dias — **[NOVO]**
**Fórmula:** `nº de clientes da safra S com ≥1 compra Shopify adicional em até 90 dias da 1ª compra ÷ N_S`. **Unidade:** %. **Rótulo sempre explícito na tela.**

---

## 7. Escopo

### 7.1 Entra na V4
- **[HERDADO]** Tudo da V1 e da V2 (abas de MC e de aquisição, filtro de período, editor de custos, alertas, só Shopify, só dias fechados, único usuário).
- **[NOVO]** Uma **aba de coortes** com: a **tabela/triângulo** (`Safra | CAC | m+0…`), a **curva de payback** (últimas 12 safras, ampliável), o **seletor de safra**, os **KPIs de cabeçalho** (payback, CAC, LTV até hoje, recompra em 90 dias), a **linha do zero** e a regra de **safra fechada**.
- **[NOVO]** A **fonte HubSpot** (`silver_deals_minimal`, filtro `Shipped`) como base oficial de cliente/1ª-compra, e a **MC real** onde há itens (**CMV estimado em 30%** onde não há).

### 7.2 Fica para depois (com justificativa)
- **Re-base da V2 no HubSpot** — *comprometido, mas item à parte; prompt guardado em `docs/prompts-guardados/re-base-v2-hubspot.md`.* Enquanto não for feito, V2 e V4 divergem de propósito (rotular na tela).
- **MC e mídia de todos os canais** (TikTok, assinatura na conta) — *versão futura; tira o viés cross-canal.*
- **Régua "acelerar/segurar/frear"** com alvos calibrados de payback/CAC + modulador de estoque — *V5; a V4 mostra a curva, não dá o veredito.*
- **Separar mídia de aquisição × remarketing** — *momento futuro (era o refino da mídia).*
- **[HERDADO]** Login multiusuário; comparação/forecast; mobile; parâmetros na tela.

### 7.3 Nunca vai entrar — **[HERDADO]**
- Fechamento contábil oficial; BI/ERP completo; tempo real ao segundo.

---

## 8. Restrições e premissas

### Dados e fonte — **[NOVO]**
- **Fonte de cliente = HubSpot no BigQuery** `moon-ventures-data-lake.prod_silver.silver_deals_minimal`, filtro `etapa_do_negocio IN ('Shipped','Negócio Fechado - Comercial')` (ver glossário §3; o Comercial é sempre estimado). Se o campo/coluna sumir, a coorte não se monta (pré-condição do Fluxo E).
- **CMV real cobre a história inteira (ATUALIZADO 2026-07-14) — em 3 camadas.** ~~O MVP usava CMV real só na janela atual (abr–jul/2026) e estimava o resto em 30%.~~ A promessa "faseada" foi **cumprida**: a fonte agora é a base local **`bases/itens_historico.csv`** (export do BQ da mesma tabela silver de itens, mas a história toda: ~1,3 M linhas, **out/2021 → hoje**). Os itens de cada pedido são resolvidos por `cascata.itens_por_nome`: **1ª** base histórica → **2ª** aba `Itens` da planilha (pedidos recentes demais pro export, que é uma foto) → **3ª** nada = **CMV estimado em 30% da receita** (`CMV_ESTIMADO_FRACAO`; ADR `2026-07-14-cmv-estimado-30-por-cento`). O 30% sobra **só onde não há itens**: antes de out/2021, o time **Comercial** (grava um número de outra numeração que colide → nunca casa) e SKUs sem custo cadastrado. As **três telas** (painel, aquisição, coorte) usam a mesma receita de custo. ADR `2026-07-14-cmv-real-historico-3-camadas`.
  - **Resíduos medidos:** ~6,4% das unidades de 2023 sem custo cadastrado (CMV parcial → MC otimista ali); 2021 ainda estimado (a base começa em out/2021).
- **Arquitetura resolvida (2026-07-14):** ~~anos de itens não cabem numa planilha estreita — decisão da spec.~~ Resolvido **exportando o histórico do BQ para um arquivo local** (`itens_historico.csv`), o mesmo padrão "torneira" do HubSpot (João puxa 1×; o painel só lê, sem credencial). Arquivo ausente = **degrada** para o comportamento anterior (30% no passado).
- **Receita = `valor` do HubSpot (RESOLVIDO 2026-07-14):** a query confirmou que `valor` é **sempre ≥ `net_revenue`**; a diferença é **frete**, que o João aceita como receita. A unificação cravou **Vendas = Σ `valor` por `data_de_fechamento`** nas três telas. ADR `2026-07-14-rebase-geral-aquisicao-hubspot`.

### Premissas de modelagem — **[NOVO]**
- **Viés cross-canal aceito e documentado:** a coorte usa a 1ª compra **cross-canal** (`data_primeira_compra`), mas a **MC e a mídia contadas são só do Shopify**. Para o cliente que estreou fora do Shopify, o **mês 0 fica incompleto** e o **CAC levemente otimista**. Aceito porque Shopify é **>95% das vendas**; a versão "todos os canais" corrige isso (§7.2). *O tamanho exato do viés será medido por query.*
- **Mix mudou muito:** o negócio multiplicou de tamanho de 2022 a 2025 (≈6 mil → ≈120 mil itens/mês). Safras velhas são quase "outra empresa" — lê-las com essa ressalva (coorte não se compara ingenuamente entre eras muito distantes).
- **Custo por SKU é o atual aplicado ao passado:** o CMV histórico usa o custo **de hoje** por SKU (é como o painel já funciona). Para SKUs antigos sem custo, herda o alerta de SKU sem custo.
- **100% mídia → novos, no mês 0 da safra:** a mídia inteira do mês-calendário pesa no mês 0 da safra daquele mês (herda a convenção da V2).

### Legais / regulatórias — **[NOVO]**
- A V4 passa a usar **e-mail** como chave de cliente (dado pessoal) — só internamente, para colar a mesma pessoa no tempo; o painel não exibe e-mail nem o usa fora do cálculo. (A V1/V2 ignoravam identidade; a V4 a usa.)

### Orçamento / prazo — **[HERDADO]**
- Evolução incremental sobre o painel local do Mac do João.
