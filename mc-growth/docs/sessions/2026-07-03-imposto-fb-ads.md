# Sessão 2026-07-03 — imposto-fb-ads

> Log da sessão. Não é resumo de commit — é o "porquê" e o "o que vem depois".

---

## Objetivo da sessão

Ajustar o cálculo do Ad Spend: embrutecer o gasto de FB Ads pelo imposto de 12,15% pago ao investir.

---

## O que foi feito

- Confirmado (olhando a planilha) que a coluna C da aba `Midia` é `fb_investimento` (FB Ads); Ad Spend somava C+D+E crus.
- Implementado o gross-up de FB em `cascata.py`: `fb_real = Σ(fb_investimento) / (1 − IMPOSTO_FB_ADS)`, com `IMPOSTO_FB_ADS = 0.1215`. Só FB; Google e Google institucional seguem crus.
- Medido o impacto (junho/2026): FB puro R$1.032.622 → real R$1.175.437 (+R$142.816). Ad Spend R$1.277.620 → R$1.420.436. MER 6,33 → 5,69. MC R$1.975.351 → R$1.832.535.
- Verificado: aritmética fecha; painel roda sem exceção.

---

## Decisões tomadas

### FB Ads embrutecido pelo imposto (gross-up)
- **Decisão:** `fb_real = fb_investimento / (1 − 0,1215)`; Ad Spend = fb_real + Google + Google instituc.
- **Por quê:** o imposto de 12,15% é desembolso real; sem ele, MC e MER ficam otimistas.
- **Descartado:** soma pura (subestima); acréscimo simples ×1,1215 (errado — o imposto é 12,15% do valor final, então é gross-up ÷0,8785).
- **ADR criado?** sim — `docs/decisions/2026-07-03-imposto-fb-ads.md`.

---

## Problemas encontrados

- Nenhum. Mudança pontual e localizada.

---

## Estado do projeto agora

### Funcionando
- Painel v1 com Ad Spend/MER/MC já considerando o imposto de FB. Três módulos passam nos testes.

### Quebrado / incompleto
- Nada novo. (Pendências do João seguem: validar a MC e lançar os custos faltantes no editor do painel.)

---

## Próximo passo

1. João validar a MC de junho **já com o imposto de FB** (≈ R$1,83M) e lançar os custos faltantes (Perfume 10ML = 11,83) no editor do painel.
2. Depois da validação, escolher a 1ª feature da "prioridade 3" (comparação com período anterior é a candidata).

---

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** invariante da aba `Midia` atualizado; nova linha na tabela de decisões.
- **`CLAUDE.md`:** seção 0 (MC de referência de junho passa a ~R$1,83M com o imposto).
- **`docs/decisions/`:** criado `2026-07-03-imposto-fb-ads.md`.
- **`docs/specs/`:** R8 atualizado com o gross-up.
- **`PRODUCT.md`:** glossário Mídia paga/Ad Spend, cartão Ad Spend e linha da cascata atualizados.
