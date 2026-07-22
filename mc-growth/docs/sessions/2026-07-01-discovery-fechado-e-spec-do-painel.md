# Sessão 2026-07-01 — discovery-fechado-e-spec-do-painel

> Log da sessão. Não é resumo de commit — é o "porquê" e o "o que vem depois".

---

## Objetivo da sessão

Retomar o MC Growth, fechar o discovery (áreas 4, 5, 7, 8) e deixar o Painel de MC v1 pronto para ser construído.

---

## O que foi feito

- Cobertas as **áreas 4–8** da entrevista de produto (entidades, fluxos, escopo, restrições) — discovery **completo**.
- Gerado o **`PRODUCT.md`** (visão, glossário, entidades, fluxos, KPIs, escopo, restrições).
- Criado o **`ARCHITECTURE.md`** (mapa das 5 abas, cálculo, pontos frágeis) e depois atualizado com a **conexão real da planilha** (`ARCHITECTURE.md` seção 3.0).
- Escrito o **spec de construção** do painel (`docs/specs/2026-07-01-painel-mc-v1.md`) com regras R1–R12 e critérios CA1–CA8.
- Registrado o **ADR do stack** (`docs/decisions/2026-07-01-stack-streamlit-planilha-unica.md`).
- Atualizado `CLAUDE.md` (seção 0 = fase Construção; seção 8 = stack preenchido).
- **Verificada a planilha real** compartilhada pelo João: acesso público OK, 4 abas de dados mapeadas por gid, formatos conferidos.

---

## Decisões tomadas

### Fonte de dados única + stack Streamlit
- **Decisão:** o painel lê **uma planilha Google única** (ao vivo, via CSV) e é feito em **Python + Streamlit + pandas**, rodando local, só para o João.
- **Por quê:** derruba o atrito de integrar 3 fontes; entrega valor "hoje"; João é de dados.
- **Descartado:** fórmulas dentro da planilha (A) e app React/Next (B) — ver ADR.
- **ADR criado?** Sim — `docs/decisions/2026-07-01-stack-streamlit-planilha-unica.md`.

### Modelo de dados da cascata (fechado no discovery)
- **Vendas** = Σ `net_revenue` (Base 1, pedidos `PAID`); **sem** linhas próprias de frete/devolução no v1.
- **CMV** = Σ (custo do SKU × quantidade) usando a base de **itens explodidos** (`item_desmembrado_codigo`), **incluindo brindes** (custam mesmo sem receita).
- **Mídia** = `fb_investimento + google_investimento + google_institucional_investimento`.
- **Parâmetros** (%) valem "pra frente" (v2 datado); no v1 ficam no modo simples.

### Parâmetros embutidos no código (não há aba)
- **Decisão:** como a planilha não tem aba `Parametros`, os 10 percentuais ficam numa constante em `cascata.py`.
- **Por quê:** manter o ritmo; valores conhecidos e estáveis.
- **ADR criado?** Não (registrado aqui e em `ARCHITECTURE.md` 3.0). Quando o João criar a aba, trocar a fonte.

---

## Problemas encontrados

### Nomes de aba/coluna diferentes do contrato + formato decimal misto
- **Descrição:** a planilha veio com nomes de coluna originais (`processed_at_data`, `id`, `item_desmembrado_codigo`…), sem aba `Parametros`, e a aba `Custos` mistura ponto e vírgula como separador decimal.
- **Causa raiz:** o João consolidou as bases cruas via IMPORTRANGE, sem renomear.
- **Solução aplicada:** documentado em `ARCHITECTURE.md` 3.0 o mapa gid→aba, o de-para de colunas e a regra do leitor robusto. O código vai **adaptar ao que existe** (não pedir para o João renomear).
- **Status:** resolvido (documentado; falta implementar o leitor).

---

## Estado do projeto agora

### Funcionando
- Documentação viva completa: `PRODUCT.md`, `ARCHITECTURE.md`, spec e ADR.
- Planilha acessível publicamente; gids e formatos mapeados e testados via CSV.
- Ambiente: Python 3.13 + pandas 3.0 prontos.

### Quebrado / incompleto
- **Ainda não há código** (`dados.py`, `cascata.py`, `painel.py` a criar).
- `streamlit` ainda não instalado.
- Aba `Parametros` inexistente (contornado no código).

---

## Próximo passo

1. **Construir** (nova sessão): `dados.py` (leitura/limpeza das 4 abas) → `cascata.py` (regras R1–R12 + constante `PARAMETROS`) → `painel.py` (herói MC, 5 cartões, DRE, filtro, alerta).
2. Instalar `streamlit` e rodar `streamlit run painel.py`.
3. **Conferir** os critérios CA1–CA8 do spec, com atenção ao CA3 (a DRE tem que fechar) e à ressalva de Vendas×CMV virem de bases diferentes (amarração).

---

## Atualizações em outros documentos

- **`ARCHITECTURE.md`:** criado; + seção **3.0** com SHEET_ID, mapa de gids, de-para de colunas, formato decimal e ausência da aba `Parametros`.
- **`CLAUDE.md`:** seção 0 (fase Construção, próximo passo = construir, ambiente) e seção 8 (stack preenchido).
- **`docs/decisions/`:** criado `2026-07-01-stack-streamlit-planilha-unica.md`.
- **`docs/specs/`:** criado `2026-07-01-painel-mc-v1.md`.
- **`PRODUCT.md`:** criado (áreas 1–8).
