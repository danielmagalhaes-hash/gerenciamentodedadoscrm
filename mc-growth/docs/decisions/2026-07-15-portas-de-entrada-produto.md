# ADR — Aba "Portas de entrada": Lucro Bruto por cliente por produto de estreia

**Data:** 2026-07-15
**Status:** Aceito
**Tema:** portas-de-entrada-produto

---

## 1. Contexto

A spec `2026-07-15-portas-de-entrada-produto.md` (discovery da mesma data) definiu uma aba nova
— **"4. Portas de entrada"** — para responder *"quanto de Lucro Bruto cada porta de entrada
(produto da 1ª compra) devolve por cliente ao longo do tempo?"* e assim negociar **CAC-teto /
ROAS-alvo diferenciado por porta**. A spec deixou **um detalhe em aberto** para a construção
resolver: como o item **"sem nome"** (SKU sem nome cadastrado, papel `desconhecido` no mapa)
interage com a regra de "categoria única" — `camiseta + item-sem-nome` vira "Multiprodutos" ou
"Camiseta"?

A régua de dado (`bases/mapa_sku_linha_produto.csv`, SKU→linha) já estava **validada à mão pelo
João**. Faltava construir o motor + a aba + o guarda de coerência, sem criar verdade nova de custo
nem de CAC (CLAUDE.md §11: cada definição tem um dono só).

Esta sessão construiu tudo e **resolveu o detalhe em aberto** (com o João, na hora).

---

## 2. Decisão

**A porta de entrada de um cliente = a linha de produto do seu pedido de ESTREIA** (o deal mais
antigo do cliente na base), resolvida pela ponte `hubspot.nome → itens (3 camadas) → SKU →
`mapa_sku_linha_produto.csv` → linha`, com estas regras:

1. **Ruído removido antes de decidir:** itens de papel `brinde` **e** de papel `desconhecido`
   ("sem nome") saem do pedido. Só os itens de papel `porta` decidem a categoria. Sobra **1**
   linha → essa porta; **>1** → "Multiprodutos"; **0** (só brinde/sem-nome, ou pedido sem itens)
   → "Produto desconhecido". Logo **`camiseta + item-sem-nome` = "Camiseta"** (o detalhe em
   aberto, resolvido pelo João: o "sem nome" é ruído, não uma categoria).
2. **Travas de dinheiro, idênticas às do CMV:** só deal **`Shipped`** pode casar itens (o
   Comercial grava número de outra numeração que colide — `cascata.pode_casar_itens`); estreia no
   Comercial → "Produto desconhecido". E a estreia tem de ter **idade 0** (cair no mês de estreia
   do cliente); se a 1ª compra real é anterior à base (cross-canal ou pré-out/2021), a estreia que
   temos é uma recompra e o produto de entrada é desconhecido → "Produto desconhecido".

**A célula é o Lucro Bruto acumulado por cliente** (antes da mídia), reusando `coortes.lucro_bruto`
(NÃO a MC — a MC já desconta a mídia; dividi-la pelo CAC contaria a mídia 2×, ADR
`2026-07-14-ratio-contra-cac-usa-lucro-bruto`). **O CAC é o blended do mês** (mídia ÷ TODOS os
novos do mês), o mesmo para qualquer produto — é régua de comparação, não CAC por produto. As
colunas `1ª compra | 30D | 60D | 90D | 180D | 365D` são **apelidos dos meses m+0/m+1/m+2/m+5/m+11
da Cohorts** (batem por construção; nenhum ADR de divergência). Duas tabelas: **por safra**
(obedece ao filtro de produto; "todos" = idêntica à Cohorts) e **por linha de produto** (obedece
ao filtro de data; cada janela usa só as safras maduras para ela). **N mínimo = 300** (ajustável).

---

## 3. Motivação

- **Uma verdade de custo/CAC (CLAUDE.md §11):** o motor não recalcula dinheiro — reusa
  `coortes.preparar_deals_cache` (MC de produto, safra, idade) e `coortes.calcular_coortes` (CAC
  blended, Lucro Bruto). A porta é a **única** dimensão nova. O guarda prova que "todos" é a
  Cohorts ao centavo (dif 0,0) e que as portas **particionam** os clientes (0/64 safras perdem
  gente).
- **"Sem nome" = ruído (decisão do João):** brinde é *sabidamente* não-produto; "sem nome" é
  falta de cadastro (2,6% das unidades), não um produto diferente de verdade. Tratá-lo como
  brinde (remover) atribui o pedido à porta conhecida em vez de escondê-lo em "Multiprodutos".
  **Impacto medido: 6.727 estreias (2,47%)** têm porta+sem-nome no mesmo pedido — não é
  desprezível; por isso a escolha foi explícita. É um flag de 1 linha se um dia quiser inverter.
- **Honestidade da régua:** rótulo "Lucro Bruto PARCIAL" na tela (sem devolução/CX/juros/criativo
  — e a devolução por produto é o custo que mais difere entre portas, registrado como ressalva).

---

## 4. Alternativas consideradas

### Alternativa A: "sem nome" é uma categoria (mix → Multiprodutos)
- **Descrição:** `camiseta + item-sem-nome` → 2 categorias → "Multiprodutos".
- **Prós:** conservador — não afirma "Camiseta" quando há um item desconhecido.
- **Contras:** joga 2,47% dos clientes para "Multiprodutos" por uma falha de cadastro, escondendo
  a porta conhecida que claramente participou da estreia.
- **Por que foi descartada:** o João preferiu recuperar a porta conhecida; o "sem nome" é gap de
  dado, não sinal. (Era o default que eu propus; ele inverteu.)

### Alternativa B: célula = MC por cliente (não Lucro Bruto)
- **Descrição:** usar a MC acumulada (já com a mídia) na célula.
- **Contras:** a mídia é bolo mensal, não se segmenta por produto; e dividir a MC pelo CAC contaria
  a mídia 2×.
- **Por que foi descartada:** ADR `2026-07-14-ratio-contra-cac-usa-lucro-bruto` — o numerador certo
  é o Lucro Bruto (antes da mídia). O CAC entra como coluna separada (blended), não como divisor.

### Alternativa C: estreia = deal carimbado "Primeira Compra"
- **Descrição:** usar `mascara_cliente_novo` para achar a estreia.
- **Contras:** o carimbo do HubSpot erra nas bordas (59 primeiras compras marcadas "Recompra") →
  clientes ficariam sem estreia e cairiam em "desconhecido" indevidamente, quebrando a partição.
- **Por que foi descartada:** o deal **mais antigo** por cliente é robusto e garante a partição
  (todo cliente tem um). A trava de idade 0 honra o viés cross-canal da spec §3.1.

---

## 5. Consequências

- **Novo módulo `portas.py`** (reusa `coortes.py`), **carregador `dados.carregar_mapa_portas`**,
  **aba `views/portas_entrada.py`** (menu "4. Portas de entrada"), e o **check nº 6** em
  `checar_coerencia.py` (portas "todos" × Cohorts + partição).
- **Régua parcial** e **viés cross-canal** (estreia fora do Shopify → "Produto desconhecido")
  seguem rotulados na tela — leitura comparativa, não fully-loaded.
- **Provisório a questionar (BACKLOG):** a régua de "categoria única", os 134 SKUs sem nome, a
  subdivisão de "Camiseta Minimal" (74,6%) e o balde "Outros Produtos".
- **Spec congelada** (regra do §6 do CLAUDE.md — spec é foto do dia); este ADR corrige/registra o
  rumo (o detalhe do "sem nome" resolvido ao contrário do default da spec).

---

## 6. Adendo (2026-07-16) — switch de leitura e a "queda" da tabela por linha

Ao usar a aba, o João pediu ajustes que viram régua:

- **Switch de leitura "Valor total (R$)" × "Aumento vs 1ª compra (×)"** (só na aba 4, nas duas
  tabelas). No modo múltiplo, célula = Lucro Bruto acumulado **÷ o da 1ª compra da própria linha**
  (base 1,00×). É **lente de display**: não recalcula custo/CAC, o CAC segue em R$, o guarda (check
  nº 6) fica intacto. 1ª compra ≤ 0 → "—".
- **Tabela por linha ordenada por nº de clientes** (maior→menor); "Multiprodutos" e "Produto
  desconhecido" fixos no fim (baldes, não portas comparáveis).
- **A tabela por linha NÃO é monotônica de propósito** (uma coluna pode ser menor que a anterior).
  Causa: cada janela usa só as safras **maduras para ela**, então o grupo por trás de cada coluna
  **muda** — é **composição**, não queda de valor (ex.: Calça Jeans 2.0 cai de R$ 148,78 no 30D
  para R$ 146,16 no 60D porque a safra 2026-06, forte na entrada, sai do 60D por falta de
  maturidade). **Decisão do João: Opção 1** — manter o máximo de dado e **explicar na tela** (aviso
  "leia por coluna, não por linha" + exemplo). A **Opção 2** (travar a turma → curva sempre-sobe,
  menos dado) foi **descartada** e virou item de backlog (possível 2º switch). A curva
  estritamente-cumulativa (a mesma turma no tempo) é a **tabela por safra**.
- **Dívida registrada (backlog):** mostrar o **N por coluna** na tabela por linha tornaria a
  composição auto-evidente (hoje só há o texto); o motor já devolve o `n` por célula.
