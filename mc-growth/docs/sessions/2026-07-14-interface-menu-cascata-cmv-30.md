# Sessão — Menu, cartões, cascata normalizada e CMV estimado em 30%

- **Data:** 2026-07-14 (2ª sessão do dia)
- **Modo:** B (construção)
- **Objetivo:** melhorias de interface pedidas pelo João (menu, cartões da aquisição, formato do
  DRE) — e, no meio do caminho, uma **mudança de regra de dinheiro**: o CMV estimado.
- **Spec:** `docs/specs/2026-07-14-interface-menu-cascata-cmv-30.md`
- **ADR:** `docs/decisions/2026-07-14-cmv-estimado-30-por-cento.md`

---

## O que o João pediu

1. Renomear e reordenar o menu (1. Geral · 2. Aquisição · 3. Cohorts · A1 - Auditoria Custos).
2. Trocar os cartões da aba de aquisição (6 cartões; MC-novos fica só como herói).
3. Normalizar **todas** as cascatas num formato só, com dois subtotais de grupo (**Deduções** e
   **Cost of Delivery**).
4. **No meio da conversa:** *"quando não tivermos a informação de custo, vamos estimar 30% no CMV.
   O restante das deduções segue as fórmulas definidas."*

## O que se descobriu antes de construir

- **A cascata estava escrita em 6 lugares** (4 em `cascata.py`, 2 em `coortes.py`), cada um
  remontando o DRE à mão. Padronizar a tela sem unificar a fonte só adiaria a divergência.
- **O 30% do João bate com o real.** Medi o CMV nos meses com itens: **29,0% (mai/2026)** e
  **28,8% (jun/2026)** da receita; o Lucro Bruto real é **42,8–43,0%**. A regra antiga estimava a
  margem de produto em **25%** — um chute **pessimista** em ~17,5 pontos. Mostrei o número ao João
  antes de mexer; ele confirmou o 30% (conservador) sabendo que **os meses históricos e as coortes
  antigas iam subir**.
- Um susto pelo caminho: a primeira leitura da aba `Vendas` voltou **sem cabeçalho** (soluço do
  Google). A segunda veio correta. O retry do `dados._ler_csv` existe, mas **não pega esse caso**
  (o CSV chega válido, só vazio) — anotado como fragilidade, não corrigido nesta sessão.

## O que foi feito

**Código**
- **`cascata.montar_cascata`** — a fábrica única do DRE. Os 6 lugares passaram a chamá-la.
- **`ui.py`** (novo) — `tabela_dre`: o **desenho** da cascata (cores, indentação, % da receita),
  antes copiado em 3 telas.
- **CMV estimado em 30%** (`CMV_ESTIMADO_FRACAO`), em `cascata.py` e `coortes.py`. A linha
  "Margem estimada (25%)" **deixou de existir**; quem carrega o ⚠️ agora é o **CMV**
  ("X% estimado a 30%").
- **`_deals_estimados`** (o roteador da borda da janela, do rebase de ontem) virou **código morto**
  com a unificação e foi **removido**.
- **Menu programável:** `painel.py` virou **roteador** (`st.navigation`); as telas foram para
  **`views/`** e a pasta `pages/` deixou de existir (senão o Streamlit descobre os arquivos sozinho
  e o menu duplica).
- **Aquisição:** 6 cartões na ordem pedida; nasceu o **Ticket Médio** de novos
  (`ResultadoAquisicao.ticket_medio`).

**Provas rodadas (critérios de aceite da spec)**
- **Subtotais** (CA3): soma das linhas filhas = subtotal do grupo, e `Vendas − Deduções −
  Cost of Delivery = Lucro Bruto` → **diferença 0,000000** nas duas telas.
- **Junho/2026** (CA4): R$ 2.152.167,92 (valor de ontem) → **R$ 2.173.703,35**. A diferença
  (+R$ 21.535) é **exatamente** a fatia não-casada do mês (o Comercial, 1,48% da receita), que
  antes rendia 25% e agora rende 42,5%. A parte com itens **não mudou**.
- **Mês histórico** (CA5, jun/2025): CMV = **30,00%** e Lucro Bruto = **42,51%** da receita. ✅
- **Coorte** (CA7): reconciliação cascata↔triângulo **exata (max |dif| = 0)** nas **63 safras**.
- **4 telas** sobem via `AppTest` sem exceção, inclusive a auditoria por safra com o toggle aberto
  (a linha de reconciliação da tela mostra "✅ bate").
- Cartões da aquisição conferidos na mão: Ticket Médio R$ 485,12 = 1.825.028,48 ÷ 3.762.

## Números que o João vai ver mudar

| Onde | Antes | Agora |
|---|---|---|
| Painel — junho/2026 (MC) | R$ 2.152.168 | **R$ 2.173.703** (+1,0%) |
| Painel — mês histórico (Lucro Bruto / receita) | 25% | **42,5%** |
| Coortes — 92,5% das células (as estimadas) | margem 25% | **margem 42,5%** |

Safras antigas que apareciam no vermelho podem virar verde. **Não é o painel ficando otimista — é
o chute velho sendo corrigido** (o real medido é ~43%).

## Pendências / o que ficou para depois

- **Comercial no painel geral** (~1,2%, não-Shopify): manter ou filtrar só `Shipped`? Continua em
  aberto (herdado do ADR do rebase).
- **Cartão de recompra a 90d + 180d** (calibração da V3) — não tocado.
- **Opção 1** (itens históricos do BigQuery → CMV real ano-a-ano): quando entrar, **aposenta a
  constante dos 30%**. É a cura de verdade; o 30% é só um curativo honesto.
- **Fragilidade do leitor:** planilha voltando vazia (sem cabeçalho) não é pega pelo retry.
- Nada foi commitado (junto com o rebase de ontem, segue tudo na árvore de trabalho).

---

## Adendo — 3ª rodada de ajustes (mesma sessão, telas de coorte)

Pedidos do João depois de rodar o painel:

1. **Curva de payback removida** da aba Cohorts (não estava fazendo sentido para ele).
2. **Tabela nova de receita por cohort**, antes do triângulo: `Cohort | Novos Clientes | CAC |
   Receita 1ª Compra | LTV m+0 | LTV m+1 | …`. Definições dele: **Receita 1ª Compra** = valor
   médio do 1º pedido; **LTV m+x** = **receita acumulada por cliente** (bruta, antes de qualquer
   custo). É a irmã bruta do triângulo.
3. **Triângulo:** "Safra" virou **"Cohort"**; entrou a coluna **MC primeira compra** (antes do
   m+0) = margem do 1º pedido **já descontada a mídia** (escolha dele) — ou seja, o m+0 **sem** as
   recompras que caíram no mesmo mês de entrada.
4. **Auditoria por safra saiu da aba** e virou a página **A2 - Auditoria MC Cohort**.
5. **Segundo triângulo**, abaixo do primeiro: a mesma conta em **reais cheios** (MC absoluta da
   turma) — mede tamanho, não eficiência.

**Provas:** MC absoluta ÷ clientes = MC/cliente (dif 0); reconciliação da A2 com o triângulo
exata nas 63 safras; as 6 telas sobem no `AppTest`.

**Achado (não é bug):** uma fatia pequena de clientes tem a **1ª compra fora da base** (comprou
antes em canal que não entra no HubSpot Shipped/Comercial) — o primeiro pedido *que existe* já
nasce em m+1/m+2. Por isso "Receita 1ª Compra" pode ser maior que o "LTV m+0" em algumas safras
velhas. Tamanho: **≤0,42% dos clientes** nas 12 safras recentes; **7,5%** na pior (2022-09). É o
viés cross-canal já documentado (ARCHITECTURE §6), agora visível também nestas colunas.

---

## Adendo 2 — régua de "cliente novo" e um bug de leitura

**O João viu Aquisição × A2 com números diferentes** (Vendas-novos junho: R$ 4.361.515 ×
R$ 4.350.722) e perguntou se as bases estavam diferentes. **Não estavam** — as duas leem o mesmo
`hubspot_deals.csv`. O que divergia era a **régua de "cliente novo"**: a Aquisição usava o
**carimbo** `tipo_de_venda` do HubSpot; a coorte derivava a 1ª compra (o primeiro pedido de cada
cliente).

**Medição do carimbo (junho/2026):** 59 pedidos que SÃO a 1ª compra do cliente vinham marcados
`Recompra`; 62 marcados `Primeira Compra` NÃO eram o 1º pedido daquele cliente (57 de clientes que
já haviam comprado no mesmo mês). Efeito: R$ 10.818 (0,25%).

**Decisão (do João, depois de reverter a primeira escolha): usar o carimbo do HubSpot**, a
definição da fonte, nos DOIS lados. A coorte passou a partir novos × recompra pelo carimbo.
Resultado: a Aquisição de junho **volta ao número que ele conhecia** (R$ 4.361.515,03 /
MC-novos R$ 452.861,30 / 8.180 pedidos). Resíduo Aquisição × A2 = **R$ 3.628 (0,08%, 5 pedidos)**,
inerente: a coorte só conta quem **estreou** no mês; a Aquisição conta todo pedido carimbado **com
data** no mês. ADR `2026-07-14-regua-unica-cliente-novo`.

**Correção junto:** a **coorte não aplicava as exclusões AnjosFrach** (ADR 2026-07-02) que o painel
aplica desde 02/07 — agora aplica (1 pedido em toda a base).

**BUG DE LEITURA ENCONTRADO (importante):** o Google devolve, de forma intermitente, **HTTP 200 com
`text/csv` e a planilha VAZIA** — 840 KB de linhas em branco, sem cabeçalho, no lugar dos 3,5 MB de
dados. Aconteceu **3× num dia**. O tipo da resposta está correto e o pandas lê sem reclamar, então a
blindagem antiga (que só checava HTML) não pegava: na tela virava o erro confuso *"a aba Vendas está
sem a coluna `order_id`"*. `dados._ler_csv` agora detecta a assinatura (todas as colunas viram
`Unnamed: N`) e **tenta de novo** (3×, espera crescente). Verificado ao vivo: 1ª tentativa vazia,
2ª correta.

---

## Adendo 3 — a regra-mãe: definições iguais em todas as telas

O João, ao ver Aquisição × A2 divergindo, instaurou uma **regra de projeto**: *"todos os dashes
devem usar a mesma definição de data de fechamento, de primeira compra etc. Os valores têm que
bater. Divergir só com ordem explícita."*

**Escrita em dois lugares:** `CLAUDE.md` §11 e `ARCHITECTURE.md` §5-bis — com a **tabela de donos**
(cada definição tem UMA fonte no código; tela nunca reescreve a regra, chama o dono).

**O conserto desta divergência:** o HubSpot **se contradiz** — 5 pedidos de junho vinham carimbados
"Primeira Compra" num mês diferente do mês de estreia do próprio cliente. Enquanto os dois campos
mandarem, a aba de período e a de turma nunca fecham. **Elegemos um mestre:** o carimbo define
"novo", mas **quando ele contradiz a estreia, a estreia manda**. Junho: Aquisição e A2 passam a
bater **ao centavo** (Vendas-novos R$ 4.357.887,48 · MC-novos R$ 451.297,38 · 8.175 pedidos ·
dif R$ 0,00). Custo: Vendas-novos de junho cai 0,08%.

**Guarda automático (novo):** `checar_coerencia.py` — prova, com números, que as telas concordam
(Aquisição × A2; A2 × triângulo; subtotais das cascatas; triângulo absoluto × por cliente). Sai
com erro se alguém quebrar a regra. Rodar após qualquer mexida em `cascata.py`/`coortes.py`.

---

## Fechamento da sessão

**Sessão paralela.** No meio do caminho, outra sessão do Claude passou a editar `cascata.py` e
`coortes.py` (construindo o **CMV real histórico** — a "Opção 1"). O sintoma foi um `KeyError:
'order_id'` na tela, causado pelo Streamlit lendo o arquivo **no meio de uma gravação**. Parei o
trabalho e avisei o João; ele pediu para esperar. **Lição registrada:** duas sessões nos mesmos
arquivos de dinheiro é receita de sobrescrita — combinar antes quem tem o volante.

**Estado ao fechar (tudo verificado):**
- `checar_coerencia.py` passa **com a base histórica ativa** — as telas seguem batendo depois da
  mudança no CMV (Aquisição × A2: dif R$ 0,00).
- As **6 telas** sobem no `AppTest` sem exceção.
- Junho/2026 **não mudou** com o CMV histórico (MC R$ 2.173.703,35).
- A fração estimada da coorte caiu de **92,5% → 4,3%**: a estimativa de 30% que criamos hoje virou
  exceção, não regra. Junho/2025, que era chute de 30%, agora tem CMV **real de 28,7%** — o que
  **valida a calibração** que fizemos de manhã (o real medido era 28,8–29,0%).
- A **pendência do Comercial** (aberta desde ontem) foi resolvida pela outra sessão: ele **colide
  de numeração** com pedidos Shopify antigos e ficou travado (só `Shipped` casa itens).

**Commits:** todo o trabalho desta sessão foi commitado (empacotado pela outra sessão em `99c177f`),
mais o alinhamento final da tabela de donos no `ARCHITECTURE.md`.

**Fila para a próxima sessão:**
1. Cartão de recompra a **90d + 180d** (a 2ª compra tem mediana de 123 dias — 90d sozinho vê menos
   da metade).
2. **6,4% das unidades de 2023 sem custo cadastrado** (achado da outra sessão): CMV parcial → MC
   otimista naquele ano. Pedir ao time de Dados, junto com os 137 SKUs zerados da 3.1.
3. Rever se a estimativa de 30% ainda faz sentido para o resíduo (4,3%) ou se vale um número por
   mês — hoje o `CMV_ESTIMADO_FRACAO` é fixo.
