# ADR — O ratio contra o CAC usa LUCRO BRUTO, nunca a MC

- **Data:** 2026-07-14
- **Status:** vigente
- **Quem decidiu:** João (achado dele, vendo a tabela na tela)
- **Contexto:** aba **3. Cohorts**, tabelas de múltiplos do CAC (spec `2026-07-14-coortes-titulos-e-ratios.md`)

## A decisão

Todo ratio "quantas vezes a turma pagou a mídia" tem no numerador o **Lucro Bruto acumulado por
cliente** (o que a turma gerou **antes** da mídia) — **nunca a MC**.

**Empate = `1,00×`** (não zero): a turma devolveu exatamente o que custou trazê-la. Abaixo de
`1,00×` = ainda não pagou a própria mídia (número em vermelho na tela).

## Por quê

A **MC já tem a mídia descontada** — no motor (`coortes.py`, montagem do incremental), o Ad Spend
sai **uma vez**, no m+0, e o acumulado o carrega para as idades seguintes. Dividir a MC pelo CAC
põe a mídia **nos dois lados da conta**: subtraída no numerador e de novo no denominador. O
resultado é um múltiplo que pune a mídia em dobro e desloca a régua (o empate aparecia como
`0,00×`, o que só "funciona" por acidente aritmético — é `MC/CAC = LB/CAC − 1`).

Medido na safra 2026-06 (CAC R$ 173,65): o ratio errado dizia **0,40×**; o certo é **1,40×**. A
diferença é exatamente 1,00 — o CAC cobrado a mais.

## Como fica no código (dono único)

- `coortes.ResultadoCoortes.lucro_bruto` (R$/cliente, acumulado, **sem mídia**) e
  `lucro_bruto_primeira_compra`. Tirados do incremental **ainda cru**, antes de o Ad Spend ser
  subtraído — **não** somando o CAC de volta na tela. Dinheiro tem um dono só (CLAUDE.md §11).
- `coortes_ui.verde_gradiente` ganhou o parâmetro **`limiar`** (a linha do empate): `1,0` no ratio
  de Lucro Bruto, `0,0` no ratio de receita (que não tem empate a marcar).

## O que fica provado (guarda)

**Check nº 5 do `checar_coerencia.py`:** `lucro_bruto = mc_acumulada + CAC` — dif
**0,0000000000** nas 64 safras. É o que garante que a mídia é contada **uma vez só**. Junto:
a linha do `1,00×` **coincide com o payback** do triângulo de MC (0 células divergentes) — as duas
telas contam a mesma história.

## O que isto impede no futuro

- Mostrar `MC ÷ CAC` em qualquer tela (é a mídia em dobro).
- Ler `1,00×` como "bom": é o **empate**, não uma meta. Alvo calibrado de LTV:CAC é **V5**
  (parkeado) — a tela mostra o número, o julgamento é do João.
- Deduzir o Lucro Bruto na camada de tela (somando CAC à MC): o número mora em `coortes.py`.

## Ressalva herdada

O Lucro Bruto da coorte é **parcial**, como a MC: não desconta CX, juros de estoque nem criativo, e
usa **CMV estimado em 30%** fora da janela de itens (célula marcada com `*`). O múltiplo é, por
isso, **otimista** em relação a uma conta de custo cheio.
