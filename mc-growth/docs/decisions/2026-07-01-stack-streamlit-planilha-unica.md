# ADR — Stack do v1: Streamlit lendo uma planilha única

**Data:** 2026-07-01
**Status:** Aceito
**Tema:** stack-streamlit-planilha-unica

---

## 1. Contexto

O MC Growth chegou ao fim do discovery com o modelo de dados e a cascata de Margem de Contribuição totalmente especificados (ver `PRODUCT.md`). Faltava decidir **com o que construir** (a Fase 1 do trilho) e **como o painel recebe os dados**.

Os dados moram em três lugares diferentes, cada um com sua forma de acesso: a Shopify (pedidos e itens), a tabela de custo (planilha) e o BigQuery (mídia paga). Plugar o painel diretamente nas três fontes significaria lidar com três autenticações e três formatos distintos — muito atrito para um prazo declarado de "pronto hoje" (2026-07-01).

O João decidiu, durante a sessão, **consolidar tudo numa planilha Google única** (via IMPORTRANGE e exports do BigQuery) e optou por um **mini-app separado** (caminho B), em vez de montar a cascata como fórmulas dentro da própria planilha (caminho A).

O v1 é **só para o João**, roda no computador dele, e não precisa de login nem de múltiplos usuários.

---

## 2. Decisão

Vamos construir o v1 em **Python + Streamlit**, usando a biblioteca *pandas* para os cálculos, rodando **localmente** no Mac do João. O painel lê **uma planilha Google única de 5 abas** (`Vendas`, `Itens`, `Custos`, `Midia`, `Parametros`) **ao vivo**, via a URL de export CSV de cada aba (planilha compartilhada como "qualquer um com o link pode ver") — **sem chaves de API nem credenciais**.

---

## 3. Motivação

- **Menor atrito para o prazo:** Streamlit transforma um script de dados em painel de navegador sem construir um site do zero; entrega herói + cartões + tabela + filtro com pouca linha de código.
- **Uma porta de entrada de dados:** a planilha única faz o painel precisar "falar" só um idioma (ler CSV), em vez de três. Derruba o risco de integração.
- **Fiel ao usuário:** o João é de dados; Python + pandas é o terreno natural. E ele mesmo mantém a planilha.
- **Respeita o escopo do v1:** sem login, sem servidor, sem nuvem — coerente com "v1 é só para mim".
- **Evolutivo:** a separação em módulos (`dados.py` / `cascata.py` / `painel.py`) permite, depois, trocar a planilha por conexão automática sem reescrever a regra de cálculo.

---

## 4. Alternativas consideradas

### Alternativa A: Painel como fórmulas dentro da própria planilha
- **Descrição:** uma aba "Painel" com fórmulas/QUERY montando a cascata.
- **Prós:** zero instalação; funciona hoje; João mexe sozinho.
- **Contras:** visual limitado; lógica espalhada em células difícil de versionar/testar; distante do mockup.
- **Por que foi descartada:** o João preferiu o caminho B (app separado), com visual mais próximo do mockup e lógica versionável.

### Alternativa B: App web em React/Next.js
- **Descrição:** front-end web "de verdade".
- **Prós:** visual mais próximo do mockup; escalável para multiusuário.
- **Contras:** muito mais trabalho; exige Node, build, hospedagem; não fica pronto hoje.
- **Por que foi descartada:** desproporcional para um v1 de um usuário só, com prazo curto.

---

## 5. Consequências

### Positivas
- Caminho mais curto até a "MC correta na tela".
- Cálculo isolado e testável (não preso a células de planilha).
- Fácil de iterar visualmente.

### Negativas
- Depende de o João manter a planilha no formato-contrato (nomes de coluna fixos).
- Streamlit tem teto de sofisticação visual; se um dia quiser algo muito custom, migra.
- Roda local: para outra pessoa ver, hoje seria "olhar a tela do João".

### O que essa decisão FECHA
> - **Multiusuário/login** não sai de graça daqui — quando o CEO/lideranças precisarem de acesso próprio, provavelmente será outra camada (hospedar o Streamlit ou migrar).
> - Enquanto a fonte for a planilha, o painel **não é tempo real** — depende de o João atualizar as abas.

---

## 6. Implementação

- **Onde se materializa no código:** `painel.py` (UI), `cascata.py` (regras), `dados.py` (leitura da planilha).
- **Migration/refactor necessário:** não (projeto novo).
- **Regra a adicionar no CLAUDE.md:** preencher a seção 8 (Stack) — Python + Streamlit + pandas; convenções técnicas do template quando o código crescer.
- **Atualização no ARCHITECTURE.md (seção 5):** feita.

---

## 7. Revisão

- **Quando reavaliar:** quando o CEO/lideranças precisarem de acesso próprio, ou quando a planilha virar gargalo (volume/latência), ou ao ligar as fontes automaticamente.
- **Sob que condições reverter:** se o Streamlit não der conta do visual desejado, ou se manter a planilha manualmente se mostrar frágil demais.
