# Sessão 2026-07-15 — Discovery da feature "Portas de entrada" (produto de entrada)

**Modo:** B (construção — mas parou no spec + artefato de dados; build fica pra próxima).
**Duração/foco:** discovery guiado pelo prompt `00-discovery`, precedido de avaliação crítica (Fable).

## O que o João pediu
Criar filtros de segmentação pra enxergar as alavancas que mexem na MC e no LTV do cliente, ancorados
na **1ª compra**: (1) produto de entrada, (2) canal de entrada, (3) oferta de entrada. Pediu (a) ativar
o **Fable** pra avaliar criticamente contra o `motor-crescimento-lucrativo-true-classic.md` e o
`Curso Pedrinho.md`, e (b) conduzir o discovery pra montar o spec.

## Como foi (a linha do tempo)
1. **Fable (avaliação crítica).** Verificou as colunas reais das bases: `hubspot_deals.csv` tem 8 colunas,
   **nenhuma de canal nem de oferta**. Só `itens_historico.csv` permite derivar **produto** da 1ª compra.
   Veredito: começar **só por produto de entrada**; canal e oferta precisam de instrumentação a montante.
   Alertou: o CAC não se segmenta (mídia é bolo mensal) → mostrar **Lucro Bruto/cliente** (numerador puro),
   não fingir ratio; N mínimo por porta; a régua ainda é **parcial** (falta devolução/CX/juros/criativo — e
   devolução por produto é o custo que mais difere entre portas).
2. **Decisão do João:** 1ª leva **só produto**; canal/oferta pro backlog. Métrica = **Lucro Bruto acumulado
   por cliente + (não) recompra** — ele preferiu só o Lucro Bruto.
3. **Discovery (18 perguntas).** Fechou: aba nova; 2 tabelas (principal por safra obedecendo o filtro de
   produto; secundária por linha de produto obedecendo o filtro de data); colunas `1ª compra | 30D (m+0) |
   60D (m+1) | 90D (m+2) | 180D (m+5) | 365D (m+11)` — **mesma régua da Cohorts** (apelidos de mês); célula =
   Lucro Bruto acumulado/cliente; CAC = blended do mês (régua); safra imatura = "—"; **N mínimo 300**.
4. **Produto de entrada = linha de produto** (não SKU, não balde). Regra provisória: pedido de estreia com
   **categoria única** → aquela linha; **mais de uma** → "Multiprodutos"; **brindes removidos antes**;
   sem produto → "Produto desconhecido".
5. **Artefato de dados (em paralelo).** Claude leu os 1,3 M itens, propôs um rascunho de classificação
   (`docs/rascunho-sku-linha-produto.csv`); **João corrigiu à mão no Sheets** e devolveu. Claude limpou
   (unificou grafias duplicadas, marcou papel porta/brinde/desconhecido) e gravou o mapa oficial
   **`bases/mapa_sku_linha_produto.csv`** — **26 linhas-porta** (95,1% un), 3 baldes brinde (2,3%),
   Produto desconhecido (2,6%).

## Decisões que viram régua
- **1ª leva = só produto de entrada** (canal/oferta bloqueados por dado → backlog).
- **Colunas = mesma régua da Cohorts** (nenhum ADR de divergência; "30D" é apelido de "m+0").
- **Célula = Lucro Bruto acumulado/cliente** (reusa `coortes.lucro_bruto`); **CAC = blended do mês** (régua).
- **Produto de entrada = linha de produto**, categoria única; brindes (carteira/BRINDE/Perfume/Skincare)
  removidos; sem produto/sem nome → "Produto desconhecido".
- **N mínimo 300** (ajustável).

## Entregáveis
- `docs/specs/2026-07-15-portas-de-entrada-produto.md` (spec, regras travadas).
- `bases/mapa_sku_linha_produto.csv` (mapa validado — a régua da feature).
- `docs/BACKLOG.md` (novo — canal, oferta, régua fully-loaded, resíduos do mapa).
- `docs/rascunho-sku-linha-produto.csv` (rascunho arquivado).

## Aberto pra próxima sessão (BUILD)
- Construir `views/portas_entrada.py` + motor (provável `portas.py`) reusando `coortes.py`.
- Check de coerência: filtro "todos" = idêntico ao Lucro Bruto acumulado da Cohorts.
- Resolver o detalhe: item "sem nome" na regra de categoria única (Multiprodutos vs ignora).
- Reiniciar o painel ao mexer em módulo (watchdog não instalado).
- Ressalva honesta: a régua segue **Lucro Bruto parcial** (não fully-loaded).

## Nota de método
- Fable rodou como subagente (model fable) e **verificou o dado antes de opinar** — o que derrubou 2 dos 3
  filtros por falta de coluna. Bom exemplo de "não produzir regra sem rastrear a fonte" (mantra nº 3/7).
