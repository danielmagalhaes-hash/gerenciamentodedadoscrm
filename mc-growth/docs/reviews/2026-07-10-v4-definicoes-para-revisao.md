# Relatório para revisão — V4 (Coortes de recompra)

> **Para quê:** rodar com um advisor (`/revisar-dados`, `/revisar-estrategia`, `/devil-advocate`)
> **antes** de escrever a spec e construir. Documento autocontido: traz as definições, as
> decisões, e os pontos que eu quero que sejam **furados**. Data: 2026-07-10.

---

## 1. A decisão que a V4 precisa destravar

**"Devo acelerar ou segurar a aquisição de clientes?"** — lendo, por safra (mês da 1ª compra),
a **Margem de Contribuição acumulada por cliente ao longo do tempo** (curva de payback). A V4
**mostra a curva**; não dá o veredito automático (isso é a régua da V5).

## 2. Definições (o que foi fechado no discovery)

| Conceito | Definição fechada |
|---|---|
| **Coorte / safra** | Clientes cuja 1ª compra caiu num mês. Cada cliente numa só safra. |
| **Cliente** | Pessoa que dura no tempo, chave = **`e_mail`** (HubSpot). |
| **Fonte oficial** | HubSpot no BQ `moon-ventures-data-lake.prod_silver.silver_deals_minimal`, filtro **`etapa_do_negocio='Shipped'`** (= Shopify, inclui pedidos de vendedores). |
| **Novo × recompra** | `tipo_de_venda` do HubSpot (não mais o carimbo nativo do Shopify). |
| **Âncora da coorte** | `data_primeira_compra` — **1ª compra cross-canal** (qualquer canal). |
| **Eixo do tempo** | `meses_desde_primeira_compra` (m+0, m+1, …). |
| **Métrica-herói** | **MC acumulada por cliente** = Σ MC da safra ÷ nº de clientes, acumulada por mês de idade; mídia inteira do mês no **mês 0**. **Cruzar o zero = a turma se pagou.** |
| **CAC por safra** | Ad Spend do mês-calendário ÷ nº de clientes da safra (2ª coluna da tabela; o "mergulho"). |
| **Payback** | Menor mês em que a MC acumulada por cliente ≥ 0; "—" se ainda não cruzou. |
| **Recompra em 90 dias** | % da safra com ≥1 compra Shopify adicional em até 90 dias (janela fixa, rótulo explícito). |
| **MC real × estimada** | Real (CMV item a item via ponte `nome`→`Vendas.order_name`→Itens→Custos) de **2022-01** em diante; **25% de margem de produto estimada** antes (≈101 linhas). |
| **Safra fechada** | Só mostra célula de mês-calendário já **encerrado**; nunca extrapola. |
| **Tela** | Tabela/triângulo (`Safra \| CAC \| m+0…`, todas) + curva (últimas 12 safras, ampliável) + seletor de safra → KPIs de cabeçalho. |

## 3. Convenções e premissas assumidas (candidatas a serem furadas)

1. **Viés cross-canal aceito.** A coorte usa a 1ª compra em qualquer canal, mas MC e mídia são
   **só do Shopify**. Cliente que estreou fora do Shopify tem mês 0 incompleto e CAC otimista.
   Justificativa: Shopify é **>95% das vendas**. **Não medido ainda.**
2. **100% da mídia → mês 0 da safra.** Toda a mídia do mês-calendário pesa na safra daquele mês,
   inclusive o que foi remarketing. Herdado da V2.
3. **Custo por SKU é o atual aplicado ao passado.** O CMV de 2022 usa o custo de hoje.
4. **Mix mudou muito.** O negócio 20x'ou de 2022 (~6 mil itens/mês) a 2025 (~120 mil). Safras
   velhas são quase "outra empresa" — o João quis "olhar tudo" mesmo assim.
5. **Confiança na classificação do HubSpot** como verdade de novo×recompra.

## 4. Decisões de método (e o que foi descartado)

- **HubSpot como âncora, não "Shopify-first".** Descartei minha própria recomendação (recomputar
  a 1ª compra dentro do `Shipped`, que casaria mídia↔aquisição e alinharia com a V2). O João
  preferiu a fonte única do HubSpot, aceitando o viés.
- **V3 esvaziada.** Custos seguem em % → o build pula de V2 para V4.
- **V4 = base oficial** → a V2 será re-baseada no HubSpot (senão duas abas divergem).

## 5. O que eu quero que o advisor fure (perguntas dirigidas)

1. **O viés cross-canal é mesmo pequeno?** "95% das vendas Shopify" ≠ "95% dos clientes Shopify
   estrearam no Shopify". Se o TikTok for uma porta de entrada barata que migra pro Shopify, a
   sobreposição pode ser bem maior que 5%. Vale construir antes de medir? (Query planejada.)
2. **A mídia no mês 0 corrompe a leitura?** A mídia do mês inteiro (incl. remarketing) cai no mês
   0 da safra daquele mês. Isso infla o CAC das safras e achata o payback? Como isolar sem entrar
   no escopo "aquisição × remarketing" (parkeado)?
3. **"Olhar tudo" ajuda ou engana?** Com o mix mudando 20x, comparar a safra de 2022 com a de
   2026 informa a decisão de hoje, ou polui? A curva deveria ter um recorte-padrão mais curto?
4. **Custo de hoje sobre venda de 2022** distorce a MC histórica a ponto de mudar o payback? Em
   que direção?
5. **`data_primeira_compra` é confiável e estável?** É point-in-time ou pode ser recalculado
   retroativamente pelo HubSpot (o que mudaria safras já lidas)?
6. **Payback por MC acumulada por cliente** é a métrica-governante certa, ou deveríamos olhar
   também o **valor absoluto** (uma safra que se paga rápido mas é minúscula vs. uma lenta e
   enorme)? A decisão de "acelerar" precisa das duas?
7. **Recompra em 90 dias** é a janela certa para este ticket/ciclo de moda masculina premium, ou
   90 dias corta cedo demais o padrão de recompra real?

## 6. Riscos abertos (pré-construção)

- **Arquitetura:** a planilha estreita não segura anos de itens → ler do BQ direto ou
  pré-agregar. **Não decidido.**
- **Validação:** `valor` (HubSpot) × `net_revenue` (Shopify) batem? **Não confirmado.**
- **Base dos 25%:** margem de produto (antes da mídia), a confirmar na implementação.

## 7. Fontes (rastreabilidade)

- HubSpot: `moon-ventures-data-lake.prod_silver.silver_deals_minimal` (colunas: `e_mail`,
  `nome`, `valor`, `data_de_fechamento`, `tipo_de_venda`, `etapa_do_negocio`,
  `data_primeira_compra`, `meses_desde_primeira_compra`, `canal_da_venda_classificado`).
- Itens (CMV): `silver_minimal_shopify_pedidos_products` (BQ) — contínua de 2022-01 até hoje.
- Custos, Mídia, Vendas: abas atuais do painel (ver `ARCHITECTURE.md` §3).
- Design completo: `PRODUCT.md` (V4). Decisão: `docs/decisions/2026-07-10-v4-coortes-recompra-hubspot.md`.
