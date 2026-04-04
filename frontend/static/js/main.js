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


autoRetrieveToken().then(({ jwtToken, refreshToken }) => validateToken(jwtToken, refreshToken)).then(({token_expired, jwtToken, refreshToken}) => {
  console.log(`[Initialization] Token retrieval and validation complete. Token expired: ${token_expired}, JWT Token: ${jwtToken}, Refresh Token: ${refreshToken}`);
  // Retrieve Task List data
  getAllTaskList(jwtToken);
}).catch(err => {
  console.error('[Initialization] Error during token retrieval/validation:', err.message);
});



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
