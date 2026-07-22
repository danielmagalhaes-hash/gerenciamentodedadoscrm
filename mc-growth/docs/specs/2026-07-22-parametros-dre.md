# Spec — Atualizar os percentuais da DRE (deduções + custos variáveis)

**Data:** 2026-07-22 · **Modo:** B · **Toca dinheiro:** SIM · Irmã da spec `2026-07-22-fonte-custos-3-2`.

## Objetivo
O Financeiro passou percentuais atualizados da DRE. Trocar os valores em `cascata.PARAMETROS`.
Fonte: valores enviados pelo João (do Financeiro) em 2026-07-22.

## De-para (chave → hoje → novo)
| Chave | Hoje | Novo |
|---|---|---|
| `pis_cofins_cbs` | 1,75 | **4,74** |
| `icms_ibs` | 12,54 | **13,73** |
| `devolucoes` | 3,48 | **3,32** |
| `chargebacks` | 0,15 | 0,15 (igual) |
| `frete` | 4,80 | **5,02** |
| `gateways` | 1,70 | **1,37** |
| `plataforma` | 0,90 | **0,44** (PLAT E-Commerce) |
| `antecipacao` | 1,60 | **1,10** |
| `embalagem` | 0,57 | **mantido** (não veio na lista — CONFIRMADO pelo João 2026-07-22) |
| `outras_deducoes` | 0,00 | **mantido** (não veio na lista) |

Soma deduções+custos: **27,49% → 30,44%** (+2,95 pts). Margem de produto estimada
(1 − soma − CMV 30%) cai de 42,5% para **39,56%**.

## Onde
Só `cascata.PARAMETROS`. Não mexe em custo por SKU (3.2), CMV estimado (30%), nem lógica.

## Aceite
1. Valores trocados; soma bate 30,44%.
2. `checar_coerencia.py` 7/7.
3. `AppTest` das 7 telas OK.
4. Impacto na MC de junho medido (com a base de custo 3.2 já ativa).

## Resolvido
**Embalagem (0,57%) continua** — confirmado pelo João em 2026-07-22.
