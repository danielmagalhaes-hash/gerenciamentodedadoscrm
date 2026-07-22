# ADR — Direção de evolução: do painel de MC ao Motor de Crescimento Lucrativo (escopo V1→V4)

**Data:** 2026-07-04
**Status:** Aceito
**Tema:** roadmap-motor-crescimento

---

## 1. Contexto

O João trouxe o documento `motor-crescimento-lucrativo-true-classic.md` — o modelo da True
Classic de "aquisição é crescimento, recompra é lucro", com decisão de mídia governada por
lucro por cliente novo *fully-loaded*, coortes, incrementalidade e base como ativo. O pedido:
mapear a evolução do MC Growth, da V1 atual (painel de MC de período fechado) até esse modelo,
em **passos pequenos, mas importantes**, com um destino final claro e o caminho de volta até
hoje.

A V1 hoje é um retrovisor: mostra a MC de um período, "blended" (novos e recorrentes juntos),
só Shopify, com custo cheio parcial. O modelo do documento é um instrumento de decisão de
aquisição para a frente. A distância entre os dois precisa ser sequenciada para não construir
capacidade especulativa nem "adotar a régua antes da instrumentação" (armadilha nº 6 do
próprio documento).

Rodamos um `/devil-advocate` sobre o caminho. Ele levantou pontos válidos (margem bruta como
gate, risco de sofisticação além do porte na incrementalidade, custo de oportunidade de um
projeto de 6-12 meses, mandato para agir sobre o número). O João optou por **seguir com o
plano**, mas **comprometer escopo só até a V4**, rodar o modelo por um tempo e então revisitar.

---

## 2. Decisão

Adotaremos um roadmap de 7 versões (`docs/ROADMAP.md`) com **escopo comprometido apenas até a
V4**:

- **V2** — identidade de cliente (e-mail) e separação novo × recorrente.
- **V3** — P&L por pedido com custo cheio (os 4 custos que "vazam") e conserto da dobra de kit.
- **V4** — lucro por cliente novo + primeiras coortes; medir margem bruta e recompra reais.

Ao fim da V4, **paramos de construir e rodamos o modelo por um tempo** antes de decidir sobre
V5 (régua calibrada), V6 (incrementalidade) e V7 (base como ativo), que ficam **parkeados como
hipóteses**, não como compromisso.

Três releituras orientam o caminho: (1) é instrumento de decisão, não relatório; (2) miramos o
instrumento e calibramos a régua da **Minimal**, não os números da True Classic; (3) a
dobradiça é o **cliente** (novo × recorrente).

---

## 3. Motivação

- **Passos pequenos que destravam decisões reais** (pedido do João): cada versão vale pela
  decisão que habilita, não pela tela nova. V2 destrava "quanto do lucro vem de recompra";
  V3, "este pedido dá lucro de verdade"; V4, "qual meu break-even real e a recompra
  justifica gastar adiantado".
- **Respeita as armadilhas do documento:** instrumentação antes da régua (nº 6), nunca alvo
  sobre margem de fachada (nº 1), calibrar a régua própria (nº 2), coorte acima de agregado
  (nº 4).
- **Limita o risco:** V4 é o menor ponto onde a tese do modelo pode ser *testada* com dados
  reais da Minimal, sem construir o aparato caro de incrementalidade (V6) antes de saber se
  vale.
- Alinhado ao Modo A/B do `CLAUDE.md`: o roadmap é o documento-produto desta sessão (Modo A);
  V2-V4 serão features de construção (Modo B) com spec própria cada.

---

## 4. Alternativas consideradas

### Alternativa A: Comprometer o roadmap inteiro (V1→V7) de uma vez
- **Descrição:** planejar e construir até a base-como-ativo e a régua horária.
- **Prós:** visão completa; nada fica "no ar".
- **Contras:** 6-12 meses de construção antes de testar a tese; incrementalidade pode exceder
  o porte de mídia da Minimal; margem bruta desconhecida pode invalidar V5-V7.
- **Por que foi descartada:** custo de oportunidade alto e risco de construir para uma
  estratégia (break-even agressivo) que a Minimal talvez não possa rodar. Melhor testar na V4.

### Alternativa B: Só consertar a V1 (dobra de kit + confiança na MC) e parar
- **Descrição:** não perseguir o modelo; deixar a MC atual robusta e usar.
- **Prós:** barato, rápido, foco.
- **Contras:** não responde a pergunta central do documento (novo × recorrente, lucro por
  cliente novo); mantém o painel como retrovisor.
- **Por que foi descartada:** o João quer caminhar em direção ao modelo; V2-V4 entregam o
  essencial disso a um custo controlado (e a V3 já inclui o conserto da V1).

---

## 5. Consequências

### Positivas
- Caminho claro e sequenciado, com critério de aceite e gancho na V1 por versão.
- V4 entrega, de fato, um ponto de teste da tese com números reais da Minimal.
- Margem bruta e recompra — hoje desconhecidas — passam a ser entregas medidas (V4).

### Negativas
- V3 depende de dados que hoje não estão na planilha (custo de devolução/CX/juros/criativo);
  risco de empacar como a base de itens empacou. Mitigação: marcar como "% provisório" na
  tela até o dado real vir.
- "Lucro por cliente novo" (V4) embute uma alocação de mídia *blended* enquanto a mídia não
  separar aquisição de remarketing — declarada como aproximação.
- Chave de cliente por e-mail é suja na borda (guest, duplicado); V2 precisa medir a sujeira.

### O que essa decisão FECHA
> - Fecha a opção de tratar o painel como um relatório de MC "e pronto" — o norte agora é
>   decisão de aquisição.
> - Fecha (por ora) qualquer construção de V5-V7 sem antes rodar a V4 e revisitar margem,
>   recompra e mandato.
> - Fecha a ideia de importar os alvos numéricos da True Classic (break-even, "gaste all day
>   long") sem calibrar com a margem/recompra reais da Minimal.

---

## 6. Implementação

- **Onde se materializa no código:** ainda não — é direção. V2 tocará `dados.py` (chave de
  cliente) e `cascata.py` (dimensão novo/recompra); V3 evolui `cascata.py`; V4 adiciona
  alocação de mídia e coorte. Cada versão terá spec própria em `docs/specs/`.
- **Migration/refactor necessário:** não agora.
- **Regra a adicionar no CLAUDE.md:** atualizar a Seção 0 (estado/próximo passo) apontando o
  roadmap. Feito nesta sessão.
- **Atualização no ARCHITECTURE.md (seção 5):** linha adicionada nesta sessão.

---

## 7. Revisão

- **Quando reavaliar:** ao concluir a **V4** — decisão explícita de rodar o modelo por um
  tempo antes de retomar V5+.
- **Sob que condições reverter:** se a margem bruta real (V4) mostrar que break-even é inviável
  e o objetivo do João mudar; se a cadeia de dados não entregar os insumos de custo cheio
  (V3) e o custo de manter estimativas provisórias superar o valor; se faltar mandato para
  agir sobre o número.
