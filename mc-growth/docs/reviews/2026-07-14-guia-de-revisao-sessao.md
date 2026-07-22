# Guia de revisão — o que foi construído na sessão de 2026-07-10 a 07-14

> Pedido do João ao fechar: deixar **muito claro o que foi construído**, porque ele **não está
> satisfeito e vai revisar bastante coisa**. Este doc separa o que está **provado por número** do
> que é **escolha de modelagem** (decisão dele, revisável), e diz **como reverter** cada peça.
>
> **Nada foi feito push.** Tudo está no branch `v4-coortes-e-unificacao-hubspot`, commit `0f751f7`.
> O `main` local está intocado. O `hubspot_deals.csv` não foi versionado (gitignore).

---

## 1. O que foi construído (3 frentes)

### Frente A — V4: aba de coortes (`pages/3_Coortes.py`, `coortes.py`)
Segue turmas de clientes (safra = mês da 1ª compra) e acumula a MC por cliente no tempo: triângulo,
curva de payback, CAC, payback, recompra em 90 dias. Fonte nova: `bases/hubspot_deals.csv` (HubSpot).

### Frente B — Auditoria por safra (dentro da aba Coortes)
Toggle que abre a cascata de uma safra em 3 blocos: **MC novos** (1ª compra) + **MC recompra** +
**MC total**, com total × por cliente, slider de horizonte e export CSV.

### Frente C — Unificação de tudo no HubSpot (`cascata.py`)
Painel geral, aquisição e coorte passaram a usar a **mesma régua**: receita = **`valor`** por **data
de fechamento**; custo = **item a item** (CMV real via ponte) na janela de itens, **25%** estimado
fora; universo **Shipped + Comercial**. Fallback ao motor antigo (net) se o CSV faltar.

---

## 2. O que está PROVADO por número (baixo risco de revisão)

- **Uma só verdade de custo:** o CMV de um pedido é idêntico no painel, na auditoria e na coorte —
  `max |dif| = 0` em 14.026 pedidos de junho (refactor `juntar_custos`/`cmv_por_pedido`).
- **Coorte reconcilia:** a MC/cliente da auditoria = a célula do triângulo nas **64 safras** (e em
  cada horizonte do slider).
- **Aquisição bate com a base ao centavo:** abr 3.134.272 / mai 4.148.119 / jun 4.361.5xx = o teu
  filtro direto (`tipo_de_venda='Primeira Compra'`, Σ`valor`, por fechamento).
- **CMV segue item a item** depois da unificação (junho CMV real ~2,39M) — não virou estimativa.
- **Fallback:** sem o CSV, painel/aquisição voltam ao motor antigo (net) sem quebrar.
- **Sem regressão de tela:** as 4 páginas sobem no `AppTest` sem exceção.

## 3. O que é ESCOLHA DE MODELAGEM (revise com atenção — é o que mais mudou número)

| # | Escolha | O que muda | Onde revisar |
|---|---|---|---|
| M1 | **Receita = `valor` (HubSpot), não `net_revenue` (Shopify)** | `valor` é sempre ≥ net (+1,1%, é **frete**). **Painel junho MC 2,05M → 2,15M (+4,8%)**. Pergunta a furar: frete deve entrar na receita e fluir pra margem? O painel já subtrai custo de frete (4,8%) — não há dupla contagem/subcontagem? | ADR `2026-07-14` §5-bis; `_cascata_de_deals` |
| M2 | **Período por data de fechamento (HubSpot), não processed_at (Shopify)** | Alguns pedidos mudam de mês na borda | idem |
| M3 | **Painel inclui o Comercial (~1,2%)** | O título ainda diz "(Shopify)" mas entra venda não-Shopify | decisão de manter (2026-07-14) — revisível |
| M4 | **"Novo" = `tipo_de_venda` do HubSpot (1ª compra na Minimal), não o carimbo Shopify** | Junho: +692 clientes vs a régua antiga; muda MC-novos/CAC/aROAS | ADR; aquisição |
| M5 | **Fora da janela de itens (histórico) = MC estimada 25%** | Hoje **~92,5% das células da coorte** são estimadas; a curva cruza o zero cedo demais ("MC parcial") | rótulos na tela; spec V4 |
| M6 | **Idade da coorte calculada** (não do campo `meses_desde_primeira_compra`, que é idade do cliente no export) | Sem isso a coorte sairia errada — mas confirme a lógica de meses-calendário | `coortes._preparar_deals`; ARCHITECTURE §6 |
| M7 | **Recompra em janela fixa de 90 dias** | A mediana da 2ª compra é 123 dias → 90d vê só 42% | calibração §9; considerar 90+180 |
| M8 | **Um cliente = uma safra** (mínimo de data_primeira_compra) | Corrige 4 deals com deriva do HubSpot | `_preparar_deals` |

## 4. Vieses/limites herdados (declarados, não resolvidos nesta sessão)
- Viés cross-canal da coorte: medido em **0,87%** (imaterial).
- Mídia inteira no m+0 (100% mídia → novos) — não separa aquisição × remarketing.
- Custo de hoje aplicado a venda antiga; SKUs antigos sem custo.
- MC "parcial": não desconta CX, juros de estoque, criativo.

## 5. Como reverter, se você discordar de algo
- **Toda a unificação no `valor`:** as telas passam `deals=` ao cálculo. Remover o `deals=` (ou
  apagar `bases/hubspot_deals.csv`) faz painel/aquisição voltarem ao **motor antigo (net, só janela
  atual)** — o código antigo continua lá como fallback.
- **Só a régua de "novo":** em `calcular_aquisicao`, a partição por `tipo_de_venda` tem fallback ao
  `customer_type`.
- **Coorte no `valor`:** `coortes._mc_produto_por_deal` — trocar `valor` de volta por `net` é 2 linhas.
- **A frente inteira:** está isolada no branch; o `main` não foi tocado.

## 6. Documentos para a revisão
- ADRs: `docs/decisions/2026-07-10-v4-*` (2), `docs/decisions/2026-07-14-rebase-geral-aquisicao-hubspot.md` (unificação, §5-bis).
- Specs: `docs/specs/2026-07-10-v4-coortes-recompra.md`, `2026-07-10-v4-auditoria-por-safra.md`, `2026-07-14-rebase-geral-aquisicao-hubspot.md`.
- Logs: `docs/sessions/2026-07-10-construcao-v4-coortes.md`, `2026-07-12-auditoria-por-safra.md`, `2026-07-14-rebase-geral-aquisicao-hubspot.md`.
- Mapa do sistema: `ARCHITECTURE.md` (§2 módulos, §5 decisões, §6 pontos frágeis).

## 7. Pendências a montante (não bloqueiam, mas ficam)
- Título do painel diz "(Shopify)" mas agora inclui Comercial — revisar.
- `PRODUCT.md`/spec V4 ainda descrevem "novo" pelo carimbo Shopify e a fórmula dos 25% antiga — alinhar.
- Opção 1 (itens reais ano-a-ano do BigQuery) → tira o "estimado 25%" do histórico; é a próxima grande.
- 137 SKUs de custo zerado (`docs/skus-custo-zerado-aba-3-1.csv`) ao time de Dados.
