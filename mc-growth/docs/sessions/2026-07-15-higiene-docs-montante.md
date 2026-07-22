# Sessão 2026-07-15 — higiene-docs-montante

> Log da sessão. Não é resumo de commit — é o "porquê" e o "o que vem depois".

---

## Objetivo da sessão

Corrigir os documentos vivos que ficaram factualmente errados depois do trabalho de 14/07 (o
próximo-passo (2) do `CLAUDE.md`: idade "vem do campo" × é calculada; fórmula 25% × 30%). Sessão só
de documentação — **nenhum código tocado**.

---

## O que foi feito

Descoberta central: **a maior parte do item (2) já estava feita** — quando o `PRODUCT.md` virou V4,
as correções de idade (§3) e de 30% (§6) já tinham entrado. A nota do próximo-passo é que estava
velha. Sobraram **resíduos vivos**, que foram corrigidos:

- `PRODUCT.md` §4 (atributos do deal): `meses_desde_primeira_compra` ganhou o aviso ⚠️ (é idade do
  cliente no export, não serve de idade da coorte); `valor` deixou de ser "a confirmar" e virou "a
  receita decidida" (`PRODUCT.md`).
- `PRODUCT.md` §5 (Fluxo A): trocado "a coluna de coorte vem pronta do pipeline" por "a idade é
  **calculada** no painel" (`PRODUCT.md`).
- `PRODUCT.md` §8 (Dados e fonte): o trecho "CMV real só na janela abr–jul/2026 (MVP)" foi
  reescrito — o CMV real cobre **out/2021→hoje** em 3 camadas; a "pendência de arquitetura" virou
  "resolvida" (arquivo local `itens_historico.csv`, padrão torneira). Resíduos medidos registrados
  (2021 estimado; ~6,4% das unidades de 2023 sem custo) (`PRODUCT.md`).
- `ARCHITECTURE.md`: descrição viva do módulo `coortes` (§2) e o ponto frágil da idade (§6)
  trocaram `0,25×valor`/"só na janela" pela realidade de hoje (`0,30`, 3 camadas); a linha "corrigir
  PRODUCT.md a montante" virou "corrigido em 2026-07-15"; bloco datado no topo registrando a passada
  (`ARCHITECTURE.md`).
- `CLAUDE.md`: o próximo-passo (2) e (4) foram atualizados — (2) marcado FEITO nos docs vivos; (4)
  a "Opção 1" marcada como **já entregue** (era o CMV real histórico de 14/07), sobrando só afinar
  resíduos (`CLAUDE.md`).

---

## Decisões tomadas

### A spec da V4 fica congelada
- **Decisão:** não reescrever `docs/specs/2026-07-10-v4-coortes-recompra.md` (que ainda diz "idade =
  campo" e "25%"), mesmo estando factualmente errada.
- **Por quê:** regra do próprio projeto (`CLAUDE.md` §6): spec é **foto do dia**; quem corrige o
  rumo é o ADR (e os ADRs de 30% e de idade-calculada existem). Reescrever spec a transformaria num
  documento vivo, contra a convenção.
- **Descartado:** (a) pôr avisos de "superado" no topo da spec; (b) reescrever as ~20 ocorrências.
- **ADR criado?** não (é aplicação de uma regra que já existe).

---

## Problemas encontrados

### A nota do próximo-passo estava desatualizada em cadeia
- **Descrição:** o `CLAUDE.md` listava como pendências coisas já feitas — a correção do `PRODUCT.md`
  (feita ao virar V4), o §8 "só abr–jul" (superado por 14/07) e a "Opção 1" (entregue por 14/07).
- **Causa raiz:** as notas de próximo-passo são escritas no fim de cada sessão e não são revisadas
  quando o trabalho seguinte as torna obsoletas.
- **Solução aplicada:** reescrever os itens (2) e (4) do próximo-passo com o estado real.
- **Status:** resolvido.

---

## Estado do projeto agora

### Funcionando
- As 4 telas rodam (Geral, Aquisição, Cohorts, Auditorias), unificadas no HubSpot.
- CMV real cobrindo out/2021→hoje em 3 camadas (base histórica → planilha → 30%).
- Docs vivos (`PRODUCT.md`, `ARCHITECTURE.md`, `CLAUDE.md`) agora **batem** com o código.

### Quebrado / incompleto
- Nada quebrado. Pendências abaixo são melhorias, não defeitos.

---

## Próximo passo

1. **João roda ao vivo** e valida meses passados (faixa amarela de estimado) + aba Cohorts.
2. **Cartão de recompra 90d + 180d** — a 2ª compra típica leva 123 dias; 90d sozinho é
   conservador (só 42% recompram em ≤90d; 60% em ≤180d). Não atacar ainda (decisão do João nesta
   sessão).
3. **Afinar resíduos de custo:** 2021 ainda estimado (base começa out/2021); ~6,4% das unidades de
   2023 sem custo cadastrado.
4. Pendências herdadas: 137 SKUs sem custo na aba 3.1 (`docs/skus-custo-zerado-aba-3-1.csv`) ao time
   de Dados.
5. **A confirmar (rápido):** se o "re-base da V2 no HubSpot" já morreu — a Aquisição parece já usar o
   HubSpot (`tipo_de_venda`) desde a unificação de 14/07; não reverificado a fundo.

---

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** bloco datado 2026-07-15 no topo; §2 (coortes) e §6 (idade) corrigidos de
  `0,25`/"só na janela" para `0,30`/3 camadas; linha "corrigir a montante" fechada.
- **`CLAUDE.md`:** próximo-passo (2) marcado FEITO; (4) "Opção 1" marcada como entregue.
- **`docs/decisions/`:** nenhum criado (a decisão "spec fica congelada" é aplicação de regra
  existente).
- **`docs/specs/`:** nenhum criado/atualizado (spec V4 deliberadamente congelada).
- **`PRODUCT.md`:** §4, §5 (Fluxo A) e §8 corrigidos (idade calculada; receita = `valor`; CMV real
  na história inteira).
