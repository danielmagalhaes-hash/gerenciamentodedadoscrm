# Prompt — Handoff de versão: gerar o PRODUCT.md da próxima versão

> Use **ao fechar uma versão do roadmap** (V2, V3, V4…). Ele pega o **entregável final da
> versão que acabou** + a definição da **próxima versão no `docs/ROADMAP.md`** e gera o
> `PRODUCT.md` da próxima — reaproveitando a estrutura de [`01-gerar-product-md.md`](01-gerar-product-md.md),
> sem entrevista de discovery do zero.
>
> É a ponte entre uma versão e a seguinte: em vez de perguntar tudo de novo, parte do que
> **já foi construído** (a realidade nova) e do que o roadmap **já definiu** como próximo passo.

> **Estilo de explicação obrigatório:** seguir [`../principios/comunicacao-com-usuario.md`](../principios/comunicacao-com-usuario.md) — analogia primeiro, termo técnico depois, sem encadear jargão.

---

## Pré-requisitos

- [ ] A versão anterior está **fechada** (spec cumprida, critério de aceite batido, log de sessão criado, `ARCHITECTURE.md` atualizado).
- [ ] O `docs/ROADMAP.md` existe e descreve a próxima versão (o que ela adiciona, a decisão que destrava, critério de aceite, pré-requisito de dado).
- [ ] Você confirmou ao João qual versão acabou (N) e qual é a próxima (N+1).

---

## Prompt

```
Vamos fazer o handoff da versão que acabou para a próxima. NÃO é uma discovery
do zero: parta do que já foi construído e do que o roadmap já definiu.

PASSO 1 — Carregar contexto (leia, nesta ordem):
- CLAUDE.md (Seção 0 — estado/próximo passo) e docs/ROADMAP.md.
- PRODUCT.md atual (descreve a versão vigente — é a base a evoluir).
- ARCHITECTURE.md (o que existe de fato hoje: módulos, entidades, dados).
- O ENTREGÁVEL FINAL DA VERSÃO QUE ACABOU (N):
  - a spec dela em docs/specs/,
  - o log de sessão que a fechou em docs/sessions/,
  - qualquer ADR criado em docs/decisions/.

PASSO 2 — Confirmar comigo, em 3 linhas:
- Qual versão acabou (N) e qual é a próxima (N+1).
- Em 1 frase, o que a N entregou de novo na realidade (o que hoje é
  verdade que não era antes: nova entidade, nova coluna, nova regra,
  nova fonte de dado).
- Em 1 frase, o que a N+1 adiciona e a decisão que ela destrava
  (copie do ROADMAP.md).
PARE aqui e espere meu "ok" antes de gerar.

PASSO 3 — Gerar o PRODUCT.md da versão N+1.
Use EXATAMENTE a estrutura e as REGRAS DE GERAÇÃO do prompt
01-gerar-product-md.md (as 8 seções, o formato de glossário e de KPI,
"não invente — pergunte", "sem TBD", termos consistentes). Só que:

- Onde o 01 fala de "v1", leia "a versão N+1". A Seção 7.1 ("Entra")
  descreve o escopo da N+1; a 7.2 ("Fica para depois") lista as versões
  seguintes do roadmap (N+2 em diante).
- NÃO comece do zero: o PRODUCT.md da N+1 é o da versão vigente
  EVOLUÍDO. O que a versão N tornou realidade sai da 7.2 e entra como
  comportamento existente. Marque em cada seção o que é HERDADO (já
  existe) e o que é NOVO nesta versão.
- Glossário: acrescente os termos novos que a N+1 introduz (ex.: na V2,
  "cliente", "primeira compra vs. recompra"; na V4, "coorte", "lucro por
  cliente novo"). Não apague os termos herdados.
- KPIs e regras de cálculo: toda regra nova precisa rastrear a fonte
  (coluna/aba/base). Se a N+1 depende de um dado que ainda não está na
  planilha/base, NÃO invente a fórmula — marque o KPI como
  "depende de dado a confirmar" e me pergunte de onde vem.
- Mantenha a disciplina do projeto: nunca produzir número/regra sem
  rastrear a origem; custo assumido é marcado como "% provisório".

PASSO 4 — Preservar o histórico (não perder a versão anterior):
- Antes de sobrescrever, copie o PRODUCT.md atual para
  docs/product-history/PRODUCT-v{N}.md (crie a pasta se não existir).
- Então salve o novo como PRODUCT.md na raiz.

PASSO 5 — Fechar o ritual (obrigatório):
- Atualize a Seção 0 do CLAUDE.md (estado = "V{N+1} em spec/construção";
  próximo passo).
- Registre no log de sessão que o PRODUCT.md avançou para a N+1.
- Se a transição tomou uma decisão duradoura, crie um ADR (use o
  prompt 12-criar-adr.md).

REGRAS:
- Se faltar informação para qualquer seção, PARE e me pergunte — não
  invente e não use "TBD".
- Não invente escopo além do que o ROADMAP.md define para a N+1. Se
  achar que o roadmap precisa mudar, me avise antes — não mude por conta.
- Explique no meu vocabulário: analogia primeiro, termo técnico depois.
```

---

## Validação após geração

Além do checklist do `01-gerar-product-md.md`, confirme:

- [ ] O `PRODUCT.md` da N+1 **descreve a próxima versão**, não a que acabou.
- [ ] O que a versão N entregou saiu de "Fica para depois" (7.2) e virou comportamento existente.
- [ ] Nenhum KPI novo tem fórmula sem fonte rastreada (ou está marcado como "depende de dado a confirmar").
- [ ] O `PRODUCT.md` da versão anterior foi arquivado em `docs/product-history/PRODUCT-v{N}.md`.
- [ ] O escopo não passou do que o `ROADMAP.md` define para a N+1.
- [ ] `CLAUDE.md` (Seção 0) e o log de sessão refletem a transição.

Se algo falhar, peça correção pontual. Não regenere o documento inteiro.
