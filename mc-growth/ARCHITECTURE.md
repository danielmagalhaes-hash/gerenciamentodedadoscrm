# ARCHITECTURE.md

> Mapa vivo do sistema. Lido em TODA sessão. Atualizado ao FIM de toda sessão.
>
> **Criado em 2026-07-01** (Fase 1). Estado: **v1 construída e verificada** — Streamlit lendo uma planilha única. Os três módulos (`dados.py`, `cascata.py`, `painel.py`) existem, rodam e passam nos critérios de aceite testáveis.
>
> **V2 construída e verificada (2026-07-09)** — a **aba de aquisição** (`pages/2_Aquisicao.py`) mostra a MC de clientes novos (MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS) partindo os pedidos pelo carimbo nativo `Vendas.customer_type`. Reusa o `_recorte_pedidos` do painel (as faixas amarram com o total) e desconta a mídia INTEIRA (convenção 100% mídia → novos). O painel de MC da V1 **não muda**. Spec: `docs/specs/2026-07-09-v2-aba-aquisicao.md`. Junho/2026 (verificado ao vivo): MC-novos +R$237.855, CAC R$189,72, aROAS 2,74.
>
> **V4 CONSTRUÍDA e verificada (2026-07-10, tarde).** A **aba de coortes de recompra** existe e roda — `pages/3_Coortes.py` + `coortes.calcular_coortes` + `dados.carregar_hubspot` lendo o **arquivo local** `bases/hubspot_deals.csv` (462k deals do HubSpot). Fonte de cliente = HubSpot (chave `e_mail`), coorte por **mês da 1ª compra** (cross-canal); MC **acumulada por cliente** (mídia inteira no m+0 = CAC); triângulo + curva (últimas 12 safras, linha do zero, safra em destaque) + seletor; recompra em 90 dias; safra fechada. **MVP = Opção 2:** MC de produto **real** só onde o pedido casa com a `Vendas`/`Itens` da janela atual (abr–jul/2026; ponte `hubspot.nome → Vendas.order_name → order_id → Itens`, reusando `cascata.cmv_por_pedido` — **a mesma receita de custo do painel**), **estimada em 0,25×valor** fora dela (célula a célula marcada real/estimada; 92,5% estimada no MVP). Rótulo honesto **"MC parcial"**. **Amarração provada:** por pedido, a MC real da coorte é **idêntica** ao Lucro Bruto do painel/Auditoria (max |dif| = 0). V1 (painel) e V2 (aquisição) **intocadas** (CMV byte-idêntico antes/depois do refactor). **Achado que contraria a spec:** o campo `meses_desde_primeira_compra` do HubSpot **NÃO é a idade do deal** — é a idade do CLIENTE no export (constante em todos os deals dele); a idade da coorte (m+0, m+1…) é **calculada** da diferença em meses-calendário entre `data_de_fechamento` e a 1ª compra (ver §6). Spec: `docs/specs/2026-07-10-v4-coortes-recompra.md`; ADRs `2026-07-10-v4-arquitetura-mvp-coortes` e `2026-07-10-v4-coortes-recompra-hubspot`; logs `docs/sessions/2026-07-10-spec-v4-coortes.md` (spec) e `docs/sessions/2026-07-10-construcao-v4-coortes.md` (build).

> **FONTE DE CUSTO 3.2 (2026-07-22).** O Financeiro entregou uma tabela de custo por SKU
> atualizada ("PREÇO JUNHO"); o João a subiu na **aba nova "3.2. Custos"** (gid `634911340`)
> da planilha. A esteira de custo virou uma **cascata de 3 abas** (`dados.FONTES_CUSTO`): **3.2**
> (principal) → 3.1 → 3, com o `custos_extra.csv` por cima (regra igual à de sempre, só ganhou
> uma camada no topo). **Só `dados.py` mudou** (`carregar_custos` percorre a lista; `GIDS["Custos"]`
> e `GID_CUSTOS_FALLBACK` saíram — a lista é o único dono dos gids de custo). **Cobertura sobe**
> (SKUs com custo 1.617 → 1.684, +67; **0 perderam custo**). **Junho/2026: MC R$ 2.173.703,35 →
> R$ 2.255.165,93** (+R$ 81.462,58 / +3,75%; CMV cai o mesmo — a 3.2 tem custos menores em várias
> famílias). Guarda **7/7** e `AppTest` das 7 telas OK depois da troca.
> Spec `docs/specs/2026-07-22-fonte-custos-3-2.md`; ADR `2026-07-22-fonte-custos-3-2`; log
> `docs/sessions/2026-07-22-fonte-custos-3-2.md`.
>
> **PERCENTUAIS DA DRE ATUALIZADOS (2026-07-22, mesma sessão).** O Financeiro também passou
> percentuais novos → `cascata.PARAMETROS`: PIS/COFINS 1,75→**4,74**, ICMS 12,54→**13,73**,
> Devoluções 3,48→**3,32**, Frete 4,80→**5,02**, Gateways 1,70→**1,37**, Plataforma 0,90→**0,44**,
> Antecipação 1,60→**1,10** (Chargebacks 0,15 igual). **Embalagem (0,57) e Outras Deduções (0,00)
> não vieram na lista → mantidas** (Embalagem 0,57 CONFIRMADA pelo João). Soma deduções+custos
> **27,49% → 30,44%** (+2,95 pts; margem de produto estimada 42,5%→39,56%). **Junto com a base
> de custo 3.2, a MC de junho fica R$ 2.010.121,79** (base 3.1+% antigos era 2.173.703,35 →
> líquido −7,5%: o custo novo soma +81k, os % novos tiram ~245k). **Nova âncora de junho =
> R$ 2.010.121,79.** Guarda 7/7 + AppTest OK. Spec `docs/specs/2026-07-22-parametros-dre.md`.
>
> **COMBINAÇÕES VIRAM PORTAS (2026-07-16).** Decisão do João: uma **combinação de linhas (≥2)**
> vira **porta de entrada própria** quando tem **≥ 1.000 clientes de estreia** (`LIMIAR_COMBO_PORTA`
> em `portas.py`); abaixo disso segue "Multiprodutos" (a cauda). Vale em **todo o painel** (muda a
> coluna `porta`): as **6 combinações** promovidas (maior: *Calça Jeans 1.0 + Camiseta Minimal*,
> 4.058) aparecem como linhas na **aba 4** (por safra/por linha, Lucro Bruto e Receita) e como portas
> na **A3**. Re-partição **limpa**: Multiprodutos 30.632 → **14.546**; *Produto desconhecido* (21.713)
> e *Camiseta Minimal* (193.616) **inalterados**; total preservado. Guarda **7/7** (partição 0/64 +
> "todos" = Cohorts ao centavo). Classificação refatorada: `_combo_por_pedido` + `_porta_do_combo` +
> `_combos_promovidos` (data-driven, sem lista curada). ADR `2026-07-16-combinacoes-viram-portas`;
> log `docs/sessions/2026-07-16-a3-auditoria-portas.md`.
>
> **A3 — MULTIPRODUTOS POR COMBINAÇÃO (2026-07-16).** Os 30.632 clientes de "Multiprodutos" não
> se olham um a um → quando essa porta é escolhida, a A3 mostra primeiro uma **tabela de
> combinações de linha da estreia** (`combinação | nº linhas | clientes | ticket médio 1ª | valor
> total`), ranqueada por nº de clientes; **clicar numa combinação** filtra a lista de clientes (aí
> pequena) e daí o drill-down por cliente. `auditar_portas` ganhou a coluna **`combo`** nas estreias
> (conjunto de linhas `porta` do pedido, reusando os `itens` já lidos). **Fato revelado:** só **1.361
> combinações distintas** (81% são pares) e a **Camiseta Minimal está em 84%** das estreias Multi; top
> combo "Calça Jeans 1.0 + Camiseta Minimal" = 4.058 (ticket R$ 745). Decisão do João: "Combinações +
> clicar pra abrir". Guarda 7/7; `AppTest` sobe a A3 com Multiprodutos sem exceção; fluxo combo→lista→
> timeline exercitado. Backlog: mesma agregação para "desconhecido" (por SKU não mapeado).
>
> **A3 — AUDITORIA DAS PORTAS (drill-down por cliente) (2026-07-16).** Aba de anexo nova
> **"A3 - Auditoria Portas"** (`views/auditoria_portas.py` + `portas.auditar_portas`): escolhe uma
> porta → lista os clientes dela (1 linha/cliente, estilo A1) → **clica num cliente e abre a linha
> do tempo de compras** (produtos de cada compra + o período m+x). Foco em **Multiprodutos** e
> **Produto desconhecido** (garimpar oportunidade: SKU não mapeado, lacuna de dado, classificação
> errada). **Nenhuma verdade nova de dinheiro** — reusa a coluna `porta` de `calcular_portas`; a
> única régua nova é o **MOTIVO** do desconhecido (4 baldes: Comercial 1.801 · fora da base 1.912 ·
> **sem itens casados 11.721** · só brinde/sem-nome 6.279 — os dois últimos são os *recuperáveis*).
> **Privacidade:** nunca mostra e-mail; no Comercial o `nome` é a PESSOA → mascarado "(Comercial)".
> **Trava §11:** o drill-down **não** casa itens de deal não-`Shipped` (a numeração do Comercial
> colide → traria itens de OUTRO pedido) — igual ao CMV. Partição dos clientes intacta (CA4, reusa o
> check nº 6); `AppTest` sobe a A3 sem exceção. Spec `docs/specs/2026-07-16-auditoria-portas-drilldown.md`;
> log `docs/sessions/2026-07-16-a3-auditoria-portas.md`.
>
> **PORTAS DE ENTRADA — MÉTRICA RECEITA (2026-07-16).** A aba "4. Portas de entrada" ganhou um
> **seletor de métrica** (Lucro Bruto × Receita) que troca o conteúdo das mesmas duas tabelas —
> decisão de layout do João (troca, não empilha 4 tabelas). O motor (`portas.py`) passou a aceitar
> **`metrica`** (default `"mc_produto"` = LB; `"valor"` = Receita bruta) nas 4 builders — **nenhuma
> conta nova**, só troca a coluna somada; a Receita não desconta mídia nem custo. **Provado:**
> `portas("todos")` com `metrica="valor"` = `coortes.ltv` (o LTV da Cohorts) ao centavo (dif 0,0 nas
> 64 safras), a par do Lucro Bruto = `coortes.lucro_bruto` — o **check nº 6** agora prova as duas.
> `AppTest` sobe a aba nos 2 modos. Log `docs/sessions/2026-07-16-portas-metrica-receita.md`.
>
> **PORTAS DE ENTRADA — CONSTRUÍDA e verificada (2026-07-15, 3ª sessão).** A aba **"4. Portas de
> entrada"** existe e roda — `views/portas_entrada.py` + o motor novo **`portas.py`** (reusa
> `coortes.py`) + `dados.carregar_mapa_portas`. Segmenta a coorte pela **linha de produto da
> estreia** do cliente e mostra o **Lucro Bruto acumulado por cliente** (célula = `coortes.lucro_bruto`;
> CAC = blended do mês) em `1ª compra | 30D | 60D | 90D | 180D | 365D` (apelidos de m+0/m+1/m+2/m+5/m+11).
> Duas tabelas: **por safra** (filtro de produto; "todos" = idêntica à Cohorts) e **por linha**
> (filtro de data; cada janela usa só as safras maduras). **NADA de verdade nova de custo/CAC** — só
> a dimensão `porta`. **Provado:** `portas("todos")` = `coortes.lucro_bruto` **ao centavo** (dif 0,0
> nas 64 safras) e as portas **particionam** os clientes (0/64 safras perdem gente) → virou o **check
> nº 6 do `checar_coerencia.py`** (7/7 passam). `AppTest` sobe as **6 telas** sem exceção.
> **Detalhe em aberto RESOLVIDO** (decisão do João): o item "sem nome" é **ruído** (removido como
> brinde) → `camiseta + sem-nome = "Camiseta"`, não "Multiprodutos" (impacto medido: 6.727 estreias,
> **2,47%**). Porta = linha única (após tirar brinde/sem-nome); >1 → "Multiprodutos"; 0 (só ruído/
> Comercial/cross-canal/pré-out-2021) → "Produto desconhecido". Régua **Lucro Bruto PARCIAL** (rotulada).
> ADR `2026-07-15-portas-de-entrada-produto`; spec `2026-07-15-portas-de-entrada-produto`; log
> `docs/sessions/2026-07-15-construcao-portas-de-entrada.md`. Ver o módulo `calculo-portas` (§2) abaixo.
>
> **DISCOVERY "PORTAS DE ENTRADA" — spec + mapa de produtos (2026-07-15, 2ª sessão).** Discovery de uma
> feature nova (aba "4. Portas de entrada"): ler o **Lucro Bruto acumulado por cliente por PORTA DE ENTRADA**
> (produto da 1ª compra) em janelas `1ª compra | 30D | 60D | 90D | 180D | 365D` (**mesma régua da Cohorts** —
> os "D" são apelidos dos meses m+0/m+1/m+2/m+5/m+11, nenhum ADR de divergência), pra definir CAC-teto/ROAS-alvo
> por porta. **Só spec + artefato de dados nesta sessão; build na próxima.** O Fable (subagente) verificou o
> dado e cortou **canal e oferta** da 1ª leva (não existem colunas na base → backlog). Nasceu a régua nova
> **`bases/mapa_sku_linha_produto.csv`** (SKU → linha de produto, papel porta/brinde/desconhecido; validada
> à mão pelo João: 26 linhas-porta). Spec `docs/specs/2026-07-15-portas-de-entrada-produto.md`; backlog novo
> `docs/BACKLOG.md`; log `docs/sessions/2026-07-15-portas-de-entrada.md`. Ressalva: a régua segue **Lucro
> Bruto parcial** (sem devolução/CX/juros/criativo — devolução por produto é o custo que mais difere entre
> portas). Ver o §3 (`bases/mapa_sku_linha_produto.csv`) abaixo.
>
> **HIGIENE DE DOCS — alinhamento a montante (2026-07-15).** Sessão só de documentação (nenhum
> código tocado). Corrigidos os **docs vivos** que ficaram para trás depois do trabalho de 14/07:
> (1) `PRODUCT.md` — a idade da coorte é **calculada**, não vem do campo `meses_desde_primeira_compra`
> (§4/Fluxo A); a receita é o **`valor`** (decidido, não "a confirmar"); o §8 deixou de dizer "CMV real
> só abr–jul/2026" e agora reflete o CMV real out/2021→hoje em 3 camadas. (2) Este `ARCHITECTURE.md` —
> a descrição viva do módulo `coortes` (§2) e o ponto frágil da idade (§6) trocaram `0,25×valor`/"só na
> janela" pela realidade de hoje (`0,30`, 3 camadas). **O que NÃO foi tocado (de propósito):** as
> **fotos datadas** (o bloco "V4 CONSTRUÍDA 2026-07-10" abaixo, a tabela de decisões §5 e o ponto
> frágil §6 "planilha estreita/Opção 1 resíduo") — são registro histórico, como as specs; leem-se com
> a data. **Descoberta registrada:** a "Opção 1" (MC real ano-a-ano desde 2022) **já foi entregue** pelo
> CMV real histórico de 14/07 — não é mais pendência. Log `docs/sessions/2026-07-15-higiene-docs-montante.md`.
>
> **CMV REAL NA HISTÓRIA INTEIRA — itens em 3 camadas (2026-07-14, 3ª sessão).** O CMV deixou de
> ser chutado em 30% no passado. Fonte nova: **`bases/itens_historico.csv`** (arquivo local, export
> do BigQuery da mesma tabela silver da aba `Itens`, só que **a história toda** — 1,3 M linhas,
> 2021-10 → 2026-07-14, 495 mil pedidos). Os itens de um pedido são resolvidos em **3 camadas**
> (`cascata.itens_por_nome`): **1ª** a base histórica → **2ª** a aba `Itens` da planilha (só os
> pedidos recentes demais para o export, que é uma **foto**) → **3ª** nada = **CMV 30%** (regra de
> sempre). A ponte é **direta** pelo número do pedido (`HubSpot.nome == itens.order_name`, os dois
> com `lstrip("#")`) — a volta pela `Vendas` (`order_name→order_id→Itens`) **sobrevive só na 2ª
> camada** (a aba `Itens` não tem a coluna `name`). **Byte-identidade provada:** o CMV por pedido
> das duas fontes é idêntico **ao centavo** nos 39.212 pedidos da janela (max |dif| = R$ 0,000000);
> junho/2026 não mudou (MC **R$ 2.173.703,35**). **TRAVA DE DINHEIRO:** só deal **`Shipped`** casa
> itens (`cascata.pode_casar_itens`) — o `Comercial` grava no `nome` um número de **outra
> numeração que COLIDE** com pedidos Shopify antigos (mediana **92 dias** de defasagem; 37 deals de
> junho casariam com itens de janeiro). Impacto: **MC de 2022 cai 24,4%** (CMV real do ano = 35,8%,
> não 30%), 2023/2024 quase não mudam, **2025 sobe 1,4%**. Arquivo ausente = **degrada** para o
> comportamento anterior (provado). ADR `2026-07-14-cmv-real-historico-3-camadas`.
>
> **RÉGUA ÚNICA DE "CLIENTE NOVO" = o carimbo do HubSpot (2026-07-14).** `cascata.mascara_cliente_novo`
> — novo = deal com **`tipo_de_venda = "Primeira Compra"`**. Vale nos DOIS lados: aba **Aquisição** e
> **bloco de novos da coorte** (A2 + a coluna "MC primeira compra"), que antes derivava a 1ª compra
> por conta própria. Decisão do João: espelhar a definição da FONTE. **Ressalva medida e aceita:** o
> carimbo erra nas bordas (em junho, 59 primeiras compras marcadas "Recompra" e 62 "Primeira Compra"
> que não eram o 1º pedido do cliente — ~R$ 10,8 mil, 0,25%). **Resíduo Aquisição × A2: R$ 3.628
> (0,08%)** — a coorte só conta quem **estreou** no mês; a Aquisição conta todo pedido carimbado
> **com data** no mês (período × turma; inerente, não é bug). **Junto:** a coorte passou a aplicar as
> **exclusões AnjosFrach** (ADR 2026-07-02) que só o painel aplicava. ADR
> `2026-07-14-regua-unica-cliente-novo`.
>
> **LEITOR BLINDADO (2026-07-14).** O Google devolve às vezes **HTTP 200 + `text/csv` com a planilha
> VAZIA** (só vírgulas, sem cabeçalho; 840 KB no lugar de 3,5 MB) — observado **3× num dia**. O
> `content-type` está certo e o pandas lê, então a guarda antiga não pegava: virava o erro confuso
> "a aba Vendas está sem a coluna `order_id`". `dados._ler_csv` agora trata "todas as colunas
> `Unnamed:`" como engasgo e **tenta de novo** (3×, espera crescente).
>
> **TELAS DE COORTE (2026-07-14, 3ª rodada).** A aba **3. Cohorts** perdeu a **curva de payback**
> (saiu a pedido do João) e ganhou **três tabelas**: (1) **Receita por cohort** — `Cohort | Novos
> Clientes | CAC | Receita 1ª Compra | LTV m+0…`, onde **Receita 1ª Compra** = valor médio do 1º
> pedido e **LTV m+x** = receita acumulada ÷ cliente (bruta, antes de qualquer custo); (2) o
> **triângulo de MC por cliente**, agora com "Safra"→**"Cohort"** e uma coluna nova **MC primeira
> compra** (margem do 1º pedido **já com a mídia** = m+0 sem as recompras do mês de entrada);
> (3) o **mesmo triângulo em reais cheios** (**MC absoluta** da turma). A **auditoria por safra**
> saiu da aba e virou a página **A2 - Auditoria MC Cohort** (`views/auditoria_cohort.py`). Peças
> comuns às duas telas em **`coortes_ui.py`** (formatação + cache de leitura). `ResultadoCoortes`
> ganhou `ltv`, `mc_absoluta`, `ticket_primeira_compra`, `mc_primeira_compra`. Provado: MC absoluta
> ÷ clientes = MC/cliente (dif 0) e a reconciliação da A2 segue exata nas 63 safras.
>
> **O RATIO CONTRA O CAC USA LUCRO BRUTO, NÃO MC (2026-07-14, correção do João).** A 1ª versão da
> tabela de ratio dividia a **MC** pelo CAC — e a **MC já tem a mídia descontada** (`coortes.py`: o
> Ad Spend sai **uma vez**, no m+0, e o acumulado o carrega adiante). Isso contava a **mídia duas
> vezes**: subtraída no numerador e de novo no denominador. O numerador certo é o **Lucro Bruto
> acumulado por cliente** (antes da mídia) → `ResultadoCoortes.lucro_bruto` +
> `lucro_bruto_primeira_compra`, tirados do incremental **ainda cru** (não somando o CAC de volta
> na tela — dinheiro tem um dono só). **A régua muda: o empate passa de `0,00×` para `1,00×`** (a
> turma devolveu o que custou trazê-la); abaixo de 1,00× = não pagou a própria mídia (número em
> vermelho — `verde_gradiente` ganhou o parâmetro `limiar`). **Provado:** `lucro_bruto =
> mc_acumulada + CAC` com dif **0,0000000000** nas 64 safras (virou o **check nº 5 do
> `checar_coerencia.py`**), e a linha do `1,00×` **coincide com o payback** do triângulo de MC (0
> células divergentes). Ex.: safra 2026-06 (CAC R$ 173,65) — o ratio velho dizia 0,40×; o certo é
> **1,40×**.
>
> **RATIOS SOBRE O CAC na aba Cohorts (2026-07-14, 4ª rodada).** A aba **3. Cohorts** ganhou **dois
> títulos de seção** (*"LTV e CAC por Cohort (Receita)"* e *"LTV MC e CAC por cohort (Margem de
> contribuição)"*) e **duas tabelas novas**, cada uma logo abaixo/entre as que já existiam:
> **LTV ÷ CAC** (múltiplo em **receita bruta** — o clássico LTV:CAC) e **MC por cliente ÷ CAC**
> (múltiplo **líquido**: a MC já vem com a mídia descontada, então **`0,00×` = a turma empatou** =
> o payback; negativo = ainda não pagou a mídia). **Nenhum número novo é calculado** — as duas
> tabelas dividem `ltv`/`mc_acumulada`/`ticket_primeira_compra`/`mc_primeira_compra` pelo `cac` do
> `ResultadoCoortes`. `coortes.py` e `cascata.py` **não foram tocados** (o diff só ADICIONA; as 3
> tabelas antigas são byte-idênticas). **Cor (decisão do João):** gradiente de **verde** (mais
> escuro = múltiplo maior) via `coortes_ui.verde_gradiente`; **abaixo de zero o fundo fica branco e
> o número vermelho** — um verde clarinho não avisaria que a turma está no vermelho, e a linha do
> zero do triângulo precisa sobreviver na tabela de ratio. CAC ausente/zero → **"—"** (nunca
> divide). Spec `docs/specs/2026-07-14-coortes-titulos-e-ratios.md`.
>
> **MENU, CASCATA E CMV ESTIMADO (2026-07-14, 2ª sessão).** Três padronizações + uma regra de
> dinheiro. (1) **Menu programável:** `painel.py` virou **roteador** (`st.navigation`); as telas
> moram em **`views/`** (a pasta `pages/` deixou de existir). Ordem/nomes: **1. Geral · 2. Aquisição
> · 3. Cohorts · A1 - Auditoria Custos**. (2) **Cascata única:** o DRE era remontado à mão em **6
> lugares** — agora sai todo de **`cascata.montar_cascata`** (números) + **`ui.tabela_dre`** (cores),
> no formato `Vendas → (−) Deduções [5] → (−) Cost of Delivery [CMV + 5] → (=) Lucro Bruto → (−)
> Mídia Paga → (=) MC`. Os subtotais de grupo são **apresentação** (somam linhas que já existem).
> (3) **Aquisição:** 6 cartões (Vendas novos · Ad Spend · aROAS Shopify · **Ticket Médio** (novo) ·
> nº Pedidos · CAC); a MC-novos só como herói. (4) **CMV estimado = 30% da receita** onde não há
> itens (antes: "margem de 25%"), com as deduções incidindo normalmente → margem de produto
> estimada de **42,5%** (o real medido é ~43%). Junho/2026: R$ 2.152.168 → **R$ 2.173.703** (+1,0%,
> só a fatia do Comercial). ADR `2026-07-14-cmv-estimado-30-por-cento`; spec
> `2026-07-14-interface-menu-cascata-cmv-30`.

---

## 1. Visão geral em 1 página

O MC Growth v1 é um **painel local** (roda no computador do João) escrito em **Python + Streamlit** que lê uma **única planilha Google** (com 5 abas) e monta a cascata de Margem de Contribuição da Minimal Club (canal Shopify).

A ideia central é ter **uma só porta de entrada de dados**: em vez de o painel conversar com Shopify, BigQuery e planilha de custo (três "idiomas" diferentes), o João consolida tudo numa planilha única (via IMPORTRANGE e exports do BigQuery), e o painel só precisa saber ler essa planilha. O painel a lê **ao vivo** (via URL de export CSV de cada aba), calcula a cascata com a biblioteca *pandas* e desenha a tela com o Streamlit (número-herói da MC, 5 cartões, tabela tipo DRE e um filtro de período).

Não há banco de dados, não há login, não há servidor. As "tabelas" do sistema são as abas da planilha.

> **Escrita:** o painel **nunca escreve na planilha compartilhada**. A única escrita é num arquivo **local** do João, `custos_extra.csv`, com correções de custo feitas na própria tela (ADR 2026-07-02-editor-custos-arquivo-local), aplicadas por cima da base ao ler.

---

## 2. Diagrama de módulos

### Lista de módulos

#### planilha-contrato (fonte de dados)
- **Responsabilidade:** entregar os dados nas 5 abas com colunas de nome fixo.
- **Depende de:** Shopify (Base 1 e base silver de itens), tabela de custo, BigQuery (mídia) — consolidados pelo João.
- **Quem depende:** carregador-de-dados.
- **Estado:** verificada em 2026-07-01 (4 abas de dados OK; sem aba `Parametros` — ver 3.0).

#### carregador-de-dados (`dados.py`)
- **Responsabilidade:** ler cada aba da planilha ao vivo e devolver tabelas limpas (datas e números normalizados). Devolve um `Dados` (dataclass com as 4 abas). Erros viram `ErroDeDados` com mensagem pronta pro João.
- **Depende de:** planilha-contrato; `certifi` (contexto SSL — ver nota abaixo).
- **Quem depende:** calculo-cascata, painel-ui.
- **Estado:** **construído e verificado (2026-07-01; +`customer_type` na Vendas em 2026-07-09; +`carregar_hubspot` e +`investimento_total` na Midia em 2026-07-10).** As 4 abas leem sem erro (0 datas/números inválidos); decimal misto (34.5 e 83,75) OK; 1 linha por pedido confirmado. `carregar_vendas` passou a exigir e mapear `Vendas.customer_type` (V2) — se a coluna sumir, a leitura falha com erro claro (decisão: barulhento > silencioso).
- **[V4] `carregar_hubspot()` (2026-07-10):** lê o **arquivo local** `bases/hubspot_deals.csv` (não a planilha) e devolve os deals limpos (e_mail minúsculo; `nome` sem o `#`; datas em **ISO** `AAAA-MM-DD` via `_para_data_iso`, ≠ do DD/MM/AAAA da planilha; `safra` = mês da 1ª compra). Descarta linhas sem e_mail/1ª-compra. Arquivo ausente/coluna faltando = `ErroDeDados`. Só a aba de coortes o lê — **V1/V2 não dependem dele** (ausência não derruba as outras abas). `carregar_midia` ganhou `investimento_total` (opcional; NaN se a aba antiga for lida).

#### calculo-cascata (`cascata.py`)
- **Responsabilidade:** aplicar as regras (R1..R12 do spec / seção 6 do PRODUCT.md) e produzir a cascata (`LinhaDRE`) + os 5 cartões + alertas para um período, num `Resultado` (dataclass).
- **Depende de:** carregador-de-dados. Os 10 percentuais estão na constante `PARAMETROS` (aba `Parametros` ainda não existe).
- **Quem depende:** painel-ui, aquisicao-ui.
- **Estado:** **construído e verificado (2026-07-01).** Aritmética da cascata confere (Vendas − deduções − CMV = Lucro Bruto; LB − mídia = MC). Casos-limite OK (vazio, sem mídia, mudança de %).
- **[V2] `calcular_aquisicao` (2026-07-09; régua trocada 2026-07-14):** função nova (não altera `calcular`). Reusa `_recorte_pedidos`, devolve `ResultadoAquisicao` (5 KPIs de novos + mini-cascata + amarração + alertas). Mídia INTEIRA. **[2026-07-14]** "novo" passou do carimbo Shopify (`customer_type`) para o **`tipo_de_venda` do HubSpot** (1ª compra na Minimal, cross-canal — bate com o filtro direto da base; unifica com a coorte) via ponte `order_name→nome`; pedido sem deal casado → fallback `customer_type`; sem `deals` → volta ao carimbo (degrada). Junho Vendas-novos 3,90M→4,24M (resíduo vs base ~2,7% = net vs valor + borda de data).
- **[V4] `juntar_custos` + `cmv_por_pedido` (2026-07-10):** refactor de extração — a **única receita de custo** do projeto (junção Itens×Custos → `sem_custo`, `custo_linha`; CMV = Σ `custo_linha`). `calcular`, `calcular_aquisicao`, `detalhar_pedidos` (Auditoria) e a coorte (V4) saem toda daqui → nunca discordam sobre o custo de um pedido. **Verificado byte-idêntico** antes/depois (painel e V2), e `cmv_por_pedido` amarra com o painel.
- **[unificação HubSpot 2026-07-14] `calcular`/`calcular_aquisicao` viram DEALS-BASED com `deals=`:** o painel geral e a aquisição passam a ler os **deals do HubSpot** — **Vendas = Σ`valor`** por **`data_de_fechamento`**, **CMV REAL via ponte** (`nome→order_name→order_id→Itens→Custos`, `_cascata_de_deals`) na janela de itens, **25%** fora. **Bate com o filtro direto da base** (aquisição-novos ao centavo). Deduções na parte casada; parte não-casada (Comercial + histórico) estimada 25%. **Sem `deals` (CSV ausente) → fallback ao motor antigo (planilha/`net_revenue`).** Rótulo `real`/`estimada`/`mista`. **Consequência:** os números mudam vs o net antigo (junho painel MC 2,05M→**2,15M**, +4,8%: `valor` inclui frete + entra o Comercial); a MC vira `valor`-based. **CMV segue item a item** (preservado — condição do João). ADR `2026-07-14-rebase-geral-aquisicao-hubspot` §5-bis. *(O roteador "borda da janela" e `_deals_estimados` ficaram como caminho morto p/ `deals=None`.)*

- **[fábrica de cascata + CMV 30% — 2026-07-14, 2ª sessão] `montar_cascata`:** a **única** função que monta o DRE (`Vendas → Deduções → Cost of Delivery → Lucro Bruto → Mídia → MC`). Os 6 lugares que remontavam a cascata à mão (4 aqui, 2 em `coortes.py`) passaram a chamá-la. Junto veio a regra nova: onde o pedido **não tem itens**, `CMV = 30% × receita` (`CMV_ESTIMADO_FRACAO`) e as **deduções/custos % incidem sobre a receita inteira** — a linha "Margem estimada (25%)" **deixou de existir** (o CMV é que leva o ⚠️). `_deals_estimados` (roteador da borda) virou código morto e foi **removido**. ADR `2026-07-14-cmv-estimado-30-por-cento`.

#### calculo-coortes (`coortes.py`) — V4
- **Responsabilidade:** montar o triângulo de coortes (safra × idade → **MC acumulada por cliente**) a partir dos deals do HubSpot + das abas do painel. Produz `ResultadoCoortes` (triângulo, flag real/estimada por célula, N_S, CAC, payback, MC/cliente até hoje, recompra 90d por safra, avisos). Toca dinheiro.
- **Depende de:** `dados.carregar_hubspot` (deals) + `dados.Dados` (Vendas/Itens/Custos/Midia) + `cascata.cmv_por_pedido`/`_recorte_pedidos` (CMV real da janela) + `cascata.PARAMETROS`/`IMPOSTO_FB_ADS`.
- **Quem depende:** coortes-ui.
- **Regras-chave:** safra e idade ancoradas na **1ª compra real do cliente** (mínimo por `e_mail` — um cliente = uma safra; corrige a deriva do HubSpot); **idade calculada** da diferença de meses-calendário (NÃO usa `meses_desde_primeira_compra` — ver §6); **receita = `valor`** em ambos os ramos (unificação 2026-07-14); MC real = `valor − deduções − CMV item a item` (CMV das **3 camadas**: base histórica `itens_historico.csv` → planilha → **30%** onde não há itens), senão o estimado é `0,30×valor`; mídia (com imposto FB só ≥2026-01) no m+0 = CAC; só **safras fechadas**. O enriquecimento por deal está em **`_preparar_deals`** (compartilhado por `calcular_coortes` e `detalhar_safra` — uma só verdade). As três telas (painel, aquisição, coorte) usam a **mesma régua** (valor + fechamento + CMV real na janela).
- **[V4] `detalhar_safra` (2026-07-12):** abre a cascata de UMA safra (`DetalheSafra`: cascata total + por idade + deals p/ export), **re-expondo a mesma `mc_produto`** (não recalcula). A MC/cliente da cascata **reconcilia** com `mc_ate_hoje` do triângulo nas 64 safras (exato). Deduções só sobre a receita **real**; o estimado é 0,30×valor direto.
- **Estado:** **construído e verificado (2026-07-10; auditoria 2026-07-12).** Amarração por pedido com o painel (max |dif| = 0); ΣN_S = clientes distintos; reconciliação cascata↔triângulo nas 64 safras; CA1–CA13 (coortes) + CA1–CA6 (auditoria) conferidos; `AppTest` sobe sem exceção. **[atualizado 2026-07-14]** a fração estimada era 92,5% no MVP (janela ~4 meses); com a base histórica de itens (`itens_historico.csv`, out/2021→hoje) o CMV real passou a cobrir quase toda a história e a estimativa (30%) sobrou só onde não há itens (pré-out/2021, Comercial, SKU sem custo) — marcado célula a célula.

#### calculo-portas (`portas.py`) — 2026-07-15
- **Responsabilidade:** segmentar a coorte pela **porta de entrada** (linha de produto da 1ª compra do cliente) e produzir o **Lucro Bruto acumulado por cliente** por porta. Devolve `ResultadoPortas` (deals enriquecidos + coluna `porta`, safras, CAC blended, lista de portas por tamanho) + duas builders de tabela (`tabela_por_safra`, `tabela_por_linha`).
- **Depende de:** `coortes.calcular_coortes` (CAC blended + o anchor `lucro_bruto`) + `coortes.preparar_deals_cache` (deals enriquecidos — a MESMA verdade de custo) + `cascata.itens_por_nome`/`mascara_cliente_novo`/`pode_casar_itens` + `dados.carregar_mapa_portas`.
- **Quem depende:** portas-ui.
- **Regra-chave (a ÚNICA coisa nova): `porta` por cliente.** Estreia = o deal **mais antigo** do cliente; ponte `nome → itens (3 camadas) → SKU → mapa → linha`. **Brinde E "sem nome" removidos como ruído** (decisão João 2026-07-15) → sobra 1 linha = essa porta; ≥2 linhas = a **combinação** (`_combo_por_pedido` → "A + B"); 0 = "Produto desconhecido". Travas de dinheiro iguais às do CMV: só **`Shipped`** casa itens (Comercial → desconhecido) e estreia **idade 0** (senão a 1ª compra é fora da base → desconhecido; viés cross-canal). `_triangulo_lb` **espelha** `coortes.lucro_bruto` num subconjunto → para "todos" reproduz a Cohorts ao centavo. CAC = **blended** (nunca por produto). Não recalcula dinheiro.
- **[2026-07-16] Combinações viram portas (`_porta_do_combo` + `_combos_promovidos`).** Uma combinação (≥2 linhas) com **≥ `LIMIAR_COMBO_PORTA` (1.000) clientes de estreia** vira porta própria (nome = "A + B"); abaixo, fica "Multiprodutos" (a cauda). Limiar **global** (porta estável entre recortes). Hoje 6 combinações promovidas. `_porta_por_pedido` foi substituída por `_combo_por_pedido` (order_name → "A + B"); `calcular_portas` monta `promovidos` 1× e passa a `_porta_por_cliente`. Re-partição limpa (só as 6 combinações trocam de balde; desconhecido/linhas únicas inalterados). ADR `2026-07-16-combinacoes-viram-portas`.
- **[2026-07-16] Escolha da estreia (`_estreias`) — desempate por "tem produto".** A estreia é o deal mais antigo; **no empate de data** (0,9% dos clientes têm >1 pedido no mesmo dia), **prefere o pedido que TEM linha `porta`** ao que não tem (antes: só alfabético pelo número) — senão um cliente com um pedido-sem-itens no mesmo dia da compra "real" caía em "desconhecido" (caso #14461). Helper único usado por `calcular_portas` e `auditar_portas`. Efeito: só melhora (desconhecido 21.713→21.654; 59 resgatados). **Privacidade:** alguns deals `Shipped` (0,03%) trazem **nome de pessoa** no `nome` — a A3 mascara qualquer `nome` não-numérico ("(sem nº)").
- **[2026-07-16] Métrica escolhível (Lucro Bruto × Receita).** As 4 builders (`_triangulo_lb`, `_lb_primeira_compra`, `tabela_por_safra`, `tabela_por_linha`) ganharam o parâmetro **`metrica`** (default `"mc_produto"` = Lucro Bruto; `"valor"` = Receita bruta). **Zero conta nova** — só troca a coluna somada. Receita **não** desconta mídia nem custo (bruta). Para "todos": `metrica="mc_produto"` reproduz `coortes.lucro_bruto`; `metrica="valor"` reproduz `coortes.ltv` (o LTV da Cohorts) ao centavo.
- **[2026-07-16] `auditar_portas` → `AuditoriaPortas` (aba A3).** Prepara o drill-down por cliente: reusa `calcular_portas` (a MESMA coluna `porta`) e acrescenta, só para os "Produto desconhecido", o **motivo** (Comercial / estreia fora da base / sem itens casados / só brinde-sem-nome — espelha a régua de `_porta_por_cliente`, só rotula o porquê; vetorizado). Devolve as **estreias** (1 linha/cliente: nome, data, valor, etapa, idade, safra, porta, motivo, nº de compras, valor total), todos os **deals** (para a linha do tempo) e os dicionários **SKU→nome/linha/papel** (nome vem de `dados.itens["descricao"]`, parcial). Não recalcula dinheiro.
- **Estado:** **construído e verificado (2026-07-15; métrica Receita + A3 2026-07-16).** `portas("todos")` = `coortes.lucro_bruto` **E** `coortes.ltv` (dif 0,0 nas 64 safras nas duas métricas); partição dos clientes intacta (0/64) → **check nº 6 do `checar_coerencia.py`** (agora prova as duas métricas). A3: motivo bate com o diagnóstico medido (11.721 sem itens + 6.279 só-ruído = 18.000 Shipped; 1.912 fora da base; 1.801 Comercial). Régua **Lucro Bruto PARCIAL** (a Receita é bruta, sem ressalva de custo).

#### roteador (`painel.py`) — 2026-07-14
- **Responsabilidade:** declarar o **menu** (`st.navigation`) e chamar a tela escolhida. Não desenha nada. Único lugar com `st.set_page_config`. Ordem/nomes: **1. Geral** (`views/geral.py`) · **2. Aquisição** (`views/aquisicao.py`) · **3. Cohorts** (`views/coortes.py`) · **4. Portas de entrada** (`views/portas_entrada.py`) · **A1 - Auditoria Custos** (`views/auditoria.py`) · **A2 - Auditoria MC Cohort** (`views/auditoria_cohort.py`) · **A3 - Auditoria Portas** (`views/auditoria_portas.py`).
- **Por quê:** com a descoberta automática da pasta `pages/`, o nome do item vinha do nome do arquivo (a tela principal aparecia como "painel") e a ordem era alfabética. Entrada segue `python3 -m streamlit run painel.py`.

#### peças-visuais (`ui.py`) — 2026-07-14
- **Responsabilidade:** desenhar a **cascata** (`tabela_dre`) — cores, indentação e a análise vertical (% da receita). É o par visual de `cascata.montar_cascata` (que faz os números). Antes, cada aba tinha a sua cópia dos estilos.
- **Quem depende:** painel-ui, aquisicao-ui, coortes-ui.

#### painel-ui (`views/geral.py`)
- **Responsabilidade:** desenhar herói, 5 cartões, tabela DRE, filtro de período, botão Atualizar, editor de custos e a barra de alertas. Cacheia a leitura (`st.cache_data`).
- **Depende de:** calculo-cascata.
- **Quem depende:** o João (usuário).
- **Estado:** **construído e verificado (2026-07-01; +rebase HubSpot 2026-07-14).** Sobe headless (HTTP 200) e roda de ponta a ponta via `AppTest` sem exceção. Tema branco (`.streamlit/config.toml`).
- **[rebase 2026-07-14]** carrega o HubSpot (`carregar_deals`, degrada p/ None se ausente) e passa a `calcular` — pode mostrar **qualquer mês** (2021→hoje). Meses históricos vêm **estimados (25%)** com faixa amarela; o mês atual segue real e idêntico. Mesma coisa na **aquisicao-ui**.

#### aquisicao-ui (`views/aquisicao.py`) — V2
- **Responsabilidade:** a aba de aquisição (página multipage). Desenha o herói MC-novos (verde ≥ 0 / vermelho < 0 = a linha do zero), 5 cartões (MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS), a mini-cascata de novos e a barra de alertas. Seletor de período próprio; mesmo cache de leitura do painel; só lê.
- **Depende de:** `cascata.calcular_aquisicao` (mesmo recorte do painel → as faixas amarram) e `dados.carregar_tudo`.
- **Estado:** **construído e verificado (2026-07-09).** `AppTest` sobe sem exceção (5 cartões + DRE); amarração das 3 faixas confere com o total do painel; aritmética da MC-novos, CAC, aROAS e bordas (sem mídia / sem novos / rótulo inesperado) testadas.

#### coortes-ui (`views/coortes.py`) — V4
- **Responsabilidade:** a aba de coortes (página multipage). Cabeçalho de KPIs da safra do seletor (payback, CAC, MC/cliente até hoje, recompra 90d), **curva de payback** (Altair — últimas N safras, linha do zero, safra em destaque), **triângulo** (tabela verde/vermelho + célula estimada em itálico com `*`), barra de notas ("MC parcial", % estimada, arquivo velho, sem mídia). Seletor de safra + slider de nº de safras; só lê.
- **[V4] Auditoria por safra (2026-07-12; redesenhada 2026-07-13):** seção **"🔍 Auditar a MC de uma safra"** atrás de um **toggle**. Três blocos (pedido do João): **A) MC dos novos** (1ª compra de cada cliente da safra) — cascata **completa igual às outras abas** (Vendas → deduções abertas → CMV → Lucro Bruto → − mídia inteira → MC-novos); **B) MC de recompra** (compras seguintes) — agrupada (Vendas → Deduções `%` → CMV → MC-recompra), **sem mídia**; **C) MC total** = novos + recompra, **total × por cliente**. **Slider de horizonte** (m+0..último fechado) recalcula a recompra/total. Partição **novos = 1ª compra por cliente** (não `tipo_de_venda`); ⚠️ diverge da aba Aquisição de propósito (régua Minimal vs Shopify). Mês-a-mês num checkbox "avançado"; **download CSV** (sem e-mail). **Reconciliação:** MC total/cliente = `mc_acumulada[safra, horizonte]` do triângulo (✅). Spec `docs/specs/2026-07-10-v4-auditoria-por-safra.md`.
- **Depende de:** `coortes.calcular_coortes` + `coortes.detalhar_safra` + `dados.carregar_tudo`/`carregar_hubspot`. Cache próprio (`carregar_e_calcular` + `auditar`, keyed por dia/safra). **CSV ausente = erro só nesta aba** (não derruba V1/V2).
- **Estado:** **construído e verificado (2026-07-10; auditoria 2026-07-12).** `AppTest` sobe sem exceção (KPIs + curva + triângulo + auditoria com toggle on/off); default = safra fechada mais recente (2026-06).

#### portas-ui (`views/portas_entrada.py`) — 2026-07-15 (switch/sort/texto 2026-07-16; métrica Receita 2026-07-16)
- **Responsabilidade:** a aba "4. Portas de entrada" (página anexa). **Seletor de métrica** (Lucro Bruto × Receita) + filtro de **produto** (para a tabela por safra) + filtro de **data** (para a tabela por linha) + N mínimo + **switch de leitura** (Valor total R$ × Aumento vs 1ª compra ×). Duas tabelas do valor/cliente (`1ª compra | 30D…365D` + CAC), verde por coluna, "—" abaixo do N mínimo, célula vazia = mês não fechado. Barra de ressalva metric-aware ("Lucro Bruto PARCIAL" / "Receita bruta"). Cache próprio (`_carregar`, keyed por dia). Só lê.
- **[2026-07-16] Seletor de métrica:** um radio no topo troca o conteúdo das **mesmas** duas tabelas entre **Lucro Bruto** (antes da mídia, régua parcial) e **Receita** (bruta, antes de qualquer custo) — decisão de layout do João (troca, não empilha). Passa `metrica="valor"`/`"mc_produto"` a `portas.tabela_por_safra`/`tabela_por_linha`. Todos os rótulos/legendas são metric-aware (`TERMO`/`TERMO_CELL`); no modo Receita a ressalva de "CMV estimado %" some (a receita = `valor` é sempre real). O switch × e os filtros valem para as duas métricas.
- **[2026-07-16] Switch de leitura (×):** no modo "Aumento vs 1ª compra", cada célula = valor ÷ a 1ª compra da própria linha (base 1,00×). Lente de **display** — não recalcula custo/CAC; guarda intacto. 1ª compra ≤ 0 → "—".
- **[2026-07-16] Tabela por linha:** ordenada por nº de clientes (baldes no fim) e com um **aviso na tela** ("leia por coluna, não por linha") + exemplo dobrável explicando que uma coluna pode ser menor que a anterior por **composição** (cada janela usa só as safras maduras para ela — a curva sempre-sobe é a tabela por safra). Decisão do João: Opção 1 (mais dado + explicar). ADR `2026-07-15-portas-de-entrada-produto` §6.
- **Depende de:** `portas.calcular_portas`/`tabela_por_safra`/`tabela_por_linha` + `coortes_ui` (formatação, `ratio`) + `dados`.
- **Estado:** **construído e verificado (2026-07-15; switch/sort/texto 2026-07-16).** `AppTest` sobe sem exceção (6 telas), nos dois modos do switch.

#### auditoria-portas-ui (`views/auditoria_portas.py`) — A3, 2026-07-16
- **Responsabilidade:** a aba "A3 - Auditoria Portas" (anexo). Filtro de **porta** (default "Produto desconhecido") + faixa de safra + busca por nº. Quando a porta é o desconhecido, mostra o **resuminho por motivo**. **Lista** 1 linha/cliente (`st.dataframe` com `on_select` de linha única — padrão do A1): data da estreia · pedido (mascarado no Comercial) · nº de compras · valor 1ª · valor total · motivo. **Drill-down** ao clicar: para cada compra do cliente, cabeçalho (data · m+x · valor · pedido) + tabela dos itens (produto · SKU · linha · papel · qtd). CSV da lista (sem e-mail). Só lê.
- **Privacidade/trava:** nunca exibe/exporta `e_mail` (guardado num array paralelo à tabela, fora da tela); no Comercial o `nome` é a PESSOA → mascara "(Comercial)"; e o drill-down **não** casa itens de deal não-`Shipped` (numeração colide — §11).
- **Depende de:** `portas.auditar_portas` + `cascata.ETAPA_SHOPIFY` + `dados` + `coortes_ui` (formatação). Cache próprio (`_carregar`, keyed por dia).
- **Estado:** **construído e verificado (2026-07-16).** `AppTest` sobe sem exceção (porta default = desconhecido); o ramo do clique (linha do tempo) exercitado nos 4 casos (só-ruído, sem-itens, Comercial mascarado, Multiprodutos com 24 compras).

#### auditoria-ui (`views/auditoria.py`)
- **Responsabilidade:** página anexa (multipage) para o João validar o custo pedido a pedido — tabela `data · pedido · itens · valor · custo · custo %`, flag de suspeitos, drill-down item a item (com descrição) e exportar CSV.
- **Depende de:** `cascata.detalhar_pedidos` (mesmo recorte de `calcular` → totais batem com a MC) e `dados.carregar_descricoes`.
- **Estado:** **construído e verificado (2026-07-04).** Soma de custo == CMV do painel; roda via `AppTest` sem exceção. Descrições parciais (fonte limitada).

> **Nota SSL (macOS / Python.org):** o Python do João não valida sozinho o certificado do Google (falta a lista de autoridades). `dados.py` resolve baixando os bytes via `urllib` com um contexto SSL do `certifi` (já instalado, não é dependência nova) e entregando ao pandas. Sem isto, toda leitura falhava com `CERTIFICATE_VERIFY_FAILED`.
>
> **Nota robustez (2026-07-02):** `_ler_csv` é blindado contra soluços do Google. Confere o `content-type` (só aceita `text/csv`; HTML = página de erro/login) e **tenta 3× com espera crescente** (1,5s, 3s) antes de desistir. Se falhar, levanta `ErroDeDados` com mensagem clara — nunca mais o erro confuso de "coluna faltando" quando o problema é rede.

### Diagrama (ASCII)

```
                                                     [roteador: painel.py]  → st.navigation
                                                        ↓        ↓       ↓        ↓
[planilha-contrato]  →  [carregador-de-dados]  →  [calculo-cascata]  →  [views/geral.py]
 (5 abas Google)          (dados.py)                (cascata.py)          [views/aquisicao.py]
                              ↑                     (juntar_custos,        [views/auditoria.py]
 [bases/hubspot_deals.csv] ───┘                      cmv_por_pedido,             ↑
 (arquivo local, V4)          └→ carregar_hubspot →  montar_cascata)        [ui.py] (desenho
                                     ↓                                       da cascata)
                                [calculo-coortes] → [views/coortes.py]
                                 (coortes.py)
```

---

## 3. Entidades e modelo de dados

> Não há banco. Cada "tabela" é uma **aba da planilha Google**. O painel lê; não escreve.

### 3.0 Conexão real (verificada em 2026-07-01)
- **Planilha:** `SHEET_ID = 1-z6gebmW_tBmJSGVS06vfjsHgLEStbFbRbEwJFXL9KM` — compartilhada como "qualquer um com o link pode ver". Acesso público por CSV confirmado.
- **Leitura ao vivo:** `https://docs.google.com/spreadsheets/d/<SHEET_ID>/export?format=csv&gid=<GID>`.
- **Mapa gid → aba (nomes de coluna vieram ORIGINAIS, não renomeados):**
  | Papel | gid | Cabeçalho real |
  |---|---|---|
  | Vendas | `0` | `order_id, order_name, processed_at_data, net_revenue` |
  | Itens (Shopify — FONTE ATIVA) | `1246117066` | `id, data_order, item_desmembrado_codigo, quantidade_final, item_desmembrado_nome`. Fonte dos itens (mais confiável que a NF de saída — decisão do João, 2026-07-04). **Dobra de kit corrigida na fonte, live na planilha (informado pelo João, 2026-07-09) — paliativo do painel aposentado (ver §6).** Nomes com 99,6% de cobertura. |
  | Custos (3.2 — FONTE PRINCIPAL) | `634911340` | `SKU, PREÇO JUNHO`. **Fonte principal de custo desde 2026-07-22** (tabela atualizada do Financeiro; 1.072 SKUs com custo). Onde vier 0/vazia, cai para a 3.1. ADR `2026-07-22-fonte-custos-3-2`. |
  | Custos (3.1 — REDE DE SEGURANÇA 1) | `1460088128` | `SKU, Custo`. Foi a principal (2026-07-09→2026-07-22); agora **fallback** onde a 3.2 falta. |
  | Custos (3 — REDE DE SEGURANÇA 2) | `423190064` | `SKU, Valor de Custo`. A mais antiga; usada onde 3.2 e 3.1 faltam. |
  | Midia | `1308114343` | `data, mes, fb_investimento, google_investimento, google_institucional_investimento` |
  | (ignorar) | `1244431795` | base agregada `receita_total...` — não usar |
  | (superado) | `1466784982` | silver crua — era dicionário SKU→nome; **superado** desde 2026-07-04 (o nome agora vem da própria aba Itens). `carregar_descricoes` virou reserva, sem uso ativo. |
  | (avaliada, parkeada) | `488044140` = "2.1. Itens" | NF-e de venda (`silver_minimal_bling_nfe_fechamento`), casa por `numeroPedidoLoja` = final do `order_id`. **Testada como fonte de itens e revertida (2026-07-04):** dobra igual à Shopify em ~91% dos pedidos e **corta brinde** (a venda é fonte mais confiável). Guardar como fonte de **receita fiscal** (v2+). Constantes ainda no código (`GID_ITENS_NF`, `_NF_*`) caso volte a ser útil. |
- **Ajustes que o carregador precisa fazer:**
  - **Mapear nomes:** `processed_at_data`→data (Vendas); `id`→order_id, `data_order`→data, `item_desmembrado_codigo`→sku, `quantidade_final`→quantidade (Itens); `SKU`→sku e a coluna de custo→valor_custo, numa **cascata de 3 abas** (`dados.FONTES_CUSTO`): `PREÇO JUNHO` (3.2, principal) → `Custo` (3.1) → `Valor de Custo` (3).
  - **Decimal misto:** `Custos` tem ponto (`34.5`) E vírgula (`145,30`) na mesma coluna; `Vendas`/`Midia` usam vírgula. Leitor robusto: com `.` e `,` → `.`=milhar; só `,` → decimal; só `.` → decimal.
  - **Datas:** `processed_at_data` e `Midia.data` = `DD/MM/AAAA`; `Itens.data_order` = `DD/MM/AAAA HH:MM:SS` (tirar a hora). Parse `dayfirst`.
- **Aba `Parametros` NÃO existe na planilha.** Na v1 os 10 percentuais ficam **embutidos no código** (`cascata.py`, constante `PARAMETROS`; valores atualizados pelo Financeiro em 2026-07-22 — spec `2026-07-22-parametros-dre`). Quando o João criar a aba, trocar a fonte para leitura da planilha.

### Aba `Vendas` (Base 1 — Shopify/atribuição, 1 linha por pedido, só `PAID`)
| Coluna | Tipo | Origem | Notas |
|---|---|---|---|
| `order_id` | texto | `order_id` | chave do pedido (`gid://shopify/Order/...`) |
| `order_name` | texto | `order_name` | número humano (ex: 503184) |
| `data` | data | `processed_at_data` | data do pagamento; filtro de período |
| `net_revenue` | número | `net_revenue` | **a linha Vendas** = Σ desta coluna |
| `customer_type` | texto | `customer_type` | **[V2]** carimbo nativo Shopify: `Primeira Compra` / `Recompra` / vazio. Exigido a partir da V2 (aba de aquisição). Só normaliza espaçamento; match sensível a acento/maiúscula. |

- **Invariantes:** 1 linha por pedido; só pedidos `PAID`. `customer_type` é imutável (foto do momento do pedido).

### Aba `Itens` (base silver `silver_minimal_shopify_pedidos_products`, 1 linha por item explodido, só `PAID`)
| Coluna | Tipo | Origem | Notas |
|---|---|---|---|
| `order_id` | texto | `id` | mesma chave da aba Vendas |
| `data` | data | `data_order` (só a data) | período do CMV |
| `sku` | texto | `item_desmembrado_codigo` | SKU real (kit já explodido) |
| `quantidade` | número | `quantidade_final` | inclui brindes |

- **Invariantes:** kits vêm explodidos; brindes entram (têm custo). **Atenção:** esta aba contém pedidos de **outros canais** (B2B, TikTok, Mercado Livre, Assinatura), não só Shopify — por isso o CMV só conta itens cujo `order_id` está na aba `Vendas` (ver ADR 2026-07-02).

### Aba `Custos` (tabela de custo, 1 linha por SKU) — cascata de três abas desde 2026-07-22
| Coluna | Tipo | Origem | Notas |
|---|---|---|---|
| `sku` | texto | `SKU` | chave de junção com `Itens.sku` |
| `valor_custo` | número | `PREÇO JUNHO` (3.2, principal) → `Custo` (3.1) → `Valor de Custo` (3) | custo unitário |

- **Regra de fonte (spec 2026-07-22):** para cada SKU o custo é o 1º que existir com valor > 0:
  (1) correção local `custos_extra.csv`; (2) aba **3.2**; (3) aba **3.1**; (4) aba **3**;
  (5) senão, sem custo → alerta. **Custo 0 é tratado como faltando, não como grátis.**
  A ordem mora em `dados.FONTES_CUSTO`. ADR `2026-07-22-fonte-custos-3-2`.
- **Invariantes:** SKU único por linha em cada aba. Se um `Itens.sku` não existir em
  nenhuma das três → **alerta na tela**.

### Aba `Midia` (BigQuery → planilha, 1 linha por dia)
| Coluna | Tipo | Origem | Notas |
|---|---|---|---|
| `data` | data | `data` | período |
| `fb_investimento` | número | `fb_investimento` | Meta |
| `google_investimento` | número | `google_investimento` | Google |
| `google_institucional_investimento` | número | `google_institucional_investimento` | Google institucional |

- **Invariantes:** Ad Spend = `fb_investimento/(1−0,1215)` + `google_investimento` + `google_institucional_investimento` (FB embrutecido pelo imposto de 12,15% — ADR 2026-07-03). (Removidas `fb_trafego`/`fb_captacao` para não contar em dobro.)

### Aba `Parametros` (João preenche, 1 linha por parâmetro)
| Coluna | Tipo | Notas |
|---|---|---|
| `parametro` | texto | grafia fixa: devolucoes, chargebacks, pis_cofins_cbs, icms_ibs, outras_deducoes, frete, embalagem, gateways, plataforma, antecipacao |
| `percentual` | número | valor sem o símbolo % (ex: 4,8) |

- **Invariantes:** todas as linhas em % incidem sobre a linha Vendas.

### `bases/hubspot_deals.csv` (arquivo LOCAL — V4, fonte de cliente/coorte)
> Não é aba da planilha. É um **CSV local** que o João gera **1×/mês** por uma query no
> BigQuery (`silver_deals_minimal`, filtro `Shipped` + `Negócio Fechado - Comercial`) — o
> BigQuery como **torneira**, sem credencial no painel (ADR `2026-07-10-v4-arquitetura-mvp-coortes`).
> 462k linhas hoje. Lido por `dados.carregar_hubspot`.

| Coluna | Tipo | Notas |
|---|---|---|
| `e_mail` | texto | **chave de cliente** (minúsculo, sem espaço). 9 vazias descartadas. |
| `nome` | texto | número do pedido → ponte com `Vendas.order_name`. **91% vêm com `#`** → removido (`lstrip("#")`). No `Negócio Fechado - Comercial` é o **nome do cliente** (nunca casa → estimado). |
| `valor` | número | receita do deal (ramo estimado; ponto decimal no export do BQ). |
| `data_de_fechamento` | data | data do pedido — **ISO `AAAA-MM-DD`**. Base da idade da coorte. |
| `tipo_de_venda` | texto | `Primeira Compra`/`Recompra`. |
| `etapa_do_negocio` | texto | `Shipped` (98,8%, casável) ou `Negócio Fechado - Comercial` (1,2%, sempre estimado). |
| `data_primeira_compra` | data | **âncora da safra** (cross-canal) — ISO. |
| `meses_desde_primeira_compra` | inteiro | ⚠️ **NÃO é a idade do deal** — é a idade do CLIENTE no export (constante por cliente). **Não usar como idade** (ver §6). |

- **Ponte de custo (ramo real):** `hubspot.nome → Vendas.order_name → Vendas.order_id (gid) → Itens.order_id → Custos.sku`. Casa via as **3 camadas** (base histórica → planilha) em quase toda a história; onde não há itens → estimado 0,30×valor.

### `bases/mapa_sku_linha_produto.csv` (arquivo LOCAL versionado — régua de "porta de entrada")
> Régua de negócio **validada à mão pelo João** (2026-07-15), não é export do BQ. Classifica cada SKU numa
> **linha de produto** (Camiseta Minimal, Calça Jeans 1.0/2.0, Polo 2.0, …). Base da feature "Portas de
> entrada" (spec `docs/specs/2026-07-15-portas-de-entrada-produto.md`; **build pendente**).

| Coluna | Tipo | Notas |
|---|---|---|
| `sku` | texto | = `Itens.item_desmembrado_codigo` (chave de junção). 1.144 SKUs. |
| `linha` | texto | linha de produto (a "porta"). **26 linhas-porta** + "Produto desconhecido". |
| `papel` | texto | `porta` (produto vendável) · `brinde` (carteira/BRINDE/Perfume/Skincare — **removido do pedido antes de decidir a porta**) · `desconhecido` (SKU sem nome → "Produto desconhecido"). |
| `nome_exemplo` | texto | um nome de item de amostra (referência humana). |
| `unidades` | número | volume histórico (só pra ordenar/priorizar; não entra no cálculo). |

- **Regra provisória (ADR a escrever):** produto de entrada = a `linha` do pedido de **estreia** quando ele
  tem **categoria única** (após remover brindes); mais de uma → "Multiprodutos"; nenhuma → "Produto desconhecido".

### Chave de junção entre abas
- `Vendas.order_id` = `Itens.order_id` (texto idêntico, `gid://shopify/Order/...`).
- `Itens.sku` = `Custos.sku`.
- **[V4]** `hubspot.nome` = `Vendas.order_name` (após remover o `#`); `hubspot.e_mail` = identidade do cliente (só na coorte).
- **[discovery 2026-07-14] Ponte DIRETA HubSpot ↔ itens (para a base histórica):** a tabela silver de itens (`silver_minimal_shopify_pedidos_products`) carrega o **número humano do pedido na coluna `name`** (ex.: `510969`) — não só o `id` (gid). Então `hubspot.nome` (com `lstrip("#")`) casa **direto** com `itens.name`, **dispensando a volta pela Vendas** que o código faz hoje (`nome → Vendas.order_name → Vendas.order_id → Itens.id`). Provado no dado: o pedido 510969 bate nas duas bases por número + e-mail + valor (836,84). É a base da **Opção 1** (CMV real histórico) — a construir em sessão dedicada (base gigante exportada → `bases/itens_historico.csv`; CMV em 3 camadas: base histórica → planilha → estima 30%). Log `docs/sessions/2026-07-14-discovery-base-itens-historica-ponte-direta.md`.

---

## 4. Fluxos de dados

### Abrir e ler o painel (bate com Fluxo B do PRODUCT.md)
1. **Trigger:** João roda `streamlit run painel.py` e escolhe um período (padrão: este mês).
2. **Função que recebe:** `painel.py` → chama `carregador-de-dados`.
3. **Validações:**
   - normaliza datas (formato BR `DD/MM/AAAA`) e números (vírgula decimal).
   - detecta `Itens.sku` sem correspondência em `Custos` → prepara alerta.
4. **Operações (em ordem):**
   - filtra `Vendas`, `Itens`, `Midia` pelo período.
   - `Vendas` do período = Σ `net_revenue`; `Pedidos` = distinct `order_id`.
   - `CMV` = Σ (`valor_custo` × `quantidade`) via junção `Itens`×`Custos`.
   - aplica os % de `Parametros` sobre Vendas → linhas de dedução/custo.
   - `Mídia` do período = Σ das 3 colunas.
   - monta Lucro Bruto e MC.
5. **Resposta para o usuário:** herói (MC), 5 cartões, tabela DRE, alerta (se houver SKU sem custo).
6. **Side effects:** nenhum (leitura pura; não escreve na planilha).

---

## 5. Decisões arquiteturais já tomadas

| Data | Decisão | Por quê | Impede no futuro | ADR |
|---|---|---|---|---|
| 2026-06-30 | Vendas = `net_sales − returns + shipping` no formato Shopify (provisório); v1 usa só `net_revenue` | fidelidade ao relatório nativo; alinhamento com Financeiro pendente | tratar a MC como número contábil oficial | `docs/decisions/2026-06-30-tratamento-devolucoes-e-net-sales.md` |
| 2026-07-01 | Stack v1: Streamlit (Python) lendo uma planilha única ao vivo | menor atrito, pronto rápido, 1 porta de entrada de dados | trocar de fonte sem reescrever o carregador; multiusuário/login | `docs/decisions/2026-07-01-stack-streamlit-planilha-unica.md` |
| 2026-07-02 | CMV conta só itens de pedidos presentes na aba `Vendas` (fonte de verdade); `Itens` tem outros canais | escopo v1 é só Shopify; alinhar receita×custo | tratar `Itens` como fonte independente de vendas; contar canais fora do Shopify na v1 | `docs/decisions/2026-07-02-cmv-so-pedidos-da-aba-vendas.md` |
| 2026-07-02 | Pedidos com camisetas `CamiseAnjosFrach*` saem inteiros da análise (Vendas, Pedidos, CMV) | João classificou fora do escopo da MC | tratar AnjosFrach como venda normal enquanto a regra existir | `docs/decisions/2026-07-02-excluir-anjosfrach.md` |
| 2026-07-02 | Correções de custo num arquivo local (`custos_extra.csv`) via editor no painel; painel escreve fora da base | João não edita a base; precisa de self-service | invariante "só lê" agora vale só p/ a planilha; multiusuário exigirá storage compartilhado | `docs/decisions/2026-07-02-editor-custos-arquivo-local.md` |
| 2026-07-03 | FB Ads embrutecido pelo imposto: `fb_real = fb_investimento/(1−0,1215)`; só FB | contabilizar o imposto de 12,15% pago ao investir; MC/MER reais | tratar Ad Spend como soma pura das colunas | `docs/decisions/2026-07-03-imposto-fb-ads.md` |
| 2026-07-04 | Direção de evolução: do painel de MC ao Motor de Crescimento Lucrativo; escopo comprometido V1→V4, V5-V7 parkeados | caminhar em direção ao modelo do documento em passos que destravam decisão; testar a tese na V4 antes do aparato caro | tratar o painel como só-relatório; importar os alvos da True Classic sem calibrar; construir V5+ antes de rodar a V4 | `docs/decisions/2026-07-04-roadmap-motor-crescimento.md` (ver `docs/ROADMAP.md`) |
| 2026-07-09 | Custo por SKU vem da aba **3.1** (mais atualizada/cobertura), com a aba **3** como rede de segurança onde a 3.1 vem zerada; custo 0 = faltando, não grátis | 3.1 é melhor no geral mas tem 137 SKUs zerados (famílias não preenchidas); trocar puro inflaria a MC | tratar 0 na 3.1 como custo real; aposentar a aba 3 antes de a 3.1 estar completa | `docs/decisions/2026-07-09-fonte-custos-3-1-com-fallback.md` |
| 2026-07-09 | **V2 — aba de aquisição** como página nova; parte por `customer_type`; mídia INTEIRA nos novos; guarda silenciosa da amarração; ausência do carimbo = falha barulhenta | responder "a aquisição se paga na 1ª compra?" reusando o recorte do painel; faixas amarram; falhar claro > silenciar | tratar recompra na tela da V2; fatiar mídia por faixa (é V4); degradar em silêncio se o carimbo sumir | spec `docs/specs/2026-07-09-v2-aba-aquisicao.md` (ADR de domínio: `2026-07-09-v2-aquisicao-customer-type-shopify`) |
| 2026-07-10 | **V4 — coortes de recompra** a partir do HubSpot (`silver_deals_minimal`, filtro `Shipped`); cliente por `e_mail`; coorte por `data_primeira_compra` (**cross-canal**); MC **acumulada por cliente**; MC real de 2022-01, 25% antes; **V3 (custo real por pedido) esvaziada** (custos seguem em %) | seguir a mesma turma no tempo pra decidir acelerar/segurar a mídia; a base já entrega a coorte pronta; fonte única de cliente; custos em % por escolha do João | tratar o carimbo Shopify como fonte de novo×recompra (agora é o HubSpot); ler o histórico pelo CSV da planilha estreita (vai pro BQ); alvo calibrado na tela (é V5) | `docs/decisions/2026-07-10-v4-coortes-recompra-hubspot.md` |
| 2026-07-10 | **V4 arquitetura (MVP = Opção 2):** BigQuery = **torneira** (puxa a base HubSpot 1×/mês → `hubspot_deals.csv` local); **cálculo na plataforma** reusando a receita de custo do painel; **CMV real só na janela de itens atual, 25% estimado antes**; ponte pelo `nome` (não há gid no HubSpot) | painel sem credencial (espírito do ADR do stack); uma verdade de custo (Auditoria=coorte); MVP roda cedo; anos de itens não cabem numa aba | tratar o BQ como motor de cálculo do painel; duas verdades de custo; ler anos de itens da planilha | `docs/decisions/2026-07-10-v4-arquitetura-mvp-coortes.md` |
| 2026-07-14 | **Rebase do painel geral e aquisição no HubSpot:** `calcular`/`calcular_aquisicao` ganham `deals=`; roteador pela **borda da janela de Vendas** (dentro = real/planilha idêntico; fora = HubSpot estimado 25%); rótulo real/estimada/mista | destravar meses históricos sem mexer na janela atual (que o João valida) nem criar verdade de custo nova; MC parcial marcada, não fingida | tratar a janela atual como estimada; contar mídia em dobro no período misto; aplicar AnjosFrach à história | `docs/decisions/2026-07-14-rebase-geral-aquisicao-hubspot.md` |
| 2026-07-14 | **CMV estimado = 30% da receita** onde não há itens (histórico + Comercial); deduções/custos % incidem sobre a receita inteira; a linha "Margem estimada (25%)" some (o ⚠️ passa para o CMV) | os 25% eram chute pessimista: o CMV real medido é 28,8–29,0% e a margem de produto real ~43% (não 25%); 30% é o real arredondado p/ cima (conservador) | tratar o número histórico como fechamento; ter duas estimativas diferentes (painel × coorte) | `docs/decisions/2026-07-14-cmv-estimado-30-por-cento.md` |
| 2026-07-14 | **CMV real na história inteira:** itens em **3 camadas** (histórico local → planilha → 30%); ponte direta pelo número do pedido; **só `Shipped` casa itens** (o Comercial colide de numeração) | o chute de 30% apagava a realidade (o CMV oscila 23%–41% conforme promoção); a base histórica cabia num arquivo local, como o HubSpot | tratar o `nome` do Comercial como nº de pedido; casar itens sem olhar a etapa do deal; depender do arquivo (ausente = degrada) | `docs/decisions/2026-07-14-cmv-real-historico-3-camadas.md` |
| 2026-07-14 | **Menu programável** (`st.navigation`, telas em `views/`) + **cascata única** (`cascata.montar_cascata` + `ui.tabela_dre`) + 6 cartões na Aquisição | nomear/ordenar o menu exigia roteador; o DRE remontado à mão em 6 lugares divergia a cada mudança | descobrir páginas pela pasta `pages/`; ter dois formatos de DRE no projeto | spec `docs/specs/2026-07-14-interface-menu-cascata-cmv-30.md` |
| 2026-07-10 | **V4 CONSTRUÍDA:** `carregar_hubspot` + `coortes.py` + `pages/3_Coortes.py` + refactor `juntar_custos`/`cmv_por_pedido`; **idade calculada** (não do campo do HubSpot); um cliente = uma safra (mínimo por `e_mail`) | amarração por pedido com o painel = 0; campo `meses_desde_primeira_compra` é idade do cliente, não do deal; deriva do HubSpot exigia ancorar no mínimo | usar o campo cru como idade; contar um cliente em 2 safras; duas verdades de custo | log `docs/sessions/2026-07-10-construcao-v4-coortes.md` |
| 2026-07-15 | **Aba "4. Portas de entrada" CONSTRUÍDA:** `portas.py` (reusa `coortes.py`) + `views/portas_entrada.py` + `carregar_mapa_portas` + check nº 6. Célula = Lucro Bruto/cliente; CAC blended; porta = linha da estreia; **"sem nome" é ruído** (mix → porta conhecida, não Multiprodutos) | uma verdade de custo/CAC (só a dimensão porta é nova); "todos" = Cohorts ao centavo + partição intacta; "sem nome" é gap de cadastro (2,47%), não sinal | usar a MC (contaria mídia 2×); CAC por produto; contar um cliente em 2 portas; tratar "sem nome" como categoria | `docs/decisions/2026-07-15-portas-de-entrada-produto.md` |

---

## 5-bis. Definições compartilhadas entre as telas (regra do projeto, 2026-07-14)

> **Todas as telas usam as MESMAS definições. Os números TÊM de bater.** Divergir só com ordem
> explícita do João, com rótulo na tela e ADR. (Motivo: em 2026-07-14 a aba Aquisição e a A2
> mostraram números diferentes para o mesmo mês — cada uma tinha a sua régua de "cliente novo".
> Números que deveriam ser iguais e não são corroem a confiança no painel inteiro.)

**Cada definição tem UM dono no código.** Tela nunca reescreve a regra — chama o dono:

| Definição | Dono (única fonte) | O que é |
|---|---|---|
| Receita / Vendas | `cascata._cascata_de_deals` | Σ `valor` dos deals do HubSpot |
| Data do pedido | idem | `data_de_fechamento` (HubSpot) |
| **Cliente novo** | **`cascata.mascara_cliente_novo`** | carimbo `tipo_de_venda = "Primeira Compra"` **E** no mês da estreia |
| Estreia / safra | `coortes._preparar_deals` | mês da `data_primeira_compra` (mínimo por `e_mail`) |
| Idade (m+x) | idem | meses-calendário entre fechamento e estreia |
| CMV | `cascata.juntar_custos` / `cmv_por_pedido` / `cmv_por_nome` | item a item (janela atual **e** base histórica); **30% da receita** só onde não há itens (`CMV_ESTIMADO_FRACAO`) |
| **Lucro Bruto por cohort** | `coortes.ResultadoCoortes.lucro_bruto` | MC **antes** da mídia — o único numerador de ratio ÷ CAC (empate = 1,00×) |
| Deduções / custos % | `cascata.PARAMETROS` via `montar_cascata` | sobre a receita inteira |
| Mídia (Ad Spend) | `cascata._ad_spend_periodo` / `coortes._ad_spend_por_mes` | gross-up FB 12,15% (≥ 2026-01) |
| Exclusões | `cascata._pedidos_excluidos` + `PEDIDOS_EXCLUIDOS_NOME` | valem em **todas** as telas |
| Forma do DRE | `cascata.montar_cascata` + `ui.tabela_dre` | uma cascata só |

**Quando a fonte se contradiz:** elege-se um campo mestre e registra-se em ADR. Vigente: entre o
carimbo `tipo_de_venda` e a `data_primeira_compra`, **a estreia manda** (ADR
`2026-07-14-regua-unica-cliente-novo`).

**Guarda automático:** `python3 checar_coerencia.py` — prova que Aquisição × A2 batem, que a A2
re-expõe a célula do triângulo, que os subtotais das cascatas fecham e que os dois triângulos da
aba Cohorts concordam. Rodar após qualquer mexida em `cascata.py`/`coortes.py`.

---

## 6. Pontos frágeis conhecidos

### Vendas e CMV vêm de tabelas diferentes — RESOLVIDO em 2026-07-02
- **Onde:** abas `Vendas` (Base 1, atribuição) e `Itens` (base silver).
- **Era frágil porque:** os órfãos apareciam em `Itens` sem venda casada. Diagnóstico de
  junho/2026: 877 pedidos em Itens sem Vendas (R$176k, 6,37% do CMV).
- **Causa (esclarecida pelo João):** a aba `Itens` traz pedidos de **outros canais**
  (B2B, TikTok, Mercado Livre, Assinatura), não só Shopify. A `Vendas` é a fonte de
  verdade dos pedidos.
- **Correção aplicada:** `cascata.py` passou a contar CMV **só de itens cujo `order_id`
  está na `Vendas` do período**. Impacto junho: CMV R$2,76M→R$2,61M; MC R$1,83M→R$1,99M;
  0 órfãos. Ver ADR `2026-07-02-cmv-so-pedidos-da-aba-vendas`.
- **Resíduo aceito:** 136 pedidos em Vendas sem Itens (R$63k, 0,78%) seguem sem CMV.

### Base 1 pode ter mais de uma linha por pedido
- **Onde:** aba `Vendas`.
- **Por que é frágil:** os nomes de coluna (`touchpoint_index`, `total_touchpoints`) têm cara de atribuição (várias linhas por pedido). João afirma ser 1 linha/pedido.
- **O que vai estourar primeiro:** Vendas inflada se houver duplicidade.
- **Plano:** o carregador conta `order_id` distintos e compara com o nº de linhas (guarda defensiva); avisar se divergir.

### Colunas de mídia podem se sobrepor
- **Onde:** aba `Midia`.
- **Por que é frágil:** se `fb_trafego`/`fb_captacao` estivessem dentro de `fb_investimento`, haveria dupla contagem. Já foram removidas.
- **Plano:** conferir o total de mídia contra o valor que o João conhece.

### Explosão de kit em dobro — RESOLVIDA (corrigida na fonte, 2026-07-09)

> **Corrigida na fonte e live na planilha (informado pelo João, 2026-07-09; não reverificado a pedido dele).** O paliativo B (`cascata.SKUS_KIT_VIRTUAL`) foi **aposentado** — com a fonte corrigida, continuar removendo o SKU virtual passaria a subtrair custo legítimo (MC inflada). O registro abaixo fica como memória do que foi o bug e de como foi medido.
- **Onde:** aba `Itens` (base silver), kits como "Compre 3 leve 4 + Carteira".
- **Sintoma:** o kit é explodido em **2× os itens** (ex: pedido #469395 = 1 kit de 5 itens virou 10; a Carteira `8301007000` aparece 2×). CMV do pedido sai ~2× o real.
- **Escopo medido:** assinatura (SKU repetido em linhas separadas) em **5.131 pedidos no histórico**; **1.824 em junho** (pedidos que somam ~18% do CMV do mês). A Carteira duplica em 4.866 pedidos.
- **Impacto medido (junho/2026):** deduplicar componentes baixaria o CMV em **~R$101.507** → MC de R$1,835M para ~**R$1,937M**. É **piso** (não corrige erros de quantidade nem itens fantasma). ~5-6% da MC. **Material — considerar priorizar o caminho A antes da v2.**
- **Dois sabores do bug:** (1) **SKU virtual** de kit junto dos componentes (ex: `8301001172`, pedido #469395) — o paliativo B pega; (2) **componentes duplicados** (ex: #469583 — Azul/Branca/Carteira em 2 linhas, sem SKU virtual) — o B **não** pega, só o A.
- **Direção do erro:** CMV **superestimado** → MC **subestimada** (o oposto do "sem custo").
- **Causa:** lógica de explosão de kit na fonte (BigQuery/silver) — NÃO é o painel (que só soma o que está na aba). Confirmado 2026-07-04: a **NF-e de venda tem a mesma dobra**, o que prova que o bug está a montante das duas bases (na explosão compartilhada), não na Shopify em si.
- **Resolução (2026-07-09):**
  - **A (definitivo) — FEITO:** a explosão foi corrigida na origem (informado pelo João); a base de Itens não duplica mais o SKU virtual junto dos componentes. Live na planilha.
  - **B (paliativo v1) — APOSENTADO:** `cascata.SKUS_KIT_VIRTUAL` (removia o SKU virtual `8301001172` do CMV) saiu do código — com a fonte corrigida, passaria a subtrair custo legítimo. Rastro no comentário do `cascata.py`; reintroduzir só se a dobra regredir.

### Datas em três abas diferentes
- **Onde:** `Vendas.data`, `Itens.data`, `Midia.data`.
- **Por que é frágil:** campos de data de origens distintas; nas bordas de período podem diferir por 1 dia.
- **Plano:** aceitar na v1; padronizar formato `DD/MM/AAAA` na planilha.

### [V4] A planilha estreita não comporta o histórico de coortes — ENDEREÇADO no MVP (2026-07-10)
- **Onde:** a stack lê CSV de uma planilha Google com janela curta (hoje abr–jul/2026).
- **Por que era frágil:** a coorte precisa de **anos** de clientes/itens; anos de itens (meses de
  ~120k linhas) **não cabem** numa aba de Google Sheet (~10M células).
- **Decisão (ADR `2026-07-10-v4-arquitetura-mvp-coortes`):** no MVP o BigQuery vira **torneira** — o
  João puxa a base HubSpot 1×/mês para um **arquivo local** (`hubspot_deals.csv`), e o cálculo roda
  na plataforma. Como o MVP usa **CMV real só na janela de itens atual** (25% estimado antes), o
  histórico de **itens** não precisa caber em lugar nenhum ainda.
- **Resíduo (Opção 1, versão seguinte):** quando a MC real ano-a-ano entrar, os **itens** históricos
  também virão de arquivo local (não da aba) — aí rodam as 3 queries de viabilidade (cobertura de
  custo de SKU antigo; ponte `order_name↔order_id` no BQ; mídia mensal desde 2022).

### [V4] Viés cross-canal da coorte — MEDIDO em 2026-07-10 (imaterial)
- **Onde:** coorte por `data_primeira_compra` (cross-canal) com MC/mídia só do Shopify.
- **Por que era frágil:** cliente que estreou fora do Shopify distorce o mês 0 e o CAC da safra.
- **Medido (query §9 V2):** só **0,87%** dos clientes têm a 1ª compra Shopify num mês posterior à
  1ª compra cross-canal — bem abaixo do portão de 10%, e **encolhendo** (2024: 1,0% → 2026: 0,08%).
  Viés aceito e confirmado pequeno. ADR `2026-07-10-v4-coortes-recompra-hubspot`.

### [V4] `meses_desde_primeira_compra` NÃO é a idade do deal — contorna a spec — 2026-07-10
- **Onde:** `bases/hubspot_deals.csv`; a spec §3.3/R4 e o `PRODUCT.md` §3 assumiam que esse campo
  era a idade da coorte (m+0, m+1) "vinda pronta da base".
- **O que se descobriu:** o campo é a **idade do CLIENTE no momento do export** — o **mesmo valor
  em todos os deals do cliente** (ex.: cliente de 2021-06 → 61 em todos; cliente que estreou em
  2026-06 → 1 até na própria 1ª compra). Usá-lo empilharia a turma inteira numa única idade.
- **Correção aplicada:** `coortes.py` **calcula** a idade = diferença em **meses-calendário** entre
  `data_de_fechamento` e a 1ª compra real do cliente (o mínimo por `e_mail`). O campo cru fica
  carregado mas **não é usado** para idade. Deals sem data de fechamento (6) ou com data anterior à
  1ª compra saem do triângulo (avisados).
- **A montante:** `PRODUCT.md` **corrigido em 2026-07-15** (§4/Fluxo A: a idade é calculada, não vem do campo). A **spec fica congelada** por decisão do João (regra do CLAUDE.md §6: spec é foto do dia; o ADR corrige o rumo).

### [V4] Janela de recompra de 90 dias vê menos da metade — MEDIDO 2026-07-10
- **Onde:** KPI "recompra em 90 dias" (R13).
- **Medido (query §9 V3):** a 2ª compra Shopify tem **mediana de 123 dias** (p75 322); só **42%**
  recompram em ≤90d, **60%** em ≤180d. O rótulo de 90d é honesto e comparável, mas **conservador**
  — a mediana cai fora dele. **Considerar mostrar 90d E 180d** numa próxima iteração (spec R13 já
  deixou aberto). Não quebra a V4; afina só o cartão.

---

## 7. Inventário de arquivos críticos

| Caminho | Responsabilidade | Quem deve mexer | Quem NÃO deve mexer |
|---|---|---|---|
| `painel.py` | **Roteador do menu** (`st.navigation`) — não desenha nada | Claude + João | — |
| `views/geral.py` | UI do painel de MC (tela "1. Geral") | Claude + João | — |
| `ui.py` | Desenho compartilhado da cascata (`tabela_dre`) | Claude + João | — |
| `cascata.py` | Regras de cálculo da MC | Claude com cuidado (toca dinheiro) | edição casual |
| `dados.py` | Leitura/limpeza da planilha + override local de custos | Claude | — |
| Planilha Google (5 abas) | Fonte de dados | João | Claude (só lê) |
| `custos_extra.csv` (local, gerado) | Correções de custo do João (via painel) | Painel/João | versionar (está no `.gitignore`) |
| `views/auditoria.py` | Auditoria de custo por pedido ("A1 - Auditoria Custos") | Claude + João | — |
| `views/aquisicao.py` | Aba de aquisição — MC de clientes novos (V2) | Claude + João | — |
| `coortes.py` | Regras das coortes de recompra (V4) — toca dinheiro | Claude com cuidado | edição casual |
| `views/coortes.py` | Aba de coortes — receita/LTV + triângulo MC/cliente + MC absoluta (V4) | Claude + João | — |
| `views/auditoria_cohort.py` | "A2 - Auditoria MC Cohort" — cascata da MC de um cohort | Claude + João | — |
| `coortes_ui.py` | Formatação (inclui `ratio` e `verde_gradiente`) + cache compartilhados pelas 2 telas de coorte | Claude + João | — |
| `bases/hubspot_deals.csv` (local, gerado 1×/mês) | Fonte de cliente/coorte do HubSpot | João (gera pelo BQ) | versionar (39 MB + contém e-mail; **já no `.gitignore`**) |
| `bases/itens_historico.csv` (local, gerado no BQ) | Itens de todo pedido desde 2021-10 → **CMV real da história** (1ª camada) | João (gera pelo BQ) | versionar (119 MB + contém e-mail; **já no `.gitignore`**) |
| `checar_coerencia.py` | O guarda: prova que as telas concordam. **Rodar ao mexer em `cascata.py`/`coortes.py`** | Claude + João | — |
| `.streamlit/config.toml` | Tema (branco) do painel | Claude | — |
| `checar_base.py` | Sanidade da planilha (linhas, período, amarração V×I) — rodar após reextrair | Claude + João | — |
