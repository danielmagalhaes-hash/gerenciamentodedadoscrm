# ADR 2026-07-22 — Aba 3.2 vira a fonte principal de custo por SKU

## Contexto
O Financeiro entregou uma tabela de custo por SKU atualizada ("PREÇO JUNHO"). O João
subiu esses dados numa **aba nova da planilha Google, "3.2. Custos"** (gid `634911340`,
colunas `SKU` + `PREÇO JUNHO`). A esteira de custo tinha duas fontes em cascata desde
2026-07-09 (ADR `2026-07-09-fonte-custos-3-1-com-fallback`): a 3.1 como principal e a 3
como rede de segurança.

## Decisão
A **aba 3.2 passa a ser a fonte principal** de custo. A esteira vira uma **cascata de três
abas** + a correção local:

1. `custos_extra.csv` (correção local do João) — por cima de tudo (inalterado).
2. **3.2** (`634911340`, col `PREÇO JUNHO`) — **principal**.
3. 3.1 (`1460088128`, col `Custo`) — rede de segurança 1 (era a principal).
4. 3 (`423190064`, col `Valor de Custo`) — rede de segurança 2.

Custo é o **1º valor > 0** na ordem acima; **0/vazio = FALTANDO** (cai para a próxima),
como já era. A regra não mudou — ganhou uma camada no topo. Simétrica com as 3 camadas
de itens de `cascata.itens_por_nome`.

**Por que na planilha (e não em `custos_extra.csv`):** a regra da Moon e o próprio projeto
mandam a planilha ser a fonte de verdade de custo — "uma verdade só". O `custos_extra.csv`
é para correções pontuais na tela, não para substituir a base. Manter na planilha deixa a
atualização durável, versionada pelo dono do dado (Financeiro/Dados), e o painel só lê.

## Consequências
- **Cobertura sobe:** SKUs com custo 1.617 → **1.684** (+67); **0 SKUs perderam custo**
  (a cascata garante — quem tinha custo na 3.1/3 e não está na 3.2 herda o valor antigo).
- **Números mudam** (é o esperado — custos novos). **Junho/2026: MC R$ 2.173.703,35 →
  R$ 2.255.165,93 (+R$ 81.462,58 / +3,75%)**; CMV cai o mesmo tanto. A base 3.2 tem custos
  menores em várias famílias (ex.: uma leva 155,00 → 81,21). Meses históricos e coortes
  também se movem (o CMV real é usado em toda a história em 3 camadas).
- **Âncora byte-idêntica de junho aposentada:** o valor documentado R$ 2.173.703,35 era
  a foto com a base 3.1; passa a ser R$ 2.255.165,93 com a 3.2. `checar_coerencia.py`
  segue **7/7** (prova concordância ENTRE telas, não um valor fixo de junho).
- **`GID_CUSTOS_FALLBACK` e `GIDS["Custos"]` saíram** — a lista `FONTES_CUSTO` é o único
  dono dos gids de custo (evita 2ª referência ao mesmo gid).

## Alternativa descartada
Colar os custos em `custos_extra.csv` (sobrescrita local): valeria no painel na hora, mas
criaria uma 2ª verdade (painel divergindo da planilha compartilhada em ~950 SKUs) e
congelaria a atualização — divergência silenciosa quando a planilha mudasse depois.

## Rastro
Spec `docs/specs/2026-07-22-fonte-custos-3-2.md`; ADR anterior
`2026-07-09-fonte-custos-3-1-com-fallback` (agora superado no topo da cascata);
código: `dados.py` (`FONTES_CUSTO`, `carregar_custos`).
