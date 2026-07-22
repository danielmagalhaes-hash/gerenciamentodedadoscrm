# Sessão 2026-06-30 — discovery

> Log da sessão de discovery (Fase 0). Entrevista de produto conduzida para gerar o futuro `PRODUCT.md`.
> **Status: discovery em andamento** — Áreas 1, 2 e 3/6 cobertas; faltam 4, 5, 7, 8.

---

## Objetivo da sessão

Conduzir o discovery do MC Growth e mapear a anatomia da Margem de Contribuição (MC) da Shopify para sustentar o `PRODUCT.md`.

---

## O que foi feito

- Cobertas as Áreas 1 (visão), 2 (usuários) e 3/6 (anatomia da MC) da entrevista.
- Mapeada a cascata completa de Vendas → Margem de Contribuição (Shopify).
- Identificadas as fontes de dados: Shopify, Tabela de custo (origem Bling), BigQuery.
- Registrado ADR provisório sobre devoluções (`docs/decisions/2026-06-30-tratamento-devolucoes-e-net-sales.md`).

---

## Contexto do negócio (Área 1)

- **MC Growth** = gestão e otimização do crescimento da **Minimal Club** via Margem de Contribuição. **v1 = dashboard diário de vendas e MC**.
- **Minimal Club:** moda masculina minimalista, premium, produto físico, D2C. Loja em **Shopify** (migrou do CartPanda). Aquisição via Meta Ads + influenciadores + Klaviyo. Tem frente B2B. Grupo **Moon Ventures**.
- **Escala:** ~R$95M (2025), meta R$145M (2026), visão R$1bi. Centenas a milhares de pedidos/dia, picos sazonais (Black November).
- **Vendas totais = 5 canais:** Shopify, B2B, TikTok Shop, Assinatura, Mercado Livre. **v1 cobre só Shopify.**
- **Dor:** hoje MC só aparece no fechamento mensal do Financeiro; a gestão voa às cegas no dia a dia.
- **NÃO é:** fechamento contábil, BI/ERP completo, tempo real ao segundo, nem os outros 4 canais (por ora).

## Usuários (Área 2)

- **João (gestão):** uso diário. **CEO + lideranças:** ≥1x/semana. Só **computador** por ora.
- **Visão única** pra todos. **Login individual** por pessoa.
- Conteúdo v1: valor de vendas + todas as linhas de desconto até a MC + filtro de data.

---

## Anatomia da Margem de Contribuição (Área 3/6)

Cascata final (cada linha exibida; Lucro Bruto é subtotal exibido):

| # | Linha | Cálculo |
|---|---|---|
| | **Vendas** | `net_sales − returns + shipping_charges` · `order_payment_status='paid'` · `sales_channel != 'TikTok'` |
| − | Devoluções | 3,48% ⚠️ (possível dupla contagem) |
| − | Chargebacks | 0,15% |
| − | PIS/COFINS + CBS | 1,75% |
| − | ICMS + IBS | 12,54% |
| − | Outras Deduções | 0% (zerada, editável) |
| − | **CMV** | tabela de custo por SKU (origem Bling) × SKUs de cada pedido Shopify |
| − | Frete | 4,8% |
| − | Embalagem | 0,57% |
| − | Taxas de Gateways | 1,70% |
| − | Valor plataforma | 0,90% |
| − | Despesas de antecipação | 1,60% |
| = | **Lucro Bruto** | subtotal exibido |
| − | Despesas de mídia paga | gasto **total** Google + Meta (do BigQuery) |
| = | **Margem de Contribuição** | |

**Regras-chave confirmadas:**
- Linha de Vendas: frete cobrado do cliente **entra**; data = **data do pagamento**; pedido não pago **não conta**.
- Filtro `!= TikTok`: o TikTok é canal separado, mas vazou pra base Shopify num período passado.
- CMV: resgatar cada pedido da Shopify → SKUs do pedido → PROCV na tabela de custo → somar.
- Linhas em % incidem sobre a **Vendas** e são **editáveis** no painel (Frete, Embalagem, Gateways, Plataforma, Antecipação — e provavelmente as deduções/impostos).
- Mídia paga: Google + Meta do BigQuery; influenciadores **fora**; usa gasto **total** (assume Shopify como maioria).

**Fontes de dados:**
| Fonte | Fornece |
|---|---|
| Shopify | vendas (pedidos + SKUs por pedido) |
| Tabela de custo (origem Bling) | CMV por SKU |
| BigQuery (BQ) | gasto de mídia paga (Google + Meta) |

---

## Decisões tomadas

### Manter fórmula de Vendas/Devoluções no formato Shopify (provisório)
- **Decisão:** usar `net_sales − returns + shipping_charges` e manter a linha Devoluções 3,48% como está no v1.
- **Por quê:** é o formato do relatório nativo da Shopify; ajuste depende de alinhamento com o Financeiro.
- **Risco aceito:** devolução possivelmente descontada 2x → MC subestimada; **não tratar como número contábil oficial** até alinhar.
- **ADR criado?** Sim — `docs/decisions/2026-06-30-tratamento-devolucoes-e-net-sales.md` (status: Em discussão).

### Parâmetros de custo editáveis no painel
- **Decisão:** os percentuais (frete, embalagem, gateways, plataforma, antecipação, deduções) ficam em campos editáveis pelo próprio usuário.
- **Por quê:** mudam com o tempo; evita pedido de alteração de código a cada mudança.
- **Consequência:** o v1 precisa de uma área de parâmetros/configuração.

---

## Pendências (a resolver antes de fechar a spec)

1. **Devoluções 2x** — aguardando alinhamento com o Financeiro (ver ADR). ⚠️
2. **Descontos/cupons:** `net_sales` já tira descontos — confirmar que não precisa de linha "Descontos" separada.
3. **SKU vendida sem custo na tabela:** painel avisa "X itens sem custo hoje" ou trata como zero silenciosamente?
4. **Manutenção da tabela de custo:** quem mantém e com que frequência (custo desatualizado = margem errada invisível).
5. **ICMS+IBS por estado:** os 12,54% são média única ou variam por estado de destino?
6. **Base das 3 taxas** (Gateways/Plataforma/Antecipação): confirmar que é sobre a Vendas.
7. **Extração técnica das fontes** (Fase 1): Shopify (API/export), Bling (API/planilha), BigQuery (conexão).

---

## Estado do projeto agora

### Pronto
- Fundação documental (CLAUDE.md, estrutura docs/, git).
- Discovery Áreas 1, 2, 3/6 cobertas.

### Incompleto
- Discovery: faltam Áreas 4 (entidades), 5 (fluxos), 7 (escopo formal), 8 (restrições).
- `PRODUCT.md` ainda não gerado (depende de fechar o discovery).

---

## Próximo passo

1. Resolver/parquear as 7 pendências acima.
2. Cobrir Áreas 4, 5, 7, 8 da entrevista.
3. Gerar o `PRODUCT.md` (`prompts/01-gerar-product-md.md`).

---

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** ainda não existe (Fase 1).
- **`CLAUDE.md`:** sem mudança.
- **`docs/decisions/`:** criado `2026-06-30-tratamento-devolucoes-e-net-sales.md`.
- **`docs/specs/`:** nenhum ainda.
- **`PRODUCT.md`:** ainda não existe.
