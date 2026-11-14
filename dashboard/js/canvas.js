/* ═══════════════════════════════════════════════════════════
   PawPulse — CCTV Canvas Simulation Engine
   Renders animated pen viewport with RT-DETR detection overlays
   ═══════════════════════════════════════════════════════════ */

const PawCanvas = (() => {
  let canvas, ctx;
  let showZones = true;
  let showTrails = true;
  let frame = 0;

  // Simulated residents with organic wandering behaviour
  const residents = [
    {
      id: 1, name: 'Buddy', species: 'dog',
      color: '#3FA365', colorFade: 'rgba(63,163,101,0.35)',
      x: 0.32, y: 0.52,
      tx: 0.38, ty: 0.58,
      trail: [], status: 'Healthy', dist: 850,
      speed: 0.0018, boxW: 72, boxH: 56,
    },
    {
      id: 3, name: 'Shanti', species: 'dog',
      color: '#D94F4F', colorFade: 'rgba(217,79,79,0.35)',
      x: 0.87, y: 0.19,
      tx: 0.87, ty: 0.19,
      trail: [], status: 'Lethargic', dist: 40,
      speed: 0.00015, boxW: 68, boxH: 54,
    },
    {
      id: 2, name: 'Mochi', species: 'cat',
      color: '#9B5287', colorFade: 'rgba(155,82,135,0.35)',
      x: 0.18, y: 0.76,
      tx: 0.22, ty: 0.80,
      trail: [], status: 'Resting', dist: 320,
      speed: 0.0004, boxW: 48, boxH: 42,
    },
  ];

  function init(canvasEl) {
    canvas = canvasEl;
    ctx = canvas.getContext('2d');
    resize();
    window.addEventListener('resize', resize);
    requestAnimationFrame(loop);
  }

  function resize() {
    const parent = canvas.parentElement;
    canvas.width = parent.clientWidth;
    canvas.height = parent.clientHeight;
  }

  function loop() {
    frame++;
    const w = canvas.width, h = canvas.height;
    draw(w, h);
    requestAnimationFrame(loop);
  }

  function draw(w, h) {
    // Dark pen floor
    ctx.fillStyle = '#18151D';
    ctx.fillRect(0, 0, w, h);

    // Subtle scan-line overlay for CRT/CCTV authenticity
    ctx.strokeStyle = 'rgba(155,82,135,0.025)';
    ctx.lineWidth = 0.5;
    for (let y = 0; y < h; y += 3) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Perspective grid (converging lines)
    ctx.strokeStyle = 'rgba(155,82,135,0.04)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 12; i++) {
      const x = (w / 12) * i;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(w * 0.5 + (x - w * 0.5) * 0.6, h);
      ctx.stroke();
    }
    for (let j = 0; j <= 8; j++) {
      const y = (h / 8) * j;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Zones
    if (showZones) {
      drawZone(ctx, w, h, 0.04, 0.67, 0.22, 0.28, 'rgba(63,163,101,0.14)', 'rgba(63,163,101,0.6)', '🍲  Food Bowl Zone');
      drawZone(ctx, w, h, 0.74, 0.04, 0.23, 0.30, 'rgba(217,79,79,0.14)', 'rgba(217,79,79,0.6)', '⚠  Secluded Corner');
    }

    // Residents
    residents.forEach(r => {
      updateWander(r, w, h);
      const px = r.x * w, py = r.y * h;

      // Trail
      if (showTrails) {
        r.trail.push({ x: px, y: py });
        if (r.trail.length > 30) r.trail.shift();
        drawTrail(ctx, r.trail, r.color);
      }

      // Bounding box with corner brackets (not full rect)
      drawDetectionBox(ctx, px, py, r.boxW, r.boxH, r.color);

      // Tag
      drawTag(ctx, px - r.boxW / 2, py - r.boxH / 2 - 22, r);
    });
  }

  function drawZone(ctx, w, h, nx, ny, nw, nh, fill, stroke, label) {
    const x = nx * w, y = ny * h, zw = nw * w, zh = nh * h;
    ctx.fillStyle = fill;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    roundRect(ctx, x, y, zw, zh, 10);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = stroke;
    ctx.font = '600 11px "DM Sans", sans-serif';
    ctx.fillText(label, x + 10, y + 22);
  }

  function drawTrail(ctx, trail, color) {
    if (trail.length < 2) return;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.8;
    ctx.setLineDash([4, 4]);
    ctx.globalAlpha = 0.4;
    ctx.beginPath();
    trail.forEach((p, i) => {
      i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
  }

  function drawDetectionBox(ctx, cx, cy, bw, bh, color) {
    const x = cx - bw / 2, y = cy - bh / 2;
    const corner = 12;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    // Top-Left
    ctx.beginPath(); ctx.moveTo(x, y + corner); ctx.lineTo(x, y); ctx.lineTo(x + corner, y); ctx.stroke();
    // Top-Right
    ctx.beginPath(); ctx.moveTo(x + bw - corner, y); ctx.lineTo(x + bw, y); ctx.lineTo(x + bw, y + corner); ctx.stroke();
    // Bottom-Left
    ctx.beginPath(); ctx.moveTo(x, y + bh - corner); ctx.lineTo(x, y + bh); ctx.lineTo(x + corner, y + bh); ctx.stroke();
    // Bottom-Right
    ctx.beginPath(); ctx.moveTo(x + bw - corner, y + bh); ctx.lineTo(x + bw, y + bh); ctx.lineTo(x + bw, y + bh - corner); ctx.stroke();

    // Centroid dot
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(cx, cy, 3, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawTag(ctx, x, y, r) {
    const label = `${r.species.toUpperCase()} #${r.id}  ${r.name}`;
    ctx.font = '600 10px "DM Sans", sans-serif';
    const tw = ctx.measureText(label).width + 16;
    ctx.fillStyle = r.color;
    ctx.beginPath();
    roundRect(ctx, x, y, tw, 18, 5);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.fillText(label, x + 8, y + 13);
  }

  function updateWander(r) {
    const dx = r.tx - r.x, dy = r.ty - r.y;
    if (Math.hypot(dx, dy) < 0.015) {
      if (r.id === 3) {
        // Shanti barely moves, stays corner
        r.tx = 0.79 + Math.random() * 0.13;
        r.ty = 0.08 + Math.random() * 0.18;
      } else {
        r.tx = 0.12 + Math.random() * 0.72;
        r.ty = 0.18 + Math.random() * 0.62;
      }
    }
    r.x += dx * r.speed;
    r.y += dy * r.speed;
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
  }

  function toggleZones() { showZones = !showZones; return showZones; }
  function toggleTrails() { showTrails = !showTrails; return showTrails; }

  return { init, toggleZones, toggleTrails };
})();
