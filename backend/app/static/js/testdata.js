/* imPress v2.2: Test data page (super admins). Test mode on/off with the
 * decision about the test data afterwards, a seeded generator, and a small
 * spreadsheet: one tab per table, Excel-style keyboard editing, paste from
 * Google Sheets / Excel, CSV upload and download per tab, validation with
 * cell-level errors, all-or-nothing import. */

const TD = {
  schema: null, sheets: {}, tab: 'teachers', sel: { r: 0, c: 0 }, anchor: null, editing: false,
  errors: [], seed: 1, counts: null, simulate: true,
};

function tdSaveDraft() {
  try { localStorage.setItem('impress.testdata.draft', JSON.stringify({ sheets: TD.sheets, seed: TD.seed })); } catch { /* storage unavailable */ }
}
function tdLoadDraft() {
  try {
    const d = JSON.parse(localStorage.getItem('impress.testdata.draft') || 'null');
    if (d && d.sheets) { TD.sheets = d.sheets; TD.seed = d.seed || 1; }
  } catch { /* none */ }
}

async function renderTestData(app) {
  const user = await authApi.me();
  if (user.role !== 'super_admin') { navigate('#/admin'); return; }
  const [state, schema] = await Promise.all([testModeApi.state(), testModeApi.schema()]);
  TD.schema = schema;
  TD.password = state.test_password;
  TD.counts = TD.counts || { ...schema.defaults };
  if (!Object.keys(TD.sheets).length) tdLoadDraft();
  for (const s of schema.sheets) TD.sheets[s.name] = TD.sheets[s.name] || [];
  System.test_mode = state.on;
  renderBanners();
  app.innerHTML = `
    ${renderNavbar(user, '#/admin/test-data')}
    <div class="container">
      ${pageHeader('Test data', 'Try imPress with realistic data without touching the real database: turn on test mode, then generate, paste or upload test data.', '', 'Administration')}
      ${tdModeCard(state)}
      ${state.on ? tdGeneratorCard() + tdSheetCard() : tdOffHelp()}
    </div>
    <div id="td-pending-modal" class="modal hidden"><div class="modal-backdrop"></div>
      <div class="modal-content card"><h2>Keep the test data?</h2>
        <p class="text-muted">Test mode is off and imPress is back on the real data. The test data you worked on is kept aside for now. Save it to load it again next time, export it as CSV files, or delete it.</p>
        <div class="form-group"><label for="td-save-name">Name to save it under</label><input id="td-save-name" maxlength="48" placeholder="e.g. Monsoon demo"></div>
        <div class="modal-actions">
          <button class="btn btn-danger-soft" id="td-p-delete">${icon('trash', 'sm')} Delete</button>
          <button class="btn btn-outline" id="td-p-export">${icon('download', 'sm')} Export CSV</button>
          <button class="btn btn-primary" id="td-p-save">${icon('save', 'sm')} Save</button></div></div></div>`;
  wireTestData(state);
}

function tdModeCard(st) {
  const ds = st.datasets || [];
  return `<div class="card">
    <div class="card-header"><div><h2>${icon('flask')} Test mode</h2>
      <div class="card-sub">${st.on ? `On since ${istDateTime(istParseToEpoch(st.since))}, by ${escHtml(st.by || '?')}. Everyone sees the test mode banner.` : 'Off: imPress is working on the real data.'}</div></div>
      ${st.on && st.forced ? `<span class="badge badge-warning">${icon('lock', 'sm')} Enabled by root</span>`
        : st.on ? `<button class="btn btn-danger-soft btn-sm" id="td-off">${icon('power', 'sm')} Turn off and return to the real data</button>`
        : `<div class="page-actions"><select id="td-dataset" class="input-sm" style="width:auto" aria-label="Start from">
             <option value="">Start from a copy of the real data</option>
             ${ds.map(d => `<option value="${escHtml(d.name)}">Load saved: ${escHtml(d.name)}</option>`).join('')}</select>
           <button class="btn btn-primary" id="td-on">${icon('flask', 'sm')} Turn on test mode</button></div>`}
    </div>
    ${st.on && st.forced ? `<div class="trash-note">${icon('lock', 'sm')}<span>Test mode was enabled by root and cannot be turned off from here. This is intentional application design.</span></div>` : ''}
    <div class="grid-2">
      <div class="mini-stat"><span>Saved datasets</span><b>${ds.length}</b></div>
      <div class="mini-stat"><span>Waiting for a decision</span><b>${(st.pending || []).length}</b></div>
    </div>
    <details class="test-more"><summary>${icon('chevronRight', 'sm')} About the real data</summary>
      <p class="text-muted mt-1">${st.on ? 'The real database is kept safe and is not changed while test mode is on. Turning test mode off brings it back exactly as it was.' : 'The real database is in use. Turning on test mode works on a copy and leaves it unchanged.'}</p></details>
    ${(st.pending || []).length ? `<h3 class="mt-2 mb-1">Test data waiting for a decision</h3>${st.pending.map(p => `<div class="feed-item"><span class="feed-icon amber">${icon('clock', 'sm')}</span>
      <div class="feed-body"><b>${escHtml(p.id)}</b><span>${(p.size / 1024).toFixed(0)} KB</span></div>
      <button class="btn btn-sm btn-outline" ${callAttr('tdPending', p.id)}>Decide</button></div>`).join('')}` : ''}
    ${ds.length ? `<h3 class="mt-2 mb-1">Saved datasets</h3><div class="table-wrap"><table class="table"><thead><tr><th>Name</th><th>Contents</th><th>Saved</th><th></th></tr></thead><tbody>
      ${ds.map(d => `<tr><td><b>${escHtml(d.name)}</b></td><td class="text-sm">${d.counts ? `${d.counts.students} students · ${d.counts.classes} classes · ${d.counts.teachers} teachers` : '—'}</td>
        <td class="text-sm">${d.saved_at ? istDateTime(istParseToEpoch(d.saved_at)) : '—'}${d.by ? ` · ${escHtml(d.by)}` : ''}</td>
        <td class="nowrap"><button class="btn btn-sm btn-outline" data-action="td-export" data-name="${escHtml(d.name)}">${icon('download', 'sm')} Export</button>
          <button class="btn btn-sm btn-danger-ghost" ${callAttr('tdDeleteDataset', d.name)}>${icon('trash', 'sm')}</button></td></tr>`).join('')}</tbody></table></div>` : ''}
  </div>`;
}

function tdOffHelp() {
  return `<div class="card"><div class="grid-3">
    <div class="feed-item"><span class="feed-icon">${icon('shield', 'sm')}</span><div class="feed-body"><b>The real data is safe</b>
      <span>Turning test mode on copies the database aside (it must verify first); everything you do happens on a copy.</span></div></div>
    <div class="feed-item"><span class="feed-icon">${icon('table', 'sm')}</span><div class="feed-body"><b>Sheets like a spreadsheet</b>
      <span>Teachers, courses, students, classes, enrolments, quizzes and polls: type, paste from Google Sheets or Excel, or upload CSV.</span></div></div>
    <div class="feed-item"><span class="feed-icon">${icon('sparkles', 'sm')}</span><div class="feed-body"><b>Realistic generator</b>
      <span>Unique, consistent data from a seed: the same seed gives the same data, with a term of past activity if you want.</span></div></div>
  </div></div>`;
}

function tdGeneratorCard() {
  const lim = TD.schema.limits;
  const fields = [['teachers', 'Teachers'], ['courses', 'Courses'], ['students', 'Students'], ['classes', 'Classes'],
    ['classes_per_student', 'Classes per student'], ['quizzes_per_class', 'Quizzes per class'], ['questions_per_quiz', 'Questions per quiz'], ['polls_per_class', 'Polls per class']];
  return `<div class="card"><div class="card-header"><div><h2>${icon('sparkles')} Generate test data</h2>
      <div class="card-sub">Fills the sheets below (nothing is saved until you import). Teachers it creates sign in with the password <code>${escHtml(TD.password)}</code>.</div></div></div>
    <div class="form-grid-3" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">
      <label>Seed<div class="flex gap-1"><input id="td-seed" type="number" min="0" value="${TD.seed}"><button class="btn btn-outline btn-icon" id="td-seed-rand" title="Random seed" aria-label="Random seed">${icon('refresh', 'sm')}</button></div></label>
      ${fields.map(([k, l]) => `<label>${l}<input type="number" min="0" max="${lim[k]}" data-count="${k}" value="${TD.counts[k]}"></label>`).join('')}
    </div>
    <div class="flex gap-1 mt-1"><button class="btn btn-primary" id="td-generate">${icon('sparkles', 'sm')} Generate into the sheets</button>
      <span class="text-sm text-muted">Replaces what is in the sheets.</span></div></div>`;
}

function tdSheetCard() {
  return `<div class="card"><div class="card-header"><div><h2>${icon('table')} Sheets</h2>
      <div class="card-sub">Click a cell and type. Arrow keys, Tab and Enter move; Shift+arrows select; Ctrl+C / Ctrl+V copy and paste blocks; Delete clears.</div></div>
      <div class="page-actions">
        <label class="btn btn-outline btn-sm">${icon('upload', 'sm')} Upload CSV<input type="file" id="td-csv" accept=".csv,text/csv" class="sr-only"></label>
        <button class="btn btn-outline btn-sm" id="td-csv-down">${icon('download', 'sm')} Download tab</button>
        <button class="btn btn-outline btn-sm" id="td-add">${icon('plus', 'sm')} 10 rows</button>
        <button class="btn btn-outline btn-sm" id="td-del">${icon('trash', 'sm')} Delete selected rows</button>
        <button class="btn btn-danger-ghost btn-sm" id="td-clear">Clear tab</button>
      </div></div>
    <div class="sheet-tabs" role="tablist" id="td-tabs"></div>
    <div class="sheet-wrap" id="td-wrap" tabindex="0" aria-label="Sheet"><table class="sheet" id="td-sheet"></table></div>
    <div class="sheet-status"><span id="td-status"></span>
      <div class="flex gap-1"><label class="check-row"><input type="checkbox" id="td-sim" ${TD.simulate ? 'checked' : ''}> Simulate a term of activity (answers, votes, attendance)</label>
        <button class="btn btn-outline" id="td-validate">${icon('checkCircle', 'sm')} Check</button>
        <button class="btn btn-primary" id="td-import">${icon('database', 'sm')} Import into the test database</button></div></div>
    <div id="td-errors"></div></div>`;
}

function tdCols() { return TD.schema.sheets.find(s => s.name === TD.tab).columns; }
function tdRows() { return TD.sheets[TD.tab]; }

function tdEnsureRows(n) {
  const rows = tdRows();
  while (rows.length < n) rows.push({});
}

function tdRender() {
  const tabs = document.getElementById('td-tabs');
  if (!tabs) return;
  const errBy = {};
  TD.errors.forEach(e => { errBy[e.sheet] = (errBy[e.sheet] || 0) + 1; });
  tabs.innerHTML = TD.schema.sheets.map(s => {
    const n = (TD.sheets[s.name] || []).filter(r => Object.values(r).some(v => String(v ?? '').trim())).length;
    return `<button role="tab" class="${s.name === TD.tab ? 'active' : ''}" data-sheet="${s.name}" aria-selected="${s.name === TD.tab}">
      ${escHtml(s.label)} <span class="n ${errBy[s.name] ? 'err' : ''}">${errBy[s.name] ? errBy[s.name] + (errBy[s.name] === 1 ? ' error' : ' errors') : n}</span></button>`;
  }).join('');
  tabs.querySelectorAll('[data-sheet]').forEach(b => b.onclick = () => { TD.tab = b.dataset.sheet; TD.sel = { r: 0, c: 0 }; TD.anchor = null; tdRender(); });
  const cols = tdCols();
  tdEnsureRows(Math.max(20, tdRows().length + 3));
  const bad = new Set(TD.errors.filter(e => e.sheet === TD.tab).map(e => `${e.row - 1}:${e.column}`));
  const [r0, r1, c0, c1] = tdRange();
  document.getElementById('td-sheet').innerHTML = `<thead><tr><th class="rownum">#</th>${cols.map(c =>
    `<th class="${c.required ? 'req' : ''}" title="${escHtml(c.help || '')}">${escHtml(c.label)}</th>`).join('')}</tr></thead>
    <tbody>${tdRows().map((row, r) => `<tr><td class="rownum">${r + 1}</td>${cols.map((c, ci) => {
      const cls = ['cell'];
      if (r === TD.sel.r && ci === TD.sel.c) cls.push('sel');
      else if (r >= r0 && r <= r1 && ci >= c0 && ci <= c1) cls.push('range');
      if (bad.has(`${r}:${c.name}`)) cls.push('bad');
      return `<td class="${cls.join(' ')}" data-r="${r}" data-c="${ci}">${escHtml(row[c.name] ?? '')}</td>`;
    }).join('')}</tr>`).join('')}</tbody>`;
  const filled = tdRows().filter(r => Object.values(r).some(v => String(v ?? '').trim())).length;
  document.getElementById('td-status').textContent = `${TD.schema.sheets.find(s => s.name === TD.tab).label}: ${filled} row${filled === 1 ? '' : 's'}`;
  tdRenderErrors();
}

function tdRange() {
  const a = TD.anchor || TD.sel;
  return [Math.min(a.r, TD.sel.r), Math.max(a.r, TD.sel.r), Math.min(a.c, TD.sel.c), Math.max(a.c, TD.sel.c)];
}

function tdRenderErrors() {
  const box = document.getElementById('td-errors');
  if (!box) return;
  if (!TD.errors.length) { box.innerHTML = ''; return; }
  box.innerHTML = `<div class="callout danger mt-1"><b>${TD.errors.length} problem${TD.errors.length === 1 ? '' : 's'} to fix</b> (nothing was imported)
    <ul class="err-list">${TD.errors.slice(0, 200).map((e, i) => `<li><a data-err="${i}">${escHtml(TD.schema.sheets.find(s => s.name === e.sheet)?.label || e.sheet)}, row ${e.row}${e.column ? `, ${escHtml(e.column)}` : ''}</a>: ${escHtml(e.message)}</li>`).join('')}</ul></div>`;
  box.querySelectorAll('[data-err]').forEach(a => a.onclick = () => {
    const e = TD.errors[+a.dataset.err];
    if (!TD.schema.sheets.some(s => s.name === e.sheet)) return;
    TD.tab = e.sheet;
    TD.sel = { r: Math.max(0, e.row - 1), c: Math.max(0, TD.schema.sheets.find(s => s.name === e.sheet).columns.findIndex(c => c.name === e.column)) };
    TD.anchor = null;
    tdRender();
    document.querySelector('#td-sheet td.sel')?.scrollIntoView({ block: 'center', inline: 'nearest' });
    document.getElementById('td-wrap').focus();
  });
}

function tdCell(r, c) { return document.querySelector(`#td-sheet td[data-r="${r}"][data-c="${c}"]`); }

function tdMove(dr, dc, extend = false) {
  const cols = tdCols();
  if (extend && !TD.anchor) TD.anchor = { ...TD.sel };
  if (!extend) TD.anchor = null;
  TD.sel = { r: Math.max(0, TD.sel.r + dr), c: Math.min(cols.length - 1, Math.max(0, TD.sel.c + dc)) };
  tdEnsureRows(TD.sel.r + 3);
  tdRender();
  tdCell(TD.sel.r, TD.sel.c)?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
}

function tdEdit(initial = null) {
  const td = tdCell(TD.sel.r, TD.sel.c);
  if (!td) return;
  const col = tdCols()[TD.sel.c];
  const row = tdRows()[TD.sel.r];
  TD.editing = true;
  td.classList.add('editing');
  td.innerHTML = '<input aria-label="Cell">';
  const input = td.querySelector('input');
  input.value = initial != null ? initial : (row[col.name] ?? '');
  input.focus();
  if (initial == null) input.select();
  const finish = (save, move) => {
    if (!TD.editing) return;
    TD.editing = false;
    if (save) { row[col.name] = input.value; TD.errors = TD.errors.filter(e => !(e.sheet === TD.tab && e.row - 1 === TD.sel.r && e.column === col.name)); tdSaveDraft(); }
    if (move) tdMove(move[0], move[1]); else tdRender();
    document.getElementById('td-wrap').focus();
  };
  input.onkeydown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); finish(true, [1, 0]); }
    else if (e.key === 'Tab') { e.preventDefault(); finish(true, [0, e.shiftKey ? -1 : 1]); }
    else if (e.key === 'Escape') { e.preventDefault(); finish(false); }
    e.stopPropagation();
  };
  input.onblur = () => finish(true);
}

function tdCopy() {
  const cols = tdCols();
  const [r0, r1, c0, c1] = tdRange();
  const lines = [];
  for (let r = r0; r <= r1; r++) {
    const row = tdRows()[r] || {};
    lines.push(cols.slice(c0, c1 + 1).map(c => String(row[c.name] ?? '').replace(/[\t\n]/g, ' ')).join('\t'));
  }
  return lines.join('\n');
}

function tdPaste(text) {
  const cols = tdCols();
  const grid = parseDelimited(text.replace(/\r\n?/g, '\n').replace(/\n$/, ''), text.includes('\t') ? '\t' : ',');
  if (!grid.length) return;
  // A header row naming the columns: map by name (paste of a whole sheet).
  const header = grid[0].map(h => h.trim().toLowerCase());
  const byName = header.filter(h => cols.some(c => c.name === h || c.label.toLowerCase() === h)).length >= Math.min(2, header.length);
  if (byName && TD.sel.r === 0 && TD.sel.c === 0) {
    const map = header.map(h => cols.find(c => c.name === h || c.label.toLowerCase() === h));
    const rows = grid.slice(1).map(cells => Object.fromEntries(map.map((c, i) => c ? [c.name, cells[i] ?? ''] : null).filter(Boolean)));
    TD.sheets[TD.tab] = rows;
  } else {
    grid.forEach((cells, dr) => {
      tdEnsureRows(TD.sel.r + dr + 1);
      cells.forEach((v, dc) => { const col = cols[TD.sel.c + dc]; if (col) tdRows()[TD.sel.r + dr][col.name] = v; });
    });
    TD.anchor = { r: TD.sel.r, c: TD.sel.c };
    TD.sel = { r: TD.sel.r + grid.length - 1, c: Math.min(cols.length - 1, TD.sel.c + Math.max(...grid.map(g => g.length)) - 1) };
  }
  TD.errors = [];
  tdSaveDraft();
  tdRender();
  showToast(`Pasted ${grid.length} row${grid.length === 1 ? '' : 's'}`, 'success');
}

/* CSV / TSV parser: quotes, escaped quotes, embedded separators and newlines. */
function parseDelimited(text, sep = ',') {
  const rows = [];
  let row = [], field = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') q = false;
      else field += ch;
    } else if (ch === '"' && field === '') q = true;
    else if (ch === sep) { row.push(field); field = ''; }
    else if (ch === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (ch !== '\r') field += ch;
  }
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  return rows.filter(r => r.some(v => v.trim() !== ''));
}

function tdUsedRows(name) {
  return (TD.sheets[name] || []).filter(r => Object.values(r).some(v => String(v ?? '').trim()));
}

function wireTestData(state) {
  document.getElementById('td-on')?.addEventListener('click', async (e) => {
    const ds = document.getElementById('td-dataset').value || null;
    if (!confirm(`Turn on test mode${ds ? ` with the saved dataset "${ds}"` : ''}?\n\nThe real database is copied aside first, and everyone sees a test-mode banner until you turn it off.`)) return;
    e.target.disabled = true;
    try { await testModeApi.enable(ds); showToast('Test mode is on', 'success'); router(); } catch (err) { showToast(err.message, 'error'); e.target.disabled = false; }
  });
  document.getElementById('td-off')?.addEventListener('click', async (e) => {
    if (!confirm('Turn off test mode and go back to the real data?\n\nYou can then save, export or delete the test data.')) return;
    e.target.disabled = true;
    try {
      const r = await testModeApi.disable();
      showToast('Test mode is off: back on the real data', 'success');
      await renderTestData(document.getElementById('app'));
      if (r.pending_id) tdPending(r.pending_id);
    } catch (err) { showToast(err.message, 'error'); e.target.disabled = false; }
  });
  if (!state.on) return;

  document.getElementById('td-seed-rand').onclick = () => { document.getElementById('td-seed').value = Math.floor(Math.random() * 1e6); };
  document.querySelectorAll('[data-count]').forEach(i => i.onchange = () => { TD.counts[i.dataset.count] = +i.value; });
  document.getElementById('td-generate').onclick = async (e) => {
    TD.seed = +document.getElementById('td-seed').value || 0;
    document.querySelectorAll('[data-count]').forEach(i => { TD.counts[i.dataset.count] = +i.value || 0; });
    e.target.disabled = true;
    try {
      const r = await testModeApi.generate(TD.seed, TD.counts);
      TD.sheets = r.sheets;
      for (const s of TD.schema.sheets) TD.sheets[s.name] = TD.sheets[s.name] || [];
      TD.errors = [];
      TD.tab = 'teachers'; TD.sel = { r: 0, c: 0 }; TD.anchor = null;
      tdSaveDraft();
      tdRender();
      const n = Object.values(r.sheets).reduce((a, rows) => a + rows.length, 0);
      showToast(`Generated ${n} rows from seed ${TD.seed}`, 'success');
    } catch (err) { showToast(err.message, 'error'); } finally { e.target.disabled = false; }
  };

  const wrap = document.getElementById('td-wrap');
  document.getElementById('td-sheet').addEventListener('mousedown', (e) => {
    const td = e.target.closest('td.cell');
    if (!td || TD.editing) return;
    const pos = { r: +td.dataset.r, c: +td.dataset.c };
    if (e.shiftKey) { TD.anchor = TD.anchor || { ...TD.sel }; TD.sel = pos; } else { TD.sel = pos; TD.anchor = null; }
    tdRender();
    wrap.focus();
    e.preventDefault();
  });
  document.getElementById('td-sheet').addEventListener('dblclick', (e) => { if (e.target.closest('td.cell')) tdEdit(); });
  wrap.addEventListener('keydown', (e) => {
    if (TD.editing) return;
    const k = e.key;
    const mv = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[k];
    if (mv) { e.preventDefault(); tdMove(mv[0], mv[1], e.shiftKey); }
    else if (k === 'Tab') { e.preventDefault(); tdMove(0, e.shiftKey ? -1 : 1); }
    else if (k === 'Enter' || k === 'F2') { e.preventDefault(); tdEdit(); }
    else if (k === 'Delete' || k === 'Backspace') {
      e.preventDefault();
      const cols = tdCols();
      const [r0, r1, c0, c1] = tdRange();
      for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) if (tdRows()[r]) tdRows()[r][cols[c].name] = '';
      tdSaveDraft(); tdRender();
    } else if (k.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); tdEdit(k); }
  });
  wrap.addEventListener('copy', (e) => { if (TD.editing) return; e.preventDefault(); e.clipboardData.setData('text/plain', tdCopy()); showToast('Copied', 'success'); });
  wrap.addEventListener('cut', (e) => {
    if (TD.editing) return;
    e.preventDefault(); e.clipboardData.setData('text/plain', tdCopy());
    const cols = tdCols(); const [r0, r1, c0, c1] = tdRange();
    for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) if (tdRows()[r]) tdRows()[r][cols[c].name] = '';
    tdSaveDraft(); tdRender();
  });
  wrap.addEventListener('paste', (e) => { if (TD.editing) return; e.preventDefault(); tdPaste(e.clipboardData.getData('text/plain')); });

  document.getElementById('td-add').onclick = () => { tdEnsureRows(tdRows().length + 10); tdRender(); };
  document.getElementById('td-del').onclick = () => {
    const [r0, r1] = tdRange();
    tdRows().splice(r0, r1 - r0 + 1);
    TD.sel = { r: r0, c: TD.sel.c }; TD.anchor = null; TD.errors = [];
    tdSaveDraft(); tdRender();
  };
  document.getElementById('td-clear').onclick = () => {
    if (!confirm('Clear every row of this tab?')) return;
    TD.sheets[TD.tab] = []; TD.errors = []; TD.sel = { r: 0, c: 0 }; TD.anchor = null;
    tdSaveDraft(); tdRender();
  };
  document.getElementById('td-csv').onchange = async (e) => {
    const f = e.target.files[0];
    e.target.value = '';
    if (!f) return;
    if (f.size > 5_000_000) { showToast('The file is larger than 5 MB', 'error'); return; }
    TD.sel = { r: 0, c: 0 }; TD.anchor = null;
    const text = await f.text();
    const grid = parseDelimited(text.replace(/^﻿/, ''), ',');
    if (!grid.length) { showToast('The file is empty', 'error'); return; }
    const cols = tdCols();
    const header = grid[0].map(h => h.trim().toLowerCase());
    const map = header.map(h => cols.find(c => c.name === h || c.label.toLowerCase() === h));
    if (!map.some(Boolean)) { showToast(`No known columns. Use: ${cols.map(c => c.name).join(', ')}`, 'error'); return; }
    TD.sheets[TD.tab] = grid.slice(1).map(cells => Object.fromEntries(map.map((c, i) => c ? [c.name, (cells[i] ?? '').replace(/^'(?=[=+\-@])/, '')] : null).filter(Boolean)));
    TD.errors = [];
    tdSaveDraft(); tdRender();
    const unknown = header.filter((h, i) => !map[i]);
    showToast(`Loaded ${grid.length - 1} rows${unknown.length ? `; ignored columns: ${unknown.join(', ')}` : ''}`, unknown.length ? 'warning' : 'success');
  };
  document.getElementById('td-csv-down').onclick = () => {
    const cols = tdCols();
    downloadCsv(`impress-${TD.tab}.csv`, cols.map(c => c.name), tdUsedRows(TD.tab).map(r => cols.map(c => r[c.name] ?? '')));
  };
  document.getElementById('td-sim').onchange = (e) => { TD.simulate = e.target.checked; };
  const payload = () => Object.fromEntries(TD.schema.sheets.map(s => [s.name, tdUsedRows(s.name)]));
  document.getElementById('td-validate').onclick = async (e) => {
    e.target.disabled = true;
    try {
      const r = await testModeApi.validate(payload());
      TD.errors = r.errors || [];
      tdRender();
      showToast(r.ok ? 'Everything checks out' : `${TD.errors.length} problem${TD.errors.length === 1 ? '' : 's'} to fix`, r.ok ? 'success' : 'error');
    } catch (err) { showToast(err.message, 'error'); } finally { e.target.disabled = false; }
  };
  document.getElementById('td-import').onclick = async (e) => {
    const data = payload();
    const n = Object.values(data).reduce((a, rows) => a + rows.length, 0);
    if (!n) { showToast('The sheets are empty', 'error'); return; }
    if (!confirm(`Import ${n} rows into the test database?`)) return;
    e.target.disabled = true;
    try {
      const r = await testModeApi.import(data, TD.simulate, TD.seed);
      TD.errors = [];
      const im = r.imported || {};
      showToast(`Imported ${Object.entries(im).filter(([, v]) => v).map(([k, v]) => `${v} ${k}`).join(', ')}${r.activity && r.activity.answers ? `, with ${r.activity.answers} answers and ${r.activity.attendance} attendance records` : ''}`, 'success');
      TD.sheets = Object.fromEntries(TD.schema.sheets.map(s => [s.name, []]));
      tdSaveDraft();
      router();
    } catch (err) {
      TD.errors = (err.detail && err.detail.errors) || [];
      tdRender();
      showToast(err.message, 'error');
    } finally { e.target.disabled = false; }
  };
  tdRender();
}

window.tdPending = function (id) {
  const m = document.getElementById('td-pending-modal');
  m.classList.remove('hidden');
  document.getElementById('td-save-name').value = '';
  document.getElementById('td-p-save').onclick = async () => {
    const name = document.getElementById('td-save-name').value.trim();
    if (!name) { showToast('Give the dataset a name', 'error'); return; }
    try { await testModeApi.decide(id, 'save', name); showToast(`Saved as "${name}"`, 'success'); m.classList.add('hidden'); router(); } catch (err) { showToast(err.message, 'error'); }
  };
  document.getElementById('td-p-export').onclick = () => testModeApi.download('pending', id).catch(err => showToast(err.message, 'error'));
  document.getElementById('td-p-delete').onclick = async () => {
    if (!confirm('Delete this test data for good?')) return;
    try { await testModeApi.decide(id, 'delete'); showToast('Test data deleted', 'success'); m.classList.add('hidden'); router(); } catch (err) { showToast(err.message, 'error'); }
  };
};

window.tdDeleteDataset = async function (name) {
  if (!confirm(`Delete the saved dataset "${name}"?`)) return;
  try { await testModeApi.deleteDataset(name); showToast('Dataset deleted', 'success'); router(); } catch (err) { showToast(err.message, 'error'); }
};
