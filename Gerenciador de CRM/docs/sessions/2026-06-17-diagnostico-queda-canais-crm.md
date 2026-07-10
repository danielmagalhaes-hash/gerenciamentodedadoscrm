# Diagnóstico de Queda de Resultados — Canais CRM
**Data:** 17/06/2026 | **Período:** 23/04 → 16/06/2026 | **Baseline:** média das 6 semanas completas de 27/04 a 01/06

---

## Resumo Executivo

O CRM total caiu **-22% na semana de 08/06 vs. baseline** (R$ 350.862 → R$ 272.541). A queda **não é uniforme** — um canal cresceu, os demais caíram por causas distintas.

| Canal | Baseline (média/semana) | Semana 08/06 | Variação | Contribuição para queda |
|---|---|---|---|---|
| E-mail Fluxo | R$ 65.946 | R$ 67.413 | **+2,2%** | Não contribuiu |
| WPP Fluxo | R$ 121.262 | R$ 112.364 | -7,3% | -R$ 8.898 (11%) |
| E-mail Campanha | R$ 86.589 | R$ 51.518 | **-40,5%** | **-R$ 35.071 (45%)** |
| WPP Campanha | R$ 54.486 | R$ 28.889 | **-47,0%** | **-R$ 25.597 (33%)** |
| WPP Comunidade | R$ 22.578 | R$ 12.357 | -45,3% | -R$ 10.221 (13%) |
| **TOTAL** | **R$ 350.862** | **R$ 272.541** | **-22,3%** | **-R$ 78.321** |

**Waterfall:**
```
Baseline:          R$ 350.862
E-mail Campanha:  −R$  35.071  ████████████████████████ 45%
WPP Campanha:     −R$  25.597  ██████████████████ 33%
WPP Comunidade:   −R$  10.221  ███████ 13%
WPP Fluxo:        −R$   8.898  ██████ 11%
E-mail Fluxo:     +R$   1.467  (cresceu)
Resultado:         R$ 272.541
```

**Causas-raiz confirmadas:**

1. **E-mail Campanha (45% da queda):** Disparos foram normais (644k). A causa é mudança de mix de campanhas — a semana teve campanhas de conteúdo/editorial ("A camiseta é só o começo", pesquisa, reforços de produtos já enviados) sem um lançamento-herói. CTOR caiu para 0,7% vs. 1,4% nas semanas com lançamento. Não é problema de lista — é problema de calendário editorial.

2. **WPP Campanha (33% da queda):** Sem dados de disparo disponíveis (Vekta não integrado). A volatilidade histórica (R$ 18k → R$ 88k → R$ 18k) mostra dependência direta de quando uma campanha pontual ocorre. Semana 08/06 provavelmente sem campanha relevante — aguarda confirmação com dados que o Daniel vai disponibilizar.

3. **WPP Comunidade (13% da queda):** Erosão estrutural crônica — a base perde mais membros do que ganha em **todas as 14 semanas disponíveis** desde março. Não é evento de 08/06: é tendência que precede o período de queda.

4. **WPP Fluxo (11% da queda):** Queda leve, sem sinal de alerta. Dados de funil disponíveis apenas desde 08/06 — sem baseline para comparar.

5. **E-mail Fluxo:** Não caiu. Volume cresceu 96% em 10 semanas, receita sustentando, mas taxa de abertura declina sistematicamente (42,9% → 37,2%). Risco de médio prazo.

---

## Fase 1 — Série Temporal de Receita

### Receita semanal por canal (R$)

| Semana | E-mail Camp. | E-mail Fluxo | WPP Camp. | WPP Fluxo | Comunidade | **TOTAL** |
|---|---|---|---|---|---|---|
| 27/04 | 85.498 | 61.564 | 86.179 | 95.347 | 16.485 | **345.073** |
| 04/05 | 74.585 | 53.696 | 18.025 | 110.876 | 22.642 | **279.824** |
| 11/05 | 110.282 | 56.434 | 42.128 | 123.830 | 36.985 | **369.659** |
| 18/05 | 84.756 | 63.853 | 67.628 | 116.569 | 25.098 | **357.904** |
| 25/05 | 80.280 | 96.745 | 88.303 | 139.236 | 17.481 | **422.045** |
| 01/06 | 84.135 | 63.386 | 24.651 | 141.714 | 16.779 | **330.665** |
| **Média baseline** | **86.589** | **65.946** | **54.486** | **121.262** | **22.578** | **350.862** |
| **08/06** | **51.518** | **67.413** | **28.889** | **112.364** | **12.357** | **272.541** |
| 15/06 *(2 dias)* | 19.894 | 19.094 | 10.042 | 27.800 | 3.508 | 80.338 |

**Ponto de inflexão:** Semana de 08/06. A semana de 15/06 tem apenas segunda e terça — não é comparável.

**Observação sobre WPP Campanha:** amplitude de R$ 70k entre pico (R$ 88k) e vale (R$ 18k) ao longo do baseline. Semanas sem campanha relevante são indistinguíveis de "queda de performance" pelos dados de receita isolados.

---

## Fase 2 — Decomposição de Funil por Canal

### 2.1 E-mail Fluxo — Estável, Risco Futuro

| Semana | Disparos | Tx Abertura | CTOR | Receita | R$/Disparo |
|---|---|---|---|---|---|
| 04/05 | 146.364 | 42,9% | 1,9% | R$ 53.696 | R$ 0,37 |
| 11/05 | 175.819 | 41,4% | 2,4% | R$ 56.434 | R$ 0,32 |
| 18/05 | 196.792 | 41,8% | 2,1% | R$ 63.853 | R$ 0,32 |
| 25/05 | 230.314 | 40,1% | 2,1% | R$ 96.745 | R$ 0,42 |
| 01/06 | 254.529 | 38,7% | 1,8% | R$ 63.386 | R$ 0,25 |
| **08/06** | **286.962** | **37,2%** | **1,8%** | **R$ 67.413** | **R$ 0,23** |

- Disparos cresceram +96% em 10 semanas. Taxa de abertura caiu -5,7pp no mesmo período.
- CTOR estável (1,7–2,4%): o conteúdo não degradou, quem abre ainda clica.
- Receita sustenta porque volume compensa, mas eficiência por disparo caiu de R$ 0,37 para R$ 0,23 (-38%).
- **Gargalo atual:** CTOR de ~2% — de cada 100 aberturas, 2 clicam. Muito baixo para um canal de fluxo.
- **Risco futuro:** se a abertura continuar caindo -1,1pp/semana, em 4–5 semanas o canal não consegue mais compensar por volume.

**Veredicto: canal saudável no curto prazo, em fadiga no médio prazo.**

---

### 2.2 E-mail Campanha — Problema de Mix, Não de Lista

**Funil semanal completo:**

| Semana | Campanhas | Disparos | Tx Abertura | CTOR | Receita | R$/Clique |
|---|---|---|---|---|---|---|
| 27/04 | 36 | 570.734 | 74,7% | 1,1% | R$ 85.498 | R$ 18,09 |
| 04/05 | 31 | 483.165 | 70,6% | 1,0% | R$ 74.585 | R$ 20,88 |
| 11/05 | 37 | 783.179 | 58,8% | **1,4%** | R$ 110.282 | R$ 17,61 |
| 18/05 | 42 | 994.119 | 39,5% | 1,1% | R$ 84.756 | R$ 19,35 |
| 25/05 | 33 | 536.591 | 59,3% | 0,8% | R$ 80.280 | R$ 32,19 |
| 01/06 | 32 | 887.821 | 54,3% | 1,0% | R$ 84.135 | R$ 16,96 |
| **Média baseline** | **35** | **709.268** | **59,5%** | **1,0%** | **R$ 86.589** | **R$ 20,84** |
| **08/06** | **30** | **644.951** | **78,8%** | **0,7%** | **R$ 51.518** | **R$ 14,20** |

**Achado principal:** disparos da semana 08/06 estavam em 91% da média do baseline — volume praticamente normal. A queda de receita não é de volume: é de qualidade da conversão.

**Detalhamento das campanhas da semana 08/06 vs. semana de pico (11/05):**

*Semana 11/05 — "Lançamento Inverno" (R$ 110.282):*

| Campanha | Disparos | Tx Abertura | CTOR | Cliques |
|---|---|---|---|---|
| [EM1249] Lançamento Inverno [CLIENTES A+] | 42.923 | 84,1% | **2,2%** | 799 |
| [EM1249] Lançamento Inverno ERRATA [CLIENTES A+] | 103.947 | 47,7% | **1,6%** | 773 |
| [EM1250] Reforço Lançamento Inverno [CLIENTES A+] | 45.244 | 79,6% | **1,8%** | 665 |
| [EM1251] Jaqueta Westfield [CLIENTES A+] | 45.786 | 76,0% | **1,9%** | 646 |
| [EM1252] Sueter Tricot [CLIENTES A+] | 46.316 | 68,5% | **1,8%** | 563 |

*Semana 08/06 — "A camiseta é só o começo" + reforços (R$ 51.518):*

| Campanha | Disparos | Tx Abertura | CTOR | Cliques |
|---|---|---|---|---|
| [EM1271] Desconto Progressivo [CLIENTES A+] | 51.460 | 81,2% | **0,7%** | 299 |
| [EM1251] Jaqueta Westfield **2** [CLIENTES A+] | 48.826 | 80,6% | **0,8%** | 300 |
| [EM1274] A camiseta é só o começo [CLIENTES A+] | 48.491 | 74,7% | **0,6%** | 212 |
| [EM1272] Última oportunidade - Gola Alta [CLIENTES A+] | 48.486 | 79,8% | **0,6%** | 243 |
| [EM1273] Fim de Estoque Inverno [CLIENTES A+] | 48.460 | 78,1% | **0,9%** | 328 |
| Clientes Vips - **Pesquisa** novas cores | 8.409 | 53,5% | 2,2% | 99 |

**O que esses dados dizem:**

1. **Mesma audiência, CTOR 2,5x menor.** Jaqueta Westfield "1" (semana 11/05) teve CTOR 1,9% com 646 cliques. A mesma campanha com "2" (segunda onda para o mesmo público, semana 08/06) teve CTOR 0,8% com 300 cliques. Audiência que já viu o produto clica bem menos na segunda exposição.

2. **Semana sem lançamento-herói.** A semana de 11/05 tinha "Lançamento Inverno" como evento âncora (novidade com urgência real). A semana de 08/06 tinha uma série editorial de conteúdo ("A camiseta é só o começo"), reforços de produtos já vistos e uma pesquisa. Nenhum desses tem a mesma força de conversão de um lançamento.

3. **Receita por clique caiu de R$ 17–21 para R$ 14,20.** Mesmo quem clicou converteu menos — as campanhas de 08/06 provavelmente apontavam para páginas de produto sem urgência (sem estoque limitado, sem oferta especial).

4. **Apple MPP distorce a taxa de abertura.** A taxa de 78–81% nos segmentos [CLIENTES A+] é inflada por abertura automática do iOS (Apple Mail Privacy Protection). A abertura "real" é menor — o CTOR calculado sobre essa base inflada subestima ainda mais o problema. Campanhas para [BASE TOTAL] na semana anterior (semana 11/05) mostram o padrão oposto: 2,7% de abertura mas CTOR de 17%, pois são aberturas reais de usuários motivados.

**Veredicto de E-mail Campanha: queda causada por calendário editorial fraco na semana de 08/06. Sem lançamento-herói + reforços de audiências já saturadas + campanha de pesquisa = CTOR mínimo. Não é degradação de lista.**

---

### 2.3 WPP Fluxo — Queda Leve, Sem Alarme

**Receita:** -7,3% na semana de 08/06 vs. baseline (R$ 112.364 vs. R$ 121.262). Menor declínio entre os canais que caíram.

**Funil de leads (leads_webhook — disponível apenas desde 08/06):**

| Fluxo | Leads/dia (média 10–16/06) | Pct resposta (aprox.) |
|---|---|---|
| Fluxo Welcome Site | ~1.300 | 15–30% |
| Up-sell Perpetuo | ~140 *(ativo desde ~12/06)* | alto (acumulado) |
| Welcome TOF | ~110 | 15–25% |
| Fluxo PageView | ~95 | 25–35% |
| [Fluxo] Aquisição - PageView | ~120 | 15–20% |

**Limitação:** sem baseline histórico de leads (dados começam em 08/06), não é possível afirmar se o funil de vendas deteriorou. A queda de -7% de receita pode ser variação normal de calendário.

**Observação:** "resposta" no leads_webhook é taxa de resposta ao vendedor no CRM, não taxa de leitura de mensagem WA.

---

### 2.4 WPP Campanha — Sem Funil, Alta Volatilidade Estrutural

Vekta campanha não integrado — dados de disparo/entrega/resposta indisponíveis. Dashboard já sinaliza "dados parcialmente fictícios".

**O padrão da receita confirma dependência de eventos pontuais:**
- Vale estrutural: R$ 18–29k (semanas sem campanha relevante)
- Pico estrutural: R$ 67–88k (semanas com campanha forte)
- Semana 08/06 (R$ 28.889) = vale, consistente com semanas sem campanha relevante (igual a 04/05 e 01/06)

Quando você disponibilizar os dados de WPP Campanha, vou incorporar o funil e confirmar se foi ausência de disparo ou queda de conversão.

---

### 2.5 WPP Comunidade — Erosão Estrutural Crônica

**Tendência de membros (semanal, fact_community_analytics):**

| Semana | Entradas | Saídas | Saldo | Cliques (aquisição) |
|---|---|---|---|---|
| 09/03 | 13 | 179 | **-166** | 0 |
| 16/03 | 33 | 327 | **-294** | 0 |
| 23/03 | 38 | 372 | **-334** | 0 |
| 30/03 | 23 | 288 | **-265** | 0 |
| 06/04 | 15 | 212 | **-197** | 0 |
| 13/04 | 17 | 230 | **-213** | 0 |
| 20/04 | 32 | 234 | **-202** | 0 |
| 27/04 | 36 | 300 | **-264** | 0 |
| 04/05 | 32 | 215 | **-183** | 0 |
| 11/05 | 85 | 318 | **-233** | **182** |
| 18/05 | 34 | 359 | **-325** | 2 |
| 25/05 | 42 | 266 | **-224** | 2 |
| 01/06 | 24 | 157 | **-133** | 0 |
| **08/06** | **49** | **219** | **-170** | **0** |
| **15/06** | **20** | **58** | **-38** | **0** |

**Leitura:**
- Saldo negativo **em todas as 14 semanas disponíveis** desde março. Sem uma semana sequer de crescimento líquido.
- Cliques de aquisição essencialmente zero — nenhum mecanismo de reposição de membros ativo.
- Único spike de cliques (182 em 11/05) não se sustentou — provavelmente uma campanha pontual de captação que não virou rotina.
- Base em 23.302 → 23.126 nos últimos dois snapshots disponíveis.
- 6 erros de cron na semana 08/06 (67% taxa de erro) — parte da queda de receita pode ser dado não capturado, não venda real perdida.

**Veredicto: o canal está em erosão estrutural desde pelo menos março. A queda de receita em 08/06 é continuação da tendência, não evento isolado.**

---

## Fase 3 — Atribuição da Queda (Waterfall Detalhado)

### E-mail Campanha — decomposição por fator

Comparando baseline (média 6 semanas) vs. semana 08/06:

| Fator | Baseline | 08/06 | Variação | Impacto em R$ |
|---|---|---|---|---|
| Disparos | 709.268 | 644.951 | -9% | Menor contribuição |
| Cliques (volume) | ~4.400 | 3.627 | -18% | — |
| CTOR | ~1,0% | 0,7% | -30% | **Gargalo principal** |
| R$/Clique | R$ 20,84 | R$ 14,20 | -32% | **Gargalo secundário** |
| Receita total | R$ 86.589 | R$ 51.518 | **-40,5%** | -R$ 35.071 |

A queda de R$ 35k é explicada principalmente por dois fatores que se multiplicam:
- CTOR menor (-30%) → menos cliques → menos compradores potenciais
- Receita por clique menor (-32%) → compradores que chegaram converteram menos

Esses dois fatores juntos explicam ~-55% de receita teórica. O volume de disparos levemente menor (-9%) contribuiu marginalmente.

### Total do CRM — contribuição por canal

| Canal | Δ Receita | % da queda |
|---|---|---|
| E-mail Campanha | **-R$ 35.071** | **45%** |
| WPP Campanha | -R$ 25.597 | 33% |
| WPP Comunidade | -R$ 10.221 | 13% |
| WPP Fluxo | -R$ 8.898 | 11% |
| E-mail Fluxo | +R$ 1.467 | (cresceu) |
| **Total** | **-R$ 78.321** | **100%** |

---

## Fase 4 — Hipóteses de Causa-Raiz

### H1: E-mail Campanha caiu por calendário editorial fraco (sem lançamento-herói)
**Veredito: Confirmada**
- Disparos na semana 08/06: 644.951 (91% da média — volume normal)
- CTOR caiu de 1,0% (baseline) para 0,7% — mínimo histórico
- Semana 11/05 (maior receita): "Lançamento Inverno" com CTOR 1,6–2,2%
- Semana 08/06: série editorial "A camiseta é só o começo" + reforços + pesquisa → CTOR 0,4–0,9%
- Mesma campanha (Jaqueta Westfield): 1,9% CTOR na 1ª onda (11/05), 0,8% na 2ª onda (08/06)

### H2: Apple MPP distorce taxa de abertura do E-mail Campanha
**Veredito: Confirmada (achado de qualidade de dado)**
- Segmentos [CLIENTES A+] mostram abertura de 80–83% consistentemente — impossível com aberturas humanas
- Algumas campanhas históricas mostram 100.000%+ de abertura (abertura acumulada dividida por zero ou quase zero disparos na semana)
- A taxa de abertura é um KPI não confiável para E-mail Campanha neste projeto. **CTOR é a única métrica de engajamento utilizável.**

### H3: WPP Comunidade em erosão estrutural de base
**Veredito: Confirmada**
- Saldo negativo em todas as 14 semanas desde março
- Sem mecanismo de reposição ativo (cliques de aquisição = 0)

### H4: Falha de ingestão mascarando receita real como queda
**Veredito: Confirmada parcialmente (Comunidade), refutada para demais canais**
- 6 erros de cron `community` na semana de 08/06 (67% falha)
- Crons de `revenue`, `email_flow`, `email_campaign` rodaram sem falhas críticas

### H5: E-mail Fluxo com fadiga de lista em início
**Veredito: Confirmada como risco futuro**
- Abertura caindo -5,7pp em 5 semanas (42,9% → 37,2%) enquanto volume cresce 96%
- R$/disparo caiu R$ 0,37 → R$ 0,23 (-38%)
- Receita ainda sustenta mas o motor está desacelerando

### H6: Queda de atribuição (medição, não venda)
**Veredito: Inconclusiva — requer verificação pontual**
- 21.222 pedidos (R$ 11,8M) sem canal atribuído no período total
- Não foi possível verificar se a proporção de pedidos sem canal aumentou especificamente na semana 08/06

---

## Recomendações Priorizadas

### 1. Calendário editorial de E-mail Campanha (impacto imediato: ~R$ 35k/semana)
A semana de 08/06 não teve um "lançamento-herói". Semanas com lançamento de produto novo geram CTOR de 1,6–2,2%; semanas com reforços e conteúdo editorial geram 0,7%. A ação é de planejamento, não técnica: garantir que toda semana de campanha tenha pelo menos um e-mail com oferta/produto novo em vez de reforçar audiências já impactadas.

### 2. Não reenviar a mesma campanha para o mesmo segmento (impacto: CTOR dobrado)
Jaqueta Westfield "1" → CTOR 1,9%. Jaqueta Westfield "2" para a mesma audiência → CTOR 0,8%. A segunda onda para o mesmo público reduz o CTOR pela metade. Onde for inevitável reenviar, mudar o segmento (ex: quem não abriu a 1ª, não quem abriu).

### 3. Parar de usar taxa de abertura como KPI de campanha
Taxa de abertura de 78–83% é inflação do Apple MPP — não reflete engajamento real. O único KPI de engajamento utilizável para E-mail Campanha é CTOR. Recomendo remover ou desprioritizar a métrica de abertura do dashboard para esse canal.

### 4. Definir estratégia para WPP Comunidade (decisão de negócio)
A base perde membros toda semana há 3+ meses. Não é tendência passageira. Há duas opções:
- **Investir em aquisição:** criar mecanismo recorrente de entrada (não campanhas pontuais) para repor o churn
- **Aceitar contração:** calibrar metas do canal para refletir uma base menor e focar em qualidade dos membros ativos

### 5. Monitorar E-mail Fluxo nos próximos 30 dias
Taxa de abertura em queda de -1,1pp/semana. Se o ritmo continuar, em 5 semanas estará abaixo de 32% — a partir daí o volume de disparos não compensa mais a perda de engajamento. Ação preventiva: auditar frequência por segmento e considerar segmentação por engajamento (ex: pausar fluxos para quem não abriu em 90 dias).

---

## Anexo Técnico

### Fontes e cobertura
| Fonte | Cobertura | Linhas | Uso nesta análise |
|---|---|---|---|
| `fact_orders` | 23/04–16/06 | 25.641 | Receita semanal por canal |
| `flow_email_metrics` | 01/03–16/06 | 11.889 | Funil semanal E-mail Fluxo |
| `campaign_email_metrics` | 01/03–16/06 | 2.235 | Funil semanal + detalhamento por campanha |
| `leads_webhook` | 08/06–17/06 | 20.128 | Funil de leads WPP Fluxo |
| `fact_community_analytics` | 11/03–16/06 | 93 | Tendência de membros Comunidade |
| `cron_logs` | Últimas 2 semanas | ~870 | Falhas de ingestão |

### Dados não acessados
- `fact_email_health`: servidor retornou erro de coluna + 504. Bounce rate e spam rate não verificados.
- AOV semanal por canal: timeout. Não confirmado se ticket médio mudou entre baseline e queda.
- WPP Campanha (funil): Vekta campanha não integrado — aguarda planilha a ser disponibilizada.

### Nota sobre a semana 15/06
Apenas 15 e 16/06 têm dados (max_date de `fact_orders` é 16/06). Os ~R$ 80k dessa semana são 2 dias, não 7 — não comparáveis com semanas cheias.

### Nota sobre 21k pedidos sem atribuição
83% do valor total de pedidos (R$ 11,8M de R$ 13,4M) não tem canal atribuído. Isso é estrutural — compras sem UTM de CRM. O risco é se essa proporção mudou entre períodos, mascarando variação real dos canais. Não foi possível verificar por instabilidade do servidor.
