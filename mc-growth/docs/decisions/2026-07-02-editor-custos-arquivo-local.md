# ADR — Correções de custo num arquivo local (o painel escreve fora da base)

**Data:** 2026-07-02
**Status:** Aceito
**Tema:** editor-custos-arquivo-local

---

## 1. Contexto

A arquitetura da v1 assumia que o João mantinha a aba `Custos` da planilha (e, no
futuro, a `Parametros`). Ao rodar, o João informou que **não consegue editar a base**
(a planilha compartilhada). Sem isso, os SKUs vendidos sem custo (ex.: Perfume 10ML =
R$11,83) ficariam para sempre no alerta e o CMV sairia subestimado.

Era preciso um jeito de o João corrigir custos **sem tocar na base**. Entre três opções
(manter no código; um arquivo local que ele edita; um editor no próprio painel), o João
escolheu o **editor no painel**.

---

## 2. Decisão

O painel ganha uma seção "🏷️ Corrigir custos faltantes" onde o João digita o custo dos
SKUs sem custo e salva. As correções são gravadas num **arquivo local** na pasta do
projeto (`custos_extra.csv`), e o carregador as aplica **por cima da base** ao ler os
custos. O painel **continua sem escrever na planilha compartilhada** — a única escrita é
nesse arquivo local, que é do João.

---

## 3. Motivação

- Desbloqueia a correção de custos sem depender de acesso à base nem de mim (self-service).
- Preserva o invariante que importa: **a fonte de verdade compartilhada (planilha) nunca é
  alterada pelo painel**. A escrita é local e isolada.
- Alinha com a visão futura do PRODUCT.md (seção 8): "configuração de parâmetros na própria tela".
- Reversível: apagar `custos_extra.csv` volta ao estado só-base.

---

## 4. Alternativas consideradas

### Alternativa A: manter as correções no código
- **Contras:** toda correção depende de mim; não é self-service.
- **Descartada:** o João quer autonomia.

### Alternativa B: um arquivo local que o João edita à mão
- **Contras:** editar CSV cru é menos amigável e sujeito a erro de formato.
- **Descartada:** o editor na tela é mais seguro (campo numérico validado).

---

## 5. Consequências

### Positivas
- João corrige custos sozinho; o SKU sai do alerta e entra no CMV na hora.
- Persiste entre sessões (é arquivo).

### Negativas
- Surge **estado local** fora da planilha: quem rodar o painel noutra máquina não terá as
  correções (ficam no Mac do João). Aceito na v1 (um usuário, uma máquina).
- O total do painel pode divergir da base pura por causa das correções — intencional.

### O que essa decisão FECHA
> - O invariante "o painel só lê, nunca escreve" passa a valer só para a **planilha
>   compartilhada**, não para o arquivo local. Registrar isso onde o invariante aparece.
> - Quando houver multiusuário (v2+), este arquivo local precisará virar armazenamento
>   compartilhado (ou a aba `Parametros`/`Custos` editável de novo).

---

## 6. Implementação

- **Onde se materializa:** `dados.py` (`CAMINHO_CUSTOS_EXTRA`, `ler_custos_extra`,
  `salvar_custos_extra`, `_aplicar_custos_extra`, aplicado em `carregar_custos`);
  `cascata.py` expõe `Resultado.skus_faltantes`; `painel.py` desenha o editor
  (`st.data_editor` + botão Salvar). `.gitignore` ignora `custos_extra.csv`.
- **Spec:** `docs/specs/2026-07-02-editor-custos-faltantes.md`.
- **Migration/refactor:** não.

---

## 7. Revisão

- **Quando reavaliar:** ao entrar multiusuário/segunda máquina, ou se a base voltar a ser
  editável pelo João.
- **Sob que condições reverter:** apagar `custos_extra.csv` e remover a seção do painel.
