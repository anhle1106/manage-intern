document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.isAuthenticated()) return;
  const user = Auth.getUser();
  if (user.role !== 'ADMIN') {
    window.location.href = '/dashboard.html';
    return;
  }

  loadUsers();

  document.getElementById('create-user-form').addEventListener('submit', handleCreateUser);
});

async function loadUsers() {
  try {
    const users = await ApiClient.get('/users');
    const tbody = document.getElementById('users-table-body');

    if (users.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No users found.</td></tr>';
      return;
    }

    tbody.innerHTML = users.map(u => `
      <tr>
        <td><strong>${u.full_name}</strong></td>
        <td>${u.email}</td>
        <td><span class="badge badge-${getRoleBadgeClass(u.role)}">${u.role}</span></td>
        <td>${u.is_active ? '<span class="badge badge-completed">Active</span>' : '<span class="badge badge-rejected">Inactive</span>'}</td>
        <td>
          ${u.is_active ? `<button class="btn btn-sm btn-danger" onclick="deleteUser('${u.id}')">Deactivate</button>` : '-'}
        </td>
      </tr>
    `).join('');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function getRoleBadgeClass(role) {
  switch (role) {
    case 'ADMIN': return 'rejected';
    case 'LEADER': return 'active';
    default: return 'draft';
  }
}

async function handleCreateUser(e) {
  e.preventDefault();
  const data = {
    full_name: document.getElementById('user-name').value,
    email: document.getElementById('user-email').value,
    password: document.getElementById('user-pass').value,
    role: document.getElementById('user-role').value,
  };

  try {
    await ApiClient.post('/users', data);
    showToast('User account created');
    closeModal('create-user-modal');
    document.getElementById('create-user-form').reset();
    loadUsers();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteUser(id) {
  if (!confirm('Are you sure you want to deactivate this user?')) return;
  try {
    await ApiClient.delete(`/users/${id}`);
    showToast('User deactivated');
    loadUsers();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
