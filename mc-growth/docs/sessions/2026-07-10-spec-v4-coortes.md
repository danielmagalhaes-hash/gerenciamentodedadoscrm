# Sessão 2026-07-10 (tarde) — Spec da V4 (coortes de recompra)

> Log da sessão. O "porquê" e o "o que vem depois", em linguagem que o João relê em 2 semanas.

---

## Objetivo da sessão
Escrever a **spec da V4** (aba de coortes de recompra), começando pela **decisão de arquitetura**,
sem construir código — confirmando antes A) arquitetura, B) validações, C) glossário/25%, D) regras
invioláveis.

---

## O que foi feito
- Ritual de início: li `CLAUDE.md`, `ARCHITECTURE.md`, `PRODUCT.md` (V4), discovery/ADR da V4, o
  relatório de definições-para-revisão, o `ROADMAP.md` e a **revisão crítica** que estava não
  commitada (`docs/reviews/2026-07-10-v4-respostas-da-revisao.md`).
- Confirmei A/B/C/D com o João **uma pergunta por vez**, e destravei o chaveamento com **planta-baixa
  do HubSpot ao vivo** (o João rodou 2 queries; a saída mostrou o esquema real).
- **Escrevi a spec da V4 (MVP)** (`docs/specs/2026-07-10-v4-coortes-recompra.md`) — 8 seções + seção
  0 de arquitetura + validações pendentes + checklist.
- **Escrevi o ADR de arquitetura** (`docs/decisions/2026-07-10-v4-arquitetura-mvp-coortes.md`).
- **Corrigi as duas inconsistências** que a revisão apontou: `ROADMAP.md` V4 (não promete mais "custo
  cheio / V3") e a fórmula dos 25% no `PRODUCT.md` §6 (conta dobrada → `0,25 × valor`), + anotação
  `[MVP vs versão-cheia]` no `PRODUCT.md` §8.
- Atualizei `ARCHITECTURE.md` (nota de topo, tabela de decisões §5, ponto frágil da planilha estreita §6).

---

## Decisões tomadas

### Arquitetura do MVP (Opção 2)
- **Decisão:** BigQuery = **torneira de dado bruto** (o João puxa a base HubSpot 1×/mês →
  `hubspot_deals.csv` local); **cálculo na plataforma** reusando a receita de custo do painel; **CMV
  real só na janela de itens atual (abr–jul/2026), 25% estimado antes** (marcado célula a célula).
- **Por quê:** painel sem credencial (espírito do ADR do stack); **uma verdade de custo** entre
  Auditoria e coorte (achado 4.4); MVP roda cedo; anos de itens não cabem numa aba.
- **Descartado:** BQ ao vivo no painel (credencial/latência para servir foto mensal); Opção 1 já no
  MVP (exige 3 queries de viabilidade antes); gid direto (não existe gid na base HubSpot).
- **ADR criado?** sim — `docs/decisions/2026-07-10-v4-arquitetura-mvp-coortes.md`.

### Chaveamento pela ponte do `nome`
- **Decisão:** casar `hubspot.nome → Vendas.order_name → order_id → Itens`. **Por quê:** a
  planta-baixa provou que **não há gid** do pedido Shopify na base HubSpot (`id` é o id interno do
  HubSpot); o único elo é o número humano (`nome` = `508767…`). Para o MVP basta (a `Vendas` cobre a
  janela dos itens). **Descartado:** o gid direto (hipótese inicial do João — dado inexistente).

### Mídia com imposto condicional por data
- **Decisão:** `Ad Spend = investimento_total` (soma crua); **a partir de 2026-01** somar o imposto
  **só da fatia FB** (`+ fb × 0,1215/0,8785`). **Por quê:** o João informou que o imposto de 12,15%
  passou a valer em **2026-01-01** — antes não havia. Invariante: para 2026 a fórmula **coincide**
  com a Ad Spend do painel/V2. `investimento_total` é soma; há coluna só-FB na mesma aba.

### Os 25% (pré-2022 / fora da janela)
- **Decisão:** `MC de produto = 0,25 × valor`, **direto, sem deduzir as % de novo**. **Por quê:** a
  redação anterior descontava duas vezes (~15%, não 25%). Confirmado pelo João ("margem de produto,
  antes da mídia"). **ADR?** não — corrigido direto no `PRODUCT.md` §6.

### V3 fica de fora (confirmado)
- **Decisão:** CX, juros de estoque e criativo **não entram** nesta versão; a curva leva o rótulo
  honesto **"MC parcial"**. **Por quê:** decisão do João; a linha do zero não promete o que não mede.

---

## Problemas encontrados

### O gid do pedido não existe na base HubSpot
- **Descrição:** a hipótese do João (chavear pelo gid via coluna `Id`) não se sustentou.
- **Causa raiz:** `silver_deals_minimal.id` é o id **interno do HubSpot**; não há coluna com
  `gid://shopify/Order/...`.
- **Solução aplicada:** voltar à ponte pelo `nome` (= `Vendas.order_name`). Para o MVP, suficiente.
- **Status:** resolvido.

### O MVP nasce majoritariamente estimado
- **Descrição:** como a janela real de itens é ~4 meses, a maioria das células do triângulo vem do
  25% estimado.
- **Causa raiz:** escolha da Opção 2 (MVP antes do histórico real).
- **Solução aplicada:** marcar cada célula real/estimada; enquadrar o MVP como "o motor funciona",
  não "o payback real". Registrado na spec §8 e no ADR.
- **Status:** aberto por design (resolve na Opção 1).

---

## Estado do projeto agora

### Funcionando
- V1 (painel de MC) e V2 (aba de aquisição) intocadas e rodando.
- **Spec da V4 (MVP) escrita e coerente**; ADR de arquitetura escrito; documentos corrigidos.

### Quebrado / incompleto
- V4 **não construída** — só spec.
- **Pré-condições de dado do João pendentes:** gerar o `hubspot_deals.csv` (query pronta na spec
  §3.5) e **estender a aba `Midia`** para 2021-04→hoje (`investimento_total` + coluna só-FB).
- **3 validações de calibração pendentes** (spec §9): `valor`×`net_revenue`; viés cross-canal;
  janela de recompra (90 vs 180 dias). Não bloqueiam o build; afinam números.

---

## Próximo passo
1. **João prepara os dados:** `hubspot_deals.csv` (export mensal) + `Midia` estendida.
2. **Construir a V4** seguindo a spec: `dados.carregar_hubspot`, módulo `coortes.py`
   (`calcular_coortes`), `pages/3_Coortes.py`, e o refactor de extração do helper de **CMV por
   `order_id`** (com teste de que a Auditoria segue idêntica).
3. **Rodar as 3 queries de calibração** (spec §9) durante o build.
4. Pendências herdadas seguem: `docs/skus-custo-zerado-aba-3-1.csv` (137 SKUs) e re-base da V2 no
   HubSpot (prompt guardado).

---

## Atualizações em outros documentos
- **`ARCHITECTURE.md`:** nota de topo (V4 spec escrita + arquitetura decidida); nova linha na tabela
  de decisões §5 (arquitetura MVP); ponto frágil da "planilha estreita" §6 marcado ENDEREÇADO.
- **`CLAUDE.md`:** §0 atualizada (V4 spec escrita, build pendente, próximo passo).
- **`docs/decisions/`:** `2026-07-10-v4-arquitetura-mvp-coortes.md` (criado).
- **`docs/specs/`:** `2026-07-10-v4-coortes-recompra.md` (criado).
- **`docs/ROADMAP.md`:** V4 — corrigido (sem "custo cheio / V3"; critérios de aceite do MVP).
- **`PRODUCT.md`:** §6 (fórmula dos 25% corrigida) e §8 (anotação `[MVP vs versão-cheia]`).

---

## Adendo (fim da sessão) — base trazida e validada

Depois de escrever a spec, o João já trouxe a base do HubSpot. Guardei em **`bases/`** (pasta nova
pra organizar as bases locais), como `hubspot_deals.csv`, **fora do git** (tem e-mail — dado pessoal;
adicionei ao `.gitignore`).

**Validações rodadas (ao vivo, 2026-07-10):**
- **Sanidade:** 462.108 deals, 279.536 clientes, 65 safras (mar/2021→jul/2026); `tipo_de_venda`,
  datas e `data_primeira_compra` limpos; nulos desprezíveis.
- **Ponte validada:** o `nome` vem com cerquilha (`#471263`) e sem; **removendo o `#`, casa 99,7%**
  com o `Vendas.order_name` na janela. → regra de leitura registrada na spec (§0.3, §3.3).
- **Receita bate:** `valor` (HubSpot) × `net_revenue` (planilha) nos 37.770 casados → razão **1,011**,
  delta mediano **0%**. Emenda real↔estimado pequena (~1%). → calibração V1 **fechada**.

**Decisão nova (Comercial):** o 1º arquivo veio só com `Shipped`; o correto é **`Shipped` +
`Negócio Fechado - Comercial`** (o João re-puxou). Descoberta ao validar: os 5.400 deals Comercial
(1,2%) gravam o **nome do cliente** no campo `nome` (ex.: "Wagner Eduardo"), não o número do pedido
→ **não casam** com a `Vendas` (0%) e são **sempre estimados (25%)**. São quase todos Recompra de
clientes de 2021 (só 486 em 2026). **Decisão do João: manter** (é valor real do cliente), marcados
como estimados. **Por quê:** impacto pequeno (1,2%, concentrado em safras velhas fora das "últimas
12–18") e mais fiel ao valor do cliente. **Consequência:** o universo da coorte fica levemente maior
que o da V1/V2 (só `Vendas`). Propagado em spec (§0.6, §3.3, §3.5, R1, R5), `PRODUCT.md` (glossário
§3, §8), ADR de domínio, `ARCHITECTURE.md` e `CLAUDE.md` §0.

**Estado da base:** `bases/hubspot_deals.csv` pronto e validado para o build. O **próximo passo 1**
(João preparar o `hubspot_deals.csv`) está **feito**; falta só **estender a aba `Midia`** (2021-04→
hoje) antes de construir.
