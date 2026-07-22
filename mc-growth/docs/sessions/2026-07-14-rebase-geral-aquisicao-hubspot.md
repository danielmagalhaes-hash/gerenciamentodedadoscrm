# Sessão — Rebase do painel geral e aquisição no HubSpot

**Data:** 2026-07-14
**Modo:** B (toca dinheiro — a MC dos painéis)
**Gatilho:** João: *"vamos alterar a base de vendas dos painéis geral e aquisição para a base do HubSpot"*.

---

## Decisões do João (2 perguntas)
1. **Escopo:** as duas telas (geral + aquisição).
2. **Janela atual:** **manter idêntica** (abr–jul/2026, onde há itens reais) e **adicionar história estimada**.

→ ADR `docs/decisions/2026-07-14-rebase-geral-aquisicao-hubspot.md`; spec `docs/specs/2026-07-14-...`.

## O que se fez (em linguagem de negócio)
Antes, o painel geral e a aquisição só enxergavam a **janela da planilha** (abr–jul/2026). Agora
enxergam **qualquer mês desde 2021**, porque passam a ler o **HubSpot** para o histórico.

O truque para não bagunçar o que já funciona é um **roteador pela borda da janela**:
- Mês **dentro** da janela de itens → a conta de sempre (aba Vendas, `net_revenue`, CMV real,
  exclusões, carimbo Shopify). **Os números não mudam** — junho continua R$ 2,05M de MC.
- Mês **fora** da janela → vem do HubSpot, com a margem de produto **estimada em 25%** (sem itens
  para o custo real), a mídia daquele mês, e "novo" pela régua da Minimal (cross-canal).
- Período que **cruza** a borda → mistura: real na parte de dentro, estimado na de fora.

Cada resultado leva um **rótulo**: **real** (mês atual), **estimada** (mês histórico, faixa amarela)
ou **mista**. Na cascata, a parte histórica entra como **uma linha "Margem estimada (25%)"** amarela.

## Código
- **`cascata.py`:** `MARGEM_ESTIMADA_FRACAO=0.25`; helpers `_janela_vendas` e `_deals_estimados`
  (deals HubSpot no período E fora da janela). `calcular` e `calcular_aquisicao` ganharam
  `deals=None` e o roteador (real + estimado; mídia contada **uma vez**). Campos novos:
  `rotulo_confianca`, `vendas_estimada`/`vendas_novos_estimada`, `pedidos_estimados`.
- **`painel.py` / `pages/2_Aquisicao.py`:** `carregar_deals` (try/except → None se o CSV faltar);
  passam `deals` ao cálculo; faixa amarela de rótulo; estilo da linha "estimada". O seletor de
  período já aceitava datas passadas.
- **V4 (coortes) e Auditoria:** inalteradas.

## Verificação (CA da spec)
- **CA1 — janela idêntica:** junho **byte-idêntico** com e sem `deals` (MC 2.053.840,87; MC-novos
  237.351,50; CAC 189,67). ✅
- **CA2 — histórico:** jan/2025 renderiza estimado (Vendas Σvalor 3,57M; MC = 0,25×venda − mídia;
  rótulo "estimada"; linha "Margem estimada"). ✅
- **CA3 — misto:** abr/2026 = real (23–30) + estimado (1–22), rótulo "mista", **mídia contada uma
  vez** (R$ 1.164.218 = mídia de abril inteiro). ✅
- **CA4 — CSV ausente:** `deals=None` → comportamento de hoje, sem exceção. ✅
- **CA5:** as 4 páginas sobem no `AppTest`; Coortes e Auditoria inalteradas. ✅

## Por que a janela fica idêntica (a sacada)
A borda é por **data**, não por casamento: **dentro** de [vmin, vmax] o HubSpot é **ignorado** (a
planilha manda), então nem o Comercial (+1,2%) nem o `valor` (vs `net_revenue`) nem o `tipo_de_venda`
entram na janela atual — só valem no histórico. Por isso o número que o João valida todo dia não se move.

## Limites declarados (na tela)
- História é **MC parcial (25%)** — tendência, não fechamento.
- "Novo" no histórico é cross-canal (HubSpot), não o carimbo Shopify — a aquisição histórica não é
  comparável 1:1 com a janela atual (rotulado).
- Exclusões AnjosFrach/pontuais e deduções abertas não valem na parte estimada.

## Ajuste 2 — "novo" da aquisição passa a ser o `tipo_de_venda` do HubSpot (mesma sessão)

O João notou que, filtrando a base direto (`tipo_de_venda = "Primeira Compra"`, Σ`valor`, por mês),
a venda de novos diverge da aba (jun: base 4,36M × aba 3,90M). Causa: **régua diferente** — a aba
usava o carimbo Shopify (`customer_type`, 1ª compra no Shopify); a base usa `tipo_de_venda` (1ª compra
na **Minimal**, cross-canal). Os 692 clientes de diferença em junho são cross-canal/guest-checkout.

**Decisão do João:** trocar a régua da aba para o **`tipo_de_venda` do HubSpot** (unifica com a
coorte e bate com a base). Só a **aquisição** muda; o **painel geral** (soma tudo) fica intocado.

- `calcular_aquisicao` partição agora vem do `tipo_de_venda` (ponte `order_name→nome`); pedido sem
  deal casado cai no `customer_type` (fallback). **Sem `deals` → volta ao carimbo Shopify** (degrada).
- Junho Vendas-novos: **3,90M → 4,24M**. Resíduo vs base (~2,7%) = **net_revenue vs valor (1,4%)** +
  **borda de data** (processed_at vs data_de_fechamento; 80 deals, 1,4%). Ambos estruturais — mantidos
  de propósito (a aba usa `net_revenue`, subconjunto do painel; e a data de processamento do Shopify).
  A divergência **grande** (a régua, ~12%) foi fechada; o resíduo é o net/valor + data.
- Verificado: 4 páginas no `AppTest`; painel geral junho **byte-idêntico**; degradação sem CSV OK.

## Ajuste 3 — unificação total no `valor` (deals-based)

O João viu que a aba ainda divergia da base (~2,7%) e decidiu **unificar tudo no HubSpot**. Medido:
`valor` é **sempre ≥ `net`** (2/3 idênticos; 1/3 +R$19; +1,1% agregado) — a diferença é **frete**
(entra no `valor`, não na coluna `net_revenue`). O João aceita (frete é receita legítima) e a
**condição** dele foi "se der pra pegar o custo por item, unifica" — **dá** (CMV real via ponte
independe de valor/net).

**`calcular` e `calcular_aquisicao` viraram deals-based** (`_cascata_de_deals`): universo = deals por
`data_de_fechamento`; **Vendas = Σ`valor`**; parte casada (janela de itens) com **CMV real** +
deduções; parte não-casada (Comercial + histórico) **25%**. Fallback ao motor antigo se `deals=None`.

**Verificado:**
- Aquisição-novos **bate com a base ao centavo**: abr 3.134.272, mai 4.148.119, jun 4.361.5xx (dif
  R$24 = 1 pedido excluído). ✅
- Painel geral junho Vendas **8.306.581** ≈ base 8.306.605; **CMV real preservado** (~2,39M item a item). ✅
- **MC junho 2,05M → 2,15M (+4,8%)** — `valor` (frete) + inclusão do **Comercial**. Mudança honesta,
  esperada da troca de receita.
- Fallback `deals=None` → net antigo; 4 páginas no `AppTest`. ✅

**Pontos decididos (João, 2026-07-14):**
- **Comercial fica** no painel geral (mantém — bate com a base). *(Título "(Shopify)" a revisar depois.)*
- **Coorte alinhada ao `valor`:** `coortes._mc_produto_por_deal` passou a usar `valor` (não `net`) na
  parte real — receita = `valor` em ambos os ramos; o que muda é só o custo (CMV real × 25%).
  Reconciliação auditoria↔triângulo segue nas 64 safras; safra 2026-06 MC/cliente 62,55 → **67,98**.
  Agora as **três telas** usam a mesma régua (valor + fechamento + CMV real na janela).

## Próximo passo
- João testa ao vivo escolhendo meses passados (faixa amarela) no painel/aquisição.
- Quando a **Opção 1** (itens reais do BigQuery ano-a-ano) entrar, a história deixa de ser estimada e
  o roteador some — este rebase é a ponte até lá.
