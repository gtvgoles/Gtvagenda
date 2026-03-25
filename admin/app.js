const els = {
  owner: document.getElementById('owner'),
  repo: document.getElementById('repo'),
  branch: document.getElementById('branch'),
  manualPath: document.getElementById('manualPath'),
  token: document.getElementById('token'),
  sourceUrl: document.getElementById('sourceUrl'),
  streamLink: document.getElementById('streamLink'),
  logoLocal: document.getElementById('logoLocal'),
  logoVisita: document.getElementById('logoVisita'),
  activo: document.getElementById('activo'),
  editIndex: document.getElementById('editIndex'),
  formTitle: document.getElementById('formTitle'),
  manualForm: document.getElementById('manualForm'),
  manualTable: document.getElementById('manualTable'),
  tableBody: document.querySelector('#manualTable tbody'),
  emptyState: document.getElementById('emptyState'),
  status: document.getElementById('status'),
  saveRepoBtn: document.getElementById('saveRepoBtn'),
  saveSettingsBtn: document.getElementById('saveSettingsBtn'),
  testConnectionBtn: document.getElementById('testConnectionBtn'),
  refreshBtn: document.getElementById('refreshBtn'),
  cancelEditBtn: document.getElementById('cancelEditBtn')
};

let state = {
  items: [],
  sha: null
};

const STORAGE_KEY = 'gtv-agenda-admin-settings-v1';

init();

async function init() {
  await preloadConfig();
  loadSavedSettings();
  render();
}

async function preloadConfig() {
  try {
    const res = await fetch('../data/config.json', { cache: 'no-store' });
    if (!res.ok) return;
    const config = await res.json();
    if (!els.owner.value) els.owner.value = config.owner || '';
    if (!els.repo.value) els.repo.value = config.repo || '';
    if (!els.branch.value) els.branch.value = config.branch || 'main';
    if (!els.manualPath.value) els.manualPath.value = config.manualPath || 'data/manual_sofa.json';
  } catch (_) {}
}

function loadSavedSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    els.owner.value = saved.owner || els.owner.value;
    els.repo.value = saved.repo || els.repo.value;
    els.branch.value = saved.branch || els.branch.value;
    els.manualPath.value = saved.manualPath || els.manualPath.value;
    els.token.value = saved.token || '';
  } catch (_) {}
}

function saveSettingsLocal() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    owner: els.owner.value.trim(),
    repo: els.repo.value.trim(),
    branch: els.branch.value.trim() || 'main',
    manualPath: els.manualPath.value.trim() || 'data/manual_sofa.json',
    token: els.token.value.trim()
  }));
}

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.style.borderColor = isError ? 'rgba(220,38,38,.6)' : '#1e293b';
  els.status.style.color = isError ? '#fecaca' : '#cbd5e1';
}

function extractSofaId(url) {
  const s = String(url || '').trim();
  const m1 = s.match(/#id:(\d+)/i);
  if (m1) return m1[1];
  const m2 = s.match(/\/event\/(\d+)/i);
  if (m2) return m2[1];
  return '';
}

function buildPayload() {
  return {
    manual_sofa: state.items
  };
}

function normalizeUrl(v) {
  return String(v || '').trim();
}

function render() {
  const hasItems = state.items.length > 0;
  els.emptyState.classList.toggle('hidden', hasItems);
  els.manualTable.classList.toggle('hidden', !hasItems);
  els.tableBody.innerHTML = '';

  state.items.forEach((item, index) => {
    const tr = document.createElement('tr');
    const sofaId = item.sofaId || extractSofaId(item.sourceUrl);
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td><a href="${escapeAttr(item.sourceUrl || '#')}" target="_blank" rel="noreferrer">Abrir link</a></td>
      <td>${escapeHtml(sofaId || '-')}</td>
      <td>${item.link ? `<a href="${escapeAttr(item.link)}" target="_blank" rel="noreferrer">Abrir</a>` : '-'}</td>
      <td>${renderLogoCell(item.logoLocal)}</td>
      <td>${renderLogoCell(item.logoVisita)}</td>
      <td><span class="badge ${item.activo ? 'ok' : 'off'}">${item.activo ? 'Activo' : 'Inactivo'}</span></td>
      <td>
        <div class="row">
          <button data-action="edit" data-index="${index}" class="secondary">Editar</button>
          <button data-action="toggle" data-index="${index}" class="${item.activo ? 'toggle-off' : 'toggle-on'}">${item.activo ? 'Desactivar' : 'Activar'}</button>
          <button data-action="delete" data-index="${index}" class="danger">Eliminar</button>
        </div>
      </td>
    `;
    els.tableBody.appendChild(tr);
  });
}

function renderLogoCell(url) {
  const clean = normalizeUrl(url);
  if (!clean) return '-';
  return `<div class="logo-preview"><img src="${escapeAttr(clean)}" alt="logo"><a href="${escapeAttr(clean)}" target="_blank" rel="noreferrer">Ver</a></div>`;
}

function escapeHtml(text) {
  return String(text || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function escapeAttr(text) {
  return escapeHtml(text);
}

function fillForm(item, index) {
  els.formTitle.textContent = 'Editar partido manual';
  els.sourceUrl.value = item.sourceUrl || '';
  els.streamLink.value = item.link || '';
  els.logoLocal.value = item.logoLocal || '';
  els.logoVisita.value = item.logoVisita || '';
  els.activo.checked = !!item.activo;
  els.editIndex.value = String(index);
  els.cancelEditBtn.classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function resetForm() {
  els.formTitle.textContent = 'Agregar partido manual';
  els.manualForm.reset();
  els.activo.checked = true;
  els.editIndex.value = '';
  els.cancelEditBtn.classList.add('hidden');
}

function currentRepoConfig() {
  return {
    owner: els.owner.value.trim(),
    repo: els.repo.value.trim(),
    branch: els.branch.value.trim() || 'main',
    manualPath: els.manualPath.value.trim() || 'data/manual_sofa.json',
    token: els.token.value.trim()
  };
}

async function fetchManualFile() {
  const cfg = currentRepoConfig();
  validateConnection(cfg);
  setStatus('Cargando manual_sofa.json...');

  const url = `https://api.github.com/repos/${encodeURIComponent(cfg.owner)}/${encodeURIComponent(cfg.repo)}/contents/${cfg.manualPath}?ref=${encodeURIComponent(cfg.branch)}`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${cfg.token}`,
      Accept: 'application/vnd.github+json'
    }
  });

  if (res.status === 404) {
    state.items = [];
    state.sha = null;
    render();
    setStatus('manual_sofa.json no existe todavía. Se creará al guardar.');
    return;
  }

  if (!res.ok) {
    throw new Error(`GitHub ${res.status}: ${await res.text()}`);
  }

  const data = await res.json();
  state.sha = data.sha || null;
  const decoded = decodeBase64Content(data.content || '');
  const parsed = JSON.parse(decoded || '{"manual_sofa":[]}');
  state.items = Array.isArray(parsed.manual_sofa) ? parsed.manual_sofa : [];
  render();
  setStatus(`Cargados ${state.items.length} partidos manuales.`);
}

async function saveManualFile() {
  const cfg = currentRepoConfig();
  validateConnection(cfg);
  const body = buildPayload();
  const content = JSON.stringify(body, null, 2) + '\n';
  const url = `https://api.github.com/repos/${encodeURIComponent(cfg.owner)}/${encodeURIComponent(cfg.repo)}/contents/${cfg.manualPath}`;

  const payload = {
    message: 'Actualizar manual_sofa.json desde admin web',
    content: btoa(unescape(encodeURIComponent(content))),
    branch: cfg.branch
  };
  if (state.sha) payload.sha = state.sha;

  setStatus('Guardando en GitHub...');

  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${cfg.token}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    throw new Error(`GitHub ${res.status}: ${await res.text()}`);
  }

  const data = await res.json();
  state.sha = data.content?.sha || data.commit?.sha || state.sha;
  setStatus('manual_sofa.json guardado correctamente.');
}

function decodeBase64Content(content) {
  const normalized = String(content || '').replace(/\n/g, '');
  return decodeURIComponent(escape(atob(normalized)));
}

function validateConnection(cfg) {
  if (!cfg.owner || !cfg.repo || !cfg.branch || !cfg.manualPath || !cfg.token) {
    throw new Error('Completa owner, repo, branch, ruta del manual y token.');
  }
}

els.saveSettingsBtn.addEventListener('click', () => {
  saveSettingsLocal();
  setStatus('Conexión guardada en este navegador.');
});

els.testConnectionBtn.addEventListener('click', async () => {
  try {
    saveSettingsLocal();
    await fetchManualFile();
  } catch (err) {
    setStatus(err.message || String(err), true);
  }
});

els.refreshBtn.addEventListener('click', async () => {
  try {
    await fetchManualFile();
  } catch (err) {
    setStatus(err.message || String(err), true);
  }
});

els.saveRepoBtn.addEventListener('click', async () => {
  try {
    await saveManualFile();
  } catch (err) {
    setStatus(err.message || String(err), true);
  }
});

els.cancelEditBtn.addEventListener('click', () => resetForm());

els.manualForm.addEventListener('submit', (event) => {
  event.preventDefault();
  try {
    const sourceUrl = normalizeUrl(els.sourceUrl.value);
    const sofaId = extractSofaId(sourceUrl);
    if (!sourceUrl || !sofaId) {
      throw new Error('El link de SofaScore debe traer un sofaId válido (#id:123 o /event/123).');
    }

    const item = {
      sofaId,
      sourceUrl,
      link: normalizeUrl(els.streamLink.value),
      logoLocal: normalizeUrl(els.logoLocal.value),
      logoVisita: normalizeUrl(els.logoVisita.value),
      activo: !!els.activo.checked,
      createdAt: new Date().toISOString()
    };

    const editIndex = els.editIndex.value;
    if (editIndex === '') {
      const existingIndex = state.items.findIndex(x => String(x.sofaId) === sofaId);
      if (existingIndex >= 0) {
        state.items[existingIndex] = { ...state.items[existingIndex], ...item };
      } else {
        state.items.unshift(item);
      }
      setStatus('Partido agregado localmente. Falta guardar en GitHub.');
    } else {
      state.items[Number(editIndex)] = { ...state.items[Number(editIndex)], ...item };
      setStatus('Partido editado localmente. Falta guardar en GitHub.');
    }

    render();
    resetForm();
  } catch (err) {
    setStatus(err.message || String(err), true);
  }
});

els.tableBody.addEventListener('click', (event) => {
  const btn = event.target.closest('button');
  if (!btn) return;
  const index = Number(btn.dataset.index);
  const action = btn.dataset.action;
  const item = state.items[index];
  if (!item) return;

  if (action === 'edit') {
    fillForm(item, index);
    return;
  }

  if (action === 'toggle') {
    item.activo = !item.activo;
    render();
    setStatus('Estado cambiado localmente. Falta guardar en GitHub.');
    return;
  }

  if (action === 'delete') {
    if (!confirm('¿Eliminar este partido manual?')) return;
    state.items.splice(index, 1);
    render();
    setStatus('Partido eliminado localmente. Falta guardar en GitHub.');
  }
});
