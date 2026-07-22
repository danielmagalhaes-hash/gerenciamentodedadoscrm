# ADR — Imposto sobre investimento em FB Ads (gross-up do gasto)

**Data:** 2026-07-03
**Status:** Aceito
**Tema:** imposto-fb-ads

---

## 1. Contexto

O Ad Spend (mídia paga) do painel somava as três colunas de investimento cruas
(`fb_investimento` + `google_investimento` + `google_institucional_investimento`). O João
apontou que **ao investir em FB Ads a empresa paga um imposto de 12,15%** que não estava
sendo contabilizado — ou seja, o desembolso real de FB é maior que o valor puro da coluna.

---

## 2. Decisão

O gasto de FB Ads passa a ser **"embrutecido" (gross-up) pelo imposto**:

```
fb_real  = Σ(fb_investimento) / (1 - 0,1215)      # = ÷ 0,8785
Ad Spend = fb_real + google_investimento + google_institucional_investimento
```

O imposto vale **só para FB Ads**. Google e Google institucional continuam pelo valor puro.
A alíquota fica na constante `cascata.IMPOSTO_FB_ADS = 0.1215`.

---

## 3. Motivação

- Reflete o **desembolso real** de mídia: o imposto de 12,15% é dinheiro que sai de fato.
- Torna a MC e o MER mais fiéis (o custo de mídia deixa de estar subestimado).
- Gross-up (÷ (1-imposto)), não soma simples (× (1+imposto)): o imposto é 12,15% do valor
  final, então o valor puro é 87,85% do real. Efeito prático: FB sobe ~13,83%.

---

## 4. Alternativas consideradas

### Alternativa A: somar o valor puro (como estava)
- **Contras:** subestima o gasto real de mídia; MER e MC otimistas.
- **Descartada:** não reflete o imposto que a empresa paga.

### Alternativa B: acréscimo simples (× 1,1215)
- **Contras:** matematicamente errado se o imposto é 12,15% do valor final (gross-up é o correto).
- **Descartada:** o João descreveu a conta como `/(1-0,1215)`.

---

## 5. Consequências

### Positivas
- Ad Spend, MER e MC passam a considerar o custo real de FB Ads.
- Alíquota centralizada numa constante — fácil de ajustar se o imposto mudar.

### Negativas / a lembrar
- Impacto material: junho +R$142,8k de Ad Spend → MC −R$142,8k, MER 6,33 → 5,69.
- Se um dia o Google também tiver imposto próprio, a regra precisará distinguir por canal.

### O que essa decisão FECHA
> - Tratar o Ad Spend como soma pura das colunas de investimento.

---

## 6. Implementação

- **Onde se materializa:** `cascata.py` — constante `IMPOSTO_FB_ADS` e cálculo de `fb_real`
  dentro de `calcular` (bloco Ad Spend/MER).
- **Migration/refactor:** não.
- **Atualização em PRODUCT.md / spec / ARCHITECTURE:** feita.

---

## 7. Revisão

- **Quando reavaliar:** se a alíquota do imposto de FB mudar, ou se o Financeiro definir
  outro tratamento para o imposto de mídia.
- **Sob que condições reverter:** definir `IMPOSTO_FB_ADS = 0`.
