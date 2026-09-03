let currentBatchFilter = '';
let currentTargetInternId = '';
let currentBatchInterns = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.isAuthenticated()) return;

  const urlParams = new URLSearchParams(window.location.search);
  const onboardingIdParam = urlParams.get('onboarding_id');

  await loadBatchOptions(onboardingIdParam);
  loadLearningProgress(currentBatchFilter, currentTargetInternId);

  document.getElementById('audit-review-form').addEventListener('submit', handleSaveAuditReview);
});

async function loadBatchOptions(selectedId) {
  try {
    const batches = await ApiClient.get('/onboardings');
    const pillsContainer = document.getElementById('learning-nav-pills');
    const user = Auth.getUser();
    const isTechLead = user.role === 'LEADER' || user.role === 'ADMIN';

    if (!batches || batches.length === 0) {
      if (pillsContainer) pillsContainer.innerHTML = '<div style="color:var(--text-muted); font-size:13px;">No assigned onboarding groups found.</div>';
      currentBatchFilter = '';
      return;
    }

    let activeBatch = batches[0];
    if (selectedId) {
      const found = batches.find(b => b.id === selectedId);
      if (found) activeBatch = found;
    }

    currentBatchFilter = activeBatch.id;

    // Render Pills
    if (pillsContainer) {
      pillsContainer.innerHTML = batches.map(b => `
        <div class="onboarding-pill ${b.id === activeBatch.id ? 'active' : ''}" id="learning-pill-${b.id}" onclick="selectLearningGroup('${b.id}')">
          <span>🎯</span>
          <span>${b.name}</span>
          <span class="badge badge-${b.status.toLowerCase()}" style="font-size:10px; padding:2px 6px;">${b.status}</span>
        </div>
      `).join('');
    }

    if (typeof updateSidebarActiveSubitem === 'function') {
      updateSidebarActiveSubitem(activeBatch.id, 'learning');
    }

    if (isTechLead && currentBatchFilter) {
      await setupInternSelector(activeBatch);
    }
  } catch (err) {
    console.error('Failed to load onboarding batches for roadmap:', err);
  }
}

async function selectLearningGroup(batchId) {
  currentBatchFilter = batchId;

  // Update URL
  const newUrl = `${window.location.pathname}?onboarding_id=${batchId}`;
  window.history.pushState({ path: newUrl }, '', newUrl);

  // Synchronize Sidebar Submenu Active Item
  if (typeof updateSidebarActiveSubitem === 'function') {
    updateSidebarActiveSubitem(batchId, 'learning');
  } else {
    document.querySelectorAll('#learning-submenu .nav-subitem').forEach(subitem => {
      subitem.classList.remove('active');
      if (subitem.getAttribute('href') === `/learning.html?onboarding_id=${batchId}`) {
        subitem.classList.add('active');
      }
    });
  }

  // Update Pills UI
  document.querySelectorAll('#learning-nav-pills .onboarding-pill').forEach(pill => {
    pill.classList.remove('active');
  });
  const activePill = document.getElementById(`learning-pill-${batchId}`);
  if (activePill) activePill.classList.add('active');

  const user = Auth.getUser();
  const isTechLead = user.role === 'LEADER' || user.role === 'ADMIN';

  if (isTechLead) {
    const batches = await ApiClient.get('/onboardings');
    const activeBatch = batches.find(b => b.id === batchId);
    if (activeBatch) {
      await setupInternSelector(activeBatch);
    }
  }

  loadLearningProgress(currentBatchFilter, currentTargetInternId);
}

async function setupInternSelector(batch) {
  const user = Auth.getUser();
  if (user.role !== 'LEADER' && user.role !== 'ADMIN') return;

  const wrapper = document.getElementById('intern-selector-wrapper');
  const select = document.getElementById('roadmap-intern-filter');

  wrapper.style.display = 'block';

  if (!batch || !batch.interns || batch.interns.length === 0) {
    select.innerHTML = '<option value="">No Interns in Batch</option>';
    currentBatchInterns = [];
    currentTargetInternId = '';
    return;
  }

  currentBatchInterns = batch.interns;
  select.innerHTML = batch.interns.map(i => `<option value="${i.id}">${i.full_name}</option>`).join('');

  if (!currentTargetInternId || !batch.interns.some(i => i.id === currentTargetInternId)) {
    currentTargetInternId = batch.interns[0].id;
  }
  select.value = currentTargetInternId;
}

async function filterRoadmapByBatch(batchId) {
  currentBatchFilter = batchId;
  loadLearningProgress(currentBatchFilter, currentTargetInternId);
}

function filterRoadmapByIntern(internId) {
  currentTargetInternId = internId;
  loadLearningProgress(currentBatchFilter, currentTargetInternId);
}

function onInternFilterChange(internId) {
  filterRoadmapByIntern(internId);
}

async function loadLearningProgress(onboardingId, internId) {
  try {
    let progressEndpoint = '/learning/progress';
    let topicsEndpoint = '/learning/topics';

    const params = [];
    if (onboardingId) params.push(`onboarding_id=${onboardingId}`);
    if (internId) params.push(`intern_id=${internId}`);

    if (params.length > 0) {
      const queryStr = `?${params.join('&')}`;
      progressEndpoint += queryStr;
      topicsEndpoint += queryStr;
    }

    const [progressData, topicsData] = await Promise.all([
      ApiClient.get(progressEndpoint),
      ApiClient.get(topicsEndpoint),
    ]);

    renderProgressHeader(progressData);
    renderTopics(topicsData);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderProgressHeader(data) {
  const bar = document.getElementById('roadmap-progress-bar');
  const text = document.getElementById('roadmap-progress-text');
  const percentText = document.getElementById('roadmap-progress-percent');

  bar.style.width = `${data.percentage}%`;
  percentText.innerText = `${data.percentage}%`;
  text.innerText = `Completed ${data.completed_topics} of ${data.total_topics} topics (${data.percentage}%)`;
}

function toggleDocGroup(groupId) {
  const body = document.getElementById(groupId);
  const chevron = document.getElementById(`chevron-${groupId}`);
  if (body) {
    if (body.style.display === 'none') {
      body.style.display = 'block';
      if (chevron) chevron.style.transform = 'rotate(0deg)';
    } else {
      body.style.display = 'none';
      if (chevron) chevron.style.transform = 'rotate(-90deg)';
    }
  }
}

function renderTopics(topics) {
  const container = document.getElementById('topics-list');
  const user = Auth.getUser();
  const isTechLead = user.role === 'LEADER' || user.role === 'ADMIN';

  if (!topics || topics.length === 0) {
    container.innerHTML = `
      <div class="card-section" style="text-align:center; padding:40px 20px;">
        <div style="font-size:36px; margin-bottom:10px;">📚</div>
        <h3 style="font-size:16px; font-weight:700; color:var(--text-primary);">No Learning Topics Available</h3>
        <p style="color:var(--text-muted); font-size:13px; margin-top:6px;">
          ${user.role === 'INTERN' 
            ? 'No training documents have been uploaded for your assigned onboarding batch yet. Please check back later!' 
            : 'No learning topics found. Upload training documents in Document Management to generate a roadmap!'}
        </p>
      </div>
    `;
    return;
  }

  // Group topics by document_name
  const docGroups = {};
  topics.forEach(t => {
    const docKey = t.document_name || 'Tài liệu Đào tạo';
    if (!docGroups[docKey]) docGroups[docKey] = [];
    docGroups[docKey].push(t);
  });

  const currentInternObj = currentBatchInterns.find(i => i.id === currentTargetInternId);
  const targetName = currentInternObj ? currentInternObj.full_name : 'Intern';

  let html = '';

  Object.keys(docGroups).forEach((docName, docIdx) => {
    const docTopics = docGroups[docName];
    const safeDocId = `doc-group-${docIdx}`;
    
    // Collapsible Document Group Header Banner
    html += `
      <div class="card-section doc-group-card" style="background:var(--bg-secondary); border-left: 4px solid var(--primary); padding:16px 20px; margin-bottom:12px; margin-top:24px; cursor:pointer; user-select:none;" onclick="toggleDocGroup('${safeDocId}')">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:38px; height:38px; border-radius:8px; background:var(--primary-alpha); display:flex; align-items:center; justify-content:center; font-size:20px;">📄</div>
            <div>
              <h3 style="font-size:16px; font-weight:700; color:var(--text-primary); margin:0;">Nguồn tài liệu: ${docName}</h3>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Bao gồm ${docTopics.length} Module bài học (Click để thu gọn / mở rộng)</div>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:12px;">
            <span class="badge badge-active" style="padding:6px 12px; font-size:11px;">DOCUMENT SOURCE</span>
            <svg id="chevron-${safeDocId}" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" class="submenu-chevron open" style="transition:transform 0.2s ease;"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>
      </div>

      <!-- Collapsible Container for Topics of this Document -->
      <div id="${safeDocId}" class="doc-group-body" style="transition:all 0.3s ease;">
    `;

    // Render topics for this document
    html += docTopics.map(t => {
      const audit = t.audit_review;
      const completedSubtopics = t.completed_subtopics || [];

      return `
        <div class="topic-card ${t.completed ? 'completed' : ''}" id="topic-card-${t.id}">
          <div class="topic-header">
            ${isTechLead ? `
              <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:18px; color:${t.completed ? 'var(--accent-emerald)' : 'var(--text-muted)'}; font-weight:700; user-select:none;">${t.completed ? '☑' : '☐'}</span>
                <span class="topic-title" style="cursor:default;">${t.title}</span>
              </div>
            ` : `
              <label class="ticket-checkbox">
                <input type="checkbox" ${t.completed ? 'checked' : ''} onchange="toggleTopic('${t.id}', ${t.completed})">
                <span class="topic-title">${t.title}</span>
              </label>
            `}
            <div style="display:flex; align-items:center; gap:8px;">
              ${t.completed ? '<span class="completed-badge">✓ Completed</span>' : '<span class="badge badge-draft">In Progress</span>'}
              ${isTechLead ? `
                <button class="btn btn-sm btn-secondary" onclick="openAuditModal('${t.id}', '${t.title.replace(/'/g, "\\'")}', '${targetName.replace(/'/g, "\\'")}', '${audit ? audit.status : 'PASSED'}', '${audit && audit.score !== null ? audit.score : ''}', '${audit ? audit.feedback.replace(/'/g, "\\'").replace(/\n/g, "\\n") : ''}')">
                  ${audit ? '✏️ Edit Audit' : '📝 Audit Review'}
                </button>
              ` : ''}
            </div>
          </div>
          
          <p style="color:var(--text-secondary); font-size:14px; margin-bottom:14px; margin-left:34px;">${t.summary}</p>

          ${t.key_concepts && t.key_concepts.length > 0 ? `
            <div style="margin-bottom:14px; margin-left:34px;">
              <strong style="font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;">Key Concepts:</strong><br>
              ${t.key_concepts.map(k => `<span class="concept-tag">${k}</span>`).join('')}
            </div>
          ` : ''}

          ${t.subtopics && t.subtopics.length > 0 ? `
            <div class="subtopics-container" style="margin-left:34px;">
              <strong style="font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;">Subtopics Checklist:</strong>
              ${t.subtopics.map((st, idx) => {
                const isSubtopicDone = t.completed || completedSubtopics.includes(idx);
                return `
                  <div class="subtopic-ticket ${isSubtopicDone ? 'done' : ''}">
                    ${isTechLead ? `
                      <span style="font-size:16px; margin-right:8px; color:${isSubtopicDone ? 'var(--accent-emerald)' : 'var(--text-muted)'}; font-weight:700; user-select:none;">${isSubtopicDone ? '☑' : '☐'}</span>
                    ` : `
                      <input type="checkbox" ${isSubtopicDone ? 'checked' : ''} onchange="toggleSubtopic('${t.id}', ${idx})">
                    `}
                    <div style="flex:1;">
                      <div class="subtopic-title">${st.title}</div>
                      <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">${st.summary}</div>

                      <!-- TechLead Audit Question Hints (Only visible to TechLead / Admin) -->
                      ${isTechLead && st.audit_checklist && st.audit_checklist.length > 0 ? `
                        <div class="audit-checklist-box">
                          <div style="font-size:11px; font-weight:700; color:var(--primary); text-transform:uppercase; margin-bottom:6px; display:flex; align-items:center; justify-content:space-between;">
                            <span>💡 TechLead Audit Questions (${st.audit_checklist.length} câu gợi ý - Đáp án có sẵn trong file):</span>
                            <span class="badge badge-active" style="font-size:10px; padding:2px 6px;">In-Doc Verified</span>
                          </div>
                          ${st.audit_checklist.map((ac, acIdx) => `
                            <div class="audit-question-item">
                              <strong style="color:var(--text-primary);">• Câu ${acIdx + 1}: ${ac.question_or_task}</strong><br>
                              <span style="color:var(--text-muted); font-size:11px;">🔑 Từ khóa đáp án trong file: <em>${ac.expected_answer_keywords}</em></span>
                            </div>
                          `).join('')}
                        </div>
                      ` : ''}

                      <!-- Multiple Choice Quiz Box for Intern Self-Testing (Only visible to INTERN role) -->
                      ${!isTechLead && st.quiz_questions && st.quiz_questions.length > 0 ? `
                        <div class="quiz-checklist-box" style="margin-top:10px; padding:12px 14px; background:rgba(124, 77, 255, 0.04); border:1px dashed rgba(124, 77, 255, 0.3); border-radius:var(--radius-md);">
                          <div style="font-size:11px; font-weight:700; color:var(--accent-purple); text-transform:uppercase; margin-bottom:8px; display:flex; align-items:center; justify-content:space-between;">
                            <span>🧠 Câu Hỏi Trắc Nghiệm Ôn Tập (${st.quiz_questions.length} câu trắc nghiệm):</span>
                            <span class="badge badge-active" style="font-size:10px; padding:2px 6px; background:var(--accent-purple); color:#fff;">Quiz Mode</span>
                          </div>
                          ${st.quiz_questions.map((qq, qIdx) => `
                            <div class="quiz-item" style="margin-top:8px; padding-bottom:8px; border-bottom:1px dashed rgba(255,255,255,0.08);">
                              <div style="font-size:13px; font-weight:600; color:var(--text-primary);">❓ Câu ${qIdx + 1}: ${qq.question}</div>
                              <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:6px;">
                                ${(qq.options || []).map((opt, optIdx) => {
                                  const optionLetter = opt.charAt(0);
                                  return `
                                    <label style="font-size:12px; color:var(--text-secondary); background:var(--bg-card); padding:6px 10px; border-radius:6px; border:1px solid var(--border-color); cursor:pointer; display:flex; align-items:center; gap:6px;">
                                      <input type="radio" name="quiz-${t.id}-${idx}-${qIdx}" value="${optionLetter}" onchange="checkQuizAnswer(this, '${(qq.correct_answer || '').replace(/'/g, "\\'")}', '${(qq.explanation || '').replace(/'/g, "\\'")}', 'feedback-${t.id}-${idx}-${qIdx}')">
                                      <span>${opt}</span>
                                    </label>
                                  `;
                                }).join('')}
                              </div>
                              <div id="feedback-${t.id}-${idx}-${qIdx}" style="display:none; font-size:12px; margin-top:6px; padding:6px 10px; border-radius:6px;"></div>
                            </div>
                          `).join('')}
                        </div>
                      ` : ''}
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          ` : ''}

          <!-- Audit Review Card -->
          ${audit ? `
            <div class="audit-review-box ${audit.status.toLowerCase()}">
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <strong style="font-size:13px; color:var(--text-primary);">👨‍🏫 Audit Review by ${audit.leader_name}</strong>
                  <span class="audit-badge ${audit.status.toLowerCase()}">${audit.status}</span>
                </div>
                ${audit.score !== null && audit.score !== undefined ? `<span style="font-size:13px; font-weight:700; color:var(--primary);">Score: ${audit.score}/100</span>` : ''}
              </div>
              <p style="font-size:13px; color:var(--text-secondary); margin:0;">${audit.feedback || 'No feedback comments provided.'}</p>
            </div>
          ` : ''}
        </div>
      `;
    }).join('');

    html += `</div>`; // Close doc-group-body
  });

  container.innerHTML = html;
}

async function toggleTopic(topicId, currentStatus) {
  const user = Auth.getUser();
  if (user.role === 'LEADER' || user.role === 'ADMIN') {
    showToast('Ticking completion checklist is read-only for Leader and Admin!', 'warning');
    return;
  }

  try {
    const endpoint = `/learning/topics/${topicId}/complete`;
    await ApiClient.put(endpoint);
    loadLearningProgress(currentBatchFilter, currentTargetInternId);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function toggleSubtopic(topicId, subtopicIndex) {
  const user = Auth.getUser();
  if (user.role === 'LEADER' || user.role === 'ADMIN') {
    showToast('Ticking completion checklist is read-only for Leader and Admin!', 'warning');
    return;
  }

  try {
    const endpoint = `/learning/topics/${topicId}/subtopics/${subtopicIndex}/toggle`;
    await ApiClient.put(endpoint);
    loadLearningProgress(currentBatchFilter, currentTargetInternId);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openAuditModal(topicId, topicTitle, internName, status, score, feedback) {
  document.getElementById('audit-topic-id').value = topicId;
  document.getElementById('audit-modal-subtitle').innerText = `Auditing: "${topicTitle}" for ${internName}`;
  document.getElementById('audit-status').value = status || 'PASSED';
  document.getElementById('audit-score').value = score || '';
  document.getElementById('audit-feedback').value = feedback || '';

  document.getElementById('audit-modal').style.display = 'flex';
}

function closeAuditModal() {
  document.getElementById('audit-modal').style.display = 'none';
}

async function handleSaveAuditReview(e) {
  e.preventDefault();

  const topicId = document.getElementById('audit-topic-id').value;
  const status = document.getElementById('audit-status').value;
  const scoreVal = document.getElementById('audit-score').value;
  const feedback = document.getElementById('audit-feedback').value;

  const score = scoreVal !== '' ? parseInt(scoreVal, 10) : null;

  try {
    await ApiClient.post('/learning/audits', {
      topic_id: topicId,
      status: status,
      score: score,
      feedback: feedback,
    });

    showToast('Audit review saved successfully!');
    closeAuditModal();
    loadLearningProgress(currentBatchFilter, currentTargetInternId);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function checkQuizAnswer(radio, correctAnswer, explanation, feedbackId) {
  const feedbackEl = document.getElementById(feedbackId);
  if (!feedbackEl) return;

  const selected = radio.value;
  const cleanCorrect = (correctAnswer || '').trim().toUpperCase();
  const isCorrect = cleanCorrect.startsWith(selected.toUpperCase()) || selected.toUpperCase() === cleanCorrect;

  feedbackEl.style.display = 'block';
  if (isCorrect) {
    feedbackEl.style.backgroundColor = 'rgba(16, 185, 129, 0.12)';
    feedbackEl.style.color = 'var(--accent-emerald)';
    feedbackEl.style.border = '1px solid rgba(16, 185, 129, 0.3)';
    feedbackEl.innerHTML = `<strong>✅ Chính xác! (Đáp án ${correctAnswer}):</strong> ${explanation}`;
  } else {
    feedbackEl.style.backgroundColor = 'rgba(244, 63, 94, 0.12)';
    feedbackEl.style.color = 'var(--accent-rose)';
    feedbackEl.style.border = '1px solid rgba(244, 63, 94, 0.3)';
    feedbackEl.innerHTML = `<strong>❌ Chưa đúng!</strong> Vui lòng chọn lại. <em>(Gợi ý: ${explanation})</em>`;
  }
}

