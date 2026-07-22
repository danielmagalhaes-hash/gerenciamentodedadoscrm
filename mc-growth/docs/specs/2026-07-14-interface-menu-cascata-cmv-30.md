# Spec — Menu, cartões de Aquisição, cascata normalizada e CMV estimado em 30%

> **Data:** 2026-07-14 (segunda sessão do dia). **Modo:** B (construção).
> **Origem:** pedido do João em sessão. Toca **interface** (3 itens) e **dinheiro** (1 item: a
> regra do CMV estimado). Nada aqui muda o cálculo dos meses **reais** (janela de itens).

---

## 0. Resumo em uma frase

Padronizar as três telas (menu, cartões de aquisição e a cascata DRE, que hoje é remontada à mão
em 6 lugares) e **trocar a estimativa de margem** onde falta custo: em vez de "margem de produto =
25% da receita", passa a ser **CMV = 30% da receita** com **todas as deduções e custos variáveis
seguindo as fórmulas de sempre**.

---

## 1. O que muda (4 entregas)

### E1 — Menu: nomes e ordem
| Hoje (rótulo na barra lateral) | Vira |
|---|---|
| `painel` (página de entrada) | **1. Geral** |
| `Aquisicao` | **2. Aquisição** |
| `Coortes` | **3. Cohorts** |
| `Auditoria de custos` | **A1 - Auditoria Custos** |

Ordem: 1 → 2 → 3 → A1 (a auditoria vai para o fim; hoje é a primeira da lista).

**Como:** `st.navigation` + `st.Page` (Streamlit 1.58, disponível). `painel.py` vira o
**roteador** (declara o menu e nada mais); o conteúdo de hoje muda para `views/geral.py`, e as
páginas atuais saem de `pages/` (a pasta `pages/` é descoberta automaticamente pelo Streamlit e
duplicaria o menu). Entrada continua sendo `python3 -m streamlit run painel.py` — o atalho
`Abrir Painel MC.command` não muda.

### E2 — Cartões da aba Aquisição
Herói (MC de clientes novos) **mantido**. A fileira de cartões passa a ser **6**, nesta ordem:

`Vendas novos clientes` · `Ad Spend` · `aROAS Shopify` · `Ticket Médio` · `nº Pedidos` · `CAC`

- Sai o cartão **MC-novos** (já é o herói).
- Entra **Ticket Médio** = `Vendas-novos ÷ Pedidos-novos` (**novo**: `ResultadoAquisicao` ganha
  `ticket_medio` — `None` se não há pedidos novos, mostrado como "—").
- Entra **Ad Spend** = a mídia inteira do período (a mesma do painel geral; convenção 100%
  mídia → novos, inalterada).
- `aROAS` passa a se chamar **aROAS Shopify**; `Pedidos-novos` vira **nº Pedidos**.

### E3 — Cascata DRE normalizada (todas as telas)
Formato único, com dois **subtotais de grupo** (cinza) que são **soma das linhas abaixo**:

```
     Vendas
(−)  Deduções                    [subtotal, CINZA]
       (−) PIS/COFINS + CBS
       (−) ICMS + IBS
       (−) Devoluções
       (−) Chargebacks
       (−) Outras Deduções
(−)  Cost of Delivery            [subtotal, CINZA]
       (−) CMV                   [CINZA CLARO]
       (−) Frete
       (−) Embalagem
       (−) Taxa de Gateways
       (−) Valor plataforma
       (−) Despesas de antecipação
(=)  Lucro Bruto
(−)  Mídia Paga
(=)  Margem de Contribuição
```

- Os subtotais são **apresentação pura** — somas de linhas que já existem. **Nenhum número muda.**
- Ordem das deduções conforme o pedido do João (impostos primeiro, depois devoluções/chargebacks).
- Vale para: **1. Geral**, **2. Aquisição** e os **3 blocos da auditoria por safra** (novos,
  recompra, total) dentro da **3. Cohorts**. A cascata de **recompra**, hoje agrupada numa linha
  só de deduções, passa a abrir linha a linha como as demais.
- **Onde é construída:** hoje o DRE é remontado à mão em **6 lugares** (`cascata.py` ×4 —
  painel antigo, aquisição antiga, e os dois motores deals-based; `coortes.py` ×2). Passa a
  existir **uma função só** — `cascata.montar_cascata(...)` — usada pelos seis. Uma forma, uma
  verdade.

### E4 — CMV estimado em 30% (**toca dinheiro**)
**Hoje:** onde o pedido não casa com a janela de itens (histórico + vendas do Comercial), a MC de
produto é estimada em `0,25 × valor` e as deduções **não** incidem sobre essa parte (entram só
sobre a receita casada) — a estimativa entra na tela como uma linha amarela "Margem estimada (25%)".

**Passa a ser:**
- **CMV estimado = `0,30 × receita sem itens`**, somado ao CMV real dos pedidos casados;
- **deduções e custos variáveis incidem sobre a receita INTEIRA** (casada + não casada), pelas
  fórmulas de sempre (`PARAMETROS`);
- **a linha "Margem estimada" DEIXA DE EXISTIR.** A cascata fica com o formato único do E3, e a
  única linha provisória é o **CMV**, marcado com ⚠️ e o aviso "X% estimado (30%)" quando houver
  mistura.

**Fórmula (deals-based):**
```
Vendas          = Σ valor dos deals do período
CMV             = CMV real (pedidos casados, item a item) + 0,30 × receita não-casada
Deduções        = Vendas × 17,92%      (PIS/COFINS+CBS, ICMS+IBS, devoluções, chargebacks, outras)
Cost of Delivery= CMV + Vendas × 9,57% (frete, embalagem, gateways, plataforma, antecipação)
Lucro Bruto     = Vendas − Deduções − Cost of Delivery
MC              = Lucro Bruto − Mídia
```
Margem de produto implícita da parte estimada: `1 − 27,49% − 30% = **42,5%** da receita`
(antes: 25%).

**Por que 30% (rastro do número):** medido nos meses com itens reais (2026-07-14):
CMV/Vendas = **29,0% (maio)** e **28,8% (junho)**; Lucro Bruto/Vendas = **42,8%** e **43,0%**.
Os 30% são o real levemente arredondado **para cima** (conservador). O 25% antigo era um chute
pessimista — subestimava a margem histórica em ~17,5 pontos de receita.

**Consequência assumida (João ciente):** todos os meses **históricos** do painel e da aquisição, e
**92,5% das células** do triângulo de coortes (as estimadas), **sobem**. Safras antigas no vermelho
podem virar verde. Os meses da janela real (abr–jul/2026) **não mudam em nada**.

---

## 2. O que NÃO muda (invariantes a provar)

1. **Janela real byte-idêntica.** Para um período 100% dentro da janela de itens (ex.: junho/2026),
   `Vendas`, `CMV`, `Lucro Bruto` e `MC` do painel e da aquisição saem **iguais aos de hoje**
   (a receita não-casada é zero → o ramo estimado não é acionado).
2. **Os subtotais não entram na conta.** `Deduções` e `Cost of Delivery` são somas de linhas
   existentes; `Lucro Bruto` e `MC` continuam vindo do motor, não da tabela.
3. **Uma verdade de custo.** O CMV real segue saindo de `cascata.juntar_custos` (item a item) —
   condição do João, preservada.
4. **Reconciliação da coorte.** A MC/cliente da cascata da auditoria segue batendo com a célula do
   triângulo (`mc_acumulada[safra, horizonte]`) nas 64 safras.
5. **Mídia** inalterada (gross-up do FB de 12,15%; inteira no m+0 / nos novos).

---

## 3. Critérios de aceite (testáveis)

- **CA1 (menu):** a barra lateral mostra, nesta ordem: `1. Geral`, `2. Aquisição`, `3. Cohorts`,
  `A1 - Auditoria Custos`. As 4 páginas sobem via `AppTest` sem exceção.
- **CA2 (cartões):** a aba de aquisição mostra 6 cartões na ordem pedida; `Ticket Médio` =
  Vendas-novos ÷ nº Pedidos (confere na mão); sem pedidos novos → "—", sem mídia → aROAS "—".
- **CA3 (cascata):** nas 5 cascatas do projeto (Geral, Aquisição, e os 3 blocos da auditoria), a
  soma das linhas filhas **é igual** ao subtotal do grupo (≤ R$ 0,01), e
  `Vendas − Deduções − Cost of Delivery = Lucro Bruto` (≤ R$ 0,01).
- **CA4 (não-regressão):** junho/2026 (janela real) — Vendas, CMV, Lucro Bruto e MC **idênticos**
  aos de antes da mudança (diferença = 0).
- **CA5 (CMV 30%):** num período 100% histórico (ex.: junho/2025), o CMV mostrado = 30% da receita
  e o Lucro Bruto = 42,5% da receita (≤ R$ 0,01 de folga).
- **CA6 (marcação):** em período misto, o CMV vem com ⚠️ e o aviso traz o % estimado; em período
  100% real, nenhum aviso de estimativa aparece.
- **CA7 (coorte):** a reconciliação cascata↔triângulo segue exata nas 64 safras, com o novo
  patamar (42,5%).

---

## 4. Fora do escopo (registrado, não feito)

- Decidir se o painel geral inclui as vendas do **Comercial** (~1,2%, não-Shopify) — pendência
  aberta do ADR `2026-07-14-rebase-geral-aquisicao-hubspot` §5-bis.
- Alinhar a régua de "novo" entre a aba Aquisição (HubSpot) e a auditoria por safra (1ª compra por
  cliente) — divergência documentada de propósito.
- Opção 1 (CMV real ano-a-ano desde 2022, itens históricos do BigQuery) — versão seguinte. Quando
  ela entrar, a estimativa de 30% perde quase todo o alcance.
