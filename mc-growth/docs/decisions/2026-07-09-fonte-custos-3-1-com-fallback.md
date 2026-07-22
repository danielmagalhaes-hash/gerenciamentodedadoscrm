# ADR 2026-07-09 — Fonte de custo: aba 3.1 (principal) com aba 3 como rede de segurança

## Contexto

A fonte de custo por SKU era a aba **"3. Custos"** (gid `423190064`, col `Valor de Custo`).
O João apontou a aba **"3.1. Custos"** (gid `1460088128`, col `Custo`) como tendo custos
mais atualizados. Investigação de 2026-07-09 comparou as duas ao vivo.

**O que a 3.1 tem de melhor:** +610 SKUs de cobertura (1698 vs 1096), quase sem lixo (3
valores não numéricos vs 51), custos mais baixos/atualizados na maioria (média R$78,82→R$62,12;
784 de 1088 SKUs em comum mudaram de valor).

**O problema:** **137 SKUs que tinham custo real na aba 3 estão zerados (R$0,00) na 3.1** —
e caem em famílias inteiras (ex: `85010010xx` a R$152,90–155; `830200633x` a R$80). Custo
zero de família inteira = "aba ainda não preenchida", não "produto grátis". Trocar puro
3→3.1 subestimaria o CMV nesses 137 → MC artificialmente inflada.

## Decisão

**A aba 3.1 é a fonte principal de custo; a aba 3 é a rede de segurança.** Para cada SKU, o
custo é o primeiro que existir, nesta ordem:

1. `custos_extra.csv` (correção local do João) — sempre vence. *(inalterado)*
2. Aba **3.1** — se valor **> 0**.
3. Aba **3** — se a 3.1 vier 0/vazia/ausente e a 3 tiver **> 0**.
4. Senão → SKU sem custo → alerta na tela (comportamento atual).

**Custo igual a 0 é tratado como "faltando", não como "grátis"** (decisão do João). Item
genuinamente grátis fica sem custo e é definido no editor (regra 1, que vence tudo).

## Por quê

- Ganha a cobertura e a atualização da 3.1 **sem** perder os 137 custos reais que ela ainda
  não preencheu. É estritamente aditivo à cobertura — o fallback nunca remove um custo real.
- Espelha o cuidado do bug de dobra de kit, na direção oposta: não deixar a MC ficar mais
  bonita por causa de um buraco de dado.

## Alternativas descartadas

- **Trocar puro 3→3.1:** simples, mas subestima o CMV em 137 SKUs (MC inflada) até o time
  preencher a aba. Rejeitado.
- **Não trocar / esperar o time preencher:** perderia o ganho imediato de +610 SKUs e custos
  atualizados por tempo indeterminado. Rejeitado.

## Impacto medido (junho/2026)

| | Antes (só aba 3) | Depois (3.1 + fallback) | Δ |
|---|---|---|---|
| CMV | R$ 2.465.133 | R$ 2.386.887 | −R$ 78.246 (−3,17%) |
| MC  | R$ 1.977.055 | R$ 2.055.301 | +R$ 78.246 (+3,96%) |

- Os **137 zerados recuperaram custo>0** (137/137) via fallback.
- SKUs sem custo em junho: **1 → 1** (sem regressão de cobertura).
- Painel e Auditoria sobem sem exceção (`AppTest`).

## Consequências / o que fica aberto

- **A montante (time de Dados):** preencher os 137 SKUs na 3.1. Lista em
  `docs/skus-custo-zerado-aba-3-1.csv`. Quando a 3.1 estiver completa, a aba 3 pode ser aposentada.
- **Fora de escopo (anotado):** marcar na Auditoria de qual aba veio cada custo (origem) —
  útil, mas mexe no contrato/UI; fica para depois se o João quiser.
- Constantes no código: `GIDS["Custos"]` = `1460088128`; `GID_CUSTOS_FALLBACK` = `423190064`.
