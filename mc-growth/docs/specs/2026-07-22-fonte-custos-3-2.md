# Spec — Aba 3.2 vira a fonte principal de custo por SKU

**Data:** 2026-07-22 · **Modo:** B (construção) · **Toca dinheiro:** SIM (CMV)

## Pergunta / objetivo
O Financeiro mandou uma tabela de custo por SKU atualizada ("PREÇO JUNHO"). O João
subiu esses dados numa **aba nova da planilha Google, "3.2. Custos"** (gid `634911340`,
colunas `SKU` + `PREÇO JUNHO`). Objetivo: fazer o painel **ler a 3.2 como fonte principal
de custo**, mantendo a 3.1 e a 3 como rede de segurança.

## O que muda (regra de negócio)
O custo de um SKU passa a ser o **primeiro que existir com valor > 0**, nesta ordem:

1. `custos_extra.csv` (correção local do João) — **por cima de tudo**, inalterado.
2. **Aba 3.2** (`634911340`, col `PREÇO JUNHO`) — **NOVA fonte principal**.
3. Aba 3.1 (`1460088128`, col `Custo`) — rede de segurança 1 (era a principal).
4. Aba 3 (`423190064`, col `Valor de Custo`) — rede de segurança 2.

**Custo 0/vazio = FALTANDO** (cai para a próxima fonte), como já era. Regra idêntica à
de hoje (spec 2026-07-09), só ganhou **mais uma camada no topo** — vira uma cascata de 3
abas, simétrica com as 3 camadas de itens (`cascata.itens_por_nome`).

## Onde (infra)
- **Só `dados.py`.** `carregar_custos` passa a percorrer uma lista ordenada de fontes
  (`FONTES_CUSTO`). Nenhum outro módulo referencia os gids de custo (verificado).
- **Não** mexe em `cascata.PARAMETROS` (percentuais da DRE) nem em `CMV_ESTIMADO_FRACAO`
  (30% estimado) — o Financeiro atualizou **custo por SKU**, não os percentuais.
- **Não** usa as colunas `PRODUTO`/`PRODUTO DRE` do CSV original (o João já colou só
  `SKU` + `PREÇO JUNHO` na aba). Ficam de backlog se virarem CMV-por-categoria depois.

## Dado medido (antes de aplicar)
- 3.2: 1.073 SKUs, **1.072 com custo > 0** (1 linha "-" ignorada).
- vs base viva: 880 SKUs mudaram (431↑, 449↓), **66 SKUs novos** (mais cobertura),
  122 iguais. Variação mediana −R$ 0,14; famílias caindo forte (ex.: 155,00 → 81,21).

## Critério de aceite (o que conta como pronto)
1. A 3.2 é lida sem erro (colunas `SKU` + `PREÇO JUNHO`).
2. **Cobertura não cai:** nenhum SKU que tinha custo hoje fica sem custo (a cascata garante).
3. `python3 checar_coerencia.py` → **7/7** (as telas seguem concordando).
4. `AppTest` sobe as 6 telas sem exceção.
5. **Impacto na MC de junho medido e reportado** ao João (antes/depois), com rastro.

## Fora de escopo
Percentuais da DRE; CMV estimado 30%; escrever na planilha (o painel só lê); as colunas
extras do CSV. Aba `Parametros` na planilha (segue embutida no código).
