# Prompt guardado — Construir a V4 (aba de coortes de recompra)

> Cole o bloco abaixo para abrir a **sessão de construção** da V4. Toda a discovery, a spec e as
> validações já estão feitas (2026-07-10); esta sessão é **implementação**.

---

Retomando o **MC Growth** para **construir a V4 (aba de coortes de recompra)** — **Modo B**, toca
dinheiro/dado, então **seguir a spec à risca** (nada de improvisar regra de cálculo).

**Leia, nesta ordem:**
- `CLAUDE.md` (§0 — estado/próximo passo) e `ARCHITECTURE.md`.
- `PRODUCT.md` (V4) — o domínio.
- **`docs/specs/2026-07-10-v4-coortes-recompra.md`** — a spec (fonte de verdade do build).
- ADRs: `docs/decisions/2026-07-10-v4-arquitetura-mvp-coortes.md` (arquitetura) e
  `2026-07-10-v4-coortes-recompra-hubspot.md` (domínio).
- Log: `docs/sessions/2026-07-10-spec-v4-coortes.md` (spec + validações + decisão do Comercial).

**Pré-condições de dado (já FEITAS — confirme antes de construir):**
- Base HubSpot em `bases/hubspot_deals.csv` (462k deals, validada; gitignored).
- Aba `Midia` estendida (2021-03→2026-12, com `investimento_total` + `fb_investimento`).

**O que construir (spec §5.2 e §8):**
1. `dados.carregar_hubspot()` — lê `bases/hubspot_deals.csv`. Normaliza: **tira o `#` do `nome`**
   (`lstrip('#')`), datas `AAAA-MM-DD`, `e_mail` strip/lower, numérico `valor`/`meses`; descarta
   linhas sem `e_mail`/`data_primeira_compra`. Arquivo ausente/velho → mensagem clara (spec 2.3).
2. **Refactor primeiro:** extrair de `cascata`/`detalhar_pedidos` um helper de **CMV por `order_id`**
   (a MESMA receita de custo: `custos_extra.csv` → 3.1 → 3), com **teste de que a Auditoria segue
   idêntica** — é o que garante uma verdade de custo só.
3. `coortes.py` — `calcular_coortes(...) -> ResultadoCoortes`: safra = mês de `data_primeira_compra`;
   `N_S` = clientes distintos; MC de produto (real via ponte `nome`→`Vendas.order_name`→itens na
   janela; senão `0,25 × valor`); MC incremental/acumulada por cliente (mídia no m+0); CAC, payback,
   recompra 90d por safra; **safra fechada** (só mês encerrado). Marca cada célula **real/estimada**.
4. `pages/3_Coortes.py` — triângulo (`Safra | Clientes | CAC | m+0…`, verde/vermelho + marca
   estimada), curva (últimas 12 safras), seletor de safra → KPIs de cabeçalho, rótulo **"MC parcial"**,
   alertas (arquivo velho / sem mídia).

**Regras que NÃO podem escapar (spec §4 e §0.6):**
- **Comercial (`Negócio Fechado - Comercial`) sempre estimado** — o `nome` é o nome do cliente,
  nunca casa.
- **Mídia:** `Ad Spend = investimento_total`; **só de 2026-01 em diante** somar
  `fb_investimento × 0,1215/0,8785` (imposto só no FB, só a partir de 2026).
- **25% = `0,25 × valor`**, sem deduzir de novo.
- Receita: ramo real usa `net_revenue` (planilha); ramo estimado usa `valor` (HubSpot).
- **V1 (painel) e V2 (aquisição) não mudam** — nenhum número muda.

**Durante o build, rodar as 3 queries de calibração (spec §9 — eu preparo, você roda):**
janela de recompra (dá pra tirar do próprio arquivo); degrau `valor`×`net_revenue` (parcial já
medido, razão 1,011); viés cross-canal (query NOVA, na base **sem** o filtro de estágio).

**Verificação:** `AppTest` sobe sem exceção; a soma da MC **real** da janela **amarra** com a
Auditoria; cumprir os critérios de aceite da spec §7.

**Fechar a sessão** com o ritual (atualizar `ARCHITECTURE.md` + criar log em `docs/sessions/`).
