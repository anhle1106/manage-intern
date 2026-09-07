let calendar = null;
let currentUserId = null;

const USER_COLORS = [
  { bg: '#38bdf8', border: '#0284c7' }, // Sky / Cyan
  { bg: '#10b981', border: '#059669' }, // Emerald
  { bg: '#a855f7', border: '#7e22ce' }, // Purple
  { bg: '#f59e0b', border: '#d97706' }, // Amber
  { bg: '#f43f5e', border: '#e11d48' }, // Rose
  { bg: '#6366f1', border: '#4338ca' }, // Indigo
  { bg: '#ec4899', border: '#be185d' }, // Pink
  { bg: '#14b8a6', border: '#0f766e' }, // Teal
];

function getUserColor(userId) {
  if (!userId) return USER_COLORS[0];
  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    hash = userId.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % USER_COLORS.length;
  return USER_COLORS[index];
}

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.isAuthenticated()) return;
  const user = Auth.getUser();
  currentUserId = user.id;

  initCalendar();
  await loadInternsList();

  document.getElementById('add-schedule-form').addEventListener('submit', handleAddSchedule);

  // Set default dates for schedule form
  const todayStr = new Date().toISOString().split('T')[0];
  document.getElementById('sched-start-date').value = todayStr;
  document.getElementById('sched-end-date').value = todayStr;

  document.getElementById('sched-start-date').addEventListener('change', (e) => {
    if (!document.getElementById('sched-end-date').value || document.getElementById('sched-end-date').value < e.target.value) {
      document.getElementById('sched-end-date').value = e.target.value;
    }
  });
});

function setAllDayTime() {
  document.getElementById('sched-start-time').value = '06:00';
  document.getElementById('sched-end-time').value = '23:00';
}

function toggleScheduleTypeUI(type) {
  const group = document.getElementById('recurring-days-group');
  if (type === 'RECURRING') {
    group.style.display = 'block';
  } else {
    group.style.display = 'none';
  }
}

function initCalendar() {
  const calendarEl = document.getElementById('calendar-container');
  calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    firstDay: 1,
    slotMinTime: '06:00:00',
    slotMaxTime: '23:00:00',
    slotDuration: '00:30:00',
    allDaySlot: false,
    events: [],
    eventClick: function(info) {
      const user = Auth.getUser();
      const eventUserId = info.event.extendedProps.userId;
      if (user.role === 'ADMIN' || eventUserId === user.id) {
        if (confirm(`Xóa lịch bận "${info.event.title}"?`)) {
          deleteSchedule(info.event.id);
        }
      } else {
        alert(`Lịch bận: ${info.event.title}\nKhung giờ: ${info.event.extendedProps.timeRange}`);
      }
    }
  });
  calendar.render();
}

async function loadInternsList() {
  const user = Auth.getUser();
  const select = document.getElementById('intern-select');
  if (!select) return;

  let html = `<option value="ALL">🌐 Tất cả thực tập sinh (Xem toàn bộ lịch)</option>`;
  html += `<option value="${user.id}">👤 Cá nhân tôi (${user.full_name})</option>`;

  try {
    const interns = await ApiClient.get('/interns');
    interns.forEach(i => {
      if (i.user_id !== user.id) {
        html += `<option value="${i.user_id}">👤 ${i.full_name} (${i.university || 'Thực tập sinh'})</option>`;
      }
    });
  } catch (err) {
    console.warn('Could not fetch interns list for filter:', err);
  }

  select.innerHTML = html;
  select.value = 'ALL';
  loadSchedules('ALL');
}

async function loadInternSchedule(userId) {
  if (!userId) return;
  loadSchedules(userId);
}

async function loadSchedules(userId) {
  try {
    const endpoint = (userId === 'ALL') ? '/schedules?user_id=ALL' : `/schedules?user_id=${userId}`;
    const schedules = await ApiClient.get(endpoint);
    const events = convertSchedulesToEvents(schedules);
    
    calendar.removeAllEvents();
    calendar.addEventSource(events);
    
    renderLegend(schedules);
    renderScheduleTable(schedules);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderLegend(schedules) {
  const legendEl = document.getElementById('schedule-filter-legend');
  if (!legendEl) return;

  const userMap = {};
  schedules.forEach(s => {
    if (s.user_id && s.user_name) {
      userMap[s.user_id] = s.user_name;
    }
  });

  const userIds = Object.keys(userMap);
  if (userIds.length === 0) {
    legendEl.innerHTML = '';
    return;
  }

  legendEl.innerHTML = userIds.map(uid => {
    const color = getUserColor(uid);
    return `
      <div style="display:flex; align-items:center; gap:6px;">
        <span style="display:inline-block; width:12px; height:12px; border-radius:50%; background-color:${color.bg}; border:1px solid ${color.border};"></span>
        <span style="font-weight:600; color:var(--text-secondary);">${userMap[uid]}</span>
      </div>
    `;
  }).join('');
}

function renderScheduleTable(schedules) {
  const tbody = document.getElementById('schedule-table-body');
  if (!tbody) return;

  const currentUser = Auth.getUser();

  if (!schedules || schedules.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">Chưa có lịch bận nào. Hãy bấm "+ Add Schedule" để thêm lịch!</td></tr>';
    return;
  }

  const daysNames = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"];

  tbody.innerHTML = schedules.map(s => {
    let typeBadge = '<span class="badge badge-draft">🗓 Ngày cụ thể</span>';
    let dowText = `${s.start_date} ~ ${s.end_date}`;

    if (s.is_recurring && s.days_of_week && s.days_of_week.length > 0) {
      typeBadge = '<span class="badge badge-active">🔄 Lặp tuần</span>';
      const dowsStr = s.days_of_week.map(d => daysNames[d] || '').join(', ');
      dowText = `${dowsStr} (${s.start_date} ~ ${s.end_date})`;
    }

    const canDelete = (currentUser.role === 'ADMIN' || s.user_id === currentUser.id);
    const color = getUserColor(s.user_id);

    return `
      <tr>
        <td>
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background-color:${color.bg};"></span>
            <strong>${s.user_name || 'N/A'}</strong>
          </div>
        </td>
        <td><strong>${s.subject}</strong></td>
        <td>${typeBadge}</td>
        <td>${dowText}</td>
        <td><strong style="color:var(--primary);">${s.start_time} - ${s.end_time}</strong></td>
        <td>
          ${canDelete ? `<button class="btn btn-sm btn-danger" onclick="deleteSchedule('${s.id}')">🗑 Xóa</button>` : '-'}
        </td>
      </tr>
    `;
  }).join('');
}

function convertSchedulesToEvents(schedules) {
  const events = [];
  const daysMap = [1, 2, 3, 4, 5, 6, 0]; // Python 0=Mon -> FC 1, 5=Sat -> FC 6, 6=Sun -> FC 0

  schedules.forEach(s => {
    let endRecurInclusive = s.end_date;
    try {
      const parts = s.end_date.split('-');
      if (parts.length === 3) {
        const ed = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
        ed.setDate(ed.getDate() + 1);
        const yyyy = ed.getFullYear();
        const mm = String(ed.getMonth() + 1).padStart(2, '0');
        const dd = String(ed.getDate()).padStart(2, '0');
        endRecurInclusive = `${yyyy}-${mm}-${dd}`;
      }
    } catch (e) {
      endRecurInclusive = s.end_date;
    }

    const activeDaysOfWeek = new Set();

    if (s.is_recurring && s.days_of_week && s.days_of_week.length > 0) {
      s.days_of_week.forEach(d => {
        activeDaysOfWeek.add(daysMap[d]);
      });
    } else {
      try {
        const pStart = s.start_date.split('-');
        const pEnd = s.end_date.split('-');
        const dStart = new Date(parseInt(pStart[0]), parseInt(pStart[1]) - 1, parseInt(pStart[2]));
        const dEnd = new Date(parseInt(pEnd[0]), parseInt(pEnd[1]) - 1, parseInt(pEnd[2]));
        
        let curr = new Date(dStart);
        while (curr <= dEnd) {
          let pyDay = curr.getDay() - 1;
          if (pyDay < 0) pyDay = 6;
          activeDaysOfWeek.add(daysMap[pyDay]);
          curr.setDate(curr.getDate() + 1);
        }
      } catch (e) {
        activeDaysOfWeek.add(daysMap[s.day_of_week || 0]);
      }
    }

    const daysList = activeDaysOfWeek.size > 0 ? Array.from(activeDaysOfWeek) : [daysMap[s.day_of_week || 0]];
    const color = getUserColor(s.user_id);
    const userName = s.user_name || 'Intern';

    events.push({
      id: s.id,
      title: `${userName}: ${s.subject}`,
      daysOfWeek: daysList,
      startTime: s.start_time,
      endTime: s.end_time,
      startRecur: s.start_date,
      endRecur: endRecurInclusive,
      backgroundColor: color.bg,
      borderColor: color.border,
      textColor: '#ffffff',
      extendedProps: {
        userId: s.user_id,
        userName: userName,
        subject: s.subject,
        timeRange: `${s.start_time} - ${s.end_time}`,
      }
    });
  });

  return events;
}

async function handleAddSchedule(e) {
  e.preventDefault();
  const startTime = document.getElementById('sched-start-time').value;
  const endTime = document.getElementById('sched-end-time').value;
  const startDate = document.getElementById('sched-start-date').value;
  const endDate = document.getElementById('sched-end-date').value;

  if (startTime >= endTime) {
    showToast('Start time must be before End time!', 'error');
    return;
  }
  if (startDate > endDate) {
    showToast('Start date must be before or equal to End date!', 'error');
    return;
  }

  const schedType = document.querySelector('input[name="sched-type"]:checked').value;
  const isRecurring = (schedType === 'RECURRING');

  let selectedDows = [];
  if (isRecurring) {
    const checkboxes = document.querySelectorAll('input[name="sched-dow"]:checked');
    checkboxes.forEach(cb => selectedDows.push(parseInt(cb.value)));
    if (selectedDows.length === 0) {
      showToast('Please select at least one day of the week for recurring classes!', 'error');
      return;
    }
  }

  const data = {
    subject: document.getElementById('sched-subject').value,
    is_recurring: isRecurring,
    days_of_week: selectedDows,
    start_time: startTime,
    end_time: endTime,
    start_date: startDate,
    end_date: endDate,
    location: "",
    note: "",
  };

  try {
    await ApiClient.post('/schedules', data);
    showToast(isRecurring ? 'Recurring class schedule created' : 'Specific date schedule entry created');
    closeModal('add-schedule-modal');
    document.getElementById('add-schedule-form').reset();
    document.getElementById('recurring-days-group').style.display = 'none';
    
    const select = document.getElementById('intern-select');
    const activeVal = select ? select.value : 'ALL';
    loadSchedules(activeVal);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteSchedule(id) {
  try {
    await ApiClient.delete(`/schedules/${id}`);
    showToast('Lịch bận đã được xóa thành công!');
    const select = document.getElementById('intern-select');
    const activeVal = select ? select.value : 'ALL';
    loadSchedules(activeVal);
  } catch (err) {
    showToast(err.message, 'error');
  }
}
