# Sessão 2026-07-10 — Discovery da V4 (coortes de recompra)

## Objetivo da sessão
Seguir para as versões V3/V4 do roadmap; a sessão virou **discovery profunda da V4** (aba de coortes de recompra) — sem código.

## O que foi feito
- Ritual de início: li `CLAUDE.md`, `ARCHITECTURE.md`, `PRODUCT.md` (V2), `ROADMAP.md`, `cascata.py`.
- Diagnóstico da V3: o João decidiu manter custos em % → **V3 esvaziada**, build pula para **V4**.
- Discovery formal (prompt `00-discovery.md`, uma pergunta por vez) fechando coorte, métrica, mídia, fonte e tela da V4.
- Medi a janela real da planilha ao vivo (`dados.carregar_tudo`): Vendas/Itens só de **abr–jul/2026**.
- Escrevi 3 queries de BigQuery (o João rodou): planta baixa + amostra do HubSpot `silver_deals_minimal`, e cobertura mensal de `silver_minimal_shopify_pedidos_products` (**contínua de 2022-01 até hoje**).
- Gerei/atualizei os documentos: `PRODUCT.md` (V4), `PRODUCT-v2.md` (arquivo), ADR, este log, `CLAUDE.md` §0, `ROADMAP.md`, `ARCHITECTURE.md`, o prompt guardado do re-base da V2, e o relatório para o advisor.

## Decisões tomadas
- **Decisão:** V3 (custo real por pedido) esvaziada; custos seguem em % (da DRE). **Por quê:** o João optou por não trocar % por custo real e adiar os 3 custos novos; sem isso a V3 não destrava decisão nova. **Descartado:** construir o P&L cheio por pedido agora. **ADR:** incluído no ADR da V4.
- **Decisão:** V4 = coortes de recompra, **MC acumulada por cliente** por safra, com a fonte **HubSpot** (`silver_deals_minimal`, filtro `Shipped`) como base oficial de cliente/1ª-compra. **Por quê:** é onde mora o valor não construído (seguir a turma no tempo → acelerar/segurar aquisição); a base já entrega a coorte pronta. **Descartado:** âncora Shopify-first (minha recomendação); estimar todo o histórico; curva com todas as ~54 safras. **ADR:** `docs/decisions/2026-07-10-v4-coortes-recompra-hubspot.md` (sim).
- **Decisão:** coorte **cross-canal** (`data_primeira_compra`), MC/mídia só do Shopify → **viés aceito e documentado**. **Por quê:** Shopify é >95% das vendas; o João prefere a definição única do HubSpot. **Descartado:** recomputar a 1ª compra dentro do Shopify. **ADR:** sim (mesmo).
- **Decisão:** MC real de 2022-01 em diante; **25%** de margem estimada antes. **Por quê:** o CMV real existe no BQ desde 2022; o pré-2022 é ínfimo (~101 linhas). **ADR:** sim (mesmo).
- **Decisão:** V4 vira a base oficial → **re-basear a V2 no HubSpot** (item à parte). **Por quê:** uma ferramenta, uma definição de "cliente novo". **Descartado:** deixar V2 e V4 como lentes divergentes. **ADR:** registrado; prompt guardado.

## Problemas encontrados
- **Problema:** a V3 do roadmap perderia a função com custos em %. **Causa:** decisão do João de manter %. **Solução:** pular para V4; registrar o resíduo (aterrar % na DRE) como melhoria pequena. **Status:** resolvido.
- **Problema:** o carimbo `customer_type` do Shopify (V2) não serve para coorte (é por pedido). **Causa:** coorte exige chave de cliente que dura no tempo. **Solução:** adotar o HubSpot (e-mail). **Status:** resolvido (na definição).
- **Problema:** `data_primeira_compra` é cross-canal → desalinha mídia↔aquisição e diverge da V2. **Causa:** a base classifica a 1ª compra em qualquer canal. **Solução:** viés aceito e documentado (Shopify >95%); medir por query na spec. **Status:** aberto (a medir).
- **Problema:** a planilha estreita não segura anos de itens. **Causa:** stack lê CSV de uma aba curta. **Solução:** decidir arquitetura na spec (ler do BQ/pré-agregar). **Status:** aberto (pré-requisito da spec).

## Estado do projeto agora
- **Funcionando:** V1 (painel de MC) e V2 (aba de aquisição) intocadas e rodando. Todos os documentos da V4 escritos e coerentes.
- **Quebrado/incompleto:** V4 **não construída** — só discovery. Arquitetura da leitura de histórico **não decidida**. Duas queries de validação **pendentes**. Receita por deal (`valor` × `net_revenue`) **a confirmar**.

## Próximo passo
1. Escrever a **spec da V4**, começando pela **decisão de arquitetura** (ler do BigQuery direto ou pré-agregar) — provável ADR próprio.
2. Rodar as **queries de validação**: `valor` (HubSpot) × `net_revenue` (Shopify); tamanho do **viés cross-canal**.
3. Confirmar contra o que os **25%** incidem (margem de produto, antes da mídia); depois, a re-base da V2 (`docs/prompts-guardados/re-base-v2-hubspot.md`).

## Atualizações em outros documentos
- **ARCHITECTURE.md:** nota da fonte nova (HubSpot no BQ) no topo; linha da V4 na tabela de decisões (§5); dois pontos frágeis novos (§6: planilha estreita, viés cross-canal).
- **CLAUDE.md:** §0 = "V4 em discovery, spec por fazer" + próximo passo; V3 esvaziada.
- **docs/decisions/:** `2026-07-10-v4-coortes-recompra-hubspot.md` (criado).
- **docs/specs/:** nenhum (a spec da V4 é o próximo passo).
- **Outros:** `PRODUCT.md` reescrito (V4); `docs/product-history/PRODUCT-v2.md`, `docs/prompts-guardados/re-base-v2-hubspot.md`, `docs/reviews/2026-07-10-v4-definicoes-para-revisao.md` (criados); `ROADMAP.md` (V3/V4).
