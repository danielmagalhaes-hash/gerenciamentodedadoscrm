# ADR — V4 (MVP): arquitetura das coortes — BigQuery como torneira, cálculo na plataforma, CMV real só na janela atual

**Data:** 2026-07-10
**Status:** Aceito (spec `docs/specs/2026-07-10-v4-coortes-recompra.md`; construção pendente)
**Tema:** v4-arquitetura-mvp-coortes

> Complementa o ADR de domínio `2026-07-10-v4-coortes-recompra-hubspot.md` (que decidiu **o que** a
> V4 mede). Este decide **como** a V4 lê e calcula — a pergunta que "bloqueava tudo".

---

## 1. Contexto

A V4 (aba de coortes) precisa seguir a mesma turma de clientes por **anos**. A stack de hoje lê
**CSV de uma planilha Google estreita** (abas cobrindo só **abr–jul/2026**). Anos de itens (meses
de ~120 mil linhas) **não cabem** numa aba do Google Sheets (teto de ~10 milhões de células). Logo,
a fonte da coorte não pode ser a planilha atual como está — era o risco de arquitetura registrado
no discovery (`ARCHITECTURE.md` §6, ponto frágil "planilha estreita").

Somam-se duas descobertas desta sessão:
1. **A base HubSpot não tem o gid do pedido Shopify.** A planta-baixa de `silver_deals_minimal`
   (2026-07-10) mostrou que a coluna `id` é o id **interno do HubSpot** (ex.: `62484146992`), não o
   `gid://shopify/Order/...`. O único elo com o pedido é o **número humano** (`nome` = `508767…` =
   `Vendas.order_name`). A ponta do gid direto (hipótese do João) **não existe** — volta-se à ponte
   `nome → Vendas.order_name → order_id → Itens`.
2. **A lógica de custo mora no painel** (correção local `custos_extra.csv` → aba 3.1 se > 0 → aba 3
   se > 0 → senão faltando). Se o CMV histórico fosse calculado no BigQuery, essa receita — e as
   correções manuais do João — **não valeriam** para a V4, e a Auditoria (V1) e a coorte (V4)
   mostrariam custos diferentes para o mesmo pedido (achado 4.4 da revisão).

O João decidiu, para **esta primeira versão**, um MVP: ter a máquina de coorte rodando de ponta a
ponta rápido, aceitando que a MC real só exista onde a planilha já tem itens, e evoluir depois para
o histórico real.

---

## 2. Decisão

Para o **MVP da V4** (Opção 2):

1. **O BigQuery entra só como torneira de dado bruto — nenhum cálculo nele.** Uma consulta nova
   (o João roda **1×/mês**) puxa a base HubSpot `silver_deals_minimal` (filtro `etapa_do_negocio =
   'Shipped'`), **apenas as colunas necessárias** (`e_mail, nome, valor, data_de_fechamento,
   tipo_de_venda, data_primeira_compra, meses_desde_primeira_compra`), para um **arquivo local**
   `hubspot_deals.csv` no Mac do João. O painel **lê o arquivo local** — como já faz com
   `custos_extra.csv`. Sem credencial no painel, sem latência, sem modo de falha novo.

2. **Todo o cálculo (junção + custo + coorte) roda na plataforma** (pandas), **reaproveitando a
   receita de custo do painel**. Extrai-se de `cascata`/`detalhar_pedidos` um helper de **CMV por
   `order_id`** que a coorte e a Auditoria compartilham — uma verdade de custo só.

3. **CMV real só na janela atual de itens (abr–jul/2026); 25% estimado antes.** Onde o deal casa
   com a `Vendas`/`Itens` de hoje, a MC de produto é **real**; fora dela, **`0,25 × valor`**
   estimado. Cada célula da tela é marcada real/estimada. A **Opção 1** (o BQ despeja também os
   itens crus → MC real desde 2022) é a **versão seguinte**.

4. **Chaveamento pela ponte do número do pedido:** `hubspot.nome → Vendas.order_name → order_id →
   Itens.order_id → Custos.sku`. Para o MVP basta, porque a `Vendas` cobre a janela dos itens.

5. **A aba `Midia` é estendida** (dado, não código) para cobrir **2021-04 → hoje** com
   `investimento_total` (soma crua) + a coluna só-Facebook — cabe folgado numa aba (é mensal-agregável).

---

## 3. Motivação

- **Fidelidade ao espírito do stack (ADR `2026-07-01`):** "o painel só lê, sem credencial". Ler o BQ
  ao vivo colocaria credencial, latência e custo por consulta no painel — para servir um número que
  é uma **foto mensal** (regra da safra fechada: o dado só muda quando um mês encerra).
- **Uma verdade de custo (achado 4.4):** reusar a receita do painel garante que a coorte e a
  Auditoria **nunca discordem** sobre o custo de um pedido — inclusive as correções manuais do João.
- **MVP primeiro (pedido do João):** provar que a máquina de coorte roda de ponta a ponta antes de
  investir na engenharia de anos de itens. O ramo estimado (25%) é o mecanismo que já existe no
  painel para "não fingir precisão que não temos".
- **Menor superfície de mudança:** V1 e V2 não mudam; a V4 só acrescenta um carregador, um módulo e
  uma página.

---

## 4. Alternativas consideradas

### Alternativa A: BigQuery ao vivo dentro do painel
- **Descrição:** o painel consulta o BQ a cada abertura da aba de coortes.
- **Prós:** sempre "fresco"; sem passo manual.
- **Contras:** credencial no painel (contra o ADR do stack); latência e custo por consulta; modo de
  falha novo; e o dado só muda 1×/mês — frescor ao vivo é desperdício.
- **Por que foi descartada:** paga-se muito para servir uma foto mensal.

### Alternativa B: Opção 1 já no MVP (BQ despeja itens crus → MC real desde 2022)
- **Descrição:** puxar do BQ também a base de itens (2022→hoje) para arquivos locais e calcular a MC
  real de todo o histórico.
- **Prós:** entrega a promessa do `PRODUCT.md` (real desde 2022) de uma vez.
- **Contras:** exige resolver a ponte `order_name↔order_id` histórica no BQ, a cobertura de custo de
  SKU antigo e a mídia histórica — três **queries de viabilidade** ainda não rodadas; mais engenharia
  antes de ver a máquina funcionar.
- **Por que foi descartada (por ora):** o João preferiu um MVP; a Opção 1 é a **versão seguinte**,
  quando as três queries de viabilidade forem rodadas.

### Alternativa C: chavear pelo gid direto (hipótese inicial do João)
- **Descrição:** casar `hubspot.Id` (supunha-se ser o gid do pedido) direto com `Itens.id`.
- **Contras:** a planta-baixa mostrou que **não há gid** na base HubSpot; `id` é o id interno do
  HubSpot.
- **Por que foi descartada:** o dado não existe. Volta-se à ponte pelo `nome`.

---

## 5. Consequências

### Positivas
- Painel segue **sem credencial**, rápido, com um só modo de leitura novo (arquivo local).
- **Uma verdade de custo** entre Auditoria e coorte.
- MVP de coorte roda de ponta a ponta cedo; V1/V2 intocadas.

### Negativas
- **MVP majoritariamente estimado (25%):** a janela real é ~4 meses, então a maioria das células vem
  do estimado. Lê-se o MVP como "o motor funciona", não como o payback real. (Marcado célula a célula.)
- **Passo manual mensal** (rodar o export do BQ) — mitigado por mensagem clara de "arquivo velho".
- **Divergência declarada com o `PRODUCT.md`** (§8): o MVP não entrega "real desde 2022" — faseado
  para a Opção 1.

### O que essa decisão FECHA
- Trata o BigQuery como motor de cálculo do painel (fica sendo torneira de dado bruto).
- Duas verdades de custo (Auditoria vs coorte) — a receita de custo é uma só.
- Ler anos de itens da planilha Google (inviável) — o histórico, quando vier, vem de arquivo local.

---

## 6. Implementação

- **Onde se materializa no código:** `dados.py` (`carregar_hubspot` + leitura da `Midia` estendida);
  `coortes.py` (novo — `calcular_coortes`/`ResultadoCoortes`); `pages/3_Coortes.py` (novo); refactor
  de extração de um helper de **CMV por `order_id`** a partir de `cascata`/`detalhar_pedidos`.
- **Migration/refactor necessário:** sim — extrair o helper de CMV (com teste de que a Auditoria
  segue idêntica); nenhuma migração de dado.
- **Preparo de dado (João):** `hubspot_deals.csv` mensal (query na spec §3.5); aba `Midia` estendida
  a 2021-04→hoje.
- **Regra a adicionar no CLAUDE.md:** sim — §0 e §8 (nova fonte HubSpot local; BQ como torneira;
  MVP = Opção 2).
- **Atualização no ARCHITECTURE.md (seção 5):** feita nesta sessão.

---

## 7. Revisão

- **Quando reavaliar:** ao evoluir para a **Opção 1** (MC real ano-a-ano) — aí rodam as 3 queries de
  viabilidade (cobertura de custo de SKU antigo; ponte `order_name↔order_id` no BQ; mídia mensal
  desde 2022) e decide-se se o histórico vem de arquivo local pré-agregado ou de outra forma.
- **Sob que condições reverter:** se o passo manual mensal se mostrar frágil na prática, reconsiderar
  um pré-agregado agendado pelo time de Dados numa aba nova (o triângulo agregado cabe numa aba — só
  anos de itens não cabem).
