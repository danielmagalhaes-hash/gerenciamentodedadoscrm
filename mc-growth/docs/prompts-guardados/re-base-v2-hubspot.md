# Prompt guardado — Re-basear a V2 (aba de aquisição) no HubSpot

> Criado em 2026-07-10, na discovery da V4. **Não executar agora** — é uma sessão futura,
> a rodar **depois** (ou junto) da construção da V4, quando a fonte HubSpot já estiver ligada.

## Por que existe

A V4 tornou o **HubSpot** a **fonte oficial** de "cliente novo × recompra" (por `e_mail`,
`tipo_de_venda`, `data_primeira_compra`). A V2 (aba de aquisição) ainda usa o **carimbo nativo
do Shopify** (`customer_type` na aba `Vendas`). As duas definições **divergem**:
- V2 = "novo **no Shopify**" (point-in-time, por pedido);
- V4 = "novo **na Minimal**" (cross-canal, por cliente/e-mail).

Duas abas do mesmo painel mostrando números de "cliente novo" que não batem **destrói a
confiança na ferramenta**. Decisão do João: **uma ferramenta, uma definição** → alinhar a V2 ao
HubSpot.

## O que a sessão deve fazer

1. **Ler o contexto:** `PRODUCT.md` (V4), o ADR `2026-07-10-v4-coortes-recompra-hubspot.md`,
   `cascata.calcular_aquisicao` e `pages/2_Aquisicao.py`.
2. **Trocar a fonte de novo×recompra** da V2: em vez do `Vendas.customer_type`, usar a
   classificação do HubSpot (`tipo_de_venda` / lookup por `e_mail`) — a mesma que a V4 usa.
3. **Reamarrar:** garantir que a partição de pedidos da aba de aquisição continua fechando com
   os totais do painel (a guarda de amarração da V2), agora sob a nova chave.
4. **Verificar a divergência** que isso corrige: rodar a query que compara, no período
   sobreposto, o `tipo_de_venda` (HubSpot) × `customer_type` (Shopify) — e mostrar de quanto a
   V2 muda ao migrar.
5. **Decidir o destino do carimbo antigo:** aposentar o `customer_type` na V2 ou mantê-lo como
   segunda lente rotulada.

## Cuidados

- Toca **dinheiro/regra de negócio** → spec antes (Mantra 3). É a `cascata.py`.
- A V4 precisa estar com a fonte HubSpot **já ligada** (a V2 vai reusar a mesma leitura).
- Confirmar antes: `valor` (HubSpot) × `net_revenue` (Shopify) — se a receita muda, a MC-novos
  da V2 muda junto.
