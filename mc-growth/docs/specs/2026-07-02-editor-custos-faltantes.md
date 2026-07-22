# Spec — Editor de custos faltantes no painel (v1.1)

> Descreve o COMPORTAMENTO antes de implementar. Fonte de domínio: `PRODUCT.md`.
> Contexto: o João **não edita a base** (a aba `Custos` da planilha compartilhada), então
> as correções de custo precisam morar num arquivo local que o painel controla.

---

## 1. Resumo

Uma seção nova no painel onde o João **digita o custo dos SKUs que aparecem sem custo**
e salva. As correções vão para um **arquivo local** (`custos_extra.csv`, na pasta do
projeto), e o painel passa a usá-las **por cima da base** (a aba `Custos`). O painel
continua **sem escrever na planilha compartilhada** — só no arquivo local do João.

---

## 2. Comportamento

1. Quando o período tem SKUs vendidos sem custo, aparece a seção "🏷️ Corrigir custos faltantes".
2. Lista os SKUs faltantes (com nº de unidades no período) e um campo de custo editável por linha.
3. Campos já corrigidos antes aparecem preenchidos (lê o `custos_extra.csv` atual).
4. O João preenche o(s) que souber e clica **💾 Salvar custos**.
5. O painel grava o arquivo local, relê os dados e **recalcula** — o SKU sai do alerta e o CMV passa a considerar o custo.

### Regras
- **R1.** A correção é por **SKU** (vale para todo período, não só o exibido).
- **R2.** Custo preenchido **vence** a base: se o SKU existe na aba `Custos` (mesmo em branco), o valor local substitui; se não existe, é adicionado.
- **R3.** Só linhas com custo preenchido são salvas. Custo **0 é válido** (ex.: sacola) e é salvo como 0; linha deixada em branco não é salva.
- **R4.** SKU **em branco** (sem código) não é editável (não há chave para custear); segue só no alerta.
- **R5.** O painel **nunca escreve na planilha compartilhada** — só em `custos_extra.csv` (local).

---

## 3. Dados

- **Novo arquivo local:** `custos_extra.csv` — colunas `sku,valor_custo`. Criado só quando o João salva.
- **Leitura:** `dados.carregar_custos()` aplica o override local sobre a base.
- **Escrita:** `dados.salvar_custos_extra(dict)` (chamada pelo painel).

---

## 4. UI

- Seção nova (expander) na barra de alertas do painel.
- Tabela editável (`st.data_editor`) com colunas SKU (travada), unidades (travada), custo (editável, numérica).
- Botão "💾 Salvar custos".

---

## 5. Critérios de aceite

- [ ] CA1. Com um SKU sem custo, a seção aparece e lista esse SKU.
- [ ] CA2. Digitar o custo, salvar e o SKU some do alerta; o CMV sobe pelo valor × unidades.
- [ ] CA3. A correção persiste ao fechar e reabrir o painel (está no arquivo).
- [ ] CA4. Custo 0 é aceito e salvo (sacola).
- [ ] CA5. A planilha compartilhada não é alterada (só o arquivo local).

---

## 6. Riscos

- Escrita em arquivo local: reversível (apagar `custos_extra.csv` volta ao estado só-base).
- Decisão registrada em ADR `2026-07-02-editor-custos-arquivo-local`.
