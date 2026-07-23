import json

with open("saida_local/jornada_dados.json", encoding="utf-8") as f:
    data = json.load(f)

data_json = json.dumps(data, ensure_ascii=False)

html = r"""<title>Jornada de Produto - Minimal Club</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7;
  --surface: #fcfcfb;
  --surface-2: #f2f1ec;
  --ink: #0b0b0b;
  --ink-2: #52514e;
  --ink-muted: #898781;
  --grid: #e1e0d9;
  --baseline: #c3c2b7;
  --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6;
  --series-2: #eb6834;
  --accent-wash: #eaf1fb;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page: #0d0d0d;
    --surface: #1a1a19;
    --surface-2: #232322;
    --ink: #ffffff;
    --ink-2: #c3c2b7;
    --ink-muted: #898781;
    --grid: #2c2c2a;
    --baseline: #383835;
    --border: rgba(255,255,255,0.10);
    --series-1: #3987e5;
    --series-2: #d95926;
    --accent-wash: #16232f;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d;
  --surface: #1a1a19;
  --surface-2: #232322;
  --ink: #ffffff;
  --ink-2: #c3c2b7;
  --ink-muted: #898781;
  --grid: #2c2c2a;
  --baseline: #383835;
  --border: rgba(255,255,255,0.10);
  --series-1: #3987e5;
  --series-2: #d95926;
  --accent-wash: #16232f;
}

* { box-sizing: border-box; }
html, body {
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}
body { padding: 32px 20px 64px; }

.wrap { max-width: 980px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }

header.top { display: flex; flex-direction: column; gap: 6px; }
header.top .eyebrow {
  font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--ink-muted);
}
header.top h1 { font-size: 24px; font-weight: 700; margin: 0; letter-spacing: -0.01em; text-wrap: balance; }
header.top p.sub { margin: 0; color: var(--ink-2); font-size: 14px; max-width: 62ch; line-height: 1.5; }

.banner {
  display: flex; align-items: center; gap: 10px;
  background: var(--accent-wash); border: 1px solid var(--border);
  border-radius: 8px; padding: 10px 14px; font-size: 13px; color: var(--ink-2);
}
.banner .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--series-2); flex: none; }

.controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.controls label { font-size: 13px; color: var(--ink-2); font-weight: 500; }
select#entrada {
  font: inherit; font-size: 14px; font-weight: 600; color: var(--ink);
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  padding: 8px 34px 8px 12px; cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6' fill='%23898781'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 12px center;
}
select#entrada:focus-visible { outline: 2px solid var(--series-1); outline-offset: 2px; }

.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.tile {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; display: flex; flex-direction: column; gap: 4px;
}
.tile .label { font-size: 12px; color: var(--ink-muted); font-weight: 500; }
.tile .value { font-size: 26px; font-weight: 700; font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
.tile .value small { font-size: 14px; font-weight: 600; color: var(--ink-2); }

.panels { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 720px) { .panels, .tiles { grid-template-columns: 1fr; } }

.panel {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px 18px 12px;
}
.panel h2 { font-size: 13px; font-weight: 600; margin: 0 0 2px; }
.panel p.hint { font-size: 12px; color: var(--ink-muted); margin: 0 0 10px; line-height: 1.4; }

svg.chart { width: 100%; height: auto; overflow: visible; }
svg.chart text { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--ink-2); }
.grid-line { stroke: var(--grid); stroke-width: 1; }
.baseline { stroke: var(--baseline); stroke-width: 1; }
.bar { fill: var(--series-1); }
.bar-label { font-size: 11px; font-weight: 700; fill: var(--ink); font-variant-numeric: tabular-nums; }
.axis-label { font-size: 11px; fill: var(--ink-muted); }
.line-1 { stroke: var(--series-1); stroke-width: 2; fill: none; }
.line-2 { stroke: var(--series-2); stroke-width: 2; fill: none; }
.dot-1 { fill: var(--series-1); }
.dot-2 { fill: var(--series-2); }

.legend { display: flex; gap: 16px; font-size: 12px; color: var(--ink-2); margin-top: 8px; }
.legend .item { display: flex; align-items: center; gap: 6px; }
.legend .swatch { width: 10px; height: 10px; border-radius: 2px; flex: none; }

.tooltip {
  position: absolute; pointer-events: none; background: var(--ink); color: var(--page);
  font-size: 12px; padding: 6px 9px; border-radius: 6px; transform: translate(-50%, -130%);
  white-space: nowrap; opacity: 0; transition: opacity 0.1s; z-index: 5; font-variant-numeric: tabular-nums;
}
.chart-wrap { position: relative; }

table.next-products { width: 100%; border-collapse: collapse; font-size: 13px; }
table.next-products th {
  text-align: left; font-size: 11px; font-weight: 600; color: var(--ink-muted);
  text-transform: uppercase; letter-spacing: 0.04em; padding: 0 10px 8px 0; border-bottom: 1px solid var(--grid);
}
table.next-products td { padding: 8px 10px 8px 0; vertical-align: top; border-bottom: 1px solid var(--grid); }
table.next-products tr:last-child td { border-bottom: none; }
.prod-row { display: flex; align-items: center; gap: 8px; margin: 3px 0; }
.prod-name { flex: 1; color: var(--ink-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.prod-bar-track { width: 64px; height: 6px; border-radius: 3px; background: var(--surface-2); flex: none; overflow: hidden; }
.prod-bar-fill { height: 100%; background: var(--series-1); border-radius: 3px; }
.prod-pct { width: 38px; text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; flex: none; }
.prod-pct.same { color: var(--series-1); }
tr.linha-nao-voltou td { border-top: 1px dashed var(--grid); border-bottom: none; padding-top: 10px; }
tr.linha-nao-voltou .prod-name { font-style: italic; color: var(--ink-muted); }
tr.linha-nao-voltou .prod-pct { color: var(--ink-muted); }

footer.note { font-size: 12px; color: var(--ink-muted); line-height: 1.6; padding-top: 4px; }
footer.note code { background: var(--surface-2); padding: 1px 5px; border-radius: 4px; font-size: 11px; }
</style>

<div class="wrap">
  <header class="top">
    <div class="eyebrow">Minimal Club &middot; An&aacute;lise local &mdash; mc-growth</div>
    <h1>Jornada de Produto</h1>
    <p class="sub">A partir de quem entrou comprando <strong>um produto s&oacute;</strong> ou um dos <strong>combos aprovados</strong> (m&iacute;n. 1.000 clientes na entrada), quais produtos aparecem nas compras seguintes &mdash; por <strong>presen&ccedil;a</strong>, n&atilde;o pela classifica&ccedil;&atilde;o do carrinho inteiro (por isso as % de um passo podem somar mais de 100%: um pedido com 2 produtos conta pros 2).</p>
  </header>

  <div class="banner"><span class="dot"></span> Rascunho local, gerado em 2026-07-23 a partir das bases baixadas hoje. Nada disto est&aacute; no gerenciadordecrm ainda.</div>

  <div class="controls">
    <label for="entrada">Produto de entrada</label>
    <select id="entrada"></select>
  </div>

  <div class="tiles" id="tiles"></div>

  <div class="panels">
    <div class="panel">
      <h2>Reten&ccedil;&atilde;o do produto de entrada</h2>
      <p class="hint">% dos clientes cuja compra seguinte TEM o(s) produto(s) da entrada de novo (combo: os 2 precisam aparecer; pode vir mais coisa junto).</p>
      <div class="chart-wrap"><svg class="chart" id="chart-retencao" viewBox="0 0 400 220"></svg><div class="tooltip" id="tip-retencao"></div></div>
    </div>
    <div class="panel">
      <h2>Tempo at&eacute; a pr&oacute;xima compra</h2>
      <p class="hint">Mediana em dias &mdash; acumulado desde a entrada vs. intervalo desde a compra anterior.</p>
      <div class="chart-wrap"><svg class="chart" id="chart-tempo" viewBox="0 0 400 220"></svg><div class="tooltip" id="tip-tempo"></div></div>
      <div class="legend">
        <div class="item"><span class="swatch" style="background:var(--series-1)"></span>Acumulado desde a entrada</div>
        <div class="item"><span class="swatch" style="background:var(--series-2)"></span>Desde a compra anterior</div>
      </div>
    </div>
  </div>

  <div class="panel">
    <h2>O que ofertar em cada passo</h2>
    <p class="hint">TODOS os produtos que passaram do m&iacute;nimo de 30 clientes (nenhum corte de top-N escondido), em % da turma de entrada inteira &mdash; por isso a soma passa de 100% (pedido com 2 itens conta pros 2) e nenhum produto sozinho chega perto de 100% (a maioria da entrada nem voltou &mdash; linha de baixo). Destacado = faz parte da pr&oacute;pria entrada.</p>
    <div style="overflow-x:auto"><table class="next-products" id="tabela-produtos"></table></div>
  </div>

  <footer class="note">
    Fonte: <code>bases/hubspot_deals.csv</code> + <code>bases/itens_historico.csv</code> + <code>bases/mapa_sku_linha_produto.csv</code> &mdash;
    l&oacute;gica em <code>jornada_produto.py</code>, reaproveitando <code>cascata.itens_por_nome</code>, <code>portas._combo_por_pedido/_estreias</code> e <code>coortes.preparar_deals_cache</code>.
    Recente/ativo/inativo usa a mesma r&eacute;gua oficial de <code>fact_repurchase_monthly_metrics</code> (6/11 meses).
    As 3 tabelas de recente &times; ativo &times; inativo (produto por produto) est&atilde;o na nota completa:
    <code>mc-growth/docs/sessions/2026-07-23-jornada-de-produto.md</code>.
  </footer>
</div>

<script id="jornada-data" type="application/json">__DATA__</script>
<script>
const DADOS = JSON.parse(document.getElementById('jornada-data').textContent);
const sel = document.getElementById('entrada');
DADOS.forEach((e, i) => {
  const opt = document.createElement('option');
  opt.value = i;
  opt.textContent = e.nome + ' (' + e.n.toLocaleString('pt-BR') + ' clientes)';
  sel.appendChild(opt);
});

function fmtN(n) { return n.toLocaleString('pt-BR'); }
function rot(compra) { return compra.replace(/a/, 'ª'); } // "2a" -> "2ª", "5a+" -> "5ª+"

function render(idx) {
  const e = DADOS[idx];
  const c2 = e.compras.find(c => c.compra === '2a');
  const t2 = e.tempos.find(t => t.compra === '2a');
  const tiles = document.getElementById('tiles');
  tiles.innerHTML = '';
  const tileData = [
    { label: 'Clientes com esta entrada', value: fmtN(e.n) },
    { label: 'Não voltaram (2ª compra)', value: c2 ? c2.pct_nao_voltou.toFixed(0) + '%' : '-' },
    { label: 'Têm o mesmo produto de novo (2ª compra)', value: c2 ? c2.pct_mesmo_produto.toFixed(0) + '%' : '-' },
    { label: 'Mediana até a 2ª compra', value: t2 ? t2.acumulado.toFixed(0) + ' <small>dias</small>' : '-' },
    { label: 'LTV 180 dias (mediana)', value: 'R$ ' + e.ltv_180d_mediana.toFixed(0) },
    { label: 'Taxa de repetição (alguma vez)', value: e.taxa_repeticao.toFixed(1) + '%' },
    { label: 'Taxa de reativação (alguma vez)', value: e.taxa_reativacao.toFixed(1) + '%' },
    { label: 'Status hoje: recente / ativo / inativo', value: e.pct_recente_hoje.toFixed(0) + '% <small>/</small> ' + e.pct_ativo_hoje.toFixed(0) + '% <small>/</small> ' + e.pct_inativo_hoje.toFixed(0) + '%' },
  ];
  tileData.forEach(t => {
    const div = document.createElement('div');
    div.className = 'tile';
    div.innerHTML = '<div class="label">' + t.label + '</div><div class="value">' + t.value + '</div>';
    tiles.appendChild(div);
  });

  renderRetencao(e);
  renderTempo(e);
  renderTabela(e);
}

function renderRetencao(e) {
  const svg = document.getElementById('chart-retencao');
  const tip = document.getElementById('tip-retencao');
  svg.innerHTML = '';
  const W = 400, H = 220, padL = 30, padR = 10, padT = 10, padB = 28;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const steps = e.compras.map(c => c.compra);
  const vals = e.compras.map(c => c.pct_mesmo_produto);
  const maxV = Math.max(10, ...vals) * 1.15;
  const bw = plotW / steps.length;

  const ns = 'http://www.w3.org/2000/svg';
  function el(tag, attrs) {
    const n = document.createElementNS(ns, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  for (let i = 0; i <= 3; i++) {
    const y = padT + plotH - (plotH * i / 3);
    svg.appendChild(el('line', { x1: padL, x2: W - padR, y1: y, y2: y, class: 'grid-line' }));
  }
  svg.appendChild(el('line', { x1: padL, x2: W - padR, y1: padT + plotH, y2: padT + plotH, class: 'baseline' }));

  steps.forEach((s, i) => {
    const v = vals[i];
    const barH = (v / maxV) * plotH;
    const x = padL + i * bw + bw * 0.22;
    const w = bw * 0.56;
    const y = padT + plotH - barH;
    const rect = el('rect', { x, y, width: w, height: Math.max(barH, 2), rx: 4, ry: 4, class: 'bar' });
    rect.addEventListener('mousemove', (ev) => showTip(tip, svg, ev, rot(s) + ' compra: ' + v.toFixed(1) + '% recompram ' + e.nome));
    rect.addEventListener('mouseleave', () => tip.style.opacity = 0);
    svg.appendChild(rect);
    const lbl = el('text', { x: x + w / 2, y: y - 6, class: 'bar-label', 'text-anchor': 'middle' });
    lbl.textContent = v.toFixed(0) + '%';
    svg.appendChild(lbl);
    const axl = el('text', { x: x + w / 2, y: H - 8, class: 'axis-label', 'text-anchor': 'middle' });
    axl.textContent = rot(s);
    svg.appendChild(axl);
  });
}

function renderTempo(e) {
  const svg = document.getElementById('chart-tempo');
  const tip = document.getElementById('tip-tempo');
  svg.innerHTML = '';
  const W = 400, H = 220, padL = 34, padR = 14, padT = 14, padB = 28;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const rows = e.tempos;
  if (!rows.length) return;
  const maxV = Math.max(...rows.map(r => Math.max(r.acumulado, r.gap))) * 1.15;
  const stepX = rows.length > 1 ? plotW / (rows.length - 1) : 0;

  const ns = 'http://www.w3.org/2000/svg';
  function el(tag, attrs) {
    const n = document.createElementNS(ns, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  for (let i = 0; i <= 3; i++) {
    const y = padT + plotH - (plotH * i / 3);
    svg.appendChild(el('line', { x1: padL, x2: W - padR, y1: y, y2: y, class: 'grid-line' }));
  }
  svg.appendChild(el('line', { x1: padL, x2: W - padR, y1: padT + plotH, y2: padT + plotH, class: 'baseline' }));

  function pathFor(key) {
    return rows.map((r, i) => {
      const x = padL + i * stepX;
      const y = padT + plotH - (r[key] / maxV) * plotH;
      return (i === 0 ? 'M' : 'L') + x + ',' + y;
    }).join(' ');
  }
  svg.appendChild(el('path', { d: pathFor('acumulado'), class: 'line-1' }));
  svg.appendChild(el('path', { d: pathFor('gap'), class: 'line-2' }));

  rows.forEach((r, i) => {
    const x = padL + i * stepX;
    [['acumulado', 'dot-1', 'Acumulado desde a entrada'], ['gap', 'dot-2', 'Desde a compra anterior']].forEach((triple) => {
      const key = triple[0], cls = triple[1], label = triple[2];
      const y = padT + plotH - (r[key] / maxV) * plotH;
      const c = el('circle', { cx: x, cy: y, r: 4, class: cls });
      c.addEventListener('mousemove', (ev) => showTip(tip, svg, ev, rot(r.compra) + ' compra — ' + label + ': ' + r[key].toFixed(0) + ' dias'));
      c.addEventListener('mouseleave', () => tip.style.opacity = 0);
      svg.appendChild(c);
    });
    const axl = el('text', { x, y: H - 8, class: 'axis-label', 'text-anchor': 'middle' });
    axl.textContent = rot(r.compra);
    svg.appendChild(axl);
  });
}

function showTip(tip, svg, ev, text) {
  const parent = svg.parentElement.getBoundingClientRect();
  tip.textContent = text;
  tip.style.left = (ev.clientX - parent.left) + 'px';
  tip.style.top = (ev.clientY - parent.top) + 'px';
  tip.style.opacity = 1;
}

function renderTabela(e) {
  const table = document.getElementById('tabela-produtos');
  const steps = e.compras.map(c => c.compra);
  let thead = '<thead><tr>' + steps.map(s => '<th>' + rot(s) + ' compra</th>').join('') + '</tr></thead>';
  const maxRows = Math.max.apply(null, e.compras.map(c => c.produtos.length));
  let rowsHtml = '';
  for (let r = 0; r < maxRows; r++) {
    rowsHtml += '<tr>';
    e.compras.forEach(c => {
      const p = c.produtos[r];
      if (!p) { rowsHtml += '<td></td>'; return; }
      const same = e.linhas_requeridas.includes(p.produto);
      rowsHtml += '<td><div class="prod-row">' +
        '<div class="prod-name" title="' + p.produto + '">' + p.produto + '</div>' +
        '<div class="prod-bar-track"><div class="prod-bar-fill" style="width:' + Math.min(100, p.pct * 1.3) + '%"></div></div>' +
        '<div class="prod-pct ' + (same ? 'same' : '') + '">' + p.pct.toFixed(1) + '%</div>' +
        '</div></td>';
    });
    rowsHtml += '</tr>';
  }
  // Linha final: quem nem chegou a fazer essa compra — pra nunca parecer que os
  // produtos "somam pouco" sem dizer por que (a maior parte é gente que não voltou).
  rowsHtml += '<tr class="linha-nao-voltou">';
  e.compras.forEach(c => {
    rowsHtml += '<td><div class="prod-row">' +
      '<div class="prod-name">N&atilde;o fez essa compra</div>' +
      '<div class="prod-bar-track"></div>' +
      '<div class="prod-pct">' + c.pct_nao_voltou.toFixed(1) + '%</div>' +
      '</div></td>';
  });
  rowsHtml += '</tr>';
  table.innerHTML = thead + '<tbody>' + rowsHtml + '</tbody>';
}

sel.addEventListener('change', () => render(Number(sel.value)));
render(0);
</script>
"""

html = html.replace("__DATA__", data_json)

with open("saida_local/jornada_produto_painel.html", "w", encoding="utf-8") as f:
    f.write(html)

print("escrito", len(html), "bytes")
