# ADR 2026-07-16 — Combinações frequentes viram portas de entrada próprias

## Contexto
A porta de entrada de um cliente é a **linha de produto da estreia** (ADR
`2026-07-15-portas-de-entrada-produto`). Quando a estreia tinha **≥2 linhas**, tudo caía num
balde único **"Multiprodutos"** (30.632 clientes) — grande demais para auditar e cego às
combinações que se repetem. Na A3 (auditoria) criamos a tabela de combinações e o João viu que os
30k colapsam em poucas combinações fortes (a maior: *Calça Jeans 1.0 + Camiseta Minimal*, 4.058
clientes; 84% das estreias Multi incluem a Camiseta Minimal). Decisão dele: **essas combinações
devem virar categorias de verdade** (portas), aparecendo na aba 4 e na A3, não só num drill-down.

## Decisão
Uma **combinação de linhas (≥2)** vira uma **porta de entrada própria** — nome = a combinação
ordenada, ex.: `"Calça Jeans 1.0 + Camiseta Minimal"` — quando tem **ao menos
`LIMIAR_COMBO_PORTA = 1000` clientes de estreia elegível** (Shipped, idade 0). Abaixo do limiar, a
combinação continua no balde **"Multiprodutos"** (a cauda). O limiar é **global** (toda a história
fechada), então a porta de um cliente é estável em qualquer recorte de data.

- **1.000 clientes** foi a escolha do João (das opções 500/300/200/100 + livre). Hoje promove
  **6 combinações** e cobre 52,5% do antigo Multiprodutos; a cauda (14.546) segue "Multiprodutos".
- **Data-driven:** o conjunto de portas-combo cresce sozinho conforme a base — nenhuma lista
  curada a manter (≠ do `mapa_sku_linha_produto.csv`, que é a régua SKU→linha).

## Escopo (onde vale)
Vale em **todo o painel**, porque muda a coluna `porta` (a classificação por cliente):
- **Aba 4 (Portas de entrada):** as 6 combinações aparecem como linhas nas tabelas por safra e por
  linha, nas duas métricas (Lucro Bruto e Receita), e no seletor de produto.
- **A3 (Auditoria):** as combinações são portas selecionáveis; ao escolher "Multiprodutos", a
  tabela de combinações mostra só a **cauda** (< 1.000).
- **Guarda:** o check nº 6 segue válido — continua uma **partição** (cada cliente = uma porta) e
  `portas("todos")` agrega todos os clientes, independente da porta.

## Como fica no código (`portas.py`)
- `_combo_por_pedido(order_name → "A + B")` substitui `_porta_por_pedido` (antes já colapsava).
- `_porta_do_combo(combo, promovidos)`: vazio→desconhecido · 1 linha→a linha · ≥2→o combo se
  promovido, senão "Multiprodutos".
- `_combos_promovidos(enr, combo_pedido)`: conta clientes de estreia por combo e devolve os
  `≥ LIMIAR_COMBO_PORTA`.
- `calcular_portas` monta `promovidos` uma vez e chama `_porta_por_cliente(enr, combo_pedido,
  promovidos)`. `auditar_portas` herda tudo (usa a coluna `porta` de `calcular_portas`).

## Provas (2026-07-16)
- **Re-partição limpa:** total de clientes preservado; 6 combos = 16.086; Multiprodutos 30.632 →
  **14.546** (= 30.632 − 16.086); **Produto desconhecido inalterado** (21.713); **Camiseta Minimal
  inalterada** (193.616). Só os clientes das 6 combinações trocaram de "Multiprodutos" para a
  combinação — nada mais mudou.
- **Guarda 7/7:** partição intacta (0/64 safras) e `portas("todos")` = `coortes.lucro_bruto` **e**
  `coortes.ltv` ao centavo (a promoção não toca o "todos").
- `AppTest`: aba 4 e A3 sobem sem exceção; o seletor da aba 4 lista as 6 combinações.

## Consequências / ressalvas
- **Nomes longos** nas tabelas ("A + B") — aceito (é o preço de ser explícito).
- A aba 4 "por linha" ganha 6 linhas; a leitura por coluna (comparar portas numa janela) segue
  valendo. As combinações competem com as linhas únicas — é a segmentação desejada.
- Régua ainda **Lucro Bruto PARCIAL** / Receita bruta (inalterado).
- Se o João quiser outro corte, é **1 constante** (`LIMIAR_COMBO_PORTA`).

## Alternativas descartadas
- **Lista curada de combos** (como o mapa SKU→linha): mais controle, mas manutenção manual; o
  João preferiu o corte por frequência (auto-adapta).
- **Só uma sub-visão na A3** (não mexer na classificação): não faria as combinações virarem
  categorias de verdade — o que ele pediu.
