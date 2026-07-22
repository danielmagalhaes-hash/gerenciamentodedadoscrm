# CLAUDE.md — MC Growth

> Manual de operação do agente neste projeto. **Lido no início de TODA sessão.** Atualizado quando as convenções mudam.
>
> Este projeto é operado pelo método em [`vibe-coding-workflow/`](vibe-coding-workflow/README.md). Este arquivo é o ponto de entrada; o guia é a referência completa.

---

## 0. Estado atual do projeto

- **Natureza:** híbrido — parte **análise/estratégia/dados de growth**, parte **construção de ferramenta/software**.
- **Fase atual:** **Fase 1 → v1 construída e corrigida (Modo B).** Os três módulos existem e passam nos testes. Ponto frágil nº 1 (Vendas×CMV) **resolvido** em 2026-07-02: CMV conta só pedidos da aba `Vendas` (a `Itens` tem outros canais) — ADR `2026-07-02-cmv-so-pedidos-da-aba-vendas`.
- **Fonte de custo — CASCATA DE 3 ABAS (2026-07-22):** custo por SKU vem da aba **3.2** (`634911340`, col `PREÇO JUNHO`; tabela atualizada do Financeiro, subida pelo João), com a **3.1** (`1460088128`, `Custo`) e a **3** (`423190064`, `Valor de Custo`) como redes de segurança em cascata — 1º valor > 0 vence; `custos_extra.csv` por cima. Ordem em `dados.FONTES_CUSTO`. Custo 0 = faltando, não grátis. **Só `dados.py` mudou** (`GIDS["Custos"]`/`GID_CUSTOS_FALLBACK` aposentados). Cobertura 1.617→**1.684** SKUs com custo (0 perderam). **Junho: MC R$2,174M→R$2,255M (+3,75%)** — nova âncora byte-idêntica de junho = **R$ 2.255.165,93**. Guarda 7/7 + AppTest 7 telas OK. NÃO mexeu em `PARAMETROS` nem no CMV estimado 30%. ADR `2026-07-22-fonte-custos-3-2` (supera o `2026-07-09-fonte-custos-3-1-com-fallback` no topo da cascata).
- **Percentuais da DRE atualizados (2026-07-22):** na mesma sessão o Financeiro passou % novos → `cascata.PARAMETROS`: PIS/COFINS 1,75→**4,74**, ICMS 12,54→**13,73**, Devoluções 3,48→**3,32**, Frete 4,80→**5,02**, Gateways 1,70→**1,37**, Plataforma 0,90→**0,44**, Antecipação 1,60→**1,10** (Chargebacks igual). **Embalagem (0,57) e Outras Deduções (0,00) NÃO vieram na lista → mantidas (Embalagem CONFIRMADA pelo João 2026-07-22).** Soma 27,49%→**30,44%**. **MC de junho (custo 3.2 + % novos) = R$ 2.010.121,79** (nova âncora; era 2.173.703,35 → −7,5% líquido). Guarda 7/7 + AppTest OK. Spec `2026-07-22-parametros-dre`.
- **Dobra de kit — RESOLVIDA (2026-07-09):** a explosão de kit em dobro (que inflava o CMV e subestimava a MC em ~R$100k/mês em junho) foi **corrigida na fonte e já está live na planilha** (informado pelo João; não reverificado a pedido dele). O paliativo do painel (`cascata.SKUS_KIT_VIRTUAL`) foi **aposentado** — com a fonte corrigida, mantê-lo passaria a subtrair custo legítimo (MC inflada). Fonte de itens do painel = Vendas Shopify (gid 1246117066, com nomes). A NF (gid 488044140) segue parkeada p/ receita fiscal v2+. A `docs/orientacao-base-itens-confiavel.md` tinha a dobra como motivo principal — essa parte está atendida; melhorias residuais (brindes, kit explodido uma vez) ficam a confirmar.
- **Direção de médio prazo (definida 2026-07-04):** evoluir o painel de MC até o modelo "Motor de Crescimento Lucrativo" (True Classic). **Escopo comprometido: V1→V4** (cliente novo×recorrente → custo cheio por pedido → lucro por cliente novo + coortes); V5-V7 parkeados até rodar o modelo. Mapa completo: `docs/ROADMAP.md`. ADR: `docs/decisions/2026-07-04-roadmap-motor-crescimento.md`.
- **V2 em spec (discovery + handoff feitos 2026-07-09):** o `PRODUCT.md` avançou para a **V2 = aba de aquisição** (V1 arquivado em `docs/product-history/PRODUCT-v1.md`). Decisão-chave: a chave de cliente é o **campo nativo `customer_type` da Shopify** (`Primeira Compra`/`Recompra`, já na aba `Vendas`, automático) — **não** e-mail construído; point-in-time + histórico completo → **sem viés de borda esquerda**. A aba mostra 5 KPIs só de cliente novo: **MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS**. Convenção registrada: **100% da mídia → novos** (ajustável; V4 refina). Régua: "MC positiva na 1ª compra" (linha do zero, verde/vermelho); LTV/coorte e a coluna de recompra ficam pra depois. Vocabulário: **MC, nunca "lucro"**. ADR `2026-07-09-v2-aquisicao-customer-type-shopify`; log `docs/sessions/2026-07-09-discovery-v2-aquisicao.md`.
- **V2 CONSTRUÍDA e verificada (2026-07-09, tarde):** a aba de aquisição existe e roda — `pages/2_Aquisicao.py` + `cascata.calcular_aquisicao` + `dados.carregar_vendas` lendo `customer_type`. Página nova no menu lateral; 5 cartões (MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS) + mini-cascata + linha do zero (verde/vermelho); guarda silenciosa da amarração; mídia inteira nos novos (100%→novos). Painel V1 intocado. Verificado ao vivo (junho: MC-novos +R$237.855, CAC R$189,72, aROAS 2,74) e por `AppTest` (sem regressão). Spec `docs/specs/2026-07-09-v2-aba-aquisicao.md`; log `docs/sessions/2026-07-09-spec-v2-aba-aquisicao.md`.
- **Decisão fechada (2026-07-09):** ausência do `customer_type` → **trava a leitura inteira** (falha barulhenta; trocar p/ "só desativa a aba" é 1 linha).
- **V4 com SPEC escrita — build pendente (spec feita 2026-07-10, tarde):** a **V4 = aba de coortes de recompra** (V2 arquivado em `docs/product-history/PRODUCT-v2.md`). Domínio: **fonte nova = HubSpot no BigQuery** `silver_deals_minimal` (filtro `etapa_do_negocio IN ('Shipped','Negócio Fechado - Comercial')` = Shopify; o Comercial, 1,2%, é sempre estimado — grava o nome do cliente no `nome`), base oficial de cliente/1ª-compra (chave `e_mail`); **coorte** = mês de `data_primeira_compra` (**cross-canal**, viés aceito); métrica = **MC acumulada por cliente** (mídia inteira no m+0; **cruzar o zero = a turma se pagou**); tela = **triângulo** (`Safra | Clientes | CAC | m+0…`) + **curva** das últimas 12 safras + **seletor**; **recompra em 90 dias**; **safra fechada**. **V3 esvaziada** (custos em %) → build pula V2→V4; a curva leva rótulo **"MC parcial"** (CX/juros/criativo ficam de fora). **Arquitetura DECIDIDA (MVP = Opção 2):** BigQuery vira **torneira** (João puxa a base HubSpot 1×/mês → `hubspot_deals.csv` local), **cálculo na plataforma** reusando a receita de custo do painel (uma verdade de custo); **CMV real só na janela de itens atual (abr–jul/2026), 25% estimado antes** (marcado célula a célula); ponte pelo **`nome`** (a base HubSpot **não tem** o gid — `id` é interno do HubSpot). Mídia = `investimento_total` (crua) + imposto FB **só de 2026-01 em diante**. Os 25% = `0,25 × valor` (sem deduzir de novo — corrigido). Spec `docs/specs/2026-07-10-v4-coortes-recompra.md`; ADRs `2026-07-10-v4-coortes-recompra-hubspot` (domínio) e `2026-07-10-v4-arquitetura-mvp-coortes` (arquitetura); logs `docs/sessions/2026-07-10-discovery-v4-coortes.md` e `2026-07-10-spec-v4-coortes.md`.
- **V4 CONSTRUÍDA e verificada (2026-07-10, tarde/noite):** a **aba de coortes** existe e roda — `pages/3_Coortes.py` + `coortes.calcular_coortes` + `dados.carregar_hubspot` lendo `bases/hubspot_deals.csv` (462k deals). Triângulo + curva (Altair) + seletor; MC real via ponte `nome→Vendas→Itens` (reusa `cascata.cmv_por_pedido` — refactor `juntar_custos`, **uma verdade de custo**), estimada 0,25×valor fora da janela (92,5% estimada no MVP; célula a célula). **Amarração provada:** MC real por pedido = Lucro Bruto do painel/Auditoria (max |dif| = 0). V1/V2 **byte-idênticas**. `AppTest` sobe as 3 páginas sem exceção. **Achado que contraria a spec:** `meses_desde_primeira_compra` do HubSpot **não é a idade do deal** (é a idade do CLIENTE no export) — a idade da coorte é **calculada** (meses-calendário entre `data_de_fechamento` e a 1ª compra). Calibração §9 rodada: viés cross-canal **0,87%** (imaterial); 2ª compra mediana **123 dias** (só 42% em ≤90d — considerar 90d+180d). Spec `docs/specs/2026-07-10-v4-coortes-recompra.md`; log `docs/sessions/2026-07-10-construcao-v4-coortes.md`.
- **V4 + AUDITORIA POR SAFRA (2026-07-12):** a aba Coortes ganhou **"🔍 Auditar a MC de uma safra"** (toggle) — abre a **cascata** (Receita → 10 deduções % → CMV → Lucro Bruto → + MC estimada → mídia m+0 → MC/cliente), a **cascata por idade** e o **download CSV** dos deals (sem e-mail; chave = número do pedido). **Não muda a matemática** — re-expõe a mesma `mc_produto` via `coortes._preparar_deals` (compartilhado com o triângulo). **Reconcilia** com o triângulo nas 64 safras (✅ na tela). Spec `docs/specs/2026-07-10-v4-auditoria-por-safra.md`; log `docs/sessions/2026-07-12-auditoria-por-safra.md`.
- **REBASE geral + aquisição no HubSpot (2026-07-14):** o painel geral (V1) e a aquisição (V2) passam a mostrar **qualquer mês** (2021→hoje) lendo o HubSpot. **Roteador pela borda da janela de Vendas:** dentro (abr–jul/2026) = lógica de sempre (real, planilha) — **byte-idêntico** (junho MC R$ 2,05M, MC-novos R$ 237k, provado com/sem `deals`); fora = HubSpot **estimado** (margem de produto = 25% do `valor`), somado à parte real, com rótulo `real`/`estimada`/`mista` e linha "Margem estimada" na cascata (amarela). `hubspot_deals.csv` ausente → volta ao de hoje (não quebra). `calcular`/`calcular_aquisicao` ganharam `deals=`; motor `_deals_estimados`. ADR `2026-07-14-rebase-geral-aquisicao-hubspot`; spec `docs/specs/2026-07-14-...`; log `docs/sessions/2026-07-14-...`.
- **UNIFICAÇÃO no HubSpot — painel geral E aquisição viram DEALS-BASED (2026-07-14, final):** decisão do João de **unificar tudo no `valor` do HubSpot**. `calcular`/`calcular_aquisicao` agora leem os deals: **Vendas = Σ`valor` por `data_de_fechamento`**, **CMV real via ponte** (item a item) na janela de itens, **25%** fora. **Bate com o filtro direto da base** (aquisição-novos ao centavo: abr 3,13M / mai 4,15M / jun 4,36M). `valor` é sempre ≥ `net` (a diferença é **frete**, que o João aceita como receita). **CMV segue item a item** (foi a condição do João). **Consequência:** os números mudam vs o net antigo — **painel junho MC 2,05M→2,15M (+4,8%)** (valor+frete e entra o Comercial). Fallback: `deals=None` → motor antigo (net). `_cascata_de_deals` em `cascata.py`. **Decidido (João):** (1) **Comercial fica** no painel (bate com a base; título "(Shopify)" a revisar); (2) **coorte alinhada ao `valor`** — `coortes._mc_produto_por_deal` usa `valor` (não net) na parte real (receita=valor nos dois ramos; safra 2026-06 MC/cliente 62,55→67,98; reconciliação intacta). Agora as **3 telas** usam a mesma régua (valor+fechamento+CMV real na janela). ADR `2026-07-14-rebase-geral-aquisicao-hubspot` §5-bis.
- **INTERFACE + CMV ESTIMADO 30% (2026-07-14, 2ª sessão):** (1) **Menu** virou programável — `painel.py` é só **roteador** (`st.navigation`), telas em **`views/`** (a pasta `pages/` sumiu): **1. Geral · 2. Aquisição · 3. Cohorts · A1 - Auditoria Custos**. (2) **Cascata única:** o DRE saía de 6 lugares diferentes; agora vem todo de **`cascata.montar_cascata`** + **`ui.tabela_dre`**, no formato `Vendas → (−) Deduções [5 linhas] → (−) Cost of Delivery [CMV + 5] → (=) Lucro Bruto → (−) Mídia Paga → (=) MC` (subtotais de grupo em cinza = **apresentação**, não mudam número). (3) **Aquisição:** 6 cartões (Vendas novos · Ad Spend · aROAS Shopify · **Ticket Médio** — novo · nº Pedidos · CAC). (4) **REGRA NOVA (dinheiro):** onde falta item, **CMV = 30% da receita** e as deduções seguem as fórmulas de sempre → margem de produto estimada **42,5%** (era "margem de 25%", um chute pessimista: o real medido é 28,8–29,0% de CMV e ~43% de margem). **Junho 2.152.168 → 2.173.703** (+1,0%, só a fatia do Comercial); **meses históricos e coortes antigas sobem bastante**. Provado: subtotais batem (dif 0), reconciliação coorte↔triângulo exata nas 63 safras, 4 telas sobem no `AppTest`. ADR `2026-07-14-cmv-estimado-30-por-cento`; spec `2026-07-14-interface-menu-cascata-cmv-30`.
- **TELAS DE COORTE (2026-07-14, 3ª rodada):** a aba **3. Cohorts** perdeu a **curva de payback** e ganhou **3 tabelas**: **Receita por cohort** (`Cohort | Novos Clientes | CAC | Receita 1ª Compra | LTV m+0…`; LTV = receita acumulada/cliente, bruta), o **triângulo de MC por cliente** ("Cohort" no lugar de "Safra" + coluna nova **MC primeira compra** = margem do 1º pedido **já com a mídia**) e o **triângulo de MC absoluta** (R$ cheios da turma). A auditoria por safra virou a página **A2 - Auditoria MC Cohort**. Peças comuns em `coortes_ui.py`. Ressalva medida: uma fatia pequena de clientes (≤0,42% nas safras recentes; 7,5% em 2022) tem a 1ª compra **fora** da base (viés cross-canal) — o 1º pedido dela nasce em m+1/m+2.
- **RÉGUA ÚNICA DE "CLIENTE NOVO" = o carimbo do HubSpot (2026-07-14, 3ª rodada):** o João viu Aquisição × A2 divergindo. Causa: réguas diferentes (Aquisição = carimbo `tipo_de_venda`; coorte = 1ª compra derivada). **Decisão do João: usar a definição da FONTE — o carimbo `tipo_de_venda`** (`cascata.mascara_cliente_novo`), agora nos DOIS lados (Aquisição + bloco de novos da coorte/A2 + coluna "MC primeira compra"). **Junho não muda na Aquisição** (Vendas-novos R$ 4.361.515,03, MC-novos R$ 452.861,30, 8.180 pedidos). **Ressalva medida e aceita:** o carimbo erra nas bordas (59 primeiras compras marcadas "Recompra"; 62 "Primeira Compra" que não eram o 1º pedido — ~R$ 10,8 mil, 0,25%); espelhamos o HubSpot, não o corrigimos. **Resíduo Aquisição × A2 = R$ 3.628 (0,08%, 5 pedidos)**: a coorte só conta quem ESTREOU no mês; a Aquisição conta todo pedido carimbado no mês — divergência inerente (período × turma). **Junto:** a coorte passou a aplicar as **exclusões AnjosFrach** (ADR 2026-07-02) que só o painel aplicava. ADR `2026-07-14-regua-unica-cliente-novo`.
- **BLINDAGEM DO LEITOR (2026-07-14):** o Google devolve, de vez em quando, **HTTP 200 + `text/csv` com a planilha VAZIA** (só vírgulas, sem cabeçalho — 840 KB no lugar de 3,5 MB). Aconteceu **3× num dia**; virava o erro confuso "a aba Vendas está sem a coluna order_id". `dados._ler_csv` agora detecta (todas as colunas `Unnamed:`) e **tenta de novo**.
- **CMV REAL NA HISTÓRIA INTEIRA (2026-07-14, 3ª sessão):** o CMV deixou de ser chutado em 30% no passado. Base nova **`bases/itens_historico.csv`** (export do BQ, 1,3 M linhas, 2021-10→hoje, 495 mil pedidos). Itens resolvidos em **3 camadas** (`cascata.itens_por_nome`): **histórico → planilha (a ponta viva; o export é uma foto) → 30%**. Ponte **direta** pelo número (`hubspot.nome == itens.order_name`; `#` dos dois lados). **Junho byte-idêntico** (MC R$ 2.173.703,35; provado ao centavo nos 39.212 pedidos da janela). **TRAVA DE DINHEIRO descoberta na construção:** só **`Shipped`** casa itens — o **Comercial** grava no `nome` um número de **outra numeração que COLIDE** com pedidos Shopify antigos (defasagem mediana **92 dias**; 37 deals de junho iam herdar o CMV de janeiro). O código antigo escapava **por sorte** (casava via `Vendas`, onde o Comercial não está). **Impacto:** **MC 2022 cai 24,4%** (CMV real = 35,8%, o chute era otimista); 2023 −0,6%; 2024 −2,2%; **2025 +1,4%**. **O 30% fixo escondia os meses de promoção** (jul/2022 = 41,3% com ticket de R$ 167; Black Friday = 40,5%) — por isso a direção depende do **mês**, não do ano (a coorte 2022-06 SOBE, de R$ 42,35 → R$ 50,33/cliente). Resíduo medido: **6,4% das unidades de 2023 sem custo cadastrado** (CMV parcial → MC otimista); 2021 segue estimado (a base começa em out/2021). Arquivo ausente = **degrada** para o comportamento anterior (provado). ADR `2026-07-14-cmv-real-historico-3-camadas`.
- **RATIOS CONTRA O CAC na aba Cohorts (2026-07-14, 4ª rodada):** a aba **3. Cohorts** ganhou 2 títulos de seção ("LTV e CAC por Cohort (Receita)" e "LTV MC e CAC por cohort (Margem de contribuição)") e **2 tabelas de múltiplos do CAC**: **LTV ÷ CAC** (receita bruta) e **Lucro Bruto ÷ CAC**. Verde em gradiente **por coluna** (o m+7 de um cohort contra o m+7 dos outros; a coluna da 1ª compra também pintada); o CAC fica em R$ (é o denominador). **REGRA DE DINHEIRO (achado do João): o ratio usa LUCRO BRUTO, nunca a MC** — a MC **já desconta a mídia**, então `MC ÷ CAC` contaria a **mídia duas vezes**. **O empate é `1,00×`**, não zero (abaixo disso = não pagou a própria mídia, número em vermelho). Safra 2026-06: o ratio errado dizia 0,40×; o certo é **1,40×**. `ResultadoCoortes` ganhou `lucro_bruto` + `lucro_bruto_primeira_compra` (tirados do incremental **cru**, não somando o CAC de volta na tela). **Provado:** `lucro_bruto = mc_acumulada + CAC`, dif **0** nas 64 safras → virou o **check nº 5 do `checar_coerencia.py`**; a linha do `1,00×` coincide com o payback do triângulo (0 células divergentes). A página **A3 (coortes de Lucro Bruto)** foi pedida e **descartada** pelo João na mesma sessão (redundante). ADR `2026-07-14-ratio-contra-cac-usa-lucro-bruto`; spec `2026-07-14-coortes-titulos-e-ratios`; log `docs/sessions/2026-07-14-coortes-ratios-cac.md`.
- **FEATURE "PORTAS DE ENTRADA" — CONSTRUÍDA e verificada (2026-07-15, 3ª sessão):** a aba **"4. Portas de entrada"** existe e roda — motor novo **`portas.py`** (reusa `coortes.py`), aba `views/portas_entrada.py`, `dados.carregar_mapa_portas`, item no menu depois da Cohorts, e **check nº 6** no `checar_coerencia.py`. Segmenta a coorte pela **linha de produto da estreia** e mostra o **Lucro Bruto acumulado/cliente** (célula = `coortes.lucro_bruto`; CAC = **blended**, nunca por produto) em `1ª compra | 30D | 60D | 90D | 180D | 365D` (apelidos de m+0/m+1/m+2/m+5/m+11). Duas tabelas: **por safra** (filtro de produto; "todos" = idêntica à Cohorts) e **por linha** (filtro de data; cada janela usa só as safras maduras). **NADA de verdade nova de custo/CAC — só a dimensão `porta`.** Porta = linha da 1ª compra (deal mais antigo; ponte `nome→itens 3 camadas→mapa`); brinde **e** "sem nome" removidos como ruído → 1 linha = essa porta, >1 = "Multiprodutos", 0 (só ruído/Comercial/cross-canal/pré-out-2021) = "Produto desconhecido". **Provado:** `portas("todos")` = `coortes.lucro_bruto` **ao centavo** (dif 0,0 nas 64 safras) + partição intacta (0/64 perdem cliente) → **7/7 no guarda**; `AppTest` sobe as **6 telas**. **Detalhe em aberto RESOLVIDO (decisão do João):** "sem nome" é **ruído** → `camiseta + sem-nome = "Camiseta"` (impacto medido: 6.727 estreias, **2,47%**; flag de 1 linha p/ inverter). Régua **Lucro Bruto PARCIAL** (rotulada). ADR `2026-07-15-portas-de-entrada-produto`; log `docs/sessions/2026-07-15-construcao-portas-de-entrada.md`. **Reiniciar o painel** (módulos novos, watchdog não instalado). **[2026-07-16 — João testou ao vivo + 3 ajustes]:** (1) **switch de leitura** na aba 4 — *Valor total (R$)* × *Aumento vs 1ª compra (×)* (célula ÷ 1ª compra da linha, base 1,00×; lente de display, guarda intacto); (2) **tabela por linha ordenada por clientes** (baldes no fim); (3) a tabela por linha **não é monotônica de propósito** (composição — cada janela usa só as safras maduras; a queda Jeans 2.0 30D→60D é troca de turma, não de valor) → **Opção 1** (mais dado + **texto explicativo na tela**: "leia por coluna, não por linha" + exemplo). Guarda **7/7**; `AppTest` OK nos 2 modos. ADR §6; backlog: mostrar N por coluna + Opção 2 como 2º switch. **[2026-07-16 — métrica Receita]:** a aba 4 ganhou um **seletor de métrica** (Lucro Bruto × Receita) que troca o conteúdo das 2 tabelas (decisão do João: troca, não empilha). Motor `portas.py`: as 4 builders aceitam **`metrica`** (default `"mc_produto"`=LB; `"valor"`=Receita bruta) — **nenhuma conta nova**, só troca a coluna somada; Receita não desconta mídia/custo. **Provado:** `portas("todos", metrica="valor")` = `coortes.ltv` ao centavo (dif 0,0 nas 64 safras) — o **check nº 6** agora prova as **duas** métricas; guarda **7/7**; `AppTest` sobe a aba nos 2 modos. Log `docs/sessions/2026-07-16-portas-metrica-receita.md`.
- **A3 — AUDITORIA DAS PORTAS (drill-down por cliente) (2026-07-16):** aba de anexo nova **"A3 - Auditoria Portas"** (`views/auditoria_portas.py` + `portas.auditar_portas`). Fluxo (desenho do João): escolhe a **porta** → **lista** os clientes dela (1 linha/cliente, estilo A1, `st.dataframe` on_select) → **clica e abre a linha do tempo de compras** do cliente (produtos de cada compra + o período m+x). Foco em **Multiprodutos** e **Produto desconhecido**. **Nenhuma verdade nova de dinheiro** — reusa a coluna `porta` de `calcular_portas`; a régua nova é o **MOTIVO** do desconhecido (4 baldes: Comercial 1.801 · fora da base 1.912 · **sem itens casados 11.721** · só brinde/sem-nome 6.279 — os 2 últimos, 18k = 6,5%, são os *recuperáveis*: pedido Shopify no prazo que não virou porta). **Privacidade:** nunca mostra e-mail (array paralelo, fora da tela); no Comercial o `nome` é a PESSOA → mascarado "(Comercial)". **Trava §11:** o drill-down **não** casa itens de deal não-`Shipped` (numeração do Comercial colide → traria itens de OUTRO pedido; corrigido na construção). Partição CA4 intacta; guarda **7/7**; `AppTest` sobe a A3 sem exceção; ramo do clique exercitado nos 4 casos. Spec `docs/specs/2026-07-16-auditoria-portas-drilldown.md`; log `docs/sessions/2026-07-16-a3-auditoria-portas.md`. **Reiniciar o painel** (módulos novos). **[Multiprodutos por combinação, mesma sessão]:** 30k clientes não se olham um a um → quando a porta é Multiprodutos, a A3 mostra primeiro a **tabela de combinações de linha da estreia** (ranqueada por clientes; `combo` novo em `auditar_portas`), e **clicar numa combinação** filtra a lista → drill-down por cliente. Revelado: 30.632 Multi = só 1.361 combos (81% pares), Camiseta Minimal em 84%; top "Calça Jeans 1.0 + Camiseta Minimal" 4.058. Guarda 7/7; `AppTest` OK. Backlog restante: mesma agregação por **SKU não mapeado** para "Produto desconhecido".
- **COMBINAÇÕES VIRAM PORTAS (2026-07-16):** decisão do João — uma **combinação de linhas (≥2)** vira **porta de entrada própria** quando tem **≥ 1.000 clientes de estreia** (`portas.LIMIAR_COMBO_PORTA`); abaixo, segue "Multiprodutos" (cauda). Vale em **todo o painel** (muda a coluna `porta`): as **6 combinações** promovidas (maior: *Calça Jeans 1.0 + Camiseta Minimal*, 4.058) viram linhas na **aba 4** (por safra/por linha, LB e Receita) e portas na **A3**. Classificação refatorada (`_combo_por_pedido` + `_porta_do_combo` + `_combos_promovidos`; data-driven, sem lista curada). **Re-partição limpa** (só as 6 combos trocam de balde; Multiprodutos 30.632→14.546; *desconhecido* 21.713 e *Camiseta Minimal* 193.616 **inalterados**; total preservado). Guarda **7/7** (partição 0/64 + "todos" = Cohorts nas 2 métricas ao centavo); `AppTest` sobe aba 4 e A3. Tuning = 1 constante. ADR `2026-07-16-combinacoes-viram-portas`. **[2 fixes vistos ao vivo]:** (1) **privacidade** — alguns deals `Shipped` (0,03%) trazem **nome de pessoa** no `nome`; a A3 agora mascara qualquer `nome` não-numérico ("(sem nº)"), zero PII na tela; (2) **estreia** — novo `portas._estreias` desempata mesma-data preferindo o pedido que **TEM produto** (linha `porta`), senão um cliente com pedido-sem-itens no mesmo dia caía em "desconhecido" (caso #14461 → agora Camiseta Minimal). Só melhora (desconhecido 21.713→21.654, 59 resgatados); Multiprodutos intacto; guarda 7/7.
- **FEATURE "PORTAS DE ENTRADA" — spec + mapa validados (discovery 2026-07-15, 2ª sessão) — BUILD JÁ FEITO (ver bullet acima):** discovery de uma **aba nova ("4. Portas de entrada")** que lê o **Lucro Bruto acumulado por cliente por PORTA DE ENTRADA** (produto da 1ª compra) em janelas `1ª compra | 30D | 60D | 90D | 180D | 365D` — **mesma régua da Cohorts** (os "D" são apelidos de m+0/m+1/m+2/m+5/m+11; nenhum ADR de divergência). Duas tabelas (principal por safra obedecendo o filtro de produto; secundária por linha de produto obedecendo o filtro de data), célula = **Lucro Bruto/cliente** (reusa `coortes.lucro_bruto`), CAC = blended do mês (régua), safra imatura = "—", **N mínimo 300**. O **Fable** (subagente) verificou o dado e cortou **canal e oferta** (não há colunas na base → backlog). Nasceu a régua **`bases/mapa_sku_linha_produto.csv`** (SKU→linha, papel porta/brinde/desconhecido; **26 linhas-porta**, validada à mão pelo João). Produto de entrada = **linha de produto**, categoria única (brindes removidos antes; sem produto → "Produto desconhecido"). **1ª leva = só produto.** Ressalva: régua ainda **Lucro Bruto parcial** (sem devolução/CX/juros/criativo). Spec `docs/specs/2026-07-15-portas-de-entrada-produto.md`; backlog novo **`docs/BACKLOG.md`**; log `docs/sessions/2026-07-15-portas-de-entrada.md`. **Próximo passo:** construir `views/portas_entrada.py` + motor (reusa `coortes.py`) + check de coerência ("todos" = idêntico à Cohorts).
- **Recarregar o painel:** o `watchdog` **não** está instalado → quando um **módulo** muda (`cascata.py`, `coortes.py`, `coortes_ui.py`, `ui.py`), o Streamlit recarrega a página mas **mantém o módulo velho em memória** (vira `TypeError` de assinatura). **Mexeu em módulo → reiniciar o painel.** (`pip install watchdog` resolveria — dependência nova, não instalada sem o ok do João.)
- **Próximo passo concreto:** (1) **João roda ao vivo** (`python3 -m streamlit run painel.py`) e testa escolher **meses passados** no painel/aquisição (vêm com faixa amarela de estimado) + a V4 (aba Coortes, toggle de auditoria). (2) **Docs a montante — FEITO nos docs vivos (2026-07-15):** o `PRODUCT.md` já estava certo no grosso (idade calculada §3; 30% §6); nesta sessão corrigi 3 resíduos vivos (idade não vem de `meses_desde_primeira_compra` nos §4/Fluxo A; receita = `valor` decidida, não "a confirmar", §4/§8). A **spec V4 fica congelada** (regra do §6: spec é foto do dia; ADR corrige o rumo) — decisão do João. A frase "84 de 37.593" só sobrevive em arquivo/log congelados (nada a fazer). Também reescrevi o §8 (linhas 217-218), que descrevia o CMV real como "só abr–jul/2026" — agora reflete que o CMV real cobre **out/2021→hoje** nas 3 telas (3 camadas), com resíduos medidos (2021 estimado; ~6,4% das unidades de 2023 sem custo). (3) Afinar o cartão de recompra para **90d + 180d** (calibração V3). (4) **Opção 1 — FEITA (2026-07-14):** a "MC real ano-a-ano desde 2022" era a Opção 1, entregue pelo "CMV real na história inteira em 3 camadas" (a spec `2026-07-14-cmv-real-historico-3-camadas` diz isso com todas as letras). Sobra só **afinar resíduos**: 2021 ainda estimado (base começa out/2021) e ~6,4% das unidades de 2023 sem custo cadastrado. (5) Pendências herdadas: `docs/skus-custo-zerado-aba-3-1.csv` (137 SKUs) ao time de Dados; re-base da V2 no HubSpot (prompt guardado).
- **Ambiente:** Python 3.13, pandas 3.0, `certifi` e `streamlit` instalados. `streamlit` não está no PATH → rodar com `python3 -m streamlit run painel.py`.
- Coração do v1: **ver a MC de um período fechado, correta, sem esperar o Financeiro.**

> Quando o projeto avançar, **atualize esta seção 0** com a fase e o próximo passo. É o primeiro lugar que qualquer sessão olha.

---

## 1. Os 3 mantras (inquebráveis)

1. **Toda sessão começa lendo este `CLAUDE.md` e o `ARCHITECTURE.md`** (quando existir). Sem exceção.
2. **Toda sessão termina atualizando `ARCHITECTURE.md` e criando um log em `docs/sessions/`.** Sem exceção.
3. **Spec/plano antes de produzir, sempre que o trabalho toca regra de negócio, dinheiro ou dado.** Atalho só em coisa cosmética.

Se eu me pegar pulando os três, é débito técnico em formação — paro e aviso o João.

---

## 2. Estilo de comunicação (obrigatório em todo output)

Seguir [`vibe-coding-workflow/principios/comunicacao-com-usuario.md`](vibe-coding-workflow/principios/comunicacao-com-usuario.md):

- **Analogia primeiro, termo técnico depois** (entre parênteses, no fim).
- **Nunca explicar jargão com mais jargão.** Se a explicação precisa de 3 termos novos, virou aula — reescrever em linguagem comum.
- O João entende lógica avançada, mas ainda está construindo vocabulário de dev. O termo aparece para ele aprender — só nunca aparece sozinho.

---

## 3. Modo híbrido — dois modos de trabalho

Este projeto alterna entre dois modos. **Identifique o modo no início da sessão** e siga o trilho correspondente.

### Modo A — Análise / Estratégia / Dados
Modelagem de receita, diagnóstico de growth, revisão de estratégia, etc.
- O "produto" da sessão é um **documento/modelo/análise**, não código de produção.
- Antes de qualquer análise que vire decisão: escrever um **plano de análise** curto (equivale à *spec*) em `docs/specs/` — pergunta, dados de entrada, método, o que conta como resposta.
- `ARCHITECTURE.md` aqui descreve **as fontes de dados, os modelos e como os números se conectam**, não módulos de software.
- Skills úteis: `revisar-dados`, `revisar-estrategia`, `devil-advocate`, `simplificar`, `copiar-para-sheets`.

### Modo B — Construção (software/ferramenta)
Quando virar app, automação ou ferramenta interna.
- Segue o ciclo de feature padrão do trilho (Fase 3): spec → validar → validar contexto → implementar → testar → atualizar docs.
- Aí valem as convenções técnicas do `vibe-coding-workflow/templates/CLAUDE.md.template` (nomenclatura, tamanho de função, tipos, erros). **O stack só é decidido na Fase 1**, com o João, e registrado aqui na seção "Stack".

> Os dois modos compartilham a mesma disciplina de documentos vivos: `docs/specs/`, `docs/decisions/`, `docs/sessions/`. O que muda é o conteúdo, não o ritual.

---

## 4. Ritual de início e fim de sessão

**Início (sempre):**
1. Ler este `CLAUDE.md` (e `ARCHITECTURE.md` + `PRODUCT.md` quando existirem).
2. Confirmar ao João, em 1 frase, o estado/fase e o objetivo da sessão.
3. Identificar o modo (A ou B) e qual checklist do guia se aplica.

**Fim (sempre):**
1. Atualizar `ARCHITECTURE.md` refletindo o que mudou (quando já existir).
2. Criar `docs/sessions/AAAA-MM-DD-[tema].md` (modelo: `vibe-coding-workflow/templates/session.md.template`).
3. Se houve decisão duradoura → `docs/decisions/AAAA-MM-DD-[tema].md` (modelo: `decision.md.template`).
4. Log em linguagem que o João entende relendo daqui a 2 semanas.

> Sessão fechada sem atualizar `ARCHITECTURE.md` e sem log = **sessão incompleta**.

---

## 5. Árvore de decisão — qual checklist usar

```
Projeto novo / sem PRODUCT.md?   → vibe-coding-workflow/02-checklist-novo-projeto.md   (estamos AQUI)
Retomando após pausa (>3 dias)?  → vibe-coding-workflow/prompts/11-retomar-projeto.md
Feature/análise nova?            → vibe-coding-workflow/03-checklist-nova-feature.md
Já fiz 3-5 entregas sem revisar? → vibe-coding-workflow/04-checklist-revisao.md
Qualquer outra sessão           → vibe-coding-workflow/01-checklist-sessao.md
```

Prompts prontos para copiar/colar: `vibe-coding-workflow/prompts/`.
Templates dos documentos: `vibe-coding-workflow/templates/`.

---

## 6. Documentos vivos (não são opcionais)

| Documento | O que é | Quando criar | Quando atualizar |
|---|---|---|---|
| `PRODUCT.md` | Visão de produto e domínio | Fase 0 | Quando o produto muda |
| `CLAUDE.md` (este) | Manual de operação do agente | Fase 1 | Quando convenções mudam |
| `ARCHITECTURE.md` | Mapa vivo do sistema/modelo | Fase 1 | Fim de toda sessão |
| `docs/specs/[nome].md` | Spec/plano antes de cada entrega | Antes de produzir | — |
| `docs/decisions/[tema].md` | Decisão duradoura (ADR) | Quando se decide | — |
| `docs/sessions/[data].md` | Log da sessão | A cada sessão | Nunca (é log) |

---

## 7. Comportamento inviolável do agente

1. **Pergunto antes de assumir.** Se eu for inferir algo do domínio, eu paro e checo a origem (`PRODUCT.md`? ou inferência minha?).
2. **Uma coisa por vez.** Se a tarefa crescer ("já que estou aqui..."), eu anoto no log e mantenho o foco do objetivo.
3. **Nunca produzo número/regra de negócio sem rastrear a fonte.** Em análise: de onde veio o dado. Em código: de onde veio a regra.
4. **Se achar inconsistência entre `ARCHITECTURE.md` e a realidade, paro e relato.** Nunca silencio.
5. **Não toco arquivos fora do plano sem perguntar.** Não adiciono dependência/ferramenta nova sem perguntar.
6. **Code/analysis review por amostragem:** ao terminar, explico 1-2 trechos "em linguagem de negócio". Se a explicação sai confusa, o trabalho está confuso — refaço.
7. **Refatoração grande / mudança de método = sessão dedicada com ADR antes.**

---

## 8. Stack e convenções técnicas (Modo B)

Decidido em 2026-07-01 (ADR `docs/decisions/2026-07-01-stack-streamlit-planilha-unica.md`).

- **Linguagem/ferramenta:** Python + **Streamlit** (painel) + **pandas** (cálculo). Roda local no Mac do João.
- **Fonte de dados:** uma **planilha Google única** de 5 abas, lida ao vivo via URL de export CSV (sem API/credencial). O painel **nunca escreve na planilha compartilhada**; a única escrita é num arquivo **local** do João (`custos_extra.csv`, correções de custo feitas na tela — ADR 2026-07-02-editor-custos-arquivo-local).
- **Módulos:** `dados.py` (leitura/limpeza) → `cascata.py` (regras de MC — toca dinheiro, mexer com cuidado) → `painel.py` (UI).
- **Regras de cálculo:** são a fonte de verdade do `PRODUCT.md` (seção 6) e do spec; nunca produzir número sem rastrear a coluna/fonte.
- Convenções gerais de código (nomenclatura, tamanho de função, tipos, erros): seguir `vibe-coding-workflow/templates/CLAUDE.md.template` quando o código crescer.

---

## 9. Skills disponíveis neste ambiente

- `/revisar-dados` — revisão sênior de dados/modelagem de receita e-commerce.
- `/revisar-estrategia` — leitura de CMO sênior sobre a estratégia.
- `/devil-advocate` — consultor cético: fura premissas e aponta riscos.
- `/simplificar` — editor de clareza: enxuga qualquer documento.
- `/copiar-para-sheets` — converte CSV→TSV e copia pro clipboard (colar no Sheets/Excel).

---

## 10. Princípios de fundo (ler na 1ª vez)

- `vibe-coding-workflow/00-trilho-mestre.md` — as 5 fases, visão geral.
- `vibe-coding-workflow/principios/clean-code-llm.md`
- `vibe-coding-workflow/principios/prompt-engineering.md`
- `vibe-coding-workflow/principios/context-engineering.md`
- `vibe-coding-workflow/principios/comunicacao-com-usuario.md`

> Regra de ouro do trilho: documentação não é burocracia — é o mecanismo que dá controle sobre um projeto que não dá pra ler linha por linha.

---

## 11. Definições compartilhadas — INEGOCIÁVEL (2026-07-14)

> **Regra do João:** *todas as telas usam as MESMAS definições — data de fechamento, primeira
> compra, cliente novo, custo, mídia, exclusões. Os valores TÊM de bater entre as abas.* Divergir
> só com **ordem explícita** dele, e mesmo assim a divergência tem de estar **rotulada na tela** e
> registrada num ADR.

**Por que existe:** em 2026-07-14 o João viu a aba Aquisição e a A2 mostrando números diferentes
para o mesmo mês. Não era base diferente — eram duas telas com definições próprias de "cliente
novo". Isso corrói a confiança no painel inteiro: se dois números que deveriam ser iguais não são,
nenhum número é confiável.

**Cada definição tem UM dono no código. Nunca reescreva a regra na tela — chame o dono.**

| Definição | Dono (única fonte) | O que é |
|---|---|---|
| **Receita / Vendas** | `cascata._cascata_de_deals` | Σ `valor` dos deals do HubSpot |
| **Data do pedido** | idem | `data_de_fechamento` (HubSpot) — nunca a data da planilha quando há deals |
| **Cliente novo** | `cascata.mascara_cliente_novo` | carimbo `tipo_de_venda = "Primeira Compra"` **E** no mês da estreia do cliente |
| **Estreia / safra do cliente** | `coortes._preparar_deals` | mês da `data_primeira_compra` (mínimo por `e_mail`; cross-canal) |
| **Idade da coorte (m+x)** | idem | meses-calendário entre `data_de_fechamento` e a estreia |
| **CMV** | `cascata.juntar_custos` / `cmv_por_pedido` / `cmv_por_nome` | item a item; **30% da receita** onde não há itens (`CMV_ESTIMADO_FRACAO`) |
| **De onde vêm os itens** | `cascata.itens_por_nome` | **3 camadas**: base histórica → planilha → nada (=30%) |
| **Quem pode casar itens** | `cascata.pode_casar_itens` | **só deal `Shipped`**. O Comercial colide de numeração → sempre estimado |
| **Lucro Bruto por cohort** | `coortes.ResultadoCoortes.lucro_bruto` | MC **antes** da mídia. É o **único** numerador válido de ratio contra o CAC (a MC já desconta a mídia → contaria 2×). Empate = **1,00×** |
| **Deduções e custos %** | `cascata.PARAMETROS` via `montar_cascata` | incidem sobre a receita inteira |
| **Mídia (Ad Spend)** | `cascata._ad_spend_periodo` / `coortes._ad_spend_por_mes` | gross-up do FB (12,15%), só ≥ 2026-01 no histórico |
| **Exclusões de negócio** | `cascata._pedidos_excluidos` + `PEDIDOS_EXCLUIDOS_NOME` | AnjosFrach e pontuais saem de **todas** as telas |
| **Forma da cascata (DRE)** | `cascata.montar_cascata` + `ui.tabela_dre` | Vendas → Deduções → Cost of Delivery → Lucro Bruto → Mídia → MC |

**O guarda:** `python3 checar_coerencia.py` prova que as telas concordam (Aquisição × A2, A2 ×
triângulo, subtotais das cascatas, triângulo absoluto × por cliente). **Rodar sempre que mexer em
`cascata.py` ou `coortes.py`** — e antes de fechar a sessão.

**Quando a fonte se contradiz:** o HubSpot tem campos que brigam entre si (o carimbo dizia
"Primeira Compra" num mês diferente da estreia do próprio cliente, em 5 pedidos de junho). Nesses
casos, **elege-se um campo como mestre e registra-se no ADR** — não se deixa cada tela escolher.
Regra vigente: **a data de estreia manda** sobre o carimbo. ADR `2026-07-14-regua-unica-cliente-novo`.
