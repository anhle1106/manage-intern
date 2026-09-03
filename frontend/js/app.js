// Main Layout & Shared UI Utilities
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname.endsWith('login.html')) return;
  Auth.requireAuth();

  renderSidebar();
  renderUserInfo();
});

async function renderSidebar() {
  const user = Auth.getUser();
  if (!user) return;

  const activePath = window.location.pathname;
  const urlParams = new URLSearchParams(window.location.search);
  const activeBatchId = urlParams.get('batch_id');
  const activeOnboardingId = urlParams.get('onboarding_id');

  const navItems = [
    { label: 'Dashboard', path: '/dashboard.html', icon: '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>', roles: ['ADMIN', 'LEADER', 'INTERN'] },
    { label: 'Schedule', path: '/schedule.html', icon: '<rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>', roles: ['ADMIN', 'LEADER', 'INTERN'] },
    { label: 'Leave Requests', path: '/leave.html', icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>', roles: ['ADMIN', 'LEADER', 'INTERN'] },
    { label: 'Onboarding', path: '/onboarding.html', isAccordion: true, icon: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>', roles: ['ADMIN', 'LEADER', 'INTERN'] },
    { label: 'Documents', path: '/documents.html', icon: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/>', roles: ['ADMIN', 'LEADER'] },
    { label: 'Learning Roadmap', path: '/learning.html', isAccordion: true, icon: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>', roles: ['ADMIN', 'LEADER', 'INTERN'] },
    { label: 'User Management', path: '/users.html', icon: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>', roles: ['ADMIN'] },
  ];

  const filteredNav = navItems.filter(item => item.roles.includes(user.role));

  // Fetch Onboarding Batches for accordion menus
  let batches = [];
  try {
    batches = await ApiClient.get('/onboardings');
  } catch (err) {
    console.error('Failed to fetch batches for sidebar:', err);
  }

  const sidebarEl = document.getElementById('sidebar');
  if (!sidebarEl) return;

  sidebarEl.innerHTML = `
    <div class="sidebar-header">
      <div class="brand-icon">D</div>
      <div>
        <div class="brand-title">DevOps Portal</div>
      </div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-label">Navigation</div>
      ${filteredNav.map(item => {
        if (item.label === 'Onboarding') {
          const isOnboardingActive = activePath.endsWith('onboarding.html');
          return `
            <div class="nav-item nav-parent ${isOnboardingActive ? 'active' : ''}" onclick="toggleSidebarSubmenu('onboarding-submenu', 'onboarding-chevron')">
              <div style="display:flex; align-items:center; gap:12px;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">${item.icon}</svg>
                <span>${item.label}</span>
              </div>
              <svg id="onboarding-chevron" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" class="submenu-chevron ${isOnboardingActive ? 'open' : ''}"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            <div id="onboarding-submenu" class="nav-submenu ${isOnboardingActive ? 'open' : ''}">
              ${batches.map((b, idx) => `
                <a href="/onboarding.html?batch_id=${b.id}" class="nav-subitem ${isOnboardingActive && (activeBatchId === b.id || (!activeBatchId && idx === 0)) ? 'active' : ''}">
                  <span>📂 ${b.name}</span>
                </a>
              `).join('')}
            </div>
          `;
        }

        if (item.label === 'Learning Roadmap') {
          const isLearningActive = activePath.endsWith('learning.html');
          return `
            <div class="nav-item nav-parent ${isLearningActive ? 'active' : ''}" onclick="toggleSidebarSubmenu('learning-submenu', 'learning-chevron')">
              <div style="display:flex; align-items:center; gap:12px;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">${item.icon}</svg>
                <span>${item.label}</span>
              </div>
              <svg id="learning-chevron" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" class="submenu-chevron ${isLearningActive ? 'open' : ''}"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            <div id="learning-submenu" class="nav-submenu ${isLearningActive ? 'open' : ''}">
              ${batches.map((b, idx) => `
                <a href="/learning.html?onboarding_id=${b.id}" class="nav-subitem ${isLearningActive && (activeOnboardingId === b.id || (!activeOnboardingId && idx === 0)) ? 'active' : ''}">
                  <span>📂 ${b.name}</span>
                </a>
              `).join('')}
            </div>
          `;
        }

        return `
          <a href="${item.path}" class="nav-item ${activePath.endsWith(item.path) ? 'active' : ''}">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">${item.icon}</svg>
            <span>${item.label}</span>
          </a>
        `;
      }).join('')}
    </nav>
    <div class="sidebar-footer">
      <div class="user-profile">
        <div class="avatar">${user.full_name ? user.full_name[0].toUpperCase() : 'U'}</div>
        <div class="user-info">
          <div class="user-name">${user.full_name}</div>
          <div class="user-role">${user.role}</div>
        </div>
        <button class="btn-logout" onclick="Auth.logout()" title="Logout">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
        </button>
      </div>
    </div>
  `;
}

function toggleSidebarSubmenu(menuId, chevronId) {
  const submenu = document.getElementById(menuId);
  const chevron = document.getElementById(chevronId || 'onboarding-chevron');
  if (submenu) {
    submenu.classList.toggle('open');
  }
  if (chevron) {
    chevron.classList.toggle('open');
  }
}

function updateSidebarActiveSubitem(batchId, menuType = 'learning') {
  const submenuId = menuType === 'learning' ? 'learning-submenu' : 'onboarding-submenu';
  const paramName = menuType === 'learning' ? 'onboarding_id' : 'batch_id';
  const submenu = document.getElementById(submenuId);
  if (!submenu) return;
  submenu.querySelectorAll('.nav-subitem').forEach(subitem => {
    const href = subitem.getAttribute('href') || '';
    if (href.includes(`${paramName}=${batchId}`)) {
      subitem.classList.add('active');
    } else {
      subitem.classList.remove('active');
    }
  });
}

function renderUserInfo() {
  const user = Auth.getUser();
  if (!user) return;
  const userGreetingEl = document.getElementById('user-greeting');
  if (userGreetingEl) {
    userGreetingEl.innerText = `Welcome back, ${user.full_name}!`;
  }
}

function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerText = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function openModal(modalId) {
  const backdrop = document.getElementById(modalId);
  if (backdrop) backdrop.classList.add('active');
}

function closeModal(modalId) {
  const backdrop = document.getElementById(modalId);
  if (backdrop) backdrop.classList.remove('active');
}
