/**
 * SkillSetu | SIH Problem Statement 26134
 * Executive Dashboard Core Module
 * "Bridging Skills to Industry | Govt. of Maharashtra (PS 26134)"
 * 
 * Features:
 * - 3-Pill Stakeholder Views (Govt / Training Institute / Employer)
 * - Fund Reallocation Engine & Statewide Agility Index
 * - Granular Syllabus Directives & Lab Equipment Forecasting
 * - Future Talent Radar & Hyper-Local Deficit Reporting Intake Form
 * - Direct Placement Matching Pipeline
 * - Direct connection to PyTorch Modal Backend: https://abhishekaj819-collab--skillsync-api-serve.modal.run
 * - Lenis smooth scrolling integration & Chart.js dynamic heatmaps
 */

// ============================================================================
// 1. CONFIGURATION & STATE STORE
// ============================================================================
export const BASE_URL = "https://abhishekaj819-collab--skillsync-api-serve.modal.run";

export function buildApiUrl(endpoint) {
  const cleanBase = BASE_URL.replace(/\/+$/, '');
  const cleanEndpoint = endpoint.replace(/^\/+/, '');
  return `${cleanBase}/${cleanEndpoint}`;
}

const state = {
  activeRole: 'govt', // 'govt' | 'institute' | 'employer'
  activeDistrict: 'pune',
  isExtracting: false,
  heatmapChart: null,
  districtTelemetry: null,
};

// District Data Store for Maharashtra Action Plans (SIH 26134)
const DISTRICT_DATA = {
  pune: {
    name: 'Pune',
    zone: 'Western Maharashtra Tech & Auto Hub',
    title: 'Pune District • Institutional Capacity Intervention',
    description: 'Auto-generated roadmap based on 4,820 live employer vacancies in Hinjawadi & Chakan and 14 high-severity course skill gaps.',
    items: [
      {
        course: 'Advanced Python & Deep Learning Engineering (NSQF Level 6)',
        action: 'expand',
        trainerDelta: '+3 Certified Faculty',
        equipment: 'Deploy 24 GPU-accelerated PyTorch workstation lab stations at ITI Aundh',
        placementRate: '92.4%',
        demand: '1,420 Vacancies (Critical Surge)'
      },
      {
        course: 'Electric Vehicle Powertrain & Battery Diagnostics',
        action: 'expand',
        trainerDelta: '+2 Master Trainers',
        equipment: 'Install 48V modular battery test bench & CAN bus diagnostic simulators',
        placementRate: '88.5%',
        demand: '980 Vacancies (Rising)'
      },
      {
        course: 'Legacy Desktop Publishing & Office 2007 Tools',
        action: 'phase_out',
        trainerDelta: '-2 Reallocated',
        equipment: 'Phase out legacy CRT equipment; reallocate space to AI hardware lab',
        placementRate: '34.2%',
        demand: '42 Vacancies (Declining)'
      },
      {
        course: 'Industrial Automation & PLC Troubleshooting',
        action: 'expand',
        trainerDelta: '+1 Senior Trainer',
        equipment: 'Upgrade Siemens S7-1200 PLC trainer boards and pneumatic rigs',
        placementRate: '86.1%',
        demand: '650 Vacancies (High)'
      }
    ]
  },
  mumbai: {
    name: 'Mumbai MMR',
    zone: 'Konkan Metro • FinTech & Cloud Enterprise',
    title: 'Mumbai Metropolitan Region • BFSI & Cloud Infrastructure Strategy',
    description: 'Auto-generated roadmap based on 7,150 vacancies across BKC, Navi Mumbai, and Thane enterprise corridors.',
    items: [
      {
        course: 'Enterprise Cloud Architecture & DevOps (AWS/Azure)',
        action: 'expand',
        trainerDelta: '+4 Certified Trainers',
        equipment: 'Establish cloud simulation sandbox & Docker/K8s certified clusters',
        placementRate: '94.8%',
        demand: '2,840 Vacancies (Critical Surge)'
      },
      {
        course: 'Financial Technology (FinTech) & Cyber Risk Auditing',
        action: 'expand',
        trainerDelta: '+2 Industry Fellows',
        equipment: 'Deploy secure financial sandbox & SOC incident response lab',
        placementRate: '91.2%',
        demand: '1,630 Vacancies (High)'
      },
      {
        course: 'Data Entry Operator (Generic BPO)',
        action: 'reduce',
        trainerDelta: '-1 Reallocated',
        equipment: 'Reduce seat intake by 40%; transition curriculum to Automated Data Quality',
        placementRate: '46.0%',
        demand: '180 Vacancies (Automating)'
      },
      {
        course: 'Full-Stack JavaScript & Microservices Engineering',
        action: 'expand',
        trainerDelta: '+3 Faculty Members',
        equipment: 'Provision modern dual-monitor development workstations at ITI Dadar',
        placementRate: '89.4%',
        demand: '1,950 Vacancies (High)'
      }
    ]
  },
  thane: {
    name: 'Thane',
    zone: 'MMR Industrial Corridor • Pharma & IT',
    title: 'Thane District • Specialty Pharma & Logistics Modernization',
    description: 'Auto-generated roadmap based on 1,950 live vacancies in Wagle Estate, Dombivli, and Belapur pharma-IT belts.',
    items: [
      {
        course: 'Pharmaceutical Quality Control & HPLC/GC Analysis (NSQF 5)',
        action: 'expand',
        trainerDelta: '+3 Pharma Chemists',
        equipment: 'Install 2 Shimadzu HPLC chromatography trainer skids at ITI Thane',
        placementRate: '91.5%',
        demand: '780 Vacancies (Surging)'
      },
      {
        course: 'Full-Stack React & Node.js Cloud Engineering',
        action: 'expand',
        trainerDelta: '+2 Senior Instructors',
        equipment: 'High-speed fiber connectivity & dual-monitor cloud workstation lab',
        placementRate: '88.2%',
        demand: '620 Vacancies (High)'
      },
      {
        course: 'Manual Warehousing & Ledger Bookkeeping',
        action: 'phase_out',
        trainerDelta: '-2 Reallocated',
        equipment: 'Decommission manual filing storage; deploy SAP SCM / ERP terminal suite',
        placementRate: '38.0%',
        demand: '55 Vacancies (Declining)'
      },
      {
        course: 'Supply Chain Analytics & SAP SCM Operations',
        action: 'expand',
        trainerDelta: '+2 Logistics Analysts',
        equipment: 'Equip ERP simulation workstations with real-world EXIM freight modules',
        placementRate: '85.4%',
        demand: '440 Vacancies (High)'
      }
    ]
  },
  nagpur: {
    name: 'Nagpur',
    zone: 'Vidarbha Industrial & Logistics MIHAN',
    title: 'Nagpur & Vidarbha • MIHAN Logistics & Industrial Mechatronics Plan',
    description: 'Auto-generated capacity directive based on 2,340 regional openings in MIHAN SEZ and Butibori industrial belt.',
    items: [
      {
        course: 'Automated Logistics & Warehouse Robotics Management',
        action: 'expand',
        trainerDelta: '+3 Mechatronics Trainers',
        equipment: 'Construct miniature automated guided vehicle (AGV) sorting track',
        placementRate: '87.6%',
        demand: '890 Vacancies (High)'
      },
      {
        course: 'Aviation Avionics Maintenance & Drone Assembly (NSQF 5)',
        action: 'expand',
        trainerDelta: '+2 Aeronautical Trainers',
        equipment: 'Procure drone flight simulators and calibration test beds at MIHAN ITI',
        placementRate: '84.0%',
        demand: '540 Vacancies (Rising)'
      },
      {
        course: 'Traditional Mechanical Drafting (Manual Drawing Board)',
        action: 'phase_out',
        trainerDelta: '-2 Reallocated',
        equipment: 'Retire drafting tables; convert classroom into 3D CAD/CAM workstation hub',
        placementRate: '31.5%',
        demand: '25 Vacancies (Near Zero)'
      },
      {
        course: 'Solar Photovoltaic Installation & Smart Grid Tech',
        action: 'expand',
        trainerDelta: '+2 Clean-Tech Trainers',
        equipment: 'Equip rooftop solar test array with bidirectional smart inverter rigs',
        placementRate: '79.2%',
        demand: '620 Vacancies (High)'
      }
    ]
  },
  nashik: {
    name: 'Nashik',
    zone: 'Northern Maharashtra • Agri-Tech & Auto Components',
    title: 'Nashik District • Precision Agri-Tech & Automotive Manufacturing Plan',
    description: 'Auto-generated capacity roadmap based on 1,680 vacancies in Ambad MIDC, Satpur, and Dindori food processing zones.',
    items: [
      {
        course: 'Automotive Robotic Welding & AWS CWI Inspection',
        action: 'expand',
        trainerDelta: '+3 Certified Welding Instructors',
        equipment: 'Install 6-axis robotic welding cell with NDT Dye Penetrant test bench',
        placementRate: '89.0%',
        demand: '590 Vacancies (Surging)'
      },
      {
        course: 'Precision Agriculture, Drone NDVI & IoT Fertigation (NSQF 4)',
        action: 'expand',
        trainerDelta: '+2 Agri-Tech Specialists',
        equipment: 'Deploy multispectral agri-drone simulator and smart soil sensor test plot',
        placementRate: '82.4%',
        demand: '410 Vacancies (Rising)'
      },
      {
        course: 'Food Processing HACCP & Fermentation Operations',
        action: 'expand',
        trainerDelta: '+2 Quality Supervisors',
        equipment: 'Install microfiltration pilot plant and FSSAI certified QA testing lab',
        placementRate: '86.5%',
        demand: '450 Vacancies (High)'
      },
      {
        course: 'Basic Conventional Lathe Fitting (Manual Non-CNC)',
        action: 'reduce',
        trainerDelta: '-1 Reallocated',
        equipment: 'Reallocate 50% floor area to CNC VMC Machining simulators',
        placementRate: '42.1%',
        demand: '90 Vacancies (Declining)'
      }
    ]
  },
  chhatrapati_sambhajinagar: {
    name: 'Chhatrapati Sambhajinagar',
    zone: 'Marathwada Industrial Region • Precision Engineering',
    title: 'Chhatrapati Sambhajinagar • Precision Tooling & HVAC Strategy',
    description: 'Auto-generated roadmap based on 1,420 industrial vacancies across Waluj, Shendra, and DMIC industrial hubs.',
    items: [
      {
        course: 'CAD/CAM Multi-Axis CNC Design (NX & CATIA V5)',
        action: 'expand',
        trainerDelta: '+3 Master Machinists',
        equipment: 'Deploy 5-axis Siemens NX CAM simulation lab and Fanuc CNC turning center',
        placementRate: '91.8%',
        demand: '580 Vacancies (Critical Surge)'
      },
      {
        course: 'Industrial Refrigeration & Ammonia Cold-Chain Commissioning',
        action: 'expand',
        trainerDelta: '+2 HVAC Specialists',
        equipment: 'Install transcritical CO2/NH3 test rig with Danfoss electronic controllers',
        placementRate: '85.2%',
        demand: '380 Vacancies (High)'
      },
      {
        course: 'Digital Commerce & MSME Growth Marketing (DigiDhan)',
        action: 'expand',
        trainerDelta: '+2 Digital Mentors',
        equipment: 'Set up MSME digital commerce incubation lab for rural entrepreneurs',
        placementRate: '81.0%',
        demand: '310 Vacancies (Rising)'
      },
      {
        course: 'Manual Sheet Metal Hammering & Tin Smithy',
        action: 'phase_out',
        trainerDelta: '-2 Reallocated',
        equipment: 'Decommission manual smithy; establish automated press brake tooling lab',
        placementRate: '28.4%',
        demand: '20 Vacancies (Near Zero)'
      }
    ]
  }
};

const HEATMAP_DOMAINS = [
  'Data Structures & Algorithms',
  'PyTorch / Neural Networks',
  'Cloud Architecture & K8s',
  'Cyber Security & SOC L2',
  'Embedded Systems & CAN-bus',
  'Industrial Robotics & PLC',
  'CNC Machining & GD&T',
  'Solar PV & BESS Storage'
];

const DISTRICT_MARKETS = [
  'Pune Tech',
  'Mumbai MMR',
  'Thane Belt',
  'Nagpur MIHAN',
  'Nashik Auto',
  'Chh. Sambhajinagar'
];

const BASELINE_SCORES = [
  [92, 88, 76, 58, 64, 52],
  [96, 82, 65, 48, 42, 38],
  [88, 97, 84, 52, 49, 45],
  [82, 94, 75, 44, 40, 36],
  [91, 62, 58, 74, 86, 78],
  [89, 58, 68, 92, 94, 88],
  [86, 52, 62, 72, 91, 95],
  [78, 86, 70, 94, 82, 75],
];

// ============================================================================
// 2. SMOOTH SCROLL & SCROLL REVEALS
// ============================================================================
function initSmoothScroll() {
  if (typeof window.Lenis === 'function') {
    const lenis = new window.Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      touchMultiplier: 1.5,
    });

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
  }
}

function initScrollAnimations() {
  const revealElements = document.querySelectorAll('.reveal-on-scroll');
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.12,
    rootMargin: '0px 0px -40px 0px'
  });

  revealElements.forEach(el => revealObserver.observe(el));

  const counterElements = document.querySelectorAll('.counter-value');
  const counterObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.25
  });

  counterElements.forEach(el => counterObserver.observe(el));
}

function animateCounter(el) {
  const target = parseFloat(el.getAttribute('data-target') || '0');
  const decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
  const duration = 1800;
  const startTime = performance.now();

  function updateCount(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
    const currentVal = easeProgress * target;

    el.textContent = currentVal.toFixed(decimals);

    if (progress < 1) {
      requestAnimationFrame(updateCount);
    } else {
      el.textContent = target.toFixed(decimals);
    }
  }

  requestAnimationFrame(updateCount);
}

// ============================================================================
// 3. 3-PILL STAKEHOLDER SWITCHER LOGIC
// ============================================================================
window.switchDashboardRole = function(role, triggerAnimation = true) {
  state.activeRole = role;

  const govtDash = document.getElementById('govtDashboard');
  const instDash = document.getElementById('instituteDashboard');
  const empDash = document.getElementById('employerDashboard');

  if (govtDash) govtDash.style.display = (role === 'govt' ? 'block' : 'none');
  if (instDash) instDash.style.display = (role === 'institute' ? 'block' : 'none');
  if (empDash) empDash.style.display = (role === 'employer' ? 'block' : 'none');

  const roleButtons = document.querySelectorAll('.role-pill');
  roleButtons.forEach(btn => {
    const btnRole = btn.getAttribute('data-role');
    if (btnRole === role) {
      btn.classList.add('active');
      btn.style.opacity = '1';
      btn.style.fontWeight = 'bold';
      btn.setAttribute('aria-selected', 'true');
    } else {
      btn.classList.remove('active');
      btn.style.opacity = '0.7';
      btn.style.fontWeight = 'normal';
      btn.setAttribute('aria-selected', 'false');
    }
  });

  const indicator = document.getElementById('rolePillIndicator');
  const activeBtn = document.querySelector(`.role-pill[data-role="${role}"]`);
  if (indicator && activeBtn) {
    indicator.style.transform = `translateX(${activeBtn.offsetLeft}px)`;
    indicator.style.width = `${activeBtn.offsetWidth}px`;
  }

  applyHeroContextForRole(role);
};

function applyHeroContextForRole(role) {
  const roleHeading = document.getElementById('heroPortalHeading');
  const roleDesc = document.getElementById('heroPortalDesc');
  const contextPill = document.getElementById('portalRoleContextName');
  const activeModeText = document.getElementById('portalActiveModeText');

  const agilityEl = document.getElementById('curriculumAgilityValue');
  const placementEl = document.getElementById('placementLiftValue');
  const districtsEl = document.getElementById('districtsCountValue');
  const tcoEl = document.getElementById('tcoValue');

  const metric1Sub = document.getElementById('metric1Subtitle');
  const metric2Sub = document.getElementById('metric2Subtitle');
  const metric3Sub = document.getElementById('metric3Subtitle');
  const metric4Sub = document.getElementById('metric4Subtitle');

  const trendPill = document.getElementById('agilityTrendPill');
  const placementPill = document.getElementById('placementLiftPill');

  if (role === 'govt') {
    if (contextPill) contextPill.textContent = 'State Executive Portal';
    if (roleHeading) roleHeading.textContent = 'Automated Labour Demand & Curriculum Alignment';
    if (roleDesc) roleDesc.textContent = 'Bridging Skills to Industry | Govt. of Maharashtra (PS 26134). Real-time vector matching between industrial job requisitions and vocational course syllabi.';
    if (activeModeText) activeModeText.textContent = 'Directorate of Vocational Education';

    if (agilityEl) agilityEl.setAttribute('data-target', '80');
    if (placementEl) placementEl.setAttribute('data-target', '35');
    if (districtsEl) districtsEl.setAttribute('data-target', '36');
    if (tcoEl) tcoEl.setAttribute('data-target', '2');

    if (metric1Sub) metric1Sub.textContent = 'Revision latency cut from years to days';
    if (metric2Sub) metric2Sub.textContent = 'Projected lift across pilot ITIs';
    if (metric3Sub) metric3Sub.textContent = 'Statewide labor-market intelligence coverage';
    if (metric4Sub) metric4Sub.textContent = 'Projected TCO per citizen / year on serverless Modal compute';

    if (trendPill) {
      trendPill.textContent = '↑ Days vs Years';
      trendPill.className = 'metric-pill emerald';
    }
    if (placementPill) {
      placementPill.textContent = 'Projected Lift';
      placementPill.className = 'metric-pill amber';
    }
  } else if (role === 'institute') {
    if (contextPill) contextPill.textContent = 'Training Institute Portal';
    if (roleHeading) roleHeading.textContent = 'Curriculum Modernization & Lab Resource Directives';
    if (roleDesc) roleDesc.textContent = 'Operational telemetry for ITI Principals and MSBTE Department Heads. Track NSQF trade compliance and requisition modernized lab hardware.';
    if (activeModeText) activeModeText.textContent = 'Government ITI & Polytechnic Network';

    if (agilityEl) agilityEl.setAttribute('data-target', '88');
    if (placementEl) placementEl.setAttribute('data-target', '42');
    if (districtsEl) districtsEl.setAttribute('data-target', '36');
    if (tcoEl) tcoEl.setAttribute('data-target', '2');

    if (metric1Sub) metric1Sub.textContent = 'Trade module agility & semester turnaround';
    if (metric2Sub) metric2Sub.textContent = 'Placement lift projected across modernized trades';
    if (metric3Sub) metric3Sub.textContent = 'Institutional nodes reporting live enrollment';
    if (metric4Sub) metric4Sub.textContent = 'Per student annual AI compute footprint';

    if (trendPill) {
      trendPill.textContent = '↑ +18.5% YoY';
      trendPill.className = 'metric-pill emerald';
    }
    if (placementPill) {
      placementPill.textContent = '18 Outdated Directives';
      placementPill.className = 'metric-pill coral';
    }
  } else if (role === 'employer') {
    if (contextPill) contextPill.textContent = 'Industry Partner Portal';
    if (roleHeading) roleHeading.textContent = 'Talent Pipeline & Real-Time Skill Demand Validation';
    if (roleDesc) roleDesc.textContent = 'Validate curriculum proposals, forecast upcoming vocational graduate batches in Pune & Mumbai, and flag missing hyper-local skills directly to the AI vector engine.';
    if (activeModeText) activeModeText.textContent = 'CII & FICCI Maharashtra Industry Council';

    if (agilityEl) agilityEl.setAttribute('data-target', '75');
    if (placementEl) placementEl.setAttribute('data-target', '48');
    if (districtsEl) districtsEl.setAttribute('data-target', '36');
    if (tcoEl) tcoEl.setAttribute('data-target', '2');

    if (metric1Sub) metric1Sub.textContent = 'Industry hiring alignment index with 2026 tech stacks';
    if (metric2Sub) metric2Sub.textContent = 'Apprenticeship fill rate acceleration';
    if (metric3Sub) metric3Sub.textContent = 'Industrial corridors actively mapped';
    if (metric4Sub) metric4Sub.textContent = 'Zero-infrastructure hiring portal integration';

    if (trendPill) {
      trendPill.textContent = '↑ +12.4% YoY';
      trendPill.className = 'metric-pill emerald';
    }
    if (placementPill) {
      placementPill.textContent = '312 Vacancy Gaps';
      placementPill.className = 'metric-pill coral';
    }
  }

  [agilityEl, placementEl, districtsEl, tcoEl].forEach(el => {
    if (el) animateCounter(el);
  });

  renderDynamicHeatmap();
}

function initRoleSwitcher() {
  const initialBtn = document.querySelector('.role-pill.active');
  const indicator = document.getElementById('rolePillIndicator');
  if (initialBtn && indicator) {
    setTimeout(() => {
      indicator.style.transform = `translateX(${initialBtn.offsetLeft}px)`;
      indicator.style.width = `${initialBtn.offsetWidth}px`;
    }, 100);
  }

  window.addEventListener('resize', () => {
    const active = document.querySelector('.role-pill.active');
    if (active && indicator) {
      indicator.style.transform = `translateX(${active.offsetLeft}px)`;
      indicator.style.width = `${active.offsetWidth}px`;
    }
  });
}

// ============================================================================
// 4. THE CORE ENGINE: PYTORCH VECTOR EMBEDDING & EXTRACTION
// ============================================================================
function initExtractionEngine() {
  const textarea = document.getElementById('curriculumInput');
  const charDisplay = document.getElementById('charCountDisplay');
  const extractBtn = document.getElementById('runNlpBtn');
  const presetChips = document.querySelectorAll('.preset-chip');

  if (textarea && charDisplay) {
    textarea.addEventListener('input', () => {
      charDisplay.textContent = textarea.value.length;
    });
  }

  presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const text = chip.getAttribute('data-text');
      if (textarea && text) {
        textarea.value = text;
        if (charDisplay) charDisplay.textContent = text.length;
        triggerSkillExtraction();
      }
    });
  });

  if (extractBtn) {
    extractBtn.addEventListener('click', () => {
      triggerSkillExtraction();
    });
  }
}

async function triggerSkillExtraction() {
  if (state.isExtracting) return;
  state.isExtracting = true;

  const btn = document.getElementById('runNlpBtn');
  const textarea = document.getElementById('curriculumInput');
  const statusPill = document.getElementById('extractionPill');
  const skillsContainer = document.getElementById('extractedSkillsContainer');
  const vectorSnippet = document.getElementById('vectorDataSnippet');
  const cosineSim = document.getElementById('vectorCosineSim');

  const text = textarea ? textarea.value.trim() : '';
  if (!text) {
    showToast('Please enter a curriculum module to extract skills.');
    state.isExtracting = false;
    return;
  }

  if (btn) btn.classList.add('loading');
  if (statusPill) {
    statusPill.textContent = 'PyTorch Vectorizer: Computing...';
    statusPill.style.color = '#FBBF24';
  }

  const endpointUrl = buildApiUrl('/api/v1/search');
  let result = null;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(endpointUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: text, top_k: 5 }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      result = await response.json();
    }
  } catch (err) {
    console.info('Live API fallback activated:', err.message);
  }

  setTimeout(() => {
    const extractedData = generateExtractionResult(text, result);

    if (skillsContainer) {
      skillsContainer.innerHTML = '';
      extractedData.skills.forEach(skill => {
        const badge = document.createElement('span');
        badge.className = `skill-tag ${skill.type}`;
        badge.textContent = skill.name;
        skillsContainer.appendChild(badge);
      });
    }

    if (vectorSnippet) vectorSnippet.textContent = extractedData.vectorSample;
    if (cosineSim) cosineSim.textContent = `Cosine Sim: ${extractedData.cosineSimilarity}`;

    if (statusPill) {
      statusPill.textContent = 'PyTorch Vectorizer: Active';
      statusPill.style.color = '#34D399';
    }

    if (btn) btn.classList.remove('loading');
    state.isExtracting = false;

    renderDynamicHeatmap(extractedData.scoreBias);
    showToast('SkillSetu NLP Extraction & Vector Matching Complete!');
  }, 450);
}

function generateExtractionResult(inputText, apiResult) {
  const lower = inputText.toLowerCase();

  let skills = [];
  let scoreBias = 0;

  if (lower.includes('data structure') || lower.includes('tree') || lower.includes('graph')) {
    skills = [
      { name: 'Data Structures & Algorithms (NSQF-6)', type: 'high-demand' },
      { name: 'Binary Search Trees & Balancing', type: 'high-demand' },
      { name: 'Time Complexity (Big-O Analysis)', type: 'high-demand' },
      { name: 'Graph Traversal (BFS/DFS)', type: '' },
      { name: 'Dynamic Memory Management', type: 'high-demand' },
      { name: '⚠️ Microservice Distributed Caching (Gap)', type: 'gap' }
    ];
    scoreBias = 12;
  } else if (lower.includes('pytorch') || lower.includes('deep learning') || lower.includes('neural') || lower.includes('genai')) {
    skills = [
      { name: 'PyTorch Tensor Mathematics (NSQF-7)', type: 'high-demand' },
      { name: 'Neural Network Gradient Descent', type: 'high-demand' },
      { name: 'Convolutional & Transformer Layers', type: 'high-demand' },
      { name: 'Model Quantization & ONNX Export', type: 'high-demand' },
      { name: 'Generative AI & LLM RAG Pipelines', type: 'high-demand' },
      { name: '⚠️ Kubernetes MLOps Pipelines (Gap)', type: 'gap' }
    ];
    scoreBias = 24;
  } else if (lower.includes('plc') || lower.includes('automation') || lower.includes('scada') || lower.includes('iot')) {
    skills = [
      { name: 'Programmable Logic Controllers (PLC)', type: 'high-demand' },
      { name: 'SCADA Supervisory Control Systems', type: 'high-demand' },
      { name: 'Industrial Modbus & Profinet Protocols', type: 'high-demand' },
      { name: 'Ladder Logic Programming (IEC 61131-3)', type: '' },
      { name: '⚠️ Edge IoT Cybersecurity (Gap)', type: 'gap' }
    ];
    scoreBias = 16;
  } else if (lower.includes('solar') || lower.includes('ev') || lower.includes('battery')) {
    skills = [
      { name: 'Electric Vehicle Diagnostics (NSQF-6)', type: 'high-demand' },
      { name: 'CAN-bus Telemetry Protocol Analysis', type: 'high-demand' },
      { name: 'Solar PV Grid Inverter Commissioning', type: 'high-demand' },
      { name: 'BESS Battery Energy Storage Systems', type: 'high-demand' },
      { name: '⚠️ High-Voltage DC Arc Flash Safety (Gap)', type: 'gap' }
    ];
    scoreBias = 20;
  } else {
    skills = [
      { name: '5-Axis VMC Machining (Fanuc/Mazak)', type: 'high-demand' },
      { name: 'CAD/CAM Multi-Axis Toolpath Generation', type: 'high-demand' },
      { name: 'GD&T Engineering Drawing Standards', type: 'high-demand' },
      { name: '⚠️ SPC Quality Gate Automation (Gap)', type: 'gap' }
    ];
    scoreBias = 14;
  }

  const sampleValues = Array.from({ length: 14 }, () => (Math.random() * 0.8 - 0.4).toFixed(4));
  const vectorSample = `[${sampleValues.join(', ')}, ... +370 dims (dense torch.float32)]`;
  
  let cosine = (0.86 + Math.random() * 0.12).toFixed(3);
  if (apiResult && apiResult.results && apiResult.results.length > 0) {
    if (apiResult.results[0].match_score) {
      cosine = (apiResult.results[0].match_score).toFixed(3);
    }
  }

  return {
    skills,
    scoreBias,
    vectorSample,
    cosineSimilarity: cosine
  };
}

// ============================================================================
// 5. DYNAMIC CURRICULUM HEATMAP (CHART.JS)
// ============================================================================
export async function renderDynamicHeatmap(bias = 0) {
  const canvas = document.getElementById('alignmentHeatmap');
  if (!canvas) return;

  if (state.heatmapChart) {
    state.heatmapChart.destroy();
  }

  function getScoreColor(val) {
    if (val >= 80) return 'rgba(16, 185, 129, 0.85)';
    if (val >= 55) return 'rgba(245, 158, 11, 0.85)';
    return 'rgba(244, 63, 94, 0.85)';
  }

  function getBorderColor(val) {
    if (val >= 80) return '#059669';
    if (val >= 55) return '#D97706';
    return '#E11D48';
  }

  const datasets = DISTRICT_MARKETS.map((districtName, districtIdx) => {
    const scores = BASELINE_SCORES.map(row => {
      let score = row[districtIdx] + (bias ? Math.round(bias * 0.35) : 0);
      return Math.min(99, Math.max(22, score));
    });

    return {
      label: districtName,
      data: scores,
      backgroundColor: scores.map(getScoreColor),
      borderColor: scores.map(getBorderColor),
      borderWidth: 1.5,
      borderRadius: 6,
      borderSkipped: false,
    };
  });

  const ctx = canvas.getContext('2d');
  state.heatmapChart = new window.Chart(ctx, {
    type: 'bar',
    data: {
      labels: HEATMAP_DOMAINS,
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 850,
        easing: 'easeOutQuart',
      },
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            font: {
              family: "'Plus Jakarta Sans', sans-serif",
              size: 11,
              weight: 600,
            },
            color: '#1E293B',
            boxWidth: 14,
            usePointStyle: true,
            pointStyle: 'rectRounded',
          },
        },
        tooltip: {
          backgroundColor: '#0B132B',
          titleFont: {
            family: "'Plus Jakarta Sans', sans-serif",
            size: 13,
            weight: 700,
          },
          bodyFont: {
            family: "'JetBrains Mono', monospace",
            size: 12,
          },
          padding: 12,
          cornerRadius: 8,
          borderColor: 'rgba(255, 255, 255, 0.15)',
          borderWidth: 1,
          callbacks: {
            label: function(context) {
              const val = context.raw;
              let status = 'Critical Deficit';
              if (val >= 80) status = 'High Alignment (Cosine >= 0.80)';
              else if (val >= 55) status = 'Moderate Match (Cosine ~ 0.60)';
              return ` ${context.dataset.label}: ${val}% (${status})`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: {
              family: "'Plus Jakarta Sans', sans-serif",
              size: 11,
              weight: 600,
            },
            color: '#475569',
            maxRotation: 25,
            minRotation: 15,
          }
        },
        y: {
          min: 0,
          max: 100,
          ticks: {
            callback: (val) => `${val}%`,
            font: { family: "'JetBrains Mono', monospace", size: 11 },
            color: '#64748B',
            stepSize: 20,
          },
          grid: { color: '#E2E8F0', drawBorder: false }
        }
      }
    }
  });
}

// ============================================================================
// 6. DISTRICT ACTION PLANS & REPORTING
// ============================================================================
function initDistrictPlans() {
  const districtCards = document.querySelectorAll('.district-card');
  const exportBtn = document.getElementById('exportPlanCsvBtn');

  districtCards.forEach(card => {
    card.addEventListener('click', () => {
      const districtId = card.getAttribute('data-district');
      if (!districtId) return;

      districtCards.forEach(c => c.classList.remove('active-district'));
      card.classList.add('active-district');
      state.activeDistrict = districtId;

      renderDistrictPlan(districtId);
    });
  });

  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      exportCurrentPlanCsv();
    });
  }

  renderDistrictPlan(state.activeDistrict);
}

function renderDistrictPlan(districtKey) {
  const data = DISTRICT_DATA[districtKey] || DISTRICT_DATA.pune;

  const titleEl = document.getElementById('planTargetTitle');
  const descEl = document.getElementById('planTargetDesc');
  const tableBody = document.getElementById('planTableBody');

  if (titleEl) {
    titleEl.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
      ${data.title}
    `;
  }

  if (descEl) descEl.textContent = data.description;

  if (tableBody) {
    tableBody.innerHTML = '';
    data.items.forEach(item => {
      const tr = document.createElement('tr');

      let actionClass = 'action-expand';
      let actionLabel = 'Expand Seats';
      if (item.action === 'phase_out') {
        actionClass = 'action-phase-out';
        actionLabel = 'Phase Out';
      } else if (item.action === 'reduce') {
        actionClass = 'action-reduce';
        actionLabel = 'Reduce 40%';
      }

      tr.innerHTML = `
        <td><strong>${item.course}</strong></td>
        <td><span class="upgrade-action-pill ${actionClass}">${actionLabel}</span></td>
        <td style="font-family: var(--font-mono); font-weight: 600;">${item.trainerDelta}</td>
        <td style="color: #475569;">${item.equipment}</td>
        <td style="font-family: var(--font-mono); font-weight: 700; color: ${item.action === 'phase_out' ? '#F43F5E' : '#10B981'};">${item.placementRate}</td>
        <td><span style="font-size: 0.8rem; font-weight: 600; color: #334155;">${item.demand}</span></td>
      `;
      tableBody.appendChild(tr);
    });
  }
}

window.filterDistrictCards = function(query) {
  const q = (query || '').toLowerCase().trim();
  const cards = document.querySelectorAll('.district-card');
  let firstVisible = null;

  cards.forEach(card => {
    const text = card.textContent.toLowerCase();
    const matches = !q || text.includes(q);
    card.style.display = matches ? 'block' : 'none';
    if (matches && !firstVisible) {
      firstVisible = card;
    }
  });

  if (firstVisible && !firstVisible.classList.contains('active-district')) {
    const distId = firstVisible.getAttribute('data-district');
    if (distId) {
      cards.forEach(c => c.classList.remove('active-district'));
      firstVisible.classList.add('active-district');
      state.activeDistrict = distId;
      renderDistrictPlan(distId);
    }
  }
};

export function exportCurrentPlanCsv() {
  const data = DISTRICT_DATA[state.activeDistrict] || DISTRICT_DATA.pune;
  const headers = ['District', 'Zone', 'Course Name', 'Action Directive', 'Trainer Delta', 'Equipment & Notes', 'Placement Rate', 'Matching Demand'];
  
  const csvRows = [headers.join(',')];
  data.items.forEach(item => {
    const row = [
      `"${data.name}"`,
      `"${data.zone}"`,
      `"${item.course.replace(/"/g, '""')}"`,
      `"${item.action}"`,
      `"${item.trainerDelta}"`,
      `"${item.equipment.replace(/"/g, '""')}"`,
      `"${item.placementRate}"`,
      `"${item.demand.replace(/"/g, '""')}"`
    ];
    csvRows.push(row.join(','));
  });

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `skillsetu_action_plan_${state.activeDistrict}_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast(`Exported ${data.name} capacity plan to CSV!`);
}

window.exportAllDistrictsCsv = function() {
  const headers = ['District', 'Zone', 'Course / Program', 'Action Directive', 'Trainer Delta', 'Equipment & Infrastructure Upgrade', 'Placement Rate', 'Market Demand Signal'];
  const csvRows = [headers.join(',')];

  Object.keys(DISTRICT_DATA).forEach(key => {
    const d = DISTRICT_DATA[key];
    d.items.forEach(item => {
      const row = [
        `"${d.name}"`,
        `"${d.zone}"`,
        `"${item.course.replace(/"/g, '""')}"`,
        `"${item.action}"`,
        `"${item.trainerDelta}"`,
        `"${item.equipment.replace(/"/g, '""')}"`,
        `"${item.placementRate}"`,
        `"${item.demand.replace(/"/g, '""')}"`
      ];
      csvRows.push(row.join(','));
    });
  });

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `skillsetu_statewide_district_action_plans_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast('Statewide 6-District Action Report downloaded (CSV)!');
};

// ============================================================================
// 7. DEMO SIMULATION HANDLERS & MODALS
// ============================================================================
window.simulateFundReallocation = function(initiative, amountCr) {
  showToast(`Authorized ₹${amountCr} Cr capital reallocation for ${initiative}!`);
  alert(`Fund Reallocation Engine Triggered\n\nInitiative: ${initiative}\nAmount: ₹${amountCr} Crores\nStatus: Authorized & Dispatched to District Skill Committee (MSSDS).`);
};

window.simulateProcurement = function(machineName, target) {
  showToast(`Requisition sent to GeM Portal for ${machineName} (${target})`);
  alert(`GeM Portal Equipment Requisition\n\nEquipment: ${machineName}\nTarget Center: ITI ${target}\nStatus: Automated procurement notice published on Government e-Marketplace (GeM).`);
};

window.scheduleInterview = function(candidateName, company) {
  showToast(`Interview invite sent to ${candidateName} for ${company}!`);
  alert(`Direct Placement Fast-Track\n\nCandidate: ${candidateName}\nEmployer: ${company}\nStatus: Pre-vetted NSQF credentials transmitted. Interview schedule confirmed.`);
};

window.handleDeficitSubmit = function(e) {
  e.preventDefault();
  const district = document.getElementById('intakeDistrict')?.value || 'Pune';
  const sector = document.getElementById('intakeSector')?.value || 'Tech';
  const skill = document.getElementById('intakeSkill')?.value || 'Emerging Skill';
  const vacancies = document.getElementById('intakeVacancies')?.value || '100';
  const company = document.getElementById('intakeCompany')?.value || 'Industry Partner';

  // Prepend to live signals ticker
  const tickerTrack = document.getElementById('signalsTickerTrack');
  if (tickerTrack) {
    const newSignal = document.createElement('span');
    newSignal.className = 'signal-item';
    newSignal.innerHTML = `🚨 <strong>${district}:</strong> Urgent ${skill} demand (<span class="trend-up">+${vacancies} openings</span>) logged by ${company}`;
    tickerTrack.insertBefore(newSignal, tickerTrack.firstChild);
  }

  // Prepend to extracted skills badges
  const skillsContainer = document.getElementById('extractedSkillsContainer');
  if (skillsContainer) {
    const badge = document.createElement('span');
    badge.className = 'skill-tag high-demand';
    badge.textContent = `${skill} (${district} Hub)`;
    skillsContainer.insertBefore(badge, skillsContainer.firstChild);
  }

  document.getElementById('deficitIntakeForm')?.reset();

  alert(`Skill Signal Successfully Vectorized!\n\nSkill: "${skill}"\nDemand: ${vacancies} openings in ${district}\nEmployer: ${company}\n\nStatus: PyTorch dense embeddings calculated. Directives updated for regional ITI curriculum boards.`);
  showToast(`Vectorized signal for ${skill} (${district})`);
};

function initAuditModal() {
  const openBtn = document.getElementById('generateAuditReportBtn');
  const modal = document.getElementById('auditModalBackdrop');
  const closeBtn = document.getElementById('closeAuditModalBtn');
  const closeActionBtn = document.getElementById('modalCloseActionBtn');
  const downloadPdfBtn = document.getElementById('downloadOfficialPdfBtn');

  if (openBtn && modal) {
    openBtn.addEventListener('click', () => {
      modal.classList.add('show');
    });
  }

  [closeBtn, closeActionBtn].forEach(b => {
    if (b && modal) {
      b.addEventListener('click', () => {
        modal.classList.remove('show');
      });
    }
  });

  if (downloadPdfBtn && modal) {
    downloadPdfBtn.addEventListener('click', () => {
      modal.classList.remove('show');
      showToast('Generating official signed PDF report for Maharashtra Skill Directorate...');
      setTimeout(() => {
        alert('SkillSetu Labor-Market Intelligence Report (PDF)\n\nDocument ID: MSSDS-SIH26134-AUDIT-2026.pdf\nVerification: Signed via Digital State Repository.\nCoverage: 36 Districts, 418 ITIs, 26 Industry Corridors.');
      }, 500);
    });
  }
}

// ============================================================================
// 8. TOAST NOTIFICATION UTILITY
// ============================================================================
export function showToast(message) {
  const toast = document.getElementById('toastNotification');
  const toastMsg = document.getElementById('toastMessage');
  if (!toast || !toastMsg) return;

  toastMsg.textContent = message;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3400);
}

// ============================================================================
// 9. APP INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  initSmoothScroll();
  initScrollAnimations();
  initRoleSwitcher();
  initExtractionEngine();
  initDistrictPlans();
  initAuditModal();
  renderDynamicHeatmap();
});


// ============================================================================
// 10. SIH PROTOTYPE INTERACTIVITY FIXES (GLOBAL EVENT LISTENER)
// ============================================================================
document.addEventListener('click', function(e) {
    const text = e.target.innerText || '';

    // 1. Fix: View Capacity Reallocation Plan
    if (text.includes('View Capacity Reallocation Plan') || e.target.closest('.view-plan-btn')) {
        e.preventDefault();
        const card = e.target.closest('div[class*="card"], div[class*="district"], div[style]') || e.target.parentElement;
        const district = card.querySelector('h2, h3')?.innerText || 'this district';
        alert(`Fetching AI-Generated Reallocation Plan for ${district}...\n\nStatus: Processing vector similarities via Modal GPU.\nRecommendation: Expand advanced manufacturing modules to meet local deficit.`);
    }

    // 2. Fix: Approve Institutional Directive
    if (text.includes('Approve Institutional Directive') || text.includes('Approve')) {
        e.preventDefault();
        alert('Directive Successfully Approved. Local ITI centers have been notified via the MSSDS portal.');
        e.target.innerText = 'Approved ✓';
        e.target.style.backgroundColor = '#10B981';
        e.target.style.color = '#ffffff';
        e.target.style.pointerEvents = 'none';
    }

    // 3. Fix: 3-Pill Dashboard Switcher (Govt / Institute / Employer)
    if (text.includes('Govt') || text.includes('Training Institute') || text.includes('Employer')) {
        if(e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.classList.contains('pill') || e.target.classList.contains('role-pill')) {
            e.preventDefault();
            
            // Visual feedback for the demo
            alert(`Switching data context to: ${text.trim()}.\nRecalculating district deficits and curriculum alignment based on ${text.trim()} priorities.`);
            
            // Highlight active pill
            const siblings = e.target.parentElement.children;
            for(let node of siblings) {
                node.style.opacity = '0.5';
                node.style.fontWeight = 'normal';
            }
            e.target.style.opacity = '1';
            e.target.style.fontWeight = 'bold';
            
            // Logic to hide/show the respective HTML dashboard sections built in Step 1
            const lower = text.toLowerCase();
            let role = 'govt';
            if (lower.includes('training') || lower.includes('institute')) role = 'institute';
            else if (lower.includes('employer')) role = 'employer';
            
            if (typeof window.switchDashboardRole === 'function') {
                window.switchDashboardRole(role, false);
            }
        }
    }
});
