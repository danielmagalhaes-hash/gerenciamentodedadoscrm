# Sessão 2026-07-15 — Construção da aba "4. Portas de entrada"

**Modo:** B (construção). **Objetivo:** construir a aba nova, já especificada e desbloqueada na
sessão de discovery da manhã (`docs/specs/2026-07-15-portas-de-entrada-produto.md`).

## O que o João pediu
Construir a aba "4. Portas de entrada": um motor que **reusa `coortes.py`** (nada de verdade nova
de custo/CAC), célula = **Lucro Bruto acumulado/cliente** (não a MC), colunas na régua da Cohorts,
CAC blended, porta = linha de produto da estreia (ponte `hubspot.nome → itens → mapa`), duas
tabelas (por safra e por linha), N mínimo 300, **resolver o detalhe do "sem nome"**, novo check de
coerência, `AppTest` das 5 telas. Antes de codar: validar contexto e mostrar o plano.

## Como foi
1. **Li o contexto** (spec, discovery, mapa, `coortes.py`, `coortes_ui.py`, `checar_coerencia.py`,
   `painel.py`, e as funções da ponte em `cascata.py`/`dados.py`).
2. **Mostrei o plano de build** e perguntei. **Decisão do João no detalhe em aberto:** inverteu o
   meu default — o item **"sem nome" é ruído** (removido como brinde) → `camiseta + sem-nome =
   "Camiseta"`, não "Multiprodutos".
3. **Construí:**
   - `dados.carregar_mapa_portas()` — lê `bases/mapa_sku_linha_produto.csv` (sku→linha, papel).
   - `portas.py` — o motor. Estreia = deal mais antigo do cliente; ponte `nome → itens (3 camadas)
     → SKU → mapa → linha`; brinde **e** sem-nome removidos; 1 linha = porta, >1 = "Multiprodutos",
     0 = "Produto desconhecido". Travas: só `Shipped` casa; estreia idade 0 (senão cross-canal →
     desconhecido). `_triangulo_lb` espelha `coortes.lucro_bruto` num subconjunto → "todos"
     reproduz a Cohorts. Duas builders: `tabela_por_safra` (filtro produto) e `tabela_por_linha`
     (filtro data; cada janela usa só as safras maduras para ela; CAC blended do período).
   - `views/portas_entrada.py` — a aba: filtros, duas tabelas (verde por coluna, "—" abaixo do N
     mínimo, vazio = imaturo), ressalva "Lucro Bruto PARCIAL".
   - `painel.py` — item "4. Portas de entrada" 🚪 no menu, depois da Cohorts.
   - `checar_coerencia.py` — **check nº 6**.
4. **Verifiquei:** identidade + partição por script; guarda 7/7; `AppTest` das 6 telas.

## Provas (números)
- **`portas("todos")` = `coortes.lucro_bruto` ao centavo:** máx |dif| = **0,0** nas 64 safras (idades
  e coluna "1ª compra"). Partição dos clientes **intacta**: 0/64 safras perdem gente.
- **`python3 checar_coerencia.py` → 7/7 ✅** (o novo: "Portas 'todos' × Cohorts: dif 0.00000000 ·
  partição quebrada em 0/64 safras").
- **`AppTest`** sobe as **6 telas** (geral, aquisição, coortes, **portas**, auditoria, auditoria_cohort)
  sem exceção.
- **Impacto da regra do "sem nome" (medido):** 6.727 estreias (Shipped, idade 0) têm porta+sem-nome
  no mesmo pedido = **2,47%** dos 272.063 clientes classificáveis. Com a regra do João, vão para a
  porta conhecida (não para Multiprodutos). Não é <1% como chutei — foi bom decidir explicitamente.
- **Sanidade das portas:** Camiseta Minimal 193.616 clientes; Calça Jeans 1.0 5.940; Multiprodutos
  30.632; Produto desconhecido 21.713. Na tabela por linha (2025): Camisa Social Tech Classics é a
  porta forte (1ª compra R$ 316 → 365D R$ 440, CAC R$ 168); Camiseta Fitness a fraca (137 → 244).

## Decisões que viram régua
- **"Sem nome" é ruído** (removido como brinde) — ADR `2026-07-15-portas-de-entrada-produto` §2.1.
- **Estreia = deal mais antigo do cliente** (robusto, garante partição), com trava idade-0 e
  Shipped-only. **Célula = Lucro Bruto/cliente** (reusa coortes), **CAC blended**.

## Entregáveis
- `portas.py` (novo), `views/portas_entrada.py` (novo), `dados.carregar_mapa_portas` (novo),
  `painel.py` (+1 item), `checar_coerencia.py` (+check nº 6).
- `docs/decisions/2026-07-15-portas-de-entrada-produto.md` (ADR).
- `ARCHITECTURE.md` (cabeçalho + 2 módulos + tabela de decisões), este log, `docs/BACKLOG.md`.

## Ajuste pós-revisão ao vivo (mesma sessão)
- João abriu a aba e viu a **tabela por linha** com várias portas em branco. Causa: o **N mínimo
  300** — linhas abaixo apareciam vazias (parecia quebrado). Decisão do João: **tirar essas portas
  da tabela**. Ajuste: (1) `_pool` devolve o `n` elegível por célula → a UI mostra **"—"** (janela
  suprimida) vs **""** (sem safra madura); (2) porta que **não passa do mínimo em nenhuma janela
  sai da tabela** (as parciais, com ≥1 coluna cheia, ficam com "—" nas janelas longas imaturas).
  Só a **tabela por linha** mudou; a **por safra** e o **check nº 6** ficaram intactos. AppTest OK.

## Aberto / próximos passos
- **João roda ao vivo** (`python3 -m streamlit run painel.py`) e testa a aba 4 (filtro de produto,
  filtro de data, N mínimo). **Reiniciar o painel** — módulos novos, watchdog não instalado.
- Resíduos no BACKLOG: 134 SKUs sem nome (recuperaria parte do "desconhecido"), subdivisão de
  "Camiseta Minimal" (74,6%), balde "Outros Produtos"; e as levas bloqueadas por dado (canal, oferta).
- Régua ainda **Lucro Bruto PARCIAL** (sem devolução por produto — o custo que mais difere entre portas).

## Continuação (2026-07-16) — switch, sort e a "queda" da tabela por linha
Mesma trilha de trabalho, no dia seguinte. Três pedidos do João ao usar a aba:

1. **Switch de leitura (×) — pedido do João, decisão dele.** Um seletor "Leitura das células"
   (só na aba 4, vale para as duas tabelas): **Valor total (R$)** × **Aumento vs 1ª compra (×)**.
   No modo múltiplo cada célula = Lucro Bruto acumulado **÷ o da 1ª compra da própria linha**
   (base 1,00×); 1,58× = o cliente já devolveu 58% a mais que na entrada. É **só uma lente de
   display** — não recalcula custo/CAC; o guarda (check nº 6) fica intacto. Onde a 1ª compra ≤ 0
   (raro) o × vira "—" (não dá para medir aumento sobre prejuízo). `AppTest` OK nos dois modos.

2. **Ordenar a tabela por linha por Clientes (maior → menor)** — `tabela_por_linha` agora ordena
   por nº de clientes do período; "Multiprodutos" e "Produto desconhecido" ficam **fixos no fim**
   (são baldes, não portas comparáveis).

3. **Dúvida do João: "como a Calça Jeans 2.0 cai de 30D (R$ 148,78) para 60D (R$ 146,16)?"**
   Investiguei com os números reais: **efeito de composição**, não queda de valor. O 30D usa 483
   clientes (safras até 2026-06); o 60D usa 402 (a safra **2026-06 sai** — não tem 2 meses de
   vida). Essa turma de junho teve 1ª compra **forte (R$ 244/cliente)**; sem ela, a **média** do
   60D fica menor. Ninguém gastou menos — mudou **quem é contado**. **Decisão do João: Opção 1**
   (manter o máximo de dado + explicar), com **texto claro na tela**: aviso azul "leia por COLUNA,
   não por linha" + exemplo dobrável. (A Opção 2 — travar a turma, curva sempre-sobe, menos dado —
   foi descartada e virou item de backlog.)

**Dívidas novas no backlog:** (a) **mostrar o N por coluna** na tabela por linha (hoje a queda só
é explicada em texto; o motor já devolve `n_primeira`/`n_0`…); (b) **Opção 2** como possível 2º
switch de leitura. Já cobertos (não duplicados): auditor da aba 4, LTV por porta, categoria
única/Multiprodutos, canal/oferta, régua parcial.

**Verificação:** `checar_coerencia.py` segue **7/7** (o sort/switch não tocam o motor de dinheiro);
`AppTest` sobe as telas nos dois modos do switch.

## Nota de método
- O guarda de coerência (`checar_coerencia.py`) fez o seu papel: em vez de "confiar" que o motor
  reusa a Cohorts, o check nº 6 **prova** (dif 0,0 + partição) — a régua não depende de memória.
- A "queda" da tabela por linha foi diagnosticada **rastreando o dado** (quais safras entram em
  cada coluna), não no chute — mantra nº 3. E a saída (Opção 1 + texto) foi **decisão do João**,
  registrada; eu não escolhi por ele um trade-off de leitura.
