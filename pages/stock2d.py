import streamlit as st
import streamlit.components.v1 as components

st.title("📦 Stock 2D Layout")
st.caption("จัดวางสินค้าบนชั้นวาง 2D — เพิ่มช่อง, ลากวางช่อง, ปรับขนาด, คลิกเพื่อดูและแก้ไขสินค้า")

st.divider()

CANVAS_HTML = r"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
/* ── Reset ── */
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#0f172a;color:#e2e8f0;padding:12px;user-select:none}

/* ── Toolbar ── */
#toolbar{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.tb-btn{padding:8px 18px;border:none;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600;transition:.15s}
#btn-add{background:linear-gradient(135deg,#f97316,#fb923c);color:#fff}
#btn-add:hover{filter:brightness(1.15);transform:translateY(-1px)}
#btn-clear{background:#1e293b;color:#94a3b8;border:1px solid #334155}
#btn-clear:hover{border-color:#f97316;color:#f97316}
#search-wrap{
  display:flex;align-items:center;gap:6px;
  background:#1e293b;border:1px solid #334155;
  border-radius:10px;padding:4px 10px;flex:1;max-width:360px;transition:.2s;
}
#search-wrap:focus-within{border-color:#f97316;box-shadow:0 0 0 2px rgba(249,115,22,.2)}
#search-inp{background:none;border:none;outline:none;color:#e2e8f0;font-size:13px;flex:1;padding:3px 0;font-family:inherit}
#search-inp::placeholder{color:#475569}
#btn-search-go{background:linear-gradient(135deg,#f97316,#fb923c);border:none;color:#fff;border-radius:7px;padding:5px 12px;font-size:12px;font-weight:600;cursor:pointer}
#btn-search-clear{background:none;border:none;color:#64748b;font-size:15px;cursor:pointer;padding:2px 4px;border-radius:4px;display:none}
#btn-search-clear:hover{color:#f87171}
#search-result-label{font-size:11px;white-space:nowrap}
.tb-label{font-size:12px;color:#64748b;margin-left:auto}

/* ── Canvas ── */
#canvas-wrap{
  position:relative;width:100%;height:520px;
  background:
    linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px),
    #0f172a;
  background-size:40px 40px;
  border:2px solid #1e293b;border-radius:14px;overflow:hidden;
}

/* ── Square tiles ── */
.sq{
  position:absolute;border-radius:10px;
  border:2px solid rgba(255,255,255,.22);
  cursor:grab;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  color:rgba(255,255,255,.95);
  box-shadow:0 4px 20px rgba(0,0,0,.5);
  transition:box-shadow .15s,border-color .15s,opacity .25s,filter .25s;
  min-width:90px;min-height:80px;
}
.sq:hover{box-shadow:0 6px 28px rgba(0,0,0,.7);border-color:rgba(255,255,255,.5)}
.sq.dragging{border-color:#f97316!important;box-shadow:0 0 0 3px rgba(249,115,22,.35)!important;cursor:grabbing}
.sq.dimmed{opacity:.2!important;filter:grayscale(1) brightness(.4)!important;pointer-events:none}
.sq.match{border-color:#f97316!important;animation:match-pulse 1.8s ease-in-out infinite}
@keyframes match-pulse{
  0%,100%{box-shadow:0 0 0 3px rgba(249,115,22,.5),0 8px 28px rgba(0,0,0,.5)}
  50%{box-shadow:0 0 0 7px rgba(249,115,22,.12),0 8px 28px rgba(0,0,0,.5)}
}
.sq-label{pointer-events:none;text-align:center;padding:2px 6px;white-space:pre-line;font-size:12px;font-weight:700;line-height:1.4}
.sq .delete-btn{
  position:absolute;top:4px;right:5px;
  background:rgba(220,38,38,.85);border:none;color:#fff;
  font-size:10px;border-radius:50%;width:18px;height:18px;line-height:18px;
  text-align:center;cursor:pointer;display:none;z-index:2;
}
.sq:hover .delete-btn{display:block}
.sq .edit-btn{
  position:absolute;top:4px;left:5px;
  background:rgba(30,41,59,.85);border:1px solid #334155;color:#94a3b8;
  font-size:9px;border-radius:4px;padding:2px 5px;
  cursor:pointer;display:none;z-index:2;white-space:nowrap;
}
.sq:hover .edit-btn{display:block}
.resize-handle{
  position:absolute;bottom:3px;right:3px;
  width:13px;height:13px;
  border-right:3px solid rgba(255,255,255,.55);
  border-bottom:3px solid rgba(255,255,255,.55);
  border-radius:0 0 4px 0;cursor:se-resize;
}
.sq-badge{position:absolute;bottom:6px;left:50%;transform:translateX(-50%);display:flex;gap:3px}
.sq-dot{width:7px;height:7px;border-radius:50%}
@keyframes collision-flash{
  0%{box-shadow:0 0 0 0 rgba(220,38,38,.9)}
  50%{box-shadow:0 0 0 12px rgba(220,38,38,0)}
  100%{box-shadow:0 0 0 0 rgba(220,38,38,0)}
}
.collision{animation:collision-flash .4s ease-out}

/* ── Shared overlay ── */
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);backdrop-filter:blur(5px);z-index:1000;align-items:center;justify-content:center}
.overlay.show{display:flex}

/* ── Create / Settings Modal ── */
#create-modal{
  background:#1e293b;border:1px solid #334155;
  border-radius:20px;width:min(560px,96vw);
  box-shadow:0 24px 64px rgba(0,0,0,.75);overflow:hidden;
}
.cm-header{padding:20px 24px 0}
.cm-header h3{font-size:15px;font-weight:700;color:#f97316;margin-bottom:4px}
.cm-header .sub{font-size:11px;color:#64748b;margin-bottom:14px}
.tab-bar{display:flex;border-bottom:1px solid #334155}
.tab-btn{padding:10px 18px;font-size:12px;font-weight:600;cursor:pointer;border:none;background:none;color:#64748b;border-bottom:2px solid transparent;transition:.15s;margin-bottom:-1px}
.tab-btn.active{color:#f97316;border-bottom-color:#f97316}
.tab-pane{display:none;padding:18px 24px}
.tab-pane.active{display:block}
.field-group{margin-bottom:14px}
.field-group label{font-size:11px;color:#94a3b8;display:block;margin-bottom:5px}
.field-group input[type=text],.field-group input[type=number]{
  width:100%;padding:8px 10px;
  background:#0f172a;border:1px solid #334155;
  border-radius:8px;color:#e2e8f0;font-size:13px;outline:none;transition:.15s;
}
.field-group input:focus{border-color:#f97316}
.color-swatch-row{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}
.cswatch{width:28px;height:28px;border-radius:6px;cursor:pointer;border:2px solid transparent;transition:.12s;flex-shrink:0}
.cswatch:hover{transform:scale(1.15)}
.cswatch.active{border-color:#fff;box-shadow:0 0 0 2px #f97316}
.preset-row{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}
.preset-btn{padding:5px 13px;border-radius:6px;font-size:12px;font-weight:600;background:#0f172a;border:1px solid #334155;color:#94a3b8;cursor:pointer;transition:.15s}
.preset-btn:hover,.preset-btn.active{background:#f97316;border-color:#f97316;color:#fff}
.grid-controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.ctrl-group{flex:1;min-width:90px}
.ctrl-group label{font-size:11px;color:#94a3b8;display:block;margin-bottom:5px}
.ctrl-group input[type=number]{width:100%;padding:7px 10px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:#e2e8f0;font-size:13px;outline:none;transition:.15s}
.ctrl-group input:focus{border-color:#f97316}
#grid-preview{width:100%;overflow:auto;max-height:180px;border:1px solid #0f172a;border-radius:10px;padding:10px;background:#0f172a}
.gp-grid{display:inline-grid;gap:var(--gap,6px)}
.gp-cell{width:40px;height:40px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff;font-weight:700}
.modal-actions{display:flex;gap:10px;justify-content:flex-end;padding:14px 24px;border-top:1px solid #334155}
.modal-btn{padding:8px 20px;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;transition:.15s}
.modal-btn-primary{background:linear-gradient(135deg,#f97316,#fb923c);color:#fff}
.modal-btn-primary:hover{filter:brightness(1.1)}
.modal-btn-secondary{background:#0f172a;color:#64748b;border:1px solid #334155}
.modal-btn-secondary:hover{border-color:#f97316;color:#f97316}

/* ── Item Grid Modal ── */
#item-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);backdrop-filter:blur(6px);z-index:1100;align-items:center;justify-content:center}
#item-overlay.show{display:flex}
#item-modal{background:#1e293b;border:1px solid #334155;border-radius:20px;width:min(760px,96vw);max-height:88vh;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 28px 80px rgba(0,0,0,.8)}
#item-modal-header{padding:16px 22px 12px;border-bottom:1px solid #334155;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
#item-modal-header h3{font-size:15px;font-weight:700;color:#f97316}
.close-btn{background:none;border:none;color:#64748b;font-size:18px;cursor:pointer;padding:2px 6px;border-radius:4px;transition:.15s}
.close-btn:hover{color:#f97316;background:#0f172a}
#item-modal-body{flex:1;overflow:auto;padding:18px 22px}
#item-grid-el{display:grid;gap:10px}
.item-cell{
  border-radius:12px;padding:10px 8px;cursor:pointer;
  transition:.18s ease;border:2px solid transparent;
  display:flex;flex-direction:column;align-items:center;
  position:relative;background:rgba(15,23,42,.6);
}
.item-cell:hover{transform:translateY(-3px);border-color:rgba(249,115,22,.5);box-shadow:0 10px 26px rgba(0,0,0,.55)}
.item-cell.cell-green{background:rgba(16,185,129,.14);border-color:rgba(16,185,129,.25)}
.item-cell.cell-orange{background:rgba(249,115,22,.14);border-color:rgba(249,115,22,.25)}
.item-cell.cell-red{background:rgba(239,68,68,.14);border-color:rgba(239,68,68,.25)}
.item-cell.cell-empty{background:rgba(30,41,59,.45);border-color:rgba(51,65,85,.3)}
.cell-edit-badge{
  position:absolute;top:5px;right:5px;
  background:rgba(15,23,42,.92);border:1px solid #334155;
  color:#94a3b8;font-size:9px;border-radius:4px;
  padding:1px 5px;opacity:0;transition:.15s;z-index:3;
}
.item-cell:hover .cell-edit-badge{opacity:1;color:#f97316;border-color:#f97316}
.cell-indicator{position:absolute;top:0;left:0;right:0;height:3px;border-radius:10px 10px 0 0}
.ind-green{background:#10b981}.ind-orange{background:#f97316}.ind-red{background:#ef4444}.ind-empty{background:#334155}

/* Real Product Image in Grid */
.cell-img{
  width:54px;height:54px;border-radius:10px;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
  margin-bottom:6px;background:rgba(0,0,0,.35);
  border:1px solid rgba(255,255,255,.08);position:relative;flex-shrink:0;
}
.cell-img img{
  width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .2s ease;
}
.item-cell:hover .cell-img img{transform:scale(1.1)}
.cell-img-empty{
  width:100%;height:100%;display:flex;align-items:center;justify-content:center;
  color:#475569;font-size:22px;
}

.cell-name{font-size:10px;font-weight:600;color:#e2e8f0;text-align:center;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%}
.cell-barcode{font-size:9px;color:#64748b;margin-bottom:4px;font-family:monospace}
.cell-stock-badge{font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;margin-top:auto}
.badge-green{background:rgba(16,185,129,.25);color:#34d399}
.badge-orange{background:rgba(249,115,22,.25);color:#fb923c}
.badge-red{background:rgba(239,68,68,.25);color:#f87171}
.badge-empty{background:rgba(51,65,85,.35);color:#64748b}

/* ── Item Edit Modal ── */
#edit-item-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);backdrop-filter:blur(4px);z-index:1200;align-items:center;justify-content:center}
#edit-item-overlay.show{display:flex}
#edit-item-modal{
  background:#1e293b;border:1px solid #334155;
  border-radius:18px;width:min(460px,96vw);
  box-shadow:0 24px 68px rgba(0,0,0,.8);overflow:hidden;
}
#edit-item-modal h4{font-size:14px;font-weight:700;color:#f97316;padding:16px 20px 10px;border-bottom:1px solid #334155}
.ei-body{padding:16px 20px;max-height:75vh;overflow-y:auto}
.ei-row{display:flex;gap:10px;margin-bottom:12px}
.ei-group{flex:1}
.ei-group label{font-size:11px;color:#94a3b8;display:block;margin-bottom:4px}
.ei-group input[type=text],.ei-group input[type=number]{
  width:100%;padding:7px 9px;
  background:#0f172a;border:1px solid #334155;
  border-radius:7px;color:#e2e8f0;font-size:12px;outline:none;transition:.15s;
}
.ei-group input:focus{border-color:#f97316}

/* Real Image Preset Picker */
.img-preset-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(48px,1fr));gap:6px;
  max-height:130px;overflow-y:auto;padding:6px;
  background:#0f172a;border:1px solid #334155;border-radius:8px;margin-bottom:8px;
}
.img-preset-btn{
  width:100%;aspect-ratio:1;border-radius:6px;border:2px solid #334155;
  background:#1e293b;cursor:pointer;overflow:hidden;padding:0;
  transition:.15s;position:relative;
}
.img-preset-btn img{width:100%;height:100%;object-fit:cover;display:block}
.img-preset-btn:hover{border-color:#f97316;transform:scale(1.06)}
.img-preset-btn.active{border-color:#f97316;box-shadow:0 0 0 2px rgba(249,115,22,.5)}

.empty-toggle{display:flex;align-items:center;gap:8px;margin-bottom:12px;font-size:12px;color:#94a3b8;cursor:pointer}
.empty-toggle input{accent-color:#f97316;width:15px;height:15px;cursor:pointer}
.ei-actions{display:flex;gap:8px;justify-content:flex-end;padding:12px 20px;border-top:1px solid #334155}

/* ── Hover tooltip ── */
#cell-tooltip{
  display:none;position:fixed;z-index:1300;pointer-events:none;
  background:rgba(10,15,30,.97);border:1px solid #f97316;
  border-radius:12px;padding:12px 14px;min-width:210px;
  box-shadow:0 12px 40px rgba(0,0,0,.7);backdrop-filter:blur(8px);
}
.tt-header{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.tt-img-box{
  width:48px;height:48px;border-radius:8px;overflow:hidden;
  background:#1e293b;flex-shrink:0;border:1px solid rgba(255,255,255,.1);
  display:flex;align-items:center;justify-content:center;
}
.tt-img-box img{width:100%;height:100%;object-fit:cover;display:block}
.tt-title{flex:1;overflow:hidden}
.tt-title h5{color:#f97316;font-size:13px;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tt-title .tt-bc-sub{font-size:10px;color:#64748b;font-family:monospace}
.tt-row{display:flex;justify-content:space-between;gap:10px;margin-bottom:4px;font-size:11px}
.tt-key{color:#64748b}.tt-val{color:#e2e8f0;font-weight:600}
.tt-bar-wrap{height:4px;border-radius:3px;background:#1e293b;margin-top:6px;overflow:hidden}
.tt-bar-fill{height:100%;border-radius:3px;transition:.3s}

/* ── Legend ── */
#legend-bar{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px;font-size:11px;color:#64748b}
.leg-item{display:flex;align-items:center;gap:5px}
.leg-dot{width:9px;height:9px;border-radius:50%}
</style>
</head>
<body>

<!-- Toolbar -->
<div id="toolbar">
  <button class="tb-btn" id="btn-add">＋ เพิ่มช่อง</button>
  <button class="tb-btn" id="btn-clear">🗑 ล้างทั้งหมด</button>
  <div id="search-wrap">
    <span style="font-size:14px;color:#475569">🔍</span>
    <input id="search-inp" type="text" placeholder="ค้นหาบาร์โค้ด / ชื่อสินค้า ..."/>
    <button id="btn-search-clear" title="ล้างการค้นหา">✕</button>
    <button id="btn-search-go">ค้นหา</button>
  </div>
  <span id="search-result-label"></span>
  <span class="tb-label" id="sq-count">ช่อง: 0</span>
</div>

<!-- Canvas -->
<div id="canvas-wrap"></div>

<!-- ════ Create / Edit Modal ════ -->
<div class="overlay" id="create-overlay">
  <div id="create-modal">
    <div class="cm-header">
      <h3 id="cm-title">➕ เพิ่มช่องใหม่</h3>
      <div class="sub" id="cm-sub">ตั้งชื่อ, สี และ Grid ก่อนวางลงผัง</div>
      <div class="tab-bar">
        <button class="tab-btn active" data-tab="tab-general">🎨 ทั่วไป</button>
        <button class="tab-btn" data-tab="tab-grid">🔲 Grid</button>
      </div>
    </div>

    <!-- General tab -->
    <div class="tab-pane active" id="tab-general">
      <div class="field-group">
        <label>ชื่อช่อง</label>
        <input type="text" id="inp-name" placeholder="เช่น ชั้น A-1"/>
      </div>
      <div class="field-group">
        <label>เลือกสี</label>
        <div class="color-swatch-row" id="color-swatches"></div>
      </div>
      <div class="field-group">
        <label>สีกำหนดเอง</label>
        <div style="display:flex;gap:8px;align-items:center">
          <input type="color" id="inp-custom-color" value="#f97316"
            style="width:40px;height:36px;border:none;background:none;cursor:pointer;padding:0"/>
          <span style="font-size:11px;color:#64748b">เลือกสีที่ต้องการ</span>
        </div>
      </div>
    </div>

    <!-- Grid tab -->
    <div class="tab-pane" id="tab-grid">
      <div class="preset-row" id="preset-row"></div>
      <div class="grid-controls">
        <div class="ctrl-group">
          <label>แถว (Rows)</label>
          <input type="number" id="inp-rows" min="1" max="20" value="3"/>
        </div>
        <div class="ctrl-group">
          <label>คอลัมน์ (Cols)</label>
          <input type="number" id="inp-cols" min="1" max="20" value="4"/>
        </div>
        <div class="ctrl-group">
          <label>ช่องว่าง (Gap px)</label>
          <input type="number" id="inp-gap" min="0" max="40" value="6"/>
        </div>
      </div>
      <div id="grid-preview"></div>
    </div>

    <div class="modal-actions">
      <button class="modal-btn modal-btn-secondary" id="btn-cm-cancel">ยกเลิก</button>
      <button class="modal-btn modal-btn-primary" id="btn-cm-done">✔ วางช่อง</button>
    </div>
  </div>
</div>

<!-- ════ Item Grid Modal ════ -->
<div id="item-overlay">
  <div id="item-modal">
    <div id="item-modal-header">
      <h3 id="im-title">📦 รายการสินค้า</h3>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="modal-btn modal-btn-secondary" id="btn-edit-shelf" style="padding:6px 14px;font-size:12px">⚙️ ตั้งค่าช่อง</button>
        <button class="close-btn" id="btn-im-close">✕</button>
      </div>
    </div>
    <div id="item-modal-body">
      <div id="item-grid-el"></div>
    </div>
  </div>
</div>

<!-- ════ Item Edit Modal ════ -->
<div id="edit-item-overlay">
  <div id="edit-item-modal">
    <h4 id="ei-title">✏️ แก้ไขสินค้า</h4>
    <div class="ei-body">
      <label class="empty-toggle">
        <input type="checkbox" id="ei-empty"/> ช่องว่าง (ไม่มีสินค้า)
      </label>
      <div id="ei-fields">
        <div class="ei-group" style="margin-bottom:10px">
          <label>ชื่อสินค้า</label>
          <input type="text" id="ei-name" placeholder="ชื่อสินค้า"/>
        </div>
        <div class="ei-row">
          <div class="ei-group">
            <label>บาร์โค้ด</label>
            <input type="text" id="ei-barcode" placeholder="0000000000000"/>
          </div>
        </div>
        <div class="ei-row">
          <div class="ei-group">
            <label>สต็อก (ชิ้น)</label>
            <input type="number" id="ei-stock" min="0" value="0"/>
          </div>
          <div class="ei-group">
            <label>สต็อกสูงสุด</label>
            <input type="number" id="ei-maxstock" min="1" value="100"/>
          </div>
        </div>
        <div class="ei-group" style="margin-bottom:10px">
          <label style="margin-bottom:5px">เลือกรูปภาพสินค้าตัวอย่าง</label>
          <div class="img-preset-grid" id="img-preset-grid"></div>
        </div>
        <div class="ei-group">
          <label>URL รูปภาพสินค้า</label>
          <input type="text" id="ei-image" placeholder="https://..."/>
        </div>
      </div>
    </div>
    <div class="ei-actions">
      <button class="modal-btn modal-btn-secondary" id="btn-ei-cancel">ยกเลิก</button>
      <button class="modal-btn modal-btn-primary" id="btn-ei-save">✔ บันทึก</button>
    </div>
  </div>
</div>

<!-- Hover tooltip -->
<div id="cell-tooltip">
  <div class="tt-header">
    <div class="tt-img-box" id="tt-img-box">
      <img id="tt-img" src="" alt="สินค้า"/>
    </div>
    <div class="tt-title">
      <h5 id="tt-name"></h5>
      <span class="tt-bc-sub" id="tt-bc"></span>
    </div>
  </div>
  <div class="tt-row"><span class="tt-key">สต็อก</span><span class="tt-val" id="tt-stock"></span></div>
  <div class="tt-row"><span class="tt-key">สถานะ</span><span class="tt-val" id="tt-status"></span></div>
  <div class="tt-bar-wrap"><div class="tt-bar-fill" id="tt-bar"></div></div>
</div>

<!-- Legend -->
<div id="legend-bar">
  <span style="color:#94a3b8;font-weight:600">สถานะ:</span>
  <span class="leg-item"><span class="leg-dot" style="background:#10b981"></span>เพียงพอ</span>
  <span class="leg-item"><span class="leg-dot" style="background:#f97316"></span>ปานกลาง</span>
  <span class="leg-item"><span class="leg-dot" style="background:#ef4444"></span>ต่ำ</span>
  <span class="leg-item"><span class="leg-dot" style="background:#334155;border:1px solid #475569"></span>ว่าง</span>
  <span style="margin-left:16px;color:#94a3b8">🖱️ คลิกช่อง → ดูสินค้า &nbsp;|&nbsp; คลิกสินค้า → แก้ไข &nbsp;|&nbsp; คลิกขวาช่อง → ตั้งค่า &nbsp;|&nbsp; ↘ ลาก/ปรับขนาด</span>
</div>

<script>
/* ════════════════════════════════════════
   CONSTANTS & REAL PRODUCT CATALOG
════════════════════════════════════════ */
const PALETTE = [
  {hex:'#f97316',grad:'linear-gradient(135deg,#f97316,#fb923c)'},
  {hex:'#6366f1',grad:'linear-gradient(135deg,#6366f1,#818cf8)'},
  {hex:'#10b981',grad:'linear-gradient(135deg,#10b981,#34d399)'},
  {hex:'#ef4444',grad:'linear-gradient(135deg,#ef4444,#f87171)'},
  {hex:'#3b82f6',grad:'linear-gradient(135deg,#3b82f6,#60a5fa)'},
  {hex:'#a855f7',grad:'linear-gradient(135deg,#a855f7,#c084fc)'},
  {hex:'#eab308',grad:'linear-gradient(135deg,#eab308,#fde047)'},
  {hex:'#ec4899',grad:'linear-gradient(135deg,#ec4899,#f472b6)'},
  {hex:'#14b8a6',grad:'linear-gradient(135deg,#14b8a6,#2dd4bf)'},
  {hex:'#f43f5e',grad:'linear-gradient(135deg,#f43f5e,#fb7185)'},
];

const PRODUCTS = [
  {name:'น้ำดื่ม 600ml', image:'https://images.unsplash.com/photo-1548839140-29a749e1bc4e?w=200&auto=format&fit=crop&q=80', maxStock:200},
  {name:'ขนมปังโฮลวีท', image:'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=200&auto=format&fit=crop&q=80', maxStock:80},
  {name:'นมสด UHT', image:'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=200&auto=format&fit=crop&q=80', maxStock:120},
  {name:'ไข่ไก่สด', image:'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=200&auto=format&fit=crop&q=80', maxStock:100},
  {name:'บะหมี่กึ่งฯ', image:'https://images.unsplash.com/photo-1612927601601-6638404737ce?w=200&auto=format&fit=crop&q=80', maxStock:150},
  {name:'น้ำอัดลม', image:'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200&auto=format&fit=crop&q=80', maxStock:180},
  {name:'ช็อกโกแลต', image:'https://images.unsplash.com/photo-1511381939415-e44015466834?w=200&auto=format&fit=crop&q=80', maxStock:60},
  {name:'คุกกี้เนยสด', image:'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=200&auto=format&fit=crop&q=80', maxStock:90},
  {name:'ซอสปรุงรส', image:'https://images.unsplash.com/photo-1472476443507-c7a5948772fc?w=200&auto=format&fit=crop&q=80', maxStock:70},
  {name:'น้ำมันพืช 1L', image:'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=200&auto=format&fit=crop&q=80', maxStock:50},
  {name:'ผงซักฟอก', image:'https://images.unsplash.com/photo-1585421514738-01798e348b17?w=200&auto=format&fit=crop&q=80', maxStock:40},
  {name:'แชมพูสระผม', image:'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=200&auto=format&fit=crop&q=80', maxStock:55},
  {name:'สบู่ก้อน', image:'https://images.unsplash.com/photo-1607006310492-c07a0c8b6b23?w=200&auto=format&fit=crop&q=80', maxStock:80},
  {name:'ยาสีฟัน', image:'https://images.unsplash.com/photo-1559591937-e1032c1c9ff5?w=200&auto=format&fit=crop&q=80', maxStock:65},
  {name:'กระดาษทิชชู่', image:'https://images.unsplash.com/photo-1584556812952-905ffd0c611a?w=200&auto=format&fit=crop&q=80', maxStock:100},
  {name:'กาแฟสำเร็จรูป', image:'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=200&auto=format&fit=crop&q=80', maxStock:75},
  {name:'ข้าวสารหอมมะลิ', image:'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=200&auto=format&fit=crop&q=80', maxStock:45},
  {name:'น้ำส้มคั้นสด', image:'https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=200&auto=format&fit=crop&q=80', maxStock:90},
  {name:'แอปเปิ้ลแดง', image:'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=200&auto=format&fit=crop&q=80', maxStock:110},
  {name:'ส้มสายน้ำผึ้ง', image:'https://images.unsplash.com/photo-1611080626919-7cf5a9dbab5b?w=200&auto=format&fit=crop&q=80', maxStock:110}
];

const PRESETS = [
  {label:'2×3',rows:2,cols:3},{label:'3×4',rows:3,cols:4},
  {label:'4×4',rows:4,cols:4},{label:'2×6',rows:2,cols:6},
  {label:'5×5',rows:5,cols:5},{label:'6×6',rows:6,cols:6},
];

/* ════════════════════════════════════════
   STATE
════════════════════════════════════════ */
const wrap      = document.getElementById('canvas-wrap');
const sqCountEl = document.getElementById('sq-count');
let squares     = [];
let nextId      = 1;
let paletteIdx  = 0;

let activeSq    = null;   // square being configured / viewed
let editItemIdx = null;   // item index being edited

/* ════════════════════════════════════════
   DATA HELPERS
════════════════════════════════════════ */
function randItem(i){
  const p = PRODUCTS[i % PRODUCTS.length];
  const empty = Math.random() < 0.1;
  return {
    name: p.name,
    image: p.image,
    barcode: '8' + String(Math.floor(Math.random() * 100000000000)).padStart(11, '0'),
    stock: empty ? 0 : Math.floor(Math.random() * p.maxStock) + 1,
    maxStock: p.maxStock,
    empty
  };
}

function generateItems(r, c){
  const a = [];
  for(let i = 0; i < r * c; i++) a.push(randItem(i));
  return a;
}

function stockClass(item){
  if(item.empty || item.stock === 0) return {cell:'cell-empty',badge:'badge-empty',ind:'ind-empty',status:'ว่าง',color:'#334155'};
  const p = item.stock / item.maxStock;
  if(p > 0.5) return {cell:'cell-green',badge:'badge-green',ind:'ind-green',status:'เพียงพอ',color:'#10b981'};
  if(p > 0.2) return {cell:'cell-orange',badge:'badge-orange',ind:'ind-orange',status:'ปานกลาง',color:'#f97316'};
  return {cell:'cell-red',badge:'badge-red',ind:'ind-red',status:'⚠️ ต่ำ',color:'#ef4444'};
}

/* ════════════════════════════════════════
   COLLISION
════════════════════════════════════════ */
function rectOf(el){ return {x:parseFloat(el.style.left)||0, y:parseFloat(el.style.top)||0, w:el.offsetWidth, h:el.offsetHeight}; }
function overlaps(a, b){ return !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y); }
function resolveCollision(el){
  const wW = wrap.clientWidth, wH = wrap.clientHeight;
  let r = rectOf(el);
  r.x = Math.max(0, Math.min(r.x, wW - r.w)); r.y = Math.max(0, Math.min(r.y, wH - r.h));
  el.style.left = r.x + 'px'; el.style.top = r.y + 'px';
  for(const s of squares){
    if(s.el === el) continue;
    const o = rectOf(s.el);
    if(overlaps(r, o)){
      s.el.classList.add('collision'); setTimeout(() => s.el.classList.remove('collision'), 450);
      const oL = (r.x + r.w) - o.x, oR = (o.x + o.w) - r.x, oT = (r.y + r.h) - o.y, oB = (o.y + o.h) - r.y;
      const mn = Math.min(oL, oR, oT, oB);
      if(mn === oL) r.x = o.x - r.w; else if(mn === oR) r.x = o.x + o.w;
      else if(mn === oT) r.y = o.y - r.h; else r.y = o.y + o.h;
      r.x = Math.max(0, Math.min(r.x, wW - r.w)); r.y = Math.max(0, Math.min(r.y, wH - r.h));
      el.style.left = r.x + 'px'; el.style.top = r.y + 'px';
    }
  }
}

/* ════════════════════════════════════════
   DRAG & RESIZE
════════════════════════════════════════ */
function makeDraggable(el){
  let ox, oy, sx, sy, dragging = false;
  el.addEventListener('mousedown', e => {
    if(e.target.closest('.delete-btn,.edit-btn,.resize-handle')) return;
    dragging = true; ox = e.clientX - parseFloat(el.style.left || 0); oy = e.clientY - parseFloat(el.style.top || 0);
    sx = e.clientX; sy = e.clientY; el.classList.add('dragging'); e.preventDefault();
  });
  document.addEventListener('mousemove', e => {
    if(!dragging) return;
    let nx = Math.max(0, Math.min(e.clientX - ox, wrap.clientWidth - el.offsetWidth));
    let ny = Math.max(0, Math.min(e.clientY - oy, wrap.clientHeight - el.offsetHeight));
    el.style.left = nx + 'px'; el.style.top = ny + 'px';
  });
  document.addEventListener('mouseup', e => {
    if(!dragging) return;
    dragging = false; el.classList.remove('dragging'); resolveCollision(el);
    el._dragged = Math.hypot(e.clientX - sx, e.clientY - sy) > 6;
    setTimeout(() => el._dragged = false, 80);
  });
  // touch
  el.addEventListener('touchstart', e => {
    if(e.target.closest('.resize-handle')) return;
    const t = e.touches[0]; ox = t.clientX - parseFloat(el.style.left || 0); oy = t.clientY - parseFloat(el.style.top || 0);
    dragging = true; e.preventDefault();
  }, {passive:false});
  document.addEventListener('touchmove', e => {
    if(!dragging) return;
    const t = e.touches[0];
    el.style.left = Math.max(0, Math.min(t.clientX - ox, wrap.clientWidth - el.offsetWidth)) + 'px';
    el.style.top  = Math.max(0, Math.min(t.clientY - oy, wrap.clientHeight - el.offsetHeight)) + 'px';
  }, {passive:false});
  document.addEventListener('touchend', () => { if(!dragging) return; dragging = false; resolveCollision(el); });
}

function makeResizable(handle, el){
  handle.addEventListener('mousedown', e => {
    let sx = e.clientX, sy = e.clientY, sw = el.offsetWidth, sh = el.offsetHeight;
    el._resizing = true; e.stopPropagation(); e.preventDefault();
    const onMove = ev => { el.style.width = Math.max(90, sw + (ev.clientX - sx)) + 'px'; el.style.height = Math.max(80, sh + (ev.clientY - sy)) + 'px'; resolveCollision(el); };
    const onUp = () => { el._resizing = false; document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
    document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp);
  });
}

/* ════════════════════════════════════════
   SQUARE DOM UPDATE
════════════════════════════════════════ */
function updateSquareDom(sq){
  sq.el.style.background = sq.grad;
  sq.el.querySelector('.sq-label').textContent = `${sq.name}\n${sq.rows}×${sq.cols}`;
  const badge = sq.el.querySelector('.sq-badge');
  badge.innerHTML = '';
  sq.items.slice(0, 6).forEach(item => {
    const d = document.createElement('div');
    d.className = 'sq-dot'; d.style.background = stockClass(item).color;
    badge.appendChild(d);
  });
}

/* ════════════════════════════════════════
   PLACE SQUARE
════════════════════════════════════════ */
function placeSquare(cfg){
  const id = nextId++;
  const el = document.createElement('div');
  el.className = 'sq';
  el.style.width = '140px'; el.style.height = '130px';
  const n = squares.length;
  el.style.left = (20 + n % 7 * 26) + 'px'; el.style.top = (20 + n % 7 * 26) + 'px';
  el.innerHTML = `
    <button class="delete-btn" title="ลบ">✕</button>
    <button class="edit-btn" title="ตั้งค่า">⚙️ ตั้งค่า</button>
    <span class="sq-label"></span>
    <div class="sq-badge"></div>
    <div class="resize-handle"></div>
  `;
  const sq = {id, el, name:cfg.name, hex:cfg.hex, grad:cfg.grad, rows:cfg.rows, cols:cfg.cols, gap:cfg.gap, items:generateItems(cfg.rows, cfg.cols)};
  squares.push(sq);
  wrap.appendChild(el);
  sqCountEl.textContent = `ช่อง: ${squares.length}`;
  updateSquareDom(sq);
  resolveCollision(el);

  // apply current search
  const q = document.getElementById('search-inp').value.trim();
  if(q){ const hit = sqMatchesQuery(sq, q); el.classList.toggle('match', hit); el.classList.toggle('dimmed', !hit); }

  // delete
  el.querySelector('.delete-btn').addEventListener('click', e => {
    e.stopPropagation(); el.remove();
    squares = squares.filter(s => s.id !== id);
    sqCountEl.textContent = `ช่อง: ${squares.length}`;
  });

  // gear button = settings
  el.querySelector('.edit-btn').addEventListener('click', e => {
    e.stopPropagation(); openCreateModal(sq);
  });

  // right-click = settings
  el.addEventListener('contextmenu', e => { e.preventDefault(); openCreateModal(sq); });

  // left click = item grid
  el.addEventListener('click', e => {
    if(el._dragged || el._resizing) return;
    if(e.target.closest('.delete-btn,.edit-btn,.resize-handle')) return;
    openItemModal(sq);
  });

  makeDraggable(el);
  makeResizable(el.querySelector('.resize-handle'), el);
  return sq;
}

/* ════════════════════════════════════════
   BUILD COLOR SWATCHES & PRESETS
════════════════════════════════════════ */
const swatchContainer = document.getElementById('color-swatches');
PALETTE.forEach((p, i) => {
  const s = document.createElement('div');
  s.className = 'cswatch'; s.style.background = p.grad; s.dataset.idx = i;
  swatchContainer.appendChild(s);
});

const presetRow = document.getElementById('preset-row');
PRESETS.forEach(p => {
  const b = document.createElement('button');
  b.className = 'preset-btn'; b.textContent = p.label;
  b.addEventListener('click', () => {
    document.getElementById('inp-rows').value = p.rows;
    document.getElementById('inp-cols').value = p.cols;
    document.querySelectorAll('.preset-btn').forEach(x => x.classList.remove('active'));
    b.classList.add('active'); renderGridPreview();
  });
  presetRow.appendChild(b);
});

/* ════════════════════════════════════════
   CREATE / EDIT MODAL
════════════════════════════════════════ */
const createOverlay = document.getElementById('create-overlay');
const inpRows = document.getElementById('inp-rows');
const inpCols = document.getElementById('inp-cols');
const inpGap  = document.getElementById('inp-gap');
let cmMode    = 'create';
let cmColorIdx= 0;

function renderGridPreview(){
  const r = Math.max(1, +inpRows.value || 1);
  const c = Math.max(1, +inpCols.value || 1);
  const g = Math.max(0, +inpGap.value  || 0);
  const pv = document.getElementById('grid-preview');
  pv.innerHTML = '';
  const grid = document.createElement('div');
  grid.className = 'gp-grid';
  grid.style.cssText = `grid-template-columns:repeat(${c},40px);--gap:${g}px`;
  const grad = PALETTE[cmColorIdx]?.grad || PALETTE[0].grad;
  for(let i = 0; i < r * c; i++){
    const cell = document.createElement('div');
    cell.className = 'gp-cell'; cell.style.background = grad; cell.style.opacity = '.7'; cell.textContent = i + 1;
    grid.appendChild(cell);
  }
  pv.appendChild(grid);
}

[inpRows, inpCols, inpGap].forEach(el => el.addEventListener('input', () => {
  document.querySelectorAll('.preset-btn').forEach(x => x.classList.remove('active'));
  renderGridPreview();
}));

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  });
});

// Swatch click
document.querySelectorAll('.cswatch').forEach(s => {
  s.addEventListener('click', () => {
    document.querySelectorAll('.cswatch').forEach(x => x.classList.remove('active'));
    s.classList.add('active'); cmColorIdx = +s.dataset.idx;
    document.getElementById('inp-custom-color').value = PALETTE[cmColorIdx].hex;
    renderGridPreview();
  });
});

function openCreateModal(sq){
  cmMode = sq ? 'edit' : 'create';
  activeSq = sq || null;
  document.getElementById('cm-title').textContent = sq ? `⚙️ ตั้งค่า — ${sq.name}` : '➕ เพิ่มช่องใหม่';
  document.getElementById('cm-sub').textContent   = sq ? 'แก้ไขชื่อ, สี และ Grid' : 'ตั้งชื่อ, สี และ Grid ก่อนวางลงผัง';
  document.getElementById('btn-cm-done').textContent = sq ? '✔ บันทึก' : '✔ วางช่อง';

  document.getElementById('inp-name').value = sq ? sq.name : `ช่อง ${nextId}`;
  inpRows.value = sq ? sq.rows : 3;
  inpCols.value = sq ? sq.cols : 4;
  inpGap.value  = sq ? sq.gap  : 6;

  const palIdx = sq ? PALETTE.findIndex(p => p.hex === sq.hex) : paletteIdx % PALETTE.length;
  cmColorIdx = palIdx >= 0 ? palIdx : 0;
  document.querySelectorAll('.cswatch').forEach((s, i) => s.classList.toggle('active', i === cmColorIdx));
  document.getElementById('inp-custom-color').value = PALETTE[cmColorIdx].hex;

  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-tab="tab-general"]').classList.add('active');
  document.getElementById('tab-general').classList.add('active');

  renderGridPreview();
  createOverlay.classList.add('show');
}

document.getElementById('btn-cm-cancel').addEventListener('click', () => createOverlay.classList.remove('show'));
createOverlay.addEventListener('click', e => { if(e.target === createOverlay) createOverlay.classList.remove('show'); });

document.getElementById('btn-cm-done').addEventListener('click', () => {
  const name = document.getElementById('inp-name').value.trim() || `ช่อง ${nextId}`;
  const customHex = document.getElementById('inp-custom-color').value;
  const palHex = PALETTE[cmColorIdx]?.hex || '#f97316';
  const finalHex  = (customHex && customHex !== palHex) ? customHex : palHex;
  const finalGrad = (customHex && customHex !== palHex)
    ? `linear-gradient(135deg,${finalHex},${finalHex}bb)`
    : PALETTE[cmColorIdx]?.grad || PALETTE[0].grad;
  const rows = Math.max(1, +inpRows.value || 1);
  const cols = Math.max(1, +inpCols.value || 1);
  const gap  = Math.max(0, +inpGap.value  || 0);

  createOverlay.classList.remove('show');

  if(cmMode === 'create'){
    paletteIdx++;
    placeSquare({name, hex:finalHex, grad:finalGrad, rows, cols, gap});
  } else {
    const gridChanged = rows !== activeSq.rows || cols !== activeSq.cols;
    activeSq.name = name; activeSq.hex = finalHex; activeSq.grad = finalGrad;
    activeSq.rows = rows; activeSq.cols = cols; activeSq.gap = gap;
    if(gridChanged) activeSq.items = generateItems(rows, cols);
    updateSquareDom(activeSq);
    const q = document.getElementById('search-inp').value.trim();
    if(q){ const hit = sqMatchesQuery(activeSq, q); activeSq.el.classList.toggle('match', hit); activeSq.el.classList.toggle('dimmed', !hit); }
  }
});

/* ════════════════════════════════════════
   ITEM GRID MODAL
════════════════════════════════════════ */
const itemOverlay = document.getElementById('item-overlay');
const itemGridEl  = document.getElementById('item-grid-el');
const cellTooltip = document.getElementById('cell-tooltip');

document.getElementById('btn-im-close').addEventListener('click', () => { itemOverlay.classList.remove('show'); cellTooltip.style.display = 'none'; });
itemOverlay.addEventListener('click', e => { if(e.target === itemOverlay){ itemOverlay.classList.remove('show'); cellTooltip.style.display = 'none'; } });
document.getElementById('btn-edit-shelf').addEventListener('click', () => {
  itemOverlay.classList.remove('show');
  openCreateModal(activeSq);
});

function openItemModal(sq){
  activeSq = sq;
  document.getElementById('im-title').textContent = `📦 ${sq.name}  (${sq.rows}×${sq.cols})`;
  buildItemGrid(sq);
  itemOverlay.classList.add('show');
}

function buildItemGrid(sq){
  itemGridEl.innerHTML = '';
  itemGridEl.style.gridTemplateColumns = `repeat(${sq.cols}, 1fr)`;
  itemGridEl.style.gap = sq.gap + 'px';
  sq.items.forEach((item, idx) => {
    const cls = stockClass(item);
    const cell = document.createElement('div');
    cell.className = `item-cell ${cls.cell}`;
    
    const imgHtml = item.empty
      ? `<div class="cell-img"><div class="cell-img-empty">📦</div></div>`
      : `<div class="cell-img"><img src="${item.image}" alt="${item.name}" loading="lazy" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1584556812952-905ffd0c611a?w=150&auto=format&fit=crop&q=80'"/></div>`;

    cell.innerHTML = `
      <div class="cell-indicator ${cls.ind}"></div>
      <span class="cell-edit-badge">✏️ แก้ไข</span>
      ${imgHtml}
      <div class="cell-name">${item.empty ? '— ว่าง —' : item.name}</div>
      <div class="cell-barcode">${item.empty ? '' : item.barcode}</div>
      <div class="cell-stock-badge ${cls.badge}">${item.empty ? 'ว่าง' : `${item.stock} ชิ้น`}</div>
    `;
    cell.addEventListener('mouseenter', e => showTooltip(e, item, cls));
    cell.addEventListener('mousemove',  e => moveTooltip(e));
    cell.addEventListener('mouseleave', () => cellTooltip.style.display = 'none');
    cell.addEventListener('click', () => openItemEdit(sq, idx));
    itemGridEl.appendChild(cell);
  });
}

function showTooltip(e, item, cls){
  const imgEl = document.getElementById('tt-img');
  const imgBox = document.getElementById('tt-img-box');
  if(item.empty){
    imgEl.style.display = 'none';
    imgBox.innerHTML = '<span style="font-size:22px;color:#64748b">📦</span>';
  } else {
    imgBox.innerHTML = `<img id="tt-img" src="${item.image}" alt="${item.name}"/>`;
  }
  document.getElementById('tt-name').textContent  = item.empty ? 'ว่าง' : item.name;
  document.getElementById('tt-bc').textContent    = item.empty ? '—' : item.barcode;
  document.getElementById('tt-stock').textContent = item.empty ? '—' : `${item.stock} / ${item.maxStock} ชิ้น`;
  document.getElementById('tt-status').textContent= cls.status;
  document.getElementById('tt-status').style.color= cls.color;
  const bar = document.getElementById('tt-bar');
  bar.style.width = (item.empty ? 0 : Math.round(item.stock / item.maxStock * 100)) + '%';
  bar.style.background = cls.color;
  moveTooltip(e);
  cellTooltip.style.display = 'block';
}

function moveTooltip(e){
  let tx = e.clientX + 14, ty = e.clientY - 8;
  const tw = cellTooltip.offsetWidth || 220, th = cellTooltip.offsetHeight || 150;
  if(tx + tw > window.innerWidth)  tx = e.clientX - tw - 10;
  if(ty + th > window.innerHeight) ty = e.clientY - th - 10;
  cellTooltip.style.left = tx + 'px'; cellTooltip.style.top = ty + 'px';
}

/* ════════════════════════════════════════
   ITEM EDIT MODAL (WITH REAL IMAGE PRESETS)
════════════════════════════════════════ */
const editItemOverlay = document.getElementById('edit-item-overlay');
const imgPresetGrid = document.getElementById('img-preset-grid');

PRODUCTS.forEach(p => {
  const b = document.createElement('button');
  b.className = 'img-preset-btn';
  b.title = p.name;
  b.innerHTML = `<img src="${p.image}" alt="${p.name}" loading="lazy"/>`;
  b.addEventListener('click', () => {
    document.querySelectorAll('.img-preset-btn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    document.getElementById('ei-image').value = p.image;
    if(!document.getElementById('ei-name').value.trim() || document.getElementById('ei-name').value.trim() === '— ว่าง —'){
      document.getElementById('ei-name').value = p.name;
    }
  });
  imgPresetGrid.appendChild(b);
});

const eiEmpty = document.getElementById('ei-empty');
eiEmpty.addEventListener('change', () => {
  document.getElementById('ei-fields').querySelectorAll('input').forEach(el => {
    if(el === eiEmpty) return;
    el.disabled = eiEmpty.checked;
    el.style.opacity = eiEmpty.checked ? .4 : 1;
  });
  imgPresetGrid.style.opacity = eiEmpty.checked ? .3 : 1;
  imgPresetGrid.style.pointerEvents = eiEmpty.checked ? 'none' : 'auto';
});

function openItemEdit(sq, idx){
  activeSq = sq; editItemIdx = idx;
  const item = sq.items[idx];
  document.getElementById('ei-title').textContent = `✏️ แก้ไขสินค้า — ช่อง ${idx + 1}`;
  eiEmpty.checked = item.empty;
  document.getElementById('ei-name').value     = item.empty ? '' : item.name;
  document.getElementById('ei-barcode').value  = item.empty ? '' : item.barcode;
  document.getElementById('ei-stock').value    = item.stock;
  document.getElementById('ei-maxstock').value = item.maxStock;
  document.getElementById('ei-image').value    = item.image || '';

  document.getElementById('ei-fields').querySelectorAll('input').forEach(el => {
    el.disabled = item.empty; el.style.opacity = item.empty ? .4 : 1;
  });
  imgPresetGrid.style.opacity = item.empty ? .3 : 1;
  imgPresetGrid.style.pointerEvents = item.empty ? 'none' : 'auto';

  document.querySelectorAll('.img-preset-btn').forEach(b => {
    const imgEl = b.querySelector('img');
    b.classList.toggle('active', imgEl && imgEl.src === item.image);
  });
  editItemOverlay.classList.add('show');
}

document.getElementById('btn-ei-cancel').addEventListener('click', () => editItemOverlay.classList.remove('show'));
editItemOverlay.addEventListener('click', e => { if(e.target === editItemOverlay) editItemOverlay.classList.remove('show'); });

document.getElementById('btn-ei-save').addEventListener('click', () => {
  if(!activeSq || editItemIdx === null) return;
  const item = activeSq.items[editItemIdx];
  item.empty    = eiEmpty.checked;
  item.name     = document.getElementById('ei-name').value.trim() || (item.empty ? '' : 'สินค้า');
  item.barcode  = document.getElementById('ei-barcode').value.trim() || item.barcode;
  item.stock    = Math.max(0, +document.getElementById('ei-stock').value || 0);
  item.maxStock = Math.max(1, +document.getElementById('ei-maxstock').value || 1);
  item.image    = document.getElementById('ei-image').value.trim() || PRODUCTS[0].image;
  if(item.empty){ item.stock = 0; }

  editItemOverlay.classList.remove('show');
  buildItemGrid(activeSq);
  updateSquareDom(activeSq);

  const q = document.getElementById('search-inp').value.trim();
  if(q){ const hit = sqMatchesQuery(activeSq, q); activeSq.el.classList.toggle('match', hit); activeSq.el.classList.toggle('dimmed', !hit); }
});

/* ════════════════════════════════════════
   SEARCH
════════════════════════════════════════ */
const searchInp   = document.getElementById('search-inp');
const searchClear = document.getElementById('btn-search-clear');
const searchLabel = document.getElementById('search-result-label');
function norm(s){ return s.toLowerCase().replace(/\s+/g, ''); }
function sqMatchesQuery(sq, q){
  if(!q) return true;
  const nq = norm(q);
  if(norm(sq.name).includes(nq)) return true;
  return sq.items.some(it => !it.empty && (norm(it.name).includes(nq) || it.barcode.includes(q)));
}
function applySearch(){
  const q = searchInp.value.trim();
  if(!q){ clearSearch(); return; }
  let cnt = 0;
  squares.forEach(sq => {
    const hit = sqMatchesQuery(sq, q);
    sq.el.classList.toggle('match', hit); sq.el.classList.toggle('dimmed', !hit);
    if(hit) cnt++;
  });
  searchClear.style.display = 'block';
  searchLabel.textContent = cnt === 0 ? '⚠️ ไม่พบสินค้า' : `พบ ${cnt} ช่อง`;
  searchLabel.style.color = cnt === 0 ? '#f87171' : '#34d399';
}
function clearSearch(){
  searchInp.value = ''; searchClear.style.display = 'none'; searchLabel.textContent = '';
  squares.forEach(sq => sq.el.classList.remove('match', 'dimmed'));
}
searchInp.addEventListener('input', applySearch);
searchInp.addEventListener('keydown', e => { if(e.key === 'Enter') applySearch(); });
document.getElementById('btn-search-go').addEventListener('click', applySearch);
searchClear.addEventListener('click', clearSearch);

/* ════════════════════════════════════════
   TOOLBAR ACTIONS
════════════════════════════════════════ */
document.getElementById('btn-add').addEventListener('click', () => openCreateModal(null));
document.getElementById('btn-clear').addEventListener('click', () => {
  squares.forEach(s => s.el.remove()); squares = []; nextId = 1; paletteIdx = 0;
  sqCountEl.textContent = 'ช่อง: 0'; clearSearch();
});

/* ════════════════════════════════════════
   SEED
════════════════════════════════════════ */
placeSquare({name:'ชั้น A-1', hex:PALETTE[0].hex, grad:PALETTE[0].grad, rows:3, cols:4, gap:6});
placeSquare({name:'ชั้น B-2', hex:PALETTE[1].hex, grad:PALETTE[1].grad, rows:2, cols:3, gap:6});
</script>
</body>
</html>
"""

components.html(CANVAS_HTML, height=700, scrolling=False)
