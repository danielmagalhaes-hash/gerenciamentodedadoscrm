# ROADMAP — Do painel de MC ao Motor de Crescimento Lucrativo

> Mapa de evolução do MC Growth, da V1 atual até o modelo descrito em
> `motor-crescimento-lucrativo-true-classic.md`. **Escopo comprometido: V1 → V4.**
> V5-V7 são hipóteses a validar *depois* de rodar o modelo por um tempo.
>
> **Criado em 2026-07-04.** Método: definir o destino (estrela-guia) e voltar até a V1,
> em passos onde cada versão destrava uma decisão que a anterior não permitia.
> Decisão de direção registrada em `docs/decisions/2026-07-04-roadmap-motor-crescimento.md`.

---

## 0. A estrela-guia (o destino, para orientar — não para construir tudo agora)

O destino final é um **cockpit de decisão de aquisição da Minimal**: para um período fechado
*e* para o último real gasto, ele responde *"estou ganhando dinheiro num cliente novo,
contando TODOS os custos, e devo acelerar ou frear a aquisição?"*.

Três releituras guiam o caminho inteiro (valem para toda versão):

1. **É um instrumento de decisão, não um relatório.** A V1 é um retrovisor ("qual foi
   minha MC?"). O destino olha para a frente ("quanto devo gastar amanhã?"). Cada versão
   vale pela **decisão que destrava**, não pela tela que mostra.
2. **Miramos o instrumento, não os números da True Classic.** A agressividade deles
   (empatar na aquisição, "gastar all day long") é habilitada por 4 pré-requisitos que a
   Minimal pode não ter (público gigante, margem ~80%, dívida barata, recompra medida).
   Copiar o alvo sem os pré-requisitos é "queimar caixa com método". **Medimos os números
   da Minimal e calibramos a régua dela** — que pode ser "lucro positivo já no 1º pedido",
   não break-even.
3. **A dobradiça é o cliente.** A frase-mãe do modelo — *"aquisição é crescimento,
   recompra é lucro"* — não existe sem separar **cliente novo × recorrente**. Hoje o painel
   soma pedidos; ele não conhece cliente. Dar identidade ao cliente é a charneira em que o
   projeto gira (V2).

### As 7 peças do destino (para referência)

| Peça                                    | O que é                                                                        | Onde entra        |
| --------------------------------------- | ------------------------------------------------------------------------------ | ----------------- |
| P&L por pedido, custo cheio             | cada pedido carrega seu custo variável real (não % médio)                      | V3                |
| Identidade de cliente + novo×recorrente | chave de cliente (e-mail) que dura no tempo; pedido marcado 1ª compra/recompra | V2                |
| Lucro por cliente novo, custo cheio     | a métrica-governante (o "medidor de eficiência")                               | V4                |
| Curvas de recompra por coorte           | lucro acumulado por cliente, por safra (LTV redefinido)                        | V4                |
| A régua das duas restrições             | eficiência (alvo calibrado) + estoque (modulador) → "acelerar/segurar/frear"   | **V5 (parkeado)** |
| Incrementalidade + survey               | ROAS real por canal (holdout, geo, survey), não o atribuído                    | **V6 (parkeado)** |
| Base como ativo + ritual                | valor residual por e-mail/SMS; "name the number", cadência diária              | **V7 (parkeado)** |

---

## 1. Onde estamos (V1)

**MC de período fechado, "blended", só Shopify, olhando pra trás.** Cascata de Vendas até
Margem de Contribuição, com deduções e custos em % sobre as Vendas, mais CMV item a item e
mídia paga. Auditoria de custo por pedido já existe.

**Limites conhecidos que o roadmap precisa vencer:**
- Não conhece **cliente** (soma pedidos). → V2
- Custo cheio **parcial**: faltam os 4 que "vazam" (devolução+processo, atendimento por
  pedido, juros da dívida de estoque, criativo como custo variável); frete/devolução são %
  estimados, não valor real. → V3
- ~~**Dobra de kit** infla o CMV (~5-6% da MC)~~ — **RESOLVIDA na fonte (2026-07-09)**; paliativo do painel aposentado.
- Não separa mídia de **aquisição** vs. remarketing. → V4

---

## 2. O caminho comprometido (V2 → V4)

> Regra de ouro do roadmap: **não montar a régua antes da instrumentação** (armadilha nº 6
> do documento). V2-V4 são a instrumentação; a régua (V5) só vem depois de rodar isso.

### V2 — Aquisição: cliente novo se paga na 1ª compra?  *(a dobradiça)*

> **Refinado no discovery de 2026-07-09** (ver `PRODUCT.md` V2 e o ADR
> `2026-07-09-v2-aquisicao-customer-type-shopify`). O desenho original ("cascata em duas
> colunas, MC-novos × MC-recompra") foi **estreitado para uma aba só de aquisição**: o João
> afinou a decisão para *"minha aquisição está lucrativa?"*. A coluna de recompra virou
> candidata a uma versão seguinte. Duas mudanças-chave de método abaixo.

**O que adiciona.** Cada pedido ganha um carimbo **1ª compra × recompra** — mas **não** por
uma chave de e-mail construída por nós, e sim pelo **campo nativo da Shopify**
(`customer_type` = `Primeira Compra` / `Recompra`), que já vem na aba `Vendas`. Uma **aba
dedicada de aquisição** mostra, só sobre os pedidos de 1ª compra: **MC-novos, Vendas-novos,
Pedidos-novos, CAC, aROAS**.

**Decisão que destrava.** *"A aquisição de clientes novos está gerando Margem de Contribuição
positiva já na primeira compra — devo acelerar ou segurar a mídia?"* Régua **conservadora**
(só o 1º toque); o *"quanto vem de recompra?"* e o LTV ficam para depois (V4).

**Duas convenções registradas (ajustáveis).**
- **Cliente novo = novo no canal Shopify** (a Shopify classifica olhando só o histórico dela).
- **100% da mídia é atribuída aos clientes novos** neste 1º momento — a V4 é quem separa
  mídia de aquisição × remarketing. Por isso CAC e aROAS são "blended" por convenção.

**Pré-requisito de dado — RESOLVIDO.** O carimbo é o campo nativo da Shopify, **point-in-time**
(cada cliente tem exatamente uma "Primeira Compra") e com **histórico completo** — logo **sem
viés de borda esquerda** (não confunde recompra antiga com aquisição). Vem **automático** no
fluxo da planilha. Cobertura medida: 99,78% (84 de 37.593 pedidos sem carimbo = 0,22%). O
e-mail/`customer_id` (para seguir a pessoa no tempo) **não** é necessário na V2 — é da V4.

**Critério de aceite (atualizado).**
- Todo pedido da aba `Vendas` classificado como Primeira Compra / Recompra / sem-classificação
  pelo campo `customer_type`.
- Aba de aquisição mostra os 5 KPIs; a soma das faixas (novos + recompra + sem-classificação)
  **amarra** com os totais atuais (Vendas, CMV, Lucro Bruto, MC).
- MC-novos com **linha do zero** (verde ≥ 0 / vermelho < 0). Sem alvo importado — régua
  calibrada é V5.
- Bordas tratadas: divisão indefinida (0 pedidos novos / 0 mídia) mostra "—" + nota, nunca
  número falso.

**Gancho na V1.** Reusa o filtro de período e a cascata existentes; adiciona uma dimensão
(novo/recompra) sobre o mesmo recorte de pedidos, numa aba nova — a aba de MC da V1 não muda.

---

### V3 — P&L por pedido, custo cheio

> **ESVAZIADA / ADIADA (decisão do João, 2026-07-10).** Na virada para a V4, o João decidiu
> **manter todos os custos em % (da DRE)** e **adiar** os 3 custos novos (CX por pedido, juros
> de estoque, criativo variável). Sem custo real por pedido e sem os custos novos, a V3 do
> roadmap **não destrava decisão nova** (o CMV real por pedido a auditoria já mostra) — então o
> build **pula de V2 → V4**. O único resíduo real (aterrar os % no valor da DRE + destravar a
> aba `Parametros`) fica como melhoria pequena, não como versão. Ver
> `docs/sessions/2026-07-10-discovery-v4-coortes.md`.

**O que adiciona.** Move a cascata de **"% médio sobre Vendas"** para **custo real por
pedido**, e acrescenta os quatro custos que a V1 esquece:
1. **Devoluções e trocas + o custo de processá-las** (frete reverso, reinspeção, reposição).
2. **Atendimento (CX) por pedido** (quantos tickets por pedido × custo do ticket).
3. **Juros da dívida que financia o estoque.**
4. **Criativo tratado como custo variável** (escala com o gasto — não é OPEX).

~~Inclui **consertar a dobra de kit**~~ — **já feito**: a dobra foi corrigida na fonte em 2026-07-09, antes da V3.

**Decisão que destrava.** *"Este pedido, sozinho, dá lucro de verdade?"* — a margem por
pedido deixa de ser fachada.

**Pré-requisito de dado (o ponto mais arriscado do roadmap).** Precisamos de números reais,
não estimativas, para: taxa e custo de devolução/troca, custo de CX por pedido, juro da
linha de estoque, custo de criativo. Boa parte disso **não está na planilha hoje** — vai
exigir pedir ao time de Dados / Financeiro, do mesmo jeito que fizemos com a base de itens.
**Enquanto um insumo real não vem, ele fica como % assumido e claramente marcado como
"provisório" na tela** — para não fingir precisão que não temos.

**Critério de aceite.**
- Cada pedido carrega seu custo cheio; a soma bate com a cascata do período.
- Dobra de kit — **já corrigida na fonte (2026-07-09)**, fora do escopo da V3.
- Cada linha de custo marcada como **"real"** ou **"% provisório"** — nada de fachada
  silenciosa.

**Gancho na V1.** É a evolução direta da `cascata.py`; o editor de custos e a auditoria por
pedido já existentes são a base natural.

---

### V4 — Lucro por cliente novo + primeiras coortes  *(fim do escopo comprometido)*

> **Refinada no discovery de 2026-07-10** (ver `PRODUCT.md` V4 e o ADR
> `2026-07-10-v4-coortes-recompra-hubspot`). Desenho concreto: a coorte vem de uma **fonte
> nova** — o **HubSpot no BigQuery** (`moon-ventures-data-lake.prod_silver.silver_deals_minimal`),
> filtrado por `etapa_do_negocio='Shipped'` (= Shopify) — que passa a ser a **base oficial** de
> cliente/1ª-compra (chave = `e_mail`; definição **cross-canal** via `data_primeira_compra`). A
> métrica é **MC acumulada por cliente** por safra (mídia inteira no mês 0; cruzar o zero = a
> turma se pagou); MC **real** de 2022-01 em diante, **25% de margem estimada** antes. Custos
> seguem em % (a V3 foi esvaziada). Como Shopify é >95% das vendas, aceitou-se o **viés** de a
> mídia/MC serem só do Shopify sob uma coorte cross-canal — registrado como premissa; a versão
> "todos os canais" fica para depois.

**O que adiciona.** A **aba de coortes** (a V2 dá o cliente; a V3 foi esvaziada — custos seguem
em %):
- **MC acumulada por cliente, por safra** (mês da 1ª compra), mês a mês — a **curva de payback**
  (o LTV redefinido: do fundo do poço no m+0 subindo com a recompra). Mídia inteira do mês no m+0
  (100% mídia → novos, *blended* declarado).
- **Triângulo** (`Safra | Clientes | CAC | m+0…`), curva das últimas 12 safras, seletor de safra
  e KPIs (payback, CAC, MC/cliente até hoje, **recompra em 90 dias**).
- **Mede a recompra real por safra** — o "gate" que o devil-advocate levantou entra como
  *entrega*, não como pré-requisito.

**Decisão que destrava.** *"Cada safra se pagou, e em quanto tempo? Devo acelerar ou segurar a
aquisição?"* — lendo a **tendência entre safras**. A V4 **mostra a curva**; o veredito absoluto
(break-even calibrado) é a V5. É aqui que dá pra **testar a tese do modelo** antes da régua.

**Custos seguem em % (V3 esvaziada).** Não há custo cheio real por pedido nem os 3 custos novos
(CX, juros de estoque, criativo). A MC da V4 é **parcial** e a curva leva esse rótulo honesto na
tela — sem alvo importado.

**Pré-requisito de dado.** Fonte nova = **HubSpot no BQ** (`silver_deals_minimal`, filtro
`Shipped`) como base oficial de cliente/1ª-compra. Premissa frágil: coortes velhas só se comparam
às novas se o mix não estiver mudando rápido demais (a Minimal 20×'ou de 2022 a 2025) — por isso a
decisão se lê nas **últimas 12–18 safras**.

**Critério de aceite (atualizado 2026-07-10 — MVP).**
- Triângulo de safras fechadas + curva de payback (MC acumulada por cliente × meses desde a 1ª
  compra), com a linha do zero.
- Cada célula marcada **real** (janela de itens atual) ou **estimada** (25%); rótulo "MC parcial".
- Recompra em 90 dias por safra, medida e com rótulo explícito.
- As abas de MC (V1) e de aquisição (V2) intocadas.

> Spec: `docs/specs/2026-07-10-v4-coortes-recompra.md`. **MVP = Opção 2** de arquitetura (CMV real
> só na janela de itens atual; histórico real ano-a-ano fica para a versão seguinte).

**Gancho na V1→V4.** Fecha o ciclo: filtro/cascata (V1) + cliente (V2) → métrica de coorte (V4).
A V3 (custo cheio) foi **esvaziada** — os custos seguem em %.

---

## 3. Ponto de parada e teste

Ao fim da **V4**, o combinado é **parar de construir e rodar o modelo por um tempo** —
usar o lucro-por-cliente-novo e as coortes em decisões reais, ver o que aguenta o mundo
real, e só então decidir se e como seguir para V5-V7. Este é um marco deliberado, não uma
pausa por falta de escopo.

**O que revisitar antes de retomar V5+:**
- A margem bruta real (medida na V4) autoriza um alvo de break-even, ou o alvo da Minimal é
  "lucro positivo no 1º pedido"?
- A recompra real (medida na V4) é forte e estável o bastante para justificar gastar
  adiantado?
- Existe **mandato** para agir sobre o número (mover budget de aquisição)? Sem isso, a régua
  (V5) é um instrumento sem volante.

---

## 4. Parkeado (V5 → V7) — hipóteses, não compromisso

> Só desenhado em bloco. Detalhar quando (e se) a V4 provar a tese.

- **V5 — A régua calibrada.** Alvo de eficiência da Minimal + modulador de estoque (DIO);
  o painel passa a dizer **acelerar / segurar / frear**. Destrava: *"quanto gastar amanhã?"*.
- **V6 — Incrementalidade + survey.** Survey pós-compra ("onde/quando ouviu falar de nós");
  1º holdout (branded search / geo); alvos de ROAS por canal recalibrados pelo real.
  *Ressalva de porte:* holdout/geo exigem volume estatístico — validar se a escala de mídia
  da Minimal comporta antes de investir nisso.
- **V7 — Base como ativo + ritual.** 4 grupos (sem contato / e-mail / SMS / ambos), valor
  residual por e-mail/SMS; ritual "name the number", cadência diária.

---

## 5. Mapa para o documento-fonte

| Versão | Fase no documento (seção 6) |
|---|---|
| V2, V3 | Fase 0 — pré-requisitos de dados (P&L por pedido; base segmentável começa) |
| V4 | Fase 1 — construir a régua (equação fully-loaded + break-even real + coorte) |
| V5 | Fase 1/3 — operar pela régua |
| V6 | Fase 2 — validar com incrementalidade |
| V7 | Fase 3 — operar, escalar, valorar a base |

---

## 6. Princípios inegociáveis do roadmap (para não errar no caminho)

1. **Instrumentação antes da régua** (armadilha nº 6). V2-V4 antes de V5.
2. **Nunca alvo sobre margem de fachada** (armadilha nº 1). Todo custo assumido é marcado
   como provisório na tela.
3. **Calibrar a régua da Minimal, não importar a da True Classic** (armadilha nº 2).
4. **Coorte, não percentual agregado** (armadilha nº 4). Quando a aquisição sobe, o % de
   recompra cai no agregado sem a retenção piorar — ler por safra.
5. **Cada versão nomeia a decisão que destrava.** Se não dá pra nomear, não constrói.
