document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.isAuthenticated()) return;
  loadDashboardData();
});

async function loadDashboardData() {
  try {
    const data = await ApiClient.get('/dashboard');
    renderDashboard(data);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteInternSchedule(scheduleId, subjectName) {
  if (!confirm(`Are you sure you want to delete the schedule "${subjectName}"?`)) return;

  try {
    await ApiClient.delete(`/schedules/${scheduleId}`);
    showToast('Schedule deleted successfully');
    loadDashboardData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderDashboard(data) {
  const statsGrid = document.getElementById('stats-grid');
  const sections = document.getElementById('dashboard-sections');

  if (data.role === 'INTERN') {
    statsGrid.innerHTML = `
      <div class="stat-card">
        <div>
          <div class="stat-label">Today's Schedule</div>
          <div class="stat-value">${data.today_schedule.length}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-label">Pending Leave Requests</div>
          <div class="stat-value">${data.pending_leaves}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-label">Assigned Batches</div>
          <div class="stat-value">${data.onboarding_batches.length}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-label">Overall Learning Progress</div>
          <div class="stat-value" style="color:var(--primary);">${data.learning_progress.percentage}%</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
      </div>
    `;

    const formatDaysText = (days) => {
      const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      if (!days || days.length === 0) return '';
      return days.map(d => dayNames[d]).join(', ');
    };

    sections.innerHTML = `
      <div class="card-section" style="border-top:3px solid var(--primary);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
          <div class="card-title" style="margin:0;">My Class & University Schedule</div>
          <a href="/schedule.html" class="btn btn-sm btn-primary">+ Add / Register Schedule</a>
        </div>
        ${data.upcoming_schedules.length === 0 ? `
          <p style="color:var(--text-muted); font-size:13px;">No university schedule registered yet. Click button above to register your busy hours!</p>
        ` : `
          <div class="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Subject / Class</th>
                  <th>Schedule Type</th>
                  <th>Day(s)</th>
                  <th>Time</th>
                  <th>Date Range</th>
                  <th>Location</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${data.upcoming_schedules.map(s => `
                  <tr>
                    <td><strong>${s.subject}</strong></td>
                    <td>
                      <span class="badge" style="background:${s.is_recurring ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.05)'}; color:${s.is_recurring ? 'var(--primary)' : 'var(--text-secondary)'}; font-size:11px;">
                        ${s.is_recurring ? '🔁 Weekly Class' : '📅 One-time Date Range'}
                      </span>
                    </td>
                    <td><strong style="color:var(--primary);">${formatDaysText(s.days_of_week)}</strong></td>
                    <td>${s.start_time} - ${s.end_time}</td>
                    <td><span style="font-size:12px; color:var(--text-muted);">${s.start_date} → ${s.end_date}</span></td>
                    <td>${s.location || 'N/A'}</td>
                    <td>
                      <button class="btn btn-sm btn-danger" onclick="deleteInternSchedule('${s.id}', '${s.subject.replace(/'/g, "\\'")}')">🗑 Xóa</button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `}
      </div>

      <div class="card-section" style="margin-top:20px;">
        <div class="card-title">Learning Progress Overview</div>
        <div class="progress-bar-container" style="margin-top: 12px; height: 12px; background: var(--bg-primary); border-radius: 6px; overflow: hidden; border: 1px solid var(--border-color);">
          <div class="progress-bar-fill" style="width: ${data.learning_progress.percentage}%; height: 100%; background: var(--primary); transition: width 0.5s ease;"></div>
        </div>
        <p style="color: var(--text-secondary); font-size: 13px; margin-top: 8px;">
          Overall learning progress: <strong>${data.learning_progress.percentage}%</strong> (${data.learning_progress.completed} of ${data.learning_progress.total} topics fully completed)
        </p>
      </div>
    `;
  } else if (data.role === 'LEADER') {
    statsGrid.innerHTML = `
      <div class="stat-card">
        <div>
          <div class="stat-label">Assigned Interns</div>
          <div class="stat-value">${data.intern_count}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-label">Pending Leave Requests</div>
          <div class="stat-value">${data.pending_leaves}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-label">Active Batches</div>
          <div class="stat-value">${data.onboarding_batches.length}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/></svg>
        </div>
      </div>
    `;

    sections.innerHTML = `
      <div class="card-section">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
          <div class="card-title" style="margin:0;">My Onboarding Batches & Members</div>
          <a href="/onboarding.html" class="btn btn-sm btn-primary">+ Manage Groups & Add Members</a>
        </div>
        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Batch Name</th>
                <th>Status</th>
                <th>TechLeads</th>
                <th>Assigned Interns</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${data.onboarding_batches.map(b => `
                <tr>
                  <td><strong>🎯 ${b.name}</strong></td>
                  <td><span class="badge badge-${b.status.toLowerCase()}">${b.status}</span></td>
                  <td><span class="badge badge-active" style="padding:4px 10px;">👨‍🎓 ${b.intern_count || 1} Interns</span></td>
                  <td>
                    <a href="/onboarding.html?batch_id=${b.id}" class="btn btn-sm btn-secondary">👥 Chi tiết Nhóm</a>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      ${renderProgressDashboardSection(data.batch_progresses, data.intern_doc_progresses)}
    `;
  } else {
    // ADMIN
    statsGrid.innerHTML = `
      <div class="stat-card">
        <div>
          <div class="stat-label">Total Interns</div>
          <div class="stat-value">${data.total_interns}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-label">Total Leaders</div>
          <div class="stat-value">${data.total_leaders}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 4 4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 1 0 7.75"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-label">Active Batches</div>
          <div class="stat-value">${data.active_batches}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-label">Pending Leaves</div>
          <div class="stat-value">${data.pending_leaves}</div>
        </div>
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
        </div>
      </div>
    `;

    sections.innerHTML = `
      <div class="card-section">
        <div class="card-title">Document Processing Overview</div>
        <div class="grid-stats" style="margin-bottom:0;">
          <div style="background-color:var(--bg-primary); padding:16px; border-radius:var(--radius-md);">
            <div style="font-size:12px; color:var(--text-muted);">TOTAL DOCS</div>
            <div style="font-size:20px; font-weight:700;">${data.document_stats.total}</div>
          </div>
          <div style="background-color:var(--bg-primary); padding:16px; border-radius:var(--radius-md);">
            <div style="font-size:12px; color:var(--accent-amber);">PROCESSING</div>
            <div style="font-size:20px; font-weight:700;">${data.document_stats.processing}</div>
          </div>
          <div style="background-color:var(--bg-primary); padding:16px; border-radius:var(--radius-md);">
            <div style="font-size:12px; color:var(--accent-emerald);">COMPLETED</div>
            <div style="font-size:20px; font-weight:700;">${data.document_stats.completed}</div>
          </div>
          <div style="background-color:var(--bg-primary); padding:16px; border-radius:var(--radius-md);">
            <div style="font-size:12px; color:var(--accent-rose);">FAILED</div>
            <div style="font-size:20px; font-weight:700;">${data.document_stats.failed}</div>
          </div>
        </div>
      </div>

      ${renderProgressDashboardSection(data.batch_progresses, data.intern_doc_progresses)}
    `;
  }
}

function renderProgressDashboardSection(batchProgresses, internProgresses) {
  return `
    <div style="margin-top:24px;">
      <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px; margin-bottom:16px; background:var(--bg-secondary); padding:14px 18px; border-radius:8px; border:1px solid var(--border-color);">
        <div>
          <h3 style="font-size:16px; font-weight:700; color:var(--text-primary); margin:0;">📊 Thống kê Tiến độ Đào tạo Real-time</h3>
          <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Chuyển đổi chế độ xem linh hoạt theo Nhóm Onboarding hoặc theo từng Thực tập sinh (Sắp xếp A-Z)</div>
        </div>
        
        <!-- Dual View Mode Switcher -->
        <div style="display:flex; background:var(--bg-primary); border:1px solid var(--border-color); border-radius:8px; padding:3px; gap:4px;">
          <button id="btn-view-by-batch" class="btn btn-sm btn-primary" onclick="switchProgressViewMode('batch')" style="border-radius:6px; font-size:12px; font-weight:600; padding:6px 12px;">
            🎯 Xem theo Nhóm
          </button>
          <button id="btn-view-by-intern" class="btn btn-sm btn-secondary" onclick="switchProgressViewMode('intern')" style="border-radius:6px; font-size:12px; font-weight:600; padding:6px 12px;">
            👨‍🎓 Xem theo Intern (A-Z)
          </button>
        </div>
      </div>

      <!-- Container 1: Group-First View Mode -->
      <div id="progress-view-by-batch">
        ${renderGroupedBatchProgressSection(batchProgresses)}
      </div>

      <!-- Container 2: Intern-First 360 View Mode -->
      <div id="progress-view-by-intern" style="display:none;">
        ${renderGroupedIntern360ProgressSection(internProgresses)}
      </div>
    </div>
  `;
}

function switchProgressViewMode(mode) {
  const batchView = document.getElementById('progress-view-by-batch');
  const internView = document.getElementById('progress-view-by-intern');
  const btnBatch = document.getElementById('btn-view-by-batch');
  const btnIntern = document.getElementById('btn-view-by-intern');

  if (mode === 'batch') {
    if (batchView) batchView.style.display = 'block';
    if (internView) internView.style.display = 'none';
    if (btnBatch) {
      btnBatch.className = 'btn btn-sm btn-primary';
    }
    if (btnIntern) {
      btnIntern.className = 'btn btn-sm btn-secondary';
    }
  } else {
    if (batchView) batchView.style.display = 'none';
    if (internView) internView.style.display = 'block';
    if (btnBatch) {
      btnBatch.className = 'btn btn-sm btn-secondary';
    }
    if (btnIntern) {
      btnIntern.className = 'btn btn-sm btn-primary';
    }
  }
}

function toggleBatchGroupContent(batchId) {
  const content = document.getElementById(`batch-group-content-${batchId}`);
  const chevron = document.getElementById(`batch-group-chevron-${batchId}`);
  if (content) {
    if (content.style.display === 'none') {
      content.style.display = 'block';
      if (chevron) chevron.style.transform = 'rotate(180deg)';
    } else {
      content.style.display = 'none';
      if (chevron) chevron.style.transform = 'rotate(0deg)';
    }
  }
}

function toggleUserDocProgress(rowId) {
  const row = document.getElementById(rowId);
  const internId = rowId.replace('user-doc-detail-', '');
  const chevron = document.getElementById(`user-chevron-${internId}`);
  if (row) {
    if (row.style.display === 'none') {
      row.style.display = 'table-row';
      if (chevron) chevron.style.transform = 'rotate(180deg)';
    } else {
      row.style.display = 'none';
      if (chevron) chevron.style.transform = 'rotate(0deg)';
    }
  }
}

function roundPercentage(num) {
  return Math.round((num + Number.EPSILON) * 10) / 10;
}

function renderGroupedBatchProgressSection(batchProgresses) {
  if (!batchProgresses || batchProgresses.length === 0) {
    return `
      <div class="card-section" style="margin-top:12px;">
        <div class="card-title">📊 Tiến độ Học tập của Các Nhóm Onboarding</div>
        <p style="color:var(--text-muted); font-size:13px; margin:0;">Chưa có dữ liệu nhóm Onboarding nào.</p>
      </div>
    `;
  }

  return batchProgresses.map((group, index) => {
    const interns = group.interns || [];
    // Sort Alphabetically (A-Z) by Intern Full Name
    interns.sort((a, b) => a.intern_name.localeCompare(b.intern_name, 'vi', { sensitivity: 'base' }));

    const isDefaultExpanded = index === 0;
    
    return `
      <div class="card-section" style="margin-top:16px; border-top: 3px solid var(--primary); padding:0; overflow:hidden;">
        <!-- Batch Group Header Banner (Clickable Accordion) -->
        <div onclick="toggleBatchGroupContent('${group.batch_id}')" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; padding:16px 20px; background:var(--bg-secondary); cursor:pointer; user-select:none; transition:background 0.2s ease;" onmouseover="this.style.background='rgba(56, 189, 248, 0.08)'" onmouseout="this.style.background='var(--bg-secondary)'">
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:38px; height:38px; border-radius:8px; background:var(--primary-alpha); color:var(--primary); display:flex; align-items:center; justify-content:center; font-size:20px; font-weight:700;">📁</div>
            <div>
              <h3 style="font-size:16px; font-weight:700; color:var(--text-primary); margin:0; display:flex; align-items:center; gap:8px;">
                ${group.batch_name}
                <span class="badge badge-${group.batch_status.toLowerCase()}" style="font-size:11px;">${group.batch_status}</span>
              </h3>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Bao gồm ${interns.length} Thực tập sinh (Click để thu gọn / xổ danh sách)</div>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:16px;">
            <!-- Group Average Progress Bar & Badge (XX% Avg.) -->
            <div style="display:flex; align-items:center; gap:10px; background:var(--bg-primary); padding:6px 14px; border-radius:20px; border:1px solid var(--border-color);">
              <span style="font-size:12px; color:var(--text-muted); font-weight:600;">TB Nhóm:</span>
              <div style="width:90px; height:8px; background:var(--bg-secondary); border-radius:4px; overflow:hidden; border:1px solid var(--border-color);">
                <div style="width:${group.avg_percentage || 0}%; height:100%; background:${(group.avg_percentage || 0) === 100 ? 'var(--accent-emerald)' : 'var(--primary)'}; transition:width 0.4s ease;"></div>
              </div>
              <span style="font-size:13px; font-weight:800; color:${(group.avg_percentage || 0) === 100 ? 'var(--accent-emerald)' : 'var(--primary)'};">${group.avg_percentage || 0}% Avg.</span>
            </div>

            <a href="/onboarding.html?batch_id=${group.batch_id}" class="btn btn-sm btn-secondary" onclick="event.stopPropagation();">👥 Quản lý Nhóm</a>
            <svg id="batch-group-chevron-${group.batch_id}" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5" style="transition:transform 0.3s ease; color:var(--primary); transform:${isDefaultExpanded ? 'rotate(180deg)' : 'rotate(0deg)'};"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>

        <!-- Collapsible Batch Group Content -->
        <div id="batch-group-content-${group.batch_id}" style="display:${isDefaultExpanded ? 'block' : 'none'}; padding:16px 20px; border-top:1px solid var(--border-color);">
          ${interns.length === 0 ? `
            <p style="color:var(--text-muted); font-size:13px; margin:0;">Chưa có Thực tập sinh nào trong nhóm này.</p>
          ` : `
            <div class="table-responsive">
              <table style="border-collapse:separate; border-spacing:0 6px;">
                <thead>
                  <tr>
                    <th>Thực tập sinh (Sắp xếp A-Z)</th>
                    <th>Số Tệp Tài liệu</th>
                    <th style="min-width:220px;">Tiến độ Tổng quan (%)</th>
                    <th style="width:50px; text-align:right;">Chi tiết</th>
                  </tr>
                </thead>
                <tbody>
                  ${interns.map(u => {
                    const safeInternId = `b${group.batch_id}-${u.intern_id}`;
                    const docs = u.docs || [];
                    return `
                      <tr onclick="toggleUserDocProgress('user-doc-detail-${safeInternId}')" style="cursor:pointer; background:var(--bg-secondary); transition:all 0.2s ease;" onmouseover="this.style.background='rgba(56, 189, 248, 0.08)'" onmouseout="this.style.background='var(--bg-secondary)'">
                        <td>
                          <div style="display:flex; align-items:center; gap:10px;">
                            <div style="width:34px; height:34px; border-radius:50%; background:var(--primary-alpha); color:var(--primary); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px;">
                              ${u.intern_name.charAt(0)}
                            </div>
                            <div>
                              <strong style="color:var(--text-primary); font-size:14px;">${u.intern_name}</strong>
                              <div style="font-size:11px; color:var(--text-muted);">${u.intern_email}</div>
                            </div>
                          </div>
                        </td>
                        <td><span class="badge badge-active" style="padding:4px 10px;">📂 ${docs.length} Tệp Tài liệu</span></td>
                        <td>
                          <div style="display:flex; align-items:center; gap:12px;">
                            <div style="flex:1; height:8px; background:var(--bg-primary); border-radius:4px; overflow:hidden; border:1px solid var(--border-color);">
                              <div style="width:${u.overall_percentage}%; height:100%; background:${u.overall_percentage === 100 ? 'var(--accent-emerald)' : 'var(--primary)'}; transition:width 0.4s ease;"></div>
                            </div>
                            <span style="font-size:13px; font-weight:700; color:${u.overall_percentage === 100 ? 'var(--accent-emerald)' : 'var(--primary)'}; min-width:45px; text-align:right;">${u.overall_percentage}%</span>
                          </div>
                        </td>
                        <td style="text-align:right;">
                          <svg id="user-chevron-${safeInternId}" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" style="transition:transform 0.2s ease; color:var(--primary);"><polyline points="6 9 12 15 18 9"/></svg>
                        </td>
                      </tr>
                      <tr id="user-doc-detail-${safeInternId}" style="display:none; background:transparent;">
                        <td colspan="4" style="padding:4px 10px 14px 10px;">
                          <div style="background:var(--bg-primary); border-radius:8px; padding:14px 18px; border:1px solid var(--border-color); box-shadow:inset 0 2px 6px rgba(0,0,0,0.2);">
                            <div style="font-size:11px; font-weight:700; color:var(--primary); margin-bottom:10px; text-transform:uppercase; letter-spacing:0.5px;">
                              📄 Chi tiết Tiến độ từng Tệp Tài liệu Nguồn:
                            </div>
                            ${docs.length === 0 ? '<p style="color:var(--text-muted); font-size:12px; margin:0;">Chưa có tài liệu đào tạo được phân cho nhóm này.</p>' : docs.map(doc => `
                              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; padding-bottom:8px; border-bottom:1px dashed var(--border-color);">
                                <div style="flex:1;">
                                  <strong style="font-size:13px; color:var(--text-primary);">📄 ${doc.filename}</strong>
                                  <span style="font-size:11px; color:var(--text-muted); margin-left:8px;">(${doc.completed_topics} / ${doc.total_topics} topics)</span>
                                </div>
                                <div style="width:240px; display:flex; align-items:center; gap:10px;">
                                  <div style="flex:1; height:6px; background:var(--bg-secondary); border-radius:3px; overflow:hidden; border:1px solid var(--border-color);">
                                    <div style="width:${doc.percentage}%; height:100%; background:${doc.percentage === 100 ? 'var(--accent-emerald)' : 'var(--primary)'};"></div>
                                  </div>
                                  <span style="font-size:12px; font-weight:700; color:${doc.percentage === 100 ? 'var(--accent-emerald)' : 'var(--primary)'}; min-width:40px; text-align:right;">${doc.percentage}%</span>
                                </div>
                              </div>
                            `).join('')}
                          </div>
                        </td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          `}
        </div>
      </div>
    `;
  }).join('');
}

function renderGroupedIntern360ProgressSection(docProgresses) {
  if (!docProgresses || docProgresses.length === 0) {
    return `
      <div class="card-section" style="margin-top:12px;">
        <div class="card-title">👨‍🎓 Tiến độ Chi tiết theo từng Thực tập sinh (A-Z)</div>
        <p style="color:var(--text-muted); font-size:13px; margin:0;">Chưa có dữ liệu tiến độ thực tập sinh nào.</p>
      </div>
    `;
  }

  const userGroups = {};
  docProgresses.forEach(dp => {
    if (!userGroups[dp.intern_id]) {
      userGroups[dp.intern_id] = {
        intern_id: dp.intern_id,
        intern_name: dp.intern_name,
        intern_email: dp.intern_email,
        batch_names: dp.batch_names || [],
        docs: [],
      };
    }
    userGroups[dp.intern_id].docs.push(dp);
  });

  const userList = Object.values(userGroups).map(u => {
    const totalSubtopicsRatio = u.docs.reduce((acc, d) => acc + d.percentage, 0);
    const avgPercentage = roundPercentage(totalSubtopicsRatio / u.docs.length);
    return { ...u, overall_percentage: avgPercentage };
  });

  // Sort Alphabetically (A-Z) by Intern Full Name
  userList.sort((a, b) => a.intern_name.localeCompare(b.intern_name, 'vi', { sensitivity: 'base' }));

  return `
    <div class="card-section" style="border-top: 3px solid var(--accent-emerald); margin-top:16px;">
      <div class="card-title" style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:14px;">
        <div>
          <span style="font-size:16px; font-weight:700; color:var(--text-primary);">👨‍🎓 Báo cáo 360° Tiến độ Học tập theo từng Thực tập sinh (Sắp xếp A-Z)</span>
          <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Sắp xếp thứ tự bảng chữ cái A-Z • Gom tất cả tài liệu của Thực tập sinh qua mọi Nhóm Onboarding vào 1 góc nhìn</div>
        </div>
        <span class="badge badge-active" style="font-size:11px; padding:4px 10px;">Sorted A-Z</span>
      </div>
      
      <div class="table-responsive">
        <table style="border-collapse:separate; border-spacing:0 6px;">
          <thead>
            <tr>
              <th>Thực tập sinh (Sắp xếp A-Z)</th>
              <th>Các Nhóm Tham gia</th>
              <th>Số Tệp Tài liệu</th>
              <th style="min-width:220px;">Tiến độ Tổng quan (%)</th>
              <th style="width:50px; text-align:right;">Chi tiết</th>
            </tr>
          </thead>
          <tbody>
            ${userList.map(u => {
              const safe360Id = `intern360-${u.intern_id}`;
              const batchesText = u.batch_names.length > 0 ? u.batch_names.join(', ') : 'Chưa xếp nhóm';
              return `
                <tr onclick="toggleUserDocProgress('user-doc-detail-${safe360Id}')" style="cursor:pointer; background:var(--bg-secondary); transition:all 0.2s ease;" onmouseover="this.style.background='rgba(56, 189, 248, 0.08)'" onmouseout="this.style.background='var(--bg-secondary)'">
                  <td>
                    <div style="display:flex; align-items:center; gap:10px;">
                      <div style="width:36px; height:36px; border-radius:50%; background:var(--primary-alpha); color:var(--primary); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px;">
                        ${u.intern_name.charAt(0)}
                      </div>
                      <div>
                        <strong style="color:var(--text-primary); font-size:14px;">${u.intern_name}</strong>
                        <div style="font-size:11px; color:var(--text-muted);">${u.intern_email}</div>
                      </div>
                    </div>
                  </td>
                  <td><span class="badge" style="background:rgba(56, 189, 248, 0.15); color:var(--primary); font-size:11px;">🎯 ${batchesText}</span></td>
                  <td><span class="badge badge-active" style="padding:4px 10px;">📂 ${u.docs.length} Tệp Tài liệu</span></td>
                  <td>
                    <div style="display:flex; align-items:center; gap:12px;">
                      <div style="flex:1; height:8px; background:var(--bg-primary); border-radius:4px; overflow:hidden; border:1px solid var(--border-color);">
                        <div style="width:${u.overall_percentage}%; height:100%; background:${u.overall_percentage === 100 ? 'var(--accent-emerald)' : 'var(--primary)'}; transition:width 0.4s ease;"></div>
                      </div>
                      <span style="font-size:13px; font-weight:700; color:${u.overall_percentage === 100 ? 'var(--accent-emerald)' : 'var(--primary)'}; min-width:45px; text-align:right;">${u.overall_percentage}%</span>
                    </div>
                  </td>
                  <td style="text-align:right;">
                    <svg id="user-chevron-${safe360Id}" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" style="transition:transform 0.2s ease; color:var(--primary);"><polyline points="6 9 12 15 18 9"/></svg>
                  </td>
                </tr>
                <tr id="user-doc-detail-${safe360Id}" style="display:none; background:transparent;">
                  <td colspan="5" style="padding:4px 10px 14px 10px;">
                    <div style="background:var(--bg-primary); border-radius:8px; padding:14px 18px; border:1px solid var(--border-color); box-shadow:inset 0 2px 6px rgba(0,0,0,0.2);">
                      <div style="font-size:11px; font-weight:700; color:var(--primary); margin-bottom:10px; text-transform:uppercase; letter-spacing:0.5px;">
                        📄 Danh sách Tệp Tài liệu của ${u.intern_name} qua các Nhóm:
                      </div>
                      ${u.docs.map(doc => `
                        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; padding-bottom:8px; border-bottom:1px dashed var(--border-color);">
                          <div style="flex:1;">
                            <strong style="font-size:13px; color:var(--text-primary);">📄 ${doc.filename}</strong>
                            <span class="badge" style="background:rgba(255,255,255,0.05); color:var(--text-secondary); margin-left:8px; font-size:11px;">🎯 ${doc.doc_batch_name}</span>
                            <span style="font-size:11px; color:var(--text-muted); margin-left:8px;">(${doc.completed_topics} / ${doc.total_topics} topics)</span>
                          </div>
                          <div style="width:240px; display:flex; align-items:center; gap:10px;">
                            <div style="flex:1; height:6px; background:var(--bg-secondary); border-radius:3px; overflow:hidden; border:1px solid var(--border-color);">
                              <div style="width:${doc.percentage}%; height:100%; background:${doc.percentage === 100 ? 'var(--accent-emerald)' : 'var(--primary)'};"></div>
                            </div>
                            <span style="font-size:12px; font-weight:700; color:${doc.percentage === 100 ? 'var(--accent-emerald)' : 'var(--primary)'}; min-width:40px; text-align:right;">${doc.percentage}%</span>
                          </div>
                        </div>
                      `).join('')}
                    </div>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}
