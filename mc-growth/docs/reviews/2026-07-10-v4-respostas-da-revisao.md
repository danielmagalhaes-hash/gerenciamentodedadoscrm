# Respostas da revisão — V4 (Coortes de recompra)

> Resposta ao relatório `2026-07-10-v4-definicoes-para-revisao.md`, com o
> `motor-crescimento-lucrativo-true-classic.md` como régua principal e os documentos do
> projeto (ROADMAP, ADRs, PRODUCT, ARCHITECTURE) como objeto. Data: 2026-07-10.
>
> **Estrutura:** (1) veredito; (2) o projeto à luz do método True Classic; (3) respostas às
> 7 perguntas dirigidas; (4) o que a revisão NÃO perguntou e deveria (achados novos);
> (5) riscos abertos do §6; (6) lista consolidada de queries de validação (insumo da spec).

---

## 1. Veredito em quatro linhas

A V4 desenhada é o passo certo e as decisões da discovery são defensáveis. Mas a promessa
central da tela — **"cruzou o zero = a turma se pagou"** — está **otimista por construção**
(custos que faltam desde que a V3 foi esvaziada), e **três premissas de viabilidade nunca
foram verificadas** (a ponte histórica pedido↔deal, a cobertura de custo sobre SKUs antigos,
o histórico de mídia). Nada disso derruba o desenho; tudo isso cabe em **seis queries e dois
ajustes de tela antes da spec**.

---

## 2. O projeto à luz do método True Classic

### 2.1 Onde o projeto está fiel (crédito onde é devido)

| Princípio / armadilha do documento | Como o projeto honra |
|---|---|
| **P5 — coorte acima de % agregado** | A V4 é literalmente isso; leitura por safra, nunca % agregado. |
| **Armadilha 6 — régua antes da instrumentação** | V5 (a régua) parkeada até rodar a V4. Disciplina mantida. |
| **Armadilha 2 — copiar números da True Classic** | Nenhum alvo importado; linha do zero neutra; calibração fica pra V5. |
| **Provisório marcado na tela** | Convenção viva desde a V1 (custo faltando = alerta, nunca silêncio). |
| **"Cada versão nomeia a decisão que destrava"** | Todas as versões têm a decisão nomeada; a V3 foi esvaziada exatamente porque não destravava nada — coerente com a regra. |

O próprio relatório de revisão (pedir pra ser furado antes de construir) é o espírito do
"name the number" aplicado a método. Isso é raro e vale registrar.

### 2.2 Os três desvios estruturais (e o que custam)

**Desvio 1 — O fully-loaded foi abandonado junto com a V3 (armadilha nº 1 do documento: "o
erro mais comum e o mais caro").** A MC da V4 desconta os % da DRE (devolução, frete,
gateway…), mas **não** desconta três custos que o modelo manda contar: **CX por pedido,
juros da dívida de estoque e criativo como custo variável** — e a devolução entra como %,
sem o custo de processá-la. Cada custo omitido infla a margem; margem inflada faz a curva
**cruzar o zero cedo demais**. É como pesar numa balança que ignora parte da carga: o
ponteiro bate no "se pagou" antes da hora (margem de fachada, no vocabulário do documento).
- **Não precisa ressuscitar a V3.** Manter custos em % é compatível com o método; o que o
  método não perdoa é custo **faltando sem aviso**. Correção mínima, em ordem de custo:
  1. **Dimensionar uma vez** os 3 ausentes (nº de tickets/pedido × custo do ticket; juro da
     linha de estoque; gasto de criativo do mês) — uma conversa com Financeiro, não um build.
  2. Se algum for material (> ~2 p.p. de margem), entra como **% provisório** na cascata
     (o mecanismo já existe).
  3. Enquanto não dimensionar: **rotular a curva** — "MC parcial (não desconta CX, juros de
     estoque e criativo)". A linha do zero deixa de prometer o que não mede.

**Desvio 2 — Mídia atribuída e blended (a V6, incrementalidade, está parkeada).** Toda a
mídia do mês cai no m+0 da safra, incluindo remarketing. Aceitável como aproximação
declarada — mas a consequência precisa ficar explícita: **a V4 é um instrumento de
TENDÊNCIA (safras melhorando ou piorando entre si), não de veredito absoluto**. O veredito
("empata? gasta all day long?") exige a mídia certa no lugar certo — é V5/V6. Detalhe na
resposta à pergunta 2.

**Desvio 3 — A curva é média; a decisão de acelerar é marginal (P4).** A coorte mostra a
economia do cliente **médio** da safra. Quando o João pisar no acelerador, o próximo cliente
custa **mais** que o médio (os últimos reais de mídia rendem menos que os primeiros). A V4
não resolve isso (nem deve) — mas dá pra importar o ritual de bolso da True Classic sem
build nenhum: **ao acelerar, declarar o CAC esperado da próxima safra e conferir quando ela
fechar** ("name the number"). Se o CAC realizado vier sistematicamente acima do declarado,
é o marginal cobrando a diferença.

### 2.3 Inconsistência de documento (mantra 4 — relatar, nunca silenciar)

O **`ROADMAP.md` (seção V4) está desatualizado**: ainda promete "lucro por cliente novo,
**custo cheio**" e "Combina V2 + **V3**" nos critérios de aceite — mas a V3 foi esvaziada e o
`PRODUCT.md` V4 já não promete custo cheio. Se a spec for escrita com o ROADMAP na mão, ela
herda uma promessa que a discovery revogou. **Corrigir o ROADMAP antes da spec.**

---

## 3. Respostas às 7 perguntas dirigidas

### P1 — O viés cross-canal é mesmo pequeno? Vale construir antes de medir?

**Não construa antes de medir — e a suspeita da pergunta está certa:** "95% das **vendas**
são Shopify" não diz nada sobre "95% dos **clientes** estrearam no Shopify". São
distribuições diferentes (a segunda é sobre pessoas, a primeira sobre reais).

E o viés **não é ruído simétrico — ele lisonjeia a curva**, por dois mecanismos:
1. **CAC diluído:** o cliente que estreou no TikTok em 2023 entra na turma de 2023 (N_S
   cresce), mas a mídia Shopify de 2023 não o comprou → CAC/cliente **subestimado**.
2. **Cauda inflada nas safras velhas:** a compra Shopify de 2026 desse cliente vira
   "recompra" da safra de 2023 — MC caindo de graça numa turma que não pagou por ele. É
   contar na turma de 2023 um aluno que só se matriculou nesta escola em 2026.

Os dois erros empurram na mesma direção: **curvas melhores do que a economia real da
aquisição Shopify** → viés pró-"acelerar". E ele se **concentra** em safras específicas
(meses de campanha forte fora do Shopify), então o número global esconde o pico.

**O que fazer (sem re-litigar a decisão do João):** a âncora HubSpot fica; o que se define é
um **portão de medição**. A query custa uma hora: por safra, % de clientes cuja 1ª compra
não está no `Shipped`. **Portão sugerido:** se em alguma safra dos últimos 12 meses passar de
~10%, o CAC daquela safra está subestimado nessa ordem — aí ou a tela ganha uma coluna
"% estreou fora do Shopify", ou a âncora se rediscute. Abaixo disso, o viés documentado
basta.

### P2 — A mídia inteira no mês 0 corrompe a leitura?

**Distorce, mas em direções opostas — e o líquido é ambíguo:**
- O **m+0 fica fundo demais**: a safra nova carrega a conta do jantar da mesa inteira
  (inclusive o remarketing que serviu os clientes antigos). CAC superestimado → pessimista.
- As **caudas sobem rápido demais**: a recompra do m+3 chega bruta, sem descontar o
  remarketing que a empurrou (essa mídia foi cobrada do m+0 de OUTRA safra). → otimista.

No sistema inteiro a mídia é contada uma vez só (a soma fecha); o que está errado é a
**alocação**. Consequências práticas:
1. **Para comparar safras entre si (tendência), o viés praticamente cancela — DESDE QUE a
   proporção remarketing/aquisição seja estável.** Se um dia a Minimal dobrar o remarketing,
   as safras novas vão "piorar" na tela sem nada ter piorado. Essa premissa de estabilidade
   deve estar escrita na tela ou no rodapé da spec.
2. **Para o veredito absoluto ("esta safra se pagou em 4 meses"), o número não é confiável**
   — nem pra mais, nem pra menos. Reforça: V4 = tendência; veredito = V5/V6.
3. **Não** tente separar aquisição × remarketing agora (é o escopo parkeado, e fazê-lo mal é
   pior que não fazer). Meio-termo barato e opcional: uma **banda de sensibilidade** — a
   curva desenhada 2x, com 100% e com um % assumido de aquisição (parâmetro único, marcado
   provisório). Comunica a incerteza sem fingir a cirurgia.

### P3 — "Olhar tudo" ajuda ou engana?

**Mostrar tudo ajuda; decidir com tudo engana.** O triângulo completo é barato e serve de
memória institucional. Mas a comparação entre eras distantes carrega **três artefatos ao
mesmo tempo** (P4 — custo de hoje penaliza as safras velhas; achado novo nº 1 — SKUs velhos
sem custo lisonjeiam as safras velhas; P1 — caudas velhas infladas pelo cross-canal). Ou
seja: **o triângulo é menos confiável exatamente onde é mais tentador contar história**
("olha como melhoramos desde 2022").

**Recomendação:** manter a tabela cheia; **a decisão se lê nas últimas 12–18 safras** (o
padrão de 12 na curva já está certo). Opcional: um separador visual de "era" na tabela
(ex.: linha divisória em 2024) pra lembrar que antes dali é outra empresa — o próprio
relatório já reconhece o 20x de mix.

### P4 — Custo de hoje sobre venda de 2022 distorce? Em que direção?

**Distorce, e a direção mecânica é: safras velhas parecem PIORES do que foram.** Custos de
insumo sobem (inflação + câmbio); aplicar o custo de 2026 à venda de 2022 infla o CMV
histórico → MC velha subestimada → payback velho esticado. Consequência perversa: a
"melhora" entre eras que a tela vai mostrar é **em parte artefato da régua**, não mérito —
é medir o passado com a régua de preços de hoje.

**Porém — e este é o ponto que a pergunta não previu — existe um efeito contrário que pode
dominar:** SKUs de 2022 descontinuados provavelmente **não existem** na tabela de custo
atual (3.1/3) → custo faltando → CMV velho **sub**estimado → safras velhas lisonjeadas
(achado nº 1, seção 4). Qual efeito ganha só a query de cobertura diz.

**Nas safras recentes (12–18 meses), os dois efeitos são ~zero** — mais um motivo pra
decidir no recorte curto. Não há como "corrigir" (custo histórico por SKU não existe);
restringir a leitura é a correção.

### P5 — `data_primeira_compra` é confiável e estável?

**Não assumir que sim — há dois mecanismos reais de reescrita retroativa:**
1. **É campo derivado do pipeline** (a tabela é `prod_silver`, feita pelo time de Dados, não
   um campo nativo do HubSpot). Se for `MIN(data)` sobre os deals, é determinístico — mas
   **muda quando entra dado antigo** (backfill de um canal, por exemplo).
2. **O HubSpot mescla contatos** (merge de duplicados). Quando dois contatos viram um, o
   e-mail vencedor e o histórico mudam — um cliente pode **trocar de safra** depois de lido.

**Ações (baratas, no padrão do projeto):**
- **Perguntar ao time de Dados** como o campo é derivado e o que o move (1 mensagem).
- **Guarda de deriva:** guardar uma foto mensal do tamanho de cada safra (N por safra) e
  **alertar se uma safra fechada mudar de tamanho** entre leituras — é conferir se alguém
  mexeu nas notas antigas do boletim. Encaixa na tradição de guarda silenciosa da V2 e
  custa poucas linhas.

### P6 — Payback por cliente basta, ou precisa do valor absoluto?

**Precisa dos dois — o método manda.** Na True Classic, eficiência é o **teto** e escala é o
**objetivo** ("maximize scale dentro das restrições"). A MC/cliente responde à eficiência;
a decisão de acelerar precisa saber **quantos clientes** e **quanta MC total** a safra traz —
uma safra minúscula que se paga em 2 meses não sustenta crescimento; uma safra enorme que se
paga em 5 pode ser o motor.

**Recomendação concreta:** o triângulo ganha a coluna **`Clientes` (N_S)** ao lado do CAC
(custo ~zero: o número já é o denominador de tudo). Opcional: MC acumulada **total** da
safra como terceira coluna ou tooltip. E o lembrete do desvio 3 (§2.2): a curva é média,
acelerar é marginal — "name the number" ao pisar.

### P7 — 90 dias é a janela certa?

**Não se decide no grito — a própria base responde.** Uma query dá a distribuição do tempo
entre a 1ª e a 2ª compra (mediana, p75) no histórico `Shipped`. Se a mediana da 2ª compra
cai em ~70 dias, 90 está ótimo; se cai em ~140 (plausível pra guarda-roupa premium
masculino, recompra por estação), 90 corta o filme no meio e vai parecer que ninguém
recompra.

**Recomendações:**
- Janela **fixa** continua certa (comparabilidade entre safras — o motivo original está
  correto). O que a query calibra é o **número**.
- Se o ciclo natural for longo, mostrar **duas janelas com rótulo** ("recompra em 90d" e
  "em 180d") — barato, e evita jogar fora a comparabilidade com o mercado (90d é o padrão
  de benchmark DTC).
- O triângulo e a curva já mostram o filme completo; a janela é KPI secundário — errar o
  número não quebra a V4, só o cartão.

---

## 4. O que a revisão NÃO perguntou (achados novos)

**4.1 — Cobertura da tabela de custo sobre SKUs históricos (potencialmente o maior viés das
safras velhas).** A convenção "custo atual aplicado ao passado" assume que o SKU de 2022
**existe** na 3.1/3 de hoje. Catálogo de moda gira; SKUs descontinuados somem da tabela →
CMV histórico faltando → MC velha inflada. Isso pode ser **maior** que o efeito inflação
(P4) e ninguém mediu. **Query nova obrigatória:** por ano, % da quantidade vendida cujo SKU
tem custo hoje (2022, 2023, 2024, 2025).

**4.2 — A ponte histórica pedido↔deal nunca foi verificada fora da janelinha da planilha.**
A ponte `nome`→`Vendas.order_name`→`order_id`→Itens foi vista funcionando **na planilha, que
só tem abr–jul/2026**. Para 2022–2025 é preciso que exista no BQ uma tabela de pedidos com
`order_name`↔`order_id` — a base de itens sozinha (`id, data_order, sku, quantidade`) **não
tem o número humano do pedido**. Se essa ponte não existir no histórico, o plano inteiro da
"MC real desde 2022" cai. **Query de viabilidade: taxa de casamento HubSpot `nome` → pedido
→ itens, por ano.**

**4.3 — O CAC de todas as safras exige mídia mensal desde 2022 — e a aba `Midia` pode ser
janelada como as outras.** Confirmar no BQ a série mensal 2022→hoje com a **mesma definição**
do painel (FB embrutecido ÷(1−0,1215) + Google + institucional). Sem isso, não há m+0 para
as safras antigas.

**4.4 — O editor de custos não alcança a V4 (decisão de arquitetura escondida).** Hoje a
lógica de custo (3.1 → 3 → `custos_extra.csv` local) mora no painel. Se o CMV histórico for
calculado **no BigQuery** (pré-agregado), as correções do João e o fallback **não se
aplicam** à V4 — as duas abas divergiriam silenciosamente. A spec precisa decidir **onde
mora a junção com custo**. Caminho que preserva os invariantes: **pré-agregação local** —
um script mensal (fora do painel) puxa o bruto do BQ, aplica a MESMA lógica de custo do
painel e salva um arquivo local; o painel só lê o arquivo. Detalhe na seção 5.

**4.5 — Fragmentação de e-mail.** Cliente com dois e-mails vira dois "clientes": a recompra
dele parece aquisição de outra pessoa → recompra **subestimada** (viés conservador nas
caudas). Provavelmente pequeno; medir só se a base tiver uma chave alternativa
(telefone/customer_id) pra amostrar. Registrar como limitação conhecida.

**4.6 — A fórmula dos 25% está internamente inconsistente no `PRODUCT.md`.** Como escrita
(§6: `CMV_est = valor × 0,75` **e** deduções % por cima), a margem estimada pré-2022 vira
`25% − deduções%` ≈ um dígito — não os "25% de margem de produto" da intenção. Se a
intenção é MC de produto = 25% do valor, o certo é `MC_produto_est = 0,25 × valor` (sem
deduzir de novo) ou `CMV_est = (0,75 − deduções%) × valor`. Materialidade ínfima (pré-2022),
mas é exatamente o tipo de formuleta que se copia errado pra spec — corrigir lá.

**4.7 — `ROADMAP.md` desatualizado** (ver §2.3): a seção V4 ainda promete custo cheio.

---

## 5. Riscos abertos do §6 — posição

**Arquitetura (BQ direto × pré-agregado): recomendo pré-agregado, com refresh mensal.**
O dado da V4 muda **uma vez por mês** (regra da safra fechada: só mês encerrado). Ler o BQ
ao vivo compraria credencial no painel (contra o espírito do ADR do stack), latência, custo
por consulta e um modo de falha novo — para servir um número que é uma foto mensal. Desenho
candidato (a spec bate o martelo):
- **Script mensal separado do painel** (esse sim com credencial BQ, rodado pelo João no
  início do mês): puxa deals `Shipped` + itens do BQ, aplica a lógica de custo **do painel**
  (3.1 → 3 → `custos_extra.csv` — resolve o achado 4.4), monta o triângulo
  (safra × mês: MC, N, receita) e salva um arquivo local pequeno (~milhares de linhas).
- **O painel só lê o arquivo local** — sem credencial, rápido, e a aba de coortes degrada
  com mensagem clara se o arquivo estiver velho ("triângulo de maio; rode a atualização").
- Alternativa se o João preferir zero-script: o time de Dados agenda a query e despeja o
  pré-agregado numa aba nova da planilha (o triângulo agregado CABE numa aba; anos de itens
  é que não cabem). Custo: a lógica de custo migra pro BQ (reabre o 4.4).

**`valor` × `net_revenue`:** rodar **antes de congelar a spec**, na janela de sobreposição
(abr–jun/2026), em duas camadas: taxa de casamento por pedido (quantos `nome` acham
`order_name`) e delta de valor nos casados (Σ e distribuição). Se o delta for sistemático
(ex.: `valor` = bruto sem desconto), a receita por deal vem da ponte com `net_revenue`, e o
`valor` do HubSpot fica só de conferência.

**Base dos 25%:** resolvido acima (achado 4.6) — definir a fórmula na spec e pronto.

---

## 6. Queries de validação consolidadas (insumo direto da spec)

| # | Query | Tipo | Decide o quê |
|---|---|---|---|
| 1 | `valor` (HubSpot) × `net_revenue` (Shopify), abr–jun/2026: taxa de casamento + delta | Calibração | De onde vem a receita por deal |
| 2 | % de clientes por safra cuja 1ª compra não está no `Shipped` | Calibração/portão | Tamanho e concentração do viés cross-canal (portão ~10%) |
| 3 | % da quantidade vendida por ano cujo SKU tem custo na 3.1/3 de hoje | **Viabilidade** | Se a MC real histórica é real mesmo (achado 4.1) |
| 4 | Taxa de casamento HubSpot `nome` → pedido → itens, por ano (2022–2025) | **Viabilidade** | Se a ponte histórica existe fora da planilha (achado 4.2) |
| 5 | Série mensal de mídia 2022→hoje no BQ, na definição do painel | **Viabilidade** | Se há CAC para as safras antigas (achado 4.3) |
| 6 | Distribuição do tempo até a 2ª compra (mediana, p75) | Calibração | A janela de recompra certa (P7) |

As três de **viabilidade** (3, 4, 5) vêm primeiro: se alguma falhar, o desenho muda; as de
calibração afinam números de um desenho que fica de pé.

---

## 7. Recomendações priorizadas (o que muda na spec)

1. **Rodar as 6 queries** (as de viabilidade primeiro). Nenhuma linha de spec de arquitetura
   antes da 4 e da 5.
2. **Dimensionar os 3 custos ausentes** (CX/pedido, juros de estoque, criativo) com o
   Financeiro — 1 conversa. Material → % provisório; imaterial → registrar; enquanto isso →
   **rotular a curva como "MC parcial"**. A linha do zero não pode prometer o que não mede.
3. **Arquitetura: pré-agregado local mensal**, lógica de custo do painel reaproveitada
   (resolve o 4.4). ADR próprio.
4. **Tela:** coluna `Clientes` (N_S) no triângulo; rótulo explícito da janela de recompra;
   premissa "proporção de remarketing estável" declarada; opcional banda de sensibilidade
   da mídia.
5. **Guarda de deriva de safra** (foto mensal de N por safra; alerta se safra fechada mudar)
   + perguntar ao Dados a derivação de `data_primeira_compra`.
6. **Corrigir documentos antes da spec:** `ROADMAP.md` V4 (custo cheio revogado) e a fórmula
   dos 25% no `PRODUCT.md`.
7. **Enquadrar a V4 na tela e na spec como instrumento de tendência** — o veredito absoluto
   de payback chega com V5/V6. Ritual de bolso ao acelerar: declarar o CAC esperado da
   próxima safra e conferir ("name the number").
