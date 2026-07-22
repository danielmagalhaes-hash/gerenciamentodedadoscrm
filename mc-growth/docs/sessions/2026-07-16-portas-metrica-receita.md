# Sessão 2026-07-16 — Portas de entrada: métrica Receita (além do Lucro Bruto)

**Modo:** B (construção). **Objetivo:** na aba "4. Portas de entrada", mostrar também a
**receita acumulada por cliente** por porta, além do Lucro Bruto que já existia.

## O que o João pediu
"Na aba de 4. Portas, vamos adicionar mais duas tabelas, na mesma estrutura das atuais, mas
ao invés de olhar para lucro bruto, bora adicionar receita."

## Decisão de layout (do João)
Em vez de empilhar 4 tabelas, **um seletor de métrica** (Lucro Bruto × Receita) troca o
conteúdo das **mesmas** duas tabelas (por safra + por linha). Página curta. As demais
lentes (switch × "Aumento vs 1ª compra", filtros de produto/data, N mínimo) valem para as
duas métricas.

## O que mudou (só ADIÇÃO — nenhuma conta de dinheiro nova)
- **`portas.py`** — as 4 builders (`_triangulo_lb`, `_lb_primeira_compra`,
  `tabela_por_safra`, `tabela_por_linha`) ganharam o parâmetro **`metrica`**
  (default `"mc_produto"` = Lucro Bruto; `"valor"` = Receita). Só troca a **coluna somada**;
  toda a mecânica (÷ N_S, cumsum na idade, máscara de safra fechada, CAC blended) é a mesma.
  Receita é **bruta**: não desconta mídia nem custo. Como o default é `mc_produto`, os
  callers antigos e o guarda não mudam de comportamento.
- **`views/portas_entrada.py`** — radio "Métrica das tabelas" no topo; rótulos e legendas
  metric-aware (`TERMO`/`TERMO_CELL`); no modo Receita a ressalva de "% de CMV estimado"
  some (a receita = `valor` é sempre real, o CMV estimado não a toca). Passa
  `metrica="valor"`/`"mc_produto"` às builders.
- **`checar_coerencia.py`** — o **check nº 6** agora prova as **duas** métricas: além de
  `portas("todos")` == `coortes.lucro_bruto`, também `portas("todos", metrica="valor")` ==
  `coortes.ltv` (o LTV da Cohorts), e a 1ª compra == `ticket_primeira_compra`.

## Por que é seguro (não inventa dinheiro)
A receita por cliente já existia e já era mostrada na aba **Cohorts** ("Receita por cohort"):
é o `coortes.ltv`. As tabelas novas são o **espelho** dele fatiado por porta — a mesma verdade,
outra dimensão. Nenhuma fonte nova, nenhum custo/CAC recalculado.

## Provas rodadas
- **Guarda `checar_coerencia.py`: 7/7** — `Portas 'todos' × Cohorts (Lucro Bruto 0.00000000 ·
  Receita 0.00000000/cliente) · partição quebrada em 0/64 safras`.
- **`AppTest`**: a aba 4 sobe sem exceção nos **dois modos** (Lucro Bruto e Receita).
- **Sanidade**: Receita ≈ 2,3× o Lucro Bruto por cliente (bruta vs pós-deduções+CMV), ambas
  acumulam nas janelas, máscara de safra imatura preservada. Ex. safra 2026-05, "todos":
  1ª compra Receita R$ 490,14 × LB R$ 209,20; 60D R$ 565,84 × R$ 241,30.

## Ressalvas (inalteradas)
- Lucro Bruto segue **PARCIAL** (sem devolução/CX/juros/criativo). A Receita é bruta (inclui
  frete, aceito como receita — unificação HubSpot 2026-07-14).
- Viés cross-canal e o carimbo de "novo" seguem os de sempre (nada tocado aqui).

## Recarregar o painel
Mexi em **módulo** (`portas.py`) → o `watchdog` não está instalado → **reiniciar o painel**
(`python3 -m streamlit run painel.py`) para o Streamlit pegar a assinatura nova.

## Próximo passo
Commit desta feature + do trabalho de "Portas de entrada" 15–16/jul que ainda está no working
tree sem commit (o João decide quando).
