# Sessão 2026-07-04 — roadmap-motor-crescimento

> Log da sessão. Não é resumo de commit — é o "porquê" e o "o que vem depois".

---

## Objetivo da sessão

Mapear a evolução do MC Growth, da V1 atual até o modelo do documento
`motor-crescimento-lucrativo-true-classic.md`, em passos pequenos, com destino final claro.

---

## O que foi feito

- Trouxe o documento de Downloads para a raiz do projeto
  (`motor-crescimento-lucrativo-true-classic.md`). Havia dois arquivos parecidos; escolhido o
  de 37,7 KB (bate com o print).
- Li o documento inteiro + `PRODUCT.md` + `ARCHITECTURE.md`. Modo A (estratégia).
- Propus o caminho: destino (estrela-guia) → volta até a V1, com 3 releituras (instrumento de
  decisão, não relatório; calibrar a régua da Minimal, não copiar a True Classic; a dobradiça
  é o cliente novo×recorrente).
- Rodei `/devil-advocate` sobre o próprio caminho (furos: margem como gate, incrementalidade
  além do porte, custo de oportunidade, mandato para agir). João optou por seguir, mas
  **comprometer só até a V4**.
- Escrevi o roadmap (`docs/ROADMAP.md`) e o ADR de direção
  (`docs/decisions/2026-07-04-roadmap-motor-crescimento.md`).
- Criei o prompt de handoff entre versões
  (`vibe-coding-workflow/prompts/13-handoff-product-md-proxima-versao.md`): ao fechar uma
  versão, ele pega o entregável dela + a próxima versão do ROADMAP e gera o `PRODUCT.md` da
  próxima, reusando o `01-gerar-product-md.md`. Arquiva o PRODUCT.md anterior em
  `docs/product-history/`. Confirmado: e-mail do cliente vem da base (V2 destravada).

---

## Decisões tomadas

### Escopo comprometido = V1 → V4; V5-V7 parkeados
- **Decisão:** roadmap de 7 versões, mas construir só até a V4 (cliente novo×recorrente →
  custo cheio por pedido → lucro por cliente novo + coortes). Depois, rodar o modelo por um
  tempo e revisitar V5-V7.
- **Por quê:** V4 é o menor ponto onde a tese do modelo pode ser testada com números reais da
  Minimal, sem construir o aparato caro de incrementalidade antes de saber se vale.
- **Descartado:** (A) comprometer V1→V7 de uma vez — custo de oportunidade e risco de
  construir para uma estratégia que a Minimal talvez não possa rodar; (B) só consertar a V1 —
  não responde a pergunta central do modelo.
- **ADR criado?** sim — `docs/decisions/2026-07-04-roadmap-motor-crescimento.md`.

### Respostas do João que calibram o roadmap
- Margem bruta: **não sabe o número** → virou entrega da V4 (medir), não pré-requisito.
- Identificador de cliente: **e-mail** → V2 é passo curto (a dobradiça existe).
- Recompra: **sabem algo, mas melhor mapear no projeto** → medir na V4.

---

## Problemas encontrados

### O modelo é de decisão de gasto; o painel não move budget
- **Descrição:** o valor da True Classic vem de *agir* (realocar mídia). O painel do João não
  controla o gasto.
- **Causa raiz:** instrumento ≠ mandato.
- **Solução aplicada:** registrado no roadmap (seção 3) e no ADR como condição a checar antes
  de V5 — "testar o mandato antes do instrumento".
- **Status:** aberto (a resolver antes de V5, não agora).

---

## Estado do projeto agora

### Funcionando
- V1 (painel de MC) e Auditoria de custos — inalterados nesta sessão.
- Roadmap V1→V4 documentado, com critério de aceite e gancho na V1 por versão.

### Quebrado / incompleto
- Nada quebrado nesta sessão (só documentos). Bugs herdados seguem: dobra de kit (será tratada
  na V3) e insumos de custo cheio ainda não estão na planilha (risco da V3).

---

## Próximo passo

1. **V2 — spec.** Escrever `docs/specs/` da V2 (chave de cliente por e-mail + classificação
   novo/recompra + relatório de qualidade da chave). Modo B.
2. Antes de codar a V2, confirmar com o João de onde vem o e-mail na base (coluna/fonte) — é
   um dado que a planilha atual pode não expor ainda.
3. Manter o encaminhamento pendente da base de itens limpa (time de Dados) — entra na V3.

---

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** nova linha na seção 5 (decisões arquiteturais) apontando o roadmap.
- **`CLAUDE.md`:** Seção 0 atualizada (estado/próximo passo apontam o roadmap V1→V4).
- **`docs/decisions/`:** criado `2026-07-04-roadmap-motor-crescimento.md`.
- **`docs/specs/`:** nada nesta sessão (V2 vem na próxima).
- **`PRODUCT.md`:** sem mudança (o produto-destino está no ROADMAP; PRODUCT.md descreve a V1).
- **`vibe-coding-workflow/prompts/`:** criado `13-handoff-product-md-proxima-versao.md`.
- **Novo:** `docs/ROADMAP.md` (entregável da sessão) e o documento-fonte na raiz.
