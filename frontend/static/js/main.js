let jwtToken = '';
let refreshToken = '';

// Fetch token on page load
async function autoRetrieveToken() {
  try {
    const res = await fetch('/api/test/token', { method: 'POST' });
    const data = await res.json();
    const display = data.detail ?? data;
    jwtToken = display.jwt_token_value ? display.jwt_token_value.replace(/"/g, '') : '';
    refreshToken = display.refresh_token_value ? display.refresh_token_value.replace(/"/g, '') : '';
    console.log('[Page Load] JWT Token retrieved:', jwtToken);
    console.log('[Page Load] Refresh Token retrieved:', refreshToken);
    return { jwtToken, refreshToken };
  } catch (err) {
    console.error('[Page Load] Token retrieval failed:', err.message);
  }
}

// validate if token expires or not
async function validateToken(jwtToken, refreshToken) {
  if (!jwtToken) {
    console.warn('[Token Validation] No token available, skipping validation.');
    return;
  }
  try {
    const res = await fetch('/api/test/validate-token', {
      method: 'POST',
      headers: {
        'Authorization': `JWT ${jwtToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({refreshToken: refreshToken}),
    });
    const data = await res.json();
    console.log('[Token Validation] Response:', data);

    if (res.ok && data.data) {
      console.log('[Token Validation] Token is valid.');
    } else {
      console.warn('[Token Validation] Token is invalid or expired. Please retrieve a new token.');
    }

    token_expired = data.detail?.expired || data.data?.expired || false;
    jwtToken = data.data.new_jwt_token ? data.data.new_jwt_token.replace(/"/g, '') : '';
    refreshToken = data.data.new_refresh_token ? data.data.new_refresh_token.replace(/"/g, '') : '';
    console.log('[Token Validation] Token expired:', token_expired);
    console.log('[Token Validation] New JWT Token:', jwtToken);
    console.log('[Token Validation] New Refresh Token:', refreshToken);
    
    return {token_expired, jwtToken, refreshToken };
  } catch (err) {
    console.error('[Token Validation] Failed to validate token:', err.message);
  }
}

// Task List API testing
async function getAllTaskList(jwtToken) {
  if (!jwtToken) {
    console.warn('[Task List] No token available, skipping retrieval.');
    return;
  }
  try {
    const res = await fetch('/api/test/init-task-list', {
      method: 'POST',
      headers: {
        'Authorization': `JWT ${jwtToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({page: 1, page_size: 10, view_type: "available"}),
    });
    const data = await res.json();
    console.log('[Task List] Response:', data);

    if (res.ok && data.data) {
      console.log('[Task List] Task list retrieved successfully.');
    } else {
      console.warn('[Task List] Failed to retrieve task list. Please check your token.');

    }

    token_expired = data.detail?.expired || data.data?.expired || false;
    jwtToken = data.data.new_jwt_token ? data.data.new_jwt_token.replace(/"/g, '') : '';
    refreshToken = data.data.new_refresh_token ? data.data.new_refresh_token.replace(/"/g, '') : '';
    console.log('[Task List] Token expired:', token_expired);
    console.log('[Task List] New JWT Token:', jwtToken);
    console.log('[Task List] New Refresh Token:', refreshToken);
    
    return {token_expired, jwtToken, refreshToken };
  } catch (err) {
    console.error('[Task List] Failed to retrieve task list:', err.message);
  }
}


// autoRetrieveToken().then(({ jwtToken, refreshToken }) => validateToken(jwtToken, refreshToken)).then(({token_expired, jwtToken, refreshToken}) => {
//   console.log(`[Initialization] Token retrieval and validation complete. Token expired: ${token_expired}, JWT Token: ${jwtToken}, Refresh Token: ${refreshToken}`);
//   // Retrieve Task List data
//   getAllTaskList(jwtToken);
// }).catch(err => {
//   console.error('[Initialization] Error during token retrieval/validation:', err.message);
// });



//////////////////////////////// html elements and event listeners for testing API endpoints //////////////////


// Token Auto Retrieve
const tokenAutoRetrieveBtn = document.getElementById('btn-token-auto-retrieve');
const tokenAutoRetrieveResult = document.getElementById('token-auto-retrieve-result');
if (tokenAutoRetrieveBtn) {
  tokenAutoRetrieveBtn.addEventListener('click', async () => {
    tokenAutoRetrieveBtn.disabled = true;
    tokenAutoRetrieveBtn.textContent = 'Running…';
    tokenAutoRetrieveResult.textContent = '';
    tokenAutoRetrieveResult.className = 'test-result';
    try {
      // Token retrieval is handled server-side via Chrome DevTools Protocol (CDP).
      // Chrome must be running with: --remote-debugging-port=9222
      const res = await fetch('/api/test/token', { method: 'POST' });
      const data = await res.json();
      // FastAPI errors use "detail"; success responses use "success"
      // If retry:true the tab was just opened – show as a warning, not an error      
      const display = data.detail ?? data;

      console.log('[Token Auto Retrieve] Response:', display);

      jwtToken = display.jwt_token_value ? display.jwt_token_value.replace(/"/g, '') : '';
      refreshToken = display.refresh_token_value ? display.refresh_token_value.replace(/"/g, '') : '';
      console.log('[Token Auto Retrieve] JWT Token:', jwtToken);
      console.log('[Token Auto Retrieve] Refresh Token:', refreshToken);

      const text = typeof display === 'string' ? display : JSON.stringify(display, null, 2);
      tokenAutoRetrieveResult.textContent = text;
      if (data.retry) {
        tokenAutoRetrieveResult.classList.add('test-result--warning');
      } else {
        tokenAutoRetrieveResult.classList.add(res.ok && data.success ? 'test-result--success' : 'test-result--error');
      }
    } catch (err) {
      tokenAutoRetrieveResult.textContent = 'Error: ' + err.message;
      tokenAutoRetrieveResult.classList.add('test-result--error');
    } finally {
      tokenAutoRetrieveBtn.disabled = false;
      tokenAutoRetrieveBtn.textContent = 'Token Auto Retrieve';
    }
  });
}

// API Task List Test
const apiTaskListTestBtn = document.getElementById('btn-api-task-list-test');
const apiTaskListTestResult = document.getElementById('api-task-list-test-result');
if (apiTaskListTestBtn) {
  apiTaskListTestBtn.addEventListener('click', async () => {
    apiTaskListTestBtn.disabled = true;
    apiTaskListTestBtn.textContent = 'Running…';
    apiTaskListTestResult.textContent = '';
    apiTaskListTestResult.className = 'test-result';
    try {
      const res = await fetch('/api/test/init-task-list', {
        method: 'POST',
        headers: {
          'Authorization': `JWT ${jwtToken}`,
          'Content-Type': 'application/json',
        },
          
      });

      const data = await res.json();

      apiTaskListTestResult.textContent = JSON.stringify(data, null, 2);
      apiTaskListTestResult.classList.add(res.ok && data.success ? 'test-result--success' : 'test-result--error');
    } catch (err) {
      apiTaskListTestResult.textContent = 'Error: ' + err.message;
      apiTaskListTestResult.classList.add('test-result--error');
    } finally {
      apiTaskListTestBtn.disabled = false;
      apiTaskListTestBtn.textContent = 'API Task List Test';
    }
  });
}

// API Assign Task Test
const apiAssignTaskBtn = document.getElementById('btn-api-assign-task');
const apiAssignTaskResult = document.getElementById('api-assign-task-result');
if (apiAssignTaskBtn) {
  apiAssignTaskBtn.addEventListener('click', async () => {
    apiAssignTaskBtn.disabled = true;
    apiAssignTaskBtn.textContent = 'Running…';
    apiAssignTaskResult.textContent = '';
    apiAssignTaskResult.className = 'test-result';
    try {
      const res = await fetch('/api/test/assign-task', {
        method: 'POST',
        headers: {
          'Authorization': `JWT ${jwtToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({task_id: 1927}),
      });

      const data = await res.json();

      apiAssignTaskResult.textContent = JSON.stringify(data, null, 2);
      apiAssignTaskResult.classList.add(res.ok && data.success ? 'test-result--success' : 'test-result--error');
    } catch (err) {
      apiAssignTaskResult.textContent = 'Error: ' + err.message;
      apiAssignTaskResult.classList.add('test-result--error');
    } finally {
      apiAssignTaskBtn.disabled = false;
      apiAssignTaskBtn.textContent = 'API Assign Task Test';
    }
  });
}

// API Abandon Task Test
const apiAbandonTaskBtn = document.getElementById('btn-api-abandon-task');
const apiAbandonTaskResult = document.getElementById('api-abandon-task-result');
if (apiAbandonTaskBtn) {
  apiAbandonTaskBtn.addEventListener('click', async () => {
    apiAbandonTaskBtn.disabled = true;
    apiAbandonTaskBtn.textContent = 'Running…';
    apiAbandonTaskResult.textContent = '';
    apiAbandonTaskResult.className = 'test-result';
    try {
      const res = await fetch('/api/test/abandon-task', {
        method: 'POST',
        headers: {
          'Authorization': `JWT ${jwtToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({task_id: 1927}),
      });

      const data = await res.json();

      apiAbandonTaskResult.textContent = JSON.stringify(data, null, 2);
      apiAbandonTaskResult.classList.add(res.ok && data.success ? 'test-result--success' : 'test-result--error');
    } catch (err) {
      apiAbandonTaskResult.textContent = 'Error: ' + err.message;
      apiAbandonTaskResult.classList.add('test-result--error');
    } finally {
      apiAbandonTaskBtn.disabled = false;
      apiAbandonTaskBtn.textContent = 'API Abandon Task Test';
    }
  });
}

// API Update Test
const apiUpdateTestBtn = document.getElementById('btn-api-update-test');
if (apiUpdateTestBtn) {
  apiUpdateTestBtn.addEventListener('click', async () => {
    apiUpdateTestBtn.disabled = true;
    apiUpdateTestBtn.textContent = 'Running…';
    try {
      const res = await fetch('/api/test/update', { method: 'POST' });
      const data = await res.json();
      alert('API Update Test result:\n' + JSON.stringify(data, null, 2));
    } catch (err) {
      alert('API Update Test failed: ' + err.message);
    } finally {
      apiUpdateTestBtn.disabled = false;
      apiUpdateTestBtn.textContent = 'API Update Test';
    }
  });
}

// Auto-dismiss flash alerts after 4 seconds
document.querySelectorAll(".alert").forEach((el) => {
  setTimeout(() => {
    el.style.transition = "opacity 0.5s";
    el.style.opacity = "0";
    setTimeout(() => el.remove(), 500);
  }, 4000);
});

// ── Next Task and Details ────────────────────────────────────────────────────
// Tracks which page of the task list has already been loaded.
// Page 1 is rendered server-side by Flask/Jinja2 on initial page load.
let currentTaskPage = 1;

/**
 * Called by the "Next Task and Details" navbar button.
 *
 * How it works:
 *   1. Increments currentTaskPage and POSTs to Flask /api/next-task.
 *   2. Flask proxies to FastAPI /api/test/init-task-list (page N, page_size=1),
 *      which already enriches the TaskInfo with full company + URL details
 *      via _enrich_task_with_details().
 *   3. The JSON response (list of TaskInfo dicts) is passed to buildTaskCard()
 *      which builds equivalent DOM to the Jinja2 task-card block.
 *   4. The new card is appended to .dash-container and scrolled into view.
 *
 * Why JS can't just update the Jinja2 `tasks` variable:
 *   Jinja2 renders {{ task.id }}, {{ company.name }} etc. once on the server
 *   before the page reaches the browser.  After that the Python variable is
 *   gone – we must build the DOM dynamically from the API JSON.
 */
async function getNextTaskAndDetails() {
  currentTaskPage += 1;

  try {
    const res = await fetch('/api/next-task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page: currentTaskPage }),
    });
    const payload = await res.json();

    if (!res.ok || !payload.success) {
      alert('Failed to load next task: ' + (payload.error || 'Unknown error'));
      currentTaskPage -= 1; // roll back on failure
      return;
    }

    const tasks = payload.data;
    if (!tasks || tasks.length === 0) {
      alert('No more tasks available.');
      currentTaskPage -= 1;
      return;
    }

    const container = document.querySelector('.dash-container');
    if (!container) return;

    tasks.forEach(task => {
      container.appendChild(buildTaskCard(task));
    });

    // Scroll to the first newly added card
    container.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (err) {
    alert('Error fetching next task: ' + err.message);
    currentTaskPage -= 1;
  }
}

// ── DOM builders ─────────────────────────────────────────────────────────────

/**
 * Build a .task-card element from a TaskInfo dict.
 * Mirrors the Jinja2 task-card block in task_dashboard.html.
 *
 * @param {Object} task - TaskInfo dict returned by /api/next-task
 * @returns {HTMLElement}
 */
function buildTaskCard(task) {
  // Append "-dyn" so the id never collides with server-rendered cards on the same page
  const taskBodyId = `task-body-${task.id}-dyn`;
  const progressPct = ((task.progress || 0) * 100).toFixed(1);
  const statusSlug  = (task.status   || '').toLowerCase().replace(/ /g, '-');
  const prioritySlug = (task.priority || '').toLowerCase();

  const card = document.createElement('div');
  card.className = 'task-card';

  // Header
  const header = document.createElement('div');
  header.className = 'task-header';
  header.setAttribute('onclick', `toggleSection('${taskBodyId}', this)`);
  header.innerHTML = `
    <div class="task-title-row">
      <span class="task-id" data-tooltip="task_id: Unique identifier for this task">
        Task_Id: ${_esc(String(task.id))}
      </span>
    </div>
    <br/>
    <div class="task-title-row">
      <span class="task-name" data-tooltip="task_name: The display name of this task">
        ${_esc(task.task_name)}
      </span>
      <span class="badge badge--${statusSlug}"
            data-tooltip="status: Current processing state of the task">
        ${_esc(task.status)}
      </span>
      <span class="badge badge--priority-${prioritySlug}"
            data-tooltip="priority: Urgency level — High / Medium / Low">
        ${_esc(task.priority)}
      </span>
      <span class="badge badge--type"
            data-tooltip="task_type: Category or type of work for this task">
        ${_esc(task.task_type)}
      </span>
    </div>
    <div class="task-meta-row">
      <span class="meta-item"
            data-tooltip="deadline: Target date by which this task must be completed">
        🗓 Deadline: <strong>${_esc(task.deadline)}</strong>
      </span>
      <span class="meta-item"
            data-tooltip="completed_companies / total_companies: Number of companies finished vs. total assigned">
        🏢 Companies: <strong>${task.completed_companies} / ${task.total_companies}</strong>
      </span>
      <span class="toggle-icon">▼</span>
    </div>
    <div class="progress-bar-wrap"
         data-tooltip="progress: Ratio of completed_companies ÷ total_companies (0.0 – 1.0)">
      <div class="progress-bar-fill" style="width:${progressPct}%"></div>
    </div>
    <div class="progress-label">${progressPct}% complete</div>
  `;

  // Body (collapsible)
  const body = document.createElement('div');
  body.id = taskBodyId;
  body.className = 'task-body';

  if (task.task_description) {
    const desc = document.createElement('div');
    desc.className = 'task-desc';
    desc.setAttribute('data-tooltip',
      'task_description: Full description and objectives for this task');
    desc.innerHTML = task.task_description; // server-supplied HTML, trusted
    body.appendChild(desc);
  }

  const companies = task.companyInfos || [];
  const sectionLabel = document.createElement('div');
  sectionLabel.className = 'section-label';
  sectionLabel.textContent = `Companies (${companies.length})`;
  body.appendChild(sectionLabel);

  if (companies.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty';
    empty.style.padding = '0.5rem 1rem';
    empty.textContent = 'No companies linked to this task.';
    body.appendChild(empty);
  } else {
    companies.forEach((company, idx) =>
      body.appendChild(buildCompanyCard(company, task.id, idx + 1))
    );
  }

  card.appendChild(header);
  card.appendChild(body);
  return card;
}

/**
 * Build a .company-card element from a CompanyInfo dict.
 * Mirrors the Jinja2 company-card block in task_dashboard.html.
 *
 * @param {Object} company - CompanyInfo dict
 * @param {number} taskId  - parent task id (for unique DOM ids)
 * @param {number} index   - 1-based loop index
 * @returns {HTMLElement}
 */
function buildCompanyCard(company, taskId, index) {
  const bodyId    = `company-body-${taskId}-${index}-dyn`;
  const statusSlug = (company.status || '').toLowerCase().replace(/ /g, '-');

  const card = document.createElement('div');
  card.className = 'company-card';

  // Company header
  const header = document.createElement('div');
  header.className = 'company-header';
  header.setAttribute('onclick', `toggleSection('${bodyId}', this)`);
  header.innerHTML = `
    <div class="company-title-row">
      <span class="company-index" data-tooltip="company index">Index: ${index}</span>
      <span class="orbit-entity-id"
            data-tooltip="orbit_entity_id: Unique identifier for this entity">
        Entity_Id: ${_esc(company.orbit_entity_id)}
      </span>
    </div>
    <br/>
    <div class="company-title-row">
      <span class="company-name"
            data-tooltip="name: Short display name for this company">
        ${_esc(company.name)}
      </span>
      <span class="company-entity"
            data-tooltip="entity_name: Full registered legal entity name">
        ${_esc(company.entity_name)}
      </span>
      <span class="badge badge--${statusSlug}"
            data-tooltip="status: Current data-collection status for this company">
        ${_esc(company.status)}
      </span>
    </div>
    <div class="company-meta-row">
      <span class="meta-item"
            data-tooltip="current_step: Active workflow step this company is currently in">
        Step: <strong>${_esc(company.current_step)}</strong>
      </span>
      ${company.completed_at ? `
      <span class="meta-item"
            data-tooltip="completed_at: Timestamp when data collection was finished">
        Completed: <strong>${_esc(company.completed_at)}</strong>
      </span>` : ''}
      <span class="toggle-icon">▼</span>
    </div>
  `;

  // Company body (collapsible)
  const body = document.createElement('div');
  body.id = bodyId;
  body.className = 'company-body';

  // Detail grid
  const grid = document.createElement('div');
  grid.className = 'detail-grid';
  const rejectionClass = company.review_rejection_reason ? 'detail-value--warn' : '';
  grid.innerHTML = `
    <div class="detail-item"
         data-tooltip="orbit_entity_id: Unique identifier for this entity on the Orbit platform">
      <span class="detail-label">Orbit Entity ID</span>
      <span class="detail-value">${_esc(company.orbit_entity_id) || '—'}</span>
    </div>
    <div class="detail-item" data-tooltip="notes: Internal notes specific to this company entry">
      <span class="detail-label">Notes</span>
      <div class="detail-value">${company.notes || '—'}</div>
    </div>
    <div class="detail-item"
         data-tooltip="shared_notes: Notes visible to all team members working on this task">
      <span class="detail-label">Shared Notes</span>
      <div class="detail-value">${company.shared_notes || '—'}</div>
    </div>
    <div class="detail-item"
         data-tooltip="review_rejection_reason: Explanation provided when a reviewer rejected this company's submission">
      <span class="detail-label">Review Rejection Reason</span>
      <div class="detail-value ${rejectionClass}">
        ${company.review_rejection_reason || '—'}
      </div>
    </div>
  `;
  body.appendChild(grid);

  // Missing reports
  const missing = company.missing_reports || [];
  if (missing.length > 0) {
    const missingDiv = document.createElement('div');
    missingDiv.className = 'missing-reports';
    missingDiv.setAttribute('data-tooltip',
      'missing_reports: List of required report documents not yet collected for this company');
    missingDiv.innerHTML = `
      <span class="detail-label">Missing Reports</span>
      <div class="tag-list">
        ${missing.map((r, i) =>
          `<span class="tag tag--warn"
                 data-tooltip="missing_reports[${i}]: '${_esc(r)}' has not been collected yet">
             ${_esc(r)}
           </span>`
        ).join('')}
      </div>`;
    body.appendChild(missingDiv);
  }

  // URLs
  const urls = company.urlInfos || [];
  if (urls.length > 0) {
    const urlSection = document.createElement('div');
    urlSection.className = 'url-section';
    urlSection.innerHTML = `
      <span class="detail-label"
            data-tooltip="urlInfos: Collection of source URLs linked to this company">
        URLs (${urls.length})
      </span>
      <table class="url-table">
        <thead>
          <tr>
            <th data-tooltip="URLInfo.type: Category of this URL resource">Type</th>
            <th data-tooltip="URLInfo.url: Direct link to the document or resource">URL</th>
            <th data-tooltip="URLInfo.comment: Optional human-readable note about this URL">Comment</th>
          </tr>
        </thead>
        <tbody>
          ${urls.map(u => {
            const displayUrl = u.url.length > 60 ? u.url.slice(0, 60) + '\u2026' : u.url;
            return `
            <tr>
              <td>
                <span class="tag tag--url" data-tooltip="type: ${_esc(u.type)}">
                  ${_esc(u.type)}
                </span>
              </td>
              <td>
                <a href="${_esc(u.url)}" target="_blank" rel="noopener" class="url-link"
                   data-tooltip="url: Full source URL — click to open in new tab">
                  ${_esc(displayUrl)}
                </a>
              </td>
              <td class="url-comment"
                  data-tooltip="comment: ${_esc(u.comment || 'No comment provided')}">
                ${_esc(u.comment) || '—'}
              </td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>`;
    body.appendChild(urlSection);
  } else {
    const noUrl = document.createElement('p');
    noUrl.className = 'empty';
    noUrl.style.fontSize = '0.85rem';
    noUrl.style.padding = '0.25rem 0';
    noUrl.textContent = 'No URLs linked.';
    body.appendChild(noUrl);
  }

  card.appendChild(header);
  card.appendChild(body);
  return card;
}

/**
 * Escape a value for safe insertion into HTML text or attribute contexts.
 * Prevents XSS from API data injected via innerHTML / template literals.
 */
function _esc(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
