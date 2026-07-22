# Spec — V2: Aba de Aquisição (MC de clientes novos)

> Spec de construção (Modo B — toca dinheiro: MC-novos, CAC, aROAS).
> Base de domínio: `PRODUCT.md` (V2, handoff 2026-07-09) + `docs/ROADMAP.md` (V2).
> Discovery: `docs/sessions/2026-07-09-discovery-v2-aquisicao.md`.
> Decisões desta sessão: `docs/sessions/2026-07-09-spec-v2-aba-aquisicao.md` (perguntas críticas respondidas).
>
> **Glossário:** todos os termos abaixo (`customer_type`, `Primeira Compra`, `Recompra`,
> **MC-novos**, **CAC**, **aROAS**, **convenção 100% mídia → novos**, **linha do zero**,
> **sem classificação**) são usados exatamente como definidos no `PRODUCT.md` seção 3.
> **Vocabulário:** MC, **nunca "lucro"**.

---

## 1. Resumo em 1 parágrafo

A V2 acrescenta ao painel uma **página nova** — a **aba de aquisição** — que responde a
uma única pergunta: *a aquisição de clientes novos está gerando **Margem de Contribuição
positiva já na primeira compra**?* Ela lê o carimbo nativo da Shopify (`customer_type`,
coluna já presente na aba `Vendas`), separa os pedidos de **Primeira Compra** do resto e
calcula, **só sobre esses pedidos**, uma cascata de MC idêntica à do painel — Vendas-novos
menos deduções, CMV-novos e custos variáveis → Lucro Bruto-novos — e então subtrai **toda**
a mídia do período (**convenção 100% mídia → novos**), chegando à **MC-novos**. Mostra 5
cartões (**MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS**), uma **mini-cascata de
novos** que explica como a MC-novos se formou, e pinta a MC-novos de **verde se ≥ 0,
vermelha se < 0** (a **linha do zero**). O painel de MC da V1 **não muda**. É só leitura,
roda local, e reusa toda a maquinaria de recorte/custo/mídia que já existe.

---

## 2. Comportamento funcional

### 2.1 Caminho feliz

1. João abre o painel (`streamlit run painel.py`) e clica em **"Aquisicao"** no menu lateral
   (a página nova, ao lado de "Auditoria de custos").
2. A página mostra o seletor de período (padrão: este mês até hoje), **independente** do
   seletor do painel de MC.
3. João escolhe um período de **dias fechados**.
4. A página lê a planilha (cacheada, mesmo cache do painel), aplica o **mesmo recorte** do
   painel (`cascata._recorte_pedidos`: só Shopify, só `PAID`, exclusões AnjosFrach/pontuais)
   e **parte os pedidos por `customer_type`**.
5. Calcula, só sobre os pedidos **Primeira Compra**: Vendas-novos, Pedidos-novos,
   deduções-novos (% sobre Vendas-novos), CMV-novos, custos variáveis-novos → **Lucro
   Bruto-novos**; depois **MC-novos = Lucro Bruto-novos − Ad Spend total**.
6. Calcula **CAC = Ad Spend total ÷ Pedidos-novos** e **aROAS = Vendas-novos ÷ Ad Spend total**.
7. Desenha, de cima para baixo:
   - **Número-herói: a MC-novos**, verde (≥ 0) ou vermelha (< 0) — a linha do zero, com o
     subtítulo "Lucro Bruto-novos − Mídia paga (inteira)".
   - **5 cartões:** MC-novos · Vendas-novos · Pedidos-novos · CAC · aROAS.
   - **Mini-cascata de novos** (tabela tipo DRE): Vendas-novos → deduções → CMV-novos →
     custos variáveis → Lucro Bruto-novos → **Mídia paga (inteira)** → MC-novos.
8. João lê a resposta: se a MC-novos é verde, a aquisição **se paga na 1ª compra** no período.

### 2.2 Caminhos alternativos

- **Trocar o período:** João muda as datas; a página recalcula (reusa o cache de leitura da
  planilha; só o cálculo roda de novo). Igual ao painel.
- **Atualizar dados:** botão "🔄 Atualizar dados" limpa o cache e relê a planilha (mesmo
  comportamento e mesmo cache compartilhado do painel — atualizar numa página vale na outra).
- **Voltar ao painel de MC:** João clica em "painel" no menu lateral. Nada de estado
  perdido; cada página tem o seu próprio seletor.
- **SKU sem custo entre os novos:** herda o comportamento do painel — **alerta amarelo** no
  topo da página avisando que a MC-novos pode estar **superestimada** (custo faltando).
  Nesta V2 a página **não** oferece o editor de custos (fica no painel de MC); o alerta só
  aponta. *(Ver R11.)*

### 2.3 Casos de erro visíveis ao usuário

| Quando | O que João vê | Como recupera |
|---|---|---|
| Falha ao ler a planilha (Google instável / link mudou) | A mesma mensagem clara do painel (`ErroDeDados`), e a página para | Aguardar e clicar em Atualizar |
| Período sem nenhum movimento (0 pedidos, 0 mídia) | "Sem dados no período." e a página para | Escolher outro período |
| Período **sem pedidos novos** (Pedidos-novos = 0) | CAC = **"—"** + nota "sem clientes novos no período". A MC-novos ainda aparece (será a mídia negativada, se houve mídia) | Escolher outro período; é informação, não erro |
| Período **sem mídia** (Ad Spend = 0) | aROAS = **"—"** + nota "sem mídia no período" (nunca "∞" nem algo que pareça aquisição de graça). MC-novos e CAC seguem válidos | — |
| `customer_type` com rótulo inesperado (nem "Primeira Compra", nem "Recompra", nem vazio) | Aviso amarelo "N pedidos com carimbo desconhecido — tratados como sem classificação" | Sinaliza problema de fonte a montante |
| A amarração das 3 faixas **não fecha** (novos + recompra + sem-classificação ≠ total) | Aviso amarelo "As faixas de cliente não somam o total de pedidos (checagem interna)" | Sinaliza problema de fonte a montante |
| Coluna `customer_type` **ausente** da aba `Vendas` | `ErroDeDados`: "A aba `Vendas` está sem a coluna `customer_type` — a aba de aquisição precisa dela." | Corrigir a extração da planilha |

---

## 3. Dados envolvidos

### 3.1 Entidades lidas
Todas do `ARCHITECTURE.md` seção 3 — **nenhuma nova**:
- **Aba `Vendas`** — `order_id`, `order_name`, `data`, `net_revenue` **+ `customer_type` (novo, ver 3.3)**.
- **Aba `Itens`** — `order_id`, `data`, `sku`, `quantidade` (para o CMV-novos).
- **Aba `Custos`** (3.1 principal + 3 fallback) — `sku`, `valor_custo`.
- **Aba `Midia`** — `fb_investimento`, `google_investimento`, `google_institucional_investimento`.
- **`custos_extra.csv`** (local) — correções de custo, aplicadas por cima, como hoje.

### 3.2 Entidades criadas/atualizadas/deletadas
**Nenhuma.** A V2 é só leitura, como a V1. Não escreve na planilha nem cria arquivo novo.

### 3.3 Campos novos
| Campo | Tipo | Onde | Default | Validação |
|---|---|---|---|---|
| `customer_type` | texto | acrescentado ao DataFrame `Dados.vendas` (lido de `Vendas.customer_type`) | `""` (vazio) | Normalizado com `.strip()`. Valores esperados: `"Primeira Compra"`, `"Recompra"`, `""`. Qualquer outro → tratado como sem classificação + aviso (R7). |

Nenhum campo novo em `Itens`, `Custos` ou `Midia`.

### 3.4 Migrations necessárias
Não há banco. A única "migração" é de **contrato de leitura**:
- **`dados.carregar_vendas`** passa a **exigir e mapear** a coluna `customer_type` (hoje ela
  lê só 4 colunas e ignora essa 5ª). Confirmado na fonte ao vivo (2026-07-09): a coluna
  existe, 5ª posição, valores `Primeira Compra` / `Recompra` / vazio.
- **Reversível?** Sim. É acrescentar uma coluna ao DataFrame e uma função nova em
  `cascata.py`; nada do existente muda de comportamento. Reverter = remover a página, a
  função `calcular_aquisicao` e o mapeamento da coluna.

---

## 4. Regras de negócio explícitas

> As percentagens de dedução e custo variável são as **mesmas** do painel (`cascata.PARAMETROS`),
> aplicadas agora sobre a **Vendas-novos**. Toda linha em % incide sobre a Vendas **da faixa**
> (aqui, a Vendas-novos) — igual ao `PRODUCT.md` seção 6.

- **R1. Recorte idêntico ao painel.** A aba de aquisição parte **exatamente** do mesmo recorte
  do painel: `cascata._recorte_pedidos` (só pedidos da aba `Vendas` = só Shopify/`PAID`; com as
  exclusões AnjosFrach e pontuais do ADR 2026-07-02; itens restritos aos `order_id` da `Vendas`
  do período). A partição por `customer_type` acontece **depois** desse recorte. Consequência:
  os totais da aba de aquisição (novos + recompra + sem-classificação) amarram com os do painel.

- **R2. Cliente novo = `customer_type == "Primeira Compra"`.** Um pedido é de **cliente novo**
  se, e só se, o carimbo (após `.strip()`) for a string exata `"Primeira Compra"`. Match
  sensível a acento e a maiúsculas (grafia confirmada na fonte). Cada cliente novo tem
  exatamente um pedido de Primeira Compra → **Pedidos-novos = clientes novos adquiridos**.

- **R3. Vendas-novos = Σ `net_revenue` dos pedidos Primeira Compra** do período (R$).

- **R4. Pedidos-novos = contagem de `order_id` distintos** com `customer_type == "Primeira
  Compra"` no período (inteiro).

- **R5. CMV-novos = Σ (`valor_custo` × `quantidade`)** dos itens cujos `order_id` são de
  pedidos Primeira Compra. Usa a **mesma junção `Itens × Custos`** e a **mesma regra de fonte
  de custo** do painel (correção local → aba 3.1 se > 0 → aba 3 se > 0 → senão faltando).
  Inclui brindes. Custo 0 = faltando, não grátis.

- **R6. Deduções-novos e custos variáveis-novos = `PARAMETROS[%] × Vendas-novos`.** As mesmas
  10 percentagens do painel, incidindo sobre a Vendas-novos.

- **R7. Sem classificação = 3ª faixa discreta.** Todo pedido do recorte que **não** for
  Primeira Compra nem Recompra (carimbo vazio ou rótulo inesperado) entra numa faixa
  "sem classificação". Ela **não vira "novos" nem "recompra"** — existe só para a amarração
  fechar (R8). Rótulo inesperado (não vazio e diferente dos dois conhecidos) gera **aviso**.

- **R8. Amarração (guarda silenciosa).** Deve valer, em contagem de pedidos:
  `Pedidos-novos + Pedidos-recompra + Pedidos-sem-classificação = Pedidos-total do recorte`.
  A tela **não** mostra recompra nem a amarração; se a igualdade **não** fechar, mostra um
  **aviso amarelo** (checagem interna). Fiel ao `PRODUCT.md`: "recompra não aparece na tela".

- **R9. Ad Spend total — convenção 100% mídia → novos.** A mídia usada na aba de aquisição é a
  **mesma e inteira** do painel: `Ad Spend = fb_investimento/(1−0,1215) + google_investimento
  + google_institucional_investimento` (FB embrutecido pelo imposto, ADR 2026-07-03). **Não é
  fatiada** por `customer_type` — toda a mídia pesa nos novos (convenção declarada, ajustável
  na V4).

- **R10. MC-novos = Lucro Bruto-novos − Ad Spend total**, onde
  `Lucro Bruto-novos = Vendas-novos − deduções-novos − CMV-novos − custos-variáveis-novos`.
  Unidade R$. **Verde se ≥ 0** (a aquisição se paga na 1ª compra), **vermelha se < 0**.

- **R11. CAC = Ad Spend total ÷ Pedidos-novos.** Unidade R$/cliente novo. Se **Pedidos-novos
  = 0**, CAC é indefinido → **"—"** + nota. (Se Ad Spend = 0, CAC = R$ 0,00 — honesto: custou
  R$ 0 de mídia; não é divisão por zero.)

- **R12. aROAS = Vendas-novos ÷ Ad Spend total.** Múltiplo (ex.: 4,0). Se **Ad Spend = 0**,
  aROAS é indefinido → **"—"** + nota (nunca "∞"). aROAS é sempre **menor** que o ROAS Shopify
  blended da V1 (que soma também a recompra).

- **R13. A aba de MC da V1 não muda.** `painel.py` e `cascata.calcular` continuam idênticos.
  A V2 só **acrescenta**: uma coluna no carregador, uma função nova em `cascata.py`, uma página
  nova. Nada é subtraído do comportamento existente.

---

## 5. UI/UX

### 5.1 Telas afetadas
- **Nova:** `pages/2_Aquisicao.py` — a aba de aquisição (página multipage, menu lateral).
- **Inalteradas:** `painel.py` (aba de MC), `pages/1_Auditoria_de_custos.py`.

### 5.2 Componentes novos necessários
- **`dados.py`** — `carregar_vendas` mapeia a coluna `customer_type` (normalizada); `Dados.vendas`
  ganha essa coluna. `_exigir_colunas` passa a exigir `customer_type` na aba `Vendas`.
- **`cascata.py`** — função nova **`calcular_aquisicao(dados, inicio, fim) -> ResultadoAquisicao`**,
  que reusa `_recorte_pedidos`, filtra por `customer_type`, e devolve os 5 KPIs + a mini-cascata
  (lista de `LinhaDRE`, reusando a classe existente) + os dados da amarração + os alertas. Uma
  dataclass nova **`ResultadoAquisicao`**.
- **`pages/2_Aquisicao.py`** — a UI: herói MC-novos (verde/vermelho), 5 cartões, mini-cascata
  (reusa o mesmo padrão de tabela DRE estilizada do painel), barra de alertas/notas. Reusa os
  helpers `reais`/`numero` (copiados como no padrão da página de Auditoria) e o `@st.cache_data`.

### 5.3 Estados visuais
| Estado | O que aparece |
|---|---|
| **Loading** | Spinner "Lendo a planilha…" (mesmo cache do painel) |
| **Vazio** (sem dados no período) | "Sem dados no período." e para |
| **Sem novos** (Pedidos-novos = 0) | CAC "—" + nota "sem clientes novos no período"; MC-novos e mini-cascata ainda desenham |
| **Sem mídia** (Ad Spend = 0) | aROAS "—" + nota "sem mídia no período"; MC-novos válida |
| **Erro** de leitura | Mensagem clara do `ErroDeDados`; para |
| **Alerta** (SKU sem custo entre novos) | Faixa amarela "MC-novos pode estar superestimada — SKU sem custo" (sem editor nesta página) |
| **Sucesso** | Herói MC-novos verde/vermelho + 5 cartões + mini-cascata |

A **linha do zero**: a MC-novos herói e a linha "MC-novos" da mini-cascata usam fundo **verde**
(`#1f7a3d`, como a MC do painel) quando ≥ 0 e **vermelho** quando < 0; Lucro Bruto-novos usa o
azul de subtotal do painel (`#dbeafe`), mantendo a identidade visual.

### 5.4 Permissões
- **João (único usuário):** vê tudo, edita nada nesta página (só leitura; correção de custo
  segue no painel de MC). — `PRODUCT.md` seção 2.
- **CEO / lideranças:** fora do escopo (sem login multiusuário na V2), como na V1.

---

## 6. Casos de borda específicos desta feature

- **Pedidos-novos = 0 com Ad Spend > 0:** MC-novos = −Ad Spend (negativa/vermelha) — leitura
  correta e proposital: gastou mídia e não trouxe cliente novo no período. CAC = "—".
- **Ad Spend = 0 com Pedidos-novos > 0:** aROAS = "—"; CAC = R$ 0,00; MC-novos = Lucro
  Bruto-novos inteiro (positiva se LB-novos > 0).
- **Período de 1 dia / borda de mês:** datas de 3 abas podem diferir 1 dia (ponto frágil
  conhecido do `ARCHITECTURE.md`); aceito na V2 como na V1.
- **Rótulo `customer_type` inesperado:** cai em sem-classificação **e** dispara aviso (R7) —
  não infla novos silenciosamente.
- **`customer_type` vazio em massa** (fonte parou de carimbar): tudo vira sem-classificação →
  Pedidos-novos = 0 → CAC "—" + nota; a amarração ainda fecha (R8 não alarma), mas o
  "sem clientes novos" já sinaliza. *(A pré-condição do Fluxo D é o carimbo estar presente.)*
- **Clicar Atualizar duas vezes / trocar período no meio:** sem efeito colateral — é leitura
  pura e o cache é idempotente (igual ao painel).
- **Amarração não fecha** (ex.: duplicidade de linha na `Vendas`): aviso amarelo, sem quebrar a
  tela; os números seguem exibidos (Pedidos-novos usa `order_id` distintos).
- **SKU sem custo só entre recompra (não entre novos):** **não** alerta na aba de aquisição
  (só importa o que afeta a MC-novos).

---

## 7. Critérios de aceite testáveis

1. Quando João abre a página "Aquisicao", o sistema mostra herói MC-novos + 5 cartões
   (MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS) + mini-cascata, sem exceção.
2. Quando o período é junho/2026, **Vendas-novos + Vendas-recompra + Vendas-sem-classificação =
   Vendas total do painel** para o mesmo período (amarração de valor), e **Pedidos-novos +
   recompra + sem-classificação = Pedidos total do painel** (amarração de contagem).
3. Quando há pedidos Primeira Compra e mídia > 0, o sistema calcula
   **MC-novos = Vendas-novos − deduções-novos − CMV-novos − custos-variáveis-novos − Ad Spend
   total**, e a Ad Spend usada é **idêntica** à Ad Spend do painel no mesmo período (mídia inteira).
4. Quando MC-novos ≥ 0, o herói e a linha "MC-novos" aparecem **verdes**; quando < 0, **vermelhos**.
5. Quando Pedidos-novos = 0, o cartão **CAC mostra "—"** e a nota "sem clientes novos no período".
6. Quando Ad Spend = 0, o cartão **aROAS mostra "—"** e a nota "sem mídia no período"; MC-novos
   segue exibida.
7. Quando **CAC** é definido, vale `CAC = Ad Spend total ÷ Pedidos-novos`; quando **aROAS** é
   definido, vale `aROAS = Vendas-novos ÷ Ad Spend total`.
8. Quando há SKU sem custo entre os pedidos novos, aparece a faixa amarela de "MC-novos pode
   estar superestimada".
9. Quando a coluna `customer_type` está ausente da aba `Vendas`, o sistema mostra a mensagem
   `ErroDeDados` específica e não quebra a tela.
10. Quando João abre a página de aquisição, **o painel de MC (aba `painel`) continua idêntico**
    ao da V1 (mesma MC, mesmos 5 cartões, mesma cascata) — nenhum número muda.
11. A página **não escreve** na planilha nem cria/edita arquivo (só leitura).

> **Referência de sanidade (junho/2026, dado ao vivo 2026-07-09, sujeito a atualização da base):**
> 14.049 pedidos no recorte bruto da `Vendas` → 7.507 Primeira Compra, 6.542 Recompra,
> 0 sem-classificação (antes das exclusões AnjosFrach/pontuais). Servem para conferir a
> partição, **não** como valores fixos de teste.

---

## 8. Riscos e impactos

- **Módulos tocados:**
  - **`carregador-de-dados` (`dados.py`)** — muda `carregar_vendas` (+1 coluna) e `_exigir_colunas`.
    Risco: se a fonte deixar de trazer `customer_type`, a leitura **inteira** passa a falhar
    (a aba `Vendas` alimenta o painel também). *Mitigação:* mensagem de erro clara e específica;
    a coluna está confirmada na fonte hoje. **Alternativa considerada e recusada:** tornar a
    coluna opcional (não exigir) mascararia a quebra da pré-condição do Fluxo D — melhor falhar
    claro. **Decidido com João (2026-07-09): bloquear a leitura inteira (Opção A).**
  - **`calculo-cascata` (`cascata.py`)** — **acrescenta** `calcular_aquisicao` e
    `ResultadoAquisicao`; **não altera** `calcular` nem `_recorte_pedidos` (usa-os). Risco de
    regressão na MC da V1: **baixo** (nada existente muda). `_recorte_pedidos` já é reusado pela
    Auditoria — reuso comprovado.
  - **`painel-ui` (`painel.py`)** — **inalterado** (R13).
- **Reversibilidade:** alta. Reverter = apagar `pages/2_Aquisicao.py`, remover
  `calcular_aquisicao`/`ResultadoAquisicao` e o mapeamento da coluna. Nenhuma migração de dados.
- **Dado em produção afetado:** nenhum (não há escrita; a planilha é fonte externa só-leitura).
- **Risco de modelagem (herdado, declarado):** a **convenção 100% mídia → novos** faz a MC-novos
  ser o cenário **mais duro** (toda a mídia nos novos, nada na recompra). É premissa declarada,
  não medição — refinada na V4. E a régua "positiva na 1ª compra" ignora recompra/LTV de
  propósito (V4). Não são bugs; são escopo.
- **Inconsistência documental encontrada (a corrigir no `PRODUCT.md`, não bloqueia a spec):** o
  `PRODUCT.md` seção 3 cita "em junho/2026, 84 de 37.593 (0,22%)" para sem-classificação; a
  fonte ao vivo (2026-07-09) mostra junho com 14.049 pedidos e **0** sem-classificação, e a base
  inteira com **500**. O "37.593/84" parece um retrato ilustrativo do discovery, não junho. A
  **regra** (3 faixas + guarda) é robusta a isso; sugiro ajustar a frase do `PRODUCT.md` numa
  próxima passada.

---

## Verificação da spec (checklist do trilho)

- [x] Glossário respeitado (mesmos termos do `PRODUCT.md`/`CLAUDE.md`; "MC", nunca "lucro").
- [x] Cada caminho da seção 2 vira ≥ 1 critério de aceite (seção 7).
- [x] Casos de borda específicos, não genéricos (seção 6).
- [x] "Migração" (contrato de leitura) descrita com reversibilidade (3.4).
- [x] Riscos citam módulos pelo nome do `ARCHITECTURE.md` (seção 8).
- [x] **Decidido com João (2026-07-09):** a ausência de `customer_type` **bloqueia a leitura
  inteira** com erro claro (Opção A — falha barulhenta > silenciosa). Já implementado em
  `dados.carregar_vendas` via `_exigir_colunas`. Trocar para "só desativar a aba" é mudança de
  1 linha, se um dia fizer sentido.
</content>
</invoke>
