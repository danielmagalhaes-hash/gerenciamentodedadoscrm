# Spec — Auditoria por safra (V4, incremento)

> Modo B (toca dinheiro: a MC de cada safra). Base: `docs/specs/2026-07-10-v4-coortes-recompra.md`.
> Pedido do João (2026-07-10): *"preciso entender se cada coorte está considerando a receita e os
> descontos corretos para chegar na MC"* — hoje a aba mostra só o número somado.

## 1. Problema
A aba Coortes guarda só a **MC de produto por deal** (um número) e acumula por cliente. Não dá para
abrir uma safra e conferir a **cascata** (Receita → deduções → CMV → Lucro Bruto → mídia → MC).
Agrava: os dois ramos tratam receita/descontos **diferente** — o **real** faz a cascata cheia; o
**estimado** é `0,25 × valor` direto (os 25% já são a margem líquida, sem linhas de dedução). Sem
abrir, não dá para ver se a receita e as deduções que entraram estão certas.

## 2. O que entra
Uma seção **"🔍 Auditar a safra {S}"** na `pages/3_Coortes.py` (atrás de um toggle, só computa quando
ligado), para a safra em foco, com **três peças** (escolha do João: "as duas" + export):

1. **Cascata total da safra** (somada até o último mês fechado), estilo DRE do painel:
   `Receita real → (10 linhas de dedução %) → CMV real → Lucro Bruto real → (+ MC estimada 25%) →
   MC de produto → Mídia (m+0) → MC total → ÷ N_S → MC parcial por cliente`.
2. **Cascata por idade** (m+0, m+1, …): uma linha por idade fechada com
   `Deals · %real · Receita · Deduções · CMV · Lucro Bruto · MC estimada · Mídia · MC incr. total ·
   MC incr./cliente · MC acum./cliente`.
3. **Export CSV** dos deals da safra: `nome (pedido) · safra · idade · tipo_de_venda · ramo ·
   receita · cmv · mc_produto`. **Sem e-mail** (PRODUCT §8 — o painel não exibe e-mail; o número do
   pedido é a chave de auditoria e liga na planilha).

## 3. Regra inviolável
- **NÃO muda a matemática da MC.** A auditoria só **re-expõe** a mesma `mc_produto` já calculada:
  para o ramo real, `Receita − Σdeduções% − CMV = mc_produto` (idêntico ao Lucro Bruto do painel por
  pedido); para o estimado, `0,25 × valor = mc_produto`. Refactor de extração (`_preparar_deals`)
  compartilhado com `calcular_coortes` — o triângulo e a auditoria saem da **mesma** enriquecimento.
- **Reconciliação obrigatória na tela:** a "MC parcial por cliente" da cascata total tem de **bater**
  com o valor da safra no triângulo (`mc_ate_hoje`). Mostrar ✓/✗.
- Deduções só incidem sobre a **receita real** (o estimado não leva linha de dedução — os 25% já são
  líquidos). Deixar isso **explícito** na tela (senão parece que faltam deduções nas safras velhas).
- Só **idades fechadas** entram (mesma régua R11).

## 4. Critérios de aceite
- [ ] CA1. Ligar o toggle mostra as duas cascatas + botão de export, sem exceção.
- [ ] CA2. Na cascata real, `Receita − Σdeduções − CMV` = Lucro Bruto real, e a soma bate com a
  `mc_produto` dos deals reais da safra (conferível).
- [ ] CA3. A "MC parcial/cliente" da cascata total = `mc_ate_hoje[S]` do triângulo (reconciliação ✓).
- [ ] CA4. A cascata por idade: MC acum./cliente da última idade = a MC total/cliente; e cada idade
  soma as incrementais anteriores.
- [ ] CA5. O CSV baixa com 1 linha por deal, sem coluna de e-mail, e a soma de `mc_produto` = a da
  cascata.
- [ ] CA6. Uma safra recente (real) mostra deduções abertas; uma safra velha (estimada) mostra o ramo
  estimado com a nota "deduções embutidas nos 25%". As outras abas e o triângulo não mudam.

## 4-bis. Redesenho da cascata (2026-07-13, pedido do João)

Substitui o layout "medida/estimada" por um que separa **aquisição × retenção**, no formato das
outras abas:

- **Bloco A — MC dos novos (1ª compra da safra):** cascata **completa igual à V2** — `Vendas-novos
  → Devoluções, Chargebacks, PIS/COFINS, ICMS, Outras → CMV-novos → Frete, Embalagem, Gateways,
  Plataforma, Antecipação → Lucro Bruto-novos → (−) Mídia inteira → MC-novos`. (Deve ~bater com a
  aba Aquisição do mês; diverge só pelos cross-canal.) A parte estimada dos novos, se houver, entra
  como **uma linha** "Margem estimada (novos, 25%)".
- **Bloco B — MC de recompra (compras seguintes da turma):** agrupado — `Vendas-recompra → (−)
  Deduções (27,5% da receita) → (−) CMV → (= ) MC-recompra`. **Sem mídia** (a mídia é o custo de
  aquisição, já no bloco A). Estimada em 1 linha, se houver.
- **Bloco C — MC total:** `MC-novos + MC-recompra = MC total`, e `÷ N = MC total por cliente`
  (o número do triângulo/curva). **Depende do horizonte de meses** analisado.
- **Horizonte:** um **slider** "analisar recompra até m+K" (padrão = último mês fechado da safra).
  A recompra e o total recomputam para o horizonte; a reconciliação passa a ser com
  `mc_acumulada[safra, K]` do triângulo.
- **Partição:** novos = `tipo_de_venda == "Primeira Compra"`; recompra = o resto. Sem matemática
  nova — só re-expressa a mesma `mc_produto`. MC-novos + MC-recompra reconcilia com o triângulo.

## 5. Riscos
- **Performance:** `detalhar_safra` reusa a ponte (barata, filtra por safra); cacheado por (safra,
  dia) e só roda com o toggle ligado. Sem impacto quando desligado.
- **Nada de escrita** (só leitura + download client-side).
