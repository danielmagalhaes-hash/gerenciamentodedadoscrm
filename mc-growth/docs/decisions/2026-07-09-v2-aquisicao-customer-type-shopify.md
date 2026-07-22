# ADR 2026-07-09 — V2 é a aba de aquisição, carimbada pelo `customer_type` nativo da Shopify

> Decisão duradoura tomada no discovery de handoff V1→V2 (Modo A). Registra as escolhas que
> moldam a V2 e por que divergem do desenho original do ROADMAP.

---

## Contexto

O ROADMAP (2026-07-04) previa a V2 como "a dobradiça": dar identidade de cliente por **e-mail**
e mostrar a cascata em **duas colunas** (MC-novos × MC-recompra), respondendo *"quanto do meu
lucro vem de recompra?"*. Ao abrir o discovery da V2, dois fatos mudaram o desenho:

1. **Não há e-mail na base.** As abas `Vendas` e `Itens` não têm coluna de e-mail. Construir a
   chave de cliente exigiria dado a montante (e lidar com guest checkout, e-mail duplicado,
   digitação errada — a "sujeira da chave").
2. **A Shopify já carimba cada pedido.** Existe (e o João adicionou à aba `Vendas`) a coluna
   `customer_type`, campo **nativo da Shopify** com valores `Primeira Compra` / `Recompra`.

E o João afinou a decisão-alvo: a pergunta que ele quer responder não é "quanto vem de
recompra", é **"minha aquisição de clientes está lucrativa?"** — e, mais preciso ainda,
**"lucrativa já na 1ª compra"** (não no tempo de vida).

## Decisão

**1. A chave de cliente da V2 é o campo nativo `customer_type` da Shopify, não uma chave de
e-mail construída por nós.**
- É **point-in-time** (cada cliente tem exatamente uma "Primeira Compra") e enxerga o
  **histórico completo** da loja → **sem viés de borda esquerda** (não confunde recompra antiga
  com aquisição nova).
- Tira de nós a parte suja da chave (guest checkout, e-mail duplicado). Adotamos a régua da
  Shopify tal como é: "returning" = ≥1 pedido anterior na loja.
- Vem **automático** no fluxo da planilha (não é manual → robusto). Cobertura 99,78%.

**2. A V2 é uma aba dedicada de aquisição, focada só em clientes novos** — não a cascata em
duas colunas. Mostra 5 KPIs: **MC-novos, Vendas-novos, Pedidos-novos, CAC, aROAS**. A coluna de
recompra (e o "% do LB que vem de recompra") vira **candidata a uma versão seguinte**.

**3. Convenção: 100% da mídia é atribuída aos clientes novos** neste 1º momento. Logo CAC e
aROAS são "blended" por convenção; a MC-novos carrega toda a mídia (visão mais dura da
aquisição). Ajustável — a V4 separa mídia de aquisição × remarketing.

**4. Régua conservadora: "lucrativa" = MC positiva na 1ª compra.** O tempo de vida
(recompra/coorte/LTV) é deliberadamente V4. A única faixa na tela é a **linha do zero** na
MC-novos (verde ≥ 0 / vermelho < 0) — nenhum alvo importado (a régua calibrada é V5).

**5. Vocabulário:** o número é **Margem de Contribuição**, nunca "lucro" (que seria depois do
custo fixo). "Lucro" é sinônimo proibido no projeto.

## Consequências

- **Positivas:** a V2 fica pequena e robusta — zero entidades novas (só um atributo no Pedido),
  zero dado pessoal (LGPD só na V4), sem dependência a montante pendente (o carimbo já vem). A
  borda esquerda, que seria o maior risco da abordagem por e-mail, some.
- **Amarração preservada:** `novos + recompra + sem-classificação = total` fecha na unha; a
  convenção 100%→novos ainda deixa MC-novos + MC-recompra = MC-total real.
- **Custo:** herdamos a definição da Shopify (se ela mudar, mudam os números); CAC/aROAS são
  blended até a V4; a dobra de kit ainda subestima a MC-novos (bug herdado).
- **Divergência do ROADMAP registrada:** a entrada da V2 no `docs/ROADMAP.md` foi atualizada
  para refletir "só aquisição"; a coluna de recompra ficou como candidata futura.

## Alternativas descartadas

- **Construir chave de e-mail (desenho original do ROADMAP):** exigiria dado a montante, lidar
  com a sujeira da chave e conviver com o viés de borda esquerda. Descartada porque o campo
  nativo da Shopify entrega o mesmo carimbo de graça e sem esses problemas. (O e-mail volta na
  V4, onde é inevitável para coorte.)
- **Mostrar as duas colunas (novos × recompra) já na V2:** adiada — o João focou a decisão em
  aquisição; some complexidade sem servir à decisão do momento.
- **Ratear a mídia por um critério (ex.: proporção de vendas) para ter "MC" por segmento
  "medida":** descartada — fingiria precisão que a V2 não tem (armadilha nº 1/2 do roadmap). A
  convenção 100%→novos é honesta e declarada; a atribuição real é V4.
