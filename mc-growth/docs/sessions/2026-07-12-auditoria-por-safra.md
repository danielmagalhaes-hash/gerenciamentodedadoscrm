# Sessão — Auditoria por safra (V4, incremento)

**Data:** 2026-07-12
**Modo:** B (construção — toca a MC por safra)
**Gatilho:** João, ao rodar a aba Coortes: *"preciso entender se cada coorte está considerando a
receita e os descontos corretos para chegar na MC"* — a tela mostrava só o número já somado.

---

## O que se fez (em linguagem de negócio)

A aba Coortes ganhou um botão **"🔍 Auditar a MC de uma safra"**. Ligando, ela **abre a cascata**
da safra em foco — a mesma conta do painel, mas para aquela turma: Receita → deduções (impostos,
frete, etc.) → CMV → Lucro Bruto → mídia → **MC por cliente**. Assim dá para conferir de onde vem
o número, em vez de confiar no total.

Duas visões (o João pediu as duas) + exportar:
1. **Cascata total** da safra (somada até o último mês fechado), com as 10 linhas de dedução
   abertas.
2. **Cascata por idade** (m+0, m+1, …): como a MC/cliente se forma mês a mês.
3. **Baixar CSV** dos deals da safra (1 linha por pedido, **sem e-mail** — a chave é o número do
   pedido, que liga na planilha).

**A raiz do "não estava fácil":** os dois ramos tratam receita/desconto diferente. O **real**
(pedido casa com a janela de itens atual) faz a cascata cheia; o **estimado** (fora da janela) é
`0,25 × valor` **direto** — os 25% já são a margem líquida, sem linha de dedução. Por isso as
safras velhas não mostram deduções abertas: estão embutidas nos 25%. A tela agora **diz isso** (o
ramo estimado vem em amarelo, com a nota).

---

## Garantia principal: não mexi na matemática da MC

A auditoria **re-expõe** a mesma `mc_produto` do triângulo — não recalcula nada. Extraí um
enriquecimento por deal (`coortes._preparar_deals`) **compartilhado** por `calcular_coortes` (o
triângulo) e `detalhar_safra` (a auditoria) → uma só verdade.

**Reconciliação provada:** a "MC parcial por cliente" da cascata **bate com a célula da safra no
triângulo** nas **64 safras** (diferença < 1e-6), com o **mesmo N_S**. A tela mostra o ✅ ao vivo.
Ajuste que fechou a conta: o denominador da cascata é o **N_S da safra inteira** (todos os clientes,
inclusive os 4 cross-canal cuja 1ª compra Shopify cai numa idade ainda não fechada) — não só os
clientes das idades fechadas.

Outros checks: Receita − deduções − CMV = Lucro Bruto real (exato); o CSV não tem coluna de e-mail
e a soma de `mc_produto` bate com a cascata; refactor deixou o **triângulo idêntico** (N, CAC,
payback, MC/cliente inalterados). `AppTest` sobe as 4 páginas sem exceção, com o toggle da
auditoria ligado e desligado.

---

## Decisões da sessão

- **Toggle, não expander:** o conteúdo do expander do Streamlit roda mesmo fechado; um **toggle**
  garante que a auditoria (pesada — reusa a ponte sobre 462k deals) **só computa quando ligada**.
  Cacheada por (safra, dia).
- **Sem e-mail no export/tela:** PRODUCT §8 (o painel não exibe dado pessoal). A chave de auditoria
  é o **número do pedido** — que é mais útil (liga direto na planilha) e respeita a regra.
- **N_S da safra inteira** como denominador (R3), para reconciliar com o triângulo.

---

## Refinamento do layout (mesma sessão, após feedback do João)

O João achou a cascata confusa: **"MC" aparecia em 4 linhas** (a estimada, a de produto, a total,
a por cliente) e não ficava claro o que era **total** e o que era **por cliente**. Reestruturei a
tela em **duas partes**, sem tocar na conta (só re-expõe a mesma `mc_produto`):

- **Parte 1 — como se forma a margem de produto** (valores **totais** da turma): a parte **medida**
  detalhada (Receita − Deduções `%` − CMV = Margem medida) + a parte **estimada numa linha só**,
  amarela e avisada (⚠️ "pedidos sem itens, 25% da venda"). As 10 linhas de dedução viraram **uma
  só** ("impostos, frete, taxas — 27,5% da receita") porque são um **% fixo** igual para toda safra
  (não acrescentam nada por-safra abertas).
- **Parte 2 — da margem à MC**: `Margem de produto → (−) Mídia → MC`, com **duas colunas: "Total da
  turma" e "Por cliente"**, deixando explícito o que é agregado e o que é por cabeça. A MC/cliente
  fecha com o número do topo e do triângulo (✅ na tela).
- Mês-a-mês foi para trás de um **checkbox "avançado"** (não polui por padrão). Reconciliação
  reverificada nas **64 safras** após a mudança.

## Redesenho 2 — cascata em novos + recompra + total (2026-07-13)

O João pediu para a cascata (1) ter o formato das outras abas e (2) separar **aquisição × retenção**.
Reestruturei em três blocos (sem matemática nova — mesma `mc_produto`, agora partida):

- **Bloco A — MC dos novos** (a **1ª compra de cada cliente** da safra): cascata **completa igual à
  V2** (Vendas-novos → deduções abertas → CMV → Lucro Bruto → − mídia inteira → MC-novos).
- **Bloco B — MC de recompra** (compras seguintes): agrupada (Vendas → Deduções `%` → CMV →
  MC-recompra), **sem mídia** (a mídia é custo de aquisição, já no bloco A).
- **Bloco C — MC total** = novos + recompra, com **total × por cliente**.
- **Slider de horizonte** ("até m+K"): a recompra e o total recomputam; a reconciliação passa a ser
  com `mc_acumulada[safra, K]` do triângulo (reverificada nas 64 safras, total e parcial).

Decisões:
- **Novos = 1ª compra por cliente** (o primeiro deal), não o `tipo_de_venda` do HubSpot (que diverge
  do Shopify). É o significado exato de aquisição e à prova de inconsistência do campo.
- **MC-novos da coorte ≠ MC-novos da V2, de propósito** (medido: junho R$396k vs R$237k). A régua
  difere — coorte conta a 1ª compra **na Minimal** (cross-canal); a V2 conta o **carimbo do Shopify**.
  O valor por pedido é ~igual (~R$518); o gap é **contagem** (~688 clientes a mais na coorte). Nota
  explícita na tela.
- Performance: o enriquecimento pesado (`preparar_deals_cache`) é cacheado 1×/dia e reusado por
  safra/horizonte — o slider fica fluido.

## Estado / próximo passo

- **Auditoria por safra construída e verificada.** A V4 agora é auditável de ponta a ponta.
- Pendências seguem as do log de construção (`2026-07-10-construcao-v4-coortes.md`): corrigir
  `PRODUCT.md`/spec a montante (idade calculada; fórmula 25%); recompra 90d+180d; Opção 1 (MC real
  ano-a-ano); re-base da V2 no HubSpot.
- Spec desta entrega: `docs/specs/2026-07-10-v4-auditoria-por-safra.md`.
