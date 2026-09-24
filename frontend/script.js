/**
 * SkillSetu / SkillSync Frontend Search, Telemetry & Export Module
 * - Live PyTorch NLP Vector Search with 65s cold-start timeout
 * - Dynamic skill telemetry progress bar rendering (NCS Demand vs Mahaswayam Supply)
 * - PDF export for District Training Plans using html2pdf.js
 */

const BASE_URL = "https://abhishekaj819-collab--skillsync-api-serve.modal.run";

// 1. Fetch Job Roles & SWAYAM Recommendations with 65s AbortController Timeout
async function fetchSearchResults(query) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 65000);

  try {
    const res = await fetch(`${BASE_URL}/api/search`, {
      method: 'POST',
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        query: query || 'Data Analyst',
        top_k: 5
      }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      const errDetail = await res.text();
      throw new Error(`HTTP ${res.status}: ${errDetail || res.statusText}`);
    }
    const data = await res.json();
    return { success: true, data };
  } catch (err) {
    clearTimeout(timeoutId);
    const isTimeout = err.name === 'AbortError' || err.message.includes('timeout') || err.message.includes('aborted');
    const is500 = err.message.includes('500');
    if (typeof showToast === 'function') {
      showToast(isTimeout ? 'Backend timeout: server may be waking up.' : `Search error: ${err.message}`, 'warning');
    }
    return {
      success: false,
      isTimeout,
      is500,
      error: err.message,
      data: null
    };
  }
}

// 2. Render Search Error & Interactive Retry Button
function renderSearchError(container, queryText, isTimeoutOr500 = false) {
  if (!container) return;
  container.innerHTML = '';

  const errorCard = document.createElement('div');
  errorCard.className = 'search-error-box glass-card';
  errorCard.style.cssText = 'display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2.5rem 1.5rem; text-align: center; gap: 1rem; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: var(--radius-md);';

  errorCard.innerHTML = `
    <div style="width: 48px; height: 48px; border-radius: 50%; background: rgba(239, 68, 68, 0.15); display: flex; align-items: center; justify-content: center;">
      <svg style="width: 24px; height: 24px; color: var(--accent-red);" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    </div>
    <div>
      <h4 style="font-size: 1.05rem; color: var(--text-main); margin-bottom: 0.35rem; font-weight: 600;">
        Network timeout or server is asleep.
      </h4>
      <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 460px; line-height: 1.5; margin: 0 auto;">
        The backend service on Render may be waking up from inactivity (which takes up to 50 seconds on the free tier), or the request encountered a timeout. Click below to retry.
      </p>
    </div>
    <button id="btn-retry-search" class="btn-filter" style="background: var(--accent-blue); border-color: var(--accent-blue); padding: 0.65rem 1.5rem; font-size: 0.875rem; cursor: pointer; display: inline-flex; align-items: center; gap: 0.5rem; color: #fff; font-weight: 500; border-radius: var(--radius-sm); margin-top: 0.25rem;">
      <svg style="width: 15px; height: 15px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="23 4 23 10 17 10"/>
        <polyline points="1 20 1 14 7 14"/>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
      </svg>
      Retry Search
    </button>
  `;

  container.appendChild(errorCard);

  const retryBtn = errorCard.querySelector('#btn-retry-search');
  if (retryBtn) {
    retryBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (typeof executeLMIQuery === 'function') {
        executeLMIQuery(queryText, false);
      }
    });
  }
}

// 3. Render Granular Skill Bars (NCS Demand vs Mahaswayam Supply)
function renderSkillBars(skillsOrRole) {
  const container = document.getElementById('skill-bars-container') || 
                    document.querySelector('#view-market-demand .skill-bars-list');
  if (!container) return;
  container.innerHTML = '';

  let skills = [];
  if (Array.isArray(skillsOrRole)) {
    skills = skillsOrRole;
  } else if (skillsOrRole && Array.isArray(skillsOrRole.skills)) {
    skills = skillsOrRole.skills;
  }

  if (!skills || skills.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem; padding: 1rem;">No matching skill telemetry found.</div>';
    return;
  }

  skills.forEach(skill => {
    const demand = typeof skill.demand === 'number' ? skill.demand : (typeof skill.demand_score === 'number' ? skill.demand_score : 80);
    const supply = typeof skill.supply === 'number' ? skill.supply : (typeof skill.supply_score === 'number' ? skill.supply_score : 50);
    const deficit = typeof skill.deficit_score === 'number' ? skill.deficit_score : (demand - supply);
    const isShortage = deficit > 0;
    const deltaText = isShortage 
      ? `-${deficit}% Shortage` 
      : `+${Math.abs(deficit)}% Surplus`;
    const deltaClass = isShortage ? 'shortage' : 'surplus';

    const row = document.createElement('div');
    row.className = 'skill-row';
    row.innerHTML = `
      <div class="skill-row-meta">
        <span class="skill-name">
          ${skill.name}
          <span class="skill-esco-tag">ESCO: ${skill.esco_code || '2512.1'}</span>
        </span>
        <span class="skill-delta-tag ${deltaClass}">${deltaText}</span>
      </div>
      <div class="progress-bar-container">
        <div class="bar-track">
          <div class="bar-fill demand" style="width: ${demand}%;" title="Demand (NCS): ${demand}%"></div>
        </div>
        <div class="bar-track">
          <div class="bar-fill supply" style="width: ${supply}%;" title="Supply (Mahaswayam): ${supply}%"></div>
        </div>
      </div>
      <div class="bar-numeric-overlay">
        <span>Demand (NCS): ${demand}/100</span>
        <span>Supply (Mahaswayam): ${supply}/100</span>
      </div>
    `;
    container.appendChild(row);
  });
}

// 4. District Plans Real PDF Exporting using html2pdf.js
function exportDistrictPlanPDF() {
  const btn = document.getElementById('btn-export-district-pdf');
  const originalText = btn ? btn.innerHTML : 'Export District Plan (PDF)';
  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Exporting...';
  }

  const targetEl = document.getElementById('view-district-plans');
  if (!targetEl) {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
    return;
  }

  if (typeof html2pdf !== 'undefined') {
    const opt = {
      margin: 1,
      filename: 'District_Training_Plan.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    const pdfPromise = html2pdf().set(opt).from(targetEl).save();
    if (pdfPromise && typeof pdfPromise.then === 'function') {
      pdfPromise
        .then(() => {
          if (typeof showToast === 'function') {
            showToast('District Training Plan PDF exported successfully!', 'success');
          }
        })
        .catch((err) => {
          console.error('PDF export error:', err);
          if (typeof showToast === 'function') {
            showToast('PDF export failed. Please try again.', 'error');
          }
        })
        .finally(() => {
          if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
          }
        });
    } else {
      setTimeout(() => {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = originalText;
        }
      }, 1200);
    }
  } else {
    console.warn('html2pdf library not loaded.');
    if (typeof showToast === 'function') {
      showToast('html2pdf library not loaded yet.', 'warning');
    }
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }
}

// Wire up event listeners on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  const exportBtn = document.getElementById('btn-export-district-pdf');
  if (exportBtn) {
    exportBtn.addEventListener('click', (e) => {
      e.preventDefault();
      exportDistrictPlanPDF();
    });
  }
});

// Expose functions on window
window.fetchSearchResults = fetchSearchResults;
window.renderSearchError = renderSearchError;
window.renderSkillBars = renderSkillBars;
window.exportDistrictPlanPDF = exportDistrictPlanPDF;
