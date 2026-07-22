# Sessão 2026-07-02 — correcao-cmv-outros-canais

> Log da sessão. Não é resumo de commit — é o "porquê" e o "o que vem depois".

---

## Objetivo da sessão

Atacar a prioridade 1: entender e resolver os 877 pedidos "órfãos" (com custo, sem venda casada) que subestimavam a MC.

---

## O que foi feito

- Diagnóstico que separou os 877 órfãos de junho: **137** existiam na `Vendas` em outro mês (borda de data) e **740** não existiam em `Vendas` nenhuma.
- **João esclareceu o domínio:** a aba `Itens` traz pedidos de **outros canais** (B2B, TikTok, Mercado Livre, Assinatura); a `Vendas` é a **fonte de verdade** dos pedidos.
- **Correção aplicada em `cascata.py`:** CMV agora conta só itens de pedidos cujo `order_id` está na `Vendas` do período (período do pedido = data de pagamento da `Vendas`).
- Medido o impacto (junho/2026): CMV R$2,76M → **R$2,61M**; MC R$1,83M → **R$1,99M** (+R$156,6k); 0 órfãos.
- Verificado: painel roda sem exceção (`AppTest`); período vazio não quebra; aritmética fecha.
- Criado ADR e atualizados PRODUCT.md, spec, ARCHITECTURE.md.

---

## Decisões tomadas

### CMV conta só pedidos presentes na aba Vendas
- **Decisão:** a `Vendas` é a fonte de verdade dos pedidos; CMV filtra `Itens` pelos `order_id` da `Vendas` do período.
- **Por quê:** a `Itens` mistura outros canais; a v1 é só Shopify; custo sem receita quebra a MC.
- **Descartado:** filtrar `Itens` pela própria data (incluía outros canais); usar `Itens` como fonte única de vendas (contraria a regra do João).
- **ADR criado?** sim — `docs/decisions/2026-07-02-cmv-so-pedidos-da-aba-vendas.md`.

---

## Problemas encontrados

### Leitura da planilha travou com erro confuso (soluço do Google)
- **Descrição:** uma das 4 leituras seguidas retornou algo que não era CSV; o código quebrou com "A aba Vendas está sem a coluna order_id" em vez de uma mensagem clara. Funcionou na 2ª tentativa.
- **Causa raiz:** `_ler_csv` não valida se a resposta é mesmo CSV; se o Google devolve HTML (rate limit/soluço), o pandas gera um erro enganoso.
- **Solução aplicada:** `_ler_csv` blindado — confere `content-type` (só `text/csv`) e tenta 3× com espera crescente (1,5s, 3s); se falhar, mensagem clara via `ErroDeDados`. Testado: leitura normal OK; link errado dá a mensagem clara (não a confusa).
- **Status:** RESOLVIDO (2026-07-02).

---

## Estado do projeto agora

### Funcionando
- Painel v1 com a MC correta para Shopify (junho: R$1,99M). Os três módulos passam nos testes.

### Quebrado / incompleto
- Carregador não trata resposta não-CSV do Google (erro confuso em soluço de rede) — a blindar.
- 136 pedidos/mês em Vendas sem Itens seguem sem CMV (resíduo aceito, ~0,78%).

---

## Próximo passo

1. **João valida a MC** com o número corrigido (R$1,99M em junho) e cadastra os 16 SKUs sem custo na aba `Custos`.
2. **Blindar o carregador** (`dados.py`): detectar resposta não-CSV e tentar de novo, com mensagem clara. Independe do João.
3. Depois: aba `Parametros` (João cria → eu ligo) e escolher a 1ª feature da "prioridade 3" (comparação com período anterior é a mais votada até agora).

---

## Adendo — exclusão das camisetas AnjosFrach

- **Contexto:** 13 dos 16 SKUs sem custo eram a linha `CamiseAnjosFrach01..13`. O João classificou como fora do escopo da MC.
- **Decisões (via pergunta direta):** remover o **pedido inteiro** (não só a linha) e valer **sempre no painel**.
- **Implementado em `cascata.py`:** constante `PREFIXOS_SKU_EXCLUIDOS`, função `_pedidos_excluidos`, filtro em `calcular`; `painel.py` mostra a contagem de excluídos. Novo campo `Resultado.pedidos_excluidos`.
- **Impacto junho/2026:** 22 pedidos removidos; Vendas R$8,10M → R$8,08M; MC R$1,99M → **R$1,976M**; SKUs sem custo 16 → **3** (sobram `1301002112`, `(em branco)`, `sacolaM`). 0 itens AnjosFrach no cálculo; aritmética fecha; painel roda sem exceção.
- **ADR:** `docs/decisions/2026-07-02-excluir-anjosfrach.md`. Spec ganhou R13.
- **Reversível:** esvaziar `PREFIXOS_SKU_EXCLUIDOS`.

## Adendo — SKUs sem custo resolvidos + exclusão do #501777

- **Perfume 10ML (`1301002112`, 145 un):** identificado pelo João; custo R$11,83. **Já existe na aba `Custos` com célula VAZIA** (linha 528) — o João preenche a célula (não criar linha nova, para não contar em dobro). Simulado: CMV +R$1.715,35, SKUs sem custo 3→2.
- **`sacolaM`:** João definiu custo 0 por enquanto (já é 0 no cálculo por R11; opcional pôr 0 na planilha só para sumir o aviso).
- **Pedido `#501777`:** receita R$0, 1 item com SKU em branco (qtd 8) — reposição/cortesia. Investigado: ~248 pedidos R$0 no histórico. João decidiu **não** fazer regra geral de R$0, só excluir esse pedido. Implementado via `PEDIDOS_EXCLUIDOS_NOME`. Impacto junho: Pedidos 14024→14023; unidades sem custo 160→152; pedidos_excluidos 22→23.
- Painel roda sem exceção; aritmética fecha. ADR atualizado (seção 8) e spec R13 ampliado.

---

## Adendo — João não edita a base → editor de custos no painel (v1.1)

- **Fato novo:** o João **não consegue editar a base** (planilha compartilhada). Isso derruba a premissa de que ele mantém as abas `Custos`/`Parametros`.
- **Decisão (via pergunta direta):** editor de custos **no próprio painel**, gravando num arquivo local (`custos_extra.csv`), aplicado por cima da base. O painel segue **sem escrever na planilha**.
- **Implementado:**
  - `dados.py`: `ler_custos_extra`, `salvar_custos_extra`, `_aplicar_custos_extra`, aplicado em `carregar_custos`; `CAMINHO_CUSTOS_EXTRA`.
  - `cascata.py`: `Resultado.skus_faltantes` (lista sku→unidades; SKU em branco fica de fora).
  - `painel.py`: seção "🏷️ Corrigir custos faltantes" (`st.data_editor` + Salvar → grava, limpa cache, recalcula).
  - `.gitignore`: ignora `custos_extra.csv`.
- **Testado:** salvar `{1301002112: 11,83, sacolaM: 0}` → faltantes 2→0, CMV +R$1.715,35, arquivo lido de volta OK; painel renderiza o editor sem exceção (expander "2 SKU" + botão Salvar).
- **Docs:** spec `2026-07-02-editor-custos-faltantes.md`, ADR `2026-07-02-editor-custos-arquivo-local.md`, ARCHITECTURE (invariante "só lê" precisado, decisões, inventário).
- **Nota:** o invariante "o painel só lê, nunca escreve" agora vale **só para a planilha compartilhada** — o arquivo local é exceção deliberada.

---

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** ponto frágil nº 1 → RESOLVIDO com números; nova linha na tabela de decisões; nota nos invariantes da aba `Itens` (outros canais).
- **`CLAUDE.md`:** seção 0 atualizada (próximo passo: validar MC corrigida + blindar carregador).
- **`docs/decisions/`:** criado `2026-07-02-cmv-so-pedidos-da-aba-vendas.md`.
- **`docs/specs/`:** R5 do spec atualizado com a regra da fonte de verdade.
- **`PRODUCT.md`:** glossário CMV, tabela da cascata e restrições atualizados.
