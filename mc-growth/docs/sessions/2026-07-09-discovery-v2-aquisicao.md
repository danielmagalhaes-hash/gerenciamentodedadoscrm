# Sessão 2026-07-09 (tarde) — Discovery + handoff do PRODUCT.md para a V2 (aquisição)

> Log da sessão. Modo A (análise/estratégia — o produto da sessão é o `PRODUCT.md` da V2).

---

## Objetivo da sessão

Rodar o **discovery da V2** e fazer o **handoff do `PRODUCT.md`** (V1 → V2), preparando o
terreno para a spec da V2. João pediu explicitamente para seguir o `prompts/00-discovery.md`
(entrevista profunda, uma pergunta por vez) depois de achar o diagnóstico inicial raso.

---

## O que foi feito

- **Investigação de dado ao vivo (antes de qualquer documento):** confirmei que **não há e-mail
  em nenhuma aba**. Mas a aba `Vendas` ganhou (o João adicionou) a coluna **`customer_type`** —
  campo nativo da Shopify, valores `Primeira Compra` (19.513) / `Recompra` (17.996) / vazio (84).
  Cobertura 99,78%.
- **Entrevista de discovery focada**, as 8 áreas do prompt, uma pergunta por vez. Decisões
  travadas (detalhe no ADR `2026-07-09-v2-aquisicao-customer-type-shopify` e no `PRODUCT.md`):
  1. **Cliente novo = novo no canal Shopify** (convenção ajustável).
  2. **Chave = `customer_type` nativo da Shopify**, não e-mail construído. Point-in-time +
     histórico completo → **borda esquerda resolvida**. Automático no fluxo (robusto).
  3. **Visão:** aba de **decisão de aquisição** — "a aquisição gera MC positiva na 1ª compra?".
     Régua conservadora; LTV é V4.
  4. **Vocabulário:** Margem de Contribuição, nunca "lucro" (sinônimo proibido).
  5. **Convenção 100% mídia → novos** (ajustável; V4 refina). CAC/aROAS "blended".
  6. **5 KPIs:** MC-novos, Vendas-novos, Pedidos-novos, CAC (R$/cliente novo), aROAS (múltiplo).
  7. **Faixa:** só a **linha do zero** na MC-novos (verde/vermelho). Régua calibrada = V5.
  8. **Escopo:** aba dedicada **só de aquisição**, ao lado do painel V1 (que não muda). A coluna
     de recompra virou candidata a versão seguinte.
  9. **Bordas:** "—" + nota quando a divisão é indefinida (0 novos / 0 mídia).
  10. **Sem entidade nova, sem dado pessoal** (LGPD só na V4).
- **Handoff executado:** V1 arquivado em `docs/product-history/PRODUCT-v1.md`; `PRODUCT.md`
  reescrito para a V2 (8 seções, marcando [HERDADO] × [NOVO]); `ROADMAP.md` (entrada V2)
  atualizado; ADR criado.

---

## Decisões tomadas

Ver ADR `docs/decisions/2026-07-09-v2-aquisicao-customer-type-shopify.md` (5 decisões +
alternativas descartadas). Resumo: **V2 = aba de aquisição carimbada pelo campo nativo da
Shopify; régua "MC positiva na 1ª compra"; 100% mídia → novos por convenção; recompra adiada.**

---

## Problemas encontrados

### E-mail não existe na base — contornado
- **Descrição:** as abas `Vendas`/`Itens` não têm coluna de e-mail; a abordagem original do
  ROADMAP (construir chave por e-mail) não teria dado a montante.
- **Solução:** o campo nativo `customer_type` da Shopify entrega o carimbo novo/recompra sem
  precisar de e-mail — e ainda resolve o viés de borda esquerda. O e-mail volta a ser necessário
  só na V4 (coorte/LTV).

---

## Estado do projeto agora

### Funcionando
- `PRODUCT.md` agora descreve a V2; V1 preservado no histórico. Painel V1 roda normal (inalterado).

### Quebrado / incompleto
- Nada quebrado. A V2 ainda é **só documento** — nenhum código escrito. A aba de aquisição não
  existe no `painel.py` ainda.
- Pendência de manutenção herdada: o trabalho de custo 3.1 (de manhã) segue **não commitado** no
  working tree, junto com estes documentos da V2.

---

## Próximo passo

1. João vai revisar o projeto com o "advisor". Aguardar retorno antes de escrever a spec.
2. **Escrever a spec da V2** (`docs/specs/2026-07-09-...`) a partir deste PRODUCT.md — Modo B:
   como a aba de aquisição lê `customer_type`, parte a cascata, calcula os 5 KPIs, e a UI.
3. Commitar: o trabalho de custo 3.1 (manhã) + estes documentos da V2 (tarde).

---

## Atualizações em outros documentos

- **`PRODUCT.md`:** reescrito para a V2 (V1 arquivado em `docs/product-history/PRODUCT-v1.md`).
- **`docs/ROADMAP.md`:** entrada da V2 refinada para "só aquisição".
- **`docs/decisions/`:** criado `2026-07-09-v2-aquisicao-customer-type-shopify.md`.
- **`CLAUDE.md`:** seção 0 — estado avançado para "V2 em spec".
- **`ARCHITECTURE.md`:** §6 (dobra de kit → RESOLVIDA) e a linha da aba Itens; a coluna
  `customer_type` entra no mapa gid→aba quando a spec/implementação começar.

---

## Continuação da sessão (tarde) — advisor, kit e commits

- **Avaliação de advisor (Fable):** rodei um agente advisor sênior que leu V1, V2, ROADMAP e
  ADRs e devolveu um relatório crítico (veredito, ataque às 4 escolhas da V2, leitura da
  sequência do roadmap, 3 movimentos, a "pergunta desconfortável"). **Decisão do João: arquivar
  e NÃO incorporar** ao rumo. Salvo em `docs/reviews/2026-07-09-advisor-fable-v1-v2-roadmap.md`
  (com cabeçalho deixando claro que não foi incorporado).
- **Dobra de kit — RESOLVIDA:** o João informou que a explosão de kit foi **corrigida na fonte**
  e já está live na planilha. Aposentei o paliativo `SKUS_KIT_VIRTUAL` do `cascata.py` (com a
  fonte corrigida, mantê-lo passaria a subtrair custo legítimo → MC inflada). Teste de ponta a
  ponta: MC de junho **inalterada** (R$2,055M) — a remoção foi no-op. Docs vivos sincronizados
  (CLAUDE.md §0, ARCHITECTURE.md §6, PRODUCT.md, ROADMAP.md) marcando o kit como resolvido.
- **Commits (nesta sessão):** `a3c6514` (remoção do paliativo de kit) e `86f49d8` (handoff da
  V2 + sync dos docs). O trabalho de custo da manhã já estava salvo em `5413c48`.
- **`.gitignore`:** adicionados os materiais de estudo pessoais (prints do Obsidian,
  `Curso Pedrinho.md`, `Auditoria de custos.md`) — não são do projeto.

### Estado atualizado + próximo passo
A spec da V2 será feita **em uma sessão/aba nova** (o João pediu o prompt de abertura). Modo B:
como a aba lê `customer_type`, parte a cascata, calcula os 5 KPIs e desenha a tela.
