# Sessão — Construção da V4 (aba de coortes de recompra)

**Data:** 2026-07-10 (tarde/noite)
**Modo:** B (construção — toca dinheiro/dado: MC por safra, CAC, payback)
**Objetivo:** construir a V4 pela spec `docs/specs/2026-07-10-v4-coortes-recompra.md`, à risca.

---

## O que se fez (em linguagem de negócio)

Antes desta sessão o painel sabia olhar um **mês fechado** e a **1ª compra** do cliente novo.
Agora ele sabe seguir a **mesma turma** de clientes ao longo dos meses: a **aba de Coortes**.

Cada **safra** é a turma que fez a 1ª compra num mês. A tela acumula, para cada safra, a
**Margem de Contribuição por cliente** conforme a turma envelhece (m+0, m+1, …): a mídia inteira
do mês de entrada pesa no m+0 (é o CAC, o "mergulho" inicial no vermelho), e cada recompra vai
somando adiante. Quando a linha **cruza o zero**, a turma se pagou. A aba mostra três coisas: os
**KPIs** da safra escolhida (payback, CAC, MC/cliente até hoje, recompra em 90 dias), a **curva**
das últimas 12 safras (com a linha do zero e a safra em foco destacada) e o **triângulo**
(uma linha por safra, verde onde já se pagou, vermelho onde não).

Como é um **MVP**, a MC de produto é **real** só onde o pedido casa com a planilha de itens de
hoje (abr–jul/2026) e **estimada em 25% da receita** antes disso — cada célula é marcada. Rótulo
honesto na tela: **"MC parcial"** (não desconta CX, juros de estoque nem criativo).

---

## O que foi construído (código)

1. **`dados.carregar_hubspot()`** — lê o arquivo local `bases/hubspot_deals.csv` (462k deals do
   HubSpot), tira o `#` do número do pedido, normaliza e-mail/valor, **datas em ISO** (`AAAA-MM-DD`,
   diferente do DD/MM/AAAA da planilha — parser novo `_para_data_iso`), descarta linha sem
   e-mail/1ª-compra, deriva a `safra`. Arquivo/coluna faltando = erro claro. **Só a aba de coortes
   o lê** — V1/V2 não dependem dele. `carregar_midia` ganhou `investimento_total`.

2. **Refactor `cascata.juntar_custos` + `cmv_por_pedido`** — extraí a junção Itens×Custos para um
   helper único (a **única receita de custo** do projeto). Painel, aquisição, Auditoria e coorte
   saem toda daqui → **nunca discordam** sobre o custo de um pedido. Provado **byte-idêntico**
   antes/depois (CMV de junho 2.389.587,39 igualzinho; MC 2.052.600,82).

3. **`coortes.py` — `calcular_coortes`** — o coração da V4. Safra e idade ancoradas na **1ª compra
   real do cliente**; MC real via ponte `nome → Vendas → Itens` senão 0,25×valor; mídia (com imposto
   FB só ≥2026-01) no m+0; CAC, payback, recompra 90d, MC/cliente até hoje por safra; só **safras
   fechadas**; cada célula marcada real/estimada. Devolve `ResultadoCoortes`.

4. **`pages/3_Coortes.py`** — a aba: cabeçalho de KPIs + seletor de safra, curva em **Altair**
   (sem dependência nova; linha do zero + destaque), triângulo estilizado (verde/vermelho +
   itálico/`*` para estimada), notas ("MC parcial", % estimada, arquivo velho, sem mídia).

---

## Verificação (critérios de aceite da spec §7)

- **Amarração provada (a mais importante):** por pedido, a MC real da coorte é **idêntica** ao
  Lucro Bruto do painel/Auditoria — **max |dif| = 0,000000** em 14.026 pedidos de junho. Uma
  verdade de custo. (No agregado, coorte/painel = 1,0009 — 0,09% de diferença de borda entre
  `processed_at` da Shopify e `data_de_fechamento` do HubSpot; imaterial.)
- **CA2** julho/2026 (mês em curso) não aparece; última safra = 2026-06.
- **CA3** MC acumulada = soma das incrementais, e o m+0 inclui `−CAC` (conferido célula a célula).
- **CA5** célula da janela = real (peso normal); de 2023 = estimada (itálico/`*`).
- **CA6** Ad Spend da coorte para junho/2026 = **idêntica** ao painel (1.420.461,57); para
  junho/2025 = `investimento_total` **sem** imposto.
- **CA7** payback = menor m com MC acumulada ≥ 0; "—" quando não cruzou.
- **CA10** CSV ausente → erro claro só nesta aba (V1/V2 seguem).
- **CA12** V1 e V2 **byte-idênticas** (fórmula de CMV antiga = `juntar_custos`, provado 1.166.310,63).
- **Sanidade** ΣN_S = clientes distintos em safras fechadas (275.777 = 275.777).
- `AppTest` sobe painel, Aquisição e **Coortes** sem exceção (0 em cada).

## Calibração (§9 — rodadas nesta sessão)

- **V2 (viés cross-canal):** só **0,87%** dos clientes têm a 1ª compra Shopify num mês posterior à
  1ª compra cross-canal — abaixo do portão de 10%, e encolhendo (2024 1,0% → 2026 0,08%). Viés
  **imaterial**, como a spec previu.
- **V3 (janela de recompra):** a 2ª compra Shopify tem **mediana de 123 dias** (p75 322); só **42%**
  recompram em ≤90d, **60%** em ≤180d. O rótulo "recompra em 90 dias" é honesto e comparável, mas
  **conservador** — a mediana cai fora dele. **Sugestão:** mostrar 90d E 180d numa próxima iteração.

---

## Achado que contraria a spec (registrado, importante)

O campo **`meses_desde_primeira_compra`** do HubSpot **NÃO é a idade do deal** (m+0, m+1) como a
spec §3.3/R4 e o `PRODUCT.md` §3 assumiram ("vem pronta da base"). É a **idade do CLIENTE no
momento do export** — o **mesmo número em todos os deals do cliente** (cliente de 2021-06 → 61 em
todos; quem estreou em 2026-06 → 1 até na própria 1ª compra). Usá-lo empilharia a turma inteira
numa única idade — o triângulo sairia errado.

**Correção aplicada:** a idade da coorte é **calculada** da diferença em meses-calendário entre
`data_de_fechamento` e a 1ª compra real do cliente. O campo cru fica carregado, mas **não é usado**
para idade. Foi o que destravou a MC do m+0 (que vinha zerada com o campo cru).

**Pendência a montante (não bloqueia):** corrigir o `PRODUCT.md` §3 (glossário "Mês da safra") e a
spec R4 para dizer que a idade é **calculada**, não lida do campo. + a correção já pendente da
fórmula dos 25% no `PRODUCT.md` §6.

---

## Decisões da sessão

- **Carregador separado (não `carregar_tudo`):** `carregar_hubspot` é chamado só pela aba de
  coortes. Assim a ausência do CSV **não derruba** V1/V2 (honra CA10 e CA12 melhor que exigir o
  arquivo no `carregar_tudo`, como a spec §3.4 permitia "ou um novo container").
- **Célula real vs estimada por maioria:** a base é bimodal (safras na janela ~99% reais; antigas
  100% estimadas). Uma dúzia de deals não-casados não pinta a célula inteira de estimada — real se
  a **maioria** dos deals casou.
- **Um cliente = uma safra:** ancorado no **mínimo** de `data_primeira_compra` por `e_mail`
  (a "deriva" do HubSpot afetava 4 deals) — assim ΣN_S = clientes distintos exatamente.
- **Altair** para a curva (vem com o Streamlit; matplotlib não está instalado; sem dependência nova).

---

## Estado ao fim / próximo passo

- **V4 construída e verificada.** MVP com **92,5% das células estimadas** (janela real ~4 meses) —
  lê-se como "o motor funciona", não como payback definitivo. As últimas 12 safras já têm o m+0
  real; a leitura de tendência entre safras recentes é a que vale.
- **Próximos (herdados/novos):**
  1. Corrigir `PRODUCT.md` §3 (idade calculada) e §6 (fórmula 25%), e a frase do §3 V2 ("84 de 37.593").
  2. Considerar recompra **90d + 180d** (calibração V3).
  3. Opção 1 (MC real ano-a-ano desde 2022) — versão seguinte; roda as 3 queries de viabilidade.
  4. Re-base da V2 no HubSpot (prompt guardado); 137 SKUs de custo zerado ao time de Dados.
