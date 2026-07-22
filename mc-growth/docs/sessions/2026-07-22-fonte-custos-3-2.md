# Sessão 2026-07-22 — Parâmetros do Financeiro: custo 3.2 + percentuais da DRE

**Modo:** B (construção) · **Toca dinheiro:** sim (CMV) · **Branch:** v4-coortes-e-unificacao-hubspot

## O que o João pediu
"Recebi do financeiro parâmetros atualizados da DRE e do CMV. Preciso atualizar." Baixou uma
planilha de CMV em Downloads e pediu pra eu trazer pro projeto, explicando antes o que faria
em termos de regra de negócio e infra.

## O que era a planilha
`CMV Minimal SKU - Página1.csv` — **não** eram percentuais da DRE, e sim uma **tabela de custo
por SKU** atualizada (coluna `PREÇO JUNHO`). Então nada de `PARAMETROS` nem de `CMV_ESTIMADO_FRACAO`
(30%); o que mudou foi o **custo real por produto**, que alimenta o CMV item a item.

Comparado com a base viva: 1.068 SKUs válidos, dos quais **880 mudaram** (431↑, 449↓), **66 novos**,
122 iguais; variação mediana −R$ 0,14, com famílias caindo forte (ex.: 155,00 → 81,21).

## Decisão de infra (do João)
Em vez de colar na 3.1 ou usar o `custos_extra.csv` local, o João **criou uma aba nova na
planilha, "3.2. Custos"** (gid `634911340`, colunas `SKU` + `PREÇO JUNHO`) e pediu pra usá-la.
Caminho durável e alinhado à regra da Moon (a planilha é a fonte de verdade — "uma verdade só").

## O que mudou no código (só `dados.py`)
- Nova constante `FONTES_CUSTO` = lista ordenada `[(3.2, PREÇO JUNHO), (3.1, Custo), (3, Valor de Custo)]`.
- `carregar_custos` agora **percorre a cascata** (custo = 1º valor > 0; 0/vazio = FALTANDO),
  com `custos_extra.csv` por cima — regra idêntica à de antes, só uma camada a mais no topo.
- Saíram `GID_CUSTOS_FALLBACK` e a entrada `GIDS["Custos"]` (a lista é o único dono dos gids
  de custo — evita 2ª referência ao mesmo número).

## Verificação (todos os critérios de aceite)
1. 3.2 lida sem erro (colunas `SKU` + `PREÇO JUNHO`; 1.072 SKUs com custo > 0). ✅
2. **Cobertura:** SKUs com custo 1.617 → **1.684** (+67); **0 SKUs perderam custo**. ✅
3. `checar_coerencia.py` → **7/7** (as telas seguem concordando). ✅
4. `AppTest` das **7 telas** → todas OK. ✅
5. **Impacto medido — Junho/2026:** MC R$ 2.173.703,35 → **R$ 2.255.165,93** (+R$ 81.462,58 /
   +3,75%); CMV cai o mesmo tanto. A reconstrução da base antiga bateu a MC de junho **ao
   centavo** com o valor documentado — prova que o Δ é confiável. ✅

## Consequências / o que registrar
- A **âncora byte-idêntica de junho** deixa de ser R$ 2.173.703,35 e passa a R$ 2.255.165,93
  (foto com a base 3.2). O guarda 7/7 prova concordância ENTRE telas, não um valor fixo.
- Meses históricos e coortes também se movem (o CMV real roda em toda a história em 3 camadas).

## Docs atualizados
Spec `docs/specs/2026-07-22-fonte-custos-3-2.md`; ADR `docs/decisions/2026-07-22-fonte-custos-3-2.md`;
`ARCHITECTURE.md` (banner + mapa de gids + tabela `Custos` + §3.0); `CLAUDE.md` §0.

## Parte 2 — Percentuais da DRE (mesma sessão)
Depois do custo, o João passou os percentuais atualizados. Troquei em `cascata.PARAMETROS`
(só valores; nenhuma lógica): PIS/COFINS 1,75→4,74 · ICMS 12,54→13,73 · Devoluções 3,48→3,32 ·
Chargebacks 0,15 (igual) · Frete 4,80→5,02 · Gateways 1,70→1,37 · Plataforma 0,90→0,44 ·
Antecipação 1,60→1,10. **Embalagem (0,57) e Outras Deduções (0,00) não vieram na lista →
mantidas** (Embalagem sinalizada pra o João confirmar). Soma 27,49% → **30,44%** (+2,95 pts).

**Impacto (junho, já com custo 3.2):** MC **R$ 2.010.121,79**. Trilha: 2.173.703,35 (3.1 + %
antigos) → 2.255.165,93 (3.2 + % antigos, custo novo +81k) → **2.010.121,79** (3.2 + % novos, os
% tiram ~245k). Líquido vs o ponto de partida: **−R$ 163.581 (−7,5%)**. Guarda **7/7**; AppTest OK.
Atualizei também o comentário do CMV estimado em `cascata.py` (42,5% → 39,56% de margem implícita).
Spec `docs/specs/2026-07-22-parametros-dre.md`.

## Em aberto pro João conferir
- **Embalagem 0,57% — RESOLVIDO:** o João confirmou que continua em 0,57% (não muda código).
- Conferir os números de junho na tela (MC R$ 2,01M).

## Próximo passo
- **Reiniciar o painel** se for testar ao vivo (`dados.py` e `cascata.py` mudaram; watchdog não instalado).
- Herdadas: a 3.2 ainda tem SKUs sem custo (27 na base final) — o alerta de SKU sem custo
  continua valendo; o `docs/skus-custo-zerado-aba-3-1.csv` (137 SKUs) pode ser re-gerado sobre a 3.2.
