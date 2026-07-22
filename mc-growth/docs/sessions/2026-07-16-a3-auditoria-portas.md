# Sessão 2026-07-16 (2ª parte) — A3: Auditoria das portas (drill-down por cliente)

**Modo:** B (construção). **Objetivo:** aba de anexo para **validar os pedidos de cada porta de
entrada** — foco em Multiprodutos e Produto desconhecido, para achar oportunidade escondida.

## O que o João pediu (desenho dele, 3 passos)
1. Filtro de porta de entrada.
2. Lista tipo A1 dos clientes daquela porta.
3. Clicar num cliente → abre embaixo a **linha do tempo de compras** dele: produtos da 1ª
   compra, da 2ª, …, cada uma com a data / período (m+x).

(Antes disso, discovery: mostrei o diagnóstico dos baldes de "desconhecido" e ele confirmou o
drill-down. Os rankings agregados que propus — SKU candidato, combos de Multiprodutos — ele
**não** pediu nesta leva → foram para o backlog.)

## O que foi construído
- **`portas.auditar_portas` → `AuditoriaPortas`** (motor novo, aditivo): reusa
  `calcular_portas` (a MESMA coluna `porta` por cliente) e acrescenta, só para os desconhecidos,
  o **motivo** (4 baldes, régua espelhando `_porta_por_cliente`, vetorizado):
  `Comercial` · `Estreia fora da base` · `Sem itens casados` · `Só brinde/sem-nome`. Devolve as
  estreias (1 linha/cliente + nº de compras + valor total), todos os deals (linha do tempo) e
  os dicionários SKU→nome/linha/papel (nome de `dados.itens["descricao"]`).
- **`views/auditoria_portas.py`** (aba A3): filtro de porta (default "Produto desconhecido") +
  faixa de safra + busca; resuminho por motivo; lista com `st.dataframe(on_select)` (padrão A1);
  drill-down da linha do tempo ao clicar (produtos por compra + m+x). CSV da lista.
- **`painel.py`**: A3 registrada no menu depois da A2.

## Privacidade e trava de dinheiro
- **Nunca** exibe/exporta `e_mail` (fica num array paralelo à tabela, nunca vai à tela).
- No **Comercial** o `nome` é o **nome da pessoa** → mascarado "(Comercial)" na lista e no
  drill-down.
- **§11:** o drill-down **não** casa itens de deal **não-`Shipped`** — a numeração do Comercial
  colide com pedidos Shopify antigos e traria os itens de OUTRO pedido (achado na construção,
  corrigido). Igual ao CMV, que também só casa `Shipped`.

## Provas
- **Motivo bate com o diagnóstico medido:** Comercial 1.801 · fora da base 1.912 · **sem itens
  casados 11.721** · só brinde/sem-nome 6.279 (os dois primeiros somam 3.713 inerentes; os dois
  últimos, 18.000, são os **recuperáveis** — pedido Shopify no prazo que não virou porta).
- **CA4 partição:** Σ clientes por porta = `res.n_por_porta` (não perde/duplica gente) — True.
- **Drill-down** exercitado nos 4 casos sem exceção: só-ruído (3 SKUs não mapeados), sem-itens
  (compras antigas "SEM ITENS"), Comercial (estreia mascarada + itens pulados; recompras Shipped
  mostram), Multiprodutos (cliente com 24 compras, produtos e m+x corretos).
- **`AppTest`:** A3 sobe sem exceção (rodar as 7 telas juntas estoura o tempo do teste porque
  cada instância relê 1,3M itens + 462k deals sem cache compartilhado; A3 isolada passa).
- **Guarda `checar_coerencia.py`: 7/7** intacto (mudança em `portas.py` é aditiva).

## Achado de negócio (a oportunidade que o João buscava)
Dos 21.713 "Produto desconhecido", **11.721 são pedidos Shopify no prazo SEM nenhum item na
base** (lacuna de dado) e **6.279 têm itens mas nenhum mapeado como porta** (SKU a mapear). Juntos,
18.000 clientes (6,5%) que hoje somem da leitura por porta — potencial de recuperação.

## Adendo (mesma sessão) — Multiprodutos por combinação
O João testou ao vivo e apontou: "Multiprodutos tem 30k pedidos, impossível olhar um por um".
Resolvido **agregando pela combinação de linhas da estreia**:
- **`auditar_portas`** ganhou a coluna **`combo`** nas estreias (conjunto de linhas `porta` do
  pedido, reusando os `itens` já lidos — sem reler a base).
- **A3, porta = Multiprodutos:** mostra primeiro a **tabela de combinações** (`combinação | nº
  linhas | clientes | ticket médio 1ª | valor total`), ranqueada por clientes; **clicar numa
  combinação** filtra a lista de clientes (aí pequena) → drill-down por cliente que já existia.
  Fora do Multiprodutos, a A3 segue igual (lista direta).
- **Fato revelado:** 30.632 Multi → só **1.361 combinações** (81% pares); **Camiseta Minimal em
  84%** das estreias; top "Calça Jeans 1.0 + Camiseta Minimal" 4.058 (ticket R$ 745), "Camiseta +
  Cueca" 3.532, "Fitness + Camiseta" 3.438. Decisão do João: "Combinações + clicar pra abrir".
- **Provas:** combos batem ao centavo com a exploração; guarda **7/7**; `AppTest` sobe a A3 com
  Multiprodutos sem exceção; fluxo combo→lista→timeline exercitado (Camiseta+Cueca 3.532).

## Adendo 2 (mesma sessão) — Combinações viram portas de entrada
Vendo a tabela de combinações, o João pediu: **essas combinações têm de virar categorias de
verdade** (portas), não só um drill-down. Decisão registrada no ADR
`2026-07-16-combinacoes-viram-portas`:
- **Regra:** combinação de linhas (≥2) com **≥ 1.000 clientes de estreia** (`LIMIAR_COMBO_PORTA`)
  vira porta própria (nome "A + B"); abaixo, fica "Multiprodutos" (cauda). Limiar global.
- **Escopo:** todo o painel (aba 4 + A3 + guarda), porque muda a coluna `porta`.
- **Corte 1.000 (escolha do João):** promove **6 combinações** (maior: Calça Jeans 1.0 + Camiseta
  Minimal, 4.058), cobre 52,5% do antigo Multiprodutos.
- **Refactor `portas.py`:** `_porta_por_pedido` → `_combo_por_pedido` (order_name → "A + B");
  novos `_porta_do_combo` e `_combos_promovidos`; `calcular_portas` monta `promovidos` 1×.
- **Provas:** re-partição limpa (só as 6 combinações trocam de balde — Multiprodutos 30.632 →
  14.546; desconhecido 21.713 e Camiseta 193.616 **inalterados**; total preservado); guarda
  **7/7** (partição 0/64 + "todos" = Cohorts nas 2 métricas ao centavo); `AppTest` sobe aba 4 e
  A3, e o seletor da aba 4 lista as 6 combinações. Tuning = 1 constante.

## Adendo 3 (mesma sessão) — 2 correções vistas ao vivo (João)
Testando a A3, o João achou pedidos "classificados errados". Diagnóstico + fix:
- **Privacidade (122 deals Shipped, 0,03%):** alguns deals `Shipped` trazem **nome de PESSOA** no
  `nome` (ex.: "Douglas Costa Pena"), não um número — e apareciam **crus** na tela (a máscara só
  pegava não-Shipped). Fix: `_pedido_visivel` mascara **qualquer `nome` não-numérico** →
  "(sem nº)". Zero nome de pessoa visível agora.
- **Estreia mal escolhida (0,9% têm >1 pedido no 1º dia):** o desempate de mesma data era só
  alfabético pelo número → um cliente com 4 pedidos no mesmo dia (3 com Camiseta, 1 sem itens)
  herdava a estreia **sem itens** e caía em "desconhecido" (caso #14461). Fix: novo helper
  `_estreias(enr, com_porta)` — no empate de data, **prefere o pedido que TEM produto** (≥1 linha
  `porta`); usado por `calcular_portas` E `auditar_portas` (uma verdade). #14461 agora = Camiseta
  Minimal (estreia = o irmão #239931, com itens).
- **Efeito:** re-partição limpa e **só melhora** — "desconhecido" 21.713 → **21.654** (59 clientes
  resgatados para portas reais); Multiprodutos intacto (14.546); total preservado. Guarda **7/7**;
  `AppTest` sobe A3 + aba 4.

## Backlog aberto
- **Mesma agregação para "Produto desconhecido"** (por SKU não mapeado, para achar candidatos a
  virar porta) — os combos de Multiprodutos já foram entregues nesta sessão. Anotado no BACKLOG.

## Recarregar o painel
Módulos novos/alterados (`portas.py`, `views/auditoria_portas.py`, `painel.py`) → o `watchdog`
não está instalado → **reiniciar o painel** para o menu pegar a A3.
