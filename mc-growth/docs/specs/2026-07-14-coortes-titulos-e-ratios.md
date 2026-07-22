# Spec — Aba Cohorts: títulos de seção + duas tabelas de ratio sobre o CAC

> **Data:** 2026-07-14 · **Modo:** B (construção) · **Arquivo tocado:** `views/coortes.py`
> (+ um helper de cor em `coortes_ui.py`).
>
> **Natureza:** apresentação. **Nenhum número novo é calculado do zero** — as duas tabelas novas
> são divisões de números que o `ResultadoCoortes` já entrega hoje. `coortes.py` e `cascata.py`
> **não são tocados**. O guarda (`checar_coerencia.py`) segue valendo sem alteração.

---

## 1. O pedido do João (4 itens)

1. Um **título de seção** antes da tabela de receita: **"LTV e CAC por Cohort (Receita)"**.
2. **Abaixo** dessa tabela, uma tabela com as **mesmas colunas**, mostrando o **ratio LTV ÷ CAC**.
3. Um **título de seção** antes dos triângulos de MC: **"LTV MC e CAC por cohort (Margem de contribuição)"**.
4. **Entre** o triângulo de MC por cliente e o de MC absoluta, uma tabela com as **mesmas colunas**,
   mostrando o **ratio MC por cliente ÷ CAC**.

---

## 2. O que a tela passa a ter (ordem final)

```
KPIs do cohort em foco (não muda)
──────────────────────────────────────────────────────────────
# LTV e CAC por Cohort (Receita)                        ← título NOVO (item 1)
    Receita por cohort — LTV (receita acumulada por cliente)   [tabela existente]
    LTV ÷ CAC — quantas vezes o cohort devolveu o CAC          [tabela NOVA  (item 2)]
──────────────────────────────────────────────────────────────
# LTV MC e CAC por cohort (Margem de contribuição)      ← título NOVO (item 3)
    Triângulo de coortes — MC por cliente                      [tabela existente]
    MC por cliente ÷ CAC                                       [tabela NOVA  (item 4)]
    Triângulo de coortes — MC absoluta (R$ da turma inteira)   [tabela existente]
──────────────────────────────────────────────────────────────
```

Os títulos novos são `st.header` (nível acima); os títulos que já existem continuam `st.subheader`.
Nada é removido, nada muda de lugar.

---

## 3. Tabela nova A — **LTV ÷ CAC** (item 2)

**Colunas** (as mesmas da tabela de receita, decisão do João de 2026-07-14):

| Cohort | Novos Clientes | CAC | Receita 1ª Compra | LTV m+0 | LTV m+1 | … |
|---|---|---|---|---|---|---|
| texto | nº | **R$** (referência) | **×** (ratio) | **×** | **×** | |

- `Receita 1ª Compra` = `ticket_primeira_compra[S] ÷ CAC[S]`
- `LTV m+x` = `ltv[S, x] ÷ CAC[S]`
- O **CAC fica em R$** (é o denominador — precisa estar visível para o número fazer sentido).
- **Formato:** `3,26×` (2 casas, vírgula decimal, sufixo `×`).

**Leitura:** "para cada R$ 1 de CAC, a turma devolveu R$ 3,26 de **receita bruta** até essa idade".
É o clássico LTV:CAC — mas com **receita**, não com margem. Não é uma régua de lucro.

---

## 4. Tabela nova B — **Lucro Bruto por cliente ÷ CAC** (item 4)

> **[CORRIGIDO em 2026-07-14, pelo João, vendo a tela]** Esta tabela nasceu como `MC ÷ CAC` — e
> isso **conta a mídia duas vezes**: a MC **já desconta** o Ad Spend (uma vez, no m+0), então
> dividi-la pelo CAC põe a mídia no numerador *e* no denominador. O numerador certo é o **Lucro
> Bruto** (o que a turma gerou **antes** da mídia): `ResultadoCoortes.lucro_bruto`. **O empate
> passa a ser `1,00×`**, não zero. O texto abaixo ficou como estava para registro do que foi
> pensado — o que vale é este bloco.

**Colunas** (as mesmas do triângulo de MC por cliente):

| Cohort | Clientes | CAC | MC primeira compra | m+0 | m+1 | … |
|---|---|---|---|---|---|---|
| texto | nº | **R$** (referência) | **×** (ratio) | **×** | **×** | |

- `MC primeira compra` = `mc_primeira_compra[S] ÷ CAC[S]`
- `m+x` = `mc_acumulada[S, x] ÷ CAC[S]`
- A célula estimada mantém o **`*`** (CMV em 30%), igual ao triângulo de cima.

**Leitura (confirmada pelo João):** a MC **já tem a mídia descontada**, então este ratio é
**líquido**: `0,00×` = a turma **empatou** (payback); `0,40×` = devolveu 40 centavos de MC limpa
por real de CAC; **negativo** = ainda no vermelho. **Não** é o "ROAS de margem" (esse seria
`MC + CAC ÷ CAC`, sempre ≥ 1 quando a margem é positiva) — o João escolheu a versão literal.

---

## 5. Cor: gradiente de verde (pedido do João)

> *"as duas pintadas, mas somente em tons de verde, sendo mais escuro o verde dos maiores ratios."*

- **Escala sequencial de verde por COLUNA** *(ajuste do João, ao ver a 1ª versão)*: cada coluna
  tem a **sua própria régua** (min→max daquela coluna na tela). Motivo: com uma escala única por
  tabela, o LTV cresce com a idade, então as colunas novas (m+0, m+1) nasciam **todas claras** e as
  velhas todas escuras — a cor mostrava a *idade*, não o *cohort*. Por coluna, ela compara o que
  interessa: **o m+7 de um cohort contra o m+7 dos outros**.
- Tom claro = ratio baixo; tom escuro = ratio alto. Texto branco a partir da metade escura da
  escala (senão fica ilegível).
- **Pintadas:** as células de idade (`LTV m+x` / `m+x`) **e** a coluna de ratio da 1ª compra
  (`Receita 1ª Compra` / `MC primeira compra`), cada uma com a sua escala.
- **Não** pintadas: `Cohort`, `Clientes`/`Novos Clientes` e `CAC` (o CAC está em R$, é o
  denominador — não é um múltiplo).
- Helper novo em `coortes_ui.py`: `verde_gradiente(v, minimo, maximo) -> css` (uma função, sem
  dependência nova — interpolação linear entre dois hex).

### ⚠️ D1 — a decisão que preciso que você confirme

O triângulo de MC de cima usa **verde/vermelho pelo sinal**: a cor É a linha do zero. Se a tabela
de ratio da MC for **só verde**, um cohort **no vermelho** (ratio negativo) vai aparecer como um
**verde clarinho** — e verde clarinho não parece um aviso. O risco é ler "está tudo bem, só fraco"
onde na verdade é "essa turma ainda não pagou a mídia".

Três saídas (escolha na aprovação do plano):

- **(a) Como você pediu, literal.** Só tons de verde; o negativo é o tom mais claro da escala.
  Ponho a régua na legenda ("abaixo de `0,00×` a turma ainda não se pagou").
- **(b) Verde a partir do zero; abaixo do zero, o número em vermelho** (fundo branco).
  Mantém "só tons de verde" no fundo **e** preserva a linha do zero. ← **minha recomendação**
- **(c) Verde/vermelho pelo sinal** nas duas, igual ao triângulo (aí a escala de intensidade some).

Na tabela de **LTV ÷ CAC** o problema não existe (receita bruta nunca é negativa) — verde
gradiente puro, sem ressalva.

---

## 6. Bordas (o que não pode virar número falso)

| Caso | O que a tela faz |
|---|---|
| `CAC[S]` é `None` (a aba `Midia` não cobre o mês da safra) | a linha inteira de ratio vira **"—"** (nunca 0, nunca divide por nada) |
| `CAC[S]` é `0` | idem: **"—"** (divisão indefinida) |
| célula `m+x` vazia (mês não fechou) | célula vazia, como nos triângulos |
| célula estimada (CMV 30%) | mantém o **`*`** (a marca da tabela de origem) |

---

## 7. Critério de aceite (testável)

1. Os dois títulos novos aparecem, nos lugares dos itens 1 e 3.
2. **Tabela A:** para cada cohort com CAC, `LTV m+x mostrado == ltv[S,x] / cac[S]` (conferido em
   ≥ 3 células contra a tabela de receita imediatamente acima).
3. **Tabela B:** `m+x mostrado == mc_acumulada[S,x] / cac[S]`; e o **sinal** de cada célula bate
   com a cor da célula correspondente no triângulo de cima (verde lá ⇒ ratio ≥ 0 aqui).
4. Cohort sem CAC (se houver na janela mostrada) exibe **"—"**, não um número.
5. `python3 checar_coerencia.py` continua passando (nada de dinheiro mudou).
6. `AppTest` sobe as 5 telas sem exceção.
7. As 3 tabelas antigas ficam **byte-idênticas** (mesmos valores, mesma ordem, mesmas cores).

---

## 8. O que esta spec NÃO faz

- Não muda MC, CMV, mídia, CAC ou qualquer definição do §11 do `CLAUDE.md`.
- Não cria alvo/régua ("LTV:CAC de 3× é bom") — calibrar alvo é **V5**, parkeado. A tela mostra o
  número; o julgamento é do João.
- Não mexe na aba A2 nem nas telas Geral/Aquisição.
