let allUsers = [];
let loadedBatches = [];
let activeBatchId = null;
let allDocuments = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.isAuthenticated()) return;
  const user = Auth.getUser();

  const canManageMembers = user.role === 'ADMIN' || user.role === 'LEADER';

  if (canManageMembers) {
    loadAllUsers();
  }

  if (user.role !== 'ADMIN') {
    document.getElementById('onboarding-actions').style.display = 'none';
  }

  await loadDocumentsList();
  loadBatches();

  document.getElementById('create-batch-form').addEventListener('submit', handleCreateBatch);
  document.getElementById('add-member-form').addEventListener('submit', handleAddMemberSubmit);
});

async function loadAllUsers() {
  try {
    allUsers = await ApiClient.get('/users');
  } catch (err) {
    console.error('Failed to load users:', err);
  }
}

async function loadDocumentsList() {
  try {
    allDocuments = await ApiClient.get('/documents');
  } catch (err) {
    console.error('Failed to load documents list:', err);
  }
}

async function loadBatches() {
  try {
    loadedBatches = await ApiClient.get('/onboardings');
    const pillsContainer = document.getElementById('onboarding-nav-pills');
    const detailContainer = document.getElementById('selected-batch-detail');

    if (!loadedBatches || loadedBatches.length === 0) {
      pillsContainer.innerHTML = '<div style="color:var(--text-muted); font-size:13px;">No assigned onboarding groups found.</div>';
      detailContainer.innerHTML = '<div class="card-section"><p style="color:var(--text-muted);">No onboarding batches found.</p></div>';
      return;
    }

    // Check URL parameter for batch_id
    const urlParams = new URLSearchParams(window.location.search);
    const paramBatchId = urlParams.get('batch_id');

    let defaultBatch = loadedBatches[0];
    if (paramBatchId) {
      const found = loadedBatches.find(x => x.id === paramBatchId);
      if (found) defaultBatch = found;
    }

    // Render Nav Pills Bar
    pillsContainer.innerHTML = loadedBatches.map(b => `
      <div class="onboarding-pill ${b.id === defaultBatch.id ? 'active' : ''}" id="pill-${b.id}" onclick="selectOnboardingGroup('${b.id}')">
        <span>📂</span>
        <span>${b.name}</span>
        <span class="badge badge-${b.status.toLowerCase()}" style="font-size:10px; padding:2px 6px;">${b.status}</span>
      </div>
    `).join('');

    activeBatchId = defaultBatch.id;
    renderSelectedGroupDetail(activeBatchId);

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function selectOnboardingGroup(batchId) {
  activeBatchId = batchId;
  
  // Update URL without full page reload
  const newUrl = `${window.location.pathname}?batch_id=${batchId}`;
  window.history.pushState({ path: newUrl }, '', newUrl);

  // Update active pill UI
  document.querySelectorAll('.onboarding-pill').forEach(pill => {
    pill.classList.remove('active');
  });
  const activePill = document.getElementById(`pill-${batchId}`);
  if (activePill) activePill.classList.add('active');

  // Update active sidebar subitem UI
  document.querySelectorAll('.nav-subitem').forEach(subitem => {
    subitem.classList.remove('active');
    if (subitem.getAttribute('href') === `/onboarding.html?batch_id=${batchId}`) {
      subitem.classList.add('active');
    }
  });

  renderSelectedGroupDetail(batchId);
}

function renderSelectedGroupDetail(batchId) {
  const container = document.getElementById('selected-batch-detail');
  const b = loadedBatches.find(x => x.id === batchId);

  if (!b) {
    container.innerHTML = '<div class="card-section"><p style="color:var(--text-muted);">Batch not found.</p></div>';
    return;
  }

  const user = Auth.getUser();
  const canManageMembers = user.role === 'ADMIN' || user.role === 'LEADER';
  const token = Auth.getToken();

  // Filter documents assigned to this onboarding group or general
  const groupDocs = allDocuments.filter(d => d.onboarding_id === b.id || (!d.onboarding_id && allDocuments.length > 0));

  container.innerHTML = `
    <div class="card-section" style="border-top: 3px solid var(--primary);">
      <!-- Group Header Banner -->
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="display:flex; align-items:center; gap:10px;">
            <h2 style="font-size:20px; font-weight:700; color:var(--text-primary); margin:0;">${b.name}</h2>
            <span class="badge badge-${b.status.toLowerCase()}">${b.status}</span>
          </div>
          <p style="color:var(--text-secondary); margin-top:6px; font-size:14px;">${b.description || 'No description provided.'}</p>
        </div>
        <div style="text-align:right;">
          <div style="font-size:13px; color:var(--text-muted); font-weight:600;">Program Duration:</div>
          <div style="font-size:13px; color:var(--primary); font-weight:700; margin-top:2px;">📅 ${b.start_date} → ${b.end_date}</div>
        </div>
      </div>

      <!-- Quick Group Actions -->
      <div style="display:flex; gap:12px; margin-bottom:24px; background:var(--bg-primary); padding:12px; border-radius:8px; border:1px solid var(--border-color); flex-wrap:wrap;">
        <a href="/learning.html?onboarding_id=${b.id}" class="btn btn-sm btn-primary" style="display:flex; align-items:center; gap:6px;">
          🎯 View Group Learning Roadmap & Progress
        </a>
      </div>

      <!-- Group Training Documents Section -->
      <div style="margin-bottom:28px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; padding-bottom:6px; border-bottom:1px solid var(--border-color);">
          <h4 style="font-size:14px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.5px;">
            📚 Group Training Documents & Materials (${groupDocs.length})
          </h4>
        </div>
        ${groupDocs.length === 0 ? `
          <p style="color:var(--text-muted); font-size:13px;">No training documents assigned to this group yet.</p>
        ` : `
          <div class="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Document Name</th>
                  <th>Format</th>
                  <th>Size</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${groupDocs.map(d => `
                  <tr>
                    <td><strong>📄 ${d.filename}</strong></td>
                    <td><span class="badge" style="background-color:rgba(255,255,255,0.05); color:var(--text-secondary);">${d.file_type.toUpperCase()}</span></td>
                    <td>${formatSize(d.file_size)}</td>
                    <td>${getProcessingBadgeHTML(d)}</td>
                    <td>
                      <a href="/api/documents/${d.id}/download?token=${encodeURIComponent(token)}" target="_blank" class="btn btn-sm btn-secondary">⬇️ Download</a>
                      <a href="/learning.html?onboarding_id=${b.id}" class="btn btn-sm btn-primary" style="margin-left:6px;">🎯 Roadmap</a>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `}
      </div>

      <!-- Members Section -->
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
        <!-- Leaders Column -->
        <div>
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; padding-bottom:6px; border-bottom:1px solid var(--border-color);">
            <h4 style="font-size:13px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin:0;">
              👨‍🏫 TechLeads / Mentors (${b.leaders.length})
            </h4>
            ${canManageMembers ? `<button class="btn btn-sm btn-primary" onclick="openAddMemberModal('${b.id}', 'leader')" style="font-weight:700; font-size:12px; padding:4px 10px;">➕ Add Leader</button>` : ''}
          </div>
          <div>
            ${b.leaders.map(l => `
              <div class="member-item">
                <div>
                  <strong style="color:var(--text-primary);">${l.full_name}</strong>
                  <div style="font-size:11px; color:var(--text-muted);">${l.email || ''}</div>
                </div>
                ${canManageMembers ? `<button class="btn-remove-member" onclick="removeMember('${b.id}', 'leader', '${l.id}', '${l.full_name}')" title="Remove leader">&times;</button>` : ''}
              </div>
            `).join('') || '<p style="color:var(--text-muted); font-size:13px;">No TechLeads assigned to this group yet.</p>'}
          </div>
        </div>

        <!-- Interns Column -->
        <div>
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; padding-bottom:6px; border-bottom:1px solid var(--border-color);">
            <h4 style="font-size:13px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin:0;">
              👨‍🎓 Interns / Students (${b.interns.length})
            </h4>
            ${canManageMembers ? `<button class="btn btn-sm btn-primary" onclick="openAddMemberModal('${b.id}', 'intern')" style="font-weight:700; font-size:12px; padding:4px 10px;">➕ Add Intern</button>` : ''}
          </div>
          <div>
            ${b.interns.map(i => `
              <div class="member-item">
                <div>
                  <strong style="color:var(--text-primary);">${i.full_name}</strong>
                  <div style="font-size:11px; color:var(--text-muted);">${i.email || ''}</div>
                </div>
                ${canManageMembers ? `<button class="btn-remove-member" onclick="removeMember('${b.id}', 'intern', '${i.id}', '${i.full_name}')" title="Remove intern">&times;</button>` : ''}
              </div>
            `).join('') || '<p style="color:var(--text-muted); font-size:13px;">No interns assigned to this group yet.</p>'}
          </div>
        </div>
      </div>
    </div>
  `;
}

function formatSize(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function getProcessingBadgeHTML(doc) {
  if (doc.processing_status === 'COMPLETED') {
    return '<span class="badge badge-completed">COMPLETED</span>';
  }
  if (doc.processing_status === 'FAILED') {
    return '<span class="badge badge-rejected">FAILED</span>';
  }

  let elapsedSec = 0;
  if (doc.created_at) {
    const createdTime = new Date(doc.created_at).getTime();
    elapsedSec = (Date.now() - createdTime) / 1000;
  }

  if (elapsedSec <= 3) {
    return '<span class="badge badge-pending"><span class="spinner-pulse"></span> ⚡ Loading...</span>';
  } else {
    return '<span class="badge badge-pending" style="background-color:rgba(168,85,247,0.2); color:var(--accent-purple); border:1px solid rgba(168,85,247,0.4);"><span class="spinner-pulse"></span> 🧠 Thinking...</span>';
  }
}

function getBadgeStatusClass(status) {
  switch (status) {
    case 'COMPLETED': return 'completed';
    case 'PROCESSING': return 'pending';
    case 'FAILED': return 'rejected';
    default: return 'draft';
  }
}

async function handleCreateBatch(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById('batch-name').value,
    description: document.getElementById('batch-desc').value,
    start_date: document.getElementById('batch-start').value,
    end_date: document.getElementById('batch-end').value,
    status: document.getElementById('batch-status').value,
  };

  try {
    await ApiClient.post('/onboardings', data);
    showToast('Onboarding batch created');
    closeModal('create-batch-modal');
    document.getElementById('create-batch-form').reset();
    loadBatches();
    renderSidebar(); // Refresh sidebar menu
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openAddMemberModal(batchId, type) {
  document.getElementById('member-batch-id').value = batchId;
  document.getElementById('member-type').value = type;

  const isLeader = type === 'leader';
  document.getElementById('add-member-title').innerText = isLeader ? 'Add Leader to Batch' : 'Add Intern to Batch';
  document.getElementById('member-select-label').innerText = isLeader ? 'Select Leader Account' : 'Select Intern Account';

  const filteredUsers = allUsers.filter(u => u.role === (isLeader ? 'LEADER' : 'INTERN') && u.is_active);
  const select = document.getElementById('member-user-id');

  if (filteredUsers.length === 0) {
    select.innerHTML = `<option value="">No available ${isLeader ? 'Leader' : 'Intern'} accounts found</option>`;
  } else {
    select.innerHTML = `<option value="">-- Choose ${isLeader ? 'Leader' : 'Intern'} --</option>` +
      filteredUsers.map(u => `<option value="${u.id}">${u.full_name} (${u.email})</option>`).join('');
  }

  openModal('add-member-modal');
}

async function handleAddMemberSubmit(e) {
  e.preventDefault();
  const batchId = document.getElementById('member-batch-id').value;
  const type = document.getElementById('member-type').value;
  const userId = document.getElementById('member-user-id').value;

  if (!userId) {
    showToast('Please select a user!', 'error');
    return;
  }

  try {
    const endpoint = `/onboardings/${batchId}/${type === 'leader' ? 'leaders' : 'interns'}`;
    await ApiClient.post(endpoint, { user_id: userId });
    showToast(`${type === 'leader' ? 'Leader' : 'Intern'} added to batch`);
    closeModal('add-member-modal');
    loadBatches();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function removeMember(batchId, type, userId, userName) {
  const roleName = type === 'leader' ? 'Leader' : 'Intern';
  if (!confirm(`Are you sure you want to remove ${roleName} "${userName}" from this onboarding batch?`)) return;

  try {
    const endpoint = `/onboardings/${batchId}/${type === 'leader' ? 'leaders' : 'interns'}/${userId}`;
    await ApiClient.delete(endpoint);
    showToast(`${roleName} removed from batch`);
    loadBatches();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
