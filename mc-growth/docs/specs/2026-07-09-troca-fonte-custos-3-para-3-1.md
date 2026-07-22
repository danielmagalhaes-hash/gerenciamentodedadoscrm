# Spec — Troca da fonte de custos (aba 3 → aba 3.1, com rede de segurança)

> Modo B (construção). Toca dinheiro (CMV/MC) → spec antes de implementar.
> Data: 2026-07-09.

## Pergunta / objetivo

Passar a fonte de custo por SKU da aba **"3. Custos"** (gid `423190064`, colunas
`SKU` / `Valor de Custo`) para a aba **"3.1. Custos"** (gid `1460088128`, colunas
`SKU` / `Custo`), que tem custos mais atualizados e mais cobertura — **sem** perder os
custos de SKUs que a 3.1 ainda não preencheu.

## Contexto medido (investigação de 2026-07-09)

- 3.1 tem **1698 SKUs** vs 1096 da 3 (+610 novos) e quase sem lixo (3 valores não
  numéricos vs 51 na 3). No geral é melhor.
- Porém **137 SKUs que tinham custo real na 3 estão zerados (R$0,00) na 3.1** — e caem em
  **famílias inteiras** (ex: `85010010xx` a R$152,90–155; `830200633x` a R$80). Custo zero
  de família inteira = "aba ainda não preenchida", não "produto grátis".
- Trocar puro 3→3.1 subestimaria o CMV nesses 137 → MC inflada. Por isso a rede de segurança.
- Lista dos 137: `docs/skus-custo-zerado-aba-3-1.csv` (a encaminhar ao time de Dados).

## Regra (fonte de verdade do cálculo)

Para cada SKU, o custo usado é **o primeiro que existir**, nesta ordem:

1. **`custos_extra.csv`** (correção local do João) — sempre vence. *(inalterado)*
2. **Aba 3.1** (principal) — se tiver valor **> 0**.
3. **Aba 3** (rede de segurança) — se a 3.1 estiver zerada/vazia/ausente **e** a 3 tiver
   valor **> 0**.
4. Nenhum dos acima → SKU **sem custo** → alerta na tela (comportamento atual).

**Decisão-chave:** custo **igual a 0 é tratado como "faltando"**, não como "grátis"
(decisão do João, 2026-07-09). Se algum item for genuinamente grátis, fica sem custo e o
João o define no editor (regra 1, que vence tudo).

## Dados de entrada

| Papel | Aba | gid | Colunas |
|---|---|---|---|
| Custo principal | 3.1. Custos | `1460088128` | `SKU`, `Custo` |
| Custo fallback | 3. Custos | `423190064` | `SKU`, `Valor de Custo` |

## O que muda no código (`dados.py`)

- `GIDS["Custos"]` → `1460088128` (3.1) e novo `GID_CUSTOS_FALLBACK = "423190064"` (3).
- `carregar_custos()` passa a: ler 3.1 (col `Custo`), ler 3 (col `Valor de Custo`),
  aplicar a regra do fallback (3.1>0 senão 3>0), e então `_aplicar_custos_extra` por cima
  (inalterado).
- **Contrato de saída inalterado:** ainda devolve `DataFrame[sku, valor_custo]`. Nada em
  `cascata.py` / `painel.py` muda.

## Como saber que deu certo (critério de aceite)

- CMV/MC de junho conferidos com o painel; **nenhum dos 137 SKUs fica com custo 0** por
  causa do fallback (todos recuperam o valor da aba 3).
- Ganho de cobertura: os 610 SKUs novos da 3.1 entram.
- `carregar_custos()` roda sem erro; `AppTest` do painel e da auditoria passam.
- Relatório antes/depois do CMV de junho registrado no log da sessão.

## Fora de escopo (anotado, não faço agora)

- Marcar na auditoria **de qual aba** veio cada custo (origem). Útil, mas mexe no contrato e
  na UI — fica para uma próxima se o João quiser.
- Preencher os 137 na 3.1 — é a montante (time de Dados). A rede de segurança é o paliativo.
