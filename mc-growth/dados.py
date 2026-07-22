"""
dados.py — carregador da planilha única (só leitura).

Responsabilidade: ler cada aba da planilha Google ao vivo (via URL de export CSV)
e devolver tabelas limpas (colunas renomeadas, datas e números normalizados),
prontas para o cascata.py calcular a Margem de Contribuição.

Este módulo NÃO calcula regra de negócio e NÃO escreve em lugar nenhum.
Não depende de Streamlit (o painel.py é quem cuida de cache e tela).

Contrato da planilha: ARCHITECTURE.md seção 3.
"""

from __future__ import annotations

import io
import os
import ssl
import time
import urllib.request
from dataclasses import dataclass

import certifi
import numpy as np
import pandas as pd

# Contexto SSL com a lista de autoridades do certifi. Sem isto, o Python do
# macOS (Python.org) não valida o certificado do Google e a leitura falha.
_CONTEXTO_SSL = ssl.create_default_context(cafile=certifi.where())

# ---------------------------------------------------------------------------
# Conexão (verificada em 2026-07-01 — ARCHITECTURE.md 3.0)
# ---------------------------------------------------------------------------
SHEET_ID = "1-z6gebmW_tBmJSGVS06vfjsHgLEStbFbRbEwJFXL9KM"

# Papel da aba -> gid (a posição da aba dentro da planilha)
GIDS = {
    "Vendas": "0",
    "Itens": "1246117066",
    # Custo NÃO fica aqui: são 3 abas em cascata (ver FONTES_CUSTO logo abaixo).
    "Midia": "1308114343",
}

# Cascata de custo por SKU, da fonte mais forte para a rede de segurança (spec 2026-07-22).
# Para cada SKU, o custo é o 1º desta lista que vier com valor > 0 (0/vazio = FALTANDO).
# As correções locais (custos_extra.csv) vêm por cima de TODAS. Simétrica com as 3 camadas
# de itens em `cascata.itens_por_nome`.
#   (gid, nome amigável, coluna de custo na aba)
FONTES_CUSTO: tuple[tuple[str, str, str], ...] = (
    ("634911340", "3.2. Custos", "PREÇO JUNHO"),  # principal desde 2026-07-22 (Financeiro)
    ("1460088128", "3.1. Custos", "Custo"),         # rede de segurança 1 (era a principal)
    ("423190064", "3. Custos", "Valor de Custo"),   # rede de segurança 2 (a mais antiga)
)

# Base silver crua — usada SÓ como dicionário SKU -> nome do produto (auditoria).
# Não é fonte de cálculo (mistura outros canais); ver ARCHITECTURE.md 3.0.
GID_DESCRICOES = "1466784982"

# Aba "2.1. Itens" — NF-e de venda (Bling). FONTE DOS ITENS desde 2026-07-04:
# casa com a Vendas por `numeroPedidoLoja` = final do `order_id`. Substitui a base
# de itens Shopify (decisão do João). Ver ARCHITECTURE.md 3.0.
GID_ITENS_NF = "488044140"

# Naturezas de NF que CONTAM como itens do pedido (venda + brinde; brinde tem custo).
_NF_NATUREZAS_CONTAM = ("Venda de mercadorias", "Remessa em bonificação, doação ou brinde")
# Situações que NÃO valem (nota sem efeito).
_NF_STATUS_INVALIDO = ("Cancelada", "Rejeitada", "Pendente")


class ErroDeDados(Exception):
    """Erro de leitura/limpeza com mensagem já pronta para mostrar ao João."""


@dataclass
class Dados:
    """As quatro abas já limpas, prontas para o cálculo."""

    vendas: pd.DataFrame  # order_id, order_name, data, net_revenue, customer_type
    itens: pd.DataFrame   # order_id, data, sku, quantidade
    custos: pd.DataFrame  # sku, valor_custo
    midia: pd.DataFrame   # data, fb_investimento, google_investimento, google_institucional_investimento


# ---------------------------------------------------------------------------
# Leitura crua
# ---------------------------------------------------------------------------
def _url_export(gid: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"


def _ler_csv(gid: str, nome_aba: str, tentativas: int = 3) -> pd.DataFrame:
    """
    Baixa a aba (pelo gid) como CSV, com blindagem contra soluços do Google.

    Às vezes o Google, em vez da planilha, devolve uma página de erro (HTML) — um
    engasgo passageiro. Aqui a gente: (1) confere se o que chegou é mesmo CSV, e
    (2) tenta de novo algumas vezes com espera crescente antes de desistir. Só então
    mostra uma mensagem clara — nunca o erro confuso de "coluna faltando".

    [2026-07-14] Há um segundo engasgo, mais traiçoeiro: o Google responde HTTP 200 com
    `text/csv` de verdade, mas a **planilha vem VAZIA** (só vírgulas, sem cabeçalho — ~840 KB
    de linhas em branco no lugar dos 3,5 MB). O pandas lê sem reclamar e nomeia as colunas de
    `Unnamed: 0`, `Unnamed: 1`… O sintoma na tela era o erro confuso "a aba Vendas está sem a
    coluna order_id". Agora isso também vira motivo de nova tentativa (observado 3× num dia).
    """
    url = _url_export(gid)
    ultimo_erro: Exception | None = None

    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(url, context=_CONTEXTO_SSL, timeout=30) as resposta:
                tipo = resposta.headers.get_content_type()  # 'text/csv' se veio a planilha
                bruto = resposta.read()
            if tipo != "text/csv":
                # veio HTML (página de erro/login), não a tabela
                raise ValueError(f"resposta não é CSV (veio '{tipo}')")
            # dtype=str: não deixa o pandas adivinhar decimais errados.
            # keep_default_na=False: célula vazia vira "" (texto), não NaN — mais previsível.
            tabela = pd.read_csv(io.BytesIO(bruto), dtype=str, keep_default_na=False)
            # Planilha vazia (sem cabeçalho): TODA coluna vem como "Unnamed: N". Não é dado —
            # é o engasgo descrito acima. Tenta de novo em vez de entregar lixo.
            if tabela.empty or all(str(c).startswith("Unnamed:") for c in tabela.columns):
                raise ValueError("a planilha voltou vazia (sem cabeçalho) — engasgo do Google")
            return tabela
        except Exception as erro:  # rede fora do ar, HTTP 4xx/5xx, resposta não-CSV, aba vazia
            ultimo_erro = erro
            if tentativa < tentativas:
                time.sleep(1.5 * tentativa)  # 1.5s, depois 3s — dá tempo do engasgo passar

    raise ErroDeDados(
        f"Não consegui ler a aba `{nome_aba}` agora (o Google pode estar instável ou o "
        "compartilhamento/link pode ter mudado). Aguarde alguns segundos e clique em "
        "Atualizar; se persistir, confira o compartilhamento da planilha."
    ) from ultimo_erro


def _exigir_colunas(df: pd.DataFrame, nome_aba: str, colunas: list[str]) -> None:
    """Garante que a aba trouxe as colunas esperadas; senão, erro claro (spec 2.3)."""
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise ErroDeDados(f"A aba `{nome_aba}` está sem a coluna `{faltando[0]}`.")


# ---------------------------------------------------------------------------
# Normalização de tipos
# ---------------------------------------------------------------------------
def _para_numero(serie: pd.Series) -> pd.Series:
    """
    Converte texto em número aguentando o decimal misto da planilha:
      - tem "." E ","  -> "." é milhar, "," é decimal   (ex: "1.594,41" -> 1594.41)
      - só ","         -> "," é decimal                 (ex: "459,15"   -> 459.15)
      - só "." ou nada -> já está no formato certo       (ex: "34.5", "273" -> 34.5, 273)
    Célula vazia ou lixo vira NaN (não quebra a conta).
    """
    texto = serie.astype("string").str.strip()

    tem_ponto = texto.str.contains(".", regex=False)
    tem_virgula = texto.str.contains(",", regex=False)
    ambos = (tem_ponto & tem_virgula).fillna(False)
    so_virgula = (tem_virgula & ~tem_ponto).fillna(False)

    versao_ambos = texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    versao_virgula = texto.str.replace(",", ".", regex=False)

    limpo = np.select(
        [ambos.to_numpy(), so_virgula.to_numpy()],
        [versao_ambos.to_numpy(), versao_virgula.to_numpy()],
        default=texto.to_numpy(),
    )
    return pd.to_numeric(pd.Series(limpo, index=serie.index), errors="coerce")


def _para_data(serie: pd.Series, com_hora: bool = False) -> pd.Series:
    """Converte 'DD/MM/AAAA' (ou 'DD/MM/AAAA HH:MM:SS') em data. Formato inválido -> NaT."""
    texto = serie.astype("string").str.strip()
    if com_hora:
        texto = texto.str.split(" ").str[0]  # descarta a hora, fica só a data
    return pd.to_datetime(texto, format="%d/%m/%Y", errors="coerce")


def _para_data_iso(serie: pd.Series) -> pd.Series:
    """Converte 'AAAA-MM-DD' (formato do HubSpot/BigQuery) em data. Inválido -> NaT."""
    texto = serie.astype("string").str.strip().str.split(" ").str[0]  # tira hora, se houver
    return pd.to_datetime(texto, format="%Y-%m-%d", errors="coerce")


# ---------------------------------------------------------------------------
# Carregadores por aba
# ---------------------------------------------------------------------------
def carregar_vendas() -> pd.DataFrame:
    """
    Aba Vendas (1 linha por pedido, só PAID)
    -> order_id, order_name, data, net_revenue, customer_type.

    `customer_type` é o carimbo nativo da Shopify (novo × recompra), exigido a partir
    da V2 (aba de aquisição — spec 2026-07-09). Valores esperados: "Primeira Compra",
    "Recompra" ou vazio. Só normalizamos o espaçamento; a grafia é mantida como veio da
    fonte (o cálculo dos novos casa com a string exata "Primeira Compra").
    """
    df = _ler_csv(GIDS["Vendas"], "Vendas")
    _exigir_colunas(
        df, "Vendas",
        ["order_id", "order_name", "processed_at_data", "net_revenue", "customer_type"],
    )
    return pd.DataFrame(
        {
            "order_id": df["order_id"].astype("string").str.strip(),
            # order_name vem inconsistente da fonte (uns com "#", outros sem) — normaliza sem "#".
            "order_name": df["order_name"].astype("string").str.strip().str.lstrip("#"),
            "data": _para_data(df["processed_at_data"]),
            "net_revenue": _para_numero(df["net_revenue"]),
            "customer_type": df["customer_type"].astype("string").str.strip(),
        }
    )


def carregar_itens() -> pd.DataFrame:
    """Aba Itens (1 linha por item explodido) -> order_id, data, sku, quantidade."""
    # Fonte de itens: base de VENDAS Shopify (mais confiável que a NF de saída — decisão
    # do João, 2026-07-04). Tem a dobra de kit (a montante), que o time de dados vai
    # corrigir — ver docs/orientacao-base-itens-confiavel.md.
    df = _ler_csv(GIDS["Itens"], "Itens")
    _exigir_colunas(df, "Itens", ["id", "data_order", "item_desmembrado_codigo", "quantidade_final"])
    # item_desmembrado_nome é opcional (nome do produto — usado na auditoria).
    if "item_desmembrado_nome" in df.columns:
        descricao = df["item_desmembrado_nome"].astype("string").str.strip()
    else:
        descricao = pd.Series("", index=df.index, dtype="string")
    return pd.DataFrame(
        {
            "order_id": df["id"].astype("string").str.strip(),
            "data": _para_data(df["data_order"], com_hora=True),
            "sku": df["item_desmembrado_codigo"].astype("string").str.strip(),
            "quantidade": _para_numero(df["quantidade_final"]),
            "descricao": descricao,
        }
    )


def _ler_aba_custo(gid: str, nome_aba: str, coluna_valor: str) -> pd.DataFrame:
    """Lê uma aba de custo (1 linha por SKU) -> sku, valor_custo. SKU repetido: fica o 1º."""
    df = _ler_csv(gid, nome_aba)
    _exigir_colunas(df, nome_aba, ["SKU", coluna_valor])
    custos = pd.DataFrame(
        {
            "sku": df["SKU"].astype("string").str.strip(),
            "valor_custo": _para_numero(df[coluna_valor]),
        }
    )
    custos = custos[custos["sku"] != ""]
    return custos.drop_duplicates(subset="sku", keep="first")


def carregar_custos() -> pd.DataFrame:
    """
    Custo por SKU numa CASCATA de fontes (spec 2026-07-22):
      1. Aba 3.2 (`PREÇO JUNHO`) é a fonte principal — a mais atualizada (Financeiro).
      2. Onde a 3.2 vem 0/vazia, cai para a 3.1 (`Custo`); onde a 3.1 também falta,
         cai para a 3 (`Valor de Custo`). Custo zero é FALTANDO, não grátis.
      3. As correções locais do João (custos_extra.csv) vêm POR CIMA de tudo.
    A ordem está em `FONTES_CUSTO` (da mais forte para a rede de segurança).
    """
    custos: pd.DataFrame | None = None  # o que já foi resolvido (sku, valor_custo)
    for gid, nome, coluna in FONTES_CUSTO:
        fonte = _ler_aba_custo(gid, nome, coluna)
        if custos is None:
            custos = fonte
            continue
        # Só usa a fonte mais fraca onde a acumulada ainda falta (NaN ou ≤ 0).
        juntas = custos.merge(fonte, on="sku", how="outer", suffixes=("_ok", "_novo"))
        atual = juntas["valor_custo_ok"]
        falta = atual.isna() | (atual <= 0)
        custos = pd.DataFrame(
            {
                "sku": juntas["sku"],
                "valor_custo": atual.where(~falta, juntas["valor_custo_novo"]),
            }
        )

    assert custos is not None  # FONTES_CUSTO nunca é vazia
    return _aplicar_custos_extra(custos)


# ---------------------------------------------------------------------------
# Correções locais de custo (custos_extra.csv) — o João não edita a base.
# O painel escreve AQUI (arquivo local), nunca na planilha compartilhada.
# ADR 2026-07-02-editor-custos-arquivo-local.
# ---------------------------------------------------------------------------
CAMINHO_CUSTOS_EXTRA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "custos_extra.csv"
)


def ler_custos_extra() -> dict[str, float]:
    """Correções locais salvas pelo João no painel. Vazio se o arquivo não existe."""
    if not os.path.exists(CAMINHO_CUSTOS_EXTRA):
        return {}
    df = pd.read_csv(CAMINHO_CUSTOS_EXTRA, dtype=str, keep_default_na=False)
    if "sku" not in df.columns or "valor_custo" not in df.columns:
        return {}
    skus = df["sku"].astype("string").str.strip()
    valores = _para_numero(df["valor_custo"])
    return {s: float(v) for s, v in zip(skus, valores) if s and pd.notna(v)}


def salvar_custos_extra(correcoes: dict[str, float]) -> None:
    """Grava (sobrescreve) o arquivo local de correções. Chave sku -> custo."""
    df = pd.DataFrame(
        [{"sku": sku, "valor_custo": valor} for sku, valor in correcoes.items()]
    )
    df.to_csv(CAMINHO_CUSTOS_EXTRA, index=False)


def _aplicar_custos_extra(custos: pd.DataFrame) -> pd.DataFrame:
    """Correção local vence a base: substitui o SKU existente ou adiciona um novo."""
    extra = ler_custos_extra()
    if not extra:
        return custos
    base = custos[~custos["sku"].isin(extra.keys())]
    novos = pd.DataFrame(
        {"sku": list(extra.keys()), "valor_custo": list(extra.values())}
    )
    return pd.concat([base, novos], ignore_index=True)


def carregar_midia() -> pd.DataFrame:
    """
    Aba Midia (1 linha por dia) -> data + as 3 colunas de investimento + investimento_total.

    A aba foi estendida (2026-07-10) para cobrir 2021-03→hoje e ganhou a coluna
    `investimento_total` (soma crua FB+Google+institucional, SEM imposto). O painel/V2
    seguem usando as 3 colunas (com o gross-up do FB); a V4 (coortes) usa
    `investimento_total` para a Ad Spend histórica com imposto condicional (só 2026+).
    A coluna é OPCIONAL aqui: se a aba antiga (sem ela) for lida, vem como NaN e só a V4
    sente falta — V1/V2 não dependem dela.
    """
    df = _ler_csv(GIDS["Midia"], "Midia")
    cols = ["data", "fb_investimento", "google_investimento", "google_institucional_investimento"]
    _exigir_colunas(df, "Midia", cols)
    if "investimento_total" in df.columns:
        investimento_total = _para_numero(df["investimento_total"])
    else:
        investimento_total = pd.Series(np.nan, index=df.index, dtype="float64")
    return pd.DataFrame(
        {
            "data": _para_data(df["data"]),
            "fb_investimento": _para_numero(df["fb_investimento"]),
            "google_investimento": _para_numero(df["google_investimento"]),
            "google_institucional_investimento": _para_numero(df["google_institucional_investimento"]),
            "investimento_total": investimento_total,
        }
    )


def carregar_tudo() -> Dados:
    """Lê e limpa as quatro abas de uma vez."""
    return Dados(
        vendas=carregar_vendas(),
        itens=carregar_itens(),
        custos=carregar_custos(),
        midia=carregar_midia(),
    )


# ---------------------------------------------------------------------------
# Base HubSpot (V4 — coortes de recompra). Nova FONTE, mas arquivo LOCAL:
# o João roda 1×/mês uma query no BigQuery que despeja a base em bases/hubspot_deals.csv
# (ADR 2026-07-10-v4-arquitetura-mvp-coortes: BigQuery como torneira, sem credencial no
# painel). O painel só LÊ o arquivo local — como já faz com custos_extra.csv.
# Só a aba de coortes depende dele; V1/V2 NÃO leem esta base.
# ---------------------------------------------------------------------------
CAMINHO_HUBSPOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "bases", "hubspot_deals.csv"
)

# Colunas mínimas do export (spec §3.3). Ausência de qualquer uma = erro claro.
_HUBSPOT_COLUNAS = [
    "e_mail", "nome", "valor", "data_de_fechamento", "tipo_de_venda",
    "etapa_do_negocio", "data_primeira_compra", "meses_desde_primeira_compra",
]


def carregar_hubspot(caminho: str = CAMINHO_HUBSPOT) -> pd.DataFrame:
    """
    Lê o `bases/hubspot_deals.csv` local (deals `Shipped` + `Negócio Fechado - Comercial`)
    e devolve os deals já limpos, prontos para o módulo de coortes.

    Colunas devolvidas: e_mail, nome, valor, data_de_fechamento, tipo_de_venda,
    etapa_do_negocio, data_primeira_compra, meses_desde_primeira_compra, safra (AAAA-MM).

    Normalizações (spec §3.3):
      - `e_mail`  -> minúsculo, sem espaço (chave de cliente).
      - `nome`    -> sem o `#` inicial (`lstrip("#")`), para casar com `Vendas.order_name`.
      - `valor`   -> número (ponto decimal no export do BQ).
      - datas     -> `AAAA-MM-DD` (formato ISO do HubSpot), não o DD/MM/AAAA da planilha.
      - `meses…`  -> inteiro (idade da safra).
    Descarta linhas sem `e_mail` ou sem `data_primeira_compra` (não têm safra nem cliente).
    Arquivo ausente ou coluna faltando -> `ErroDeDados` com mensagem pronta pro João.
    """
    if not os.path.exists(caminho):
        raise ErroDeDados(
            "Arquivo de coortes não encontrado (`bases/hubspot_deals.csv`). Rode a "
            "atualização mensal do HubSpot (a query do BigQuery da spec) e salve o CSV em "
            "`bases/`."
        )
    bruto = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    _exigir_colunas(bruto, "hubspot_deals.csv", _HUBSPOT_COLUNAS)

    df = pd.DataFrame(
        {
            "e_mail": bruto["e_mail"].astype("string").str.strip().str.lower(),
            # tira o `#` inicial (91% dos nomes vêm com cerquilha) para casar com a Vendas.
            "nome": bruto["nome"].astype("string").str.strip().str.lstrip("#"),
            "valor": _para_numero(bruto["valor"]),
            "data_de_fechamento": _para_data_iso(bruto["data_de_fechamento"]),
            "tipo_de_venda": bruto["tipo_de_venda"].astype("string").str.strip(),
            "etapa_do_negocio": bruto["etapa_do_negocio"].astype("string").str.strip(),
            "data_primeira_compra": _para_data_iso(bruto["data_primeira_compra"]),
            "meses_desde_primeira_compra": _para_numero(bruto["meses_desde_primeira_compra"]),
        }
    )

    # Descarta o que não tem cliente ou safra (spec §3.3): sem e_mail ou sem 1ª compra.
    valido = (df["e_mail"].str.strip() != "") & df["data_primeira_compra"].notna()
    df = df[valido].copy()

    # Idade em inteiro; safra = mês-calendário da 1ª compra (a âncora, cross-canal).
    df["meses_desde_primeira_compra"] = (
        df["meses_desde_primeira_compra"].round().astype("Int64")
    )
    df["safra"] = df["data_primeira_compra"].dt.to_period("M").astype("string")

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Base HISTÓRICA de itens (2026-07-14) — o CMV real da história inteira.
# Mesma tabela silver da aba `Itens`, só que a história toda (2021-10 → hoje), extraída do
# BigQuery pelo João e salva como arquivo local (a mesma "torneira" do hubspot_deals.csv).
# É a 1ª camada da resolução de itens; a planilha vira fallback (spec 2026-07-14
# `cmv-real-historico-3-camadas`). Ausência do arquivo NÃO derruba o painel: devolve vazio
# e o cálculo degrada para o comportamento anterior (planilha + 30% estimado).
# ---------------------------------------------------------------------------
CAMINHO_ITENS_HISTORICO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "bases", "itens_historico.csv"
)

# Só o que serve ao CMV + a ponte. O `email` do export NÃO é lido (dado pessoal, inútil aqui).
_ITENS_HISTORICO_COLUNAS = ["name", "data_order", "item_desmembrado_codigo", "quantidade_final"]

COLUNAS_ITENS_HISTORICO = ["order_name", "data", "sku", "quantidade"]


def itens_historico_vazio() -> pd.DataFrame:
    """A base histórica no formato certo, porém vazia (arquivo ausente = degrada, não quebra)."""
    return pd.DataFrame(
        {
            "order_name": pd.Series(dtype="string"),
            "data": pd.Series(dtype="datetime64[ns]"),
            "sku": pd.Series(dtype="string"),
            "quantidade": pd.Series(dtype="float64"),
        }
    )


def carregar_itens_historico(caminho: str = CAMINHO_ITENS_HISTORICO) -> pd.DataFrame:
    """
    Lê a base histórica de itens (`bases/itens_historico.csv`, ~1,3 M linhas) e devolve
    `order_name | data | sku | quantidade` — o item a item de todo pedido desde 2021-10.

    `order_name` é o **número humano** do pedido (`name` no export), a ponte direta com o
    `nome` do HubSpot. Vem com `#` na origem (`#7877`) — removido aqui, dos dois lados da ponte.

    Arquivo ausente -> devolve **vazio** (sem erro): o CMV volta a sair da planilha (2ª camada)
    e do estimado de 30% (3ª). É a garantia de que o painel nunca depende deste arquivo.
    """
    if not os.path.exists(caminho):
        return itens_historico_vazio()

    bruto = pd.read_csv(
        caminho,
        usecols=_ITENS_HISTORICO_COLUNAS,
        dtype={"name": "string", "item_desmembrado_codigo": "string"},
    )
    _exigir_colunas(bruto, "itens_historico.csv", _ITENS_HISTORICO_COLUNAS)

    # `data_order` vem ISO com hora e fuso ("2021-10-21 14:48:38 UTC") — só a data interessa.
    return pd.DataFrame(
        {
            "order_name": bruto["name"].str.strip().str.lstrip("#"),
            "data": pd.to_datetime(bruto["data_order"].str.slice(0, 10), errors="coerce"),
            "sku": bruto["item_desmembrado_codigo"].fillna("").str.strip(),
            "quantidade": pd.to_numeric(bruto["quantidade_final"], errors="coerce").fillna(0.0),
        }
    )


# ---------------------------------------------------------------------------
# Mapa SKU -> linha de produto (a "porta de entrada") — arquivo LOCAL versionado,
# validado à mão pelo João (2026-07-15). Régua da aba "4. Portas de entrada".
# Classifica cada SKU numa linha de produto e num papel (porta/brinde/desconhecido).
# ---------------------------------------------------------------------------
CAMINHO_MAPA_PORTAS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "bases", "mapa_sku_linha_produto.csv"
)

_MAPA_PORTAS_COLUNAS = ["sku", "linha", "papel"]


def carregar_mapa_portas(caminho: str = CAMINHO_MAPA_PORTAS) -> pd.DataFrame:
    """
    Lê o mapa SKU -> linha de produto (`bases/mapa_sku_linha_produto.csv`) e devolve
    `sku | linha | papel`. `papel` é `porta` (produto vendável), `brinde` (carteira/BRINDE/
    Perfume/Skincare — não é porta) ou `desconhecido` (SKU sem nome cadastrado).

    Só a aba de Portas de entrada o lê. Arquivo ausente/coluna faltando = `ErroDeDados`
    (não degrada em silêncio: sem o mapa a feature não tem régua). Não derruba V1/V2/Cohorts.
    """
    if not os.path.exists(caminho):
        raise ErroDeDados(
            "O mapa de portas (`bases/mapa_sku_linha_produto.csv`) não foi encontrado — "
            "a aba Portas de entrada precisa dele para classificar o produto de estreia."
        )
    bruto = pd.read_csv(caminho, dtype={"sku": "string"})
    _exigir_colunas(bruto, "mapa_sku_linha_produto.csv", _MAPA_PORTAS_COLUNAS)
    return pd.DataFrame(
        {
            "sku": bruto["sku"].fillna("").str.strip(),
            "linha": bruto["linha"].fillna("").str.strip(),
            "papel": bruto["papel"].fillna("").str.strip(),
        }
    )


def carregar_descricoes() -> dict[str, str]:
    """
    Dicionário SKU -> nome do produto, da base silver (para a auditoria de custos).
    É OPCIONAL: se a base falhar ou faltar coluna, devolve vazio (mostra só o código).
    """
    try:
        df = _ler_csv(GID_DESCRICOES, "Descrições")
    except ErroDeDados:
        return {}
    if "item_desmembrado_codigo" not in df.columns or "item_desmembrado_nome" not in df.columns:
        return {}
    sku = df["item_desmembrado_codigo"].astype("string").str.strip()
    nome = df["item_desmembrado_nome"].astype("string").str.strip()
    tabela = pd.DataFrame({"sku": sku, "nome": nome})
    tabela = tabela[(tabela["sku"] != "") & (tabela["nome"] != "")]
    tabela = tabela.drop_duplicates(subset="sku", keep="first")
    return dict(zip(tabela["sku"], tabela["nome"]))
