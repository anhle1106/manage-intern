document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.isAuthenticated()) return;
  const user = Auth.getUser();

  if (user.role !== 'INTERN') {
    document.getElementById('leave-actions').style.display = 'none';
  }

  loadLeaveRequests();

  document.getElementById('create-leave-form').addEventListener('submit', handleCreateLeave);
});

async function loadLeaveRequests() {
  try {
    const requests = await ApiClient.get('/leave-requests');
    const tbody = document.getElementById('leave-table-body');

    if (requests.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No leave requests found.</td></tr>';
      return;
    }

    tbody.innerHTML = requests.map(req => {
      let reviewerDisplay = '<span style="color:var(--text-muted); font-size:13px;">-</span>';
      if (req.reviewed_by_name) {
        if (req.status === 'APPROVED') {
          reviewerDisplay = `<div style="display:flex; align-items:center; gap:6px; color:var(--accent-emerald); font-weight:600; font-size:13px;">
            <span>✔</span> <span>${req.reviewed_by_name}</span>
          </div>`;
        } else if (req.status === 'REJECTED') {
          reviewerDisplay = `<div style="display:flex; align-items:center; gap:6px; color:var(--accent-rose); font-weight:600; font-size:13px;">
            <span>✖</span> <span>${req.reviewed_by_name}</span>
          </div>`;
        } else {
          reviewerDisplay = `<span style="font-weight:600;">${req.reviewed_by_name}</span>`;
        }
      } else if (req.status === 'PENDING') {
        reviewerDisplay = `<span class="badge badge-pending">⏳ Chờ duyệt</span>`;
      } else if (req.status === 'CANCELLED') {
        reviewerDisplay = `<span style="color:var(--text-muted); font-size:12px;">Đã hủy bởi Intern</span>`;
      }

      return `
        <tr>
          <td><strong>${req.user_name}</strong></td>
          <td>
            ${req.leave_type}
            ${req.created_schedule_id ? '<br><span style="font-size:11px; color:var(--primary); font-weight:600;">📅 Auto Schedule Created</span>' : ''}
          </td>
          <td>${formatDate(req.start_datetime)}</td>
          <td>${formatDate(req.end_datetime)}</td>
          <td>${req.reason}</td>
          <td><span class="badge badge-${req.status.toLowerCase()}">${req.status}</span></td>
          <td>${reviewerDisplay}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

async function handleCreateLeave(e) {
  e.preventDefault();
  const startInput = document.getElementById('leave-start').value;
  const endInput = document.getElementById('leave-end').value;

  const data = {
    leave_type: document.getElementById('leave-type').value,
    start_datetime: new Date(startInput).toISOString(),
    end_datetime: new Date(endInput).toISOString(),
    reason: document.getElementById('leave-reason').value,
    create_schedule: document.getElementById('leave-create-schedule').checked,
    schedule_subject: document.getElementById('leave-schedule-subject').value.trim() || null,
  };

  try {
    await ApiClient.post('/leave-requests', data);
    showToast('Leave request & schedule submitted successfully');
    closeModal('create-leave-modal');
    document.getElementById('create-leave-form').reset();
    loadLeaveRequests();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function approveLeave(id) {
  try {
    await ApiClient.put(`/leave-requests/${id}/approve`);
    showToast('Leave request approved');
    loadLeaveRequests();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function rejectLeave(id) {
  try {
    await ApiClient.put(`/leave-requests/${id}/reject`);
    showToast('Leave request rejected');
    loadLeaveRequests();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function cancelLeave(id) {
  try {
    await ApiClient.put(`/leave-requests/${id}/cancel`);
    showToast('Leave request cancelled');
    loadLeaveRequests();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
