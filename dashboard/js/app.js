/* ═══════════════════════════════════════════════════════════
   PawPulse — Caretaker App Controller & Supabase Integration
   Handles telemetry state, charts, realtime alerts, and modals
   ═══════════════════════════════════════════════════════════ */

const PawApp = (() => {
  // State
  let supabase = null;
  let activityChart = null;
  let activeAlerts = [
    {
      id: 'alert-shanti-01',
      animalId: 3,
      name: 'Shanti',
      species: 'dog',
      pen: 'Pen 2 - North Ward',
      severity: 'CRITICAL',
      type: 'LETHARGY & ISOLATION',
      message: 'Dog #3 (Shanti) has moved only 40m in the last 24h (5% of 750m baseline) and stayed secluded in the back-right corner. Possible early illness or lethargy.',
      timeAgo: '12m ago',
      resolved: false
    }
  ];

  const telemetry = {
    buddy:  { id: 1, dist: 850, baseline: 800, restHours: 4.2, bowlVisits: 3, status: 'Healthy' },
    shanti: { id: 3, dist: 40,  baseline: 750, restHours: 14.1, bowlVisits: 0, status: 'Lethargic' },
    mochi:  { id: 2, dist: 320, baseline: 350, restHours: 6.5, bowlVisits: 2, status: 'Resting' }
  };

  function init() {
    initChart();
    initCanvas();
    initEventListeners();
    checkSavedSupabaseConfig();
    startTelemetryHeartbeat();
  }

  // 1. Chart.js Distance vs Baseline
  function initChart() {
    const ctx = document.getElementById('activityChart');
    if (!ctx) return;

    activityChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Buddy (Dog #1)', 'Shanti (Dog #3)', 'Mochi (Cat #2)'],
        datasets: [
          {
            label: 'Distance Today (m)',
            data: [telemetry.buddy.dist, telemetry.shanti.dist, telemetry.mochi.dist],
            backgroundColor: [
              'rgba(63, 163, 101, 0.85)', // Sage
              'rgba(217, 79, 79, 0.85)',   // Rose / Alert
              'rgba(155, 82, 135, 0.85)'   // Mauve
            ],
            hoverBackgroundColor: [
              'rgba(63, 163, 101, 1)',
              'rgba(217, 79, 79, 1)',
              'rgba(155, 82, 135, 1)'
            ],
            borderRadius: 14,
            borderSkipped: false,
            barThickness: 32,
            categoryPercentage: 0.8,
            barPercentage: 0.9
          },
          {
            label: '3-Day Baseline (m)',
            data: [telemetry.buddy.baseline, telemetry.shanti.baseline, telemetry.mochi.baseline],
            backgroundColor: 'rgba(238, 220, 233, 0.65)',
            hoverBackgroundColor: 'rgba(238, 220, 233, 0.95)',
            borderRadius: 14,
            borderSkipped: false,
            barThickness: 32,
            categoryPercentage: 0.8,
            barPercentage: 0.9
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 900,
          easing: 'easeOutQuart'
        },
        plugins: {
          legend: {
            position: 'top',
            align: 'end',
            labels: {
              boxWidth: 10,
              boxHeight: 10,
              usePointStyle: true,
              pointStyle: 'circle',
              font: { family: '"DM Sans", sans-serif', size: 12, weight: '600' },
              color: '#8A8295',
              padding: 16
            }
          },
          tooltip: {
            backgroundColor: 'rgba(42, 36, 51, 0.92)',
            titleFont: { family: '"Space Grotesk", sans-serif', size: 13, weight: '700' },
            bodyFont: { family: '"DM Sans", sans-serif', size: 12 },
            padding: 12,
            cornerRadius: 12,
            callbacks: {
              label: (item) => ` ${item.dataset.label}: ${item.raw} meters`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 1000,
            grid: {
              color: 'rgba(155, 82, 135, 0.06)',
              drawBorder: false
            },
            ticks: {
              font: { family: '"JetBrains Mono", monospace', size: 11 },
              color: '#8A8295',
              stepSize: 200,
              callback: (v) => `${v}m`
            }
          },
          x: {
            grid: { display: false, drawBorder: false },
            ticks: {
              font: { family: '"Space Grotesk", sans-serif', size: 12, weight: '600' },
              color: '#2A2433',
              padding: 6
            }
          }
        }
      }
    });
  }

  // 2. CCTV Canvas Initializer
  function initCanvas() {
    const canvas = document.getElementById('cctvCanvas');
    if (canvas && typeof PawCanvas !== 'undefined') {
      PawCanvas.init(canvas);
    }
  }

  // 3. Event Listeners
  function initEventListeners() {
    // Zone & Trail buttons
    const btnZones = document.getElementById('toggleZonesBtn');
    if (btnZones) {
      btnZones.addEventListener('click', () => {
        const on = PawCanvas.toggleZones();
        btnZones.classList.toggle('off', !on);
        btnZones.innerHTML = on ? '🔘 Zones: ON' : '⚪ Zones: OFF';
      });
    }

    const btnTrails = document.getElementById('toggleTrailsBtn');
    if (btnTrails) {
      btnTrails.addEventListener('click', () => {
        const on = PawCanvas.toggleTrails();
        btnTrails.classList.toggle('off', !on);
        btnTrails.innerHTML = on ? '🐾 Trails: ON' : '⚪ Trails: OFF';
      });
    }

    // MP4 File Ingestion Picker
    const videoInput = document.getElementById('videoFileInput');
    if (videoInput) {
      videoInput.addEventListener('change', handleVideoUpload);
    }
  }

  function playPresetVideo(type) {
    const video = document.getElementById('cctvVideo');
    const canvas = document.getElementById('cctvCanvas');
    const statusEl = document.getElementById('videoStatusLabel');
    if (!video || !canvas) return;

    const videoSrc = `assets/monitored_${type}.mp4`;
    const telemetrySrc = `assets/monitored_${type}_telemetry.json`;

    canvas.style.display = 'none';
    video.style.display = 'block';
    video.src = videoSrc;
    video.play().catch(e => console.log('Autoplay handled:', e));

    if (statusEl) {
      statusEl.innerHTML = `<span style="color: var(--mv-mauve); font-weight: 700;">▶ Monitored ${type.toUpperCase()} Video (RT-DETR-L + ByteTrack)</span>`;
    }

    // Fetch and display telemetry summary
    fetch(telemetrySrc)
      .then(res => res.json())
      .then(data => {
        const count = data.unique_animals_tracked || 0;
        showNotification(
          `🎬 Playing Monitored ${type.toUpperCase()}`,
          `Detected ${count} tracks | Processed at ${data.processed_fps} FPS. Check ID continuity & species consistency!`
        );
      })
      .catch(() => {
        showNotification(`🎬 Playing Monitored ${type.toUpperCase()}`, 'H.264 video with RT-DETR-L detection overlay & ByteTrack');
      });
  }

  function play5MinCCTV() {
    const video = document.getElementById('cctvVideo');
    const canvas = document.getElementById('cctvCanvas');
    const statusEl = document.getElementById('videoStatusLabel');
    if (!video || !canvas) return;

    canvas.style.display = 'none';
    video.style.display = 'block';
    video.src = 'assets/cctv_5min_shelter_pen2.mp4';
    video.play().catch(e => console.log('Autoplay handled:', e));

    if (statusEl) {
      statusEl.innerHTML = `<span style="color: var(--mv-mauve); font-weight: 700;">▶ 5-Minute Shelter CCTV Stream (CAM-02 Pen 2 North • 300s / 4500 Frames)</span>`;
    }
    showNotification('🎬 Playing 5-Min CCTV Stream', 'Streaming continuous 5-minute shelter surveillance recording (CAM-02 Pen 2).');
  }

  function showLiveCanvas() {
    const video = document.getElementById('cctvVideo');
    const canvas = document.getElementById('cctvCanvas');
    const statusEl = document.getElementById('videoStatusLabel');
    if (!video || !canvas) return;

    video.pause();
    video.style.display = 'none';
    canvas.style.display = 'block';

    if (statusEl) {
      statusEl.innerHTML = `<span style="color: var(--mv-muted); font-weight: 600;">Real-Time Pen 2 Stream Active</span>`;
    }
    showNotification('📡 Switched to Live Pen 2', 'Continuous CCTV simulation with RT-DETR-L HUD & dynamic roaming active');
  }

  function handleVideoUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const video = document.getElementById('cctvVideo');
    const canvas = document.getElementById('cctvCanvas');
    const statusEl = document.getElementById('videoStatusLabel');

    if (video && canvas) {
      canvas.style.display = 'none';
      video.style.display = 'block';
      video.src = URL.createObjectURL(file);
      video.play().catch(e => console.log('Autoplay handled:', e));
    }

    if (statusEl) {
      statusEl.innerHTML = `<span style="color: var(--sage-600); font-weight: 600;">✓ Ingested: ${file.name} (${(file.size / (1024*1024)).toFixed(1)} MB)</span>`;
    }

    // Notification toast
    showNotification(`🎬 Video Ingested: "${file.name}"`, 'Playing file inside Pen 2 Viewport with active audio/controls...');
  }

  // 4. Alert Actions
  function acknowledgeAlert(alertId) {
    const banner = document.getElementById('alertBanner');
    if (banner) {
      banner.style.opacity = '0.45';
      banner.style.transform = 'scale(0.99)';
    }

    const found = activeAlerts.find(a => a.id === alertId) || activeAlerts[0];
    if (found) found.resolved = true;

    showNotification(
      '🩺 Caretaker Action Logged',
      'Staff dispatched to Pen 2 to check on Shanti. Temp check, hydration & veterinary notes updated.'
    );

    // If connected to Supabase, update row
    if (supabase) {
      supabase.from('alerts')
        .update({ is_resolved: true, resolved_at: new Date().toISOString(), resolved_by: 'Caretaker on Duty' })
        .eq('alert_type', 'LETHARGY')
        .then(() => console.log('Resolved alert in Supabase'));
    }
  }

  function triggerSimulatedAlert() {
    const banner = document.getElementById('alertBanner');
    if (banner) {
      banner.style.opacity = '1';
      banner.style.transform = 'scale(1)';
      banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
      banner.classList.add('flash-glow');
      setTimeout(() => banner.classList.remove('flash-glow'), 1200);
    }
  }

  // 5. Supabase Connection Modal
  function openSupabaseModal() {
    const m = document.getElementById('supabaseModal');
    if (m) m.classList.add('open');
  }

  function closeSupabaseModal() {
    const m = document.getElementById('supabaseModal');
    if (m) m.classList.remove('open');
  }

  function saveSupabaseConfig() {
    const url = document.getElementById('supabaseUrlInput').value.trim();
    const key = document.getElementById('supabaseKeyInput').value.trim();

    if (!url || !key) {
      alert('Please provide both Project URL and Anon Key.');
      return;
    }

    try {
      supabase = window.supabase.createClient(url, key);
      localStorage.setItem('pawpulse_sb_url', url);
      localStorage.setItem('pawpulse_sb_key', key);

      updateSupabaseStatusUI(true);
      closeSupabaseModal();

      // Listen to live alerts
      supabase
        .channel('public:alerts')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'alerts' }, payload => {
          handleIncomingRealtimeAlert(payload.new);
        })
        .subscribe();

      showNotification('✨ Supabase Connected!', 'Live Realtime subscriptions active for alerts and telemetry.');
    } catch (err) {
      alert('Connection error: ' + err.message);
    }
  }

  function checkSavedSupabaseConfig() {
    const url = localStorage.getItem('pawpulse_sb_url');
    const key = localStorage.getItem('pawpulse_sb_key');
    if (url && key && window.supabase) {
      try {
        supabase = window.supabase.createClient(url, key);
        updateSupabaseStatusUI(true);
      } catch (e) {
        console.warn('Cached Supabase credentials failed:', e);
      }
    }
  }

  function updateSupabaseStatusUI(connected) {
    const dot = document.getElementById('supabaseStatusDot');
    const text = document.getElementById('supabaseStatusText');
    if (dot) dot.style.background = connected ? 'var(--sage-400)' : 'var(--peach-400)';
    if (text) text.innerText = connected ? 'Supabase Live' : 'Connect Supabase';
  }

  function handleIncomingRealtimeAlert(alertRow) {
    console.log('Realtime alert received:', alertRow);
    const banner = document.getElementById('alertBanner');
    if (banner) {
      banner.style.opacity = '1';
      const msgEl = banner.querySelector('.alert-message');
      if (msgEl) msgEl.innerText = alertRow.message;
    }
    showNotification('🚨 Live Alert Received', alertRow.message);
  }

  // 6. Subtle Real-Time Heartbeat (Simulates Active Telemetry)
  function startTelemetryHeartbeat() {
    setInterval(() => {
      // Small live distance increments
      telemetry.buddy.dist += Math.random() > 0.4 ? 0.3 : 0.0;
      telemetry.mochi.dist += Math.random() > 0.7 ? 0.1 : 0.0;
      // Shanti does NOT move (emphasizing lethargy)

      // Update DOM numbers smoothly
      const buddyDistEl = document.getElementById('buddyDistValue');
      if (buddyDistEl) buddyDistEl.innerText = `${telemetry.buddy.dist.toFixed(0)}m`;

      const mochiDistEl = document.getElementById('mochiDistValue');
      if (mochiDistEl) mochiDistEl.innerText = `${telemetry.mochi.dist.toFixed(0)}m`;
    }, 2500);
  }

  // Toast Notification System
  function showNotification(title, desc) {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.style.cssText = 'position: fixed; bottom: 24px; right: 24px; z-index: 999; display: flex; flex-direction: column; gap: 10px; pointer-events: none;';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'glass-solid';
    toast.style.cssText = 'pointer-events: auto; padding: 14px 20px; min-width: 300px; max-width: 420px; box-shadow: var(--shadow-lg); border-left: 4px solid var(--mauve-500); animation: slideIn 0.35s var(--ease-bounce);';
    toast.innerHTML = `
      <div style="font-family: var(--font-display); font-size: 0.88rem; font-weight: 700; color: var(--charcoal);">${title}</div>
      <div style="font-size: 0.76rem; color: var(--muted); margin-top: 2px;">${desc}</div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'all 0.4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  }

  function exportCSVReport() {
    const rows = [
      ['Timestamp', 'Enclosure', 'Animal_ID', 'Name', 'Species', 'Distance_24h_m', 'Baseline_3d_m', 'Activity_Pct', 'Z_Score', 'Posture_Aspect_Ratio', 'Corner_Dwell_hrs', 'Bowl_Visits', 'Health_Status', 'Alert_Level'],
      [new Date().toISOString(), 'Pen 2 - North', '1', 'Buddy', 'dog', '854.2', '800.0', '106.8%', '+0.24', '0.88', '0.3', '3', 'Active & Healthy', 'NORMAL'],
      [new Date().toISOString(), 'Pen 2 - North', '3', 'Shanti', 'dog', '40.0', '750.0', '5.3%', '-2.81', '1.65', '14.1', '0', 'Lethargic / Isolated in Corner', 'CRITICAL'],
      [new Date().toISOString(), 'Pen 2 - North', '2', 'Mochi', 'cat', '321.5', '350.0', '91.9%', '-0.15', '1.25', '0.8', '2', 'Normal Resting Curve', 'NORMAL']
    ];

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map(e => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `pawpulse_telemetry_pen2_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showNotification('📥 Caretaker Report Downloaded', 'Exported 24h spatio-temporal telemetry and Z-score deviation logs to CSV.');
  }

  return {
    init,
    playPresetVideo,
    play5MinCCTV,
    showLiveCanvas,
    exportCSVReport,
    acknowledgeAlert,
    triggerSimulatedAlert,
    openSupabaseModal,
    closeSupabaseModal,
    saveSupabaseConfig
  };
})();

// Self-init on DOM loaded
document.addEventListener('DOMContentLoaded', PawApp.init);
