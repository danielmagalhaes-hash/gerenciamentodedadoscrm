# MC Growth — Painel de Margem de Contribuição · **V2 (Aquisição)**

> Documento de produto. Fonte de verdade do **domínio** e do **comportamento esperado**. Lido por todos os outros documentos. Atualizado quando o produto muda.
>
> **V1 gerado na Fase 0 (Discovery), 2026-06-30/07-01.** **V2 gerado por handoff de versão em 2026-07-09** (entrevista de discovery focada — `docs/sessions/2026-07-09-discovery-v2-aquisicao.md`). Base do handoff: `docs/ROADMAP.md` (V2) + o V1 arquivado em `docs/product-history/PRODUCT-v1.md`.
>
> **Como ler as marcas:** **[HERDADO]** = já existe desde a V1, não muda. **[NOVO]** = entra na V2. O que a V2 acrescenta gira todo em torno de uma coisa: **o painel deixa de só somar pedidos e passa a saber se um pedido é de um cliente novo ou de uma recompra.**

---

## 1. Visão e proposta de valor

**Em uma frase:**
- **[HERDADO]** um painel diário que mostra a **Margem de Contribuição (MC)** da Minimal Club no canal Shopify, sem esperar o fechamento mensal do Financeiro.
- **[NOVO]** e, numa **aba dedicada de aquisição**, responde se **a aquisição de clientes novos está gerando Margem de Contribuição positiva já na primeira compra**.

**Para quem, qual problema, como resolve:**
A Minimal Club (moda masculina minimalista, premium, D2C) fatura ~R$95M/ano e cresce rápido. A V1 tirou a gestão do escuro sobre a MC do mês. Mas a V1 é um **retrovisor que só soma pedidos** — ela não sabe distinguir o cliente que a empresa **pagou pra trazer** do cliente que **voltou sozinho**. A V2 acrescenta essa distinção usando o carimbo que a própria Shopify já põe em cada pedido (novo × recompra) e monta uma tela que responde à pergunta que decide o botão da mídia: **"estou ganhando ou perdendo Margem de Contribuição em cada cliente novo que trago, já na primeira compra dele?"** É uma **régua conservadora** (olha só o primeiro toque): se a aquisição já se paga na 1ª compra, ótimo; se não, a resposta de "mas ele volta e compra de novo" fica para a V4 (recompra/coorte).

**O que este produto NÃO é:**
- **[HERDADO]** Não é fechamento contábil oficial; não é BI/ERP; não é tempo real ao segundo; na v1/v2 cobre **só Shopify** (não B2B, TikTok Shop, Assinatura, Mercado Livre).
- **[NOVO] Não mede "lucro".** Mede **Margem de Contribuição** — o que sobra depois dos custos **variáveis** (inclui a mídia), **antes** dos custos fixos (aluguel, salário, sistemas). "Aquisição com MC positiva" quer dizer que ela paga os variáveis e ajuda a cobrir o fixo — **não** que a empresa lucrou.
- **[NOVO] Não mede tempo de vida (LTV).** A V2 olha **só a 1ª compra dentro do período**. Se um cliente novo dá MC negativa na porta de entrada mas se paga na recompra, isso é a **V4** (coortes), não a V2.
- **[NOVO] Não conhece a pessoa.** A V2 não guarda e-mail, não segue o cliente no tempo, não faz cadastro. Ela só lê uma etiqueta por pedido.

---

## 2. Usuários e papéis

### João (gestão de growth) — único usuário — **[HERDADO]**
- **Contexto:** opera o crescimento da Minimal; entende lógica avançada, vocabulário de dev em construção. Usa só computador.
- **Objetivos no sistema:** abrir o painel, escolher um período, ver a MC e a cascata (V1); **[NOVO]** e abrir a aba de aquisição pra decidir se acelera ou segura a mídia com base na MC do cliente novo.
- **Frustrações atuais:** a V1 já resolveu "ver a MC do mês"; a dor que sobra é **não saber se o dinheiro de mídia está trazendo cliente que se paga**.
- **Frequência de uso:** diária.

### CEO e lideranças — **fora do escopo (v2+)** — **[HERDADO]**
- Consultariam ≥1x/semana, só leitura. Login individual multiusuário segue fora da V2 (fatia grande de trabalho; a V2 nasce só pro João). A aba de aquisição é justamente a tela que a diretoria vai querer um dia — registrado, mas não construído agora.

---

## 3. Glossário do domínio

> Os termos **[HERDADO]** vêm da V1 e continuam valendo idênticos. Os **[NOVO]** são o vocabulário que a V2 introduz.

### Margem de Contribuição (MC) — **[HERDADO]**
- **Definição:** o que sobra das Vendas depois de tirar todos os custos e deduções **variáveis**, incluindo a mídia paga. É o número-herói do painel.
- **Exemplo:** Vendas de R$609k no mês, menos deduções/impostos/CMV/taxas/frete e menos a mídia, resulta na MC do período.
- **Relações:** fim da cascata. Lucro Bruto é o subtotal antes de descontar a mídia.
- **NÃO confundir com:** **lucro líquido** (que é depois do custo fixo), margem bruta isolada, nem o fechamento do Financeiro. **"Lucro" é sinônimo proibido de MC neste projeto.**

### Vendas (Order Revenue / net_revenue) — **[HERDADO]**
- **Definição:** receita líquida dos pedidos pagos do Shopify no período. = soma do `net_revenue` (Base 1), só `PAID`.
- **Exemplo:** pedido 503184 com `net_revenue` = R$350,28.
- **Relações:** topo da cascata; base das linhas em %; numerador do ROAS e do Ticket.
- **NÃO confundir com:** faturamento bruto; receita com frete/devolução separados.

### CMV (Custo da Mercadoria Vendida) — **[HERDADO]**
- **Definição:** custo dos produtos que saíram em cada pedido, item a item (custo do SKU × quantidade). Só conta itens de pedidos presentes na aba `Vendas`.
- **Exemplo:** pedido com Camiseta Preta M (SKU 8301001013) ×2, custo R$34,50 → R$69 de CMV.
- **Relações:** vem da base Itens cruzada com Custos. Inclui **brindes**.
- **NÃO confundir com:** preço de venda, valor do desconto.

### SKU / Kit — **[HERDADO]**
- SKU = código do produto real com custo cadastrado (ex.: `8301001013`). Kit = produto que é um conjunto (ex.: "Compre 3 leve 4 + Carteira"), entregue **já explodido** nos componentes. Não confundir o SKU do kit (`kit4xcamisetas31`) com os SKUs reais.

### Mídia paga (Ad Spend) — **[HERDADO]**
- **Definição:** gasto total em anúncios pagos no período. = `fb_investimento/(1−0,1215)` + `google_investimento` + `google_institucional_investimento` (FB embrutecido pelo imposto de 12,15%).
- **Relações:** última linha antes da MC. **[NOVO]** na V2, é também numerador do CAC e denominador do aROAS.
- **NÃO confundir com:** o valor puro de `fb_investimento` (sem imposto); custo de influenciador (fora da conta).

### ROAS Shopify (blended) — **[HERDADO]**
- Vendas **totais** ÷ Ad Spend. Retorno geral da mídia.
- **NÃO confundir com:** o **aROAS** (novo, abaixo), que olha só a fatia de novos e dá sempre **menor**.

### Ticket médio (AOV) / Dia fechado — **[HERDADO]**
- Ticket = Vendas ÷ nº de pedidos. Dia fechado = dia cujas fontes já atualizaram (o painel mostra ontem pra trás).

---

### `customer_type` (carimbo de cliente) — **[NOVO]**
- **Definição:** etiqueta que a **própria Shopify** põe em cada pedido, **no momento do pedido**, dizendo se aquele cliente era novo ou já tinha comprado antes. Três valores na base: `Primeira Compra`, `Recompra`, ou vazio.
- **Exemplo:** pedido 508271 → `customer_type = "Primeira Compra"`.
- **Relações:** é a chave que parte toda a V2 (novos × recompra). Vem na aba `Vendas`, coluna `customer_type`, automático no fluxo.
- **NÃO confundir com:** um cálculo nosso — é o campo **nativo da Shopify**, que enxerga o histórico completo da loja (por isso não sofre viés de "cliente que comprou antes do início da nossa base").

### Cliente novo / Primeira Compra — **[NOVO]**
- **Definição:** pedido com `customer_type = "Primeira Compra"` — a **1ª compra daquele cliente no Shopify**. Cada cliente tem **exatamente um** na vida.
- **Exemplo:** alguém que nunca comprou no Shopify faz o 1º pedido hoje → Primeira Compra.
- **Relações:** base de MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS. "Cliente novo" é uma **convenção ajustável**: hoje = novo **no canal Shopify** (não olha se comprou em outro canal). Se um dia a régua mudar, muda a leitura.
- **NÃO confundir com:** "lead" ou "cadastro" (não é cadastro, é pedido pago carimbado); nem "novo na Minimal" (é novo **no Shopify**).

### Recompra — **[NOVO]**
- **Definição:** pedido com `customer_type = "Recompra"` — o cliente já tinha ≥1 pedido Shopify antes.
- **Relações:** o complemento de Primeira Compra. Na V2 a recompra **não aparece na tela** (o foco é aquisição); a leitura de recompra é candidata a uma versão seguinte.
- **NÃO confundir com:** "cliente fiel" ou "assinante" — recompra não implica recorrência regular.

### Sem classificação — **[NOVO]**
- **Definição:** os pedidos sem carimbo (`customer_type` vazio) — em junho/2026, 84 de 37.593 (0,22%).
- **Relações:** formam uma **3ª faixa** discreta, não empurrada pra "novos" nem "recompra", pra que `novos + recompra + sem-classificação = total` feche na unha.

### MC de novos clientes (MC-novos) — **[NOVO]**
- **Definição:** a Margem de Contribuição gerada **só pelos pedidos de 1ª compra**, já descontada **toda** a mídia do período. É a manchete da aba de aquisição.
- **Fórmula (soletrada):** `Vendas-novos − (deduções % sobre Vendas-novos) − CMV-novos − Ad Spend total`.
- **Exemplo:** se os pedidos novos geram R$300k de Lucro Bruto e a mídia do mês foi R$250k → MC-novos = R$50k (positiva: a aquisição se paga na 1ª compra).
- **Relações:** MC-novos > 0 ⇔ Lucro Bruto médio do pedido novo > CAC. É o número que a linha do zero pinta de verde/vermelho.
- **NÃO confundir com:** "lucro de novos" (é contribuição, não lucro — antes do fixo).

### Vendas de novos clientes — **[NOVO]**
- **Definição:** Σ `net_revenue` dos pedidos `Primeira Compra` do período. Unidade R$.
- **Relações:** numerador do aROAS.

### Pedidos de novos clientes — **[NOVO]**
- **Definição:** contagem de pedidos `Primeira Compra` do período. É o **mesmo número** de "clientes novos" adquiridos (cada cliente novo tem um único pedido de 1ª compra). Unidade: inteiro.
- **Relações:** denominador do CAC.
- **NÃO confundir com:** "pedidos totais" — aqui só os de 1ª compra. E cuidado: "pedidos de novos = clientes novos" só vale por causa da regra de 1-por-cliente.

### CAC (Custo de Aquisição de Cliente) — **[NOVO]**
- **Definição:** quanto custou, em mídia, trazer um cliente novo no período.
- **Fórmula:** `CAC = Ad Spend total ÷ Pedidos de novos`.
- **Exemplo:** R$1M de mídia ÷ 5.000 clientes novos = R$200 por cliente novo.
- **Relações:** compara com o Lucro Bruto médio do pedido novo (se LB médio > CAC, a aquisição se paga). É um **CAC "blended" por convenção** — usa a mídia inteira, tratando tudo como aquisição (ver "Convenção 100% mídia → novos"). Unidade: R$/cliente novo.
- **NÃO confundir com:** "custo por pedido" (que dividiria por **todos** os pedidos, não só os de 1ª compra).

### aROAS (ROAS de aquisição) — **[NOVO]**
- **Definição:** para cada R$1 de mídia, quantos reais de **venda de clientes novos** voltaram. O "a" é de aquisição.
- **Fórmula:** `aROAS = Vendas de novos ÷ Ad Spend total`. Múltiplo, sem unidade.
- **Exemplo:** R$4M de venda de novos ÷ R$1M de mídia = aROAS 4,0.
- **Relações:** é o mesmo fato do CAC por outro ângulo (receita, não R$/cliente). Sempre **menor** que o ROAS Shopify blended (que soma também a recompra).
- **NÃO confundir com:** o "ROAS Shopify" da V1 (Vendas **totais** ÷ mídia).

### Convenção 100% mídia → novos — **[NOVO]**
- **Definição:** uma **suposição do primeiro momento**: atribuir **toda** a mídia do período aos clientes novos (aquisição), como se nenhum real de mídia fosse remarketing.
- **Relações:** é o que faz a MC-novos, o CAC e o aROAS carregarem a mídia inteira. Consequência: MC-novos é a visão **mais dura** da aquisição (pior cenário); a recompra fica sem custo de mídia. **Ajustável** — a V4 refina, separando mídia de aquisição × remarketing.
- **NÃO confundir com:** uma medição real de atribuição — é convenção declarada, não fato medido.

---

## 4. Entidades do negócio

> A V2 é **magra** em entidades: **não cria nenhuma nova.** Só pendura um atributo no Pedido.

### Pedido — **[HERDADO]** + um atributo **[NOVO]**
- **Atributos:** `order_id`, `order_name`, data de pagamento, status, `net_revenue`, lista de itens **[HERDADO]**; **[NOVO]** `customer_type` (Primeira Compra / Recompra / vazio).
- **Ciclo de vida:** nasce pago na Shopify → entra no painel no dia fechado. O `customer_type` é carimbado no nascimento e é **imutável** (foto do momento).
- **Quem cria/edita:** a Shopify (inclusive o carimbo). **Quem consulta:** o painel (só lê).

### Item de pedido / Tabela de custo / Parâmetro de custo / Gasto de mídia — **[HERDADO]**
- Inalterados na V2 (detalhe no V1 arquivado e no `ARCHITECTURE.md`). O **e-mail / identidade de cliente** que permitiria uma entidade "Cliente" de verdade (com história e coorte) **não entra na V2** — é V4.

---

## 5. Fluxos principais

### Fluxo A — Atualização diária dos dados — **[HERDADO]**
Automático; no início do dia seguinte as fontes refletem o dia anterior. **[NOVO]** a coluna `customer_type` vem junto, automática no fluxo — sem passo manual.

### Fluxo B — Abrir e ler o painel (aba MC) — **[HERDADO]**
João abre, escolhe período, vê a MC (herói) + 5 cartões + cascata DRE. Alerta de SKU sem custo. **A aba MC da V1 não muda na V2.**

### Fluxo C — Editar parâmetros de custo — **[HERDADO]**
Inalterado.

### Fluxo D — Abrir a aba de aquisição — **[NOVO]**
- **Quem dispara:** João.
- **Pré-condições:** coluna `customer_type` presente na aba `Vendas` (já está); dias fechados.
- **Passos:**
  1. João abre a aba de aquisição e escolhe o período.
  2. O painel lê `Vendas` (com o carimbo) + `Itens` + `Custos` + `Midia` do período.
  3. Separa os pedidos por `customer_type` e calcula, só sobre os `Primeira Compra`: Vendas-novos, Pedidos-novos, CMV-novos, deduções-novos → Lucro Bruto-novos → **MC-novos** (menos **toda** a mídia).
  4. Calcula **CAC** e **aROAS**.
  5. Mostra os 5 números; a MC-novos aparece **verde se positiva, vermelha se negativa** (a linha do zero).
- **Pós-condições:** João sabe se a aquisição gerou **MC positiva na 1ª compra** no período.
- **Divergências:**
  - **Período sem pedidos novos** (Primeira Compra = 0) → CAC indefinido → mostra **"—"** + nota "sem clientes novos no período".
  - **Período sem mídia** (Ad Spend = 0) → aROAS indefinido → **"—"** + nota "sem mídia no período" (nada de "∞" nem "R$0" que pareça aquisição de graça). A MC-novos segue válida.
  - **SKU sem custo** num pedido novo → herda o alerta da V1 (a MC-novos pode estar superestimada).

---

## 6. KPIs e regras de cálculo

> **[HERDADO]** — a cascata DRE completa e os 5 cartões da V1 (Vendas, Ad Spend, ROAS Shopify, Ticket, Pedidos) seguem idênticos; detalhe no V1 arquivado. Abaixo, **[NOVO]**, os 5 KPIs da aba de aquisição. Toda linha em % incide sobre a **Vendas** da faixa correspondente.

### MC de novos clientes (MC-novos) — **[NOVO]**
**Mede:** a contribuição da aquisição na 1ª compra, com toda a mídia pesando nela.
**Fórmula:** `Vendas-novos − (deduções % sobre Vendas-novos) − CMV-novos − Ad Spend total`.
**Unidade:** R$. **Frequência:** período fechado.
**Normal:** ≥ 0 (verde) — a aquisição se paga na 1ª compra.
**Alerta:** < 0 (vermelho) — a aquisição **não** se paga na 1ª compra (pode ainda se pagar na recompra — isso é V4).

### Vendas de novos clientes — **[NOVO]**
**Mede:** receita dos pedidos de 1ª compra.
**Fórmula:** `Σ net_revenue` onde `customer_type = "Primeira Compra"`.
**Unidade:** R$. **Frequência:** período fechado.
**Normal / Alerta:** sem faixa — mostra o número cru (a régua calibrada é V5).

### Pedidos de novos clientes — **[NOVO]**
**Mede:** quantos clientes novos foram adquiridos no período.
**Fórmula:** `COUNT` de pedidos com `customer_type = "Primeira Compra"`.
**Unidade:** inteiro. **Frequência:** período fechado.
**Normal / Alerta:** sem faixa — número cru.

### CAC (Custo de Aquisição de Cliente) — **[NOVO]**
**Mede:** quanto de mídia custou trazer cada cliente novo.
**Fórmula:** `Ad Spend total ÷ Pedidos de novos`, onde `Ad Spend = fb/(1−0,1215) + google + google_institucional`.
**Unidade:** R$/cliente novo. **Frequência:** período fechado.
**Normal / Alerta:** sem faixa própria — o julgamento é relativo à MC-novos (se o LB médio do pedido novo supera o CAC). Teto de CAC calibrado = V5.
**Borda:** Pedidos de novos = 0 → "—".

### aROAS (ROAS de aquisição) — **[NOVO]**
**Mede:** reais de venda de clientes novos por real de mídia.
**Fórmula:** `Vendas de novos ÷ Ad Spend total`.
**Unidade:** múltiplo (ex.: 4,0). **Frequência:** período fechado.
**Normal / Alerta:** sem faixa — número cru (piso calibrado = V5).
**Borda:** Ad Spend = 0 → "—".

---

## 7. Escopo

### 7.1 Entra na V2
- **[HERDADO]** Tudo da V1: aba de MC (herói + 5 cartões + cascata DRE), filtro de período, editor de custos, alerta de SKU sem custo, só Shopify, só dias fechados, único usuário.
- **[NOVO]** Uma **aba dedicada de aquisição**, ao lado da aba de MC (que não muda), com:
  - Os 5 KPIs: **MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS**.
  - A **linha do zero** na MC-novos (verde/vermelho).
  - A faixa "sem classificação" contabilizada pra fechar a amarração.
  - Tratamento de borda ("—" + nota) nas divisões indefinidas.

### 7.2 Fica para depois (com justificativa)
- **Coluna de recompra na tela** (MC-recompra, "% do LB que vem de recompra") — *a V2 foca só aquisição; registrada como candidata à próxima versão.*
- **Custo cheio real por pedido** — *V3 (evolução da `cascata.py`).* (A **dobra de kit já foi corrigida na fonte** em 2026-07-09; o paliativo do painel saiu — não é mais item da V3.)
- **Seguir o cliente no tempo / LTV / coortes / margem bruta e recompra reais** — *V4; exige identificador de cliente (e-mail/`customer_id`) que a V2 não traz.*
- **Separar mídia de aquisição × remarketing** (tirar a convenção 100%→novos) — *V4.*
- **Régua calibrada "acelerar/segurar/frear"** (alvos de CAC/aROAS/MC, modulador de estoque) — *V5; não importar alvo da True Classic sem calibrar o da Minimal.*
- **[HERDADO]** Login multiusuário (CEO/liderança); outros 4 canais; comparação/forecast; visão dia-a-dia; mobile; parâmetros "valem pra frente".

### 7.3 Nunca vai entrar — **[HERDADO]**
- Fechamento contábil oficial (é indicador de gestão, não verdade fiscal).
- BI/ERP completo (fora da proposta).
- Tempo real ao segundo (trabalha com dias fechados).

---

## 8. Restrições e premissas

### Operacionais
- **[HERDADO]** Cada fonte atualiza em ritmo próprio, mas no início do dia seguinte todas estão atualizadas (sustenta "só dias fechados"). Vendas e CMV vêm de tabelas diferentes; o CMV conta só pedidos presentes na `Vendas`.
- **[NOVO] A V2 depende do carimbo `customer_type` na aba `Vendas` — e ele vem automático no fluxo** (parte permanente da extração, não colado à mão). Se um dia sumir, a aba de aquisição não tem como classificar (pré-condição explícita do Fluxo D).
- **[RESOLVIDO 2026-07-09] Dobra de kit:** corrigida na fonte (live na planilha, informado pelo João); o paliativo do painel (`cascata.SKUS_KIT_VIRTUAL`) foi aposentado. O CMV-novos **deixa de ser subestimado** por kit.

### Premissas de modelagem — **[NOVO]**
- **Confiança na Shopify:** adota-se a classificação nativa dela (new/returning) como verdade. Se a Shopify mudar a definição, os números mudam junto.
- **Convenção 100% mídia → novos:** suposição do 1º momento, ajustável (V4 refina).
- **Régua conservadora:** "lucrativa" = MC positiva **na 1ª compra**. A leitura de tempo de vida (recompra) é deliberadamente adiada pra V4.

### Legais / regulatórias
- **[HERDADO]** Os pedidos carregam dados pessoais, mas o painel os **ignora**.
- **[NOVO] A V2 não traz nenhum dado pessoal novo:** `customer_type` é só uma etiqueta (novo/recompra), não e-mail nem CPF. A conversa de LGPD só entra na **V4**, quando o e-mail/`customer_id` for necessário pra coorte.

### Orçamento / prazo
- **[HERDADO]** Evolução incremental sobre o painel que já roda local no Mac do João.

### Integrações futuras esperadas
- **[HERDADO]** Conexão direta com Shopify/BigQuery (hoje via planilha); demais canais; configuração de parâmetros na tela.
- **[NOVO]** Identificador de cliente (e-mail/`customer_id`) na base, para destravar a V4 (coorte/LTV).
