# BACKLOG — MC Growth

> Lista viva de coisas **a resolver** e **a fazer**. Não é spec nem log — é a fila.
> Criado em 2026-07-15 (discovery da feature "portas de entrada"). Atualizar sempre que
> surgir item novo ou algo for concluído (mover para "Feito" com a data).

---

## 🔜 Próxima leva (comprometido, tem dado)

- [x] **Filtro de PRODUTO de entrada** — ✅ **CONSTRUÍDO (2026-07-15)** → aba "4. Portas de
      entrada" (`portas.py` + `views/portas_entrada.py`). Duas tabelas (por safra / por linha),
      colunas `1ª compra | 30D | 60D | 90D | 180D | 365D`, célula = Lucro Bruto/cliente, CAC
      blended. ADR `2026-07-15-portas-de-entrada-produto`; log `2026-07-15-construcao-portas...`.
- [x] **Mapa SKU → linha de produto** — ✅ **VALIDADO pelo João (2026-07-15)** →
      `bases/mapa_sku_linha_produto.csv` (26 linhas-porta, 3 baldes brinde, Produto
      desconhecido). Rascunho gerado por Claude, corrigido à mão pelo João no Sheets.
- [x] **N mínimo por porta** — ✅ **300** (padrão, ajustável na tela; abaixo → "—").
- [x] **Detalhe de build (sem nome × categoria única):** ✅ **RESOLVIDO (2026-07-15, decisão do
      João):** "sem nome" é **ruído** (removido como brinde) → `camiseta + sem-nome = "Camiseta"`.
      Impacto medido: 2,47% das estreias. Flag de 1 linha se um dia inverter. ADR §2.1/§4-A.

- [x] **Auditor da aba 4 ("Portas de entrada")** — ✅ **CONSTRUÍDO (2026-07-16)** → aba
      **"A3 - Auditoria Portas"** (`views/auditoria_portas.py` + `portas.auditar_portas`):
      escolhe a porta → lista os clientes → clica e abre a **linha do tempo de compras** do
      cliente (produtos por compra + m+x). Resuminho por **motivo** do "Produto desconhecido"
      (Comercial / fora da base / sem itens / só ruído). Spec `2026-07-16-auditoria-portas-drilldown`;
      log `2026-07-16-a3-auditoria-portas`. *(A parte agregada — ranking de SKU candidato,
      combos — ficou de fora: ver item novo abaixo.)*

- [x] **LTV (receita) por porta de entrada** — ✅ **CONSTRUÍDO (2026-07-16)** → **seletor de
      métrica** (Lucro Bruto × Receita) na aba 4 troca o conteúdo das duas tabelas. Receita =
      `coortes.ltv` fatiado por porta (provado ao centavo no check nº 6). Log
      `2026-07-16-portas-metrica-receita`.

- [~] **Rankings agregados na A3 (garimpo automático)** — PARCIAL.
      - [x] **Combinações de linha mais comuns em "Multiprodutos"** — ✅ **FEITO (2026-07-16)**:
        tabela de combinações ranqueada + clique abre os clientes (`combo` em `auditar_portas`).
      - [ ] **Ranking dos SKUs frequentes em "Produto desconhecido" que NÃO estão mapeados como
        porta** (candidatos a virar linha no `mapa_sku_linha_produto.csv`). Dado já em
        `AuditoriaPortas` (estreias + itens + sku2papel). Contexto: dos 21.713 desconhecidos,
        11.721 são "sem itens casados" e 6.279 "só brinde/sem-nome" (medido 2026-07-16) — o
        ranking de SKU ataca os 6.279.

- [ ] **Mostrar o nº de clientes POR COLUNA na tabela por linha** (aba 4). Cada janela (30D,
      60D…) usa só as safras maduras para ela → o grupo por trás de cada coluna encolhe conforme
      a janela cresce, e por isso um número pode ficar **menor que o da coluna anterior** (efeito
      de composição, não queda de valor — decisão de 2026-07-15: **Opção 1**, manter o máximo de
      dado + explicar). Hoje isso só é **explicado em texto** (aviso azul + exemplo dobrável); o N
      por coluna não aparece na tabela. Mostrá-lo (tooltip, 2ª linha, ou coluna auxiliar) tornaria
      a queda **auto-evidente** sem depender da prosa. `tabela_por_linha` já devolve o `n` por
      célula (`n_primeira`, `n_0`…) — falta só a UI usá-lo.

## 🧭 Levas seguintes (bloqueadas por DADO — instrumentar a montante primeiro)

- [ ] **CANAL de entrada** (2ª leva). **Não há dado hoje** (`hubspot_deals.csv` tem 8
      colunas, nenhuma de canal). Antes de resolver: **definir o que o João quer dizer**
      por canal — (a) canal de venda/operação (Shopify × Comercial × TikTok × Assinatura)
      ou (b) canal de marketing (Meta/Google/orgânico/indicação, que é o que a True Classic
      mede por survey/incrementalidade). Depois: instrumentar na torneira do BQ / survey
      pós-compra.
- [ ] **OFERTA de entrada** (3ª leva). **Não há dado hoje** (sem cupom/desconto em base
      local). Conceitualmente é o corte mais potente (o Curso Pedrinho: "desconto explode
      o breakeven ROAS"). Instrumentar `discount_code` da Shopify no pipeline — e lembrar
      que oferta site-wide **não deixa carimbo de cupom** (precisa de outra marcação).
      "A instrumentação de hoje decide se a pergunta mais valiosa será respondível ainda
      este ano" (Fable).

## ⚠️ Dívidas de modelagem a questionar

- [ ] **Leitura alternativa "turma travada" (Opção 2, descartada em 2026-07-15).** Na tabela por
      linha, escolhemos a **Opção 1** (cada janela usa o máx. de safras maduras → mais dado, mas a
      linha pode cair de uma coluna para a outra). A **Opção 2** — travar todas as colunas de uma
      porta na **mesma turma** (só as safras maduras até a última janela) — faria a linha **sempre
      subir**, ao custo de menos clientes e menos alcance nas janelas longas. Registrada como
      alternativa considerada; um dia pode virar um **2º switch de leitura** ("mais dado" ×
      "sempre sobe"). Não é bug — é um trade-off de leitura.
- [ ] **Regra provisória "produto de entrada"** (registrar no ADR, questionar depois):
      só pedidos de estreia com **categoria única**; mais de uma categoria → "Multiprodutos";
      **carteira é brinde** (removida antes de avaliar). Revisar quando houver mais dado.
- [ ] **Régua ainda é MC/Lucro Bruto PARCIAL, não fully-loaded.** Falta descontar
      devolução, troca, CX, juros de estoque e criativo (o modelo True Classic exige).
      Crítico: a **taxa de devolução por produto** é justamente o custo que mais difere
      entre portas de entrada — e está fora da conta. Segmentar por entrada **não conserta**
      isso. Alavanca grande, parkeada.
- [ ] **Survey pós-compra** ("onde ouviu falar primeiro?" + "quando?") — pré-requisito do
      modelo para medir canal/incrementalidade de verdade.

## 🧾 Resíduos do mapa de produtos (a montante / futuro)

- [ ] **134 SKUs `SEM NOME`** (2,6% das unidades) — sem nome cadastrado na base de itens.
      Hoje caem em "Produto desconhecido". Cadastrar o nome a montante pra recuperá-los.
- [ ] **"Camiseta Minimal" = 74,6%** num balde só (202 SKUs) — revisitar se merece
      subdivisão (GT, gola V × gola O, colabs) quando for útil pra decisão.
- [ ] **Balde "Outros Produtos"** (276 SKUs, 1,9%) — classificar melhor se virar relevante.

## 🧹 Herdadas (de sessões anteriores)

- [ ] Entregar `docs/skus-custo-zerado-aba-3-1.csv` (137 SKUs) ao time de Dados.
- [ ] Re-base da V2 (aquisição) no HubSpot (prompt guardado em `docs/prompts-guardados/`).
- [ ] Afinar cartão de recompra para **90d + 180d** (calibração V3).
- [ ] Resíduos de CMV: 2021 ainda estimado (base começa out/2021); ~6,4% das unidades de
      2023 sem custo cadastrado (MC otimista ali).

---

## ✅ Feito

- (nada ainda nesta trilha)
