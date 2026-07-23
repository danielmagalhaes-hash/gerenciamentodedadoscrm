# Sessão 2026-07-23 — Jornada de Produto

**Modo:** A (análise) → virou código local (`mc-growth/jornada_produto.py`) · **Toca dinheiro:** não (produto e tempo, não receita/custo) · **Destino final:** aba Recompra do `gerenciadordecrm` — **só depois de comando explícito do Daniel**; até lá fica local.

---

## Objetivo

A partir da PORTA DE ENTRADA (produto ou combo da 1ª compra), entender **o que o cliente compra nas compras seguintes e em quanto tempo** — pra decidir o que ofertar depois de cada tipo de entrada. Pergunta original do Daniel (2026-07-23): *"por onde o cliente entra, e quais são os outros produtos que são comprados na segunda, terceira, quarta e outras compras; em quanto tempo isso acontece em média"*.

## Fonte dos dados

Mesmas 3 bases locais que já alimentam o mc-growth (Portas de Entrada / LTV), baixadas do BigQuery pelo Daniel em 2026-07-23:

- `bases/hubspot_deals.csv` — pedidos/clientes (462k linhas)
- `bases/itens_historico.csv` — item a item de cada pedido (1,3M linhas)
- `bases/mapa_sku_linha_produto.csv` — SKU → linha de produto (1.145 SKUs)

Nenhuma base nova; a ponte pedido→item (`cascata.itens_por_nome`, 3 camadas) e o enriquecimento de safra/idade (`coortes.preparar_deals_cache`) são os MESMOS do painel principal do mc-growth. Só a **classificação de produto/combo** é própria deste módulo (ver Metodologia).

---

## Decisões tomadas nesta sessão (ordem cronológica)

1. **Escopo definido:** a partir do produto de entrada (produto único, mesma régua da aba "Portas de Entrada"), mapear os produtos das compras 2ª–5ª+ e o tempo até cada uma (visão acumulada desde a entrada + visão de intervalo entre recompras).
2. **Camiseta Minimal segmentada por quantidade** — picos reais medidos na base: 1, 4, 6, 10 unidades. Qualquer outra quantidade cai em "outras qtd".
3. **11 combos aprovados** para virarem porta de entrada própria (7 pedidos + 4 descobertos na análise de frequência da base e aprovados pelo Daniel): Camiseta + Calça Alfaiataria, Camiseta + Camisa Henley, Camiseta + Camiseta Fitness, Camiseta + Carteira, Camiseta + Comfort, Camiseta + Cueca, Camiseta + Jeans, Camiseta + Perfume, Camiseta + Polo 2.0, Camiseta + Social, Jeans + Comfort.
4. **Carteira e Perfume separados** do SKU genérico "BRINDE" do mc-growth (que misturava os dois): SKU 8301007000 = Carteira; SKUs 1301002011, 1301002012, 1301002112 = Perfume (brinde).
5. **Sub-linhas genéricas nos combos** — Jeans 1.0/2.0 e Social Tech Classics/Malha juntam num nome só ("Jeans", "Social") só para efeito de combo; a entrada de produto único continua usando o nome específico.
6. **Limpeza:** entrada com menos de 1000 clientes sai da análise inteira (não só da tela) — de 45 entradas caiu para **20**.
7. **Bug 1 corrigido (retenção zerada):** a compra seguinte nunca levava o sufixo de quantidade ("Camiseta Minimal", nunca "Camiseta Minimal (4 un)"), então a comparação "mesmo produto" nunca batia com a entrada. Corrigido comparando pela FAMÍLIA do produto (`familia_entrada`).
8. **Bug 2 corrigido (denominador errado):** a % de cada compra usava como base "quem chegou pelo menos na 2ª compra" em vez do total da entrada — somava 100% na 2ª mas caía sem sentido nas seguintes, misturando "não comprou esse produto de novo" com "nem voltou". Corrigido fixando o denominador em `entrada_por_cliente.value_counts()` (o tamanho TOTAL da entrada) em todas as posições.
9. **Pivot principal — presença de produto, não classificação exclusiva.** A 1ª versão classificava o PEDIDO INTEIRO (produto único, um dos 11 combos, ou "Multiprodutos"/"Produto desconhecido") — isso enterrava informação real toda vez que o carrinho não batia com a lista fixa. A versão final pergunta "quais produtos apareceram nessa compra" (não exclusivo: um pedido com Camiseta+Jeans conta pras duas linhas). "Multiprodutos"/"Produto desconhecido" saíram da lista de oferta.
10. **Árvore de jornada removida.** Foi construída, mas a árvore precisa de ramos EXCLUSIVOS (um cliente só pode estar num ramo por vez) — incompatível com presença de produto (um cliente pode estar em vários produtos ao mesmo tempo). Substituída pela tabela de afinidade por compra.
11. **Transparência do funil:** a tabela agora mostra TODOS os produtos (sem corte de top-N escondido) + uma linha "Não fez essa compra" + um card com essa %, pra nunca parecer que os números "somam pouco" sem explicar que a maior parte é gente que não voltou.
12. **LTV, taxa de repetição e taxa de reativação adicionados** (pedido do Daniel, 2026-07-23, 2ª rodada) — reaproveitando a régua OFICIAL já validada com ele em 2026-07-21 para `fact_repurchase_monthly_metrics` (recente = 6 meses, inativo = mais de 11 meses sem comprar), adaptada de "mensal/global" pra "foto de hoje, por produto de entrada".
13. **Bug 3 corrigido (retenção de combo sempre 0%):** o combo usa nome GENÉRICO na régua de retenção ("Jeans"), mas a presença crua só tem nomes ESPECÍFICOS ("Calça Jeans 1.0") — sem aliasar a comparação, "Camiseta + Jeans" e "Camiseta + Social" davam sempre 0%. Corrigido comparando cada linha exigida contra a presença direta OU aliasada (não as duas juntas de uma vez, que quebrava a entrada solo).
14. **Bug 4 corrigido (cliente contado 2× na tabela por momento):** um cliente pode ter mais de uma compra do mesmo tipo ("Repetição", por exemplo) na vida dele — contar por EVENTO em vez de por CLIENTE inflava o número (uma linha chegou a mostrar mais clientes que a própria base). Corrigido contando cliente distinto por produto.

---

## Metodologia final

### Elegibilidade da entrada
- Deal `Shipped` (Shopify) na idade 0 (a estreia real do cliente — mesma régua de `portas._estreias`).
- Produto único (1 linha de papel "porta") **ou** um dos 11 combos aprovados.
- Entrada com menos de 1000 clientes → excluída da análise.

### "O que ofertar" (afinidade por compra)
Para cada (entrada, compra Nª), cada LINHA presente naquela compra específica conta — não é a classificação do pedido inteiro. `% da entrada` = `clientes com aquela linha presente ÷ tamanho TOTAL da entrada × 100` (denominador fixo, igual em toda posição). Célula com menos de 30 clientes não é reportada.

### Retenção ("tem o mesmo produto de novo")
Solo: a linha da família precisa estar presente (pode vir mais coisa junto). Combo: as 2 linhas do combo precisam estar AMBAS presentes.

### Tempo até a próxima compra
Duas visões, mediana em dias: **acumulado** (da entrada até a compra N) e **entre recompras** (da compra N-1 até a N).

### LTV 180 dias
Σ `valor` de todas as compras do cliente dentro de 180 dias desde a entrada (inclui a própria compra de entrada). Quem não voltou entra com o valor só da entrada — não é excluído nem zerado.

### Status do cliente HOJE / taxas por entrada
Régua OFICIAL de `fact_repurchase_monthly_metrics` (validada com o Daniel em 2026-07-21), adaptada de mensal/global pra foto de hoje / por entrada:

- **Recente** = a entrada (1ª compra) foi há menos de 6 meses.
- **Ativo** = não é recente, e a ÚLTIMA compra foi há até 11 meses (a "janela de atividade" ainda está aberta).
- **Inativo** = mais de 11 meses sem comprar (a janela fechou).

Essas 3 são o status ATUAL do cliente (uma foto de hoje). Já **taxa de repetição** e **taxa de reativação** olham a vida INTEIRA do cliente (todo evento de compra que ele já teve, não só o status de hoje):

- **Taxa de repetição** (por entrada) = % da entrada que já teve, alguma vez, uma compra classificada "Repetição" — comprou de novo DENTRO da janela de 11 meses, já fora do 1º semestre de vida.
- **Taxa de reativação** (por entrada) = % da entrada que já teve, alguma vez, uma compra classificada "Reativação" — voltou a comprar DEPOIS da janela ter fechado (tinha ficado inativo).

Cada COMPRA (não o cliente) é classificada em um dos 3 momentos: **Recente** (menos de 6 meses desde a entrada do cliente), **Reativação** (gap desde a compra anterior maior que 11 meses) ou **Repetição** (o resto). Isso alimenta as 3 tabelas segmentadas da seção seguinte.

---

## LTV, repetição e reativação — as 20 entradas

| Entrada | Clientes | LTV 180d (mediana) | LTV 180d (média) | Taxa repetição | Taxa reativação | Recente hoje | Ativo hoje | Inativo hoje |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Camiseta Minimal (4 un) | 84.413 | R$ 457.23 | R$ 565.99 | 13.8% | 11.2% | 12.9% | 35.7% | 51.4% |
| Camiseta Minimal (1 un) | 60.803 | R$ 147.01 | R$ 243.32 | 12.9% | 10.0% | 8.5% | 24.5% | 67.0% |
| Camiseta Minimal (outras qtd) | 38.274 | R$ 422.77 | R$ 559.62 | 15.9% | 12.4% | 5.6% | 33.1% | 61.3% |
| Camiseta + Carteira | 5.933 | R$ 473.35 | R$ 582.39 | 1.2% | 0.3% | 73.5% | 21.4% | 5.1% |
| Calça Jeans 1.0 | 5.804 | R$ 369.07 | R$ 588.71 | 8.4% | 1.7% | 29.9% | 40.2% | 29.9% |
| Camiseta Minimal (6 un) | 5.130 | R$ 669.50 | R$ 793.26 | 13.1% | 8.9% | 7.8% | 40.6% | 51.5% |
| Camiseta + Jeans | 3.833 | R$ 752.71 | R$ 920.47 | 10.4% | 2.4% | 19.1% | 53.5% | 27.4% |
| Camiseta + Cueca | 3.475 | R$ 568.22 | R$ 697.00 | 20.6% | 18.1% | 6.9% | 28.9% | 64.2% |
| Camisa Social Tech Classics | 3.284 | R$ 629.87 | R$ 753.25 | 9.0% | 3.6% | 15.5% | 37.5% | 47.0% |
| Camiseta + Camiseta Fitness | 3.270 | R$ 602.02 | R$ 750.97 | 13.4% | 7.7% | 13.9% | 35.7% | 50.4% |
| Camiseta Fitness | 3.233 | R$ 344.67 | R$ 424.41 | 10.5% | 7.1% | 11.5% | 29.2% | 59.3% |
| Overshirt | 2.711 | R$ 391.56 | R$ 510.09 | 2.7% | 0.5% | 73.9% | 14.6% | 11.4% |
| Outros Produtos | 2.141 | R$ 398.32 | R$ 480.04 | 10.6% | 7.5% | 7.7% | 21.3% | 70.9% |
| Cueca | 1.990 | R$ 351.31 | R$ 396.40 | 17.8% | 19.9% | 5.3% | 19.0% | 75.6% |
| Calça Comfort | 1.793 | R$ 499.90 | R$ 814.29 | 2.1% | 0.0% | 67.0% | 32.2% | 0.7% |
| Camiseta Manga Longa | 1.790 | R$ 335.80 | R$ 436.40 | 17.9% | 13.3% | 5.4% | 20.4% | 74.2% |
| Camisa Henley | 1.488 | R$ 406.50 | R$ 517.25 | 8.3% | 1.4% | 20.0% | 38.0% | 42.0% |
| Camiseta + Perfume | 1.435 | R$ 482.23 | R$ 723.93 | 4.9% | 2.4% | 62.4% | 16.6% | 21.0% |
| Camiseta + Social | 1.314 | R$ 880.31 | R$ 1123.95 | 14.9% | 5.5% | 6.8% | 47.1% | 46.0% |
| Polo 2.0 | 1.043 | R$ 458.39 | R$ 581.17 | 0.9% | 0.0% | 57.0% | 43.0% | 0.0% |

---

## As 3 análises segmentadas — entrada + produtos por momento da compra

Pedido do Daniel (2026-07-23, 2ª rodada): pra clientes **recentes**, entrada + próximas compras; pra **ativos não recentes**, entrada + produtos que mais REPETEM; pra **inativos**, entrada + produtos que mais REATIVAM. Adaptação: em vez de olhar o status do CLIENTE hoje, cada tabela olha as COMPRAS que aconteceram naquele momento específico da vida do cliente (ver Metodologia) — assim dá pra listar produto, não só um rótulo de status.

### 1) Clientes recentes — entrada + próximas compras
Compras feitas ainda dentro do 1º semestre de vida do cliente (< 6 meses desde a entrada).

**Camiseta Minimal (4 un)** — 14.400 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 11.420 | 79.31% |
| Calça Jeans 1.0 | 1.266 | 8.79% |
| Cueca | 864 | 6.00% |
| Camiseta Fitness | 836 | 5.81% |
| Outros Produtos | 810 | 5.62% |
| Camiseta Manga Longa | 766 | 5.32% |
| Camisa Social Tech Classics | 488 | 3.39% |
| Carteira | 471 | 3.27% |
| Perfume | 446 | 3.10% |
| Calça Alfaiataria | 352 | 2.44% |
| Camisa Henley | 349 | 2.42% |
| Polo 2.0 | 347 | 2.41% |
| Calça Comfort | 291 | 2.02% |
| Overshirt | 158 | 1.10% |
| Calça Jeans 2.0 | 143 | 0.99% |
| Cueca Fitness | 98 | 0.68% |
| Polo Tricot | 95 | 0.66% |
| Suéter Classic 2026 | 80 | 0.56% |
| Suéter Zíper | 80 | 0.56% |
| Polo 1.0 | 64 | 0.44% |
| Camisa Social Malha | 61 | 0.42% |
| Camiseta Fitness Manga Longa | 47 | 0.33% |
| Jaqueta Essential | 43 | 0.30% |
| Camiseta Gola Alta Manga Longa | 29 | 0.20% |
| Camiseta Modal Tech | 26 | 0.18% |
| Calça Essential | 26 | 0.18% |
| Jaqueta Westfield | 25 | 0.17% |
| Camiseta Gola Alta Manga Curta | 15 | 0.10% |

**Camiseta Minimal (1 un)** — 12.367 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 11.178 | 90.39% |
| Camiseta Fitness | 567 | 4.58% |
| Calça Jeans 1.0 | 531 | 4.29% |
| Cueca | 477 | 3.86% |
| Camiseta Manga Longa | 460 | 3.72% |
| Outros Produtos | 389 | 3.15% |
| Camisa Social Tech Classics | 250 | 2.02% |
| Perfume | 246 | 1.99% |
| Camisa Henley | 195 | 1.58% |
| Carteira | 176 | 1.42% |
| Calça Alfaiataria | 131 | 1.06% |
| Polo 2.0 | 121 | 0.98% |
| Calça Comfort | 67 | 0.54% |
| Cueca Fitness | 58 | 0.47% |
| Overshirt | 56 | 0.45% |
| Polo 1.0 | 51 | 0.41% |
| Polo Tricot | 33 | 0.27% |
| Suéter Classic 2026 | 31 | 0.25% |
| Calça Jeans 2.0 | 25 | 0.20% |
| Suéter Zíper | 21 | 0.17% |
| Camiseta Fitness Manga Longa | 19 | 0.15% |
| Camiseta Modal Tech | 16 | 0.13% |
| Jaqueta Essential | 13 | 0.11% |
| Camisa Social Malha | 10 | 0.08% |
| Camiseta Gola Alta Manga Longa | 8 | 0.06% |
| Camiseta Gola Alta Manga Curta | 8 | 0.06% |
| Calça Essential | 6 | 0.05% |
| Jaqueta Westfield | 6 | 0.05% |

**Camiseta Minimal (outras qtd)** — 7.559 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 6.371 | 84.28% |
| Calça Jeans 1.0 | 513 | 6.79% |
| Cueca | 462 | 6.11% |
| Camiseta Fitness | 458 | 6.06% |
| Camiseta Manga Longa | 458 | 6.06% |
| Outros Produtos | 384 | 5.08% |
| Camisa Social Tech Classics | 242 | 3.20% |
| Perfume | 212 | 2.80% |
| Carteira | 196 | 2.59% |
| Calça Alfaiataria | 161 | 2.13% |
| Polo 2.0 | 150 | 1.98% |
| Camisa Henley | 146 | 1.93% |
| Calça Comfort | 104 | 1.38% |
| Overshirt | 58 | 0.77% |
| Cueca Fitness | 49 | 0.65% |
| Polo 1.0 | 49 | 0.65% |
| Suéter Zíper | 35 | 0.46% |
| Suéter Classic 2026 | 34 | 0.45% |
| Polo Tricot | 28 | 0.37% |
| Calça Jeans 2.0 | 26 | 0.34% |
| Camiseta Modal Tech | 17 | 0.22% |
| Camisa Social Malha | 16 | 0.21% |
| Camiseta Fitness Manga Longa | 13 | 0.17% |
| Jaqueta Westfield | 9 | 0.12% |
| Jaqueta Essential | 5 | 0.07% |
| Camiseta Gola Alta Manga Curta | 5 | 0.07% |
| Camiseta Gola Alta Manga Longa | 4 | 0.05% |
| Calça Essential | 3 | 0.04% |

**Camiseta + Carteira** — 433 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 304 | 70.21% |
| Calça Jeans 1.0 | 53 | 12.24% |
| Carteira | 48 | 11.09% |
| Cueca | 25 | 5.77% |
| Perfume | 23 | 5.31% |
| Overshirt | 22 | 5.08% |
| Outros Produtos | 22 | 5.08% |
| Calça Jeans 2.0 | 22 | 5.08% |
| Camisa Social Tech Classics | 21 | 4.85% |
| Calça Alfaiataria | 21 | 4.85% |
| Calça Comfort | 17 | 3.93% |
| Camisa Henley | 17 | 3.93% |
| Polo 2.0 | 17 | 3.93% |
| Camiseta Fitness | 16 | 3.70% |
| Camiseta Manga Longa | 13 | 3.00% |
| Suéter Zíper | 9 | 2.08% |
| Suéter Classic 2026 | 8 | 1.85% |
| Camisa Social Malha | 5 | 1.15% |
| Camiseta Gola Alta Manga Longa | 5 | 1.15% |
| Camiseta Gola Alta Manga Curta | 5 | 1.15% |
| Jaqueta Essential | 4 | 0.92% |
| Camiseta Modal Tech | 4 | 0.92% |
| Polo Tricot | 4 | 0.92% |
| Jaqueta Westfield | 3 | 0.69% |
| Cueca Fitness | 3 | 0.69% |
| Calça Essential | 1 | 0.23% |
| Camiseta Fitness Manga Longa | 1 | 0.23% |
| Polo 1.0 | 1 | 0.23% |

**Calça Jeans 1.0** — 1.134 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Calça Jeans 1.0 | 604 | 53.26% |
| Camiseta Minimal | 407 | 35.89% |
| Calça Jeans 2.0 | 112 | 9.88% |
| Calça Comfort | 81 | 7.14% |
| Calça Alfaiataria | 74 | 6.53% |
| Outros Produtos | 70 | 6.17% |
| Camisa Social Tech Classics | 49 | 4.32% |
| Camiseta Fitness | 43 | 3.79% |
| Carteira | 41 | 3.62% |
| Polo 2.0 | 41 | 3.62% |
| Perfume | 38 | 3.35% |
| Cueca | 38 | 3.35% |
| Overshirt | 37 | 3.26% |
| Camisa Henley | 28 | 2.47% |
| Polo Tricot | 21 | 1.85% |
| Camiseta Manga Longa | 20 | 1.76% |
| Suéter Zíper | 17 | 1.50% |
| Camiseta Modal Tech | 11 | 0.97% |
| Jaqueta Essential | 11 | 0.97% |
| Camisa Social Malha | 11 | 0.97% |
| Camiseta Fitness Manga Longa | 7 | 0.62% |
| Cueca Fitness | 7 | 0.62% |
| Jaqueta Westfield | 6 | 0.53% |
| Suéter Classic 2026 | 6 | 0.53% |
| Calça Essential | 5 | 0.44% |
| Camiseta Gola Alta Manga Curta | 4 | 0.35% |
| Camiseta Gola Alta Manga Longa | 3 | 0.26% |
| Polo 1.0 | 3 | 0.26% |

**Camiseta Minimal (6 un)** — 861 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 682 | 79.21% |
| Calça Jeans 1.0 | 75 | 8.71% |
| Outros Produtos | 71 | 8.25% |
| Camiseta Fitness | 68 | 7.90% |
| Camiseta Manga Longa | 42 | 4.88% |
| Camisa Social Tech Classics | 38 | 4.41% |
| Cueca | 34 | 3.95% |
| Perfume | 34 | 3.95% |
| Carteira | 33 | 3.83% |
| Calça Alfaiataria | 23 | 2.67% |
| Polo 2.0 | 22 | 2.56% |
| Camisa Henley | 21 | 2.44% |
| Calça Comfort | 18 | 2.09% |
| Suéter Classic 2026 | 15 | 1.74% |
| Polo 1.0 | 10 | 1.16% |
| Cueca Fitness | 5 | 0.58% |
| Suéter Zíper | 4 | 0.46% |
| Calça Jeans 2.0 | 4 | 0.46% |
| Overshirt | 4 | 0.46% |
| Camiseta Modal Tech | 2 | 0.23% |
| Jaqueta Westfield | 2 | 0.23% |
| Calça Essential | 2 | 0.23% |
| Jaqueta Essential | 2 | 0.23% |
| Camisa Social Malha | 2 | 0.23% |
| Polo Tricot | 2 | 0.23% |
| Camiseta Fitness Manga Longa | 1 | 0.12% |
| Camiseta Gola Alta Manga Curta | 1 | 0.12% |
| Camiseta Gola Alta Manga Longa | 1 | 0.12% |

**Camiseta + Jeans** — 793 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 503 | 63.43% |
| Calça Jeans 1.0 | 355 | 44.77% |
| Outros Produtos | 71 | 8.95% |
| Camiseta Fitness | 62 | 7.82% |
| Camisa Social Tech Classics | 59 | 7.44% |
| Calça Alfaiataria | 52 | 6.56% |
| Calça Jeans 2.0 | 50 | 6.31% |
| Cueca | 45 | 5.67% |
| Calça Comfort | 44 | 5.55% |
| Carteira | 43 | 5.42% |
| Perfume | 43 | 5.42% |
| Polo 2.0 | 38 | 4.79% |
| Camisa Henley | 37 | 4.67% |
| Camiseta Manga Longa | 28 | 3.53% |
| Overshirt | 22 | 2.77% |
| Cueca Fitness | 16 | 2.02% |
| Suéter Zíper | 14 | 1.77% |
| Polo Tricot | 10 | 1.26% |
| Jaqueta Westfield | 7 | 0.88% |
| Camiseta Modal Tech | 7 | 0.88% |
| Camisa Social Malha | 6 | 0.76% |
| Camiseta Gola Alta Manga Curta | 5 | 0.63% |
| Jaqueta Essential | 4 | 0.50% |
| Suéter Classic 2026 | 4 | 0.50% |
| Camiseta Fitness Manga Longa | 4 | 0.50% |
| Polo 1.0 | 3 | 0.38% |
| Calça Essential | 3 | 0.38% |
| Camiseta Gola Alta Manga Longa | 2 | 0.25% |

**Camiseta + Cueca** — 798 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 611 | 76.57% |
| Cueca | 321 | 40.23% |
| Outros Produtos | 74 | 9.27% |
| Camiseta Manga Longa | 61 | 7.64% |
| Camiseta Fitness | 58 | 7.27% |
| Calça Jeans 1.0 | 41 | 5.14% |
| Camisa Social Tech Classics | 27 | 3.38% |
| Cueca Fitness | 25 | 3.13% |
| Carteira | 18 | 2.26% |
| Perfume | 15 | 1.88% |
| Calça Alfaiataria | 13 | 1.63% |
| Calça Comfort | 11 | 1.38% |
| Suéter Classic 2026 | 9 | 1.13% |
| Polo 1.0 | 9 | 1.13% |
| Camisa Henley | 8 | 1.00% |
| Polo 2.0 | 6 | 0.75% |
| Overshirt | 3 | 0.38% |
| Suéter Zíper | 3 | 0.38% |
| Calça Jeans 2.0 | 3 | 0.38% |
| Camiseta Modal Tech | 2 | 0.25% |
| Jaqueta Essential | 1 | 0.13% |

**Camisa Social Tech Classics** — 624 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camisa Social Tech Classics | 356 | 57.05% |
| Camiseta Minimal | 233 | 37.34% |
| Calça Alfaiataria | 72 | 11.54% |
| Calça Jeans 1.0 | 59 | 9.46% |
| Outros Produtos | 45 | 7.21% |
| Perfume | 33 | 5.29% |
| Camisa Henley | 31 | 4.97% |
| Carteira | 30 | 4.81% |
| Camiseta Fitness | 28 | 4.49% |
| Overshirt | 20 | 3.21% |
| Cueca | 18 | 2.88% |
| Calça Comfort | 14 | 2.24% |
| Camiseta Manga Longa | 14 | 2.24% |
| Polo 2.0 | 13 | 2.08% |
| Polo 1.0 | 13 | 2.08% |
| Camisa Social Malha | 12 | 1.92% |
| Suéter Zíper | 7 | 1.12% |
| Polo Tricot | 6 | 0.96% |
| Suéter Classic 2026 | 3 | 0.48% |
| Jaqueta Essential | 2 | 0.32% |
| Calça Essential | 2 | 0.32% |
| Camiseta Modal Tech | 2 | 0.32% |
| Calça Jeans 2.0 | 2 | 0.32% |
| Cueca Fitness | 1 | 0.16% |
| Jaqueta Westfield | 1 | 0.16% |
| Camiseta Fitness Manga Longa | 1 | 0.16% |

**Camiseta + Camiseta Fitness** — 728 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 529 | 72.66% |
| Camiseta Fitness | 265 | 36.40% |
| Calça Jeans 1.0 | 79 | 10.85% |
| Outros Produtos | 64 | 8.79% |
| Camisa Social Tech Classics | 51 | 7.01% |
| Cueca | 42 | 5.77% |
| Carteira | 42 | 5.77% |
| Calça Alfaiataria | 32 | 4.40% |
| Camiseta Manga Longa | 31 | 4.26% |
| Perfume | 31 | 4.26% |
| Camisa Henley | 24 | 3.30% |
| Calça Comfort | 18 | 2.47% |
| Cueca Fitness | 15 | 2.06% |
| Polo 2.0 | 15 | 2.06% |
| Overshirt | 13 | 1.79% |
| Camiseta Fitness Manga Longa | 9 | 1.24% |
| Calça Jeans 2.0 | 8 | 1.10% |
| Suéter Zíper | 6 | 0.82% |
| Polo Tricot | 6 | 0.82% |
| Polo 1.0 | 4 | 0.55% |
| Jaqueta Westfield | 3 | 0.41% |
| Suéter Classic 2026 | 2 | 0.27% |
| Camisa Social Malha | 2 | 0.27% |
| Camiseta Gola Alta Manga Longa | 2 | 0.27% |
| Jaqueta Essential | 2 | 0.27% |
| Camiseta Modal Tech | 1 | 0.14% |
| Camiseta Gola Alta Manga Curta | 1 | 0.14% |

**Camiseta Fitness** — 633 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 367 | 57.98% |
| Camiseta Fitness | 253 | 39.97% |
| Outros Produtos | 43 | 6.79% |
| Calça Jeans 1.0 | 34 | 5.37% |
| Camisa Social Tech Classics | 29 | 4.58% |
| Cueca | 26 | 4.11% |
| Camiseta Manga Longa | 18 | 2.84% |
| Cueca Fitness | 17 | 2.69% |
| Camisa Henley | 14 | 2.21% |
| Polo 2.0 | 12 | 1.90% |
| Calça Alfaiataria | 11 | 1.74% |
| Camiseta Fitness Manga Longa | 11 | 1.74% |
| Carteira | 11 | 1.74% |
| Perfume | 9 | 1.42% |
| Calça Jeans 2.0 | 4 | 0.63% |
| Suéter Classic 2026 | 4 | 0.63% |
| Overshirt | 3 | 0.47% |
| Jaqueta Westfield | 2 | 0.32% |
| Camiseta Modal Tech | 2 | 0.32% |
| Calça Comfort | 2 | 0.32% |
| Polo 1.0 | 2 | 0.32% |
| Polo Tricot | 1 | 0.16% |
| Suéter Zíper | 1 | 0.16% |

**Overshirt** — 280 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Overshirt | 132 | 47.14% |
| Camiseta Minimal | 69 | 24.64% |
| Calça Comfort | 26 | 9.29% |
| Jaqueta Westfield | 18 | 6.43% |
| Suéter Zíper | 15 | 5.36% |
| Camisa Henley | 15 | 5.36% |
| Outros Produtos | 14 | 5.00% |
| Camiseta Gola Alta Manga Curta | 13 | 4.64% |
| Calça Jeans 1.0 | 12 | 4.29% |
| Carteira | 9 | 3.21% |
| Calça Alfaiataria | 8 | 2.86% |
| Camiseta Manga Longa | 8 | 2.86% |
| Cueca | 8 | 2.86% |
| Camiseta Gola Alta Manga Longa | 7 | 2.50% |
| Polo Tricot | 6 | 2.14% |
| Calça Jeans 2.0 | 5 | 1.79% |
| Camisa Social Tech Classics | 4 | 1.43% |
| Polo 2.0 | 4 | 1.43% |
| Suéter Classic 2026 | 3 | 1.07% |
| Camisa Social Malha | 3 | 1.07% |
| Camiseta Fitness | 3 | 1.07% |
| Calça Essential | 3 | 1.07% |
| Perfume | 2 | 0.71% |
| Camiseta Fitness Manga Longa | 2 | 0.71% |
| Jaqueta Essential | 1 | 0.36% |

**Outros Produtos** — 296 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 145 | 48.99% |
| Outros Produtos | 95 | 32.09% |
| Cueca | 24 | 8.11% |
| Camiseta Manga Longa | 24 | 8.11% |
| Calça Jeans 1.0 | 22 | 7.43% |
| Camiseta Fitness | 16 | 5.41% |
| Calça Comfort | 9 | 3.04% |
| Calça Alfaiataria | 8 | 2.70% |
| Polo 2.0 | 7 | 2.36% |
| Suéter Classic 2026 | 7 | 2.36% |
| Suéter Zíper | 5 | 1.69% |
| Camisa Social Tech Classics | 5 | 1.69% |
| Overshirt | 5 | 1.69% |
| Carteira | 3 | 1.01% |
| Cueca Fitness | 3 | 1.01% |
| Camiseta Fitness Manga Longa | 2 | 0.68% |
| Camisa Henley | 2 | 0.68% |
| Perfume | 2 | 0.68% |
| Polo 1.0 | 2 | 0.68% |
| Calça Essential | 1 | 0.34% |
| Polo Tricot | 1 | 0.34% |

**Cueca** — 326 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 195 | 59.82% |
| Cueca | 124 | 38.04% |
| Camiseta Manga Longa | 31 | 9.51% |
| Outros Produtos | 21 | 6.44% |
| Calça Jeans 1.0 | 14 | 4.29% |
| Camiseta Fitness | 8 | 2.45% |
| Cueca Fitness | 5 | 1.53% |
| Perfume | 4 | 1.23% |
| Calça Alfaiataria | 3 | 0.92% |
| Carteira | 3 | 0.92% |
| Polo 2.0 | 3 | 0.92% |
| Calça Comfort | 2 | 0.61% |
| Calça Jeans 2.0 | 2 | 0.61% |
| Camisa Social Tech Classics | 2 | 0.61% |
| Overshirt | 2 | 0.61% |
| Polo 1.0 | 1 | 0.31% |
| Camisa Henley | 1 | 0.31% |
| Suéter Zíper | 1 | 0.31% |
| Suéter Classic 2026 | 1 | 0.31% |
| Jaqueta Essential | 1 | 0.31% |

**Calça Comfort** — 441 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Calça Comfort | 261 | 59.18% |
| Camiseta Minimal | 118 | 26.76% |
| Calça Jeans 1.0 | 95 | 21.54% |
| Overshirt | 35 | 7.94% |
| Calça Jeans 2.0 | 35 | 7.94% |
| Outros Produtos | 31 | 7.03% |
| Calça Alfaiataria | 29 | 6.58% |
| Polo 2.0 | 23 | 5.22% |
| Camisa Social Tech Classics | 18 | 4.08% |
| Camiseta Fitness | 15 | 3.40% |
| Camisa Henley | 14 | 3.17% |
| Camisa Social Malha | 13 | 2.95% |
| Calça Essential | 13 | 2.95% |
| Polo Tricot | 12 | 2.72% |
| Camiseta Gola Alta Manga Curta | 11 | 2.49% |
| Jaqueta Essential | 9 | 2.04% |
| Carteira | 7 | 1.59% |
| Cueca | 7 | 1.59% |
| Suéter Classic 2026 | 7 | 1.59% |
| Camiseta Gola Alta Manga Longa | 7 | 1.59% |
| Suéter Zíper | 7 | 1.59% |
| Perfume | 6 | 1.36% |
| Jaqueta Westfield | 5 | 1.13% |
| Camiseta Manga Longa | 4 | 0.91% |
| Cueca Fitness | 2 | 0.45% |
| Camiseta Fitness Manga Longa | 2 | 0.45% |
| Camiseta Modal Tech | 2 | 0.45% |

**Camiseta Manga Longa** — 341 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 204 | 59.82% |
| Camiseta Manga Longa | 112 | 32.84% |
| Outros Produtos | 39 | 11.44% |
| Camiseta Fitness | 17 | 4.99% |
| Cueca | 16 | 4.69% |
| Calça Jeans 1.0 | 15 | 4.40% |
| Suéter Classic 2026 | 7 | 2.05% |
| Camisa Social Tech Classics | 6 | 1.76% |
| Calça Comfort | 6 | 1.76% |
| Camisa Henley | 5 | 1.47% |
| Camiseta Fitness Manga Longa | 5 | 1.47% |
| Carteira | 4 | 1.17% |
| Polo 2.0 | 4 | 1.17% |
| Overshirt | 3 | 0.88% |
| Perfume | 3 | 0.88% |
| Polo 1.0 | 2 | 0.59% |
| Calça Alfaiataria | 2 | 0.59% |
| Suéter Zíper | 1 | 0.29% |
| Camiseta Modal Tech | 1 | 0.29% |
| Cueca Fitness | 1 | 0.29% |

**Camisa Henley** — 261 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camisa Henley | 118 | 45.21% |
| Camiseta Minimal | 101 | 38.70% |
| Overshirt | 22 | 8.43% |
| Calça Jeans 1.0 | 22 | 8.43% |
| Camisa Social Tech Classics | 19 | 7.28% |
| Outros Produtos | 17 | 6.51% |
| Calça Alfaiataria | 14 | 5.36% |
| Camiseta Fitness | 14 | 5.36% |
| Polo Tricot | 14 | 5.36% |
| Carteira | 13 | 4.98% |
| Cueca | 13 | 4.98% |
| Polo 2.0 | 13 | 4.98% |
| Calça Comfort | 12 | 4.60% |
| Suéter Zíper | 10 | 3.83% |
| Camiseta Manga Longa | 8 | 3.07% |
| Perfume | 8 | 3.07% |
| Camiseta Gola Alta Manga Longa | 2 | 0.77% |
| Cueca Fitness | 2 | 0.77% |
| Camisa Social Malha | 2 | 0.77% |
| Calça Jeans 2.0 | 2 | 0.77% |
| Camiseta Fitness Manga Longa | 2 | 0.77% |
| Camiseta Gola Alta Manga Curta | 1 | 0.38% |
| Camiseta Modal Tech | 1 | 0.38% |
| Jaqueta Essential | 1 | 0.38% |
| Jaqueta Westfield | 1 | 0.38% |

**Camiseta + Perfume** — 193 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 139 | 72.02% |
| Perfume | 31 | 16.06% |
| Calça Jeans 1.0 | 22 | 11.40% |
| Carteira | 18 | 9.33% |
| Camiseta Fitness | 13 | 6.74% |
| Overshirt | 12 | 6.22% |
| Outros Produtos | 9 | 4.66% |
| Camisa Henley | 8 | 4.15% |
| Cueca | 8 | 4.15% |
| Calça Alfaiataria | 8 | 4.15% |
| Calça Comfort | 6 | 3.11% |
| Suéter Zíper | 6 | 3.11% |
| Calça Jeans 2.0 | 5 | 2.59% |
| Camisa Social Tech Classics | 5 | 2.59% |
| Camiseta Manga Longa | 5 | 2.59% |
| Calça Essential | 2 | 1.04% |
| Polo Tricot | 2 | 1.04% |
| Camiseta Gola Alta Manga Longa | 2 | 1.04% |
| Cueca Fitness | 1 | 0.52% |
| Jaqueta Essential | 1 | 0.52% |
| Suéter Classic 2026 | 1 | 0.52% |
| Polo 1.0 | 1 | 0.52% |
| Camiseta Gola Alta Manga Curta | 1 | 0.52% |
| Camiseta Fitness Manga Longa | 1 | 0.52% |

**Camiseta + Social** — 383 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 250 | 65.27% |
| Camisa Social Tech Classics | 164 | 42.82% |
| Calça Jeans 1.0 | 66 | 17.23% |
| Carteira | 49 | 12.79% |
| Perfume | 43 | 11.23% |
| Calça Alfaiataria | 38 | 9.92% |
| Camiseta Fitness | 36 | 9.40% |
| Outros Produtos | 31 | 8.09% |
| Camisa Henley | 22 | 5.74% |
| Cueca | 16 | 4.18% |
| Camiseta Manga Longa | 16 | 4.18% |
| Overshirt | 14 | 3.66% |
| Polo 2.0 | 13 | 3.39% |
| Calça Comfort | 10 | 2.61% |
| Polo 1.0 | 7 | 1.83% |
| Camisa Social Malha | 7 | 1.83% |
| Cueca Fitness | 6 | 1.57% |
| Camiseta Modal Tech | 4 | 1.04% |
| Suéter Zíper | 4 | 1.04% |
| Polo Tricot | 3 | 0.78% |
| Suéter Classic 2026 | 3 | 0.78% |
| Camiseta Fitness Manga Longa | 2 | 0.52% |
| Camiseta Gola Alta Manga Longa | 1 | 0.26% |
| Jaqueta Westfield | 1 | 0.26% |
| Calça Jeans 2.0 | 1 | 0.26% |

**Polo 2.0** — 188 clientes com compra tipo "Recente"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Polo 2.0 | 87 | 46.28% |
| Camiseta Minimal | 67 | 35.64% |
| Calça Jeans 1.0 | 17 | 9.04% |
| Calça Comfort | 16 | 8.51% |
| Polo Tricot | 12 | 6.38% |
| Camiseta Fitness | 11 | 5.85% |
| Calça Jeans 2.0 | 11 | 5.85% |
| Outros Produtos | 11 | 5.85% |
| Overshirt | 10 | 5.32% |
| Suéter Zíper | 7 | 3.72% |
| Cueca | 7 | 3.72% |
| Camisa Henley | 6 | 3.19% |
| Jaqueta Essential | 6 | 3.19% |
| Jaqueta Westfield | 5 | 2.66% |
| Camisa Social Tech Classics | 5 | 2.66% |
| Calça Alfaiataria | 5 | 2.66% |
| Camiseta Gola Alta Manga Longa | 3 | 1.60% |
| Suéter Classic 2026 | 3 | 1.60% |
| Perfume | 2 | 1.06% |
| Calça Essential | 2 | 1.06% |
| Camiseta Modal Tech | 1 | 0.53% |
| Cueca Fitness | 1 | 0.53% |
| Camisa Social Malha | 1 | 0.53% |
| Carteira | 1 | 0.53% |
| Camiseta Gola Alta Manga Curta | 1 | 0.53% |


### 2) Clientes ativos não recentes — produtos que mais repetem
Compras feitas depois do 1º semestre, dentro da janela de 11 meses desde a compra anterior (o cliente nunca ficou inativo até essa compra).

**Camiseta Minimal (4 un)** — 11.647 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 9.322 | 80.04% |
| Calça Jeans 1.0 | 1.568 | 13.46% |
| Camiseta Fitness | 1.171 | 10.05% |
| Outros Produtos | 1.086 | 9.32% |
| Cueca | 873 | 7.50% |
| Camiseta Manga Longa | 801 | 6.88% |
| Camisa Social Tech Classics | 708 | 6.08% |
| Carteira | 674 | 5.79% |
| Perfume | 600 | 5.15% |
| Calça Alfaiataria | 570 | 4.89% |
| Camisa Henley | 502 | 4.31% |
| Polo 2.0 | 473 | 4.06% |
| Calça Comfort | 432 | 3.71% |
| Overshirt | 402 | 3.45% |
| Calça Jeans 2.0 | 250 | 2.15% |
| Suéter Zíper | 221 | 1.90% |
| Polo Tricot | 190 | 1.63% |
| Suéter Classic 2026 | 177 | 1.52% |
| Polo 1.0 | 176 | 1.51% |
| Jaqueta Essential | 143 | 1.23% |
| Cueca Fitness | 139 | 1.19% |
| Camisa Social Malha | 104 | 0.89% |
| Jaqueta Westfield | 88 | 0.76% |
| Camiseta Gola Alta Manga Curta | 86 | 0.74% |
| Camiseta Fitness Manga Longa | 80 | 0.69% |
| Calça Essential | 78 | 0.67% |
| Camiseta Modal Tech | 71 | 0.61% |
| Camiseta Gola Alta Manga Longa | 70 | 0.60% |

**Camiseta Minimal (1 un)** — 7.866 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 6.395 | 81.30% |
| Calça Jeans 1.0 | 934 | 11.87% |
| Camiseta Fitness | 690 | 8.77% |
| Outros Produtos | 599 | 7.62% |
| Cueca | 507 | 6.45% |
| Camiseta Manga Longa | 495 | 6.29% |
| Camisa Social Tech Classics | 445 | 5.66% |
| Calça Alfaiataria | 310 | 3.94% |
| Polo 2.0 | 309 | 3.93% |
| Camisa Henley | 294 | 3.74% |
| Perfume | 261 | 3.32% |
| Overshirt | 228 | 2.90% |
| Calça Comfort | 226 | 2.87% |
| Carteira | 223 | 2.83% |
| Suéter Zíper | 117 | 1.49% |
| Polo 1.0 | 112 | 1.42% |
| Calça Jeans 2.0 | 110 | 1.40% |
| Cueca Fitness | 100 | 1.27% |
| Suéter Classic 2026 | 86 | 1.09% |
| Polo Tricot | 84 | 1.07% |
| Jaqueta Essential | 63 | 0.80% |
| Camiseta Fitness Manga Longa | 62 | 0.79% |
| Camiseta Gola Alta Manga Longa | 46 | 0.58% |
| Camiseta Modal Tech | 37 | 0.47% |
| Jaqueta Westfield | 36 | 0.46% |
| Camisa Social Malha | 35 | 0.44% |
| Camiseta Gola Alta Manga Curta | 33 | 0.42% |
| Calça Essential | 31 | 0.39% |

**Camiseta Minimal (outras qtd)** — 6.072 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 4.931 | 81.21% |
| Calça Jeans 1.0 | 863 | 14.21% |
| Camiseta Fitness | 717 | 11.81% |
| Outros Produtos | 641 | 10.56% |
| Cueca | 538 | 8.86% |
| Camiseta Manga Longa | 507 | 8.35% |
| Camisa Social Tech Classics | 422 | 6.95% |
| Carteira | 343 | 5.65% |
| Calça Alfaiataria | 315 | 5.19% |
| Perfume | 287 | 4.73% |
| Camisa Henley | 268 | 4.41% |
| Polo 2.0 | 261 | 4.30% |
| Overshirt | 235 | 3.87% |
| Calça Comfort | 232 | 3.82% |
| Suéter Classic 2026 | 120 | 1.98% |
| Suéter Zíper | 117 | 1.93% |
| Polo 1.0 | 108 | 1.78% |
| Calça Jeans 2.0 | 103 | 1.70% |
| Polo Tricot | 86 | 1.42% |
| Jaqueta Essential | 77 | 1.27% |
| Cueca Fitness | 76 | 1.25% |
| Jaqueta Westfield | 55 | 0.91% |
| Camisa Social Malha | 52 | 0.86% |
| Camiseta Fitness Manga Longa | 45 | 0.74% |
| Camiseta Gola Alta Manga Longa | 43 | 0.71% |
| Camiseta Gola Alta Manga Curta | 43 | 0.71% |
| Calça Essential | 39 | 0.64% |
| Camiseta Modal Tech | 35 | 0.58% |

**Camiseta + Carteira** — 73 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 50 | 68.49% |
| Outros Produtos | 11 | 15.07% |
| Calça Jeans 1.0 | 10 | 13.70% |
| Carteira | 9 | 12.33% |
| Overshirt | 8 | 10.96% |
| Camisa Social Tech Classics | 7 | 9.59% |
| Cueca | 7 | 9.59% |
| Camiseta Fitness | 7 | 9.59% |
| Perfume | 6 | 8.22% |
| Camiseta Manga Longa | 5 | 6.85% |
| Polo 2.0 | 5 | 6.85% |
| Calça Alfaiataria | 5 | 6.85% |
| Calça Comfort | 5 | 6.85% |
| Suéter Zíper | 4 | 5.48% |
| Camisa Henley | 4 | 5.48% |
| Jaqueta Westfield | 3 | 4.11% |
| Calça Jeans 2.0 | 3 | 4.11% |
| Jaqueta Essential | 3 | 4.11% |
| Polo Tricot | 3 | 4.11% |
| Suéter Classic 2026 | 2 | 2.74% |
| Camiseta Gola Alta Manga Curta | 1 | 1.37% |
| Calça Essential | 1 | 1.37% |

**Calça Jeans 1.0** — 486 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Calça Jeans 1.0 | 203 | 41.77% |
| Camiseta Minimal | 202 | 41.56% |
| Calça Comfort | 54 | 11.11% |
| Polo 2.0 | 47 | 9.67% |
| Calça Jeans 2.0 | 44 | 9.05% |
| Outros Produtos | 40 | 8.23% |
| Overshirt | 40 | 8.23% |
| Camisa Social Tech Classics | 39 | 8.02% |
| Calça Alfaiataria | 37 | 7.61% |
| Camisa Henley | 27 | 5.56% |
| Cueca | 23 | 4.73% |
| Camiseta Fitness | 22 | 4.53% |
| Polo Tricot | 20 | 4.12% |
| Jaqueta Essential | 15 | 3.09% |
| Carteira | 14 | 2.88% |
| Camiseta Manga Longa | 13 | 2.67% |
| Suéter Zíper | 12 | 2.47% |
| Jaqueta Westfield | 11 | 2.26% |
| Perfume | 10 | 2.06% |
| Camisa Social Malha | 9 | 1.85% |
| Suéter Classic 2026 | 8 | 1.65% |
| Calça Essential | 8 | 1.65% |
| Camiseta Gola Alta Manga Longa | 5 | 1.03% |
| Camiseta Modal Tech | 4 | 0.82% |
| Camiseta Gola Alta Manga Curta | 4 | 0.82% |
| Camiseta Fitness Manga Longa | 2 | 0.41% |
| Cueca Fitness | 2 | 0.41% |
| Polo 1.0 | 2 | 0.41% |

**Camiseta Minimal (6 un)** — 674 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 549 | 81.45% |
| Calça Jeans 1.0 | 95 | 14.09% |
| Outros Produtos | 77 | 11.42% |
| Carteira | 76 | 11.28% |
| Camiseta Fitness | 65 | 9.64% |
| Perfume | 55 | 8.16% |
| Camisa Social Tech Classics | 47 | 6.97% |
| Calça Alfaiataria | 46 | 6.82% |
| Polo 2.0 | 43 | 6.38% |
| Camisa Henley | 42 | 6.23% |
| Cueca | 40 | 5.93% |
| Overshirt | 32 | 4.75% |
| Camiseta Manga Longa | 30 | 4.45% |
| Calça Comfort | 26 | 3.86% |
| Suéter Zíper | 17 | 2.52% |
| Polo Tricot | 16 | 2.37% |
| Jaqueta Essential | 12 | 1.78% |
| Calça Jeans 2.0 | 10 | 1.48% |
| Suéter Classic 2026 | 10 | 1.48% |
| Camiseta Gola Alta Manga Longa | 10 | 1.48% |
| Calça Essential | 9 | 1.34% |
| Camisa Social Malha | 5 | 0.74% |
| Polo 1.0 | 5 | 0.74% |
| Camiseta Gola Alta Manga Curta | 5 | 0.74% |
| Camiseta Fitness Manga Longa | 4 | 0.59% |
| Cueca Fitness | 4 | 0.59% |
| Camiseta Modal Tech | 4 | 0.59% |
| Jaqueta Westfield | 3 | 0.45% |

**Camiseta + Jeans** — 398 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 258 | 64.82% |
| Calça Jeans 1.0 | 141 | 35.43% |
| Calça Comfort | 45 | 11.31% |
| Outros Produtos | 44 | 11.06% |
| Polo 2.0 | 43 | 10.80% |
| Cueca | 34 | 8.54% |
| Camiseta Fitness | 34 | 8.54% |
| Calça Alfaiataria | 33 | 8.29% |
| Calça Jeans 2.0 | 31 | 7.79% |
| Carteira | 28 | 7.04% |
| Overshirt | 27 | 6.78% |
| Perfume | 25 | 6.28% |
| Camisa Henley | 21 | 5.28% |
| Camisa Social Tech Classics | 20 | 5.03% |
| Camiseta Manga Longa | 18 | 4.52% |
| Suéter Zíper | 18 | 4.52% |
| Jaqueta Essential | 13 | 3.27% |
| Polo Tricot | 12 | 3.02% |
| Calça Essential | 11 | 2.76% |
| Suéter Classic 2026 | 10 | 2.51% |
| Jaqueta Westfield | 9 | 2.26% |
| Camiseta Fitness Manga Longa | 8 | 2.01% |
| Camiseta Gola Alta Manga Longa | 8 | 2.01% |
| Camisa Social Malha | 7 | 1.76% |
| Camiseta Gola Alta Manga Curta | 5 | 1.26% |
| Cueca Fitness | 5 | 1.26% |
| Camiseta Modal Tech | 5 | 1.26% |

**Camiseta + Cueca** — 717 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 524 | 73.08% |
| Cueca | 229 | 31.94% |
| Camiseta Fitness | 124 | 17.29% |
| Outros Produtos | 122 | 17.02% |
| Calça Jeans 1.0 | 117 | 16.32% |
| Calça Alfaiataria | 65 | 9.07% |
| Camiseta Manga Longa | 64 | 8.93% |
| Perfume | 63 | 8.79% |
| Camisa Social Tech Classics | 62 | 8.65% |
| Carteira | 55 | 7.67% |
| Cueca Fitness | 42 | 5.86% |
| Camisa Henley | 39 | 5.44% |
| Calça Comfort | 37 | 5.16% |
| Overshirt | 28 | 3.91% |
| Polo 2.0 | 25 | 3.49% |
| Polo 1.0 | 21 | 2.93% |
| Suéter Classic 2026 | 17 | 2.37% |
| Suéter Zíper | 16 | 2.23% |
| Polo Tricot | 10 | 1.39% |
| Camiseta Modal Tech | 10 | 1.39% |
| Calça Jeans 2.0 | 9 | 1.26% |
| Jaqueta Essential | 8 | 1.12% |
| Jaqueta Westfield | 7 | 0.98% |
| Camisa Social Malha | 6 | 0.84% |
| Calça Essential | 5 | 0.70% |
| Camiseta Gola Alta Manga Curta | 5 | 0.70% |
| Camiseta Gola Alta Manga Longa | 5 | 0.70% |
| Camiseta Fitness Manga Longa | 3 | 0.42% |

**Camisa Social Tech Classics** — 296 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 140 | 47.30% |
| Camisa Social Tech Classics | 94 | 31.76% |
| Calça Jeans 1.0 | 55 | 18.58% |
| Calça Alfaiataria | 44 | 14.86% |
| Outros Produtos | 39 | 13.18% |
| Overshirt | 30 | 10.14% |
| Calça Comfort | 28 | 9.46% |
| Camisa Henley | 26 | 8.78% |
| Camiseta Fitness | 21 | 7.09% |
| Carteira | 20 | 6.76% |
| Polo 2.0 | 16 | 5.41% |
| Cueca | 16 | 5.41% |
| Suéter Zíper | 16 | 5.41% |
| Perfume | 15 | 5.07% |
| Camisa Social Malha | 11 | 3.72% |
| Polo Tricot | 8 | 2.70% |
| Calça Jeans 2.0 | 7 | 2.36% |
| Camiseta Manga Longa | 6 | 2.03% |
| Suéter Classic 2026 | 6 | 2.03% |
| Calça Essential | 5 | 1.69% |
| Jaqueta Westfield | 5 | 1.69% |
| Camiseta Gola Alta Manga Curta | 4 | 1.35% |
| Jaqueta Essential | 4 | 1.35% |
| Camiseta Gola Alta Manga Longa | 3 | 1.01% |
| Camiseta Modal Tech | 3 | 1.01% |
| Cueca Fitness | 3 | 1.01% |
| Camiseta Fitness Manga Longa | 2 | 0.68% |
| Polo 1.0 | 1 | 0.34% |

**Camiseta + Camiseta Fitness** — 437 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 314 | 71.85% |
| Camiseta Fitness | 152 | 34.78% |
| Calça Jeans 1.0 | 90 | 20.59% |
| Outros Produtos | 55 | 12.59% |
| Camisa Social Tech Classics | 43 | 9.84% |
| Carteira | 41 | 9.38% |
| Perfume | 40 | 9.15% |
| Calça Comfort | 37 | 8.47% |
| Calça Alfaiataria | 32 | 7.32% |
| Polo 2.0 | 30 | 6.86% |
| Camisa Henley | 30 | 6.86% |
| Cueca | 29 | 6.64% |
| Camiseta Manga Longa | 22 | 5.03% |
| Overshirt | 20 | 4.58% |
| Polo Tricot | 14 | 3.20% |
| Calça Jeans 2.0 | 10 | 2.29% |
| Jaqueta Essential | 10 | 2.29% |
| Camiseta Fitness Manga Longa | 10 | 2.29% |
| Polo 1.0 | 9 | 2.06% |
| Suéter Zíper | 8 | 1.83% |
| Calça Essential | 7 | 1.60% |
| Cueca Fitness | 7 | 1.60% |
| Camisa Social Malha | 6 | 1.37% |
| Suéter Classic 2026 | 6 | 1.37% |
| Camiseta Gola Alta Manga Curta | 5 | 1.14% |
| Jaqueta Westfield | 5 | 1.14% |
| Camiseta Modal Tech | 5 | 1.14% |
| Camiseta Gola Alta Manga Longa | 2 | 0.46% |

**Camiseta Fitness** — 341 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 212 | 62.17% |
| Camiseta Fitness | 133 | 39.00% |
| Calça Jeans 1.0 | 55 | 16.13% |
| Outros Produtos | 36 | 10.56% |
| Camisa Social Tech Classics | 24 | 7.04% |
| Cueca | 19 | 5.57% |
| Perfume | 16 | 4.69% |
| Camisa Henley | 15 | 4.40% |
| Calça Alfaiataria | 15 | 4.40% |
| Polo 2.0 | 15 | 4.40% |
| Calça Comfort | 14 | 4.11% |
| Camiseta Manga Longa | 11 | 3.23% |
| Overshirt | 11 | 3.23% |
| Cueca Fitness | 10 | 2.93% |
| Carteira | 10 | 2.93% |
| Camiseta Fitness Manga Longa | 8 | 2.35% |
| Jaqueta Essential | 7 | 2.05% |
| Camiseta Modal Tech | 6 | 1.76% |
| Suéter Zíper | 5 | 1.47% |
| Polo 1.0 | 5 | 1.47% |
| Camisa Social Malha | 5 | 1.47% |
| Calça Jeans 2.0 | 4 | 1.17% |
| Calça Essential | 3 | 0.88% |
| Polo Tricot | 3 | 0.88% |
| Camiseta Gola Alta Manga Curta | 3 | 0.88% |
| Jaqueta Westfield | 2 | 0.59% |
| Suéter Classic 2026 | 2 | 0.59% |

**Overshirt** — 73 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Overshirt | 30 | 41.10% |
| Camiseta Minimal | 24 | 32.88% |
| Calça Jeans 1.0 | 13 | 17.81% |
| Calça Comfort | 9 | 12.33% |
| Polo Tricot | 7 | 9.59% |
| Polo 2.0 | 7 | 9.59% |
| Outros Produtos | 6 | 8.22% |
| Camisa Henley | 6 | 8.22% |
| Calça Jeans 2.0 | 5 | 6.85% |
| Jaqueta Westfield | 5 | 6.85% |
| Suéter Classic 2026 | 4 | 5.48% |
| Camiseta Fitness | 3 | 4.11% |
| Calça Essential | 3 | 4.11% |
| Calça Alfaiataria | 3 | 4.11% |
| Camisa Social Malha | 3 | 4.11% |
| Suéter Zíper | 3 | 4.11% |
| Jaqueta Essential | 2 | 2.74% |
| Camiseta Manga Longa | 2 | 2.74% |
| Perfume | 2 | 2.74% |
| Camisa Social Tech Classics | 2 | 2.74% |
| Camiseta Gola Alta Manga Longa | 1 | 1.37% |
| Carteira | 1 | 1.37% |

**Outros Produtos** — 226 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 129 | 57.08% |
| Calça Jeans 1.0 | 48 | 21.24% |
| Outros Produtos | 47 | 20.80% |
| Camiseta Fitness | 27 | 11.95% |
| Camisa Social Tech Classics | 20 | 8.85% |
| Camiseta Manga Longa | 19 | 8.41% |
| Camisa Henley | 17 | 7.52% |
| Calça Alfaiataria | 16 | 7.08% |
| Overshirt | 16 | 7.08% |
| Polo 2.0 | 15 | 6.64% |
| Cueca | 13 | 5.75% |
| Perfume | 13 | 5.75% |
| Calça Comfort | 10 | 4.42% |
| Carteira | 9 | 3.98% |
| Suéter Classic 2026 | 9 | 3.98% |
| Suéter Zíper | 7 | 3.10% |
| Calça Jeans 2.0 | 5 | 2.21% |
| Cueca Fitness | 4 | 1.77% |
| Polo Tricot | 4 | 1.77% |
| Calça Essential | 4 | 1.77% |
| Camiseta Modal Tech | 3 | 1.33% |
| Camisa Social Malha | 3 | 1.33% |
| Polo 1.0 | 3 | 1.33% |
| Jaqueta Westfield | 2 | 0.88% |
| Camiseta Gola Alta Manga Longa | 2 | 0.88% |
| Jaqueta Essential | 2 | 0.88% |
| Camiseta Gola Alta Manga Curta | 2 | 0.88% |
| Camiseta Fitness Manga Longa | 1 | 0.44% |

**Cueca** — 354 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 230 | 64.97% |
| Cueca | 98 | 27.68% |
| Calça Jeans 1.0 | 55 | 15.54% |
| Outros Produtos | 49 | 13.84% |
| Camiseta Fitness | 44 | 12.43% |
| Camiseta Manga Longa | 30 | 8.47% |
| Camisa Social Tech Classics | 25 | 7.06% |
| Camisa Henley | 19 | 5.37% |
| Calça Alfaiataria | 17 | 4.80% |
| Overshirt | 16 | 4.52% |
| Calça Comfort | 14 | 3.95% |
| Carteira | 14 | 3.95% |
| Perfume | 13 | 3.67% |
| Cueca Fitness | 13 | 3.67% |
| Polo 2.0 | 10 | 2.82% |
| Polo 1.0 | 9 | 2.54% |
| Suéter Classic 2026 | 8 | 2.26% |
| Suéter Zíper | 7 | 1.98% |
| Camiseta Gola Alta Manga Longa | 4 | 1.13% |
| Camisa Social Malha | 4 | 1.13% |
| Calça Jeans 2.0 | 4 | 1.13% |
| Camiseta Fitness Manga Longa | 4 | 1.13% |
| Jaqueta Westfield | 2 | 0.56% |
| Jaqueta Essential | 2 | 0.56% |
| Polo Tricot | 2 | 0.56% |
| Camiseta Gola Alta Manga Curta | 2 | 0.56% |
| Camiseta Modal Tech | 1 | 0.28% |
| Calça Essential | 1 | 0.28% |

**Calça Comfort** — 38 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Calça Comfort | 19 | 50.00% |
| Camiseta Minimal | 9 | 23.68% |
| Calça Essential | 7 | 18.42% |
| Jaqueta Essential | 6 | 15.79% |
| Overshirt | 5 | 13.16% |
| Camiseta Fitness | 4 | 10.53% |
| Camiseta Gola Alta Manga Curta | 4 | 10.53% |
| Camisa Social Tech Classics | 3 | 7.89% |
| Calça Jeans 1.0 | 3 | 7.89% |
| Outros Produtos | 3 | 7.89% |
| Polo Tricot | 2 | 5.26% |
| Camisa Social Malha | 2 | 5.26% |
| Calça Jeans 2.0 | 2 | 5.26% |
| Camiseta Gola Alta Manga Longa | 1 | 2.63% |
| Cueca | 1 | 2.63% |
| Cueca Fitness | 1 | 2.63% |
| Camisa Henley | 1 | 2.63% |
| Calça Alfaiataria | 1 | 2.63% |
| Polo 2.0 | 1 | 2.63% |

**Camiseta Manga Longa** — 320 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 205 | 64.06% |
| Camiseta Manga Longa | 71 | 22.19% |
| Calça Jeans 1.0 | 55 | 17.19% |
| Outros Produtos | 46 | 14.37% |
| Camisa Social Tech Classics | 39 | 12.19% |
| Camiseta Fitness | 32 | 10.00% |
| Calça Alfaiataria | 21 | 6.56% |
| Overshirt | 20 | 6.25% |
| Cueca | 19 | 5.94% |
| Calça Comfort | 16 | 5.00% |
| Carteira | 16 | 5.00% |
| Camisa Henley | 16 | 5.00% |
| Perfume | 15 | 4.69% |
| Suéter Zíper | 10 | 3.12% |
| Polo Tricot | 9 | 2.81% |
| Polo 2.0 | 9 | 2.81% |
| Jaqueta Essential | 9 | 2.81% |
| Camiseta Gola Alta Manga Longa | 9 | 2.81% |
| Camiseta Fitness Manga Longa | 9 | 2.81% |
| Calça Essential | 8 | 2.50% |
| Calça Jeans 2.0 | 7 | 2.19% |
| Polo 1.0 | 7 | 2.19% |
| Suéter Classic 2026 | 5 | 1.56% |
| Camiseta Modal Tech | 5 | 1.56% |
| Camiseta Gola Alta Manga Curta | 4 | 1.25% |
| Cueca Fitness | 3 | 0.94% |
| Jaqueta Westfield | 2 | 0.62% |
| Camisa Social Malha | 1 | 0.31% |

**Camisa Henley** — 124 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 53 | 42.74% |
| Camisa Henley | 29 | 23.39% |
| Overshirt | 18 | 14.52% |
| Polo Tricot | 17 | 13.71% |
| Calça Comfort | 12 | 9.68% |
| Polo 2.0 | 10 | 8.06% |
| Calça Jeans 1.0 | 9 | 7.26% |
| Suéter Zíper | 9 | 7.26% |
| Outros Produtos | 8 | 6.45% |
| Camisa Social Tech Classics | 7 | 5.65% |
| Camiseta Fitness | 6 | 4.84% |
| Suéter Classic 2026 | 6 | 4.84% |
| Camisa Social Malha | 5 | 4.03% |
| Camiseta Manga Longa | 4 | 3.23% |
| Camiseta Gola Alta Manga Longa | 4 | 3.23% |
| Camiseta Gola Alta Manga Curta | 3 | 2.42% |
| Cueca | 3 | 2.42% |
| Jaqueta Essential | 3 | 2.42% |
| Perfume | 3 | 2.42% |
| Calça Alfaiataria | 3 | 2.42% |
| Jaqueta Westfield | 3 | 2.42% |
| Calça Jeans 2.0 | 2 | 1.61% |
| Camiseta Fitness Manga Longa | 2 | 1.61% |
| Calça Essential | 2 | 1.61% |
| Carteira | 2 | 1.61% |
| Cueca Fitness | 1 | 0.81% |
| Camiseta Modal Tech | 1 | 0.81% |

**Camiseta + Perfume** — 71 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 53 | 74.65% |
| Camiseta Fitness | 7 | 9.86% |
| Calça Jeans 1.0 | 7 | 9.86% |
| Perfume | 6 | 8.45% |
| Camiseta Manga Longa | 5 | 7.04% |
| Camisa Social Tech Classics | 5 | 7.04% |
| Polo 2.0 | 4 | 5.63% |
| Calça Alfaiataria | 4 | 5.63% |
| Outros Produtos | 3 | 4.23% |
| Overshirt | 3 | 4.23% |
| Calça Jeans 2.0 | 3 | 4.23% |
| Carteira | 3 | 4.23% |
| Camiseta Gola Alta Manga Longa | 2 | 2.82% |
| Cueca | 2 | 2.82% |
| Calça Comfort | 1 | 1.41% |
| Camiseta Gola Alta Manga Curta | 1 | 1.41% |
| Suéter Classic 2026 | 1 | 1.41% |
| Calça Essential | 1 | 1.41% |
| Jaqueta Essential | 1 | 1.41% |
| Suéter Zíper | 1 | 1.41% |
| Camisa Henley | 1 | 1.41% |
| Camisa Social Malha | 1 | 1.41% |
| Camiseta Fitness Manga Longa | 1 | 1.41% |
| Cueca Fitness | 1 | 1.41% |

**Camiseta + Social** — 196 clientes com compra tipo "Repetição"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 127 | 64.80% |
| Camisa Social Tech Classics | 47 | 23.98% |
| Outros Produtos | 37 | 18.88% |
| Calça Jeans 1.0 | 32 | 16.33% |
| Camiseta Fitness | 26 | 13.27% |
| Camisa Henley | 19 | 9.69% |
| Cueca | 17 | 8.67% |
| Calça Alfaiataria | 15 | 7.65% |
| Overshirt | 14 | 7.14% |
| Camiseta Manga Longa | 14 | 7.14% |
| Carteira | 13 | 6.63% |
| Perfume | 13 | 6.63% |
| Camisa Social Malha | 12 | 6.12% |
| Polo 2.0 | 11 | 5.61% |
| Jaqueta Essential | 9 | 4.59% |
| Suéter Zíper | 9 | 4.59% |
| Calça Comfort | 8 | 4.08% |
| Calça Essential | 8 | 4.08% |
| Camiseta Fitness Manga Longa | 6 | 3.06% |
| Camiseta Gola Alta Manga Curta | 3 | 1.53% |
| Calça Jeans 2.0 | 3 | 1.53% |
| Jaqueta Westfield | 3 | 1.53% |
| Polo Tricot | 3 | 1.53% |
| Polo 1.0 | 2 | 1.02% |
| Suéter Classic 2026 | 2 | 1.02% |
| Camiseta Gola Alta Manga Longa | 2 | 1.02% |
| Camiseta Modal Tech | 2 | 1.02% |
| Cueca Fitness | 1 | 0.51% |


### 3) Clientes inativos (que voltaram) — produtos que mais reativam
Compras feitas DEPOIS de 11+ meses sem comprar — a janela tinha fechado; esse produto foi o que trouxe o cliente de volta.

**Camiseta Minimal (4 un)** — 9.471 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 7.369 | 77.81% |
| Calça Jeans 1.0 | 969 | 10.23% |
| Camiseta Fitness | 630 | 6.65% |
| Outros Produtos | 424 | 4.48% |
| Carteira | 416 | 4.39% |
| Cueca | 410 | 4.33% |
| Camisa Social Tech Classics | 404 | 4.27% |
| Perfume | 379 | 4.00% |
| Calça Alfaiataria | 322 | 3.40% |
| Camiseta Manga Longa | 277 | 2.92% |
| Camisa Henley | 240 | 2.53% |
| Polo 2.0 | 234 | 2.47% |
| Calça Comfort | 219 | 2.31% |
| Overshirt | 207 | 2.19% |
| Calça Jeans 2.0 | 86 | 0.91% |
| Cueca Fitness | 64 | 0.68% |
| Suéter Zíper | 59 | 0.62% |
| Polo Tricot | 52 | 0.55% |
| Polo 1.0 | 51 | 0.54% |
| Suéter Classic 2026 | 43 | 0.45% |
| Camisa Social Malha | 33 | 0.35% |
| Camiseta Fitness Manga Longa | 28 | 0.30% |
| Jaqueta Westfield | 26 | 0.27% |
| Jaqueta Essential | 23 | 0.24% |
| Camiseta Gola Alta Manga Curta | 22 | 0.23% |
| Camiseta Modal Tech | 21 | 0.22% |
| Calça Essential | 19 | 0.20% |
| Camiseta Gola Alta Manga Longa | 9 | 0.10% |

**Camiseta Minimal (1 un)** — 6.108 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 4.623 | 75.69% |
| Calça Jeans 1.0 | 579 | 9.48% |
| Camiseta Fitness | 329 | 5.39% |
| Cueca | 236 | 3.86% |
| Camisa Social Tech Classics | 225 | 3.68% |
| Outros Produtos | 210 | 3.44% |
| Calça Alfaiataria | 176 | 2.88% |
| Carteira | 165 | 2.70% |
| Overshirt | 160 | 2.62% |
| Perfume | 154 | 2.52% |
| Camiseta Manga Longa | 154 | 2.52% |
| Polo 2.0 | 149 | 2.44% |
| Camisa Henley | 139 | 2.28% |
| Calça Comfort | 117 | 1.92% |
| Calça Jeans 2.0 | 57 | 0.93% |
| Cueca Fitness | 50 | 0.82% |
| Suéter Zíper | 44 | 0.72% |
| Polo Tricot | 40 | 0.65% |
| Suéter Classic 2026 | 32 | 0.52% |
| Polo 1.0 | 25 | 0.41% |
| Camiseta Fitness Manga Longa | 24 | 0.39% |
| Jaqueta Essential | 22 | 0.36% |
| Camiseta Modal Tech | 17 | 0.28% |
| Camisa Social Malha | 14 | 0.23% |
| Camiseta Gola Alta Manga Longa | 13 | 0.21% |
| Camiseta Gola Alta Manga Curta | 13 | 0.21% |
| Jaqueta Westfield | 12 | 0.20% |
| Calça Essential | 8 | 0.13% |

**Camiseta Minimal (outras qtd)** — 4.758 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 3.625 | 76.19% |
| Calça Jeans 1.0 | 542 | 11.39% |
| Camiseta Fitness | 340 | 7.15% |
| Outros Produtos | 240 | 5.04% |
| Cueca | 238 | 5.00% |
| Carteira | 218 | 4.58% |
| Perfume | 206 | 4.33% |
| Camisa Social Tech Classics | 191 | 4.01% |
| Calça Alfaiataria | 188 | 3.95% |
| Camiseta Manga Longa | 158 | 3.32% |
| Camisa Henley | 141 | 2.96% |
| Calça Comfort | 112 | 2.35% |
| Overshirt | 109 | 2.29% |
| Polo 2.0 | 98 | 2.06% |
| Cueca Fitness | 52 | 1.09% |
| Calça Jeans 2.0 | 44 | 0.92% |
| Suéter Zíper | 39 | 0.82% |
| Polo Tricot | 39 | 0.82% |
| Polo 1.0 | 28 | 0.59% |
| Suéter Classic 2026 | 22 | 0.46% |
| Camiseta Modal Tech | 15 | 0.32% |
| Jaqueta Essential | 14 | 0.29% |
| Calça Essential | 14 | 0.29% |
| Jaqueta Westfield | 13 | 0.27% |
| Camiseta Gola Alta Manga Curta | 13 | 0.27% |
| Camiseta Fitness Manga Longa | 12 | 0.25% |
| Camisa Social Malha | 10 | 0.21% |
| Camiseta Gola Alta Manga Longa | 8 | 0.17% |

**Calça Jeans 1.0** — 97 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Calça Jeans 1.0 | 34 | 35.05% |
| Camiseta Minimal | 24 | 24.74% |
| Calça Jeans 2.0 | 14 | 14.43% |
| Calça Comfort | 10 | 10.31% |
| Overshirt | 7 | 7.22% |
| Camisa Social Tech Classics | 6 | 6.19% |
| Polo 2.0 | 6 | 6.19% |
| Camiseta Fitness | 5 | 5.15% |
| Cueca | 3 | 3.09% |
| Outros Produtos | 3 | 3.09% |
| Carteira | 3 | 3.09% |
| Camisa Social Malha | 3 | 3.09% |
| Polo Tricot | 2 | 2.06% |
| Camiseta Gola Alta Manga Longa | 2 | 2.06% |
| Camiseta Gola Alta Manga Curta | 2 | 2.06% |
| Camiseta Modal Tech | 2 | 2.06% |
| Jaqueta Essential | 1 | 1.03% |
| Cueca Fitness | 1 | 1.03% |
| Calça Alfaiataria | 1 | 1.03% |
| Calça Essential | 1 | 1.03% |
| Suéter Zíper | 1 | 1.03% |

**Camiseta Minimal (6 un)** — 457 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 365 | 79.87% |
| Calça Jeans 1.0 | 47 | 10.28% |
| Carteira | 31 | 6.78% |
| Camiseta Fitness | 29 | 6.35% |
| Perfume | 27 | 5.91% |
| Outros Produtos | 22 | 4.81% |
| Camisa Social Tech Classics | 20 | 4.38% |
| Calça Comfort | 14 | 3.06% |
| Cueca | 13 | 2.84% |
| Camisa Henley | 13 | 2.84% |
| Calça Alfaiataria | 10 | 2.19% |
| Camiseta Manga Longa | 9 | 1.97% |
| Overshirt | 9 | 1.97% |
| Polo 2.0 | 8 | 1.75% |
| Calça Jeans 2.0 | 5 | 1.09% |
| Suéter Zíper | 5 | 1.09% |
| Jaqueta Essential | 5 | 1.09% |
| Suéter Classic 2026 | 4 | 0.88% |
| Polo Tricot | 4 | 0.88% |
| Camiseta Gola Alta Manga Curta | 4 | 0.88% |
| Calça Essential | 2 | 0.44% |
| Camiseta Fitness Manga Longa | 1 | 0.22% |
| Polo 1.0 | 1 | 0.22% |
| Jaqueta Westfield | 1 | 0.22% |
| Camiseta Gola Alta Manga Longa | 1 | 0.22% |
| Cueca Fitness | 1 | 0.22% |

**Camiseta + Jeans** — 91 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 47 | 51.65% |
| Calça Jeans 1.0 | 25 | 27.47% |
| Calça Jeans 2.0 | 10 | 10.99% |
| Calça Comfort | 7 | 7.69% |
| Perfume | 6 | 6.59% |
| Calça Alfaiataria | 6 | 6.59% |
| Polo 2.0 | 5 | 5.49% |
| Camiseta Fitness | 5 | 5.49% |
| Outros Produtos | 4 | 4.40% |
| Camisa Social Tech Classics | 4 | 4.40% |
| Jaqueta Essential | 4 | 4.40% |
| Cueca | 3 | 3.30% |
| Camiseta Manga Longa | 3 | 3.30% |
| Carteira | 2 | 2.20% |
| Polo Tricot | 2 | 2.20% |
| Calça Essential | 2 | 2.20% |
| Camiseta Modal Tech | 1 | 1.10% |
| Camiseta Gola Alta Manga Curta | 1 | 1.10% |
| Camisa Social Malha | 1 | 1.10% |
| Overshirt | 1 | 1.10% |
| Cueca Fitness | 1 | 1.10% |
| Suéter Zíper | 1 | 1.10% |

**Camiseta + Cueca** — 629 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 421 | 66.93% |
| Cueca | 147 | 23.37% |
| Calça Jeans 1.0 | 75 | 11.92% |
| Camiseta Fitness | 64 | 10.17% |
| Outros Produtos | 47 | 7.47% |
| Perfume | 44 | 7.00% |
| Carteira | 38 | 6.04% |
| Camiseta Manga Longa | 31 | 4.93% |
| Camisa Social Tech Classics | 29 | 4.61% |
| Calça Alfaiataria | 29 | 4.61% |
| Camisa Henley | 26 | 4.13% |
| Overshirt | 22 | 3.50% |
| Cueca Fitness | 19 | 3.02% |
| Calça Comfort | 17 | 2.70% |
| Polo 2.0 | 16 | 2.54% |
| Polo 1.0 | 8 | 1.27% |
| Suéter Zíper | 7 | 1.11% |
| Jaqueta Essential | 4 | 0.64% |
| Suéter Classic 2026 | 4 | 0.64% |
| Calça Jeans 2.0 | 3 | 0.48% |
| Polo Tricot | 3 | 0.48% |
| Calça Essential | 3 | 0.48% |
| Camiseta Gola Alta Manga Longa | 2 | 0.32% |
| Camiseta Gola Alta Manga Curta | 2 | 0.32% |
| Camiseta Modal Tech | 2 | 0.32% |
| Camisa Social Malha | 1 | 0.16% |
| Camiseta Fitness Manga Longa | 1 | 0.16% |
| Jaqueta Westfield | 1 | 0.16% |

**Camisa Social Tech Classics** — 118 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 45 | 38.14% |
| Camisa Social Tech Classics | 26 | 22.03% |
| Calça Jeans 1.0 | 17 | 14.41% |
| Calça Comfort | 12 | 10.17% |
| Overshirt | 12 | 10.17% |
| Calça Alfaiataria | 7 | 5.93% |
| Suéter Zíper | 6 | 5.08% |
| Perfume | 6 | 5.08% |
| Outros Produtos | 6 | 5.08% |
| Polo 2.0 | 6 | 5.08% |
| Camisa Henley | 5 | 4.24% |
| Carteira | 5 | 4.24% |
| Camiseta Fitness | 4 | 3.39% |
| Cueca | 4 | 3.39% |
| Calça Essential | 3 | 2.54% |
| Jaqueta Essential | 3 | 2.54% |
| Camisa Social Malha | 3 | 2.54% |
| Polo Tricot | 3 | 2.54% |
| Jaqueta Westfield | 2 | 1.69% |
| Camiseta Fitness Manga Longa | 1 | 0.85% |
| Suéter Classic 2026 | 1 | 0.85% |
| Calça Jeans 2.0 | 1 | 0.85% |
| Camiseta Gola Alta Manga Curta | 1 | 0.85% |

**Camiseta + Camiseta Fitness** — 252 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 153 | 60.71% |
| Camiseta Fitness | 63 | 25.00% |
| Calça Jeans 1.0 | 41 | 16.27% |
| Outros Produtos | 25 | 9.92% |
| Cueca | 17 | 6.75% |
| Camisa Social Tech Classics | 16 | 6.35% |
| Carteira | 13 | 5.16% |
| Calça Comfort | 13 | 5.16% |
| Polo 2.0 | 11 | 4.37% |
| Camisa Henley | 10 | 3.97% |
| Perfume | 10 | 3.97% |
| Calça Alfaiataria | 9 | 3.57% |
| Overshirt | 7 | 2.78% |
| Camiseta Fitness Manga Longa | 6 | 2.38% |
| Calça Jeans 2.0 | 6 | 2.38% |
| Suéter Zíper | 5 | 1.98% |
| Camiseta Manga Longa | 5 | 1.98% |
| Jaqueta Essential | 3 | 1.19% |
| Camiseta Modal Tech | 3 | 1.19% |
| Cueca Fitness | 3 | 1.19% |
| Suéter Classic 2026 | 2 | 0.79% |
| Polo Tricot | 2 | 0.79% |
| Calça Essential | 1 | 0.40% |
| Camisa Social Malha | 1 | 0.40% |

**Camiseta Fitness** — 231 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 107 | 46.32% |
| Camiseta Fitness | 77 | 33.33% |
| Calça Jeans 1.0 | 26 | 11.26% |
| Camisa Social Tech Classics | 12 | 5.19% |
| Polo 2.0 | 12 | 5.19% |
| Outros Produtos | 12 | 5.19% |
| Calça Alfaiataria | 10 | 4.33% |
| Calça Comfort | 8 | 3.46% |
| Perfume | 8 | 3.46% |
| Cueca | 7 | 3.03% |
| Overshirt | 6 | 2.60% |
| Calça Jeans 2.0 | 6 | 2.60% |
| Carteira | 6 | 2.60% |
| Camisa Henley | 6 | 2.60% |
| Polo Tricot | 4 | 1.73% |
| Camiseta Fitness Manga Longa | 4 | 1.73% |
| Cueca Fitness | 3 | 1.30% |
| Camiseta Manga Longa | 2 | 0.87% |
| Camiseta Modal Tech | 2 | 0.87% |
| Camiseta Gola Alta Manga Curta | 1 | 0.43% |

**Outros Produtos** — 161 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 86 | 53.42% |
| Calça Jeans 1.0 | 20 | 12.42% |
| Calça Alfaiataria | 18 | 11.18% |
| Outros Produtos | 13 | 8.07% |
| Overshirt | 11 | 6.83% |
| Camiseta Fitness | 9 | 5.59% |
| Calça Comfort | 7 | 4.35% |
| Camisa Social Tech Classics | 7 | 4.35% |
| Suéter Zíper | 5 | 3.11% |
| Carteira | 5 | 3.11% |
| Perfume | 4 | 2.48% |
| Polo 2.0 | 3 | 1.86% |
| Camisa Henley | 3 | 1.86% |
| Camiseta Modal Tech | 2 | 1.24% |
| Polo Tricot | 2 | 1.24% |
| Camiseta Manga Longa | 2 | 1.24% |
| Suéter Classic 2026 | 2 | 1.24% |
| Jaqueta Westfield | 1 | 0.62% |
| Cueca Fitness | 1 | 0.62% |
| Jaqueta Essential | 1 | 0.62% |
| Camiseta Fitness Manga Longa | 1 | 0.62% |
| Camisa Social Malha | 1 | 0.62% |
| Cueca | 1 | 0.62% |

**Cueca** — 396 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 253 | 63.89% |
| Cueca | 67 | 16.92% |
| Calça Jeans 1.0 | 38 | 9.60% |
| Camiseta Fitness | 31 | 7.83% |
| Outros Produtos | 30 | 7.58% |
| Camisa Social Tech Classics | 17 | 4.29% |
| Cueca Fitness | 16 | 4.04% |
| Camiseta Manga Longa | 15 | 3.79% |
| Perfume | 14 | 3.54% |
| Camisa Henley | 13 | 3.28% |
| Calça Alfaiataria | 11 | 2.78% |
| Overshirt | 10 | 2.53% |
| Carteira | 9 | 2.27% |
| Suéter Classic 2026 | 8 | 2.02% |
| Calça Comfort | 7 | 1.77% |
| Jaqueta Essential | 4 | 1.01% |
| Polo 2.0 | 3 | 0.76% |
| Polo 1.0 | 3 | 0.76% |
| Calça Jeans 2.0 | 3 | 0.76% |
| Suéter Zíper | 3 | 0.76% |
| Calça Essential | 2 | 0.51% |
| Camiseta Fitness Manga Longa | 1 | 0.25% |

**Camiseta Manga Longa** — 238 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 122 | 51.26% |
| Camiseta Manga Longa | 37 | 15.55% |
| Calça Jeans 1.0 | 35 | 14.71% |
| Camisa Social Tech Classics | 18 | 7.56% |
| Camiseta Fitness | 17 | 7.14% |
| Outros Produtos | 13 | 5.46% |
| Overshirt | 9 | 3.78% |
| Carteira | 8 | 3.36% |
| Calça Alfaiataria | 8 | 3.36% |
| Cueca | 7 | 2.94% |
| Calça Comfort | 7 | 2.94% |
| Calça Jeans 2.0 | 5 | 2.10% |
| Polo 2.0 | 5 | 2.10% |
| Camiseta Gola Alta Manga Longa | 4 | 1.68% |
| Camiseta Fitness Manga Longa | 4 | 1.68% |
| Suéter Classic 2026 | 4 | 1.68% |
| Camisa Henley | 4 | 1.68% |
| Perfume | 4 | 1.68% |
| Suéter Zíper | 3 | 1.26% |
| Cueca Fitness | 2 | 0.84% |
| Camiseta Gola Alta Manga Curta | 2 | 0.84% |
| Jaqueta Essential | 2 | 0.84% |
| Camisa Social Malha | 1 | 0.42% |
| Jaqueta Westfield | 1 | 0.42% |
| Calça Essential | 1 | 0.42% |
| Camiseta Modal Tech | 1 | 0.42% |
| Polo 1.0 | 1 | 0.42% |

**Camiseta + Perfume** — 35 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 25 | 71.43% |
| Outros Produtos | 5 | 14.29% |
| Perfume | 5 | 14.29% |
| Calça Jeans 1.0 | 5 | 14.29% |
| Carteira | 3 | 8.57% |
| Polo 2.0 | 3 | 8.57% |
| Calça Comfort | 2 | 5.71% |
| Camiseta Fitness | 2 | 5.71% |
| Camisa Henley | 2 | 5.71% |
| Calça Jeans 2.0 | 2 | 5.71% |
| Overshirt | 1 | 2.86% |
| Camisa Social Tech Classics | 1 | 2.86% |
| Calça Alfaiataria | 1 | 2.86% |
| Camiseta Gola Alta Manga Curta | 1 | 2.86% |

**Camiseta + Social** — 72 clientes com compra tipo "Reativação"

| Produto | Clientes | % desse grupo |
|---|---:|---:|
| Camiseta Minimal | 41 | 56.94% |
| Camisa Social Tech Classics | 13 | 18.06% |
| Calça Jeans 1.0 | 10 | 13.89% |
| Calça Comfort | 8 | 11.11% |
| Calça Alfaiataria | 8 | 11.11% |
| Camisa Social Malha | 5 | 6.94% |
| Camisa Henley | 5 | 6.94% |
| Camiseta Fitness | 4 | 5.56% |
| Carteira | 4 | 5.56% |
| Overshirt | 4 | 5.56% |
| Perfume | 4 | 5.56% |
| Cueca | 4 | 5.56% |
| Outros Produtos | 3 | 4.17% |
| Polo 2.0 | 3 | 4.17% |
| Jaqueta Essential | 1 | 1.39% |
| Camiseta Fitness Manga Longa | 1 | 1.39% |
| Calça Jeans 2.0 | 1 | 1.39% |


---

## Resumo — as 20 entradas (233.157 clientes elegíveis)

| Entrada | Clientes | Não voltaram (2ª) | Retenção (2ª) | Mediana dias (2ª) |
|---|---:|---:|---:|---:|
| Camiseta Minimal (4 un) | 84.413 | 68.9% | 24.0% | 139 |
| Camiseta Minimal (1 un) | 60.803 | 68.4% | 26.9% | 92 |
| Camiseta Minimal (outras qtd) | 38.274 | 65.8% | 27.3% | 126 |
| Camiseta + Carteira | 5.933 | 91.8% | 0.9% | 34 |
| Calça Jeans 1.0 | 5.804 | 75.0% | 11.8% | 49 |
| Camiseta Minimal (6 un) | 5.130 | 70.3% | 23.0% | 137 |
| Camiseta + Jeans | 3.833 | 72.2% | 4.8% | 64 |
| Camiseta + Cueca | 3.475 | 57.4% | 7.1% | 141 |
| Camisa Social Tech Classics | 3.284 | 74.1% | 11.9% | 50 |
| Camiseta + Camiseta Fitness | 3.270 | 66.9% | 5.6% | 84 |
| Camiseta Fitness | 3.233 | 71.4% | 9.7% | 66 |
| Overshirt | 2.711 | 87.6% | 5.4% | 16 |
| Outros Produtos | 2.141 | 75.9% | 4.5% | 127 |
| Cueca | 1.990 | 63.5% | 9.8% | 191 |
| Calça Comfort | 1.793 | 74.8% | 13.1% | 28 |
| Camiseta Manga Longa | 1.790 | 65.3% | 8.4% | 144 |
| Camisa Henley | 1.488 | 76.6% | 8.5% | 60 |
| Camiseta + Perfume | 1.435 | 81.6% | 1.6% | 50 |
| Camiseta + Social | 1.314 | 60.8% | 5.8% | 71 |
| Polo 2.0 | 1.043 | 81.4% | 8.1% | 32 |

---

## Dado a dado — cada entrada, cada compra, todos os produtos

Tabelas completas (sem corte de top-N), direto de `afinidade_produtos.csv`. `% da entrada` soma mais de 100% quando um pedido tem 2+ produtos (conta pros 2); a linha **Não fez essa compra** fecha a conta do funil.

### Camiseta Minimal (4 un) — 84.413 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal.*

**2ª compra** — 26.275 chegaram (68.9% não voltaram). retenção 24.0% · mediana acumulada **139 dias**. intervalo desde a anterior **139 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 20.251 | 23.99% |
| Calça Jeans 1.0 | 1.810 | 2.14% |
| Camiseta Fitness | 1.209 | 1.43% |
| Cueca | 1.138 | 1.35% |
| Outros Produtos | 974 | 1.15% |
| Camiseta Manga Longa | 971 | 1.15% |
| Carteira | 764 | 0.91% |
| Camisa Social Tech Classics | 722 | 0.86% |
| Perfume | 624 | 0.74% |
| Calça Alfaiataria | 482 | 0.57% |
| Polo 2.0 | 447 | 0.53% |
| Camisa Henley | 446 | 0.53% |
| Calça Comfort | 394 | 0.47% |
| Overshirt | 257 | 0.30% |
| Calça Jeans 2.0 | 195 | 0.23% |
| Cueca Fitness | 121 | 0.14% |
| Suéter Zíper | 110 | 0.13% |
| Suéter Classic 2026 | 102 | 0.12% |
| Polo 1.0 | 95 | 0.11% |
| Polo Tricot | 93 | 0.11% |
| Camisa Social Malha | 60 | 0.07% |
| Camiseta Fitness Manga Longa | 51 | 0.06% |
| Jaqueta Essential | 45 | 0.05% |
| Camiseta Gola Alta Manga Curta | 35 | 0.04% |
| Camiseta Gola Alta Manga Longa | 34 | 0.04% |
| Jaqueta Westfield | 34 | 0.04% |
| Calça Essential | 32 | 0.04% |
| Camiseta Modal Tech | 31 | 0.04% |

**3ª compra** — 11.438 chegaram (86.4% não voltaram). retenção 9.3% · mediana acumulada **330 dias**. intervalo desde a anterior **141 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 7.835 | 9.28% |
| Calça Jeans 1.0 | 1.002 | 1.19% |
| Camiseta Fitness | 755 | 0.89% |
| Outros Produtos | 589 | 0.70% |
| Cueca | 562 | 0.67% |
| Camiseta Manga Longa | 472 | 0.56% |
| Camisa Social Tech Classics | 409 | 0.48% |
| Carteira | 371 | 0.44% |
| Perfume | 352 | 0.42% |
| Calça Alfaiataria | 321 | 0.38% |
| Camisa Henley | 270 | 0.32% |
| Polo 2.0 | 258 | 0.31% |
| Calça Comfort | 247 | 0.29% |
| Overshirt | 191 | 0.23% |
| Calça Jeans 2.0 | 114 | 0.14% |
| Polo 1.0 | 77 | 0.09% |
| Cueca Fitness | 76 | 0.09% |
| Suéter Zíper | 75 | 0.09% |
| Suéter Classic 2026 | 68 | 0.08% |
| Polo Tricot | 62 | 0.07% |
| Camisa Social Malha | 53 | 0.06% |
| Jaqueta Essential | 45 | 0.05% |
| Jaqueta Westfield | 31 | 0.04% |
| Camiseta Modal Tech | 29 | 0.03% |
| Camiseta Fitness Manga Longa | 28 | 0.03% |
| Camiseta Gola Alta Manga Curta | 26 | 0.03% |
| Calça Essential | 20 | 0.02% |
| Camiseta Gola Alta Manga Longa | 19 | 0.02% |

**4ª compra** — 5.796 chegaram (93.1% não voltaram). retenção 4.3% · mediana acumulada **454 dias**. intervalo desde a anterior **118 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 3.648 | 4.32% |
| Calça Jeans 1.0 | 592 | 0.70% |
| Camiseta Fitness | 440 | 0.52% |
| Outros Produtos | 402 | 0.48% |
| Cueca | 310 | 0.37% |
| Camisa Social Tech Classics | 281 | 0.33% |
| Camiseta Manga Longa | 235 | 0.28% |
| Perfume | 225 | 0.27% |
| Carteira | 201 | 0.24% |
| Calça Alfaiataria | 194 | 0.23% |
| Camisa Henley | 187 | 0.22% |
| Polo 2.0 | 152 | 0.18% |
| Calça Comfort | 149 | 0.18% |
| Overshirt | 119 | 0.14% |
| Calça Jeans 2.0 | 73 | 0.09% |
| Suéter Zíper | 64 | 0.08% |
| Polo Tricot | 59 | 0.07% |
| Suéter Classic 2026 | 47 | 0.06% |
| Cueca Fitness | 45 | 0.05% |
| Polo 1.0 | 40 | 0.05% |
| Jaqueta Essential | 33 | 0.04% |
| Camisa Social Malha | 31 | 0.04% |
| Camiseta Fitness Manga Longa | 28 | 0.03% |
| Jaqueta Westfield | 21 | 0.02% |
| Calça Essential | 21 | 0.02% |
| Camiseta Gola Alta Manga Longa | 19 | 0.02% |
| Camiseta Modal Tech | 17 | 0.02% |
| Camiseta Gola Alta Manga Curta | 12 | 0.01% |

**5ª compra** — 3.180 chegaram (96.2% não voltaram). retenção 2.3% · mediana acumulada **554 dias**. intervalo desde a anterior **109 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 1.918 | 2.27% |
| Calça Jeans 1.0 | 334 | 0.40% |
| Camiseta Fitness | 259 | 0.31% |
| Outros Produtos | 241 | 0.29% |
| Cueca | 170 | 0.20% |
| Camiseta Manga Longa | 142 | 0.17% |
| Camisa Social Tech Classics | 135 | 0.16% |
| Calça Alfaiataria | 130 | 0.15% |
| Perfume | 120 | 0.14% |
| Carteira | 119 | 0.14% |
| Camisa Henley | 99 | 0.12% |
| Polo 2.0 | 99 | 0.12% |
| Overshirt | 77 | 0.09% |
| Calça Comfort | 76 | 0.09% |
| Calça Jeans 2.0 | 44 | 0.05% |
| Polo Tricot | 37 | 0.04% |
| Suéter Zíper | 35 | 0.04% |
| Polo 1.0 | 30 | 0.04% |
| Cueca Fitness | 29 | 0.03% |
| Suéter Classic 2026 | 28 | 0.03% |
| Camisa Social Malha | 22 | 0.03% |
| Jaqueta Essential | 21 | 0.02% |
| Camiseta Fitness Manga Longa | 18 | 0.02% |
| Camiseta Gola Alta Manga Longa | 13 | 0.02% |
| Camiseta Gola Alta Manga Curta | 12 | 0.01% |
| Calça Essential | 11 | 0.01% |
| Jaqueta Westfield | 10 | 0.01% |
| Camiseta Modal Tech | 9 | 0.01% |


### Camiseta Minimal (1 un) — 60.803 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal.*

**2ª compra** — 19.229 chegaram (68.4% não voltaram). retenção 26.9% · mediana acumulada **92 dias**. intervalo desde a anterior **92 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 16.340 | 26.87% |
| Calça Jeans 1.0 | 736 | 1.21% |
| Camiseta Fitness | 645 | 1.06% |
| Cueca | 545 | 0.90% |
| Camiseta Manga Longa | 474 | 0.78% |
| Outros Produtos | 413 | 0.68% |
| Camisa Social Tech Classics | 352 | 0.58% |
| Perfume | 265 | 0.44% |
| Carteira | 236 | 0.39% |
| Camisa Henley | 221 | 0.36% |
| Calça Alfaiataria | 170 | 0.28% |
| Polo 2.0 | 154 | 0.25% |
| Overshirt | 146 | 0.24% |
| Calça Comfort | 116 | 0.19% |
| Cueca Fitness | 71 | 0.12% |
| Polo 1.0 | 60 | 0.10% |
| Suéter Classic 2026 | 51 | 0.08% |
| Calça Jeans 2.0 | 46 | 0.08% |
| Suéter Zíper | 45 | 0.07% |
| Polo Tricot | 32 | 0.05% |
| Jaqueta Essential | 25 | 0.04% |
| Camiseta Fitness Manga Longa | 24 | 0.04% |
| Camiseta Modal Tech | 20 | 0.03% |
| Camiseta Gola Alta Manga Curta | 17 | 0.03% |
| Camiseta Gola Alta Manga Longa | 14 | 0.02% |
| Calça Essential | 12 | 0.02% |
| Jaqueta Westfield | 10 | 0.02% |
| Camisa Social Malha | 8 | 0.01% |

**3ª compra** — 8.655 chegaram (85.8% não voltaram). retenção 10.6% · mediana acumulada **268 dias**. intervalo desde a anterior **124 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 6.430 | 10.58% |
| Calça Jeans 1.0 | 627 | 1.03% |
| Camiseta Fitness | 458 | 0.75% |
| Cueca | 365 | 0.60% |
| Outros Produtos | 329 | 0.54% |
| Camiseta Manga Longa | 318 | 0.52% |
| Camisa Social Tech Classics | 224 | 0.37% |
| Perfume | 174 | 0.29% |
| Calça Alfaiataria | 173 | 0.28% |
| Polo 2.0 | 165 | 0.27% |
| Camisa Henley | 148 | 0.24% |
| Carteira | 131 | 0.22% |
| Calça Comfort | 119 | 0.20% |
| Overshirt | 85 | 0.14% |
| Calça Jeans 2.0 | 56 | 0.09% |
| Cueca Fitness | 51 | 0.08% |
| Polo 1.0 | 45 | 0.07% |
| Suéter Zíper | 42 | 0.07% |
| Suéter Classic 2026 | 36 | 0.06% |
| Polo Tricot | 33 | 0.05% |
| Camiseta Fitness Manga Longa | 21 | 0.03% |
| Jaqueta Essential | 17 | 0.03% |
| Camiseta Modal Tech | 15 | 0.02% |
| Camisa Social Malha | 13 | 0.02% |
| Camiseta Gola Alta Manga Longa | 11 | 0.02% |
| Calça Essential | 10 | 0.02% |
| Jaqueta Westfield | 8 | 0.01% |
| Camiseta Gola Alta Manga Curta | 8 | 0.01% |

**4ª compra** — 4.350 chegaram (92.8% não voltaram). retenção 4.6% · mediana acumulada **385 dias**. intervalo desde a anterior **113 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 2.820 | 4.64% |
| Calça Jeans 1.0 | 423 | 0.70% |
| Camiseta Fitness | 273 | 0.45% |
| Outros Produtos | 208 | 0.34% |
| Camiseta Manga Longa | 192 | 0.32% |
| Cueca | 189 | 0.31% |
| Camisa Social Tech Classics | 161 | 0.26% |
| Calça Alfaiataria | 134 | 0.22% |
| Polo 2.0 | 119 | 0.20% |
| Camisa Henley | 111 | 0.18% |
| Perfume | 111 | 0.18% |
| Carteira | 83 | 0.14% |
| Overshirt | 81 | 0.13% |
| Calça Comfort | 67 | 0.11% |
| Cueca Fitness | 46 | 0.08% |
| Polo 1.0 | 39 | 0.06% |
| Calça Jeans 2.0 | 39 | 0.06% |
| Polo Tricot | 31 | 0.05% |
| Suéter Zíper | 26 | 0.04% |
| Camiseta Fitness Manga Longa | 17 | 0.03% |
| Camiseta Gola Alta Manga Longa | 14 | 0.02% |
| Suéter Classic 2026 | 14 | 0.02% |
| Jaqueta Essential | 12 | 0.02% |
| Camisa Social Malha | 11 | 0.02% |
| Jaqueta Westfield | 10 | 0.02% |
| Camiseta Gola Alta Manga Curta | 7 | 0.01% |
| Camiseta Modal Tech | 6 | 0.01% |
| Calça Essential | 4 | 0.01% |

**5ª compra** — 2.384 chegaram (96.1% não voltaram). retenção 2.5% · mediana acumulada **475 dias**. intervalo desde a anterior **101 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 1.499 | 2.47% |
| Calça Jeans 1.0 | 229 | 0.38% |
| Camiseta Fitness | 175 | 0.29% |
| Outros Produtos | 158 | 0.26% |
| Cueca | 124 | 0.20% |
| Camisa Social Tech Classics | 109 | 0.18% |
| Camiseta Manga Longa | 82 | 0.13% |
| Calça Alfaiataria | 70 | 0.12% |
| Perfume | 64 | 0.11% |
| Camisa Henley | 63 | 0.10% |
| Carteira | 61 | 0.10% |
| Polo 2.0 | 55 | 0.09% |
| Calça Comfort | 54 | 0.09% |
| Overshirt | 53 | 0.09% |
| Calça Jeans 2.0 | 31 | 0.05% |
| Suéter Zíper | 25 | 0.04% |
| Cueca Fitness | 25 | 0.04% |
| Polo 1.0 | 17 | 0.03% |
| Polo Tricot | 16 | 0.03% |
| Camiseta Fitness Manga Longa | 14 | 0.02% |
| Jaqueta Essential | 13 | 0.02% |
| Suéter Classic 2026 | 11 | 0.02% |
| Camiseta Gola Alta Manga Longa | 11 | 0.02% |
| Camiseta Modal Tech | 9 | 0.01% |
| Jaqueta Westfield | 8 | 0.01% |
| Camisa Social Malha | 7 | 0.01% |
| Calça Essential | 4 | 0.01% |
| Camiseta Gola Alta Manga Curta | 4 | 0.01% |


### Camiseta Minimal (outras qtd) — 38.274 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal.*

**2ª compra** — 13.102 chegaram (65.8% não voltaram). retenção 27.3% · mediana acumulada **126 dias**. intervalo desde a anterior **126 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 10.438 | 27.27% |
| Calça Jeans 1.0 | 797 | 2.08% |
| Camiseta Fitness | 594 | 1.55% |
| Cueca | 572 | 1.49% |
| Camiseta Manga Longa | 547 | 1.43% |
| Outros Produtos | 482 | 1.26% |
| Camisa Social Tech Classics | 356 | 0.93% |
| Carteira | 344 | 0.90% |
| Perfume | 283 | 0.74% |
| Calça Alfaiataria | 233 | 0.61% |
| Camisa Henley | 214 | 0.56% |
| Polo 2.0 | 153 | 0.40% |
| Calça Comfort | 141 | 0.37% |
| Overshirt | 119 | 0.31% |
| Cueca Fitness | 68 | 0.18% |
| Calça Jeans 2.0 | 58 | 0.15% |
| Polo 1.0 | 55 | 0.14% |
| Suéter Classic 2026 | 47 | 0.12% |
| Suéter Zíper | 47 | 0.12% |
| Polo Tricot | 39 | 0.10% |
| Camiseta Modal Tech | 22 | 0.06% |
| Jaqueta Essential | 17 | 0.04% |
| Camisa Social Malha | 15 | 0.04% |
| Calça Essential | 13 | 0.03% |
| Camiseta Gola Alta Manga Curta | 13 | 0.03% |
| Camiseta Gola Alta Manga Longa | 12 | 0.03% |
| Jaqueta Westfield | 11 | 0.03% |
| Camiseta Fitness Manga Longa | 10 | 0.03% |

**3ª compra** — 6.329 chegaram (83.5% não voltaram). retenção 11.6% · mediana acumulada **307 dias**. intervalo desde a anterior **133 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 4.447 | 11.62% |
| Calça Jeans 1.0 | 541 | 1.41% |
| Camiseta Fitness | 422 | 1.10% |
| Cueca | 372 | 0.97% |
| Outros Produtos | 346 | 0.90% |
| Camiseta Manga Longa | 290 | 0.76% |
| Camisa Social Tech Classics | 230 | 0.60% |
| Perfume | 177 | 0.46% |
| Calça Alfaiataria | 163 | 0.43% |
| Carteira | 159 | 0.42% |
| Polo 2.0 | 127 | 0.33% |
| Camisa Henley | 119 | 0.31% |
| Calça Comfort | 112 | 0.29% |
| Overshirt | 95 | 0.25% |
| Suéter Zíper | 53 | 0.14% |
| Calça Jeans 2.0 | 44 | 0.11% |
| Polo 1.0 | 38 | 0.10% |
| Cueca Fitness | 38 | 0.10% |
| Suéter Classic 2026 | 37 | 0.10% |
| Polo Tricot | 35 | 0.09% |
| Jaqueta Essential | 21 | 0.05% |
| Jaqueta Westfield | 17 | 0.04% |
| Camiseta Gola Alta Manga Longa | 12 | 0.03% |
| Camiseta Gola Alta Manga Curta | 12 | 0.03% |
| Camisa Social Malha | 11 | 0.03% |
| Camiseta Fitness Manga Longa | 10 | 0.03% |
| Calça Essential | 9 | 0.02% |
| Camiseta Modal Tech | 6 | 0.02% |

**4ª compra** — 3.377 chegaram (91.2% não voltaram). retenção 5.8% · mediana acumulada **439 dias**. intervalo desde a anterior **118 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 2.219 | 5.80% |
| Calça Jeans 1.0 | 322 | 0.84% |
| Camiseta Fitness | 284 | 0.74% |
| Outros Produtos | 225 | 0.59% |
| Cueca | 198 | 0.52% |
| Camiseta Manga Longa | 179 | 0.47% |
| Camisa Social Tech Classics | 130 | 0.34% |
| Carteira | 114 | 0.30% |
| Calça Alfaiataria | 113 | 0.30% |
| Perfume | 104 | 0.27% |
| Camisa Henley | 89 | 0.23% |
| Polo 2.0 | 72 | 0.19% |
| Calça Comfort | 72 | 0.19% |
| Overshirt | 53 | 0.14% |
| Polo 1.0 | 40 | 0.10% |
| Cueca Fitness | 33 | 0.09% |
| Suéter Classic 2026 | 32 | 0.08% |
| Suéter Zíper | 32 | 0.08% |
| Calça Jeans 2.0 | 21 | 0.05% |
| Polo Tricot | 20 | 0.05% |
| Camiseta Fitness Manga Longa | 15 | 0.04% |
| Jaqueta Westfield | 14 | 0.04% |
| Camisa Social Malha | 14 | 0.04% |
| Jaqueta Essential | 11 | 0.03% |
| Camiseta Gola Alta Manga Curta | 7 | 0.02% |
| Camiseta Gola Alta Manga Longa | 6 | 0.02% |
| Calça Essential | 6 | 0.02% |
| Camiseta Modal Tech | 5 | 0.01% |

**5ª compra** — 1.982 chegaram (94.8% não voltaram). retenção 3.2% · mediana acumulada **538 dias**. intervalo desde a anterior **99 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 1.209 | 3.16% |
| Calça Jeans 1.0 | 182 | 0.48% |
| Camiseta Fitness | 178 | 0.47% |
| Outros Produtos | 136 | 0.36% |
| Cueca | 115 | 0.30% |
| Camisa Social Tech Classics | 86 | 0.22% |
| Camiseta Manga Longa | 82 | 0.21% |
| Polo 2.0 | 71 | 0.19% |
| Perfume | 69 | 0.18% |
| Carteira | 65 | 0.17% |
| Calça Alfaiataria | 64 | 0.17% |
| Camisa Henley | 56 | 0.15% |
| Calça Comfort | 54 | 0.14% |
| Overshirt | 45 | 0.12% |
| Polo 1.0 | 26 | 0.07% |
| Calça Jeans 2.0 | 22 | 0.06% |
| Cueca Fitness | 20 | 0.05% |
| Suéter Classic 2026 | 18 | 0.05% |
| Suéter Zíper | 17 | 0.04% |
| Polo Tricot | 15 | 0.04% |
| Jaqueta Essential | 13 | 0.03% |
| Camiseta Modal Tech | 11 | 0.03% |
| Camiseta Fitness Manga Longa | 10 | 0.03% |
| Camisa Social Malha | 9 | 0.02% |
| Camiseta Gola Alta Manga Longa | 6 | 0.02% |
| Calça Essential | 6 | 0.02% |
| Jaqueta Westfield | 6 | 0.02% |
| Camiseta Gola Alta Manga Curta | 3 | 0.01% |


### Camiseta + Carteira — 5.933 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal, Carteira.*

**2ª compra** — 488 chegaram (91.8% não voltaram). retenção 0.9% · mediana acumulada **34 dias**. intervalo desde a anterior **34 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 333 | 5.61% |
| Carteira **(entrada)** | 56 | 0.94% |
| Calça Jeans 1.0 | 51 | 0.86% |
| Perfume | 28 | 0.47% |
| Cueca | 25 | 0.42% |
| Camisa Social Tech Classics | 22 | 0.37% |
| Calça Jeans 2.0 | 22 | 0.37% |
| Calça Comfort | 19 | 0.32% |
| Overshirt | 19 | 0.32% |
| Outros Produtos | 19 | 0.32% |
| Calça Alfaiataria | 18 | 0.30% |
| Polo 2.0 | 17 | 0.29% |
| Camiseta Fitness | 16 | 0.27% |
| Camiseta Manga Longa | 15 | 0.25% |
| Camisa Henley | 14 | 0.24% |
| Suéter Zíper | 8 | 0.13% |
| Suéter Classic 2026 | 7 | 0.12% |
| Camiseta Gola Alta Manga Curta | 5 | 0.08% |
| Jaqueta Essential | 3 | 0.05% |
| Camiseta Gola Alta Manga Longa | 3 | 0.05% |
| Camisa Social Malha | 3 | 0.05% |
| Polo Tricot | 3 | 0.05% |
| Jaqueta Westfield | 2 | 0.03% |
| Camiseta Modal Tech | 2 | 0.03% |
| Cueca Fitness | 2 | 0.03% |
| Calça Essential | 1 | 0.02% |
| Camiseta Fitness Manga Longa | 1 | 0.02% |
| Polo 1.0 | 1 | 0.02% |

**3ª compra** — 100 chegaram (98.3% não voltaram). retenção 0.0% · mediana acumulada **110 dias**. intervalo desde a anterior **47 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 48 | 0.81% |
| Outros Produtos | 11 | 0.19% |
| Calça Jeans 1.0 | 10 | 0.17% |
| Cueca | 8 | 0.13% |
| Perfume | 8 | 0.13% |
| Camisa Social Tech Classics | 6 | 0.10% |
| Polo 2.0 | 6 | 0.10% |
| Calça Alfaiataria | 5 | 0.08% |
| Camiseta Fitness | 5 | 0.08% |
| Camisa Henley | 4 | 0.07% |
| Jaqueta Essential | 4 | 0.07% |
| Calça Comfort | 4 | 0.07% |
| Overshirt | 4 | 0.07% |
| Camiseta Modal Tech | 3 | 0.05% |
| Suéter Classic 2026 | 3 | 0.05% |
| Camisa Social Malha | 2 | 0.03% |
| Polo Tricot | 2 | 0.03% |
| Camiseta Gola Alta Manga Longa | 2 | 0.03% |
| Calça Jeans 2.0 | 2 | 0.03% |
| Carteira **(entrada)** | 2 | 0.03% |
| Jaqueta Westfield | 2 | 0.03% |
| Camiseta Manga Longa | 2 | 0.03% |
| Suéter Zíper | 1 | 0.02% |
| Cueca Fitness | 1 | 0.02% |


### Calça Jeans 1.0 — 5.804 clientes
*Precisa ter presente pra contar como retenção: Calça Jeans 1.0.*

**2ª compra** — 1.452 chegaram (75.0% não voltaram). retenção 11.8% · mediana acumulada **49 dias**. intervalo desde a anterior **49 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Calça Jeans 1.0 **(entrada)** | 686 | 11.82% |
| Camiseta Minimal | 450 | 7.75% |
| Calça Jeans 2.0 | 126 | 2.17% |
| Calça Comfort | 72 | 1.24% |
| Calça Alfaiataria | 66 | 1.14% |
| Outros Produtos | 56 | 0.96% |
| Camisa Social Tech Classics | 49 | 0.84% |
| Polo 2.0 | 46 | 0.79% |
| Carteira | 40 | 0.69% |
| Overshirt | 37 | 0.64% |
| Camiseta Fitness | 36 | 0.62% |
| Cueca | 34 | 0.59% |
| Perfume | 33 | 0.57% |
| Camisa Henley | 29 | 0.50% |
| Camiseta Manga Longa | 19 | 0.33% |
| Polo Tricot | 17 | 0.29% |
| Suéter Zíper | 17 | 0.29% |
| Jaqueta Essential | 12 | 0.21% |
| Camiseta Modal Tech | 11 | 0.19% |
| Camisa Social Malha | 8 | 0.14% |
| Calça Essential | 6 | 0.10% |
| Cueca Fitness | 5 | 0.09% |
| Camiseta Gola Alta Manga Curta | 4 | 0.07% |
| Jaqueta Westfield | 4 | 0.07% |
| Camiseta Gola Alta Manga Longa | 4 | 0.07% |
| Camiseta Fitness Manga Longa | 4 | 0.07% |
| Polo 1.0 | 2 | 0.03% |
| Suéter Classic 2026 | 2 | 0.03% |

**3ª compra** — 529 chegaram (90.9% não voltaram). retenção 3.0% · mediana acumulada **138 dias**. intervalo desde a anterior **57 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 185 | 3.19% |
| Calça Jeans 1.0 **(entrada)** | 177 | 3.05% |
| Calça Comfort | 43 | 0.74% |
| Outros Produtos | 37 | 0.64% |
| Calça Jeans 2.0 | 36 | 0.62% |
| Camisa Social Tech Classics | 34 | 0.59% |
| Calça Alfaiataria | 29 | 0.50% |
| Polo 2.0 | 27 | 0.47% |
| Camiseta Fitness | 24 | 0.41% |
| Overshirt | 22 | 0.38% |
| Camisa Henley | 21 | 0.36% |
| Cueca | 20 | 0.34% |
| Carteira | 12 | 0.21% |
| Perfume | 10 | 0.17% |
| Polo Tricot | 9 | 0.16% |
| Camiseta Manga Longa | 9 | 0.16% |
| Camisa Social Malha | 7 | 0.12% |
| Jaqueta Essential | 6 | 0.10% |
| Jaqueta Westfield | 5 | 0.09% |
| Suéter Zíper | 5 | 0.09% |
| Suéter Classic 2026 | 4 | 0.07% |
| Cueca Fitness | 4 | 0.07% |
| Camiseta Gola Alta Manga Longa | 3 | 0.05% |
| Camiseta Fitness Manga Longa | 2 | 0.03% |
| Polo 1.0 | 2 | 0.03% |
| Calça Essential | 2 | 0.03% |
| Camiseta Modal Tech | 1 | 0.02% |

**4ª compra** — 241 chegaram (95.8% não voltaram). retenção 0.9% · mediana acumulada **191 dias**. intervalo desde a anterior **34 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 78 | 1.34% |
| Calça Jeans 1.0 **(entrada)** | 54 | 0.93% |
| Calça Comfort | 23 | 0.40% |
| Outros Produtos | 22 | 0.38% |
| Polo 2.0 | 19 | 0.33% |
| Overshirt | 18 | 0.31% |
| Camisa Social Tech Classics | 13 | 0.22% |
| Calça Alfaiataria | 13 | 0.22% |
| Calça Jeans 2.0 | 11 | 0.19% |
| Polo Tricot | 10 | 0.17% |
| Camisa Henley | 9 | 0.16% |
| Cueca | 9 | 0.16% |
| Camiseta Fitness | 8 | 0.14% |
| Jaqueta Essential | 6 | 0.10% |
| Jaqueta Westfield | 6 | 0.10% |
| Carteira | 6 | 0.10% |
| Perfume | 6 | 0.10% |
| Camiseta Gola Alta Manga Curta | 4 | 0.07% |
| Suéter Classic 2026 | 3 | 0.05% |
| Camisa Social Malha | 3 | 0.05% |
| Calça Essential | 3 | 0.05% |
| Suéter Zíper | 3 | 0.05% |
| Camiseta Fitness Manga Longa | 1 | 0.02% |
| Camiseta Manga Longa | 1 | 0.02% |
| Polo 1.0 | 1 | 0.02% |
| Camiseta Gola Alta Manga Longa | 1 | 0.02% |

**5ª compra** — 124 chegaram (97.9% não voltaram). retenção 0.6% · mediana acumulada **212 dias**. intervalo desde a anterior **28 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 39 | 0.67% |
| Calça Jeans 1.0 **(entrada)** | 32 | 0.55% |
| Calça Comfort | 15 | 0.26% |
| Calça Alfaiataria | 11 | 0.19% |
| Outros Produtos | 9 | 0.16% |
| Camisa Social Tech Classics | 8 | 0.14% |
| Overshirt | 7 | 0.12% |
| Polo Tricot | 6 | 0.10% |
| Polo 2.0 | 6 | 0.10% |
| Camiseta Fitness | 4 | 0.07% |
| Camisa Henley | 4 | 0.07% |
| Camiseta Modal Tech | 3 | 0.05% |
| Camiseta Manga Longa | 3 | 0.05% |
| Suéter Classic 2026 | 2 | 0.03% |
| Suéter Zíper | 2 | 0.03% |
| Jaqueta Essential | 2 | 0.03% |
| Calça Jeans 2.0 | 2 | 0.03% |
| Camisa Social Malha | 2 | 0.03% |
| Cueca | 2 | 0.03% |
| Perfume | 1 | 0.02% |
| Camiseta Fitness Manga Longa | 1 | 0.02% |
| Calça Essential | 1 | 0.02% |
| Jaqueta Westfield | 1 | 0.02% |
| Camiseta Gola Alta Manga Curta | 1 | 0.02% |


### Camiseta Minimal (6 un) — 5.130 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal.*

**2ª compra** — 1.525 chegaram (70.3% não voltaram). retenção 23.0% · mediana acumulada **137 dias**. intervalo desde a anterior **137 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 1.182 | 23.04% |
| Calça Jeans 1.0 | 101 | 1.97% |
| Camiseta Fitness | 90 | 1.75% |
| Outros Produtos | 87 | 1.70% |
| Carteira | 75 | 1.46% |
| Perfume | 70 | 1.36% |
| Camisa Social Tech Classics | 56 | 1.09% |
| Camiseta Manga Longa | 46 | 0.90% |
| Cueca | 42 | 0.82% |
| Calça Alfaiataria | 35 | 0.68% |
| Polo 2.0 | 34 | 0.66% |
| Calça Comfort | 30 | 0.58% |
| Camisa Henley | 29 | 0.57% |
| Suéter Classic 2026 | 17 | 0.33% |
| Overshirt | 12 | 0.23% |
| Suéter Zíper | 10 | 0.19% |
| Calça Jeans 2.0 | 9 | 0.18% |
| Jaqueta Essential | 8 | 0.16% |
| Polo 1.0 | 6 | 0.12% |
| Polo Tricot | 6 | 0.12% |
| Cueca Fitness | 5 | 0.10% |
| Camiseta Gola Alta Manga Curta | 5 | 0.10% |
| Calça Essential | 4 | 0.08% |
| Camiseta Modal Tech | 2 | 0.04% |
| Jaqueta Westfield | 2 | 0.04% |
| Camiseta Fitness Manga Longa | 2 | 0.04% |
| Camisa Social Malha | 2 | 0.04% |
| Camiseta Gola Alta Manga Longa | 2 | 0.04% |

**3ª compra** — 632 chegaram (87.7% não voltaram). retenção 8.3% · mediana acumulada **280 dias**. intervalo desde a anterior **125 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 424 | 8.27% |
| Calça Jeans 1.0 | 76 | 1.48% |
| Outros Produtos | 43 | 0.84% |
| Camiseta Fitness | 39 | 0.76% |
| Carteira | 38 | 0.74% |
| Cueca | 28 | 0.55% |
| Camisa Social Tech Classics | 28 | 0.55% |
| Perfume | 27 | 0.53% |
| Camiseta Manga Longa | 25 | 0.49% |
| Calça Alfaiataria | 21 | 0.41% |
| Camisa Henley | 20 | 0.39% |
| Polo 2.0 | 14 | 0.27% |
| Overshirt | 13 | 0.25% |
| Calça Comfort | 11 | 0.21% |
| Suéter Classic 2026 | 7 | 0.14% |
| Polo 1.0 | 7 | 0.14% |
| Suéter Zíper | 6 | 0.12% |
| Polo Tricot | 5 | 0.10% |
| Calça Jeans 2.0 | 3 | 0.06% |
| Cueca Fitness | 3 | 0.06% |
| Calça Essential | 3 | 0.06% |
| Camiseta Gola Alta Manga Longa | 2 | 0.04% |
| Jaqueta Essential | 2 | 0.04% |
| Camiseta Gola Alta Manga Curta | 2 | 0.04% |
| Camisa Social Malha | 1 | 0.02% |
| Camiseta Modal Tech | 1 | 0.02% |
| Camiseta Fitness Manga Longa | 1 | 0.02% |
| Jaqueta Westfield | 1 | 0.02% |

**4ª compra** — 293 chegaram (94.3% não voltaram). retenção 3.6% · mediana acumulada **372 dias**. intervalo desde a anterior **94 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 183 | 3.57% |
| Calça Jeans 1.0 | 29 | 0.57% |
| Outros Produtos | 27 | 0.53% |
| Camiseta Fitness | 16 | 0.31% |
| Camisa Henley | 16 | 0.31% |
| Carteira | 15 | 0.29% |
| Perfume | 14 | 0.27% |
| Cueca | 13 | 0.25% |
| Calça Alfaiataria | 12 | 0.23% |
| Polo 2.0 | 12 | 0.23% |
| Camisa Social Tech Classics | 11 | 0.21% |
| Overshirt | 11 | 0.21% |
| Calça Comfort | 9 | 0.18% |
| Camiseta Manga Longa | 6 | 0.12% |
| Polo 1.0 | 4 | 0.08% |
| Jaqueta Essential | 3 | 0.06% |
| Calça Essential | 2 | 0.04% |
| Camisa Social Malha | 2 | 0.04% |
| Calça Jeans 2.0 | 2 | 0.04% |
| Jaqueta Westfield | 2 | 0.04% |
| Camiseta Gola Alta Manga Curta | 2 | 0.04% |
| Camiseta Fitness Manga Longa | 1 | 0.02% |
| Polo Tricot | 1 | 0.02% |
| Cueca Fitness | 1 | 0.02% |
| Suéter Zíper | 1 | 0.02% |
| Camiseta Gola Alta Manga Longa | 1 | 0.02% |
| Suéter Classic 2026 | 1 | 0.02% |
| Camiseta Modal Tech | 1 | 0.02% |

**5ª compra** — 153 chegaram (97.0% não voltaram). retenção 1.8% · mediana acumulada **484 dias**. intervalo desde a anterior **82 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 90 | 1.75% |
| Outros Produtos | 20 | 0.39% |
| Camiseta Fitness | 17 | 0.33% |
| Carteira | 12 | 0.23% |
| Calça Jeans 1.0 | 12 | 0.23% |
| Calça Alfaiataria | 10 | 0.19% |
| Cueca | 9 | 0.18% |
| Perfume | 9 | 0.18% |
| Camisa Social Tech Classics | 8 | 0.16% |
| Camisa Henley | 8 | 0.16% |
| Polo 2.0 | 6 | 0.12% |
| Calça Comfort | 5 | 0.10% |
| Overshirt | 5 | 0.10% |
| Polo Tricot | 3 | 0.06% |
| Camiseta Manga Longa | 3 | 0.06% |
| Suéter Classic 2026 | 3 | 0.06% |
| Camiseta Gola Alta Manga Longa | 3 | 0.06% |
| Jaqueta Westfield | 1 | 0.02% |
| Calça Jeans 2.0 | 1 | 0.02% |
| Camiseta Fitness Manga Longa | 1 | 0.02% |
| Suéter Zíper | 1 | 0.02% |
| Cueca Fitness | 1 | 0.02% |
| Camiseta Modal Tech | 1 | 0.02% |
| Camisa Social Malha | 1 | 0.02% |


### Camiseta + Jeans — 3.833 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal, Jeans.*

**2ª compra** — 1.065 chegaram (72.2% não voltaram). retenção 4.8% · mediana acumulada **64 dias**. intervalo desde a anterior **64 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 618 | 16.12% |
| Calça Jeans 1.0 | 405 | 10.57% |
| Calça Jeans 2.0 | 64 | 1.67% |
| Outros Produtos | 61 | 1.59% |
| Calça Alfaiataria | 55 | 1.43% |
| Camiseta Fitness | 55 | 1.43% |
| Cueca | 53 | 1.38% |
| Calça Comfort | 49 | 1.28% |
| Camisa Social Tech Classics | 46 | 1.20% |
| Carteira | 45 | 1.17% |
| Polo 2.0 | 41 | 1.07% |
| Camisa Henley | 41 | 1.07% |
| Perfume | 40 | 1.04% |
| Camiseta Manga Longa | 37 | 0.97% |
| Overshirt | 20 | 0.52% |
| Suéter Zíper | 16 | 0.42% |
| Cueca Fitness | 11 | 0.29% |
| Polo Tricot | 10 | 0.26% |
| Jaqueta Essential | 9 | 0.23% |
| Camisa Social Malha | 8 | 0.21% |
| Camiseta Modal Tech | 6 | 0.16% |
| Jaqueta Westfield | 6 | 0.16% |
| Suéter Classic 2026 | 5 | 0.13% |
| Calça Essential | 4 | 0.10% |
| Camiseta Gola Alta Manga Longa | 3 | 0.08% |
| Camiseta Fitness Manga Longa | 3 | 0.08% |
| Polo 1.0 | 2 | 0.05% |
| Camiseta Gola Alta Manga Curta | 2 | 0.05% |

**3ª compra** — 394 chegaram (89.7% não voltaram). retenção 0.9% · mediana acumulada **160 dias**. intervalo desde a anterior **63 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 203 | 5.30% |
| Calça Jeans 1.0 | 100 | 2.61% |
| Outros Produtos | 37 | 0.97% |
| Polo 2.0 | 30 | 0.78% |
| Camiseta Fitness | 29 | 0.76% |
| Calça Comfort | 29 | 0.76% |
| Camisa Social Tech Classics | 24 | 0.63% |
| Perfume | 20 | 0.52% |
| Cueca | 20 | 0.52% |
| Calça Alfaiataria | 19 | 0.50% |
| Calça Jeans 2.0 | 16 | 0.42% |
| Carteira | 14 | 0.37% |
| Camisa Henley | 14 | 0.37% |
| Overshirt | 9 | 0.23% |
| Cueca Fitness | 8 | 0.21% |
| Suéter Zíper | 8 | 0.21% |
| Polo Tricot | 5 | 0.13% |
| Camiseta Manga Longa | 4 | 0.10% |
| Camiseta Gola Alta Manga Curta | 4 | 0.10% |
| Camiseta Modal Tech | 3 | 0.08% |
| Suéter Classic 2026 | 3 | 0.08% |
| Jaqueta Essential | 3 | 0.08% |
| Calça Essential | 3 | 0.08% |
| Camiseta Gola Alta Manga Longa | 2 | 0.05% |
| Camiseta Fitness Manga Longa | 2 | 0.05% |
| Jaqueta Westfield | 2 | 0.05% |
| Polo 1.0 | 1 | 0.03% |
| Camisa Social Malha | 1 | 0.03% |

**4ª compra** — 176 chegaram (95.4% não voltaram). retenção 0.4% · mediana acumulada **212 dias**. intervalo desde a anterior **52 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 87 | 2.27% |
| Calça Jeans 1.0 | 30 | 0.78% |
| Outros Produtos | 23 | 0.60% |
| Camiseta Fitness | 17 | 0.44% |
| Calça Comfort | 16 | 0.42% |
| Calça Alfaiataria | 15 | 0.39% |
| Camisa Social Tech Classics | 12 | 0.31% |
| Polo 2.0 | 12 | 0.31% |
| Carteira | 10 | 0.26% |
| Perfume | 10 | 0.26% |
| Overshirt | 9 | 0.23% |
| Cueca | 8 | 0.21% |
| Camiseta Manga Longa | 6 | 0.16% |
| Calça Jeans 2.0 | 6 | 0.16% |
| Camiseta Fitness Manga Longa | 4 | 0.10% |
| Suéter Zíper | 4 | 0.10% |
| Jaqueta Westfield | 4 | 0.10% |
| Polo Tricot | 4 | 0.10% |
| Calça Essential | 3 | 0.08% |
| Jaqueta Essential | 3 | 0.08% |
| Camisa Henley | 3 | 0.08% |
| Camiseta Gola Alta Manga Curta | 2 | 0.05% |
| Suéter Classic 2026 | 2 | 0.05% |
| Cueca Fitness | 1 | 0.03% |
| Camisa Social Malha | 1 | 0.03% |
| Camiseta Modal Tech | 1 | 0.03% |
| Camiseta Gola Alta Manga Longa | 1 | 0.03% |

**5ª compra** — 89 chegaram (97.7% não voltaram). retenção 0.2% · mediana acumulada **223 dias**. intervalo desde a anterior **41 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 35 | 0.91% |
| Calça Jeans 1.0 | 22 | 0.57% |
| Outros Produtos | 12 | 0.31% |
| Calça Comfort | 8 | 0.21% |
| Camiseta Fitness | 6 | 0.16% |
| Polo 2.0 | 6 | 0.16% |
| Perfume | 4 | 0.10% |
| Camiseta Gola Alta Manga Curta | 3 | 0.08% |
| Camiseta Manga Longa | 3 | 0.08% |
| Cueca | 3 | 0.08% |
| Cueca Fitness | 3 | 0.08% |
| Jaqueta Essential | 3 | 0.08% |
| Polo Tricot | 3 | 0.08% |
| Calça Alfaiataria | 3 | 0.08% |
| Carteira | 3 | 0.08% |
| Camiseta Fitness Manga Longa | 2 | 0.05% |
| Camisa Social Malha | 2 | 0.05% |
| Camisa Social Tech Classics | 2 | 0.05% |
| Calça Essential | 2 | 0.05% |
| Suéter Classic 2026 | 2 | 0.05% |
| Calça Jeans 2.0 | 2 | 0.05% |
| Overshirt | 1 | 0.03% |
| Camisa Henley | 1 | 0.03% |
| Jaqueta Westfield | 1 | 0.03% |
| Suéter Zíper | 1 | 0.03% |


### Camiseta + Cueca — 3.475 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal, Cueca.*

**2ª compra** — 1.481 chegaram (57.4% não voltaram). retenção 7.1% · mediana acumulada **141 dias**. intervalo desde a anterior **141 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 1.021 | 29.38% |
| Cueca **(entrada)** | 425 | 12.23% |
| Outros Produtos | 96 | 2.76% |
| Camiseta Fitness | 93 | 2.68% |
| Calça Jeans 1.0 | 90 | 2.59% |
| Camiseta Manga Longa | 73 | 2.10% |
| Perfume | 54 | 1.55% |
| Cueca Fitness | 42 | 1.21% |
| Camisa Social Tech Classics | 41 | 1.18% |
| Carteira | 41 | 1.18% |
| Calça Alfaiataria | 22 | 0.63% |
| Camisa Henley | 21 | 0.60% |
| Calça Comfort | 18 | 0.52% |
| Polo 2.0 | 15 | 0.43% |
| Overshirt | 12 | 0.35% |
| Polo 1.0 | 10 | 0.29% |
| Suéter Classic 2026 | 8 | 0.23% |
| Calça Jeans 2.0 | 4 | 0.12% |
| Suéter Zíper | 2 | 0.06% |
| Camiseta Modal Tech | 1 | 0.03% |
| Camiseta Gola Alta Manga Longa | 1 | 0.03% |
| Polo Tricot | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |
| Calça Essential | 1 | 0.03% |
| Jaqueta Essential | 1 | 0.03% |
| Camisa Social Malha | 1 | 0.03% |
| Camiseta Fitness Manga Longa | 1 | 0.03% |

**3ª compra** — 754 chegaram (78.3% não voltaram). retenção 3.0% · mediana acumulada **316 dias**. intervalo desde a anterior **125 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 462 | 13.29% |
| Cueca **(entrada)** | 207 | 5.96% |
| Camiseta Fitness | 74 | 2.13% |
| Outros Produtos | 68 | 1.96% |
| Calça Jeans 1.0 | 51 | 1.47% |
| Camiseta Manga Longa | 43 | 1.24% |
| Calça Alfaiataria | 30 | 0.86% |
| Camisa Social Tech Classics | 25 | 0.72% |
| Carteira | 24 | 0.69% |
| Calça Comfort | 20 | 0.58% |
| Perfume | 20 | 0.58% |
| Cueca Fitness | 18 | 0.52% |
| Camisa Henley | 17 | 0.49% |
| Overshirt | 15 | 0.43% |
| Polo 1.0 | 11 | 0.32% |
| Suéter Classic 2026 | 10 | 0.29% |
| Suéter Zíper | 10 | 0.29% |
| Polo 2.0 | 6 | 0.17% |
| Jaqueta Essential | 6 | 0.17% |
| Calça Jeans 2.0 | 5 | 0.14% |
| Camiseta Modal Tech | 3 | 0.09% |
| Calça Essential | 3 | 0.09% |
| Camiseta Gola Alta Manga Longa | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |
| Polo Tricot | 1 | 0.03% |
| Camisa Social Malha | 1 | 0.03% |

**4ª compra** — 439 chegaram (87.4% não voltaram). retenção 1.2% · mediana acumulada **473 dias**. intervalo desde a anterior **143 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 251 | 7.22% |
| Cueca **(entrada)** | 93 | 2.68% |
| Camiseta Fitness | 47 | 1.35% |
| Outros Produtos | 43 | 1.24% |
| Calça Jeans 1.0 | 35 | 1.01% |
| Camisa Social Tech Classics | 25 | 0.72% |
| Camiseta Manga Longa | 20 | 0.58% |
| Calça Alfaiataria | 18 | 0.52% |
| Carteira | 17 | 0.49% |
| Perfume | 17 | 0.49% |
| Cueca Fitness | 16 | 0.46% |
| Camisa Henley | 12 | 0.35% |
| Polo 2.0 | 11 | 0.32% |
| Calça Comfort | 10 | 0.29% |
| Overshirt | 7 | 0.20% |
| Suéter Zíper | 4 | 0.12% |
| Polo 1.0 | 4 | 0.12% |
| Polo Tricot | 3 | 0.09% |
| Suéter Classic 2026 | 2 | 0.06% |
| Jaqueta Essential | 2 | 0.06% |
| Calça Essential | 1 | 0.03% |
| Jaqueta Westfield | 1 | 0.03% |
| Camiseta Gola Alta Manga Longa | 1 | 0.03% |
| Camiseta Modal Tech | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |
| Camisa Social Malha | 1 | 0.03% |
| Camiseta Fitness Manga Longa | 1 | 0.03% |

**5ª compra** — 258 chegaram (92.6% não voltaram). retenção 0.7% · mediana acumulada **564 dias**. intervalo desde a anterior **112 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 145 | 4.17% |
| Cueca **(entrada)** | 46 | 1.32% |
| Calça Jeans 1.0 | 29 | 0.83% |
| Outros Produtos | 23 | 0.66% |
| Camisa Social Tech Classics | 21 | 0.60% |
| Calça Alfaiataria | 20 | 0.58% |
| Camiseta Fitness | 18 | 0.52% |
| Perfume | 16 | 0.46% |
| Camiseta Manga Longa | 15 | 0.43% |
| Carteira | 9 | 0.26% |
| Calça Comfort | 8 | 0.23% |
| Overshirt | 7 | 0.20% |
| Camisa Henley | 6 | 0.17% |
| Polo 1.0 | 5 | 0.14% |
| Suéter Zíper | 5 | 0.14% |
| Suéter Classic 2026 | 5 | 0.14% |
| Cueca Fitness | 4 | 0.12% |
| Polo Tricot | 4 | 0.12% |
| Jaqueta Westfield | 4 | 0.12% |
| Camiseta Modal Tech | 3 | 0.09% |
| Calça Jeans 2.0 | 1 | 0.03% |
| Calça Essential | 1 | 0.03% |
| Jaqueta Essential | 1 | 0.03% |
| Camiseta Gola Alta Manga Longa | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |
| Polo 2.0 | 1 | 0.03% |


### Camisa Social Tech Classics — 3.284 clientes
*Precisa ter presente pra contar como retenção: Camisa Social Tech Classics.*

**2ª compra** — 852 chegaram (74.1% não voltaram). retenção 11.9% · mediana acumulada **50 dias**. intervalo desde a anterior **50 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camisa Social Tech Classics **(entrada)** | 391 | 11.91% |
| Camiseta Minimal | 291 | 8.86% |
| Calça Alfaiataria | 77 | 2.34% |
| Calça Jeans 1.0 | 68 | 2.07% |
| Outros Produtos | 47 | 1.43% |
| Carteira | 42 | 1.28% |
| Perfume | 39 | 1.19% |
| Camisa Henley | 30 | 0.91% |
| Camiseta Fitness | 29 | 0.88% |
| Overshirt | 27 | 0.82% |
| Calça Comfort | 26 | 0.79% |
| Cueca | 22 | 0.67% |
| Polo 2.0 | 17 | 0.52% |
| Camisa Social Malha | 12 | 0.37% |
| Camiseta Manga Longa | 11 | 0.33% |
| Polo 1.0 | 8 | 0.24% |
| Polo Tricot | 8 | 0.24% |
| Suéter Zíper | 5 | 0.15% |
| Camiseta Fitness Manga Longa | 3 | 0.09% |
| Calça Essential | 3 | 0.09% |
| Suéter Classic 2026 | 3 | 0.09% |
| Jaqueta Essential | 2 | 0.06% |
| Cueca Fitness | 2 | 0.06% |
| Calça Jeans 2.0 | 1 | 0.03% |
| Jaqueta Westfield | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |

**3ª compra** — 340 chegaram (89.6% não voltaram). retenção 3.2% · mediana acumulada **185 dias**. intervalo desde a anterior **68 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 116 | 3.53% |
| Camisa Social Tech Classics **(entrada)** | 106 | 3.23% |
| Calça Jeans 1.0 | 45 | 1.37% |
| Calça Alfaiataria | 33 | 1.00% |
| Outros Produtos | 28 | 0.85% |
| Overshirt | 23 | 0.70% |
| Camisa Henley | 19 | 0.58% |
| Polo 2.0 | 15 | 0.46% |
| Camiseta Fitness | 14 | 0.43% |
| Calça Comfort | 13 | 0.40% |
| Cueca | 12 | 0.37% |
| Carteira | 10 | 0.30% |
| Suéter Zíper | 9 | 0.27% |
| Perfume | 8 | 0.24% |
| Camisa Social Malha | 7 | 0.21% |
| Polo 1.0 | 5 | 0.15% |
| Polo Tricot | 4 | 0.12% |
| Calça Jeans 2.0 | 4 | 0.12% |
| Jaqueta Essential | 3 | 0.09% |
| Calça Essential | 2 | 0.06% |
| Jaqueta Westfield | 2 | 0.06% |
| Suéter Classic 2026 | 2 | 0.06% |
| Camiseta Manga Longa | 2 | 0.06% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |
| Camiseta Modal Tech | 1 | 0.03% |
| Camiseta Fitness Manga Longa | 1 | 0.03% |

**4ª compra** — 144 chegaram (95.6% não voltaram). retenção 0.9% · mediana acumulada **290 dias**. intervalo desde a anterior **52 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 53 | 1.61% |
| Camisa Social Tech Classics **(entrada)** | 28 | 0.85% |
| Calça Jeans 1.0 | 23 | 0.70% |
| Calça Alfaiataria | 16 | 0.49% |
| Outros Produtos | 14 | 0.43% |
| Calça Comfort | 9 | 0.27% |
| Suéter Zíper | 8 | 0.24% |
| Polo 2.0 | 7 | 0.21% |
| Camiseta Fitness | 7 | 0.21% |
| Camisa Henley | 7 | 0.21% |
| Overshirt | 6 | 0.18% |
| Polo Tricot | 4 | 0.12% |
| Cueca | 4 | 0.12% |
| Calça Essential | 3 | 0.09% |
| Perfume | 3 | 0.09% |
| Carteira | 3 | 0.09% |
| Jaqueta Westfield | 2 | 0.06% |
| Jaqueta Essential | 2 | 0.06% |
| Camiseta Manga Longa | 2 | 0.06% |
| Camiseta Modal Tech | 2 | 0.06% |
| Suéter Classic 2026 | 2 | 0.06% |
| Camisa Social Malha | 1 | 0.03% |
| Polo 1.0 | 1 | 0.03% |
| Calça Jeans 2.0 | 1 | 0.03% |
| Cueca Fitness | 1 | 0.03% |

**5ª compra** — 68 chegaram (97.9% não voltaram). retenção 0.1% · mediana acumulada **322 dias**. intervalo desde a anterior **41 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 18 | 0.55% |
| Outros Produtos | 10 | 0.30% |
| Calça Jeans 1.0 | 9 | 0.27% |
| Calça Comfort | 6 | 0.18% |
| Suéter Zíper | 6 | 0.18% |
| Camisa Social Tech Classics **(entrada)** | 4 | 0.12% |
| Calça Alfaiataria | 4 | 0.12% |
| Camisa Social Malha | 4 | 0.12% |
| Polo Tricot | 3 | 0.09% |
| Camiseta Fitness | 3 | 0.09% |
| Camisa Henley | 3 | 0.09% |
| Overshirt | 3 | 0.09% |
| Calça Jeans 2.0 | 3 | 0.09% |
| Perfume | 3 | 0.09% |
| Camiseta Manga Longa | 2 | 0.06% |
| Camiseta Modal Tech | 1 | 0.03% |
| Jaqueta Westfield | 1 | 0.03% |
| Camiseta Gola Alta Manga Longa | 1 | 0.03% |
| Cueca | 1 | 0.03% |
| Polo 2.0 | 1 | 0.03% |
| Suéter Classic 2026 | 1 | 0.03% |
| Carteira | 1 | 0.03% |


### Camiseta + Camiseta Fitness — 3.270 clientes
*Precisa ter presente pra contar como retenção: Camiseta Fitness, Camiseta Minimal.*

**2ª compra** — 1.083 chegaram (66.9% não voltaram). retenção 5.6% · mediana acumulada **84 dias**. intervalo desde a anterior **84 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 723 | 22.11% |
| Camiseta Fitness **(entrada)** | 320 | 9.79% |
| Calça Jeans 1.0 | 112 | 3.43% |
| Outros Produtos | 67 | 2.05% |
| Carteira | 58 | 1.77% |
| Camisa Social Tech Classics | 57 | 1.74% |
| Cueca | 48 | 1.47% |
| Perfume | 37 | 1.13% |
| Calça Alfaiataria | 35 | 1.07% |
| Camisa Henley | 31 | 0.95% |
| Polo 2.0 | 26 | 0.80% |
| Camiseta Manga Longa | 26 | 0.80% |
| Calça Comfort | 23 | 0.70% |
| Overshirt | 18 | 0.55% |
| Cueca Fitness | 15 | 0.46% |
| Calça Jeans 2.0 | 10 | 0.31% |
| Camiseta Fitness Manga Longa | 10 | 0.31% |
| Polo 1.0 | 9 | 0.28% |
| Jaqueta Essential | 4 | 0.12% |
| Polo Tricot | 4 | 0.12% |
| Camisa Social Malha | 3 | 0.09% |
| Suéter Zíper | 3 | 0.09% |
| Camiseta Modal Tech | 3 | 0.09% |
| Jaqueta Westfield | 2 | 0.06% |
| Camiseta Gola Alta Manga Longa | 1 | 0.03% |
| Suéter Classic 2026 | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |

**3ª compra** — 467 chegaram (85.7% não voltaram). retenção 1.9% · mediana acumulada **214 dias**. intervalo desde a anterior **93 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 270 | 8.26% |
| Camiseta Fitness **(entrada)** | 127 | 3.88% |
| Calça Jeans 1.0 | 57 | 1.74% |
| Outros Produtos | 42 | 1.28% |
| Camisa Social Tech Classics | 34 | 1.04% |
| Cueca | 22 | 0.67% |
| Carteira | 21 | 0.64% |
| Perfume | 20 | 0.61% |
| Calça Comfort | 20 | 0.61% |
| Camiseta Manga Longa | 19 | 0.58% |
| Calça Alfaiataria | 17 | 0.52% |
| Camisa Henley | 15 | 0.46% |
| Polo 2.0 | 9 | 0.28% |
| Overshirt | 7 | 0.21% |
| Camiseta Fitness Manga Longa | 7 | 0.21% |
| Cueca Fitness | 6 | 0.18% |
| Suéter Zíper | 6 | 0.18% |
| Polo Tricot | 6 | 0.18% |
| Calça Jeans 2.0 | 4 | 0.12% |
| Camisa Social Malha | 3 | 0.09% |
| Camiseta Modal Tech | 3 | 0.09% |
| Jaqueta Westfield | 2 | 0.06% |
| Suéter Classic 2026 | 2 | 0.06% |
| Jaqueta Essential | 2 | 0.06% |
| Polo 1.0 | 2 | 0.06% |
| Calça Essential | 1 | 0.03% |

**4ª compra** — 220 chegaram (93.3% não voltaram). retenção 1.0% · mediana acumulada **312 dias**. intervalo desde a anterior **111 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 117 | 3.58% |
| Camiseta Fitness **(entrada)** | 65 | 1.99% |
| Calça Jeans 1.0 | 31 | 0.95% |
| Outros Produtos | 22 | 0.67% |
| Perfume | 16 | 0.49% |
| Carteira | 14 | 0.43% |
| Camisa Social Tech Classics | 14 | 0.43% |
| Calça Comfort | 11 | 0.34% |
| Cueca | 10 | 0.31% |
| Camisa Henley | 10 | 0.31% |
| Camiseta Manga Longa | 9 | 0.28% |
| Calça Alfaiataria | 9 | 0.28% |
| Polo 2.0 | 8 | 0.24% |
| Overshirt | 6 | 0.18% |
| Suéter Zíper | 6 | 0.18% |
| Camiseta Fitness Manga Longa | 6 | 0.18% |
| Suéter Classic 2026 | 5 | 0.15% |
| Calça Jeans 2.0 | 4 | 0.12% |
| Polo Tricot | 4 | 0.12% |
| Calça Essential | 3 | 0.09% |
| Cueca Fitness | 2 | 0.06% |
| Camiseta Gola Alta Manga Curta | 2 | 0.06% |
| Jaqueta Essential | 2 | 0.06% |
| Jaqueta Westfield | 2 | 0.06% |
| Polo 1.0 | 1 | 0.03% |

**5ª compra** — 111 chegaram (96.6% não voltaram). retenção 0.4% · mediana acumulada **346 dias**. intervalo desde a anterior **59 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 61 | 1.87% |
| Camiseta Fitness **(entrada)** | 23 | 0.70% |
| Calça Jeans 1.0 | 16 | 0.49% |
| Outros Produtos | 11 | 0.34% |
| Polo 2.0 | 8 | 0.24% |
| Cueca | 8 | 0.24% |
| Polo Tricot | 7 | 0.21% |
| Calça Alfaiataria | 7 | 0.21% |
| Calça Jeans 2.0 | 7 | 0.21% |
| Calça Comfort | 6 | 0.18% |
| Camiseta Manga Longa | 6 | 0.18% |
| Camisa Social Tech Classics | 6 | 0.18% |
| Carteira | 4 | 0.12% |
| Camisa Henley | 4 | 0.12% |
| Overshirt | 3 | 0.09% |
| Suéter Zíper | 2 | 0.06% |
| Jaqueta Essential | 2 | 0.06% |
| Camiseta Fitness Manga Longa | 2 | 0.06% |
| Perfume | 2 | 0.06% |
| Suéter Classic 2026 | 2 | 0.06% |
| Polo 1.0 | 1 | 0.03% |
| Calça Essential | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |
| Camiseta Gola Alta Manga Longa | 1 | 0.03% |


### Camiseta Fitness — 3.233 clientes
*Precisa ter presente pra contar como retenção: Camiseta Fitness.*

**2ª compra** — 926 chegaram (71.4% não voltaram). retenção 9.7% · mediana acumulada **66 dias**. intervalo desde a anterior **66 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 501 | 15.50% |
| Camiseta Fitness **(entrada)** | 313 | 9.68% |
| Calça Jeans 1.0 | 56 | 1.73% |
| Outros Produtos | 42 | 1.30% |
| Camisa Social Tech Classics | 32 | 0.99% |
| Cueca | 25 | 0.77% |
| Polo 2.0 | 21 | 0.65% |
| Carteira | 19 | 0.59% |
| Calça Alfaiataria | 18 | 0.56% |
| Perfume | 16 | 0.49% |
| Camiseta Manga Longa | 14 | 0.43% |
| Camisa Henley | 14 | 0.43% |
| Cueca Fitness | 14 | 0.43% |
| Overshirt | 9 | 0.28% |
| Calça Comfort | 9 | 0.28% |
| Camiseta Fitness Manga Longa | 9 | 0.28% |
| Calça Jeans 2.0 | 3 | 0.09% |
| Polo Tricot | 3 | 0.09% |
| Suéter Classic 2026 | 3 | 0.09% |
| Camiseta Gola Alta Manga Curta | 2 | 0.06% |
| Camiseta Modal Tech | 2 | 0.06% |
| Polo 1.0 | 2 | 0.06% |
| Camisa Social Malha | 1 | 0.03% |
| Jaqueta Westfield | 1 | 0.03% |
| Suéter Zíper | 1 | 0.03% |

**3ª compra** — 388 chegaram (88.0% não voltaram). retenção 4.0% · mediana acumulada **194 dias**. intervalo desde a anterior **91 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 173 | 5.35% |
| Camiseta Fitness **(entrada)** | 129 | 3.99% |
| Calça Jeans 1.0 | 34 | 1.05% |
| Outros Produtos | 25 | 0.77% |
| Camisa Social Tech Classics | 22 | 0.68% |
| Cueca | 13 | 0.40% |
| Perfume | 11 | 0.34% |
| Calça Alfaiataria | 10 | 0.31% |
| Camisa Henley | 10 | 0.31% |
| Cueca Fitness | 9 | 0.28% |
| Camiseta Manga Longa | 8 | 0.25% |
| Polo 2.0 | 7 | 0.22% |
| Overshirt | 7 | 0.22% |
| Camiseta Fitness Manga Longa | 7 | 0.22% |
| Carteira | 5 | 0.15% |
| Calça Comfort | 5 | 0.15% |
| Polo 1.0 | 4 | 0.12% |
| Calça Jeans 2.0 | 4 | 0.12% |
| Camiseta Modal Tech | 4 | 0.12% |
| Jaqueta Essential | 3 | 0.09% |
| Polo Tricot | 2 | 0.06% |
| Camisa Social Malha | 2 | 0.06% |
| Calça Essential | 1 | 0.03% |
| Suéter Zíper | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |
| Suéter Classic 2026 | 1 | 0.03% |

**4ª compra** — 181 chegaram (94.4% não voltaram). retenção 1.6% · mediana acumulada **294 dias**. intervalo desde a anterior **77 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 76 | 2.35% |
| Camiseta Fitness **(entrada)** | 51 | 1.58% |
| Calça Jeans 1.0 | 16 | 0.49% |
| Camisa Social Tech Classics | 14 | 0.43% |
| Outros Produtos | 14 | 0.43% |
| Cueca | 8 | 0.25% |
| Calça Alfaiataria | 8 | 0.25% |
| Camiseta Fitness Manga Longa | 6 | 0.19% |
| Camiseta Manga Longa | 6 | 0.19% |
| Calça Comfort | 6 | 0.19% |
| Perfume | 5 | 0.15% |
| Camisa Henley | 5 | 0.15% |
| Polo 2.0 | 5 | 0.15% |
| Calça Jeans 2.0 | 4 | 0.12% |
| Carteira | 3 | 0.09% |
| Cueca Fitness | 2 | 0.06% |
| Jaqueta Westfield | 1 | 0.03% |
| Camisa Social Malha | 1 | 0.03% |
| Camiseta Modal Tech | 1 | 0.03% |
| Camiseta Gola Alta Manga Curta | 1 | 0.03% |
| Polo 1.0 | 1 | 0.03% |
| Jaqueta Essential | 1 | 0.03% |

**5ª compra** — 98 chegaram (97.0% não voltaram). retenção 0.8% · mediana acumulada **344 dias**. intervalo desde a anterior **76 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 39 | 1.21% |
| Camiseta Fitness **(entrada)** | 27 | 0.84% |
| Calça Jeans 1.0 | 11 | 0.34% |
| Outros Produtos | 10 | 0.31% |
| Cueca | 8 | 0.25% |
| Polo 2.0 | 5 | 0.15% |
| Camisa Social Tech Classics | 4 | 0.12% |
| Calça Alfaiataria | 3 | 0.09% |
| Cueca Fitness | 3 | 0.09% |
| Camisa Henley | 3 | 0.09% |
| Perfume | 2 | 0.06% |
| Calça Comfort | 2 | 0.06% |
| Calça Jeans 2.0 | 2 | 0.06% |
| Polo Tricot | 2 | 0.06% |
| Camiseta Manga Longa | 1 | 0.03% |
| Jaqueta Westfield | 1 | 0.03% |


### Overshirt — 2.711 clientes
*Precisa ter presente pra contar como retenção: Overshirt.*

**2ª compra** — 335 chegaram (87.6% não voltaram). retenção 5.4% · mediana acumulada **16 dias**. intervalo desde a anterior **16 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Overshirt **(entrada)** | 147 | 5.42% |
| Camiseta Minimal | 73 | 2.69% |
| Calça Comfort | 24 | 0.89% |
| Calça Jeans 1.0 | 18 | 0.66% |
| Jaqueta Westfield | 18 | 0.66% |
| Camisa Henley | 16 | 0.59% |
| Suéter Zíper | 15 | 0.55% |
| Camiseta Gola Alta Manga Curta | 10 | 0.37% |
| Outros Produtos | 10 | 0.37% |
| Carteira | 9 | 0.33% |
| Calça Alfaiataria | 8 | 0.30% |
| Calça Jeans 2.0 | 7 | 0.26% |
| Camiseta Manga Longa | 7 | 0.26% |
| Polo Tricot | 7 | 0.26% |
| Polo 2.0 | 7 | 0.26% |
| Cueca | 6 | 0.22% |
| Camiseta Gola Alta Manga Longa | 5 | 0.18% |
| Camisa Social Malha | 5 | 0.18% |
| Camisa Social Tech Classics | 4 | 0.15% |
| Calça Essential | 4 | 0.15% |
| Camiseta Fitness | 3 | 0.11% |
| Perfume | 2 | 0.07% |
| Jaqueta Essential | 2 | 0.07% |
| Suéter Classic 2026 | 1 | 0.04% |
| Camiseta Fitness Manga Longa | 1 | 0.04% |
| Camiseta Modal Tech | 1 | 0.04% |

**3ª compra** — 76 chegaram (97.2% não voltaram). retenção 0.8% · mediana acumulada **92 dias**. intervalo desde a anterior **18 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Overshirt **(entrada)** | 23 | 0.85% |
| Camiseta Minimal | 18 | 0.66% |
| Calça Comfort | 6 | 0.22% |
| Jaqueta Westfield | 6 | 0.22% |
| Calça Jeans 1.0 | 5 | 0.18% |
| Camiseta Gola Alta Manga Longa | 5 | 0.18% |
| Outros Produtos | 4 | 0.15% |
| Polo Tricot | 4 | 0.15% |
| Camiseta Fitness | 3 | 0.11% |
| Camisa Henley | 3 | 0.11% |
| Jaqueta Essential | 3 | 0.11% |
| Suéter Classic 2026 | 3 | 0.11% |
| Camiseta Gola Alta Manga Curta | 3 | 0.11% |
| Polo 2.0 | 3 | 0.11% |
| Calça Alfaiataria | 3 | 0.11% |
| Calça Essential | 2 | 0.07% |
| Suéter Zíper | 2 | 0.07% |
| Camiseta Manga Longa | 2 | 0.07% |
| Cueca | 2 | 0.07% |
| Camisa Social Tech Classics | 1 | 0.04% |
| Camiseta Fitness Manga Longa | 1 | 0.04% |
| Perfume | 1 | 0.04% |
| Carteira | 1 | 0.04% |


### Outros Produtos — 2.141 clientes
*Precisa ter presente pra contar como retenção: Outros Produtos.*

**2ª compra** — 517 chegaram (75.9% não voltaram). retenção 4.5% · mediana acumulada **127 dias**. intervalo desde a anterior **127 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 248 | 11.58% |
| Outros Produtos **(entrada)** | 97 | 4.53% |
| Calça Jeans 1.0 | 42 | 1.96% |
| Camiseta Fitness | 24 | 1.12% |
| Camiseta Manga Longa | 21 | 0.98% |
| Calça Alfaiataria | 20 | 0.93% |
| Cueca | 17 | 0.79% |
| Overshirt | 16 | 0.75% |
| Camisa Social Tech Classics | 15 | 0.70% |
| Calça Comfort | 10 | 0.47% |
| Camisa Henley | 9 | 0.42% |
| Suéter Zíper | 9 | 0.42% |
| Polo 2.0 | 8 | 0.37% |
| Suéter Classic 2026 | 7 | 0.33% |
| Carteira | 6 | 0.28% |
| Perfume | 5 | 0.23% |
| Cueca Fitness | 4 | 0.19% |
| Camisa Social Malha | 3 | 0.14% |
| Polo Tricot | 2 | 0.09% |
| Camiseta Gola Alta Manga Longa | 2 | 0.09% |
| Polo 1.0 | 2 | 0.09% |
| Calça Jeans 2.0 | 1 | 0.05% |
| Jaqueta Westfield | 1 | 0.05% |
| Calça Essential | 1 | 0.05% |
| Camiseta Gola Alta Manga Curta | 1 | 0.05% |
| Camiseta Modal Tech | 1 | 0.05% |

**3ª compra** — 229 chegaram (89.3% não voltaram). retenção 1.5% · mediana acumulada **277 dias**. intervalo desde a anterior **107 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 95 | 4.44% |
| Outros Produtos **(entrada)** | 33 | 1.54% |
| Calça Jeans 1.0 | 30 | 1.40% |
| Camiseta Fitness | 18 | 0.84% |
| Camiseta Manga Longa | 14 | 0.65% |
| Cueca | 10 | 0.47% |
| Calça Alfaiataria | 10 | 0.47% |
| Polo 2.0 | 8 | 0.37% |
| Overshirt | 7 | 0.33% |
| Calça Comfort | 7 | 0.33% |
| Perfume | 7 | 0.33% |
| Suéter Zíper | 5 | 0.23% |
| Camisa Social Tech Classics | 5 | 0.23% |
| Camisa Henley | 4 | 0.19% |
| Cueca Fitness | 3 | 0.14% |
| Carteira | 3 | 0.14% |
| Suéter Classic 2026 | 2 | 0.09% |
| Calça Jeans 2.0 | 2 | 0.09% |
| Camiseta Fitness Manga Longa | 2 | 0.09% |
| Jaqueta Essential | 2 | 0.09% |
| Camiseta Modal Tech | 1 | 0.05% |
| Jaqueta Westfield | 1 | 0.05% |
| Camiseta Gola Alta Manga Longa | 1 | 0.05% |
| Calça Essential | 1 | 0.05% |
| Polo 1.0 | 1 | 0.05% |

**4ª compra** — 108 chegaram (95.0% não voltaram). retenção 0.8% · mediana acumulada **432 dias**. intervalo desde a anterior **88 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 43 | 2.01% |
| Outros Produtos **(entrada)** | 17 | 0.79% |
| Camiseta Manga Longa | 8 | 0.37% |
| Camiseta Fitness | 8 | 0.37% |
| Calça Jeans 1.0 | 7 | 0.33% |
| Calça Comfort | 6 | 0.28% |
| Camisa Henley | 6 | 0.28% |
| Calça Alfaiataria | 5 | 0.23% |
| Overshirt | 5 | 0.23% |
| Cueca | 5 | 0.23% |
| Suéter Zíper | 4 | 0.19% |
| Suéter Classic 2026 | 4 | 0.19% |
| Camisa Social Tech Classics | 3 | 0.14% |
| Carteira | 3 | 0.14% |
| Perfume | 3 | 0.14% |
| Camiseta Fitness Manga Longa | 1 | 0.05% |
| Polo Tricot | 1 | 0.05% |
| Camisa Social Malha | 1 | 0.05% |
| Calça Essential | 1 | 0.05% |
| Polo 2.0 | 1 | 0.05% |

**5ª compra** — 66 chegaram (96.9% não voltaram). retenção 0.6% · mediana acumulada **507 dias**. intervalo desde a anterior **86 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 29 | 1.35% |
| Outros Produtos **(entrada)** | 12 | 0.56% |
| Calça Jeans 1.0 | 9 | 0.42% |
| Camiseta Fitness | 7 | 0.33% |
| Calça Alfaiataria | 7 | 0.33% |
| Camisa Social Tech Classics | 6 | 0.28% |
| Cueca | 5 | 0.23% |
| Carteira | 5 | 0.23% |
| Camiseta Manga Longa | 4 | 0.19% |
| Perfume | 4 | 0.19% |
| Polo 2.0 | 3 | 0.14% |
| Overshirt | 3 | 0.14% |
| Camisa Henley | 3 | 0.14% |
| Calça Comfort | 2 | 0.09% |
| Polo Tricot | 2 | 0.09% |
| Polo 1.0 | 2 | 0.09% |
| Camiseta Modal Tech | 1 | 0.05% |
| Camisa Social Malha | 1 | 0.05% |
| Cueca Fitness | 1 | 0.05% |
| Calça Jeans 2.0 | 1 | 0.05% |


### Cueca — 1.990 clientes
*Precisa ter presente pra contar como retenção: Cueca.*

**2ª compra** — 726 chegaram (63.5% não voltaram). retenção 9.8% · mediana acumulada **191 dias**. intervalo desde a anterior **191 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 428 | 21.51% |
| Cueca **(entrada)** | 196 | 9.85% |
| Camiseta Manga Longa | 41 | 2.06% |
| Calça Jeans 1.0 | 36 | 1.81% |
| Outros Produtos | 35 | 1.76% |
| Camiseta Fitness | 24 | 1.21% |
| Cueca Fitness | 20 | 1.01% |
| Camisa Social Tech Classics | 10 | 0.50% |
| Carteira | 9 | 0.45% |
| Perfume | 9 | 0.45% |
| Camisa Henley | 8 | 0.40% |
| Overshirt | 7 | 0.35% |
| Calça Alfaiataria | 5 | 0.25% |
| Calça Comfort | 5 | 0.25% |
| Suéter Classic 2026 | 5 | 0.25% |
| Polo 1.0 | 4 | 0.20% |
| Polo 2.0 | 3 | 0.15% |
| Calça Jeans 2.0 | 2 | 0.10% |
| Suéter Zíper | 1 | 0.05% |
| Jaqueta Essential | 1 | 0.05% |
| Camiseta Fitness Manga Longa | 1 | 0.05% |

**3ª compra** — 368 chegaram (81.5% não voltaram). retenção 3.5% · mediana acumulada **472 dias**. intervalo desde a anterior **190 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 216 | 10.85% |
| Cueca **(entrada)** | 69 | 3.47% |
| Camiseta Fitness | 27 | 1.36% |
| Outros Produtos | 25 | 1.26% |
| Calça Jeans 1.0 | 22 | 1.11% |
| Camiseta Manga Longa | 15 | 0.75% |
| Camisa Social Tech Classics | 11 | 0.55% |
| Calça Alfaiataria | 9 | 0.45% |
| Cueca Fitness | 8 | 0.40% |
| Overshirt | 7 | 0.35% |
| Camisa Henley | 6 | 0.30% |
| Perfume | 6 | 0.30% |
| Suéter Classic 2026 | 6 | 0.30% |
| Carteira | 4 | 0.20% |
| Polo 2.0 | 4 | 0.20% |
| Suéter Zíper | 3 | 0.15% |
| Calça Jeans 2.0 | 2 | 0.10% |
| Jaqueta Essential | 2 | 0.10% |
| Calça Comfort | 2 | 0.10% |
| Polo 1.0 | 1 | 0.05% |
| Camisa Social Malha | 1 | 0.05% |
| Polo Tricot | 1 | 0.05% |

**4ª compra** — 220 chegaram (88.9% não voltaram). retenção 1.3% · mediana acumulada **624 dias**. intervalo desde a anterior **151 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 114 | 5.73% |
| Cueca **(entrada)** | 26 | 1.31% |
| Calça Jeans 1.0 | 17 | 0.85% |
| Outros Produtos | 16 | 0.80% |
| Camiseta Fitness | 14 | 0.70% |
| Camiseta Manga Longa | 13 | 0.65% |
| Camisa Social Tech Classics | 10 | 0.50% |
| Calça Comfort | 7 | 0.35% |
| Camisa Henley | 7 | 0.35% |
| Overshirt | 7 | 0.35% |
| Calça Alfaiataria | 4 | 0.20% |
| Carteira | 4 | 0.20% |
| Cueca Fitness | 3 | 0.15% |
| Polo 2.0 | 3 | 0.15% |
| Suéter Classic 2026 | 3 | 0.15% |
| Polo 1.0 | 3 | 0.15% |
| Perfume | 2 | 0.10% |
| Calça Jeans 2.0 | 2 | 0.10% |
| Suéter Zíper | 1 | 0.05% |

**5ª compra** — 125 chegaram (93.7% não voltaram). retenção 0.9% · mediana acumulada **700 dias**. intervalo desde a anterior **135 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 62 | 3.12% |
| Cueca **(entrada)** | 17 | 0.85% |
| Outros Produtos | 13 | 0.65% |
| Calça Jeans 1.0 | 13 | 0.65% |
| Camiseta Fitness | 11 | 0.55% |
| Perfume | 8 | 0.40% |
| Camiseta Manga Longa | 7 | 0.35% |
| Calça Comfort | 4 | 0.20% |
| Camisa Henley | 4 | 0.20% |
| Calça Alfaiataria | 4 | 0.20% |
| Polo 2.0 | 4 | 0.20% |
| Polo 1.0 | 3 | 0.15% |
| Jaqueta Essential | 3 | 0.15% |
| Carteira | 3 | 0.15% |
| Camisa Social Tech Classics | 2 | 0.10% |
| Calça Essential | 2 | 0.10% |
| Overshirt | 2 | 0.10% |
| Cueca Fitness | 2 | 0.10% |


### Calça Comfort — 1.793 clientes
*Precisa ter presente pra contar como retenção: Calça Comfort.*

**2ª compra** — 452 chegaram (74.8% não voltaram). retenção 13.1% · mediana acumulada **28 dias**. intervalo desde a anterior **28 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Calça Comfort **(entrada)** | 235 | 13.11% |
| Camiseta Minimal | 102 | 5.69% |
| Calça Jeans 1.0 | 74 | 4.13% |
| Overshirt | 21 | 1.17% |
| Calça Alfaiataria | 21 | 1.17% |
| Calça Jeans 2.0 | 20 | 1.12% |
| Polo 2.0 | 15 | 0.84% |
| Outros Produtos | 15 | 0.84% |
| Camisa Henley | 11 | 0.61% |
| Camiseta Fitness | 10 | 0.56% |
| Camisa Social Tech Classics | 10 | 0.56% |
| Camiseta Gola Alta Manga Curta | 9 | 0.50% |
| Carteira | 6 | 0.33% |
| Polo Tricot | 6 | 0.33% |
| Camisa Social Malha | 6 | 0.33% |
| Calça Essential | 5 | 0.28% |
| Jaqueta Essential | 5 | 0.28% |
| Cueca | 4 | 0.22% |
| Perfume | 4 | 0.22% |
| Suéter Zíper | 4 | 0.22% |
| Camiseta Gola Alta Manga Longa | 4 | 0.22% |
| Suéter Classic 2026 | 3 | 0.17% |
| Camiseta Manga Longa | 2 | 0.11% |
| Jaqueta Westfield | 2 | 0.11% |
| Camiseta Modal Tech | 2 | 0.11% |
| Cueca Fitness | 1 | 0.06% |

**3ª compra** — 140 chegaram (92.2% não voltaram). retenção 3.0% · mediana acumulada **70 dias**. intervalo desde a anterior **24 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Calça Comfort **(entrada)** | 54 | 3.01% |
| Camiseta Minimal | 29 | 1.62% |
| Calça Jeans 1.0 | 17 | 0.95% |
| Overshirt | 13 | 0.73% |
| Outros Produtos | 12 | 0.67% |
| Calça Alfaiataria | 9 | 0.50% |
| Calça Jeans 2.0 | 9 | 0.50% |
| Calça Essential | 6 | 0.33% |
| Polo 2.0 | 6 | 0.33% |
| Camisa Social Tech Classics | 6 | 0.33% |
| Polo Tricot | 5 | 0.28% |
| Camiseta Fitness | 4 | 0.22% |
| Jaqueta Essential | 3 | 0.17% |
| Suéter Classic 2026 | 3 | 0.17% |
| Suéter Zíper | 3 | 0.17% |
| Camisa Social Malha | 3 | 0.17% |
| Perfume | 2 | 0.11% |
| Camiseta Gola Alta Manga Longa | 2 | 0.11% |
| Camisa Henley | 2 | 0.11% |
| Camiseta Manga Longa | 1 | 0.06% |
| Camiseta Gola Alta Manga Curta | 1 | 0.06% |
| Jaqueta Westfield | 1 | 0.06% |
| Cueca | 1 | 0.06% |

**4ª compra** — 63 chegaram (96.5% não voltaram). retenção 1.3% · mediana acumulada **88 dias**. intervalo desde a anterior **17 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Calça Comfort **(entrada)** | 24 | 1.34% |
| Outros Produtos | 7 | 0.39% |
| Calça Jeans 1.0 | 7 | 0.39% |
| Calça Jeans 2.0 | 6 | 0.33% |
| Camiseta Minimal | 6 | 0.33% |
| Camisa Social Tech Classics | 5 | 0.28% |
| Overshirt | 5 | 0.28% |
| Calça Essential | 4 | 0.22% |
| Camisa Social Malha | 3 | 0.17% |
| Jaqueta Essential | 3 | 0.17% |
| Camiseta Fitness | 3 | 0.17% |
| Polo 2.0 | 3 | 0.17% |
| Calça Alfaiataria | 3 | 0.17% |
| Cueca | 1 | 0.06% |
| Suéter Zíper | 1 | 0.06% |
| Jaqueta Westfield | 1 | 0.06% |
| Carteira | 1 | 0.06% |
| Camiseta Manga Longa | 1 | 0.06% |
| Camisa Henley | 1 | 0.06% |

**5ª compra** — 36 chegaram (98.0% não voltaram). retenção 0.4% · mediana acumulada **94 dias**. intervalo desde a anterior **16 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 10 | 0.56% |
| Calça Comfort **(entrada)** | 8 | 0.45% |
| Outros Produtos | 6 | 0.33% |
| Calça Jeans 1.0 | 5 | 0.28% |
| Jaqueta Essential | 3 | 0.17% |
| Calça Essential | 2 | 0.11% |
| Camiseta Fitness | 2 | 0.11% |
| Calça Jeans 2.0 | 2 | 0.11% |
| Jaqueta Westfield | 1 | 0.06% |
| Camiseta Gola Alta Manga Longa | 1 | 0.06% |
| Suéter Zíper | 1 | 0.06% |
| Camisa Social Tech Classics | 1 | 0.06% |
| Camiseta Fitness Manga Longa | 1 | 0.06% |
| Camiseta Manga Longa | 1 | 0.06% |
| Camisa Henley | 1 | 0.06% |
| Camiseta Gola Alta Manga Curta | 1 | 0.06% |
| Overshirt | 1 | 0.06% |


### Camiseta Manga Longa — 1.790 clientes
*Precisa ter presente pra contar como retenção: Camiseta Manga Longa.*

**2ª compra** — 622 chegaram (65.3% não voltaram). retenção 8.4% · mediana acumulada **144 dias**. intervalo desde a anterior **144 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 322 | 17.99% |
| Camiseta Manga Longa **(entrada)** | 150 | 8.38% |
| Outros Produtos | 47 | 2.63% |
| Calça Jeans 1.0 | 35 | 1.96% |
| Camiseta Fitness | 27 | 1.51% |
| Cueca | 20 | 1.12% |
| Camisa Social Tech Classics | 20 | 1.12% |
| Carteira | 11 | 0.61% |
| Overshirt | 11 | 0.61% |
| Calça Alfaiataria | 9 | 0.50% |
| Suéter Classic 2026 | 8 | 0.45% |
| Calça Comfort | 8 | 0.45% |
| Camisa Henley | 7 | 0.39% |
| Camiseta Fitness Manga Longa | 6 | 0.34% |
| Perfume | 6 | 0.34% |
| Polo 2.0 | 5 | 0.28% |
| Calça Jeans 2.0 | 3 | 0.17% |
| Suéter Zíper | 2 | 0.11% |
| Polo Tricot | 2 | 0.11% |
| Polo 1.0 | 2 | 0.11% |
| Jaqueta Westfield | 1 | 0.06% |
| Calça Essential | 1 | 0.06% |
| Jaqueta Essential | 1 | 0.06% |
| Camiseta Gola Alta Manga Longa | 1 | 0.06% |
| Camiseta Gola Alta Manga Curta | 1 | 0.06% |

**3ª compra** — 321 chegaram (82.1% não voltaram). retenção 3.5% · mediana acumulada **303 dias**. intervalo desde a anterior **105 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 170 | 9.50% |
| Camiseta Manga Longa **(entrada)** | 63 | 3.52% |
| Calça Jeans 1.0 | 29 | 1.62% |
| Outros Produtos | 21 | 1.17% |
| Camiseta Fitness | 17 | 0.95% |
| Camisa Social Tech Classics | 17 | 0.95% |
| Cueca | 11 | 0.61% |
| Carteira | 9 | 0.50% |
| Overshirt | 8 | 0.45% |
| Calça Alfaiataria | 7 | 0.39% |
| Polo 2.0 | 6 | 0.34% |
| Polo 1.0 | 5 | 0.28% |
| Perfume | 5 | 0.28% |
| Calça Comfort | 5 | 0.28% |
| Camisa Henley | 4 | 0.22% |
| Suéter Zíper | 4 | 0.22% |
| Camisa Social Malha | 2 | 0.11% |
| Calça Jeans 2.0 | 2 | 0.11% |
| Suéter Classic 2026 | 2 | 0.11% |
| Jaqueta Essential | 2 | 0.11% |
| Camiseta Modal Tech | 2 | 0.11% |
| Cueca Fitness | 1 | 0.06% |
| Camiseta Gola Alta Manga Curta | 1 | 0.06% |
| Calça Essential | 1 | 0.06% |
| Polo Tricot | 1 | 0.06% |
| Camiseta Fitness Manga Longa | 1 | 0.06% |
| Camiseta Gola Alta Manga Longa | 1 | 0.06% |

**4ª compra** — 174 chegaram (90.3% não voltaram). retenção 1.3% · mediana acumulada **404 dias**. intervalo desde a anterior **87 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 84 | 4.69% |
| Camiseta Manga Longa **(entrada)** | 24 | 1.34% |
| Calça Jeans 1.0 | 17 | 0.95% |
| Outros Produtos | 15 | 0.84% |
| Camiseta Fitness | 10 | 0.56% |
| Camisa Social Tech Classics | 6 | 0.34% |
| Overshirt | 5 | 0.28% |
| Camisa Henley | 5 | 0.28% |
| Calça Alfaiataria | 4 | 0.22% |
| Carteira | 4 | 0.22% |
| Calça Comfort | 3 | 0.17% |
| Cueca | 3 | 0.17% |
| Camiseta Gola Alta Manga Longa | 2 | 0.11% |
| Polo 1.0 | 2 | 0.11% |
| Polo Tricot | 2 | 0.11% |
| Suéter Classic 2026 | 2 | 0.11% |
| Cueca Fitness | 2 | 0.11% |
| Polo 2.0 | 2 | 0.11% |
| Perfume | 2 | 0.11% |
| Jaqueta Essential | 1 | 0.06% |
| Suéter Zíper | 1 | 0.06% |
| Calça Jeans 2.0 | 1 | 0.06% |

**5ª compra** — 111 chegaram (93.8% não voltaram). retenção 0.7% · mediana acumulada **544 dias**. intervalo desde a anterior **76 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 43 | 2.40% |
| Calça Jeans 1.0 | 14 | 0.78% |
| Camiseta Manga Longa **(entrada)** | 13 | 0.73% |
| Camisa Social Tech Classics | 9 | 0.50% |
| Outros Produtos | 8 | 0.45% |
| Camiseta Fitness | 6 | 0.34% |
| Cueca | 5 | 0.28% |
| Camiseta Gola Alta Manga Longa | 4 | 0.22% |
| Calça Comfort | 4 | 0.22% |
| Camiseta Fitness Manga Longa | 4 | 0.22% |
| Calça Alfaiataria | 3 | 0.17% |
| Camisa Henley | 3 | 0.17% |
| Calça Jeans 2.0 | 2 | 0.11% |
| Calça Essential | 2 | 0.11% |
| Jaqueta Essential | 2 | 0.11% |
| Suéter Zíper | 2 | 0.11% |
| Suéter Classic 2026 | 2 | 0.11% |
| Overshirt | 1 | 0.06% |
| Carteira | 1 | 0.06% |
| Polo 2.0 | 1 | 0.06% |
| Camiseta Modal Tech | 1 | 0.06% |
| Polo Tricot | 1 | 0.06% |
| Perfume | 1 | 0.06% |
| Jaqueta Westfield | 1 | 0.06% |


### Camisa Henley — 1.488 clientes
*Precisa ter presente pra contar como retenção: Camisa Henley.*

**2ª compra** — 348 chegaram (76.6% não voltaram). retenção 8.5% · mediana acumulada **60 dias**. intervalo desde a anterior **60 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camisa Henley **(entrada)** | 126 | 8.47% |
| Camiseta Minimal | 123 | 8.27% |
| Overshirt | 22 | 1.48% |
| Polo Tricot | 18 | 1.21% |
| Outros Produtos | 17 | 1.14% |
| Calça Comfort | 16 | 1.08% |
| Calça Jeans 1.0 | 15 | 1.01% |
| Camisa Social Tech Classics | 14 | 0.94% |
| Camiseta Fitness | 13 | 0.87% |
| Cueca | 13 | 0.87% |
| Polo 2.0 | 12 | 0.81% |
| Calça Alfaiataria | 11 | 0.74% |
| Suéter Zíper | 10 | 0.67% |
| Camiseta Manga Longa | 9 | 0.60% |
| Carteira | 8 | 0.54% |
| Perfume | 7 | 0.47% |
| Jaqueta Westfield | 4 | 0.27% |
| Camiseta Gola Alta Manga Longa | 3 | 0.20% |
| Camisa Social Malha | 2 | 0.13% |
| Camiseta Fitness Manga Longa | 2 | 0.13% |
| Camiseta Gola Alta Manga Curta | 1 | 0.07% |
| Cueca Fitness | 1 | 0.07% |
| Jaqueta Essential | 1 | 0.07% |
| Calça Jeans 2.0 | 1 | 0.07% |

**3ª compra** — 123 chegaram (91.7% não voltaram). retenção 2.3% · mediana acumulada **142 dias**. intervalo desde a anterior **50 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 36 | 2.42% |
| Camisa Henley **(entrada)** | 34 | 2.28% |
| Overshirt | 14 | 0.94% |
| Camisa Social Tech Classics | 9 | 0.60% |
| Polo 2.0 | 9 | 0.60% |
| Calça Comfort | 8 | 0.54% |
| Calça Jeans 1.0 | 7 | 0.47% |
| Outros Produtos | 6 | 0.40% |
| Polo Tricot | 5 | 0.34% |
| Suéter Zíper | 4 | 0.27% |
| Cueca | 4 | 0.27% |
| Calça Alfaiataria | 4 | 0.27% |
| Camiseta Fitness | 3 | 0.20% |
| Perfume | 2 | 0.13% |
| Camisa Social Malha | 2 | 0.13% |
| Cueca Fitness | 2 | 0.13% |
| Camiseta Manga Longa | 2 | 0.13% |
| Camiseta Fitness Manga Longa | 2 | 0.13% |
| Camiseta Gola Alta Manga Longa | 2 | 0.13% |
| Camiseta Gola Alta Manga Curta | 1 | 0.07% |
| Calça Jeans 2.0 | 1 | 0.07% |
| Suéter Classic 2026 | 1 | 0.07% |
| Camiseta Modal Tech | 1 | 0.07% |
| Carteira | 1 | 0.07% |

**4ª compra** — 53 chegaram (96.4% não voltaram). retenção 0.3% · mediana acumulada **197 dias**. intervalo desde a anterior **61 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 16 | 1.08% |
| Calça Jeans 1.0 | 8 | 0.54% |
| Camiseta Fitness | 6 | 0.40% |
| Camisa Social Tech Classics | 6 | 0.40% |
| Camisa Henley **(entrada)** | 5 | 0.34% |
| Outros Produtos | 5 | 0.34% |
| Overshirt | 5 | 0.34% |
| Calça Comfort | 4 | 0.27% |
| Polo Tricot | 3 | 0.20% |
| Suéter Zíper | 3 | 0.20% |
| Polo 2.0 | 3 | 0.20% |
| Carteira | 3 | 0.20% |
| Suéter Classic 2026 | 2 | 0.13% |
| Camiseta Gola Alta Manga Longa | 2 | 0.13% |
| Camiseta Gola Alta Manga Curta | 1 | 0.07% |
| Camiseta Manga Longa | 1 | 0.07% |
| Jaqueta Essential | 1 | 0.07% |
| Calça Alfaiataria | 1 | 0.07% |
| Jaqueta Westfield | 1 | 0.07% |


### Camiseta + Perfume — 1.435 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal, Perfume.*

**2ª compra** — 264 chegaram (81.6% não voltaram). retenção 1.6% · mediana acumulada **50 dias**. intervalo desde a anterior **50 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 182 | 12.68% |
| Perfume **(entrada)** | 37 | 2.58% |
| Calça Jeans 1.0 | 25 | 1.74% |
| Carteira | 21 | 1.46% |
| Camiseta Fitness | 16 | 1.11% |
| Camisa Social Tech Classics | 11 | 0.77% |
| Outros Produtos | 9 | 0.63% |
| Cueca | 9 | 0.63% |
| Calça Alfaiataria | 9 | 0.63% |
| Calça Comfort | 8 | 0.56% |
| Overshirt | 8 | 0.56% |
| Calça Jeans 2.0 | 8 | 0.56% |
| Camisa Henley | 7 | 0.49% |
| Camiseta Manga Longa | 5 | 0.35% |
| Polo 2.0 | 4 | 0.28% |
| Suéter Zíper | 4 | 0.28% |
| Camiseta Gola Alta Manga Curta | 2 | 0.14% |
| Camiseta Gola Alta Manga Longa | 2 | 0.14% |
| Cueca Fitness | 1 | 0.07% |
| Calça Essential | 1 | 0.07% |
| Jaqueta Essential | 1 | 0.07% |
| Camiseta Fitness Manga Longa | 1 | 0.07% |
| Polo Tricot | 1 | 0.07% |

**3ª compra** — 75 chegaram (94.8% não voltaram). retenção 0.3% · mediana acumulada **194 dias**. intervalo desde a anterior **104 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 45 | 3.14% |
| Perfume **(entrada)** | 9 | 0.63% |
| Calça Jeans 1.0 | 7 | 0.49% |
| Outros Produtos | 5 | 0.35% |
| Overshirt | 4 | 0.28% |
| Camiseta Manga Longa | 3 | 0.21% |
| Carteira | 3 | 0.21% |
| Calça Alfaiataria | 3 | 0.21% |
| Camiseta Fitness | 3 | 0.21% |
| Calça Jeans 2.0 | 2 | 0.14% |
| Camisa Henley | 2 | 0.14% |
| Calça Comfort | 1 | 0.07% |
| Suéter Classic 2026 | 1 | 0.07% |
| Polo Tricot | 1 | 0.07% |
| Polo 1.0 | 1 | 0.07% |
| Calça Essential | 1 | 0.07% |
| Polo 2.0 | 1 | 0.07% |
| Suéter Zíper | 1 | 0.07% |
| Camisa Social Malha | 1 | 0.07% |
| Cueca Fitness | 1 | 0.07% |
| Camisa Social Tech Classics | 1 | 0.07% |


### Camiseta + Social — 1.314 clientes
*Precisa ter presente pra contar como retenção: Camiseta Minimal, Social.*

**2ª compra** — 515 chegaram (60.8% não voltaram). retenção 5.8% · mediana acumulada **71 dias**. intervalo desde a anterior **71 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 295 | 22.45% |
| Camisa Social Tech Classics | 176 | 13.39% |
| Calça Jeans 1.0 | 70 | 5.33% |
| Carteira | 52 | 3.96% |
| Calça Alfaiataria | 38 | 2.89% |
| Perfume | 37 | 2.82% |
| Camiseta Fitness | 34 | 2.59% |
| Outros Produtos | 32 | 2.44% |
| Camisa Henley | 21 | 1.60% |
| Cueca | 19 | 1.45% |
| Overshirt | 15 | 1.14% |
| Camiseta Manga Longa | 14 | 1.07% |
| Polo 2.0 | 13 | 0.99% |
| Calça Comfort | 12 | 0.91% |
| Camisa Social Malha | 9 | 0.68% |
| Polo 1.0 | 8 | 0.61% |
| Cueca Fitness | 6 | 0.46% |
| Suéter Zíper | 6 | 0.46% |
| Camiseta Fitness Manga Longa | 4 | 0.30% |
| Camiseta Modal Tech | 3 | 0.23% |
| Jaqueta Essential | 2 | 0.15% |
| Calça Jeans 2.0 | 2 | 0.15% |
| Suéter Classic 2026 | 2 | 0.15% |
| Calça Essential | 1 | 0.08% |
| Camiseta Gola Alta Manga Curta | 1 | 0.08% |
| Polo Tricot | 1 | 0.08% |

**3ª compra** — 215 chegaram (83.6% não voltaram). retenção 1.3% · mediana acumulada **190 dias**. intervalo desde a anterior **93 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 117 | 8.90% |
| Camisa Social Tech Classics | 47 | 3.58% |
| Calça Jeans 1.0 | 27 | 2.05% |
| Outros Produtos | 24 | 1.83% |
| Perfume | 18 | 1.37% |
| Calça Alfaiataria | 16 | 1.22% |
| Camiseta Fitness | 14 | 1.07% |
| Camisa Henley | 12 | 0.91% |
| Cueca | 11 | 0.84% |
| Overshirt | 9 | 0.68% |
| Calça Comfort | 9 | 0.68% |
| Carteira | 9 | 0.68% |
| Camiseta Manga Longa | 8 | 0.61% |
| Camisa Social Malha | 7 | 0.53% |
| Polo 2.0 | 6 | 0.46% |
| Polo Tricot | 3 | 0.23% |
| Calça Essential | 3 | 0.23% |
| Jaqueta Essential | 3 | 0.23% |
| Suéter Zíper | 2 | 0.15% |
| Camiseta Fitness Manga Longa | 2 | 0.15% |
| Jaqueta Westfield | 2 | 0.15% |
| Polo 1.0 | 1 | 0.08% |
| Suéter Classic 2026 | 1 | 0.08% |
| Camiseta Gola Alta Manga Longa | 1 | 0.08% |
| Camiseta Modal Tech | 1 | 0.08% |

**4ª compra** — 91 chegaram (93.1% não voltaram). retenção 0.5% · mediana acumulada **243 dias**. intervalo desde a anterior **26 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 43 | 3.27% |
| Camisa Social Tech Classics | 13 | 0.99% |
| Outros Produtos | 13 | 0.99% |
| Camiseta Fitness | 12 | 0.91% |
| Calça Jeans 1.0 | 11 | 0.84% |
| Calça Alfaiataria | 7 | 0.53% |
| Cueca | 6 | 0.46% |
| Perfume | 6 | 0.46% |
| Camisa Henley | 5 | 0.38% |
| Carteira | 4 | 0.30% |
| Camiseta Manga Longa | 3 | 0.23% |
| Camisa Social Malha | 3 | 0.23% |
| Polo 2.0 | 3 | 0.23% |
| Calça Comfort | 2 | 0.15% |
| Overshirt | 2 | 0.15% |
| Camiseta Modal Tech | 2 | 0.15% |
| Camiseta Gola Alta Manga Curta | 1 | 0.08% |
| Cueca Fitness | 1 | 0.08% |
| Polo Tricot | 1 | 0.08% |

**5ª compra** — 48 chegaram (96.3% não voltaram). retenção 0.2% · mediana acumulada **280 dias**. intervalo desde a anterior **40 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal **(entrada)** | 20 | 1.52% |
| Camisa Social Tech Classics | 9 | 0.68% |
| Outros Produtos | 9 | 0.68% |
| Camiseta Fitness | 4 | 0.30% |
| Calça Alfaiataria | 4 | 0.30% |
| Camisa Henley | 3 | 0.23% |
| Overshirt | 3 | 0.23% |
| Calça Jeans 1.0 | 3 | 0.23% |
| Polo 2.0 | 3 | 0.23% |
| Camiseta Fitness Manga Longa | 2 | 0.15% |
| Cueca | 2 | 0.15% |
| Camisa Social Malha | 2 | 0.15% |
| Perfume | 2 | 0.15% |
| Camiseta Manga Longa | 1 | 0.08% |
| Carteira | 1 | 0.08% |
| Polo Tricot | 1 | 0.08% |
| Suéter Zíper | 1 | 0.08% |
| Suéter Classic 2026 | 1 | 0.08% |


### Polo 2.0 — 1.043 clientes
*Precisa ter presente pra contar como retenção: Polo 2.0.*

**2ª compra** — 194 chegaram (81.4% não voltaram). retenção 8.1% · mediana acumulada **32 dias**. intervalo desde a anterior **32 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Polo 2.0 **(entrada)** | 84 | 8.05% |
| Camiseta Minimal | 60 | 5.75% |
| Calça Comfort | 14 | 1.34% |
| Polo Tricot | 12 | 1.15% |
| Calça Jeans 1.0 | 11 | 1.05% |
| Camiseta Fitness | 10 | 0.96% |
| Calça Jeans 2.0 | 8 | 0.77% |
| Overshirt | 7 | 0.67% |
| Camisa Henley | 5 | 0.48% |
| Outros Produtos | 5 | 0.48% |
| Cueca | 4 | 0.38% |
| Jaqueta Essential | 3 | 0.29% |
| Calça Alfaiataria | 2 | 0.19% |
| Jaqueta Westfield | 2 | 0.19% |
| Suéter Zíper | 2 | 0.19% |
| Perfume | 2 | 0.19% |
| Calça Essential | 2 | 0.19% |
| Camisa Social Tech Classics | 2 | 0.19% |
| Suéter Classic 2026 | 1 | 0.10% |
| Camiseta Modal Tech | 1 | 0.10% |
| Cueca Fitness | 1 | 0.10% |
| Carteira | 1 | 0.10% |
| Camiseta Gola Alta Manga Longa | 1 | 0.10% |
| Camiseta Gola Alta Manga Curta | 1 | 0.10% |

**3ª compra** — 57 chegaram (94.5% não voltaram). retenção 1.1% · mediana acumulada **64 dias**. intervalo desde a anterior **32 dias**

| Produto | Clientes | % da entrada |
|---|---:|---:|
| Camiseta Minimal | 16 | 1.53% |
| Polo 2.0 **(entrada)** | 11 | 1.05% |
| Calça Jeans 1.0 | 7 | 0.67% |
| Overshirt | 5 | 0.48% |
| Outros Produtos | 5 | 0.48% |
| Calça Comfort | 4 | 0.38% |
| Jaqueta Essential | 4 | 0.38% |
| Cueca | 3 | 0.29% |
| Camisa Social Tech Classics | 3 | 0.29% |
| Calça Alfaiataria | 3 | 0.29% |
| Calça Jeans 2.0 | 3 | 0.29% |
| Suéter Zíper | 2 | 0.19% |
| Jaqueta Westfield | 2 | 0.19% |
| Suéter Classic 2026 | 2 | 0.19% |
| Camiseta Gola Alta Manga Longa | 2 | 0.19% |
| Camiseta Fitness | 1 | 0.10% |
| Camisa Henley | 1 | 0.10% |
| Polo Tricot | 1 | 0.10% |


---

## Onde estão os dados e o código

- Motor: `mc-growth/jornada_produto.py` (`montar_jornada`, `afinidade_por_compra`, `tempo_entre_compras`, `classificar_momento_compras`, `ltv_por_entrada`, `taxas_por_entrada`, `afinidade_por_momento`)
- Saída bruta: `mc-growth/saida_local/afinidade_produtos.csv`, `tempo_entre_compras.csv`, `sequencia_compras_detalhe.csv`, `afinidade_por_momento.csv`, `ltv_por_entrada.csv`, `taxas_por_entrada.csv`
- JSON do painel: `mc-growth/saida_local/jornada_dados.json` (gerado por `_agregar_dados_painel.py`)
- Painel visual local (Artifact, privado): https://claude.ai/code/artifact/f731ece0-8c8a-4de9-956c-f974f5732471

## Pendências / próximos passos

- [ ] Daniel decide se abre o bucket "Camiseta Minimal (outras qtd)" (38.274 clientes — maior que os buckets de 6un e 10un juntos) em sub-buckets (2un e 5un são picos reais também).
- [ ] Combos descobertos e ainda não aprovados: Camiseta + Manga Longa (4.786 clientes na base geral) ficou de fora por decisão do Daniel — revisar se entra numa leva futura.
- [ ] Nenhuma decisão duradoura registrada em ADR ainda — considerar um `docs/decisions/2026-07-23-jornada-de-produto-metodologia.md` se este método for usado de novo.
- [ ] Subir para o `gerenciadordecrm` (aba Recompra) **só após comando explícito do Daniel** — hoje é 100% local.
- [ ] **Achado a confirmar com o Daniel:** Polo 2.0 e Calça Comfort têm 0% de clientes "inativo hoje" — só faz sentido se essas linhas forem recentes o bastante pra ninguém ainda ter passado de 11 meses sem comprar desde a entrada. Vale checar a data de lançamento das linhas antes de usar esse número em qualquer decisão.
