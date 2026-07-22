# Spec — Re-base do painel geral e aquisição no HubSpot

> Modo B (toca dinheiro). Decisão: ADR `2026-07-14-rebase-geral-aquisicao-hubspot.md`.
> Fonte de domínio: PRODUCT.md (V4), spec V4 (`2026-07-10-v4-coortes-recompra`).

## 1. Objetivo
Painel geral (V1) e aquisição (V2) passam a mostrar **qualquer mês** (2021→hoje), lendo a base
HubSpot para o histórico, **sem mudar os números da janela atual** (abr–jul/2026), que seguem 100%
da planilha (real). Roteador pela **borda da janela de Vendas**.

## 2. Regras (R = do ADR)
- **R1. Motor real (dentro da janela `[vmin,vmax]`):** `calcular`/`calcular_aquisicao` de hoje,
  inalterados. Números idênticos.
- **R2. Motor estimado (fora da janela):** por mês, sobre os deals HubSpot (Shipped + Comercial) com
  `data_de_fechamento` no período **e fora** de `[vmin,vmax]`:
  - Vendas = Σ `valor`; Pedidos = nº de deals; Margem de produto = **0,25 × Vendas**;
  - Mídia do período (aba Midia; imposto FB só ≥2026-01); MC = Margem de produto − Mídia;
  - Novos (aquisição) = deals com `tipo_de_venda == "Primeira Compra"`; MC-novos = 0,25×Vendas-novos − mídia inteira.
- **R3. Roteador:** resultado do período = **real (parte ∩ janela)** + **estimado (parte fora)**.
  Mídia contada **uma vez** para o período inteiro (não somar nos dois motores).
- **R4. Rótulo:** `real` (período ⊆ janela), `estimada` (período ∩ janela = ∅), `mista` (cruza a borda).
- **R5. Degradação:** `hubspot_deals.csv` ausente → só o motor real (comportamento de hoje). Não quebra.
- **R6. Cascata na tela:** a parte real abre as linhas (deduções/CMV); a parte estimada entra como
  **uma linha** "Margem estimada (25%)". Igual à filosofia da auditoria da coorte.

## 3. Onde mexe
- **`cascata.py`:** `calcular_historico(deals, inicio, fim, midia, ...)` (motor estimado, sem itens);
  `calcular`/`calcular_aquisicao` ganham `deals=None` e o roteador (real+estimado). Sem `deals` →
  idêntico a hoje.
- **`painel.py` / `pages/2_Aquisicao.py`:** `carregar_hubspot` (try/except → None se faltar); passam
  `deals` ao `calcular`; seletor de período aceita meses passados; mostram o rótulo.
- **V4 (coortes) e Auditoria:** inalteradas.

## 4. Critérios de aceite
- [ ] CA1. **Junho/2026 (⊆ janela): painel geral e aquisição byte-idênticos** aos de hoje
  (MC R$ 2,05M; MC-novos etc.). Sem `deals` OU com `deals`, o resultado da janela é o mesmo.
- [ ] CA2. Um mês **histórico** (ex.: jan/2025) renderiza: Vendas = Σvalor, MC = 0,25×Vendas − mídia,
  rótulo **estimada**, uma linha "Margem estimada (25%)".
- [ ] CA3. Um período que **cruza a borda** (ex.: abr/2026 inteiro) = real (abr23–30) + estimado
  (abr1–22), rótulo **mista**; a mídia entra uma vez.
- [ ] CA4. `hubspot_deals.csv` ausente → as duas telas funcionam como hoje (janela real), sem exceção.
- [ ] CA5. Coortes e Auditoria **inalteradas**. As 4 páginas sobem no `AppTest`.
- [ ] CA6. Nada é escrito (só leitura).

## 5. Riscos
- Duplo-contar mídia no período misto → mídia é do período inteiro, subtraída uma vez (teste CA3).
- Deals sem `valor` (1 linha) → 0. Deals fora do casamento dentro da janela **não** entram no estimado
  (a borda é por data, não por casamento) — garante CA1.
