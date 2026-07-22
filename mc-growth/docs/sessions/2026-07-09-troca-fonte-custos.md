# Sessão 2026-07-09 — troca da fonte de custos (aba 3 → aba 3.1)

> Log da sessão. O "porquê" e o "o que vem depois".

---

## Objetivo da sessão

Trocar a base de custo por SKU da aba **"3. Custos"** para a aba **"3.1. Custos"** (custos
mais atualizados, segundo o João). Modo B (toca dinheiro: CMV/MC).

---

## O que foi feito

- Investiguei as duas abas ao vivo antes de tocar código (mantra: rastrear a fonte). A 3.1 é
  melhor no geral (+610 SKUs, menos lixo), **mas achei 137 SKUs que tinham custo real na 3 e
  estão zerados (R$0,00) na 3.1** — em famílias inteiras (padrão de "aba não preenchida").
- Mandei a lista dos 137 ao João. Ele decidiu: nesses zerados, o custo vem da aba 3.
- Escrevi a spec (`docs/specs/2026-07-09-troca-fonte-custos-3-para-3-1.md`) com a regra de
  fallback e o critério de aceite.
- Implementei em `dados.py`: `GIDS["Custos"]`→3.1 (`1460088128`, col `Custo`); novo
  `GID_CUSTOS_FALLBACK`→3 (`423190064`, col `Valor de Custo`); refatorei `carregar_custos`
  para juntar as duas (3.1 se >0, senão 3), mantendo `custos_extra.csv` por cima. Extraí
  `_ler_aba_custo` (reuso das duas leituras). **Contrato de saída inalterado** — `cascata.py`
  e `painel.py` não mudaram.
- Verifiquei: 137/137 zerados recuperados; painel e Auditoria sobem sem exceção (`AppTest`).

---

## Decisões tomadas

### Aba 3.1 como fonte principal, aba 3 como rede de segurança
- **Decisão:** custo por SKU = 3.1 se >0, senão 3 se >0, com correção local vencendo tudo.
  Custo 0 = faltando, não grátis. ADR `2026-07-09-fonte-custos-3-1-com-fallback.md`.
- **Por quê:** ganha cobertura/atualização da 3.1 sem perder os 137 custos reais que ela
  ainda não preencheu.
- **Descartado:** trocar puro (inflaria a MC); não trocar (perderia o ganho por tempo indef.).

---

## Problemas encontrados

### 137 SKUs zerados na 3.1
- **Descrição:** famílias inteiras de produto vieram com custo 0 na 3.1 (ex: R$155, R$80…).
- **Causa raiz:** a 3.1 ainda não foi preenchida para esses SKUs (a montante, time de Dados).
- **Solução aplicada:** rede de segurança da aba 3 (paliativo, como a dobra de kit).
- **Status:** paliativo ativo. Definitivo = time preencher a 3.1 (lista em `docs/skus-custo-zerado-aba-3-1.csv`).

---

## Estado do projeto agora

### Funcionando
- Painel e Auditoria com a fonte nova. CMV/MC de junho recalculados e verificados.
- **Impacto junho/2026:** CMV −R$78.246 (−3,17%); MC R$1.977M → **R$2.055M** (+3,96%).
- SKUs sem custo em junho: 1 → 1 (sem regressão).

### Quebrado / incompleto
- Nada quebrado. Bug herdado (dobra de kit) segue — será tratado na V3.
- Pendente a montante: 137 SKUs a preencher na 3.1 (lista pronta pra encaminhar).

---

## Próximo passo

1. **João:** encaminhar `docs/skus-custo-zerado-aba-3-1.csv` (137 SKUs) ao time de Dados para
   preencher a 3.1. Quando completa, a aba 3 pode ser aposentada.
2. Retomar o rumo do roadmap: **spec da V2** (chave de cliente por e-mail + novo/recompra) —
   antes, confirmar de onde vem o e-mail na base.
3. (Opcional) marcar na Auditoria a origem do custo (3.1 x fallback 3) — fora de escopo hoje.

---

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** mapa gid→aba (3.1 principal + 3 fallback); mapeamento de nomes de
  coluna; tabela da aba Custos com a regra de fonte; nova linha na seção 5 (decisões).
- **`docs/decisions/`:** criado `2026-07-09-fonte-custos-3-1-com-fallback.md`.
- **`docs/specs/`:** criado `2026-07-09-troca-fonte-custos-3-para-3-1.md`.
- **`dados.py`:** `GIDS["Custos"]`, `GID_CUSTOS_FALLBACK`, `_ler_aba_custo`, `carregar_custos`.
- **`CLAUDE.md`:** seção 0 — nota da fonte de custo (3.1 + fallback) e MC de junho atualizada.
