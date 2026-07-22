# Spec — Auditoria de custos por pedido (v1.2)

> Página anexa ao painel para o João validar, por pedido, se a estimativa de custo (CMV) faz sentido.
> Contexto e design: sessões 2026-07-03/04. Fonte de domínio: `PRODUCT.md`.

---

## 1. Resumo

Uma **segunda página** (multipage Streamlit) chamada "Auditoria de custos". Lista os pedidos
do período com `data · pedido · nº itens · valor · custo · custo %`, sinaliza os suspeitos
(sem custo / margem fora da faixa), permite **abrir um pedido** para ver item a item
(SKU · descrição · qtd · custo unit · custo linha) e **exportar** a tabela. Usa exatamente
o mesmo recorte de pedidos do painel (mesmas exclusões, mesma fonte Vendas), então os
totais batem com a MC.

---

## 2. Comportamento

1. Abre em página própria (nav lateral do Streamlit). Período padrão: este mês.
2. Topo: resumo (nº de pedidos, nº suspeitos, CMV total).
3. Filtro: "só suspeitos".
4. Tabela por pedido, ordenável (por custo %, valor, etc.).
5. Selecionar um pedido → abre o detalhe item a item abaixo.
6. Botão exportar CSV.

### Regras
- **R1.** Mesmo recorte do painel: exclusões (AnjosFrach, #501777) e fonte Vendas (só Shopify). O CMV somado aqui = CMV do painel.
- **R2.** `custo %` = custo ÷ valor (× 100). Vazio se valor 0.
- **R3.** Suspeito = tem item sem custo **ou** custo % fora da faixa `[FAIXA_MIN, FAIXA_MAX]` (heurística, ajustável).
- **R4.** Descrição do SKU vem da base silver (`item_desmembrado_nome`), só como dicionário; se faltar, mostra o código.
- **R5.** `id do pedido` = número humano (`order_name`), pesquisável no Shopify.
- **R6.** Custos já incluem as correções locais do João (`custos_extra.csv`).

---

## 3. Dados

- **Reusa:** `dados.carregar_tudo()` + `cascata` (novo `detalhar_pedidos`, que compartilha o recorte com `calcular`).
- **Novo:** `dados.carregar_descricoes()` — sku→nome da base silver (gid 1466784982). Opcional: se falhar, dicionário vazio (mostra código).

---

## 4. UI

- Página `pages/1_Auditoria_de_custos.py`.
- Tabela: `st.dataframe` com seleção de 1 linha; detalhe do pedido selecionado numa tabela abaixo.
- `st.download_button` para CSV.

---

## 5. Critérios de aceite

- [ ] CA1. A soma da coluna `custo` da auditoria = CMV do painel no mesmo período.
- [ ] CA2. Pedido com item sem custo aparece marcado como suspeito.
- [ ] CA3. Abrir um pedido mostra os itens com custo unitário e descrição.
- [ ] CA4. Filtro "só suspeitos" reduz a lista aos marcados.
- [ ] CA5. Exportar gera CSV com as colunas da tabela.

---

## 6. Riscos

- Base silver grande → latência; mitigado por cache e por ser só na página de auditoria.
- Faixa de suspeita é heurística — começa larga; ajustável na constante.
