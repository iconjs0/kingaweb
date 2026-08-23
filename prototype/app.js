const form = document.querySelector('#scan-form');
const statusNode = document.querySelector('#form-status');
const results = document.querySelector('#results');

const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = form.querySelector('button');
  const domain = form.domain.value.trim();
  button.disabled = true;
  button.textContent = 'Checking…';
  statusNode.textContent = 'KingaWeb is safely reviewing public security signals…';
  results.hidden = true;

  try {
    const response = await fetch('/api/scan', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({domain})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'The check could not be completed.');
    renderResults(data);
    statusNode.textContent = 'Check complete.';
  } catch (error) {
    statusNode.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = 'Check security';
  }
});

function renderResults(data) {
  const checks = data.checks.map(check => `
    <article class="check">
      <h3>${escapeHtml(check.name)} <span class="${escapeHtml(check.status)}">${escapeHtml(check.label)}</span></h3>
      <p>${escapeHtml(check.detail)}</p>
    </article>`).join('');
  results.innerHTML = `
    <div class="results-head">
      <div><p class="eyebrow"><span></span> Security snapshot</p><h2>${escapeHtml(data.host)}</h2></div>
      <div><span class="grade">${data.score}/100</span><br><small>${escapeHtml(data.summary)}</small></div>
    </div>
    <div class="checks">${checks}</div>`;
  results.hidden = false;
  results.scrollIntoView({behavior: 'smooth', block: 'start'});
}
