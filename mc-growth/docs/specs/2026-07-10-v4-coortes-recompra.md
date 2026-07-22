# Spec — V4 (MVP): Aba de Coortes de Recompra

> Spec de construção (Modo B — toca dinheiro: MC por safra, CAC, payback).
> Base de domínio: `PRODUCT.md` (V4, 2026-07-10) + `docs/ROADMAP.md` (V4).
> Discovery: `docs/sessions/2026-07-10-discovery-v4-coortes.md`.
> ADR de domínio: `docs/decisions/2026-07-10-v4-coortes-recompra-hubspot.md`.
> Revisão crítica incorporada: `docs/reviews/2026-07-10-v4-respostas-da-revisao.md`.
> Decisões desta sessão (arquitetura, chaveamento, imposto, 25%): `docs/sessions/2026-07-10-spec-v4-coortes.md`.
>
> **Glossário:** todos os termos abaixo (**safra/coorte**, **cliente** (`e_mail`), **MC acumulada
> por cliente**, **CAC por safra**, **payback**, **recompra em 90 dias**, **safra fechada**,
> **MC real × estimada**, **`Shipped`**) são usados exatamente como no `PRODUCT.md` seção 3.
> **Vocabulário:** MC, **nunca "lucro"**.
>
> **Marca de escopo:** esta spec descreve o **MVP da V4** (Opção 2 de arquitetura — ver §0). O
> histórico de itens real ano-a-ano (Opção 1) fica para a **versão seguinte**; aqui a MC real só
> existe na janela atual de itens e o resto é **estimado (25%)**. Isso **diverge de propósito** do
> `PRODUCT.md` V4 §8 ("MC real desde 2022-01") — a divergência está registrada em §0 e §8.

---

## 0. Decisão de arquitetura (o que bloqueava tudo)

> Esta é a decisão-cabeça da V4 e pede **ADR próprio** (`2026-07-10-v4-arquitetura-mvp-coortes`,
> a criar no fim da sessão). Resumo abaixo; o "porquê" completo vai no ADR.

### 0.1 O problema
A stack de hoje lê **CSV de uma planilha Google estreita** (abas cobrindo só **abr–jul/2026**).
A coorte precisa de **anos** de clientes e pedidos. Anos de itens (meses de ~120 mil linhas) **não
cabem** numa aba do Google Sheets (teto de ~10 milhões de células). Logo, a fonte da coorte não
pode ser a planilha atual como está.

### 0.2 A decisão (MVP = Opção 2)
1. **O BigQuery entra só como torneira de dado bruto — nada de cálculo nele.** A única consulta
   nova puxa a base **HubSpot** `moon-ventures-data-lake.prod_silver.silver_deals_minimal`
   (filtro `etapa_do_negocio IN ('Shipped', 'Negócio Fechado - Comercial')` — ver §0.6), com
   **apenas as colunas necessárias**, para um
   **arquivo local** no Mac do João (`hubspot_deals.csv`), atualizado **1×/mês** (regra da safra
   fechada — o dado só muda quando um mês encerra). O painel **lê o arquivo local**, como já faz
   com `custos_extra.csv`. Sem credencial no painel, sem latência, sem modo de falha novo.
2. **Todo o cálculo (junção + custo + coorte) roda na plataforma** (pandas), **reaproveitando a
   mesma receita de custo do painel** (correção local `custos_extra.csv` → aba 3.1 se > 0 → aba 3
   se > 0 → senão faltando). Isso garante que o CMV da V4 **bate** com o da Auditoria/painel —
   não há duas verdades de custo (achado 4.4 da revisão).
3. **MC real só na janela atual de itens; 25% estimado antes (Opção 2).** Onde o pedido do
   HubSpot casa com a `Vendas`/`Itens` de hoje (abr–jul/2026), o CMV é **real**. Fora dela, a MC
   de produto é **estimada em 0,25 × valor**. Cada célula da tela é marcada **real** ou
   **estimada**. A Opção 1 (BQ despeja também os itens crus, MC real desde 2022) é a **versão
   seguinte** — fora desta spec.

### 0.3 Chaveamento (o pedido HubSpot → itens → custo)
A base HubSpot **não tem** o gid do pedido Shopify (`gid://shopify/Order/...`). Conferido na
planta-baixa (2026-07-10): a coluna `id` é o **id interno do HubSpot** (ex.: `62484146992`), não
o do pedido. A ponte é pelo **número humano do pedido**:

```
HubSpot.nome  →  Vendas.order_name  →  Vendas.order_id (gid)  →  Itens.order_id  →  Custos.sku
```

- `HubSpot.nome` (ex.: `508767`) = `Vendas.order_name` (mesmo formato do `503184` de hoje) —
  **com uma normalização:** parte dos `nome` vem com **cerquilha** (`#471263`, o padrão Shopify).
  **A leitura remove o `#` inicial** (`nome.lstrip("#")`) antes de casar.
- **Medido contra a planilha real (2026-07-10, base já com Comercial):** na janela `Vendas`
  (abr 23 – jul 10/2026), removendo o `#`, os **`Shipped` casam 99,7%**; os **`Negócio Fechado -
  Comercial` casam 0%** (por construção — `nome` = nome do cliente → sempre estimados, §0.6). A
  ponte do MVP está validada para o ramo casável.
- Para o MVP isso **basta**, porque a aba `Vendas` cobre exatamente a janela dos itens
  (abr–jul/2026). Deals fora da janela **não casam** → caem no ramo estimado (0,25 × valor).
- (Na Opção 1, o casamento histórico exigirá `order_name ↔ order_id` no BQ — problema adiado.)

### 0.4 O que o João precisa preparar (pré-condições de dado)
- **`hubspot_deals.csv`** local: export do BQ (query em §3.5), Shipped, colunas mínimas, base
  inteira (desde 2021). Atualizado no começo de cada mês.
- **Aba `Midia` estendida** cobrindo **2021-04 → hoje** com `investimento_total` (soma FB+Google+
  institucional, **crua, sem imposto**) e a coluna **só-Facebook** (para o imposto de 2026+). É
  mensal-agregável e cabe folgado numa aba.
- As abas `Vendas`/`Itens`/`Custos` seguem **inalteradas** (janela atual = ramo real).

### 0.5 Divergência declarada com o PRODUCT.md
O `PRODUCT.md` V4 §8 promete "CMV real de 2022-01 em diante". **O MVP não entrega isso** — entrega
real só na janela atual. É uma **redução de escopo consciente** (decisão do João: "bora na Opção 2
pra ter um MVP; depois a Opção 1"). O `PRODUCT.md` recebe uma anotação `[MVP vs versão-cheia]`
nessa passagem. A promessa não foi revogada; foi **faseada**.

### 0.6 Universo = `Shipped` + `Negócio Fechado - Comercial` (decisão 2026-07-10)
A base oficial inclui **dois** estágios (medido na base real, 2026-07-10 — 462.108 deals):
- **`Shipped`** (456.708 deals) — pedidos Shopify que **casam com a `Vendas`** pelo `nome` (99,7% na
  janela) → **CMV real** onde há itens.
- **`Negócio Fechado - Comercial`** (5.400 deals, 1,2%) — vendas do time comercial. **Gravam o _nome
  do cliente_ no campo `nome`** (ex.: "Wagner Eduardo"), não um número de pedido → **não casam com a
  `Vendas`** (0% medido) e são **sempre estimados (25%)**, marcados como tal. Quase todos
  **Recompra** de clientes que estrearam em **2021** (só 486 de 5.400 em 2026) → engrossam a cauda
  das safras velhas, quase nada nas últimas 12–18.

**Consequência de escopo:** o universo da coorte é levemente **maior** que o da V1/V2 (que é só a
`Vendas`/`Shipped`) — a coorte é uma visão de **valor do cliente** que inclui a compra comercial. A
amarração da MC **real** segue sendo só sobre os deals casáveis (`Shipped` na janela de itens).
*Decisão do João: manter o Comercial (é valor real do cliente), sempre estimado.*

---

## 1. Resumo em 1 parágrafo

A V4 acrescenta ao painel uma **terceira página** — a **aba de coortes** — que responde a uma
pergunta que nenhuma tela anterior respondia: *cada **safra** de clientes novos (a turma que fez a
1ª compra num mês) **se pagou** ao longo do tempo, e em quanto tempo?* Ela troca a lógica de
"período fechado" por "seguir a mesma turma mês a mês": usa o **HubSpot** (base oficial de cliente,
chave `e_mail`) para agrupar os clientes por **mês da 1ª compra** (`data_primeira_compra`,
cross-canal) e, para cada safra, acumula a **Margem de Contribuição por cliente** conforme a idade
da turma cresce (m+0, m+1, …) — a mídia inteira do mês pesa no **m+0** (convenção 100% mídia →
novos, herdada da V2), e a recompra vai somando adiante. **Cruzar o zero = a turma se pagou.** A
tela mostra três coisas: um **triângulo** (`Safra | Clientes | CAC | m+0 | m+1 | …`), a **curva de
payback** (últimas 12 safras) e um **seletor de safra** que dirige os KPIs de cabeçalho (payback,
CAC, MC/cliente até hoje, recompra em 90 dias). Neste **MVP**, a MC de produto é **real** só na
janela atual de itens (abr–jul/2026) e **estimada em 25% do valor** antes disso — cada célula
marcada como tal —, e a curva leva o rótulo honesto **"MC parcial"** (não desconta CX, juros de
estoque nem criativo, que ficam de fora desta versão). É **só leitura**, roda local, e as abas de
MC (V1) e de aquisição (V2) **não mudam**.

---

## 2. Comportamento funcional

### 2.1 Caminho feliz
1. João abre o painel (`streamlit run painel.py`) e clica em **"Coortes"** no menu lateral (a
   página nova, ao lado de "Aquisicao" e "Auditoria de custos").
2. A página lê o **`hubspot_deals.csv`** local + as abas (`Vendas`, `Itens`, `Custos`, `Midia`),
   tudo cacheado (mesmo `@st.cache_data` das outras páginas).
3. Para **cada safra** (mês de `data_primeira_compra`), o sistema:
   - conta **N_S** = clientes distintos (`e_mail`) da safra;
   - calcula, por **idade** (`meses_desde_primeira_compra`), a **MC de produto** dos deals daquela
     idade (real via ponte se o pedido está na janela; senão `0,25 × valor`), soma e divide por N_S;
   - no **m+0**, subtrai também `Ad Spend(mês da safra) ÷ N_S` (o CAC da safra);
   - **acumula** as incrementais → a série da **MC acumulada por cliente**.
4. O sistema aplica a regra de **safra fechada**: só entram células de **mês-calendário já
   encerrado** (hoje 2026-07-10 → o último mês fechado é **junho/2026**; julho ainda corre).
5. Desenha, de cima para baixo:
   - **Cabeçalho de KPIs** da safra selecionada no seletor (padrão: a safra fechada mais recente):
     **payback, CAC, MC/cliente até hoje, recompra em 90 dias**.
   - **Curva de payback**: eixo X = meses desde a 1ª compra, eixo Y = MC acumulada por cliente,
     uma linha por safra (padrão: **últimas 12 safras fechadas**), com a **linha do zero** marcada
     e a safra selecionada **destacada**. Rótulo do gráfico: **"MC parcial por cliente"**.
   - **Triângulo** (tabela): uma linha por safra, colunas `Safra | Clientes | CAC | m+0 | m+1 | …`,
     célula **verde se ≥ 0 / vermelha se < 0** (a linha do zero), e marca visual de **estimada**
     (ex.: célula em itálico/asterisco) vs **real**.
6. João lê: se as safras recentes cruzam o zero **mais cedo** que as antigas, a aquisição está
   ficando mais eficiente (tendência de "acelerar"); se demoram mais, o contrário.

### 2.2 Caminhos alternativos
- **Trocar a safra no seletor:** os KPIs de cabeçalho e o destaque na curva passam a ser da safra
  escolhida. Recalcula do cache; sem reler o CSV.
- **Ampliar a curva:** um controle "quantas safras mostrar" (padrão 12) permite ver mais safras
  antigas (com a ressalva de era — §6).
- **Atualizar dados:** botão "🔄 Atualizar dados" limpa o cache e relê CSV + abas (mesmo cache
  compartilhado das outras páginas). Se o `hubspot_deals.csv` estiver velho, ver 2.3.
- **Voltar às outras abas:** menu lateral; nada de estado perdido (cada página tem o seu seletor).

### 2.3 Casos de erro visíveis ao usuário
| Quando | O que João vê | Como recupera |
|---|---|---|
| `hubspot_deals.csv` **ausente** | Mensagem clara: "Arquivo de coortes não encontrado — rode a atualização mensal do HubSpot." A página para. | Rodar o export do BQ |
| `hubspot_deals.csv` **velho** (mês do arquivo < último mês fechado) | Faixa amarela: "Triângulo de {mês do arquivo}; rode a atualização para incluir {último mês fechado}." A tela **ainda desenha** com o que há. | Rodar o export |
| Falha ao ler as abas (Google instável / link mudou) | A mesma mensagem clara do painel (`ErroDeDados`); a página para. | Aguardar e Atualizar |
| Coluna essencial ausente no CSV (`e_mail`, `nome`, `data_primeira_compra`, `meses_desde_primeira_compra`, `valor`, `data_de_fechamento`) | `ErroDeDados` específico nomeando a coluna. A página para. | Corrigir o export |
| Aba `Midia` sem cobrir o mês de uma safra | CAC daquela safra = **"—"** + a safra fica marcada "sem mídia"; as demais seguem. | Estender a aba `Midia` |
| Nenhuma safra fechada no recorte | "Sem safras fechadas para exibir." e para. | — (informação) |

---

## 3. Dados envolvidos

### 3.1 Entidades lidas
- **`hubspot_deals.csv`** (local, **nova fonte**) — os deals `Shipped` + `Negócio Fechado -
  Comercial` (ver §0.6) com a identidade de cliente e a coorte já prontas. Colunas em 3.3.
- **Aba `Vendas`** — `order_name`, `order_id`, `net_revenue`, `data` (ramo **real**: casar o deal e
  pegar a receita/CMV do pedido na janela atual).
- **Aba `Itens`** — `order_id`, `sku`, `quantidade` (CMV real da janela).
- **Aba `Custos`** (3.1 principal + 3 fallback) — `sku`, `valor_custo`.
- **Aba `Midia`** (**estendida — confirmada 2026-07-10, 2021-03→2026-12**) — `data`, `investimento_total`, `fb_investimento` (fatia FB p/ o imposto de 2026+).
- **`custos_extra.csv`** (local) — correções de custo, aplicadas por cima, como hoje.

### 3.2 Entidades criadas / atualizadas / deletadas
**Nenhuma escrita pelo painel.** A V4 é só leitura (como V1/V2). O `hubspot_deals.csv` é escrito
por um **passo externo** (o export do BQ que o João roda), **não** pelo painel.

### 3.3 Campos novos (do `hubspot_deals.csv`)
| Campo | Tipo | Origem | Uso | Validação |
|---|---|---|---|---|
| `e_mail` | texto | HubSpot | chave de cliente (N_S, recompra) | não-vazio; normaliza `.strip().lower()` |
| `nome` | texto | HubSpot | ponte → `Vendas.order_name` (ramo real) | **remove o `#` inicial** (`lstrip("#")`), depois casa por igualdade. Match medido 99,7% na janela |
| `valor` | número | HubSpot | receita do deal (ramo estimado; e conferência vs `net_revenue`) | > 0 |
| `data_de_fechamento` | data | HubSpot | data do pedido | `AAAA-MM-DD` |
| `tipo_de_venda` | texto | HubSpot | "Primeira Compra"/"Recompra" (checagem, recompra 90d) | grafia exata |
| `data_primeira_compra` | data | HubSpot | **âncora da safra** (cross-canal) | `AAAA-MM-DD` |
| `meses_desde_primeira_compra` | inteiro | HubSpot | **idade** (m+0, m+1, …) | ≥ 0 |
| `etapa_do_negocio` | texto | HubSpot | distingue `Shipped` (casável, CMV real na janela) de `Negócio Fechado - Comercial` (sempre estimado) | ∈ {"Shipped", "Negócio Fechado - Comercial"} |

> Colunas do HubSpot **ignoradas** no MVP (existem mas não usamos): `id`, `dealstage`, `descricao`,
> `canal_da_venda*`, `proprietario`, `id_do_contato`, `pedido_cartpanda`, `assinatura__*`,
> `valor_renovacao_*`, etc. Ficam de fora do export para o arquivo ser enxuto.

### 3.4 Migrations necessárias
Não há banco. As "migrações" são de **contrato de leitura** e de **preparo de dado**:
- **`dados.py`** ganha `carregar_hubspot()` (lê o CSV local, normaliza datas/números/e-mail) e o
  `Dados` (ou um novo container) passa a carregar os deals. `carregar_tudo` passa a **exigir** o
  arquivo — ausência = `ErroDeDados` clara (não quebra as outras abas, mas a de coortes não roda).
- **Aba `Midia`** estendida (dado, não código): 2021-04→hoje, `investimento_total` + só-FB.
- **Reversível?** Sim. Reverter = apagar `pages/3_Coortes.py`, o módulo de coorte e
  `carregar_hubspot`; o `hubspot_deals.csv` e a extensão da `Midia` são inertes para V1/V2.
- **Impacto em dado existente:** nenhum. V1 e V2 leem as mesmas colunas de sempre.

### 3.5 Query de export (o João roda 1×/mês; leitura pura)
```sql
-- Export mensal → hubspot_deals.csv (só o necessário, base inteira, só Shopify)
SELECT
  e_mail, nome, valor, data_de_fechamento, tipo_de_venda, etapa_do_negocio,
  data_primeira_compra, meses_desde_primeira_compra
FROM `moon-ventures-data-lake.prod_silver.silver_deals_minimal`
WHERE etapa_do_negocio IN ('Shipped', 'Negócio Fechado - Comercial')
  AND e_mail IS NOT NULL
  AND data_primeira_compra IS NOT NULL;
```

---

## 4. Regras de negócio explícitas

> Notação: safra **S** = mês-calendário de `data_primeira_compra`; **N_S** = nº de clientes da
> safra; idade **m** = `meses_desde_primeira_compra`. Deduções e % são as mesmas do painel
> (`cascata.PARAMETROS`), incidindo sobre a receita do deal.

- **R1. Fonte da coorte = HubSpot `Shipped` + `Negócio Fechado - Comercial`, chave `e_mail`.** O
  universo é o `hubspot_deals.csv` (ver §0.6). Não se mistura TikTok/assinatura.

- **R2. Safra = mês de `data_primeira_compra` (cross-canal).** A safra de um deal é
  `AAAA-MM` de `data_primeira_compra`. Vem pronta da base; não recomputamos. Um cliente pertence a
  **uma** safra (a 1ª compra é única). **Viés cross-canal aceito e declarado** (R12).

- **R3. N_S = clientes distintos (`e_mail`) da safra S** presentes no arquivo (i.e., com ≥1 deal
  Shopify). É o **denominador** de toda métrica por cliente da safra. Cliente que estreou fora do
  Shopify e nunca comprou Shopify **não** aparece (a base é só Shopify) — não infla N_S.

- **R4. Idade = `meses_desde_primeira_compra`.** m+0 = mês da 1ª compra; m+1 = seguinte; etc. Vem
  pronta da base.

- **R5. MC de produto de um deal (antes da mídia):**
  - **Ramo real** (o `nome` casa com `Vendas.order_name` da janela atual): `MC_produto =
    net_revenue − (Σ deduções% × net_revenue) − CMV_real`, onde `CMV_real = Σ(valor_custo ×
    quantidade)` dos itens do pedido, com a **mesma receita de custo do painel** (correção local →
    3.1 se > 0 → 3 se > 0 → senão faltando; custo 0 = faltando; inclui brindes).
  - **Ramo estimado** (não casa: deal fora da janela de itens **ou** deal `Negócio Fechado -
    Comercial`, cujo `nome` é o nome do cliente e nunca casa — §0.6): `MC_produto = 0,25 × valor`.
    **Sem deduzir de novo** — os 25% já são a margem de produto líquida (decisão 2026-07-10; corrige
    a fórmula do `PRODUCT.md` §6). Marcado **estimado**.

- **R6. Ad Spend do mês (mídia da safra), com imposto condicional:**
  - Base = `investimento_total` do mês (soma FB+Google+institucional, crua).
  - **Mês ≥ 2026-01:** `Ad Spend = investimento_total + fb_investimento × 0,1215/0,8785` (embrutece
    só a fatia do FB; o imposto de 12,15% passou a valer em **2026-01-01**). *(Aba `Midia` confirmada
    2026-07-10: `data, mes, fb_investimento, google_investimento, google_institucional_investimento,
    investimento_total`, cobrindo 2021-03→2026-12.)*
  - **Mês < 2026-01:** `Ad Spend = investimento_total` (não havia imposto).
  - **Invariante de consistência:** para meses de 2026, essa fórmula é **idêntica** à Ad Spend do
    painel/V2 (`fb/(1−0,1215) + google + institucional`) — a V4 só **estende para trás** a mesma
    definição, sem imposto no passado.

- **R7. CAC por safra = `Ad Spend(mês-calendário de S) ÷ N_S`.** R$/cliente. É a 2ª coluna do
  triângulo e o "mergulho" do m+0. Se a `Midia` não cobre o mês de S → CAC = "—" e a safra marcada
  "sem mídia" (não zera à toa).

- **R8. Convenção 100% mídia → mês 0 da safra (herdada da V2).** Toda a mídia do mês-calendário
  pesa no m+0 da safra **daquele mês**, inclusive remarketing. Não se fatia aquisição × remarketing
  (escopo parkeado). Premissa que a leitura de tendência exige: **proporção remarketing/aquisição
  estável entre safras** (R12).

- **R9. MC incremental e acumulada por cliente:**
  - `MC_incremental(S, m) = [Σ MC_produto dos deals da safra S com idade m] ÷ N_S`, e **no m=0**
    subtrai também `Ad Spend(mês de S) ÷ N_S` (= o CAC da safra).
  - `MC_acumulada(S, m) = Σ_{k=0..m} MC_incremental(S, k)`. **Unidade:** R$/cliente. **Cruzar o
    zero = a turma se pagou.**

- **R10. Payback(S) = menor m com `MC_acumulada(S, m) ≥ 0`.** Em meses. Se a safra ainda não
  cruzou o zero (ou é imatura) → **"—"**. **Nunca extrapola** (não inventa mês futuro).

- **R11. Safra fechada (só mês encerrado).** Uma célula (S, m) só aparece se o **mês-calendário
  correspondente já terminou**. Hoje 2026-07-10 → julho não conta; o último mês com m+0 novo é
  **junho/2026**. Vale para toda a tabela e a curva; nada de mês correndo.

- **R12. Vieses declarados (não são bugs; são escopo):**
  - **Cross-canal:** a safra usa a 1ª compra em qualquer canal, mas MC/mídia são só Shopify → para
    quem estreou fora do Shopify, o m+0 fica incompleto e o CAC **levemente otimista**. Aceito
    porque Shopify é >95% das vendas; **tamanho a medir** (query §9).
  - **Mídia blended no m+0** (R8) → a V4 é instrumento de **tendência entre safras**, não de
    veredito absoluto de payback (isso é V5/V6).
  - **Custo de hoje sobre venda antiga** (no ramo real) e **cobertura de custo de SKU antigo** →
    distorcem safras velhas em direções opostas; por isso a decisão se lê nas **últimas 12–18
    safras**, onde os dois efeitos são ~zero.

- **R13. Recompra em 90 dias(S) = `nº de clientes de S com ≥1 compra Shopify adicional em até 90
  dias da 1ª compra ÷ N_S`.** Janela **fixa** (comparabilidade entre safras). Na tela, rótulo
  **sempre explícito** ("recompra em 90 dias"), nunca um "%" solto. *(O número da janela — 90 vs
  180 — é calibrável por query §9; errar não quebra a V4, só o cartão.)*

- **R14. MC/cliente até hoje(S) = `MC_acumulada(S, m*)`**, com **m\*** = maior idade **fechada** da
  safra. R$/cliente. É o "LTV até agora" da safra.

- **R15. Rótulo "MC parcial".** A curva e o triângulo levam o rótulo **"MC parcial por cliente"** e
  uma nota: *"não desconta CX, juros de estoque nem criativo; parte da MC é estimada (25%) fora da
  janela de itens atual."* A linha do zero **não promete** o que não mede. *(CX, juros de estoque e
  criativo ficam **de fora** desta versão — decisão do João 2026-07-10.)*

- **R16. As abas de MC (V1) e de aquisição (V2) não mudam.** A V4 só **acrescenta**:
  `carregar_hubspot` em `dados.py`, um módulo/funsão de coorte, e a página nova. Nada existente
  muda de comportamento.

---

## 5. UI/UX

### 5.1 Telas afetadas
- **Nova:** `pages/3_Coortes.py` — a aba de coortes (página multipage, menu lateral).
- **Inalteradas:** `painel.py`, `pages/1_Auditoria_de_custos.py`, `pages/2_Aquisicao.py`.

### 5.2 Componentes novos necessários
- **`dados.py`** — `carregar_hubspot() -> DataFrame` (lê `hubspot_deals.csv`, normaliza
  datas/números/e-mail); ganchos de leitura da `Midia` estendida (agregar diário→mensal).
- **`coortes.py`** (módulo novo) — `calcular_coortes(dados, ...) -> ResultadoCoortes`: monta o
  triângulo (safra × idade → MC acumulada/cliente + flag real/estimada), N_S, CAC, payback,
  recompra 90d por safra. Reusa a receita de custo do painel (helper compartilhado de CMV por
  pedido — extrair de `cascata`/`detalhar_pedidos` o cálculo por `order_id`). Dataclass nova
  **`ResultadoCoortes`**.
- **`pages/3_Coortes.py`** — a UI: cabeçalho de KPIs (seletor de safra), curva (matplotlib/Altair,
  o que o painel já usa), triângulo (tabela estilizada, verde/vermelho + marca real/estimada),
  barra de alertas/notas ("MC parcial", arquivo velho, sem mídia). Reusa `@st.cache_data` e os
  helpers `reais`/`numero`.

### 5.3 Estados visuais
| Estado | O que aparece |
|---|---|
| **Loading** | Spinner "Lendo coortes…" |
| **Vazio** (sem safra fechada) | "Sem safras fechadas para exibir." e para |
| **Arquivo ausente** | Erro claro "rode a atualização mensal do HubSpot"; para |
| **Arquivo velho** | Faixa amarela (2.3) + tela desenha com o que há |
| **Sem mídia** num mês de safra | CAC "—" naquela safra; nota; demais seguem |
| **Erro** de leitura das abas | Mensagem clara do `ErroDeDados`; para |
| **Sucesso** | Cabeçalho de KPIs + curva "MC parcial" + triângulo |

**Linha do zero:** células/curva **verde** (`#1f7a3d`, como a MC do painel) quando MC acumulada
≥ 0, **vermelho** quando < 0. **Marca de estimada:** célula em itálico com asterisco (`*`) e
legenda "‪*‬ MC estimada (25%)"; célula **real** em peso normal.

### 5.4 Permissões
- **João (único usuário):** vê tudo, edita nada (só leitura). — `PRODUCT.md` §2.
- **CEO / lideranças:** fora do escopo (sem login multiusuário), como na V1/V2.

---

## 6. Casos de borda específicos desta feature

| Caso | Comportamento esperado |
|---|---|
| Safra imatura (poucos meses fechados) | Mostra só os meses fechados; payback = "—"; **não** extrapola a curva |
| Safra que ainda não cruzou o zero | Payback = "—"; a linha segue no vermelho até onde há dado |
| Deal sem casar na janela (a maioria, no MVP) | Ramo estimado `0,25 × valor`; célula marcada **estimada** |
| Deal na janela com SKU sem custo | Herda o alerta de SKU sem custo do painel; célula real mas com nota "custo faltando" |
| Cliente que estreou fora do Shopify | m+0 Shopify incompleto; CAC da safra otimista (viés R12); recompra dele soma na cauda da safra dele |
| Mês da safra sem mídia na `Midia` | CAC "—" para a safra; MC acumulada ainda desenha (só sem o mergulho de mídia no m+0) |
| `meses_desde_primeira_compra` inconsistente para o mesmo `e_mail` (pipeline recomputou) | Usa o valor do próprio deal; se N_S de uma safra fechada mudar entre leituras, **guarda de deriva** avisa (§8) |
| Julho/2026 (mês corrente) | Não aparece como safra com m+0; entra só quando julho fechar (regra R11) |
| `valor` ≠ `net_revenue` no ramo real | Usa `net_revenue` (fonte do painel) no ramo real; `valor` só no estimado; o degrau na emenda é medido (query §9) |
| Curva com >12 safras selecionadas | Desenha, com aviso de "eras não comparáveis" antes de ~2024 (mix 20×) |
| Atualizar duas vezes / trocar safra no meio | Sem efeito colateral — leitura pura, cache idempotente |

---

## 7. Critérios de aceite testáveis

- [ ] **CA1.** Ao abrir "Coortes", o sistema mostra cabeçalho de KPIs + curva + triângulo, sem
  exceção, para os dados atuais.
- [ ] **CA2.** O triângulo tem uma linha por **safra fechada** e as colunas `Safra | Clientes |
  CAC | m+0 | m+1 | …`; **nenhuma** célula de mês-calendário ainda em curso aparece (R11).
- [ ] **CA3.** Para uma safra S, `MC_acumulada(S, m)` = soma das incrementais de 0..m, e o **m=0**
  inclui `− Ad Spend(mês de S) ÷ N_S`; conferível célula a célula contra um caso montado à mão.
- [ ] **CA4.** Célula com MC acumulada ≥ 0 aparece **verde**; < 0, **vermelha**.
- [ ] **CA5.** Célula do **ramo estimado** aparece marcada (itálico/asterisco); do **ramo real**,
  peso normal. Um deal da janela (abr–jul/2026) cai no real; um de 2023 cai no estimado.
- [ ] **CA6.** `CAC(S) = Ad Spend(mês de S) ÷ N_S`; para um mês de 2026, a Ad Spend usada é
  **idêntica** à do painel (`fb/(1−0,1215)+google+inst`); para um mês de 2025, é o
  `investimento_total` **sem** imposto (R6).
- [ ] **CA7.** `Payback(S)` = menor m com MC acumulada ≥ 0; safra que não cruzou o zero mostra
  **"—"** (nunca um número extrapolado).
- [ ] **CA8.** `Recompra em 90 dias(S)` calculada na janela fixa de 90 dias, com **rótulo
  explícito** na tela (não um "%" solto).
- [ ] **CA9.** Curva mostra as **últimas 12 safras fechadas** por padrão, com a **linha do zero**
  e a safra do seletor **destacada**; título "MC parcial por cliente".
- [ ] **CA10.** Com o `hubspot_deals.csv` **ausente**, a página mostra a mensagem de "rode a
  atualização" e não quebra as outras abas.
- [ ] **CA11.** Com o arquivo **velho** (mês < último fechado), aparece a faixa amarela e a tela
  ainda desenha.
- [ ] **CA12.** As abas **painel** (V1) e **Aquisicao** (V2) seguem **idênticas** — nenhum número
  muda ao introduzir a V4.
- [ ] **CA13.** A página **não escreve** na planilha nem em arquivo (só leitura).

> **Referência de sanidade (a preencher ao construir):** somar N_S de todas as safras deve dar o
> total de clientes distintos (`e_mail`) do arquivo; a soma da MC real da janela abr–jul/2026 deve
> **amarrar** com a MC dos mesmos pedidos na Auditoria/painel. Servem para conferir, não como
> valores fixos de teste.

---

## 8. Riscos e impactos

### Módulos tocados
- **`carregador-de-dados` (`dados.py`)** — **acrescenta** `carregar_hubspot` e a leitura da `Midia`
  estendida; não altera as leituras de V1/V2. Risco: arquivo local ausente/velho → tratado com
  mensagem clara (2.3), sem contaminar as outras abas.
- **`calculo-cascata` (`cascata.py`)** — **não muda** `calcular`/`calcular_aquisicao`. Extrai-se um
  **helper de CMV por `order_id`** (o cálculo já existe em `detalhar_pedidos`) para o módulo de
  coorte reusar a **mesma receita de custo** — refactor de extração, com teste de que a Auditoria
  segue idêntica.
- **`coortes.py` + `pages/3_Coortes.py`** — novos; risco de regressão em V1/V2 **baixo** (nada
  existente muda).

### Reversibilidade
Alta. Reverter = apagar a página e o módulo de coorte, remover `carregar_hubspot`. `hubspot_deals.csv`
e a extensão da `Midia` são inertes para V1/V2. Nenhuma migração de dado.

### Dado em produção afetado
Nenhum — não há escrita; a planilha e o BQ são fontes externas só-leitura; o CSV é gerado por passo
externo.

### Riscos de modelagem (declarados)
- **MVP é majoritariamente estimado (25%).** Como a janela real é ~4 meses, a maioria das células
  vem do estimado. **Lê-se o MVP como "o motor funciona", não como o payback real** — a tela marca
  cada célula. *(Alternativa considerada: MVP 100% estimado, sem o ramo real; mantido o ramo real a
  pedido do João — reaproveita dado que já temos, ao custo de um triângulo em mosaico.)*
- **MC parcial** (R15): faltam CX, juros de estoque e criativo — **fora de escopo desta versão** —,
  então a curva cruza o zero **cedo demais**. Rótulo honesto na tela; sem alvo importado.
- **Vieses R12** (cross-canal, mídia blended, era do mix): a decisão se lê nas **últimas 12–18
  safras**; a comparação com eras pré-2024 é memória, não decisão.
- **Deriva de `data_primeira_compra`** (campo derivado do pipeline; merge de contatos no HubSpot
  pode reescrever safra retroativamente): **guarda de deriva** — guardar a foto mensal de N por
  safra e **avisar se uma safra fechada mudar de tamanho** entre leituras (no espírito da guarda
  silenciosa da V2). Perguntar ao time de Dados como o campo é derivado.

### Inconsistências documentais a corrigir (não bloqueiam a spec)
- **`ROADMAP.md` V4** promete "custo cheio" e "Combina V2 + **V3**" — a V3 foi esvaziada. **Corrigir
  antes/junto da spec** (senão a implementação herda promessa revogada).
- **`PRODUCT.md` §6** (fórmula dos 25%) — corrigir para `MC_produto = 0,25 × valor` (sem deduzir de
  novo). E anotar §8 com `[MVP vs versão-cheia]` (o MVP não entrega real desde 2022 — §0.5).

---

## 9. Validações pendentes (rodar durante o build; o João roda, eu preparo)

> Nenhuma **bloqueia** o desenho (o chaveamento, que bloqueava, já foi resolvido). São de
> **calibração** — afinam números de uma spec que já fica de pé.

| # | Query | Decide | Onde entra |
|---|---|---|---|
| V1 | ~~`valor` × `net_revenue` na janela~~ **MEDIDO (2026-07-10):** casamento **99,7%** (removendo o `#`); nos 37.729 pedidos casados, **Σvalor/Σnet = 1,011** e delta mediano por pedido **0%** (p75 +3,75%, p90 +6,89%; poucos outliers extremos onde `net` é ~0). Emenda real↔estimado **pequena** (~1% no agregado) | R5: usar `net_revenue` no ramo real, `valor` no estimado; degrau ~1% documentado | **feito** |
| V2 | % de clientes por safra cuja 1ª compra não está no `Shipped` (estreou fora do Shopify) | tamanho e concentração do viés cross-canal (R12); portão ~10% | eventual coluna "% estreou fora" |
| V3 | Distribuição do tempo até a 2ª compra Shopify (mediana, p75) | se 90 dias é a janela certa (R13); talvez mostrar 90d **e** 180d | rótulo do cartão |

> As de **viabilidade** do histórico (cobertura de custo de SKU antigo; ponte `order_name↔order_id`
> no BQ; mídia mensal desde 2022) pertencem à **Opção 1** (versão-cheia), **fora deste MVP**.

---

## Verificação da spec (checklist do trilho)

- [x] Glossário respeitado (mesmos termos do `PRODUCT.md`/`CLAUDE.md`; "MC", nunca "lucro").
- [x] Cada caminho da seção 2 vira ≥ 1 critério de aceite (seção 7).
- [x] Casos de borda específicos, não genéricos (seção 6).
- [x] Decisão de arquitetura explícita e com ADR próprio pendente (seção 0).
- [x] "Migração" (contrato de leitura + preparo de dado) descrita com reversibilidade (3.4).
- [x] Riscos citam módulos pelo nome do `ARCHITECTURE.md` (seção 8).
- [x] Divergências com `PRODUCT.md`/`ROADMAP.md` relatadas, não silenciadas (0.5, 8).
- [x] Números rastreados à fonte (HubSpot `silver_deals_minimal`, abas atuais); nenhum inventado.
