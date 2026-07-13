"""Panoramic study path — 55 foundation trees + exam sprint, drag to explore."""

import json

import streamlit.components.v1 as components

from garden_life import MAX_GROVE_TREES, FOUNDATION_TREE_TARGET
from profile import FIRST_NAME


def render_garden_world(garden_state, height=780):
    life = garden_state.get("life") or garden_state.get("vitality") or {}
    data = {
        "xp": garden_state["xp"],
        "life": life.get("life", 40),
        "mood": life.get("mood", "growing"),
        "goalStreak": life.get("goal_streak", 0),
        "harvestTier": life.get("harvest_tier", "sprout"),
        "harvestLabel": life.get("harvest_label", "First Tree"),
        "harvestEmoji": life.get("harvest_emoji", "🌱"),
        "trees": life.get("trees", []),
        "treeCount": life.get("tree_count", 1),
        "unlockedCount": life.get("unlocked_count", 1),
        "maxTrees": life.get("max_trees", MAX_GROVE_TREES),
        "foundationTarget": life.get("foundation_target", FOUNDATION_TREE_TARGET),
        "foundationTrees": life.get("foundation_trees", 1),
        "treesToFoundation": life.get("trees_to_foundation_full", FOUNDATION_TREE_TARGET - 1),
        "journeyPhase": life.get("journey_phase", "foundation"),
        "hasFruit": life.get("has_fruit", False),
        "sakuraCount": life.get("sakura_count", 0),
        "waterLevel": life.get("water_level", 0),
        "waterPct": life.get("water_pct", 0),
        "todayHours": life.get("today_hours", 0),
        "dailyGoal": life.get("daily_goal", 6),
        "goalMet": life.get("goal_met", False),
        "daysToNextTree": life.get("days_to_next_tree", 4),
        "nextTree": life.get("next_tree"),
        "weekDays": life.get("week_days", []),
        "hint": life.get("hint", ""),
        "firstName": FIRST_NAME,
    }
    payload = json.dumps(data)
    min_h = max(580, height - 40)

    html = f"""
    <div class="zen-wrap">
      <canvas id="zenCanvas" class="zen-canvas"></canvas>
      <div class="zen-hint">Drag the path · 1 tree / 4 study days · {FOUNDATION_TREE_TARGET} foundation · {MAX_GROVE_TREES} total</div>
    </div>
    <style>
      .zen-wrap {{
        position: relative; width: 100vw; margin-left: calc(-50vw + 50%);
        min-height: {min_h}px; background: #0a1220;
        overflow: hidden; box-shadow: 0 20px 60px rgba(10,18,32,0.5);
      }}
      .zen-canvas {{ width: 100%; min-height: {min_h}px; display: block; cursor: grab; touch-action: none; }}
      .zen-canvas.grab {{ cursor: grabbing; }}
      .zen-hint {{
        position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
        background: rgba(255,255,255,0.07); backdrop-filter: blur(12px);
        color: rgba(255,255,255,0.85); border: 1px solid rgba(255,255,255,0.15);
        padding: 9px 20px; border-radius: 24px;
        font: 600 10px/1.4 'Segoe UI',system-ui,sans-serif; pointer-events: none;
      }}
    </style>
    <script>
    (function() {{
      const D = {payload};
      const PER_ROW = 8;
      const TREE_SP = 108;
      const ROW_H = 118;
      const cvs = document.getElementById('zenCanvas');
      const ctx = cvs.getContext('2d');
      let W, H, t = 0, panX = 0, panY = 0, drag = false, dx = 0, dy = 0;
      const petals = [], fireflies = [];
      const rows = Math.ceil(D.maxTrees / PER_ROW);
      const WW = 200 + PER_ROW * TREE_SP;
      const WH = 420 + rows * ROW_H;

      function rng(n) {{
        let s = (n % 2147483646) || 1;
        return () => {{ s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }};
      }}

      function treeWorldPos(slot) {{
        const row = Math.floor(slot / PER_ROW);
        const col = slot % PER_ROW;
        const zig = row % 2 === 1;
        const c = zig ? (PER_ROW - 1 - col) : col;
        return {{
          x: 120 + c * TREE_SP,
          y: 480 + row * ROW_H + Math.sin(c * 0.65 + row) * 14,
          row, col: c
        }};
      }}

      function screenPos(wp) {{
        return {{ x: wp.x + panX, y: wp.y + panY }};
      }}

      function inView(sx, sy, margin) {{
        margin = margin || 80;
        return sx > -margin && sx < W + margin && sy > -margin && sy < H + margin;
      }}

      function initParticles() {{
        petals.length = 0; fireflies.length = 0;
        const r = rng(7000 + D.sakuraCount * 31);
        D.trees.forEach(tree => {{
          if (!tree.has_sakura) return;
          for (let i = 0; i < 6; i++) {{
            petals.push({{
              slot: tree.slot, ox: (r() - 0.5) * 50, oy: (r() - 0.5) * 40,
              vx: 0.15 + r() * 0.35, vy: 0.25 + r() * 0.35,
              rot: r() * 6.28, spin: (r() - 0.5) * 0.025, s: 1.5 + r() * 2.5
            }});
          }}
        }});
        if (D.mood === 'flourishing' || D.harvestTier === 'golden') {{
          for (let i = 0; i < 14; i++) fireflies.push({{ x: r(), y: r(), ph: r() * 6.28 }});
        }}
      }}

      function resize() {{
        let rw = cvs.parentElement.clientWidth || 920;
        if (rw < 80) rw = Math.min(1100, window.innerWidth - 16);
        W = cvs.width = Math.floor(rw);
        H = cvs.height = Math.max({min_h}, Math.floor(W * 0.55));
        initParticles();
        const last = D.treeCount > 0 ? treeWorldPos(D.trees[D.treeCount - 1].slot) : treeWorldPos(0);
        panX = W * 0.42 - last.x;
        panY = H * 0.55 - last.y;
        clampPan();
      }}

      function clampPan() {{
        panX = Math.min(120, Math.max(W - WW - 80, panX));
        panY = Math.min(80, Math.max(H - WH - 60, panY));
      }}

      function drawSky() {{
        const golden = D.harvestTier === 'golden';
        const g = ctx.createLinearGradient(0, 0, 0, H);
        if (golden) {{
          g.addColorStop(0, '#1a237e'); g.addColorStop(0.35, '#ff8a65'); g.addColorStop(0.7, '#ffcc80'); g.addColorStop(1, '#1b3a2a');
        }} else if (D.journeyPhase === 'mains') {{
          g.addColorStop(0, '#1a0a2e'); g.addColorStop(0.4, '#4a1942'); g.addColorStop(0.7, '#7b2d5e'); g.addColorStop(1, '#1a2e22');
        }} else {{
          g.addColorStop(0, '#0d1b2a'); g.addColorStop(0.4, '#1b3344'); g.addColorStop(0.65, '#4a6070'); g.addColorStop(0.85, '#8a9aaa'); g.addColorStop(1, '#1a2e22');
        }}
        ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      }}

      function drawWorldBg() {{
        ctx.save(); ctx.translate(panX, panY);
        for (let row = 0; row < rows; row++) {{
          const isSprint = row >= Math.floor(D.foundationTarget / PER_ROW);
          const y = 440 + row * ROW_H;
          const grd = ctx.createLinearGradient(0, y, 0, y + ROW_H + 40);
          grd.addColorStop(0, isSprint ? '#2e4a32' : '#2a4530');
          grd.addColorStop(1, isSprint ? '#1a3020' : '#152818');
          ctx.fillStyle = grd;
          ctx.fillRect(0, y, WW, ROW_H + 50);
        }}
        ctx.restore();
      }}

      function drawRiver() {{
        ctx.save(); ctx.translate(panX, panY);
        ctx.strokeStyle = 'rgba(79,195,247,0.35)'; ctx.lineWidth = 28; ctx.lineCap = 'round';
        ctx.beginPath();
        for (let row = 0; row < rows; row++) {{
          const y = 530 + row * ROW_H;
          const x1 = row % 2 ? 80 : WW - 80;
          const x2 = row % 2 ? WW - 80 : 80;
          if (row === 0) ctx.moveTo(x1, y);
          else ctx.lineTo(x1, y);
          ctx.quadraticCurveTo((x1 + x2) / 2, y + 30, x2, y);
        }}
        ctx.stroke();
        ctx.restore();
      }}

      function drawPath() {{
        ctx.save(); ctx.translate(panX, panY);
        ctx.strokeStyle = 'rgba(210,180,140,0.35)'; ctx.lineWidth = 14; ctx.lineCap = 'round';
        ctx.beginPath();
        D.trees.forEach((tree, i) => {{
          const p = treeWorldPos(tree.slot);
          if (i === 0) ctx.moveTo(p.x, p.y + 10);
          else ctx.lineTo(p.x, p.y + 10);
        }});
        if (D.nextTree) {{
          const np = treeWorldPos(D.nextTree.tree_no - 1);
          ctx.setLineDash([8, 10]); ctx.stroke();
          ctx.setLineDash([]);
          ctx.strokeStyle = 'rgba(255,255,255,0.2)'; ctx.lineWidth = 8;
          const last = D.trees[D.treeCount - 1];
          const lp = treeWorldPos(last.slot);
          ctx.beginPath(); ctx.moveTo(lp.x, lp.y + 10); ctx.lineTo(np.x, np.y + 10); ctx.stroke();
        }} else ctx.stroke();
        ctx.restore();
      }}

      function drawMilestoneGate(treeNo, label, color) {{
        const slot = treeNo - 1;
        const wp = treeWorldPos(slot);
        const sp = screenPos(wp);
        if (!inView(sp.x, sp.y, 200)) return;
        ctx.save(); ctx.translate(sp.x, sp.y - 55);
        ctx.fillStyle = color;
        ctx.fillRect(-55, -50, 10, 70); ctx.fillRect(45, -50, 10, 70);
        ctx.fillRect(-62, -52, 124, 10); ctx.fillRect(-50, -28, 100, 7);
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        ctx.font = '700 10px Segoe UI,sans-serif'; ctx.textAlign = 'center';
        ctx.fillText(label, 0, -58);
        ctx.restore();
      }}

      function growthScale(tree, lod) {{
        const m = {{ sapling: 0.5, young: 0.68, mature: 0.88, fruiting: 1.0, sakura: 1.05 }};
        let s = (m[tree.growth] || 0.7) * (lod === 'far' ? 0.75 : 1);
        return s * (1 + Math.sin(t * 0.03 + tree.slot) * 0.012);
      }}

      function drawTree(tree, lod) {{
        const wp = treeWorldPos(tree.slot);
        const sp = screenPos(wp);
        if (!inView(sp.x, sp.y)) return;

        const s = growthScale(tree, lod);
        const sway = Math.sin(t / 48 + tree.slot * 0.9) * (lod === 'far' ? 1 : 2.5);
        const x = sp.x, y = sp.y;

        ctx.fillStyle = 'rgba(0,0,0,0.15)';
        ctx.beginPath(); ctx.ellipse(x, y + 5, 22 * s, 7 * s, 0, 0, Math.PI * 2); ctx.fill();

        if (lod === 'far') {{
          ctx.fillStyle = tree.has_sakura ? '#f48fb1' : '#2e7d32';
          ctx.beginPath(); ctx.moveTo(x + sway, y - 28 * s);
          ctx.lineTo(x - 14 * s + sway, y); ctx.lineTo(x + 14 * s + sway, y); ctx.closePath(); ctx.fill();
          return;
        }}

        ctx.fillStyle = '#5d4037';
        ctx.fillRect(x - 5 * s + sway * 0.15, y - 8 * s, 10 * s, 32 * s);

        if (tree.has_sakura) {{
          [[0,-42,26],[-18,-30,16],[16,-32,14],[-6,-52,12]].forEach(([bx,by,br]) => {{
            const rg = ctx.createRadialGradient(x+bx*s+sway, y+by*s, 0, x+bx*s+sway, y+by*s, br*s);
            rg.addColorStop(0, '#fce4ec'); rg.addColorStop(1, '#ec407a');
            ctx.fillStyle = rg;
            ctx.beginPath(); ctx.arc(x+bx*s+sway, y+by*s, br*s, 0, Math.PI*2); ctx.fill();
          }});
        }} else {{
          const a = 0.7 + D.waterLevel * 0.3;
          ctx.fillStyle = `rgba(46,125,50,${{a}})`;
          ctx.beginPath(); ctx.arc(x+sway, y-36*s, 22*s, 0, Math.PI*2); ctx.fill();
          ctx.fillStyle = `rgba(67,160,71,${{a*0.85}})`;
          ctx.beginPath(); ctx.arc(x-12*s+sway, y-28*s, 14*s, 0, Math.PI*2); ctx.fill();
          if (tree.has_fruit) {{
            [[-8,-38],[6,-46],[14,-32]].forEach(([fx,fy], i) => {{
              ctx.fillStyle = ['#e53935','#fb8c00','#fdd835'][i];
              ctx.beginPath(); ctx.arc(x+fx*s+sway, y+fy*s, 4*s, 0, Math.PI*2); ctx.fill();
            }});
          }}
        }}

        if (s >= 0.75) {{
          ctx.fillStyle = 'rgba(30,25,20,0.8)';
          ctx.beginPath(); ctx.roundRect(x - 28, y + 10, 56, 20, 3); ctx.fill();
          ctx.fillStyle = '#f0ebe3';
          ctx.font = `700 ${{7*s}}px sans-serif`; ctx.textAlign = 'center';
          const tag = tree.test_no ? ('T' + tree.test_no) : ('#' + tree.tree_no);
          ctx.fillText(tag, x, y + 22);
          if (tree.has_sakura && tree.score) {{
            ctx.fillStyle = '#f8bbd9'; ctx.font = `600 ${{6*s}}px sans-serif`;
            ctx.fillText('🌸'+tree.score+'%', x, y - 52*s);
          }}
        }}
      }}

      function drawNextPlot() {{
        if (!D.nextTree) return;
        const wp = treeWorldPos(D.nextTree.tree_no - 1);
        const sp = screenPos(wp);
        if (!inView(sp.x, sp.y)) return;
        const pulse = 0.25 + Math.sin(t * 0.05) * 0.15;
        ctx.strokeStyle = `rgba(255,255,255,${{pulse}})`;
        ctx.setLineDash([5, 7]); ctx.lineWidth = 2;
        ctx.beginPath(); ctx.ellipse(sp.x, sp.y + 14, 30, 10, 0, 0, Math.PI*2); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.font = '600 9px sans-serif'; ctx.textAlign = 'center';
        ctx.fillText('#' + D.nextTree.tree_no + ' · ' + D.nextTree.days_away + 'd', sp.x, sp.y + 18);
      }}

      function drawPetals() {{
        petals.forEach(p => {{
          const wp = treeWorldPos(p.slot);
          const sp = screenPos(wp);
          p.ox += p.vx; p.oy += p.vy; p.rot += p.spin;
          if (p.oy > 60) {{ p.oy = -30; p.ox = (Math.random()-0.5)*40; }}
          if (!inView(sp.x + p.ox, sp.y + p.oy, 0)) return;
          ctx.save(); ctx.translate(sp.x + p.ox, sp.y + p.oy); ctx.rotate(p.rot);
          ctx.fillStyle = '#f8bbd9';
          ctx.beginPath(); ctx.ellipse(0, 0, p.s, p.s*0.55, 0, 0, Math.PI*2); ctx.fill();
          ctx.restore();
        }});
      }}

      function drawWatering() {{
        if (D.waterLevel < 0.05 || D.treeCount === 0) return;
        const recent = D.trees.slice(-6);
        recent.forEach(tree => {{
          const wp = treeWorldPos(tree.slot);
          const sp = screenPos(wp);
          if (!inView(sp.x, sp.y)) return;
          ctx.strokeStyle = `rgba(100,200,255,${{0.25 + D.waterLevel * 0.4}})`;
          ctx.lineWidth = 1.5;
          ctx.beginPath(); ctx.moveTo(sp.x - 20, sp.y - 70);
          ctx.quadraticCurveTo(sp.x, sp.y - 90, sp.x, sp.y - 45 * growthScale(tree, 'near'));
          ctx.stroke();
        }});
      }}

      function drawMinimap() {{
        const mw = 120, mh = 56, mx = W - mw - 14, my = H - mh - 14;
        ctx.fillStyle = 'rgba(10,18,32,0.85)'; ctx.strokeStyle = 'rgba(255,255,255,0.15)';
        ctx.beginPath(); ctx.roundRect(mx, my, mw, mh, 8); ctx.fill(); ctx.stroke();
        const sx = (mw - 8) / WW, sy = (mh - 8) / WH;
        ctx.fillStyle = '#1b4332'; ctx.fillRect(mx+4, my+4, mw-8, mh-8);
        const gateY = Math.floor(D.foundationTarget / PER_ROW) * ROW_H;
        ctx.fillStyle = 'rgba(255,183,77,0.25)';
        ctx.fillRect(mx+4, my+4 + gateY * sy, mw-8, 3);
        D.trees.forEach(tree => {{
          const wp = treeWorldPos(tree.slot);
          ctx.fillStyle = tree.has_sakura ? '#f48fb1' : tree.has_fruit ? '#ff9800' : '#66bb6a';
          ctx.fillRect(mx+4+wp.x*sx-1, my+4+wp.y*sy-1, 3, 3);
        }});
        ctx.strokeStyle = '#fff';
        ctx.strokeRect(mx+4-panX*sx, my+4-panY*sy, W*sx, H*sy);
        ctx.fillStyle = 'rgba(255,255,255,0.5)'; ctx.font = '600 7px sans-serif';
        ctx.fillText('FOUNDATION', mx+6, my+10);
        ctx.fillText('SPRINT', mx+6, my+mh-6);
      }}

      function drawHud() {{
        ctx.fillStyle = 'rgba(8,14,28,0.82)';
        ctx.strokeStyle = 'rgba(255,255,255,0.1)';
        ctx.beginPath(); ctx.roundRect(14, 14, W - 28, 108, 14); ctx.fill(); ctx.stroke();

        ctx.fillStyle = '#fff';
        ctx.font = '700 15px Segoe UI,sans-serif'; ctx.textAlign = 'left';
        ctx.fillText(D.harvestEmoji + ' ' + D.firstName + "'s 220-Day Path", 30, 40);
        ctx.font = '600 11px Segoe UI,sans-serif'; ctx.fillStyle = 'rgba(255,255,255,0.75)';
        ctx.fillText(
          D.treeCount + '/' + D.maxTrees + ' trees · Foundation ' + D.foundationTrees + '/' + D.foundationTarget +
          ' · ' + D.goalStreak + 'd streak · 💧' + D.waterPct + '%',
          30, 60
        );
        ctx.font = '500 10px Segoe UI,sans-serif'; ctx.fillStyle = 'rgba(255,255,255,0.5)';
        const hint = (D.hint || '').length > 95 ? D.hint.slice(0, 92) + '…' : (D.hint || '');
        ctx.fillText(hint, 30, 78);

        const bw = W - 60;
        ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(30, 88, bw, 7);
        ctx.fillStyle = '#4fc3f7'; ctx.fillRect(30, 88, bw * D.waterLevel, 7);

        const pw = bw * (D.foundationTrees / D.foundationTarget);
        ctx.fillStyle = 'rgba(102,187,106,0.35)'; ctx.fillRect(30, 100, pw, 4);
        ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.font = '600 8px sans-serif';
        ctx.fillText('Foundation grove progress', 30, 114);

        if (D.daysToNextTree > 0) {{
          ctx.fillStyle = '#ffab91'; ctx.font = '600 10px sans-serif'; ctx.textAlign = 'right';
          ctx.fillText(D.daysToNextTree + 'd → tree #' + (D.treeCount + 1), W - 30, 114);
        }}
      }}

      function frame() {{
        t++;
        if (W < 80) {{ resize(); requestAnimationFrame(frame); return; }}
        drawSky();
        drawWorldBg();
        drawRiver();
        drawPath();
        drawMilestoneGate(D.foundationTarget, 'FOUNDATION COMPLETE · TREE ' + D.foundationTarget, '#ff8f00');
        drawMilestoneGate(D.foundationTarget + 1, 'EXAM SPRINT', '#ce93d8');
        D.trees.forEach(tree => {{
          const wp = treeWorldPos(tree.slot);
          const sp = screenPos(wp);
          const lod = inView(sp.x, sp.y, 200) ? 'near' : (inView(sp.x, sp.y, 0) ? 'far' : 'skip');
          if (lod !== 'skip') drawTree(tree, lod);
        }});
        drawNextPlot();
        drawWatering();
        drawPetals();
        drawHud();
        drawMinimap();
        requestAnimationFrame(frame);
      }}

      cvs.addEventListener('mousedown', e => {{ drag=true; dx=e.clientX; dy=e.clientY; cvs.classList.add('grab'); }});
      window.addEventListener('mouseup', () => {{ drag=false; cvs.classList.remove('grab'); }});
      window.addEventListener('mousemove', e => {{
        if (!drag) return;
        panX += e.clientX - dx; panY += e.clientY - dy; dx=e.clientX; dy=e.clientY;
        clampPan();
      }});
      resize();
      if (typeof ResizeObserver !== 'undefined') new ResizeObserver(resize).observe(cvs.parentElement);
      setTimeout(resize, 400);
      frame();
    }})();
    </script>
    """
    components.html(html, height=height, scrolling=False)