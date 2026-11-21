"""P5 Script: Render self-contained interactive 1,633-frame HTML diagnostic gallery with real image rendering."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import cv2
import numpy as np

from geminicode.src.common import (
    PROJECT_ROOT,
    save_json,
    load_csv,
    read_uint8_bmp,
    parse_anchors_file,
)

def export_single_image(inv: dict, images_dir: Path, quality: int = 75, max_dim: int = 2560):
    g = inv['group']
    fid = int(inv['frame_id'])
    out_path = images_dir / f"{g}_{fid}.jpg"
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path.name
    try:
        img = read_uint8_bmp(inv['current'])
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            nw, nh = int(round(w * scale)), int(round(h * scale))
            img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(out_path), img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return out_path.name
    except Exception as e:
        print(f"Warning: Failed to export image for {g} frame {fid}: {e}", flush=True)
        return None

def export_gallery_images(inventory_rows: list[dict], images_dir: Path, max_workers: int = 8, quality: int = 75, max_dim: int = 2560):
    images_dir.mkdir(parents=True, exist_ok=True)
    total = len(inventory_rows)
    print(f"Exporting gallery images to {images_dir} ({total} frames, workers={max_workers})...", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(export_single_image, row, images_dir, quality, max_dim) for row in inventory_rows]
        for f in futures:
            f.result()
            done += 1
            if done % 250 == 0 or done == total:
                print(f"  Exported/verified {done}/{total} images...", flush=True)
    print(f"Image export complete: {total} frames checked/saved.", flush=True)

def build_gallery(run_dir: Path, skip_images: bool = False):
    run_dir = Path(run_dir).resolve()
    manifest_csv = run_dir / 'manifests/input_inventory.csv'
    assert manifest_csv.exists(), f"Missing input inventory: {manifest_csv}"
    
    inventory_rows = load_csv(manifest_csv)
    gallery_dir = run_dir / 'galleries'
    images_dir = gallery_dir / 'images'
    
    # Export real preview images if not skipped
    if not skip_images:
        export_gallery_images(inventory_rows, images_dir)
    
    # Load all results from dev and locked if available
    pred_map = {}
    for split in ['dev', 'locked']:
        res_csv = run_dir / f'raw_inference/results_{split}_FULL.csv'
        if res_csv.exists():
            for r in load_csv(res_csv):
                pred_map[(r['group'], int(r['frame_id']))] = r
                
    # Load offline GT evaluations if available
    gt_map = {}
    for split in ['dev', 'locked']:
        det_csv = run_dir / f'offline_evaluation/detailed_errors_{split}_FULL.csv'
        if det_csv.exists():
            for r in load_csv(det_csv):
                gt_map[(r['group'], int(r['frame_id']))] = r

    # Load diagnostics from inference jsonl if available (roi, notch_root)
    diag_map = {}
    for split in ['dev', 'locked']:
        jsonl_path = run_dir / f'raw_inference/inference_{split}_FULL.jsonl'
        if jsonl_path.exists():
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            g = rec.get('group')
                            fid = int(rec.get('frame_id'))
                            diag = rec.get('diagnostics', {})
                            diag_map[(g, fid)] = {
                                'roi': diag.get('roi'),
                                'notch_root': diag.get('notch_root'),
                            }
                        except Exception:
                            pass

    # Load anchors (p1, p2)
    anchor_map = {}
    anchor_sources = {
        'group_a': PROJECT_ROOT / 'data/anchors/开发组A_基准点坐标.txt',
        'three_point_bend': PROJECT_ROOT / 'data/anchors/三点弯_基准点坐标.txt',
        'group_c': PROJECT_ROOT / 'data/anchors/验证组C_基准点坐标.txt',
    }
    for g, path in anchor_sources.items():
        if path.exists():
            try:
                anchor_map[g] = parse_anchors_file(path)
            except Exception:
                pass
                
    # Assemble index of all 1,633 frames
    index_items = []
    for inv in inventory_rows:
        g = inv['group']
        fid = int(inv['frame_id'])
        pred = pred_map.get((g, fid), {})
        gt_eval = gt_map.get((g, fid), {})
        diag = diag_map.get((g, fid), {})
        
        p1, p2 = None, None
        if g in anchor_map and fid in anchor_map[g]:
            p1, p2 = anchor_map[g][fid]
        
        item = {
            'group': g,
            'frame_id': fid,
            'tracking_num': int(inv['tracking_num']),
            'role': inv.get('role', 'UNKNOWN'),
            'width': int(inv.get('width', 1856)),
            'height': int(inv.get('height', 2072)),
            'status': pred.get('status', 'PENDING'),
            'tip_x': float(pred['tip_x']) if pred.get('tip_x') not in [None, 'None', ''] else None,
            'tip_y': float(pred['tip_y']) if pred.get('tip_y') not in [None, 'None', ''] else None,
            'selected_track_id': pred.get('selected_track_id'),
            'preferred_uncertain_tip_x': float(pred['preferred_uncertain_tip_x']) if pred.get('preferred_uncertain_tip_x') not in [None, 'None', ''] else None,
            'preferred_uncertain_tip_y': float(pred['preferred_uncertain_tip_y']) if pred.get('preferred_uncertain_tip_y') not in [None, 'None', ''] else None,
            'fixed_ref_channel': pred.get('fixed_ref_channel', 'UNKNOWN'),
            'prev_ref_channel': pred.get('prev_ref_channel', 'UNKNOWN'),
            'failure_stage': pred.get('failure_stage'),
            'failure_reason': pred.get('failure_reason'),
            'budget_exhausted': pred.get('budget_exhausted') in [True, 'True', '1'],
            'time_ms': float(pred['time_ms']) if pred.get('time_ms') not in [None, 'None', ''] else None,
            'flags': pred.get('flags', '').split(';') if pred.get('flags') else [],
            'has_gt': (g, fid) in gt_map,
            'gt_x': float(gt_eval['gt_x']) if gt_eval.get('gt_x') not in [None, 'None', ''] else None,
            'gt_y': float(gt_eval['gt_y']) if gt_eval.get('gt_y') not in [None, 'None', ''] else None,
            'error_px': float(gt_eval['error_px']) if gt_eval.get('error_px') not in [None, 'None', ''] else None,
            'hit10': gt_eval.get('hit10') in [True, 'True', '1'],
            'oracle_min_error_px': float(gt_eval['oracle_min_error_px']) if gt_eval.get('oracle_min_error_px') not in [None, 'None', ''] else None,
            'roi': diag.get('roi'),
            'notch_root': diag.get('notch_root'),
            'p1': p1,
            'p2': p2,
            'image_rel_path': f"images/{g}_{fid}.jpg",
        }
        index_items.append(item)
        
    gallery_dir.mkdir(parents=True, exist_ok=True)
    save_json(gallery_dir / 'gallery_index.json', index_items, overwrite=True)
    
    html_content = generate_gallery_html(index_items)
    (gallery_dir / 'index.html').write_text(html_content, encoding='utf-8')
    print(f"Gallery successfully rendered to: {gallery_dir / 'index.html'} ({len(index_items)} frames)", flush=True)

def generate_gallery_html(index_items: list[dict]) -> str:
    json_str = json.dumps(index_items, ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Unified Crack Tip Detection - 1,633 Frames Diagnostic Gallery</title>
<style>
  :root {{
    --bg-dark: #101217;
    --card-bg: #181c24;
    --panel-bg: #141720;
    --border: #283042;
    --text-main: #f0f3fa;
    --text-muted: #8b99ac;
    --accent: #3a86ff;
    --accent-hover: #2670e8;
    --success: #06d6a0;
    --warning: #ffd166;
    --danger: #ef476f;
    --cyan: #00b4d8;
    --pink: #ff006e;
    --purple: #8338ec;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg-dark);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.5;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }}
  header {{
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 8px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 10;
  }}
  h1 {{ font-size: 1.1rem; font-weight: 600; display: flex; align-items: center; gap: 8px; }}
  .tag {{ font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; background: var(--accent); color: white; font-weight: 500; }}
  .main-layout {{
    display: grid;
    grid-template-columns: 310px 1fr 370px;
    flex: 1;
    overflow: hidden;
  }}
  .panel {{
    background: var(--panel-bg);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    padding: 14px;
    gap: 12px;
  }}
  .panel.right {{ border-right: none; border-left: 1px solid var(--border); }}
  .filter-group {{ display: flex; flex-direction: column; gap: 4px; }}
  .filter-group label {{ font-size: 0.76rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }}
  select, input[type="text"], input[type="number"] {{
    width: 100%;
    background: #0d0f14;
    border: 1px solid var(--border);
    color: var(--text-main);
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 0.85rem;
    outline: none;
  }}
  select:focus, input:focus {{ border-color: var(--accent); }}
  .nav-buttons {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 6px; }}
  button {{
    background: #202634;
    border: 1px solid var(--border);
    color: var(--text-main);
    padding: 7px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    font-size: 0.82rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    transition: background 0.15s, border-color 0.15s;
  }}
  button:hover {{ background: #2b3346; border-color: var(--accent); }}
  button.btn-primary {{ background: var(--accent); border-color: var(--accent); color: white; }}
  button.btn-primary:hover {{ background: var(--accent-hover); }}
  
  /* Canvas Area */
  .canvas-area {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #090a0e;
    position: relative;
    overflow: hidden;
    user-select: none;
  }}
  .viewport-toolbar {{
    position: absolute;
    top: 12px;
    left: 12px;
    right: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(20, 23, 32, 0.9);
    padding: 6px 12px;
    border-radius: 8px;
    backdrop-filter: blur(10px);
    border: 1px solid var(--border);
    z-index: 20;
    gap: 12px;
    font-size: 0.8rem;
  }}
  .toolbar-group {{ display: flex; align-items: center; gap: 10px; }}
  .toolbar-group label {{ display: flex; align-items: center; gap: 5px; cursor: pointer; color: var(--text-main); font-size: 0.78rem; }}
  .toolbar-group input[type="range"] {{ width: 70px; accent-color: var(--accent); cursor: pointer; }}
  .btn-sm {{ padding: 4px 8px; font-size: 0.75rem; border-radius: 4px; }}
  
  #svgCanvas {{
    width: 100%;
    height: 100%;
    cursor: grab;
    display: block;
  }}
  #svgCanvas:active {{ cursor: grabbing; }}
  
  .canvas-footer {{
    position: absolute;
    bottom: 10px;
    left: 12px;
    background: rgba(16, 18, 24, 0.85);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    color: var(--text-muted);
    font-family: monospace;
    pointer-events: none;
    z-index: 10;
    border: 1px solid #1f2533;
  }}
  
  /* Badges & Tables */
  .stat-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.8rem;
  }}
  .badge-valid {{ background: rgba(6, 214, 160, 0.18); color: var(--success); border: 1px solid var(--success); }}
  .badge-uncertain {{ background: rgba(255, 209, 102, 0.18); color: var(--warning); border: 1px solid var(--warning); }}
  .badge-notrack {{ background: rgba(239, 71, 111, 0.18); color: var(--danger); border: 1px solid var(--danger); }}
  
  .info-table {{ width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 0.82rem; }}
  .info-table td {{ padding: 5px 4px; border-bottom: 1px solid #202636; }}
  .info-table td:first-child {{ color: var(--text-muted); width: 38%; }}
  .pill {{ font-size: 0.72rem; padding: 2px 6px; border-radius: 3px; margin: 2px; display: inline-block; background: #202636; border: 1px solid var(--border); }}
</style>
</head>
<body>

<header>
  <h1>Unified Crack Tip Detection (UCTIP-60Q-v1.0) <span class="tag">1,633 FRAMES DIAGNOSTIC GALLERY</span></h1>
  <div style="font-size:0.82rem; color:var(--text-muted);">DEV: GROUP_A (551) &bull; Three-point (520) | LOCKED: group_c (562)</div>
</header>

<div class="main-layout">
  <!-- Left Filter & Navigation Panel -->
  <div class="panel">
    <div class="filter-group">
      <label>Specimen Group</label>
      <select id="groupSelect" onchange="applyFilters()">
        <option value="ALL">All Specimens (1,633)</option>
        <option value="group_a">GROUP_A (551 DEV)</option>
        <option value="three_point_bend">Three-point-bend (520 DEV)</option>
        <option value="group_c">group_c (562 LOCKED)</option>
      </select>
    </div>

    <div class="filter-group">
      <label>Status Filter</label>
      <select id="statusSelect" onchange="applyFilters()">
        <option value="ALL">All Statuses</option>
        <option value="VALID">VALID Only</option>
        <option value="IDENTITY_UNCERTAIN">IDENTITY_UNCERTAIN</option>
        <option value="NO_VISIBLE_TRACK">NO_VISIBLE_TRACK</option>
      </select>
    </div>

    <div class="filter-group">
      <label>Ground Truth Filter</label>
      <select id="gtSelect" onchange="applyFilters()">
        <option value="ALL">All Frames</option>
        <option value="VISIBLE_GT">Visible GT Only (54 frames)</option>
        <option value="GT_FAIL">Visible GT Errors > 10px</option>
      </select>
    </div>

    <div class="filter-group">
      <label>Anomaly / Flags Filter</label>
      <select id="flagSelect" onchange="applyFilters()">
        <option value="ALL">All Frames</option>
        <option value="ANOMALY">Motion Anomaly Rechecked</option>
        <option value="BUDGET">Budget Exhausted</option>
      </select>
    </div>

    <div class="filter-group" style="margin-top:auto; padding-top:10px; border-top:1px solid var(--border);">
      <label>Jump to Index (<span id="matchCount">1633</span> matches)</label>
      <input type="number" id="frameIndexInput" min="1" max="1633" value="1" onchange="jumpToIndex(this.value - 1)">
      <div class="nav-buttons">
        <button onclick="prevFrame()">&#9664; Prev Frame</button>
        <button onclick="nextFrame()">Next Frame &#9654;</button>
      </div>
      <div style="font-size:0.75rem; color:var(--text-muted); margin-top:8px;">
        Keyboard: &larr; / &rarr; (Step), F (Focus Tip), R (Reset), T (Tip), G (GT)
      </div>
    </div>
  </div>

  <!-- Center Canvas Area -->
  <div class="canvas-area" id="canvasContainer">
    <!-- Viewport Toolbar -->
    <div class="viewport-toolbar">
      <div class="toolbar-group">
        <label><input type="checkbox" id="showImage" checked onchange="drawFrame()"> Image</label>
        <input type="range" id="imageOpacity" min="0" max="100" value="100" title="Image Opacity" oninput="updateImageOpacity()">
        <label><input type="checkbox" id="showTip" checked onchange="drawFrame()"><span style="color:var(--success);">&#9679;</span> Tip</label>
        <label><input type="checkbox" id="showUncertain" checked onchange="drawFrame()"><span style="color:var(--warning);">&#9675;</span> Uncertain</label>
        <label><input type="checkbox" id="showGT" checked onchange="drawFrame()"><span style="color:var(--danger);">&#9632;</span> GT</label>
        <label><input type="checkbox" id="showRoi" checked onchange="drawFrame()"><span style="color:var(--accent);">&#9645;</span> ROI</label>
        <label><input type="checkbox" id="showAnchors" checked onchange="drawFrame()"><span style="color:var(--cyan);">&#9671;</span> Anchors</label>
      </div>

      <div class="toolbar-group">
        <button class="btn-sm" onclick="focusTip()" title="Focus on Tip or GT (F)">Focus Tip (F)</button>
        <button class="btn-sm" onclick="focusRoi()" title="Focus on Working ROI">Focus ROI</button>
        <button class="btn-sm" onclick="resetView()" title="Fit Full Frame (R)">Reset (R)</button>
        <label title="Keep current zoom & pan when navigating frames"><input type="checkbox" id="keepZoom" checked> Lock Zoom</label>
      </div>
    </div>

    <svg id="svgCanvas" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet"></svg>

    <div class="canvas-footer" id="coordsDisplay">X: 0 | Y: 0 | Zoom: 100%</div>
  </div>

  <!-- Right Diagnostics & Metric Panel -->
  <div class="panel right">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h3 id="diagTitle" style="font-size:1.0rem;">Frame 1</h3>
      <span id="diagStatus" class="stat-badge badge-valid">VALID</span>
    </div>

    <table class="info-table">
      <tr><td>Specimen</td><td id="infoGroup">GROUP_A</td></tr>
      <tr><td>Frame / Tracking</td><td id="infoFid">1 / #0</td></tr>
      <tr><td>Official Tip (x, y)</td><td id="infoTip" style="font-weight:600; color:var(--success);">-</td></tr>
      <tr><td>Selected Track</td><td id="infoTrack">-</td></tr>
      <tr><td>Ground Truth</td><td id="infoGt">-</td></tr>
      <tr><td>Error (px)</td><td id="infoError">-</td></tr>
      <tr><td>Hit@10 Status</td><td id="infoHit">-</td></tr>
      <tr><td>Oracle Min Error</td><td id="infoOracle">-</td></tr>
      <tr><td>Notch Root (x, y)</td><td id="infoNotch">-</td></tr>
      <tr><td>Working ROI</td><td id="infoRoi" style="font-family:monospace; font-size:0.75rem;">-</td></tr>
      <tr><td>P1 / P2 Anchors</td><td id="infoAnchors" style="font-family:monospace; font-size:0.75rem;">-</td></tr>
      <tr><td>Fixed Channel</td><td id="infoFixed">-</td></tr>
      <tr><td>Prev Channel</td><td id="infoPrev">-</td></tr>
      <tr><td>Latency / Budget</td><td id="infoBudget">-</td></tr>
      <tr><td>Failure Stage</td><td id="infoStage">-</td></tr>
      <tr><td>Failure Reason</td><td id="infoReason">-</td></tr>
    </table>

    <div style="margin-top:6px;">
      <label style="font-size:0.75rem; color:var(--text-muted); font-weight:600; text-transform:uppercase;">Flags &amp; Recheck Lineage</label>
      <div id="infoFlags" style="margin-top:4px;"></div>
    </div>
  </div>
</div>

<script>
  const framesData = {json_str};
  let filteredIndices = [];
  let currentPointer = 0;

  // Viewport transformation state
  let viewBox = {{ x: 0, y: 0, w: 1856, h: 2072 }};
  let isPanning = false;
  let panStart = {{ x: 0, y: 0 }};
  let activeGroup = '';

  function init() {{
    setupInteractions();
    applyFilters();
  }}

  function getCurrentFrame() {{
    if (filteredIndices.length === 0) return null;
    return framesData[filteredIndices[currentPointer]];
  }}

  function applyFilters() {{
    const group = document.getElementById('groupSelect').value;
    const status = document.getElementById('statusSelect').value;
    const gt = document.getElementById('gtSelect').value;
    const flag = document.getElementById('flagSelect').value;

    filteredIndices = [];
    for (let i = 0; i < framesData.length; i++) {{
      const d = framesData[i];
      if (group !== 'ALL' && d.group !== group) continue;
      if (status !== 'ALL' && d.status !== status) continue;
      if (gt === 'VISIBLE_GT' && !d.has_gt) continue;
      if (gt === 'GT_FAIL' && (!d.has_gt || d.error_px === null || d.error_px <= 10.0)) continue;
      if (flag === 'ANOMALY' && !d.flags.some(f => f.includes('ANOMALY'))) continue;
      if (flag === 'BUDGET' && !d.budget_exhausted) continue;
      filteredIndices.push(i);
    }}

    document.getElementById('matchCount').innerText = filteredIndices.length;
    currentPointer = 0;
    renderCurrent(true);
  }}

  function jumpToIndex(idx) {{
    const p = Math.max(0, Math.min(filteredIndices.length - 1, idx));
    currentPointer = p;
    renderCurrent(false);
  }}

  function prevFrame() {{
    if (currentPointer > 0) {{
      currentPointer--;
      renderCurrent(false);
    }}
  }}

  function nextFrame() {{
    if (currentPointer < filteredIndices.length - 1) {{
      currentPointer++;
      renderCurrent(false);
    }}
  }}

  function renderCurrent(forceResetView = false) {{
    const d = getCurrentFrame();
    if (!d) return;

    document.getElementById('frameIndexInput').value = currentPointer + 1;
    document.getElementById('diagTitle').innerText = `${{d.group.toUpperCase()}} - Frame ${{d.frame_id}}`;
    
    // Status Badge
    const stEl = document.getElementById('diagStatus');
    stEl.innerText = d.status;
    stEl.className = 'stat-badge ' + (d.status === 'VALID' ? 'badge-valid' : (d.status.includes('UNCERTAIN') ? 'badge-uncertain' : 'badge-notrack'));

    // Details Table
    document.getElementById('infoGroup').innerText = `${{d.group}} (${{d.role}})`;
    document.getElementById('infoFid').innerText = `${{d.frame_id}} (tracking #${{d.tracking_num}})`;
    document.getElementById('infoTip').innerText = (d.tip_x !== null && d.tip_y !== null) ? `(${{d.tip_x.toFixed(1)}}, ${{d.tip_y.toFixed(1)}})` : 'null';
    document.getElementById('infoTrack').innerText = d.selected_track_id || '-';
    document.getElementById('infoGt').innerText = (d.gt_x !== null && d.gt_y !== null) ? `(${{d.gt_x.toFixed(1)}}, ${{d.gt_y.toFixed(1)}})` : 'N/A';
    
    const errEl = document.getElementById('infoError');
    if (d.error_px !== null) {{
      errEl.innerText = `${{d.error_px.toFixed(2)}} px`;
      errEl.style.color = d.error_px <= 10.0 ? 'var(--success)' : (d.error_px > 100.0 ? 'var(--danger)' : 'var(--warning)');
    }} else {{
      errEl.innerText = '-';
      errEl.style.color = 'inherit';
    }}

    document.getElementById('infoHit').innerText = d.has_gt ? (d.hit10 ? 'HIT@10 PASS (<=10px)' : 'FAIL (>10px)') : 'NO_GT';
    document.getElementById('infoOracle').innerText = d.oracle_min_error_px !== null ? `${{d.oracle_min_error_px.toFixed(2)}} px` : '-';
    document.getElementById('infoNotch').innerText = d.notch_root ? `(${{d.notch_root[0].toFixed(1)}}, ${{d.notch_root[1].toFixed(1)}})` : '-';
    document.getElementById('infoRoi').innerText = d.roi ? `[${{d.roi[0]}}, ${{d.roi[1]}}, ${{d.roi[2]}}, ${{d.roi[3]}}]` : '-';
    
    if (d.p1 && d.p2) {{
      document.getElementById('infoAnchors').innerText = `P1:(${{d.p1[0].toFixed(0)}},${{d.p1[1].toFixed(0)}}) P2:(${{d.p2[0].toFixed(0)}},${{d.p2[1].toFixed(0)}})`;
    }} else {{
      document.getElementById('infoAnchors').innerText = '-';
    }}
    
    document.getElementById('infoFixed').innerText = d.fixed_ref_channel;
    document.getElementById('infoPrev').innerText = d.prev_ref_channel;
    document.getElementById('infoBudget').innerText = d.time_ms !== null ? `${{d.time_ms}} ms ${{d.budget_exhausted ? '[EXHAUSTED]' : ''}}` : '-';
    document.getElementById('infoStage').innerText = d.failure_stage || 'NONE';
    document.getElementById('infoReason').innerText = d.failure_reason || '-';

    // Flags
    const flContainer = document.getElementById('infoFlags');
    flContainer.innerHTML = '';
    if (d.flags && d.flags.length > 0) {{
      d.flags.forEach(f => {{
        const span = document.createElement('span');
        span.className = 'pill';
        span.innerText = f;
        flContainer.appendChild(span);
      }});
    }} else {{
      flContainer.innerHTML = '<span style="color:var(--text-muted); font-size:0.78rem;">No anomaly flags</span>';
    }}

    const lockZoom = document.getElementById('keepZoom').checked;
    if (forceResetView || !lockZoom || activeGroup !== d.group) {{
      resetView();
      activeGroup = d.group;
    }} else {{
      applyViewBox();
    }}

    drawFrame();
  }}

  function updateSvgViewBox() {{
    const svg = document.getElementById('svgCanvas');
    svg.setAttribute('viewBox', `${{viewBox.x}} ${{viewBox.y}} ${{viewBox.w}} ${{viewBox.h}}`);
    updateFooter();
  }}

  function applyViewBox() {{
    updateSvgViewBox();
  }}

  function resetView() {{
    const d = getCurrentFrame();
    if (!d) return;
    viewBox = {{ x: 0, y: 0, w: d.width, h: d.height }};
    updateSvgViewBox();
  }}

  function focusTip() {{
    const d = getCurrentFrame();
    if (!d) return;
    let cx = d.tip_x, cy = d.tip_y;
    if (cx === null || cy === null) {{
      if (d.gt_x !== null && d.gt_y !== null) {{
        cx = d.gt_x; cy = d.gt_y;
      }} else if (d.roi) {{
        cx = (d.roi[0] + d.roi[2]) / 2;
        cy = (d.roi[1] + d.roi[3]) / 2;
      }} else {{
        return;
      }}
    }}
    const span = Math.min(d.width, d.height) * 0.28;
    viewBox = {{
      x: cx - span / 2,
      y: cy - span / 2,
      w: span,
      h: span
    }};
    updateSvgViewBox();
  }}

  function focusRoi() {{
    const d = getCurrentFrame();
    if (!d || !d.roi) return;
    const [x1, y1, x2, y2] = d.roi;
    const rw = x2 - x1;
    const rh = y2 - y1;
    const pad = Math.max(rw, rh) * 0.2;
    viewBox = {{
      x: x1 - pad,
      y: y1 - pad,
      w: rw + pad * 2,
      h: rh + pad * 2
    }};
    updateSvgViewBox();
  }}

  function updateImageOpacity() {{
    const op = document.getElementById('imageOpacity').value / 100.0;
    const imgEl = document.getElementById('rawImgNode');
    if (imgEl) imgEl.style.opacity = op;
  }}

  function drawFrame() {{
    const d = getCurrentFrame();
    if (!d) return;
    const svg = document.getElementById('svgCanvas');
    svg.innerHTML = '';

    // 1. Image or Background rect
    if (document.getElementById('showImage').checked) {{
      const imgEl = document.createElementNS('http://www.w3.org/2000/svg', 'image');
      imgEl.setAttribute('id', 'rawImgNode');
      imgEl.setAttribute('href', d.image_rel_path);
      imgEl.setAttribute('x', '0');
      imgEl.setAttribute('y', '0');
      imgEl.setAttribute('width', d.width);
      imgEl.setAttribute('height', d.height);
      imgEl.setAttribute('preserveAspectRatio', 'none');
      imgEl.style.opacity = document.getElementById('imageOpacity').value / 100.0;
      svg.appendChild(imgEl);
    }} else {{
      const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      bg.setAttribute('width', d.width);
      bg.setAttribute('height', d.height);
      bg.setAttribute('fill', '#101217');
      svg.appendChild(bg);
    }}

    // 2. Working ROI box
    if (document.getElementById('showRoi').checked && d.roi) {{
      const [rx1, ry1, rx2, ry2] = d.roi;
      const roiRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      roiRect.setAttribute('x', rx1);
      roiRect.setAttribute('y', ry1);
      roiRect.setAttribute('width', rx2 - rx1);
      roiRect.setAttribute('height', ry2 - ry1);
      roiRect.setAttribute('fill', 'rgba(58, 134, 255, 0.08)');
      roiRect.setAttribute('stroke', '#3a86ff');
      roiRect.setAttribute('stroke-width', 2);
      roiRect.setAttribute('stroke-dasharray', '6,6');
      svg.appendChild(roiRect);
      
      const roiText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      roiText.setAttribute('x', rx1 + 10);
      roiText.setAttribute('y', ry1 + 24);
      roiText.setAttribute('fill', '#3a86ff');
      roiText.setAttribute('font-size', '16');
      roiText.setAttribute('font-weight', '600');
      roiText.textContent = `ROI [${{rx1}},${{ry1}},${{rx2}},${{ry2}}]`;
      svg.appendChild(roiText);
    }}

    // 3. Anchors & Notch Root
    if (document.getElementById('showAnchors').checked) {{
      if (d.p1 && d.p2) {{
        const [p1x, p1y] = d.p1;
        const [p2x, p2y] = d.p2;
        const baseLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        baseLine.setAttribute('x1', p1x); baseLine.setAttribute('y1', p1y);
        baseLine.setAttribute('x2', p2x); baseLine.setAttribute('y2', p2y);
        baseLine.setAttribute('stroke', '#00b4d8'); baseLine.setAttribute('stroke-width', 2);
        baseLine.setAttribute('stroke-dasharray', '5,5');
        svg.appendChild(baseLine);

        [d.p1, d.p2].forEach(([ax, ay], i) => {{
          const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          c.setAttribute('cx', ax); c.setAttribute('cy', ay); c.setAttribute('r', 8);
          c.setAttribute('fill', '#00b4d8');
          c.setAttribute('stroke', '#ffffff');
          c.setAttribute('stroke-width', 2);
          svg.appendChild(c);
        }});
      }}
      if (d.notch_root) {{
        const [nrx, nry] = d.notch_root;
        const nr = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        nr.setAttribute('cx', nrx); nr.setAttribute('cy', nry); nr.setAttribute('r', 9);
        nr.setAttribute('fill', '#ff006e');
        nr.setAttribute('stroke', '#ffffff');
        nr.setAttribute('stroke-width', 2);
        svg.appendChild(nr);

        const nrText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        nrText.setAttribute('x', nrx + 12); nrText.setAttribute('y', nry - 10);
        nrText.setAttribute('fill', '#ff006e');
        nrText.setAttribute('font-size', '15');
        nrText.setAttribute('font-weight', 'bold');
        nrText.textContent = `Notch Root`;
        svg.appendChild(nrText);
      }}
    }}

    // 4. Ground Truth Marker
    if (document.getElementById('showGT').checked && d.gt_x !== null && d.gt_y !== null) {{
      const gtRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      gtRect.setAttribute('x', d.gt_x - 12);
      gtRect.setAttribute('y', d.gt_y - 12);
      gtRect.setAttribute('width', 24);
      gtRect.setAttribute('height', 24);
      gtRect.setAttribute('fill', 'rgba(239, 71, 111, 0.25)');
      gtRect.setAttribute('stroke', '#ef476f');
      gtRect.setAttribute('stroke-width', 2.5);
      svg.appendChild(gtRect);

      const gtDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      gtDot.setAttribute('cx', d.gt_x); gtDot.setAttribute('cy', d.gt_y); gtDot.setAttribute('r', 3);
      gtDot.setAttribute('fill', '#ef476f');
      svg.appendChild(gtDot);

      const gtText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      gtText.setAttribute('x', d.gt_x + 16);
      gtText.setAttribute('y', d.gt_y - 8);
      gtText.setAttribute('fill', '#ef476f');
      gtText.setAttribute('font-size', '16');
      gtText.setAttribute('font-weight', 'bold');
      gtText.textContent = `GT (${{d.gt_x.toFixed(1)}}, ${{d.gt_y.toFixed(1)}})`;
      svg.appendChild(gtText);
    }}

    // 5. Uncertain Tip Marker
    if (document.getElementById('showUncertain').checked && d.preferred_uncertain_tip_x !== null) {{
      const ux = d.preferred_uncertain_tip_x;
      const uy = d.preferred_uncertain_tip_y;
      const uCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      uCircle.setAttribute('cx', ux); uCircle.setAttribute('cy', uy); uCircle.setAttribute('r', 12);
      uCircle.setAttribute('fill', 'rgba(255, 209, 102, 0.35)');
      uCircle.setAttribute('stroke', '#ffd166');
      uCircle.setAttribute('stroke-width', 2);
      uCircle.setAttribute('stroke-dasharray', '5,5');
      svg.appendChild(uCircle);
    }}

    // 6. Rightmost Verified Tip
    if (document.getElementById('showTip').checked && d.tip_x !== null && d.tip_y !== null) {{
      const tx = d.tip_x, ty = d.tip_y;

      // Error connection line to GT if present
      if (document.getElementById('showGT').checked && d.gt_x !== null && d.gt_y !== null) {{
        const errLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        errLine.setAttribute('x1', tx); errLine.setAttribute('y1', ty);
        errLine.setAttribute('x2', d.gt_x); errLine.setAttribute('y2', d.gt_y);
        errLine.setAttribute('stroke', '#ef476f');
        errLine.setAttribute('stroke-width', 2);
        errLine.setAttribute('stroke-dasharray', '4,4');
        svg.appendChild(errLine);
      }}

      const tipCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      tipCircle.setAttribute('cx', tx); tipCircle.setAttribute('cy', ty); tipCircle.setAttribute('r', 12);
      tipCircle.setAttribute('fill', 'rgba(6, 214, 160, 0.35)');
      tipCircle.setAttribute('stroke', '#06d6a0');
      tipCircle.setAttribute('stroke-width', 3);
      svg.appendChild(tipCircle);

      const cross1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      cross1.setAttribute('x1', tx - 22); cross1.setAttribute('y1', ty);
      cross1.setAttribute('x2', tx + 22); cross1.setAttribute('y2', ty);
      cross1.setAttribute('stroke', '#06d6a0'); cross1.setAttribute('stroke-width', 2.5);
      svg.appendChild(cross1);

      const cross2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      cross2.setAttribute('x1', tx); cross2.setAttribute('y1', ty - 22);
      cross2.setAttribute('x2', tx); cross2.setAttribute('y2', ty + 22);
      cross2.setAttribute('stroke', '#06d6a0'); cross2.setAttribute('stroke-width', 2.5);
      svg.appendChild(cross2);

      const tipText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      tipText.setAttribute('x', tx + 16);
      tipText.setAttribute('y', ty + 24);
      tipText.setAttribute('fill', '#06d6a0');
      tipText.setAttribute('font-size', '16');
      tipText.setAttribute('font-weight', 'bold');
      tipText.textContent = `TIP (${{tx.toFixed(1)}}, ${{ty.toFixed(1)}})`;
      svg.appendChild(tipText);
    }}
  }}

  function setupInteractions() {{
    const svg = document.getElementById('svgCanvas');

    // Pan with mouse drag
    svg.addEventListener('mousedown', (e) => {{
      if (e.button !== 0) return;
      isPanning = true;
      panStart = {{ x: e.clientX, y: e.clientY }};
    }});

    window.addEventListener('mousemove', (e) => {{
      const d = getCurrentFrame();
      if (!d) return;
      const rect = svg.getBoundingClientRect();
      const svgX = viewBox.x + ((e.clientX - rect.left) / rect.width) * viewBox.w;
      const svgY = viewBox.y + ((e.clientY - rect.top) / rect.height) * viewBox.h;

      if (isPanning) {{
        const dx = ((e.clientX - panStart.x) / rect.width) * viewBox.w;
        const dy = ((e.clientY - panStart.y) / rect.height) * viewBox.h;
        viewBox.x -= dx;
        viewBox.y -= dy;
        panStart = {{ x: e.clientX, y: e.clientY }};
        updateSvgViewBox();
      }}

      // Update footer coords
      const zoomPct = Math.round((d.width / viewBox.w) * 100);
      document.getElementById('coordsDisplay').innerText = `X: ${{Math.round(svgX)}} | Y: ${{Math.round(svgY)}} | Zoom: ${{zoomPct}}%`;
    }});

    window.addEventListener('mouseup', () => {{
      isPanning = false;
    }});

    // Zoom with mouse wheel
    svg.addEventListener('wheel', (e) => {{
      e.preventDefault();
      const d = getCurrentFrame();
      if (!d) return;

      const rect = svg.getBoundingClientRect();
      const mouseSvgX = viewBox.x + ((e.clientX - rect.left) / rect.width) * viewBox.w;
      const mouseSvgY = viewBox.y + ((e.clientY - rect.top) / rect.height) * viewBox.h;

      const factor = e.deltaY < 0 ? 0.8 : 1.25;
      const newW = viewBox.w * factor;
      const newH = viewBox.h * factor;

      if (newW < 60 || newW > d.width * 3.5) return;

      viewBox.x = mouseSvgX - ((e.clientX - rect.left) / rect.width) * newW;
      viewBox.y = mouseSvgY - ((e.clientY - rect.top) / rect.height) * newH;
      viewBox.w = newW;
      viewBox.h = newH;
      updateSvgViewBox();
    }}, {{ passive: false }});

    // Keyboard shortcuts
    window.addEventListener('keydown', (e) => {{
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
      if (e.key === 'ArrowLeft') prevFrame();
      if (e.key === 'ArrowRight') nextFrame();
      if (e.key === 'f' || e.key === 'F') focusTip();
      if (e.key === 'r' || e.key === 'R') resetView();
      if (e.key === 't' || e.key === 'T') {{
        const chk = document.getElementById('showTip');
        chk.checked = !chk.checked;
        drawFrame();
      }}
      if (e.key === 'g' || e.key === 'G') {{
        const chk = document.getElementById('showGT');
        chk.checked = !chk.checked;
        drawFrame();
      }}
    }});
  }}

  function updateFooter() {{
    const d = getCurrentFrame();
    if (!d) return;
    const zoomPct = Math.round((d.width / viewBox.w) * 100);
    const curText = document.getElementById('coordsDisplay').innerText.split('|');
    const xPart = curText[0] || 'X: 0';
    const yPart = curText[1] || 'Y: 0';
    document.getElementById('coordsDisplay').innerText = `${{xPart.trim()}} | ${{yPart.trim()}} | Zoom: ${{zoomPct}}%`;
  }}

  window.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>"""

def main():
    parser = argparse.ArgumentParser(description="Render interactive HTML diagnostic gallery with images")
    parser.add_argument('--run', required=True, help="Run output directory")
    parser.add_argument('--skip-images', action='store_true', help="Skip exporting images if already present")
    args = parser.parse_args()
    
    run_dir = Path(args.run)
    if not run_dir.is_absolute():
        run_dir = PROJECT_ROOT / run_dir
    build_gallery(run_dir, skip_images=args.skip_images)

if __name__ == '__main__':
    main()
