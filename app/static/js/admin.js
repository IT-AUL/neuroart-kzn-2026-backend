// NeuroArt KZN 2026 Admin & Quest Editor JavaScript

function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button style="background:none;border:none;color:white;cursor:pointer;margin-left:8px;font-size:16px;" onclick="this.parentElement.remove()">&times;</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Modal helper
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

// Global modal close on click outside
window.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});

// Quest Editing & Saving
async function saveQuest(isNew = false) {
  const form = document.getElementById('quest-form');
  if (!form) return;

  const locId = document.getElementById('loc-id').value.trim();
  const order = parseInt(document.getElementById('loc-order').value, 10);
  const priority = document.getElementById('loc-priority').value;
  const title = document.getElementById('loc-title').value.trim();
  const mechanic = document.getElementById('loc-mechanic').value;

  // Mechanic params JSON
  let mechanicParams = {};
  const rawParams = document.getElementById('loc-mechanic-params').value.trim();
  if (rawParams) {
    try {
      mechanicParams = JSON.parse(rawParams);
    } catch (e) {
      showToast('Ошибка в JSON параметров механики: ' + e.message, 'error');
      return;
    }
  }

  // Marker
  const markerType = document.getElementById('loc-marker-type').value || 'image';
  const markerAsset = document.getElementById('loc-marker-asset').value.trim() || 'marker_default.png';

  // 3D Model & Coordinates
  const modelUrl = document.getElementById('loc-model-url').value.trim();
  const coordX = parseFloat(document.getElementById('loc-coord-x').value) || 0.0;
  const coordY = parseFloat(document.getElementById('loc-coord-y').value) || 0.0;
  const coordZ = parseFloat(document.getElementById('loc-coord-z').value) || 0.0;
  const coordScale = parseFloat(document.getElementById('loc-coord-scale').value) || 1.0;

  // Models JSON
  let models = [];
  const rawModels = document.getElementById('loc-models-json').value.trim();
  if (rawModels) {
    try {
      models = JSON.parse(rawModels);
    } catch (e) {
      showToast('Ошибка в JSON подмоделей: ' + e.message, 'error');
      return;
    }
  }

  // Animations JSON
  let animations = [];
  const rawAnimations = document.getElementById('loc-animations-json').value.trim();
  if (rawAnimations) {
    try {
      animations = JSON.parse(rawAnimations);
    } catch (e) {
      showToast('Ошибка в JSON анимаций: ' + e.message, 'error');
      return;
    }
  }

  // Texts
  const layer1 = document.getElementById('loc-text-layer1').value.trim();
  const layer2 = document.getElementById('loc-text-layer2').value.trim();
  const actionHint = document.getElementById('loc-text-action-hint').value.trim() || null;
  const easterEgg = document.getElementById('loc-text-easter-egg').value.trim() || null;

  // Artifact
  const artifactId = document.getElementById('loc-artifact-id').value.trim() || `art_${locId}`;
  const artifactName = document.getElementById('loc-artifact-name').value.trim() || title;
  const artifactIcon = document.getElementById('loc-artifact-icon').value.trim() || 'icons/default.png';

  // Next location
  const nextLocId = document.getElementById('loc-next-id').value.trim() || null;
  const nextLocOrderVal = document.getElementById('loc-next-order').value.trim();
  const nextLocOrder = nextLocOrderVal ? parseInt(nextLocOrderVal, 10) : null;
  const nextLocHint = document.getElementById('loc-next-hint').value.trim() || null;

  const payload = {
    id: locId,
    order: order,
    priority: priority,
    title: title,
    mechanic: mechanic,
    mechanic_params: mechanicParams,
    marker: {
      type: markerType,
      asset: markerAsset,
    },
    model_url: modelUrl,
    models: models,
    coordinates: {
      x: coordX,
      y: coordY,
      z: coordZ,
      scale: coordScale,
    },
    animations: animations,
    texts: {
      layer1: layer1,
      layer2: layer2,
      action_hint: actionHint,
      easter_egg: easterEgg,
    },
    artifact: {
      id: artifactId,
      name: artifactName,
      icon: artifactIcon,
    },
    next_location_id: nextLocId,
    next_location_order: nextLocOrder,
    next_location_hint: nextLocHint,
  };

  const saveBtn = document.getElementById('btn-save-quest');
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerText = 'Сохранение...';
  }

  try {
    const url = isNew ? '/locations' : `/locations/${encodeURIComponent(locId)}`;
    const method = isNew ? 'POST' : 'PUT';

    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Ошибка сервера (${res.status})`);
    }

    showToast(isNew ? 'Квест успешно создан!' : 'Изменения сохранены!', 'success');

    if (isNew) {
      setTimeout(() => {
        window.location.href = `/admin/quests/${encodeURIComponent(locId)}/edit`;
      }, 700);
    }
  } catch (err) {
    showToast('Ошибка сохранения: ' + err.message, 'error');
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerText = isNew ? 'Создать точку' : 'Сохранить изменения';
    }
  }
}

// Delete Quest
let pendingDeleteId = null;

function promptDeleteQuest(id, title) {
  pendingDeleteId = id;
  const nameSpan = document.getElementById('delete-loc-title');
  if (nameSpan) nameSpan.innerText = title;
  openModal('modal-delete-confirm');
}

async function confirmDeleteQuest() {
  if (!pendingDeleteId) return;

  try {
    const res = await fetch(`/locations/${encodeURIComponent(pendingDeleteId)}`, {
      method: 'DELETE',
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Ошибка (${res.status})`);
    }

    showToast('Точка маршрута удалена', 'success');
    closeModal('modal-delete-confirm');

    // If on edit page, go back to list; otherwise remove row from table
    if (window.location.pathname.includes('/edit')) {
      setTimeout(() => { window.location.href = '/admin/quests'; }, 500);
    } else {
      const row = document.getElementById(`row-${pendingDeleteId}`);
      if (row) row.remove();
    }
  } catch (err) {
    showToast('Ошибка удаления: ' + err.message, 'error');
  }
}

// AI HITL Lore Generator
async function generateAiLore() {
  const title = document.getElementById('loc-title').value.trim();
  const theme = document.getElementById('ai-theme-input').value.trim();
  const count = parseInt(document.getElementById('ai-variants-count').value, 10) || 2;

  if (!title) {
    showToast('Сначала укажите название точки в форме', 'error');
    return;
  }

  const btn = document.getElementById('btn-generate-ai');
  const list = document.getElementById('ai-variants-list');
  btn.disabled = true;
  btn.innerText = '✨ Генерирую варианты (YandexGPT)...';
  list.innerHTML = '<p style="color:var(--text-muted);font-style:italic;">Запрос к нейросети...</p>';

  try {
    const res = await fetch('/locations/editor/generate-content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title,
        context_or_theme: theme || null,
        variant_count: count,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Не удалось сгенерировать контент');
    }

    const data = await res.json();
    list.innerHTML = '';

    const variants = data.options || data.variants || [];

    if (variants.length === 0) {
      list.innerHTML = '<p style="color:var(--text-muted);padding:0.5rem;">Варианты не найдены</p>';
      return;
    }

    variants.forEach((v, index) => {
      const card = document.createElement('div');
      card.className = 'ai-variant-card';
      const artifactText = v.artifact_suggestion
        ? (typeof v.artifact_suggestion === 'object' ? (v.artifact_suggestion.name || v.artifact_suggestion.id || JSON.stringify(v.artifact_suggestion)) : v.artifact_suggestion)
        : '';

      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
          <h5>Вариант #${index + 1} (${v.variant_id || 'AI'})</h5>
          <button type="button" class="btn btn-sm btn-primary" onclick="applyAiVariant(${index})">
            Вставить в форму
          </button>
        </div>
        <p><strong>Карточка (Layer 1):</strong> ${escapeHtml(v.layer1)}</p>
        <p style="margin-top:0.35rem;"><strong>Лор (Layer 2):</strong> ${escapeHtml(v.layer2)}</p>
        <p style="margin-top:0.35rem;"><strong>AR-подсказка:</strong> ${escapeHtml(v.action_hint || '—')}</p>
        ${v.easter_egg ? `<p style="margin-top:0.35rem;"><strong>Пасхалка:</strong> ${escapeHtml(v.easter_egg)}</p>` : ''}
        ${artifactText ? `<p style="margin-top:0.35rem;"><strong>Сувенир:</strong> ${escapeHtml(artifactText)}</p>` : ''}
      `;
      list.appendChild(card);
    });

    window._aiVariants = variants;
    showToast('Сгенерировано вариантов: ' + variants.length, 'success');
  } catch (err) {
    list.innerHTML = `<p style="color:var(--danger)">Ошибка: ${escapeHtml(err.message)}</p>`;
    showToast('Ошибка генерации: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerText = '✨ Сгенерировать варианты';
  }
}

function applyAiVariant(index) {
  if (!window._aiVariants || !window._aiVariants[index]) return;
  const v = window._aiVariants[index];

  if (v.layer1) document.getElementById('loc-text-layer1').value = v.layer1;
  if (v.layer2) document.getElementById('loc-text-layer2').value = v.layer2;
  if (v.action_hint) document.getElementById('loc-text-action-hint').value = v.action_hint;
  if (v.easter_egg) document.getElementById('loc-text-easter-egg').value = v.easter_egg;
  if (v.artifact_suggestion) {
    const artNameInput = document.getElementById('loc-artifact-name');
    const artIdInput = document.getElementById('loc-artifact-id');
    const artIconInput = document.getElementById('loc-artifact-icon');

    if (typeof v.artifact_suggestion === 'object') {
      if (artNameInput && v.artifact_suggestion.name) artNameInput.value = v.artifact_suggestion.name;
      if (artIdInput && v.artifact_suggestion.id && !artIdInput.value) artIdInput.value = v.artifact_suggestion.id;
      if (artIconInput && v.artifact_suggestion.icon) artIconInput.value = v.artifact_suggestion.icon;
    } else if (artNameInput) {
      artNameInput.value = v.artifact_suggestion;
    }
  }

  showToast(`Вариант #${index + 1} подставлен в поля формы!`, 'success');
}

// POI Review Actions
async function reviewPoi(poiId, status) {
  try {
    const res = await fetch(`/poi/admin/${encodeURIComponent(poiId)}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status }),
    });

    if (!res.ok) throw new Error('Не удалось обновить статус POI');

    showToast(`Статус POI изменен на "${status}"`, 'success');
    const row = document.getElementById(`poi-row-${poiId}`);
    if (row) {
      row.style.opacity = '0.5';
      setTimeout(() => row.remove(), 400);
    }
  } catch (err) {
    showToast('Ошибка: ' + err.message, 'error');
  }
}

// Convert POI to Quest
let pendingConvertPoi = null;

function promptConvertPoi(poiId, poiName, defaultCategory) {
  pendingConvertPoi = { id: poiId, name: poiName, category: defaultCategory };
  document.getElementById('convert-poi-name').innerText = poiName;
  document.getElementById('convert-poi-title').value = poiName;
  openModal('modal-convert-poi');
}

async function confirmConvertPoi() {
  if (!pendingConvertPoi) return;

  const order = parseInt(document.getElementById('convert-poi-order').value, 10) || 10;
  const priority = document.getElementById('convert-poi-priority').value;
  const mechanic = document.getElementById('convert-poi-mechanic').value;
  const customTitle = document.getElementById('convert-poi-title').value.trim();

  const payload = {
    poi_id: pendingConvertPoi.id,
    order: order,
    priority: priority,
    mechanic: mechanic,
    custom_title: customTitle || null,
  };

  try {
    const res = await fetch('/locations/from-poi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Не удалось создать квест из POI');
    }

    const created = await res.json();
    showToast('Квест успешно создан из POI!', 'success');
    closeModal('modal-convert-poi');

    setTimeout(() => {
      window.location.href = `/admin/quests/${encodeURIComponent(created.id)}/edit`;
    }, 600);
  } catch (err) {
    showToast('Ошибка создания квеста: ' + err.message, 'error');
  }
}

// OSM Overpass Sync Trigger
async function triggerOsmSync() {
  const btn = document.getElementById('btn-trigger-sync');
  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Синхронизация с OSM...';
  }

  try {
    const res = await fetch('/poi/sync/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ area_name: 'Kazan', force_remote: true }),
    });

    if (!res.ok) throw new Error('Ошибка запуска синхронизации');

    const result = await res.json();
    showToast(`Синхронизация завершена: добавлено ${result.created || 0}, обновлено ${result.updated || 0}`, 'success');
    setTimeout(() => { window.location.reload(); }, 1200);
  } catch (err) {
    showToast('Ошибка: ' + err.message, 'error');
    if (btn) {
      btn.disabled = false;
      btn.innerText = 'Запустить синхронизацию OSM';
    }
  }
}

function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  if (typeof text === 'object') {
    try {
      text = text.text || text.description || text.name || JSON.stringify(text);
    } catch {
      text = String(text);
    }
  } else {
    text = String(text);
  }
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Asset Upload & S3 File Picker
async function uploadAssetFile(inputElem, prefix, targetInputId, previewImgId) {
  if (!inputElem.files || !inputElem.files[0]) return;
  const file = inputElem.files[0];

  const formData = new FormData();
  formData.append('file', file);
  formData.append('key_prefix', prefix);

  showToast(`Загрузка "${file.name}" в S3...`, 'info', 6000);

  try {
    const res = await fetch('/storage/upload', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Ошибка сервера (${res.status})`);
    }

    const data = await res.json();
    const targetInput = document.getElementById(targetInputId);
    if (targetInput) {
      targetInput.value = data.key;
    }

    if (previewImgId) {
      updateAssetPreview(previewImgId, data.key);
    }

    showToast(`Файл успешно загружен в S3: ${data.key}`, 'success');
  } catch (err) {
    showToast('Ошибка загрузки в S3: ' + err.message, 'error');
  } finally {
    inputElem.value = '';
  }
}

function updateAssetPreview(imgId, assetKey) {
  const img = document.getElementById(imgId);
  if (!img) return;

  if (!assetKey) {
    img.style.display = 'none';
    return;
  }

  // If already a full URL
  if (assetKey.startsWith('http://') || assetKey.startsWith('https://')) {
    img.src = assetKey;
  } else {
    img.src = `/storage/asset/${assetKey.replace(/^\//, '')}`;
  }
  img.style.display = 'block';
}

window._s3PickerTarget = null;

async function openS3Browser(prefix, targetInputId, previewImgId) {
  window._s3PickerTarget = { targetInputId, previewImgId };
  const modal = document.getElementById('modal-s3-picker');
  const titleElem = document.getElementById('s3-picker-title');
  const listElem = document.getElementById('s3-picker-file-list');

  if (titleElem) titleElem.innerText = `Файлы в S3 (${prefix ? 'папка ' + prefix : 'все файлы'})`;
  if (listElem) listElem.innerHTML = '<p style="padding:1rem;color:var(--text-muted);">Загрузка файлов из S3...</p>';

  openModal('modal-s3-picker');

  try {
    const res = await fetch(`/storage/files?prefix=${encodeURIComponent(prefix || '')}`);
    if (!res.ok) throw new Error('Не удалось получить список файлов');

    const files = await res.json();
    if (!files || files.length === 0) {
      listElem.innerHTML = '<p style="padding:1.5rem;text-align:center;color:var(--text-muted);">Файлы в этой категории еще не загружены</p>';
      return;
    }

    listElem.innerHTML = '';
    files.forEach(f => {
      const item = document.createElement('div');
      item.className = 's3-file-item';
      const sizeKb = f.size ? Math.round(f.size / 1024) + ' KB' : '';
      item.innerHTML = `
        <div style="display:flex;align-items:center;gap:0.5rem;overflow:hidden;">
          <span style="font-size:1.1rem;">📄</span>
          <div style="overflow:hidden;">
            <div style="font-weight:600;font-size:0.85rem;text-overflow:ellipsis;overflow:hidden;white-space:nowrap;">${escapeHtml(f.key)}</div>
            <div style="font-size:0.7rem;color:var(--text-muted);">${sizeKb} ${f.last_modified ? '&bull; ' + f.last_modified.slice(0, 10) : ''}</div>
          </div>
        </div>
        <button type="button" class="btn btn-sm btn-primary" onclick="selectS3File('${escapeHtml(f.key)}')">Выбрать</button>
      `;
      listElem.appendChild(item);
    });
  } catch (err) {
    listElem.innerHTML = `<p style="padding:1rem;color:var(--danger)">Ошибка: ${escapeHtml(err.message)}</p>`;
  }
}

function selectS3File(key) {
  if (!window._s3PickerTarget) return;
  const { targetInputId, previewImgId } = window._s3PickerTarget;

  const input = document.getElementById(targetInputId);
  if (input) input.value = key;

  if (previewImgId) {
    updateAssetPreview(previewImgId, key);
  }

  closeModal('modal-s3-picker');
  showToast(`Выбран файл: ${key}`, 'success');
}

function selectPresetIcon(iconKey, iconName) {
  const iconInput = document.getElementById('loc-artifact-icon');
  const nameInput = document.getElementById('loc-artifact-name');

  if (iconInput) iconInput.value = iconKey;
  if (nameInput && (!nameInput.value || nameInput.value.startsWith('Сувенир'))) {
    nameInput.value = iconName;
  }

  updateAssetPreview('artifact-icon-preview', iconKey);
  showToast(`Выбран сувенир: ${iconName}`, 'success');
}

