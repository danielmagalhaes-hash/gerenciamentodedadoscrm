# Sessão 2026-07-04 — auditoria-custos-por-pedido

> Log da sessão. Não é resumo de commit — é o "porquê" e o "o que vem depois".

---

## Objetivo da sessão

Construir uma página anexa para o João validar, pedido a pedido, se o custo (CMV) faz sentido.

---

## O que foi feito

- **Design discutido antes de construir:** custo é atributo de SKU, não de pedido; validar por exceção + impacto; o João optou por visão **por pedido** com `data · pedido · itens · valor · custo`, e eu somei `custo %` + drill-down de itens + flag de suspeitos + export.
- **Descrições:** a base silver (`item_desmembrado_nome`) vira dicionário SKU→nome, mas é um snapshot de ~500 linhas/1 dia → cobre só ~141 SKUs. Uso o que tem e caio pro código no resto (`dados.carregar_descricoes`, opcional/resiliente).
- **`cascata.py`:** extraí `_recorte_pedidos` (compartilhado por `calcular` e pela auditoria → totais idênticos) e criei `detalhar_pedidos` (por_pedido + por_item, com flag de suspeito por faixa de custo %).
- **`dados.py`:** `_ler_csv` agora recebe gid; novo `carregar_descricoes` (gid silver); `GID_DESCRICOES`.
- **`pages/1_Auditoria_de_custos.py`:** página multipage com resumo, filtro "só suspeitos", tabela selecionável, detalhe item a item e export CSV (`;`/`,` para Excel BR).
- Trocado `use_container_width` (depreciado) por `width="stretch"`.

---

## Decisões tomadas

### Auditoria por pedido, com custo % e drill-down (não só as 5 colunas cruas)
- **Decisão:** manter as colunas do João + `custo %` (sinal de validação) + abrir itens + flag de suspeitos.
- **Por quê:** 14k pedidos são inauditáveis em lista crua; a triagem por exceção/impacto torna viável.
- **ADR?** não (feature coberta por spec; sem reversão estrutural). Spec `2026-07-04-auditoria-custos-por-pedido.md`.

### Silver só como dicionário de nomes
- **Decisão:** custo continua vindo da aba `Itens` limpa; silver só dá nome (parcial).
- **Por quê:** silver mistura canais e é um snapshot pequeno; usá-la no cálculo divergiria do painel.

---

## Problemas encontrados

### Só 141 descrições (perfume sem nome)
- **Causa:** a base silver é um snapshot de 1 dia (~500 linhas), não um catálogo completo.
- **Solução:** descrição vira opcional; SKU sem nome mostra o código. Transparente na tela ("descrições parciais").
- **Status:** contornado. **Aberto:** achar um catálogo SKU→nome completo (se existir) melhoraria muito.

### Estado de teste esquecido (`custos_extra.csv`)
- **Descrição:** um `custos_extra.csv` de teste (perfume/sacola) ficou no projeto e mascarava os flags "sem custo".
- **Solução:** removido. Estado limpo confirmado: 133 pedidos "sem custo", 726 "custo alto", 19 "custo baixo" em junho.
- **Status:** resolvido.

---

## Estado do projeto agora

### Funcionando
- Painel (página 1) + Auditoria de custos (página 2). CMV da auditoria == CMV do painel (CA1). Ambas rodam sem exceção (AppTest).

### Quebrado / incompleto
- Descrições de produto parciais (~141 SKUs).
- Seleção de linha não testável via AppTest (código simples e guardado; validado o dado do drill-down à parte).

---

## Próximo passo

1. João abrir o painel (`python3 -m streamlit run painel.py`), ir na página **Auditoria de custos**, filtrar "só suspeitos", conferir os "custo alto"/"sem custo" e validar amostras via drill-down.
2. Lançar os custos faltantes que a auditoria revelar (editor da página do painel).
3. Se houver catálogo SKU→nome completo, me apontar para enriquecer as descrições.

---

## Ajustes de acompanhamento (mesmo dia)

- **Base de Itens truncada:** a reextração do João veio cortada em 25.000 linhas (16 dias) — CMV caiu p/ R$1,1M. Diagnosticado com `checar_base.py` (novo). João reextraiu do BigQuery sem o teto → 99.031 linhas, amarração V×I 98,5%, CMV junho de volta a R$2,61M.
- **Coluna "id pedido (chave)":** adicionada na auditoria (número final do order_id) — tabela + export.
- **Bug "##":** a Vendas reextraída trouxe `order_name` inconsistente (uns com "#", outros sem); normalizado em `carregar_vendas` (sem "#"). Deixa a exclusão do #501777 mais robusta também.
- **Busca por pedido:** adicionada caixa "digite o nº do pedido" na auditoria — o João não precisa cruzar com a aba Itens na mão; clica na linha OU busca pelo número e vê os itens.
- **Ferramenta:** `checar_base.py` — sanidade da planilha (rodar após reextrair).

## Achado grande — explosão de kit em dobro (via auditoria)

- O João achou pelo painel o pedido #469395 (kit "Compre 3 leve 4 + Carteira"): 5 itens reais viraram 10 na base. Dois sintomas: (1) **SKU virtual de kit** (`8301001172`) fica junto dos componentes; (2) **componente duplicado** (Carteira `8301007000` em 2 linhas).
- **Escopo:** assinatura em ~5.131 pedidos no histórico (1.824 em junho, ~18% do CMV). Direção: CMV inflado → MC **subestimada**.
- **Causa:** explosão de kit na fonte (BigQuery), não o painel.
- **Decisão do João:** começar pelo paliativo (B) e registrar o conserto de fonte (A) como problema de v2+.
  - **B (feito):** `cascata.SKUS_KIT_VIRTUAL = ("8301001172",)` — removido do CMV no `_recorte_pedidos` (vale painel + auditoria). Conferido seguro (redundante em 45/45 pedidos). Incremental: adicionar SKUs conforme o João confirmar.
  - **A (registrado):** PRODUCT.md 7.2 + ARCHITECTURE 6 — corrigir a explosão no BigQuery (SKU virtual + dedup de componentes).
- **Limitação honesta:** não consigo enumerar todos os SKUs virtuais (a silver, única fonte com estrutura de kit, é snapshot de 500 linhas/1 dia e nem tem o 8301001172). O método pro João achar todos na fonte: códigos que são `item_original_codigo` (kit) E também `item_desmembrado_codigo` (componente).

## Bases novas avaliadas (Bling NF-e) — nomes ganhos, troca rejeitada

- **NF-e de compra** (fornecedores): tem SKU→custo real + nomes, mas o valor da nota parece FOB (~metade do custo cadastrado R$83,75) → não usar como custo sem entender frete/imposto de importação. Guardado para decisão de custo futura.
- **NF-e de venda** (`silver_minimal_bling_nfe_fechamento`, aba "2.1. Itens" gid 488044140): casa com Vendas por `numeroPedidoLoja` = final do `order_id`. **Testada como fonte de itens e rejeitada:** tem a MESMA dobra de kit (confirmado #489248/#496667/#491156), veio truncada (100k, só 15/05+) e com ruído (devolução/transferência/cancelada). Prova que o bug do kit é a montante das duas bases.
- **Ganho aproveitado:** o João adicionou `item_desmembrado_nome` na aba Itens Shopify (99,6% de cobertura). Liguei na auditoria: `carregar_itens` traz `descricao`; `detalhar_pedidos` usa o nome da própria base (dict silver virou reserva). Auditoria agora com nomes reais. `carregar_descricoes`/gid silver: sem uso ativo.

## Virada — itens passam a vir da NF (decisão do João)

- **Decisão:** parar de usar a base de itens Shopify; puxar os itens **da base de NF** casando `numeroPedidoLoja` = final do `order_id`.
- **Antes disso, medi o quadro:** NF vs Shopify em 32.462 pedidos → 91% idênticos (incl. dobrados), NF mais limpa em 7%, maior em 2%. Ou seja, a NF **não conserta** o kit no geral, mas o João optou por ela mesmo assim (fica mais limpa em casos como #469583, e traz os nomes).
- **Implementado:** `dados.carregar_itens` agora lê o gid 488044140 (NF), reconstrói `order_id` a partir de `numeroPedidoLoja`, filtra natureza ∈ {Venda, Bonificação} e status ∉ {Cancelada, Rejeitada, Pendente}. Novos: `GID_ITENS_NF`, `_NF_NATUREZAS_CONTAM`, `_NF_STATUS_INVALIDO`.
- **Impacto junho:** CMV R$2,61M → **R$2,53M**; MC R$1,835M → **R$1,923M**; cobertura 99,1% (128 pedidos sem NF → custo 0); "suspeitos" 870 → 532; #469583 saiu de 9 linhas dobradas para 3 limpas.
- **Caveats ativos (a confirmar com o João):** filtros de natureza/status são premissa minha; brinde pode estar sendo cortado; kit ainda dobra em ~91%. **Falta ADR** formalizando a troca de fonte.

## Fechamento da sessão

- **Reversão da fonte de itens:** o João concluiu que **puxar da venda é mais confiável que da NF de saída** (a NF dobra em ~91% e corta brinde). Revertido `carregar_itens` para a base de **Vendas Shopify** (com nomes). Junho: CMV R$2,61M, MC R$1,835M. Painel + auditoria OK.
- **Documento de orientação criado:** `docs/orientacao-base-itens-confiavel.md` — pro time de Dados construir uma base de itens **a partir da venda**, com kit explodido corretamente (uma vez, folhas, brindes incluídos, sem duplicar). Substitui o antigo `bug-explosao-kit-bigquery.md` (removido).
- **Estado no fecho:** kit ainda dobra (fonte a montante — depende do time de Dados). Painel usa Vendas Shopify + nomes. NF guardada como fonte de receita fiscal futura (v2+). Paliativo B (`SKUS_KIT_VIRTUAL`) ativo mas pequeno.

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** novo módulo `auditoria-ui`; silver reclassificada (dicionário de nomes); inventário (+ página de auditoria, + `.streamlit/config.toml`).
- **`CLAUDE.md`:** seção 0 (página de auditoria disponível).
- **`docs/specs/`:** criado `2026-07-04-auditoria-custos-por-pedido.md`.
