# Spec — A3: Auditoria das portas de entrada (drill-down por cliente)

**Data:** 2026-07-16 · **Modo:** B (construção) · **Autor do desenho:** João.

## Pergunta / objetivo
Validar os pedidos de cada porta de entrada — especialmente **Multiprodutos** e **Produto
desconhecido** — para achar oportunidade escondida (SKU que merecia virar porta, combinação
comum, classificação errada). Ferramenta de conferência, não de leitura de KPI.

## Desenho (do João, 3 passos)
1. **Filtro de porta de entrada** (dropdown: as linhas + Multiprodutos + Produto desconhecido).
2. **Lista tipo A1** dos clientes daquela porta (1 linha por cliente; a estreia define a porta).
3. **Clicar num cliente → abre embaixo a linha do tempo de compras dele**: produtos da 1ª
   compra, da 2ª compra, …, cada uma com a **data / período** (m+x) em que aconteceu.

## Dados (nenhuma verdade nova de dinheiro)
- Reusa `portas.calcular_portas` → `res.enr` (todos os deals já com a coluna **`porta`** por
  cliente — a MESMA classificação da aba 4; um cliente = uma porta, pela estreia).
- **Produtos de um pedido:** `cascata.itens_por_nome` (3 camadas) → `order_name → sku, qtd`.
  Nome do produto = `dados.itens["descricao"]` (714 SKUs nomeados); linha/papel = mapa.
- **Motivo do "Produto desconhecido"** (por que a estreia não virou porta), 4 baldes:
  `Comercial` (etapa ≠ Shipped, numeração colide) · `Estreia fora da base` (idade ≠ 0:
  cross-canal / pré-out-2021) · `Sem itens casados` (Shipped, no prazo, mas o pedido não tem
  itens na base) · `Só brinde/sem-nome` (tem itens, mas nenhum é papel `porta`). Owner novo:
  `portas.auditar_portas` (espelha a régua de `_porta_por_cliente`, só rotula o porquê).

## Privacidade (trava)
- **Nunca** exibir/exportar `e_mail`.
- No **Comercial** o `nome` do deal é o **nome da pessoa** (não um número) → **mascarar**
  como "(Comercial)" na lista e na linha do tempo. Só pedidos `Shipped` mostram o número.

## Tela (`views/auditoria_portas.py`, anexo "A3")
- Controles: porta (default "Produto desconhecido"); faixa de safra (de/até); busca por nº.
- Quando a porta é "Produto desconhecido": um **resuminho por motivo** (contagem por balde) —
  mostra quanto do desconhecido é inerente (Comercial/fora da base) × recuperável (sem itens /
  só ruído).
- **Lista** (1 linha/cliente): data da estreia · pedido de estreia (mascarado no Comercial) ·
  nº de compras · valor da 1ª compra · valor total · motivo. `st.dataframe` com
  `on_select="single-row"` (padrão do A1). Cap de segurança de linhas + aviso p/ estreitar.
- **Drill-down** (ao clicar): para cada compra do cliente, em ordem de data — cabeçalho
  "🛍️ Compra N · data · m+x · R$ valor · pedido" + tabela dos itens (produto · SKU · linha ·
  papel · qtd). Pedido sem itens na base → nota "sem itens casados".
- Só lê. Vocabulário: MC/Lucro Bruto, nunca "lucro líquido".

## O que conta como pronto (aceite)
- CA1: escolher "Produto desconhecido" lista os clientes; o resuminho por motivo bate com o
  diagnóstico já medido (Comercial 1.801 · fora da base 1.912 · Shipped+idade0 18.000, este
  último repartido em sem-itens × só-ruído).
- CA2: clicar num cliente abre a linha do tempo com produtos por compra e o m+x correto.
- CA3: nenhum e-mail e nenhum nome de pessoa (Comercial) aparece na tela ou no CSV.
- CA4: a soma dos clientes listados por porta (faixa cheia) = `res.n_por_porta` (não perde/
  duplica gente) — reusa a partição já provada no check nº 6.
- CA5: `AppTest` sobe as 7 telas sem exceção.

## Fora de escopo (backlog)
- Ranking de SKUs candidatos a virar porta (agregado) e combos mais comuns em Multiprodutos —
  úteis, mas o João pediu o drill-down primeiro. Anotar em `docs/BACKLOG.md`.
