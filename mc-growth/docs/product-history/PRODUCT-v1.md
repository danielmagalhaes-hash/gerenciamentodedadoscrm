# MC Growth — Painel de Margem de Contribuição

> Documento de produto. Fonte de verdade do **domínio** e do **comportamento esperado**. Lido por todos os outros documentos. Atualizado quando o produto muda.
>
> **Gerado na Fase 0 (Discovery), 2026-06-30 / 2026-07-01.** Base: `docs/sessions/2026-06-30-discovery.md` e a continuação de 2026-07-01.

---

## 1. Visão e proposta de valor

**Em uma frase:** um painel diário que mostra a **Margem de Contribuição (MC)** da Minimal Club no canal Shopify, sem esperar o fechamento mensal do Financeiro.

**Para quem, qual problema, como resolve:**
A Minimal Club (moda masculina minimalista, premium, D2C) fatura ~R$95M/ano e cresce rápido, mas hoje só enxerga sua Margem de Contribuição no fechamento contábil mensal — ou seja, a gestão decide o mês inteiro "no escuro". O MC Growth resolve isso mostrando, todo dia, a cascata completa de Vendas até a Margem de Contribuição de um período já fechado (ontem pra trás), a partir de dados que a empresa já tem (Shopify, tabela de custo, mídia paga). O coração do produto: **ver a MC de um período fechado, correta, sem esperar o Financeiro.**

**O que este produto NÃO é:**
- Não é fechamento contábil oficial (o número é indicador de gestão, não verdade fiscal).
- Não é BI/ERP completo nem substitui o Financeiro.
- Não é tempo real ao segundo (trabalha com dias já fechados).
- Não cobre, na v1, os outros 4 canais (B2B, TikTok Shop, Assinatura, Mercado Livre) — só Shopify.

---

## 2. Usuários e papéis

### João (gestão de growth) — único usuário da v1
- **Contexto:** opera o crescimento da Minimal; entende lógica avançada, vocabulário de dev em construção. Usa só computador.
- **Objetivos no sistema:** abrir o painel, escolher um período, ver a MC e a cascata para tomar decisão de gestão. Editar os parâmetros de custo (%) quando mudarem.
- **Frustrações atuais:** MC só aparece no fechamento mensal; gestão do dia a dia às cegas.
- **Frequência de uso:** diária.

### CEO e lideranças — **fora do escopo da v1** (v2+)
- **Contexto:** consultariam ≥1x/semana, só leitura, só computador.
- **Por que fora da v1:** login individual para várias pessoas é uma fatia grande de trabalho; a v1 nasce só para o João. Ver seção 7.2.

---

## 3. Glossário do domínio

### Margem de Contribuição (MC)
- **Definição:** o que sobra das Vendas depois de tirar todos os custos e deduções variáveis, incluindo a mídia paga. É o número-herói do painel.
- **Exemplo:** Vendas de R$609k no mês, menos deduções/impostos/CMV/taxas/frete e menos a mídia paga, resulta na MC do período.
- **Relações:** é o fim da cascata (ver KPIs). Lucro Bruto é o subtotal antes de descontar a mídia paga.
- **NÃO confundir com:** lucro líquido contábil, margem bruta isolada, nem o resultado do fechamento do Financeiro.

### Vendas (Order Revenue / net_revenue)
- **Definição:** a receita líquida dos pedidos pagos do canal Shopify no período. Na v1 = soma do `net_revenue` da base de pedidos (Base 1), só `PAID`.
- **Exemplo:** pedido 503184 com `net_revenue` = R$350,28.
- **Relações:** topo da cascata; base de cálculo das linhas em % (impostos, frete, etc.); numerador do MER e do Ticket médio.
- **NÃO confundir com:** faturamento bruto (antes de desconto), nem receita com frete/devolução separados (a v1 usa só o `net_revenue`, sem linha de frete ou devolução própria — ver ADR de devoluções).

### CMV (Custo da Mercadoria Vendida / COGS)
- **Definição:** o custo dos produtos que saíram em cada pedido. Calculado item a item: custo de cada SKU × quantidade. **Só conta itens de pedidos que estão na aba `Vendas`** (ver abaixo).
- **Exemplo:** pedido com Camiseta Preta M (SKU 8301001013) ×2, custo R$34,50 cada → R$69 de CMV nessa linha.
- **Relações:** vem da base de Itens (SKUs por pedido) cruzada com a tabela de Custos (SKU→custo). A aba `Itens` contém **pedidos de outros canais** (B2B, TikTok Shop, Mercado Livre, Assinatura) além do Shopify; a v1 conta o CMV **apenas dos pedidos presentes na aba `Vendas`** (fonte de verdade dos pedidos Shopify). Ver ADR `2026-07-02-cmv-so-pedidos-da-aba-vendas`.
- **NÃO confundir com:** preço de venda, valor do desconto. Inclui **brindes** (o item grátis custa, mesmo sem gerar receita).

### SKU
- **Definição:** o código do produto real (item físico) que tem custo cadastrado.
- **Exemplo:** `8301001013` = Camiseta Gola O M Preta.
- **Relações:** é a chave que liga a base de Itens à tabela de Custos. Na base de Itens é o `item_desmembrado_codigo` (já com o kit explodido no componente real).
- **NÃO confundir com:** o código do "produto vendido" na Shopify quando é um **kit** (ex: `kit4xcamisetas31`), que precisa ser explodido nos SKUs reais antes de buscar o custo.

### Kit / combo
- **Definição:** um produto vendido que na verdade é um conjunto de vários itens (ex: "Compre 3 e leve 4 + Carteira").
- **Exemplo:** `kit4xcamisetas31` → explode em 4 camisetas + 1 carteira, cada uma com seu SKU e custo.
- **Relações:** a base de Itens já entrega o kit **explodido** nos componentes (`tipo_explosao = kit_desmembrado`), então cada componente aparece como linha com seu SKU.
- **NÃO confundir com:** um único SKU. Contar o kit como 1 item subestima o CMV.

### Parâmetros de custo (as linhas em %)
- **Definição:** percentuais que incidem sobre as Vendas para estimar deduções e custos variáveis (impostos, frete, embalagem, taxas, etc.).
- **Exemplo:** Frete = 4,8% das Vendas.
- **Relações:** ficam numa aba editável (`Parametros`); o João é o único que edita.
- **NÃO confundir com:** valores absolutos em R$ — são percentuais aplicados sobre a linha Vendas.

### Mídia paga (Ad Spend)
- **Definição:** o gasto total em anúncios pagos (Meta/Facebook + Google) no período.
- **Exemplo:** R$88k no mês.
- **Relações:** é a última linha antes da MC; denominador do MER. Na v1 = `fb_real + google_investimento + google_institucional_investimento`, onde `fb_real = fb_investimento / (1 − 0,1215)` — o FB Ads é embrutecido pelo imposto de 12,15% pago ao investir (ADR 2026-07-03). Google não leva imposto.
- **NÃO confundir com:** custo de influenciadores (fora da conta na v1). O valor puro da coluna `fb_investimento` (sem o imposto) **não** é o gasto real.

### ROAS Shopify (blended)
- **Definição:** quantos reais de venda saem por real de mídia paga. É o "retorno geral" da mídia. Fórmula: Vendas ÷ Ad Spend.
- **Exemplo:** Vendas R$8,09M ÷ Ad Spend R$1,42M ≈ 5,69.
- **NÃO confundir com:** ROAS por campanha/canal — este é "blended", usa o gasto total (FB com imposto + Google). Histórico: a v1 nasceu com o nome "MER"; renomeado para "ROAS Shopify" em 2026-07-03 (mesma conta).

### Ticket médio (AOV)
- **Definição:** valor médio por pedido. Vendas ÷ nº de pedidos.
- **NÃO confundir com:** valor médio por item.

### Dia fechado
- **Definição:** um dia cujas três fontes já foram atualizadas (ocorre no início do dia seguinte). Só dias fechados aparecem no painel.
- **Relações:** garante que o número não "dança". A v1 mostra ontem pra trás.

---

## 4. Entidades do negócio

> Na v1 as entidades **vivem como abas de uma planilha Google** (não há banco de dados). Detalhe técnico das colunas em `ARCHITECTURE.md`.

### Pedido
- **Atributos relevantes:** `order_id` (chave interna, formato `gid://shopify/Order/...`), `order_name` (número humano), data de pagamento, status de pagamento, `net_revenue`, e a lista de itens (SKUs).
- **Ciclo de vida:** nasce pago na Shopify → entra no painel no dia seguinte (dia fechado). A v1 só considera `PAID`.
- **Quem cria/edita/consulta:** criado pela operação da loja (Shopify); a v1 só consulta (leitura).

### Item de pedido (SKU explodido)
- **Atributos relevantes:** `order_id`, `sku` (componente real após explosão de kit), `quantidade`.
- **Ciclo de vida:** derivado do pedido; um pedido tem N itens; kits já vêm explodidos.
- **Quem cria/edita/consulta:** origem Shopify (base silver); a v1 só consulta.

### Tabela de custo (SKU → custo)
- **Atributos relevantes:** `sku`, `valor_custo` (e outras colunas ignoradas na v1).
- **Ciclo de vida:** mantida fora do escopo da v1 (quem mantém e com que frequência não é problema da v1).
- **Quem cria/edita/consulta:** mantida por terceiros; a v1 só consulta.

### Parâmetro de custo (%)
- **Atributos relevantes:** `parametro` (nome), `percentual`.
- **Ciclo de vida:** editável a qualquer momento pelo João. Na v1 vale no modo "recalcula tudo" (mexeu, muda o passado). O modo "vale pra frente" (versão datada) fica para v2 — ver 7.2.
- **Quem cria/edita:** só o João. **Quem consulta:** o painel.

### Gasto de mídia (por dia)
- **Atributos relevantes:** `data`, `fb_investimento`, `google_investimento`, `google_institucional_investimento`.
- **Ciclo de vida:** origem BigQuery → planilha; a v1 só consulta.

---

## 5. Fluxos principais

### Fluxo A — Atualização diária dos dados
- **Quem dispara:** automático (as fontes se atualizam sozinhas).
- **Pré-condições:** é um novo dia; no início do dia seguinte todas as três fontes já refletem o dia anterior.
- **Passos:**
  1. Shopify atualiza pedidos e itens; a tabela de custo e o BigQuery (mídia) alimentam a planilha única.
  2. No início do dia seguinte, o dia anterior está "fechado" nas três fontes.
  3. O painel, ao ser aberto/atualizado, lê a planilha ao vivo.
- **Pós-condições:** o painel reflete os dias fechados até ontem.
- **Divergências:** se alguma fonte atrasar, o dia pode sair incompleto — premissa aceita: no início do dia seguinte está tudo lá.

### Fluxo B — Abrir e ler o painel
- **Quem dispara:** o João.
- **Pré-condições:** planilha compartilhada e acessível.
- **Passos:**
  1. Abre o painel (padrão: "este mês até agora").
  2. Vê a MC (herói) + 5 cartões + a cascata tipo DRE.
  3. Ajusta o filtro de período; tudo na tela respeita o período (dados somados).
- **Pós-condições:** entende a MC do período escolhido.
- **Divergências:** se houver SKU vendido sem custo cadastrado, o painel **avisa na tela** (ex: "⚠️ X itens sem custo — MC pode estar superestimada") e ainda mostra o número.

### Fluxo C — Editar parâmetros de custo
- **Quem dispara:** o João.
- **Pré-condições:** —
- **Passos:** edita o `percentual` na aba `Parametros` da planilha.
- **Pós-condições:** o painel passa a usar o novo % (na v1, recalcula inclusive o passado).
- **Divergências:** nome do parâmetro precisa bater com a grafia esperada.

---

## 6. KPIs e regras de cálculo

> Todas as linhas em % incidem sobre a linha **Vendas**. Detalhe de fontes/colunas em `ARCHITECTURE.md`.

### Margem de Contribuição (herói)
- **Mede:** o resultado variável do período, já descontada a mídia paga.
- **Fórmula:** `Lucro Bruto − Mídia paga`, onde `Lucro Bruto = Vendas − (soma das linhas em % sobre Vendas) − CMV`.
- **Unidade:** R$. **Frequência:** diária (períodos fechados).

### Cascata (linhas exibidas, tipo DRE)
| # | Linha | Cálculo |
|---|---|---|
| | **Vendas** | Σ `net_revenue` (pedidos pagos, Shopify) |
| − | Devoluções | Vendas × 3,48% |
| − | Chargebacks | Vendas × 0,15% |
| − | PIS/COFINS + CBS | Vendas × 1,75% |
| − | ICMS + IBS | Vendas × 12,54% |
| − | Outras Deduções | Vendas × 0% |
| − | **CMV** | Σ (custo do SKU × quantidade), inclui brindes; **só pedidos presentes na aba `Vendas`** |
| − | Frete | Vendas × 4,8% |
| − | Embalagem | Vendas × 0,57% |
| − | Taxas de Gateways | Vendas × 1,70% |
| − | Valor plataforma | Vendas × 0,90% |
| − | Despesas de antecipação | Vendas × 1,60% |
| = | **Lucro Bruto** | subtotal exibido |
| − | Despesas de mídia paga | `fb_investimento/(1−0,1215)` + `google_investimento` + `google_institucional_investimento` (FB embrutecido pelo imposto) |
| = | **Margem de Contribuição** | |

### Cartões (5)
- **Vendas (Order Revenue):** Σ `net_revenue`. R$.
- **Ad Spend:** mídia paga (FB embrutecido pelo imposto de 12,15% + Google + Google instituc.). R$.
- **ROAS Shopify:** Vendas ÷ Ad Spend. Número (ex: 5,69). (Antes chamado MER.)
- **Ticket médio (AOV):** Vendas ÷ nº de pedidos. R$.
- **Pedidos (Orders):** `COUNT(DISTINCT order_id)` pagos no período. Inteiro.

> **Faixas de normalidade/alerta:** não definidas na v1 (sem comparação/meta). Fica para v2.

---

## 7. Escopo

### 7.1 Entra na v1
- Painel diário, **só canal Shopify**, **só dias fechados** (ontem pra trás).
- Herói (MC) + 5 cartões (Vendas, Ad Spend, MER, Ticket médio, Pedidos).
- Cascata DRE linha a linha até a MC.
- Filtro de período (padrão: este mês até agora), **dados somados**.
- Parâmetros de custo editáveis (só João), via aba da planilha.
- Alerta de "SKU vendido sem custo cadastrado".
- Único usuário: o João.

### 7.2 Fica para depois
- Login individual para CEO/lideranças — *Justificativa: fatia grande de trabalho; v1 é só para o João.*
- Outros 4 canais (B2B, TikTok Shop, Assinatura, Mercado Livre) — *Justificativa: v1 foca Shopify.*
- Comparação/forecast (número menor + %) — *Justificativa: não é o coração; some da v1.*
- Visão dia-a-dia lado a lado — *Justificativa: v1 mostra só dados somados.*
- Acesso mobile e dia "ao vivo" (parcial) — *Justificativa: v1 é desktop e dias fechados.*
- Parâmetros "valem pra frente" (versão datada) — *Justificativa: v1 usa o modo simples (recalcula tudo).*
- Linhas próprias de Frete e Devolução a partir do dado real — *Justificativa: base atual só tem `net_revenue`; alinhamento com Financeiro pendente (ver ADR de devoluções).*
- **[PROBLEMA A RESOLVER v2+] Corrigir a explosão de kit na fonte (BigQuery).** A base de Itens conta os itens dos kits **em dobro** (SKU virtual do kit fica junto dos componentes; e componentes como a Carteira aparecem 2×) → CMV inflado, MC subestimada. Detectado 2026-07-04 (~1.824 pedidos/junho, ~18% do CMV tocado). *Paliativo v1:* `cascata.SKUS_KIT_VIRTUAL` remove SKUs virtuais conhecidos (parcial — não conserta a duplicação de componentes). *Conserto definitivo:* ajustar a consulta do BigQuery para (1) não emitir o SKU virtual junto dos componentes e (2) deduplicar componentes repetidos. Ver ARCHITECTURE.md 6.

### 7.3 Nunca vai entrar
- Fechamento contábil oficial — *Motivo: é indicador de gestão, não verdade fiscal.*
- BI/ERP completo — *Motivo: fora da proposta.*
- Tempo real ao segundo — *Motivo: trabalha com dias fechados.*

---

## 8. Restrições e premissas

### Operacionais
- Cada fonte atualiza em ritmo próprio, mas **no início do dia seguinte todas estão atualizadas** (premissa que sustenta "só dias fechados").
- Vendas vem de uma base (atribuição) e CMV de outra (itens). **Conferido em 2026-07-02:** a aba `Itens` traz também pedidos de outros canais; por isso o CMV conta só os pedidos que existem na `Vendas` (fonte de verdade). Ver ADR `2026-07-02-cmv-so-pedidos-da-aba-vendas`.

### Legais / regulatórias
- Os pedidos carregam dados pessoais (CPF, nome, e-mail, endereço). A v1 **ignora** esses campos (não precisa deles). Sem obrigação de apagar; se um dia precisar, guarda-se.

### Orçamento / prazo
- Prazo declarado: "pronto hoje" (2026-07-01). Caminho realista: começar pelo coração (MC correta) e evoluir.

### Integrações futuras esperadas
- Conexão automática direta com Shopify/BigQuery (hoje intermediadas pela planilha única).
- Demais canais de venda.
- Área de configuração de parâmetros na própria tela (hoje na planilha).
