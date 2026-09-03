let batchesMap = {};
let pollingInterval = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.isAuthenticated()) return;
  const user = Auth.getUser();

  const canManageDocs = user.role === 'ADMIN' || user.role === 'LEADER';

  if (!canManageDocs) {
    document.getElementById('document-actions').style.display = 'none';
  }

  await loadOnboardingBatches();
  loadDocuments();

  document.getElementById('upload-doc-form').addEventListener('submit', handleUploadDocument);
});

async function loadOnboardingBatches() {
  try {
    const batches = await ApiClient.get('/onboardings');
    const select = document.getElementById('doc-onboarding');
    select.innerHTML = '<option value="">-- General / All Batches --</option>' + 
      batches.map(b => `<option value="${b.id}">${b.name} (${b.status})</option>`).join('');

    batches.forEach(b => {
      batchesMap[b.id] = b.name;
    });
  } catch (err) {
    console.error('Failed to load onboardings:', err);
  }
}

async function loadDocuments() {
  try {
    const docs = await ApiClient.get('/documents');
    const tbody = document.getElementById('documents-table-body');
    const user = Auth.getUser();
    const token = Auth.getToken();

    if (docs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No training documents uploaded yet.</td></tr>';
      stopPolling();
      return;
    }

    let hasProcessing = false;

    tbody.innerHTML = docs.map(d => {
      if (d.processing_status === 'PROCESSING' || d.processing_status === 'UPLOADED') {
        hasProcessing = true;
      }

      // Deletion permission: ADMIN can delete any doc; LEADER can ONLY delete docs uploaded by themselves!
      const canDeleteThisDoc = user.role === 'ADMIN' || (user.role === 'LEADER' && d.uploaded_by === user.id);

      return `
        <tr>
          <td><strong>${d.filename}</strong></td>
          <td><span class="badge badge-active">${batchesMap[d.onboarding_id] || d.onboarding_name || 'General'}</span></td>
          <td><span class="badge" style="background-color:rgba(255,255,255,0.05); color:var(--text-secondary);">${d.file_type.toUpperCase()}</span></td>
          <td>${formatSize(d.file_size)}</td>
          <td>${getProcessingBadgeHTML(d)}</td>
          <td>${d.uploader_name}</td>
          <td>
            <a href="/api/documents/${d.id}/download?token=${encodeURIComponent(token)}" target="_blank" class="btn btn-sm btn-secondary">Download</a>
            <a href="/learning.html?onboarding_id=${d.onboarding_id || ''}" class="btn btn-sm btn-primary" style="margin-left:6px;">View Roadmap</a>
            ${canDeleteThisDoc ? `<button class="btn btn-sm btn-danger" onclick="deleteDocument('${d.id}', '${d.filename}')" style="margin-left:6px;">Delete</button>` : ''}
          </td>
        </tr>
      `;
    }).join('');

    // Manage auto polling status
    if (hasProcessing) {
      startPolling();
    } else {
      stopPolling();
    }

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function getProcessingBadgeHTML(doc) {
  if (doc.processing_status === 'COMPLETED') {
    return '<span class="badge badge-completed">COMPLETED</span>';
  }
  if (doc.processing_status === 'FAILED') {
    return '<span class="badge badge-rejected">FAILED</span>';
  }

  // Calculate elapsed seconds since doc created
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

function startPolling() {
  if (pollingInterval) return;
  console.log('[Documents] Auto polling document processing status...');
  pollingInterval = setInterval(() => {
    loadDocuments();
  }, 2000);
}

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
    console.log('[Documents] Polling stopped - all documents processed.');
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

async function handleUploadDocument(e) {
  e.preventDefault();
  const fileInput = document.getElementById('doc-file');
  const batchId = document.getElementById('doc-onboarding').value;
  const submitBtn = e.target.querySelector('button[type="submit"]');

  if (!fileInput.files[0]) return;

  const originalBtnContent = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> ⚡ Loading document...';
  fileInput.disabled = true;

  // After 3 seconds, switch button text to '🧠 Thinking with Gemini 3.6 Flash...'
  const thinkingTimer = setTimeout(() => {
    if (submitBtn.disabled) {
      submitBtn.innerHTML = '<span class="spinner"></span> 🧠 Thinking with Gemini 3.6 Flash...';
    }
  }, 3000);

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  if (batchId) {
    formData.append('onboarding_id', batchId);
  }

  try {
    showToast('Uploading document to Cloudinary...', 'success');
    await ApiClient.post('/documents/upload', formData);
    showToast('Document uploaded! Gemini 3.6 Flash is thinking and building the roadmap...');
    closeModal('upload-doc-modal');
    document.getElementById('upload-doc-form').reset();
    loadDocuments();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    clearTimeout(thinkingTimer);
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnContent;
    fileInput.disabled = false;
  }
}

async function deleteDocument(docId, filename) {
  if (!confirm(`Are you sure you want to delete "${filename}"?\nThis will also remove all associated learning roadmap topics.`)) return;

  try {
    await ApiClient.delete(`/documents/${docId}`);
    showToast('Document and associated roadmap topics deleted successfully');
    loadDocuments();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
