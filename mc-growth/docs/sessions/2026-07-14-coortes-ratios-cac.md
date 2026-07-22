# Sessão 2026-07-14 — Aba Cohorts: títulos de seção + duas tabelas de ratio sobre o CAC

> **Modo:** B (construção). **Spec:** `docs/specs/2026-07-14-coortes-titulos-e-ratios.md`.
> **Arquivos tocados:** `views/coortes.py`, `coortes_ui.py`. **Não tocados:** `coortes.py`,
> `cascata.py`, `dados.py` — nenhuma regra de dinheiro mudou.

## O que o João pediu

Quatro ajustes na aba **3. Cohorts**:
1. Título antes da tabela de receita: **"LTV e CAC por Cohort (Receita)"**.
2. Abaixo dela, a mesma tabela em **ratio LTV ÷ CAC**.
3. Título antes dos triângulos de MC: **"LTV MC e CAC por cohort (Margem de contribuição)"**.
4. Entre os dois triângulos, a mesma tabela em **ratio MC por cliente ÷ CAC**.

## O que foi feito

A tela ficou nesta ordem (nada saiu do lugar; só entraram os 2 títulos e as 2 tabelas):

```
# LTV e CAC por Cohort (Receita)                      ← título novo
    Receita por cohort — LTV                                (existia)
    LTV ÷ CAC                                               (NOVA)
# LTV MC e CAC por cohort (Margem de contribuição)    ← título novo
    Triângulo — MC por cliente                              (existia)
    MC por cliente ÷ CAC                                    (NOVA)
    Triângulo — MC absoluta                                 (existia)
```

**É só apresentação.** As duas tabelas novas **não calculam nada** — dividem números que o
`ResultadoCoortes` já entregava (`ltv`, `mc_acumulada`, `ticket_primeira_compra`,
`mc_primeira_compra`) pelo `cac` da mesma safra. Por isso `coortes.py` não foi aberto.

## As três decisões que o João tomou na aprovação

1. **O CAC fica em R$; todo o resto vira ratio** — inclusive a coluna da 1ª compra
   (`Receita 1ª Compra ÷ CAC`, `MC primeira compra ÷ CAC`). O CAC é o denominador: tem de
   estar visível para o múltiplo fazer sentido.
2. **O ratio da MC é literal e líquido.** A MC **já vem com a mídia descontada**, então
   `MC/CAC = 0,00×` significa **a turma empatou** (é o payback), `0,40×` = sobraram 40 centavos
   de MC limpa por real de CAC, e **negativo = ainda não pagou a mídia**. Ele recusou a variante
   "(MC + CAC) ÷ CAC" (o ROAS de margem, que nunca fica negativo).
3. **Cor = tons de verde, mais escuro para o múltiplo maior** — com uma ressalva que ele
   aceitou (opção **(b)** do plano): **abaixo do zero, fundo branco e número em vermelho**. Motivo:
   num gradiente só-verde, uma turma no vermelho apareceria como *verde clarinho* — e verde claro
   não parece um aviso. A linha do zero do triângulo precisava sobreviver na tabela de ratio.

## Ajuste depois de ele ver na tela (mesma sessão)

- **A escala do verde virou POR COLUNA** (era uma só por tabela). Com a escala única, o LTV cresce
  com a idade, então as colunas novas (m+0, m+1) saíam **todas claras** e as velhas todas escuras:
  a cor estava mostrando a **idade**, não o **cohort**. Por coluna, ela compara o que interessa —
  o m+7 de um cohort contra o m+7 dos outros.
- **A coluna de ratio da 1ª compra também foi pintada** (`Receita 1ª Compra` / `MC primeira
  compra`), com a escala dela. O `CAC` (em R$) e o nº de clientes seguem sem cor.
- **Bug de renderização corrigido:** o `R$ 1` da legenda virava fórmula matemática no Streamlit (o
  `$…$` do markdown) — saía *"para cada R 1 de mídia"* com o resto em fonte de código. Escapado
  (`R\$`).

## O que ficou provado

- `python3 checar_coerencia.py` → **todas as telas concordam** (Aquisição × A2, A2 × triângulo,
  subtotais das cascatas, triângulo absoluto ÷ clientes). Nada de dinheiro se moveu.
- `AppTest` sobe as **5 telas** sem exceção. A aba Cohorts passou de 3 para **5 tabelas** e de 4
  para **6 subheaders** — exatamente o esperado.
- **Ratios conferidos na safra 2026-06** (CAC R$ 173,65): LTV m+0 R$ 566,32 → **3,26×**;
  MC m+0 R$ 69,45 → **0,40×**; MC 1ª compra R$ 55,17 → **0,32×**.
- **Sinal preservado:** 0 células em que o sinal do ratio diverge do sinal do triângulo de origem
  (ou seja, tudo que está verde lá está ≥ 0 aqui).
- **Nenhuma safra sem CAC** nas 63 da base — o caminho do `"—"` é defensivo (a aba `Midia` cobre
  todos os meses de safra hoje).
- **As 3 tabelas antigas ficaram byte-idênticas por construção:** o diff de `views/coortes.py`
  só **adiciona** (a única linha removida é o `import`, reescrito).

## CORREÇÃO DE MÉTODO — o ratio da MC contava a mídia DUAS vezes (achado do João)

Ao ver a tabela na tela, o João apontou: **`MC ÷ CAC` conta a mídia duas vezes**. Está certo — a
MC **já tem a mídia descontada** (`coortes.py:306`: o Ad Spend sai uma vez, no m+0, e o acumulado
o carrega para as idades seguintes). Dividi-la pelo CAC põe a mídia no numerador (subtraída) **e**
no denominador. A decisão nº 2 da lista acima (o ratio "literal e líquido") foi **revogada por ele
mesmo** — e a variante que ele havia recusado no plano é a correta.

**O que passou a valer:** o numerador é o **Lucro Bruto acumulado por cliente** — o que a turma
gerou **antes** da mídia. A tabela virou **`Lucro Bruto ÷ CAC`**, e com ela a régua muda:

- **empate = `1,00×`** (não zero): a turma devolveu exatamente o que custou trazê-la;
- `1,40×` = gerou 40% a mais do que custou; **abaixo de `1,00×` = ainda não pagou a própria mídia**
  (número em vermelho — o `limiar` do `verde_gradiente` deixou de ser 0 e passou a ser parâmetro).

**Onde o número mora:** `coortes.py` ganhou `ResultadoCoortes.lucro_bruto` (R$/cliente acumulado,
sem mídia) e `lucro_bruto_primeira_compra`. Tirado do `inc` **ainda cru**, antes de o Ad Spend ser
subtraído — **não** somando o CAC de volta na tela: dinheiro tem um dono só.

**Provado:**
- `lucro_bruto = mc_acumulada + CAC` — **dif 0,0000000000** nas 64 safras (a mídia sai 1× só). A
  prova virou o **check nº 5 do `checar_coerencia.py`**, para não se perder.
- A linha do empate `1,00×` **coincide com o payback** do triângulo de MC: **0 células** em que
  "MC ≥ 0" e "LB/CAC ≥ 1,00×" discordam.
- Safra 2026-06 (CAC R$ 173,65): MC/cliente m+0 R$ 69,45 → o ratio velho dizia **0,40×**; o Lucro
  Bruto é R$ 243,10 → o ratio certo é **1,40×**. (A diferença entre os dois é exatamente 1,00 — o
  CAC contado a mais.)
- Nenhuma célula de Lucro Bruto negativa (a margem de produto é positiva em todas as safras).

## Página "A3 - Coortes - Lucro Bruto" — pedida e DESCARTADA na mesma sessão

O João chegou a pedir uma página nova (uma cópia da aba de coortes, com base no **Lucro Bruto**) e
**cancelou** depois da correção acima: *"Não precisa criar o A3. Não faz sentido."* E não faz
mesmo — a correção do ratio já trouxe o Lucro Bruto para dentro da aba Cohorts (em múltiplos do
CAC), e um triângulo de Lucro Bruto em reais seria só o triângulo de MC com a mídia somada de
volta (a identidade `LB = MC + CAC`), numa tela a mais sem decisão nova. **Não construir.**

## Pendências (não mexidas nesta sessão)

Seguem valendo as do `CLAUDE.md`: corrigir o `PRODUCT.md` §3/§6 (a idade da coorte é **calculada**,
não vem do campo do HubSpot; a fórmula dos 25% virou CMV 30%); afinar o cartão de recompra para
**90d + 180d** (a 2ª compra tem mediana de 123 dias); e os 137 SKUs sem custo para o time de Dados.
