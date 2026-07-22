# ADR — V4: coortes de recompra a partir do HubSpot (cliente cross-canal, MC por safra no tempo)

- **Data:** 2026-07-10
- **Status:** aceita (discovery fechada; spec pendente)
- **Contexto/sessão:** `docs/sessions/2026-07-10-discovery-v4-coortes.md`
- **Afeta:** `PRODUCT.md` (V4), `ROADMAP.md` (V3/V4), `ARCHITECTURE.md`, futura `cascata.py`/nova aba.

## Contexto

Fim do escopo comprometido V1→V4. A sessão começou com "seguir para V3 e V4". Duas viradas:

1. **V3 (custo cheio real por pedido) foi esvaziada** pelo João: os custos seguem em **%** (da DRE) e os 3 custos novos (CX por pedido, juros de estoque, criativo variável) ficam pra depois. Sem custo real por pedido nem custos novos, a V3 do roadmap **não destrava decisão nova** (o CMV real por pedido a auditoria já mostra). Logo, o build **pula de V2 → V4**.
2. **V4 = coortes de recompra.** A decisão que destrava: **acelerar ou segurar a aquisição**, lendo a **MC acumulada por cliente** de cada safra ao longo do tempo (curva de payback).

O carimbo `customer_type` do Shopify (usado na V2) **não serve** para coorte: ele vive no **pedido**, e coorte exige seguir a **mesma pessoa** por meses — uma chave que dura no tempo.

## Decisão

1. **Fonte oficial de cliente/1ª-compra = HubSpot no BigQuery** `moon-ventures-data-lake.prod_silver.silver_deals_minimal`, filtrada por **`etapa_do_negocio IN ('Shipped', 'Negócio Fechado - Comercial')`** (= Shopify; inclui pedidos lançados por vendedores). Chave de cliente = **`e_mail`**. Novo×recompra = `tipo_de_venda`; a categorização passa a sair do HubSpot (por e-mail), não do carimbo nativo do Shopify.
   > **Refinamento 2026-07-10 (spec):** o filtro passou de só `Shipped` para **`Shipped` + `Negócio Fechado - Comercial`**. O Comercial (1,2%) grava o **nome do cliente** no campo `nome` (não o número do pedido) → **não casa com a `Vendas`** e entra **sempre estimado (25%)**, marcado. Decisão do João: manter (é valor real do cliente). Detalhe na spec `2026-07-10-v4-coortes-recompra` §0.6.
2. **Coorte = mês de `data_primeira_compra`** (1ª compra **cross-canal**). Eixo do tempo = `meses_desde_primeira_compra`. Ambos vêm prontos da base.
3. **Métrica = MC acumulada por cliente** por safra: mídia inteira do mês-calendário no **mês 0** da safra; recompra futura **segue o cliente** até a safra dele, sem nova mídia. **Cruzar o zero = a turma se pagou.**
4. **MC real de 2022-01 em diante** (ponte `nome`→`Vendas.order_name`→Itens→Custos, que existe no BQ de forma contínua desde 2022); **25% de margem de produto estimada** antes de 2022 (≈101 linhas), marcada como provisória.
5. **Tela:** tabela/triângulo (`Safra | CAC | m+0…`, todas as safras) + curva de payback (últimas 12 safras, ampliável) + seletor de safra dirigindo os KPIs de cabeçalho (payback, CAC, LTV até hoje, **recompra em 90 dias** com rótulo explícito). Regra de **safra fechada** (só mês encerrado; sem extrapolar).
6. **Viés aceito e documentado:** coorte cross-canal, mas MC/mídia só do Shopify. Aceito porque Shopify é **>95% das vendas**. A versão "todos os canais" fica para depois.
7. **V4 vira a base oficial** de "cliente novo" → a **V2 será re-baseada no HubSpot** (item à parte; prompt guardado).

## Alternativas descartadas

- **Âncora Shopify-first (recomputar a 1ª compra dentro do `Shipped`)** — era a minha recomendação (casa mídia↔aquisição, alinha com a V2). Descartada pelo João: prefere a definição do HubSpot como fonte única, aceitando o viés dado o peso do Shopify.
- **Estimar todo o histórico por margem %** — desnecessário: o CMV real existe no BQ desde 2022.
- **Curva com todas as ~54 safras** — ilegível; ficou "últimas 12 + tabela cheia".

## Consequências

- **Positivas:** a base já entrega a coorte quase pronta (`data_primeira_compra` + `meses_desde_primeira_compra`); MC real com anos de histórico; uma fonte única de cliente.
- **Custos/riscos:** (a) **arquitetura** — a planilha estreita não segura anos de itens; a V4 provavelmente lê do BQ direto/pré-agregado (decisão da spec); (b) **divergência V2×V4** até o re-base; (c) **viés cross-canal** (a medir por query); (d) **a confirmar:** `valor` do HubSpot × `net_revenue` do Shopify.

## Pendências antes de construir (para a spec)

1. Decisão de arquitetura (como ler o histórico do BQ).
2. Query: `valor` (HubSpot) × `net_revenue` (Shopify) batem?
3. Query: tamanho do viés cross-canal (quantos `Shipped` estrearam fora do Shopify).
4. Confirmar contra o que os **25%** incidem (margem de produto, antes da mídia).
