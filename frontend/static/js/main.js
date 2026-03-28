let jwtToken = '';


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

      jwtToken = display.token ? display.token.replace(/"/g, '') : '';
       console.log('[Token Auto Retrieve] JWT Token:', jwtToken);

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
      const res = await fetch('/api/test/task-list', {
        method: 'POST',
        headers: {
          'Authorization': `JWT ${jwtToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({page: 1, page_size: 12, view_type: "available"}),
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
