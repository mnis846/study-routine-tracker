/**
 * Interactive study garden grove — touch-pan canvas of planted trees.
 */
(function (global) {
  function drawTree(ctx, x, y, tree, t) {
    const growth = tree.growth || "sapling";
    const scale =
      growth === "fruiting" ? 1.15 : growth === "mature" ? 1.05 : growth === "young" ? 0.9 : 0.75;
    const sway = Math.sin(t * 0.002 + x * 0.01) * 3;

    // ground shadow
    ctx.fillStyle = "rgba(0,0,0,0.18)";
    ctx.beginPath();
    ctx.ellipse(x, y + 8, 22 * scale, 7 * scale, 0, 0, Math.PI * 2);
    ctx.fill();

    // trunk
    ctx.strokeStyle = tree.phase === "sprint" ? "#5D4037" : "#6D4C41";
    ctx.lineWidth = 6 * scale;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(x, y + 6);
    ctx.quadraticCurveTo(x + sway, y - 18 * scale, x + sway * 0.5, y - 40 * scale);
    ctx.stroke();

    // canopy
    const cy = y - 42 * scale;
    const cx = x + sway * 0.5;
    const greens =
      tree.phase === "sprint"
        ? ["#1B5E20", "#2E7D32", "#43A047"]
        : ["#33691E", "#558B2F", "#7CB342"];
    for (let i = 0; i < 3; i++) {
      ctx.fillStyle = greens[i];
      ctx.beginPath();
      ctx.ellipse(cx + (i - 1) * 8, cy + i * 2, (20 - i * 2) * scale, (14 - i) * scale, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    if (tree.has_fruit) {
      ctx.fillStyle = "#E53935";
      [[-8, -4], [6, 0], [0, 6]].forEach(([dx, dy]) => {
        ctx.beginPath();
        ctx.arc(cx + dx * scale, cy + dy * scale, 3.2 * scale, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    // label
    ctx.fillStyle = "rgba(255,255,255,0.75)";
    ctx.font = `${Math.max(10, 11 * scale)}px system-ui,sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText(`#${tree.tree_no}`, x, y + 22);
  }

  function createGarden(canvas) {
    const ctx = canvas.getContext("2d");
    let life = null;
    let panX = 0;
    let panY = 0;
    let drag = false;
    let lx = 0;
    let ly = 0;
    let raf = 0;
    let t0 = performance.now();

    function layout() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = canvas.clientWidth || 360;
      const h = canvas.clientHeight || 320;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return { w, h };
    }

    function worldSize(trees) {
      const cols = 6;
      const rows = Math.max(1, Math.ceil((trees.length || 1) / cols));
      return { ww: 120 + cols * 72, wh: 160 + rows * 90, cols };
    }

    function clamp(w, h, ww, wh) {
      const minX = Math.min(0, w - ww);
      const minY = Math.min(0, h - wh);
      panX = Math.max(minX, Math.min(0, panX));
      panY = Math.max(minY, Math.min(0, panY));
    }

    function frame(now) {
      const { w, h } = layout();
      const trees = life?.trees || [];
      const { ww, wh, cols } = worldSize(trees);
      clamp(w, h, ww, wh);
      const t = now - t0;

      // sky
      const g = ctx.createLinearGradient(0, 0, 0, h);
      const mood = life?.mood || "resting";
      if (mood === "flourishing") {
        g.addColorStop(0, "#0ea5e9");
        g.addColorStop(1, "#064e3b");
      } else if (mood === "thirsty") {
        g.addColorStop(0, "#78716c");
        g.addColorStop(1, "#44403c");
      } else {
        g.addColorStop(0, "#1e3a5f");
        g.addColorStop(1, "#0a1220");
      }
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      ctx.translate(panX, panY);

      // path / ground
      ctx.fillStyle = "#1a2e1a";
      ctx.fillRect(0, 80, ww, wh);
      ctx.fillStyle = "rgba(34,197,94,0.08)";
      for (let i = 0; i < 12; i++) {
        ctx.fillRect(20 + i * 70, 100, 40, wh);
      }

      // next plot ghost
      if (life?.next_tree) {
        const n = life.next_tree.tree_no;
        const col = (n - 1) % cols;
        const row = Math.floor((n - 1) / cols);
        const x = 56 + col * 72;
        const y = 130 + row * 90;
        ctx.strokeStyle = "rgba(255,255,255,0.25)";
        ctx.setLineDash([6, 6]);
        ctx.strokeRect(x - 28, y - 70, 56, 90);
        ctx.setLineDash([]);
        ctx.fillStyle = "rgba(255,255,255,0.45)";
        ctx.font = "11px system-ui";
        ctx.textAlign = "center";
        ctx.fillText(`Next #${n}`, x, y + 30);
        if (life.days_to_next_tree > 0) {
          ctx.fillText(`${life.days_to_next_tree}d`, x, y + 44);
        }
      }

      trees.forEach((tree, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        const x = 56 + col * 72;
        const y = 130 + row * 90;
        drawTree(ctx, x, y, tree, t);
      });

      ctx.restore();

      // HUD
      ctx.fillStyle = "rgba(15,23,42,0.55)";
      ctx.beginPath();
      roundRect(ctx, 10, 10, Math.min(w - 20, 280), 54, 12);
      ctx.fill();
      ctx.fillStyle = "#f8fafc";
      ctx.font = "600 13px system-ui";
      ctx.textAlign = "left";
      ctx.fillText(
        `${life?.harvest_emoji || "🌱"} ${life?.harvest_label || "Grove"} · ${life?.tree_count || 1}/${life?.max_trees || 77} trees`,
        22,
        32
      );
      ctx.fillStyle = "rgba(248,250,252,0.75)";
      ctx.font = "12px system-ui";
      ctx.fillText("Drag / swipe to explore the path", 22, 50);

      raf = requestAnimationFrame(frame);
    }

    function roundRect(c, x, y, w, h, r) {
      c.moveTo(x + r, y);
      c.arcTo(x + w, y, x + w, y + h, r);
      c.arcTo(x + w, y + h, x, y + h, r);
      c.arcTo(x, y + h, x, y, r);
      c.arcTo(x, y, x + w, y, r);
      c.closePath();
    }

    function onDown(clientX, clientY) {
      drag = true;
      lx = clientX;
      ly = clientY;
      canvas.classList.add("grabbing");
    }
    function onMove(clientX, clientY) {
      if (!drag) return;
      panX += clientX - lx;
      panY += clientY - ly;
      lx = clientX;
      ly = clientY;
    }
    function onUp() {
      drag = false;
      canvas.classList.remove("grabbing");
    }

    canvas.addEventListener("mousedown", (e) => onDown(e.clientX, e.clientY));
    window.addEventListener("mousemove", (e) => onMove(e.clientX, e.clientY));
    window.addEventListener("mouseup", onUp);
    canvas.addEventListener(
      "touchstart",
      (e) => {
        if (!e.touches[0]) return;
        e.preventDefault();
        onDown(e.touches[0].clientX, e.touches[0].clientY);
      },
      { passive: false }
    );
    canvas.addEventListener(
      "touchmove",
      (e) => {
        if (!e.touches[0]) return;
        e.preventDefault();
        onMove(e.touches[0].clientX, e.touches[0].clientY);
      },
      { passive: false }
    );
    canvas.addEventListener("touchend", onUp);
    canvas.addEventListener("touchcancel", onUp);

    function setLife(next) {
      life = next;
      // center on latest trees when data changes
      const trees = life?.trees || [];
      if (trees.length) {
        const cols = 6;
        const last = trees.length - 1;
        const col = last % cols;
        const row = Math.floor(last / cols);
        const { w, h } = layout();
        panX = Math.min(0, w / 2 - (56 + col * 72));
        panY = Math.min(0, h / 2 - (130 + row * 90));
      }
    }

    function start() {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(frame);
    }

    function stop() {
      cancelAnimationFrame(raf);
    }

    return { setLife, start, stop, layout };
  }

  global.SRTGarden = { createGarden };
})(window);
