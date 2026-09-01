import streamlit as st
import streamlit.components.v1 as components

st.title("📦 Stock 3D Layout")
st.caption("จัดวางสินค้าบนชั้นวาง 3D — เพิ่มช่อง, ลากย้าย, หมุน/ซูม, คลิกเพื่อดูสินค้าใน 3D Shelf")

st.divider()

CANVAS_3D = r"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#0a0f1e;color:#e2e8f0;overflow:hidden;height:100vh;display:flex;flex-direction:column}

/* ── Toolbar ── */
#toolbar{display:flex;align-items:center;gap:8px;padding:9px 12px;background:rgba(15,23,42,.95);border-bottom:1px solid #1e293b;flex-wrap:wrap;flex-shrink:0}
.tb-btn{padding:7px 15px;border:none;border-radius:8px;cursor:pointer;font-size:12px;font-weight:600;transition:.15s;font-family:inherit}
#btn-add{background:linear-gradient(135deg,#f97316,#fb923c);color:#fff}
#btn-add:hover{filter:brightness(1.2);transform:translateY(-1px)}
#btn-clear{background:#1e293b;color:#94a3b8;border:1px solid #334155}
#btn-clear:hover{border-color:#f97316;color:#f97316}
.view-btn{padding:5px 11px;border-radius:6px;font-size:11px;font-weight:600;border:1px solid #334155;background:#1e293b;color:#64748b;cursor:pointer;transition:.15s;font-family:inherit}
.view-btn:hover,.view-btn.active{background:#f97316;border-color:#f97316;color:#fff}
#btn-autorot{padding:5px 11px;border-radius:6px;font-size:11px;font-weight:600;border:1px solid #334155;background:#1e293b;color:#64748b;cursor:pointer;font-family:inherit}
#btn-autorot.on{background:rgba(249,115,22,.2);border-color:#f97316;color:#f97316}
#search-wrap{display:flex;align-items:center;gap:5px;background:#1e293b;border:1px solid #334155;border-radius:9px;padding:4px 9px;flex:1;max-width:320px;transition:.2s}
#search-wrap:focus-within{border-color:#f97316;box-shadow:0 0 0 2px rgba(249,115,22,.2)}
#search-inp{background:none;border:none;outline:none;color:#e2e8f0;font-size:12px;flex:1;padding:2px 0;font-family:inherit}
#search-inp::placeholder{color:#475569}
#btn-sg{background:linear-gradient(135deg,#f97316,#fb923c);border:none;color:#fff;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600;cursor:pointer;font-family:inherit}
#btn-sc{background:none;border:none;color:#64748b;font-size:14px;cursor:pointer;padding:1px 4px;display:none}
#btn-sc:hover{color:#f87171}
#search-label{font-size:11px;white-space:nowrap}
.tb-sep{width:1px;height:22px;background:#1e293b;margin:0 2px}
.tb-right{margin-left:auto;display:flex;align-items:center;gap:8px}
#box-count{font-size:11px;color:#64748b}

/* ── Main Canvas ── */
#c3d{display:block;flex:1;cursor:grab}
#c3d.grabbing{cursor:grabbing}

/* ── Legend ── */
#legend-bar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:7px 14px;background:rgba(15,23,42,.9);border-top:1px solid #1e293b;font-size:11px;color:#64748b;flex-shrink:0}
.leg-item{display:flex;align-items:center;gap:5px}
.leg-dot{width:9px;height:9px;border-radius:50%}
#hint-text{margin-left:auto;color:#475569;font-size:11px}

/* ── Create/Settings Modal ── */
#cm-ovl{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);backdrop-filter:blur(6px);z-index:100;align-items:center;justify-content:center}
#cm-ovl.show{display:flex}
#cm{background:#1e293b;border:1px solid #334155;border-radius:20px;width:min(560px,96vw);box-shadow:0 24px 70px rgba(0,0,0,.8);overflow:hidden}
.cm-hd{padding:18px 22px 0}
.cm-hd h3{font-size:15px;font-weight:700;color:#f97316;margin-bottom:3px}
.cm-hd .sub{font-size:11px;color:#64748b;margin-bottom:12px}
.tab-bar{display:flex;border-bottom:1px solid #334155}
.t-btn{padding:9px 16px;font-size:12px;font-weight:600;cursor:pointer;border:none;background:none;color:#64748b;border-bottom:2px solid transparent;transition:.15s;margin-bottom:-1px;font-family:inherit}
.t-btn.active{color:#f97316;border-bottom-color:#f97316}
.t-pane{display:none;padding:16px 22px}
.t-pane.active{display:block}
.fgrp{margin-bottom:12px}
.fgrp label{font-size:11px;color:#94a3b8;display:block;margin-bottom:4px}
.fgrp input[type=text],.fgrp input[type=number]{width:100%;padding:7px 10px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:#e2e8f0;font-size:13px;outline:none;transition:.15s;font-family:inherit}
.fgrp input:focus{border-color:#f97316}
.sw-row{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.sw{width:27px;height:27px;border-radius:6px;cursor:pointer;border:2px solid transparent;transition:.12s;flex-shrink:0}
.sw:hover{transform:scale(1.15)}.sw.active{border-color:#fff;box-shadow:0 0 0 2px #f97316}
.pre-row{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.pre-btn{padding:4px 12px;border-radius:6px;font-size:12px;font-weight:600;background:#0f172a;border:1px solid #334155;color:#94a3b8;cursor:pointer;transition:.15s;font-family:inherit}
.pre-btn:hover,.pre-btn.active{background:#f97316;border-color:#f97316;color:#fff}
.g-ctrls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.gc{flex:1;min-width:80px}
.gc label{font-size:11px;color:#94a3b8;display:block;margin-bottom:4px}
.gc input{width:100%;padding:6px 9px;background:#0f172a;border:1px solid #334155;border-radius:7px;color:#e2e8f0;font-size:12px;outline:none;font-family:inherit}
.gc input:focus{border-color:#f97316}
#gp{width:100%;overflow:auto;max-height:160px;border:1px solid #0f172a;border-radius:8px;padding:10px;background:#0f172a}
.gp-grid{display:inline-grid}
.gp-cell{width:36px;height:36px;border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:9px;color:#fff;font-weight:700}
.m-act{display:flex;gap:8px;justify-content:flex-end;padding:12px 22px;border-top:1px solid #334155}
.m-btn{padding:7px 18px;border:none;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;transition:.15s;font-family:inherit}
.m-prim{background:linear-gradient(135deg,#f97316,#fb923c);color:#fff}.m-prim:hover{filter:brightness(1.1)}
.m-sec{background:#0f172a;color:#64748b;border:1px solid #334155}.m-sec:hover{border-color:#f97316;color:#f97316}

/* ── Shelf 3D Modal ── */
#im-ovl{display:none;position:fixed;inset:0;background:rgba(0,0,0,.82);backdrop-filter:blur(8px);z-index:110;align-items:center;justify-content:center}
#im-ovl.show{display:flex}
#im{background:#0f1929;border:1px solid #1e293b;border-radius:20px;width:min(840px,96vw);max-height:92vh;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 32px 90px rgba(0,0,0,.9)}
#im-hd{padding:14px 20px 12px;border-bottom:1px solid #1e293b;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;background:rgba(15,23,42,.8)}
#im-hd h3{font-size:14px;font-weight:700;color:#f97316}
.im-acts{display:flex;gap:7px;align-items:center}
.cl-btn{background:none;border:none;color:#64748b;font-size:16px;cursor:pointer;padding:2px 5px;border-radius:4px;transition:.15s;font-family:inherit}
.cl-btn:hover{color:#f97316}
/* shelf canvas container */
#shelf-wrap{flex:1;position:relative;overflow:hidden;background:#050810;min-height:360px}
#shelf-c{display:block;cursor:grab;width:100%;height:100%}
#shelf-c.grabbing{cursor:grabbing}
/* shelf controls bar */
#shelf-controls{
  display:flex;align-items:center;gap:8px;padding:7px 16px;
  border-top:1px solid #1e293b;flex-shrink:0;
  background:rgba(10,15,30,.95);
}
#shelf-controls span{font-size:10px;color:#64748b;flex:1}
.s-btn{padding:4px 10px;border-radius:5px;font-size:10px;font-weight:600;border:1px solid #334155;background:#1e293b;color:#64748b;cursor:pointer;font-family:inherit;transition:.12s}
.s-btn:hover{border-color:#f97316;color:#f97316}

/* ── Item Edit Modal (With Real Product Presets) ── */
#ei-ovl{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(4px);z-index:120;align-items:center;justify-content:center}
#ei-ovl.show{display:flex}
#ei{background:#1e293b;border:1px solid #334155;border-radius:18px;width:min(440px,96vw);box-shadow:0 20px 60px rgba(0,0,0,.8);overflow:hidden}
#ei h4{font-size:13px;font-weight:700;color:#f97316;padding:14px 18px 10px;border-bottom:1px solid #334155}
.ei-body{padding:14px 18px;max-height:75vh;overflow-y:auto}
.ei-r{display:flex;gap:8px;margin-bottom:10px}
.eg{flex:1}.eg label{font-size:10px;color:#94a3b8;display:block;margin-bottom:3px}
.eg input{width:100%;padding:6px 8px;background:#0f172a;border:1px solid #334155;border-radius:7px;color:#e2e8f0;font-size:12px;outline:none;font-family:inherit}
.eg input:focus{border-color:#f97316}

.img-preset-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(46px,1fr));gap:6px;
  max-height:120px;overflow-y:auto;padding:5px;
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

.ei-toggle{display:flex;align-items:center;gap:7px;margin-bottom:10px;font-size:11px;color:#94a3b8;cursor:pointer}
.ei-toggle input{accent-color:#f97316;width:14px;height:14px;cursor:pointer}
.ei-act{display:flex;gap:7px;justify-content:flex-end;padding:10px 18px;border-top:1px solid #334155}

/* ── Tooltip ── */
#tt{
  display:none;position:fixed;z-index:130;pointer-events:none;
  background:rgba(10,15,30,.97);border:1px solid #f97316;
  border-radius:12px;padding:12px 14px;min-width:210px;
  box-shadow:0 10px 36px rgba(0,0,0,.7);backdrop-filter:blur(8px);
}
.tt-hd{display:flex;align-items:center;gap:9px;margin-bottom:8px}
.tt-img-box{
  width:46px;height:46px;border-radius:8px;overflow:hidden;
  background:#1e293b;flex-shrink:0;border:1px solid rgba(255,255,255,.1);
  display:flex;align-items:center;justify-content:center;
}
.tt-img-box img{width:100%;height:100%;object-fit:cover;display:block}
.tt-title-wrap{flex:1;overflow:hidden}
.tt-title-wrap h5{color:#f97316;font-size:12px;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tt-title-wrap .tt-sub{font-size:10px;color:#64748b;font-family:monospace}
.tr{display:flex;justify-content:space-between;gap:8px;margin-bottom:3px;font-size:11px}
.tk{color:#64748b}.tv{color:#e2e8f0;font-weight:600}
.tb-bar{height:4px;border-radius:3px;background:#1e293b;margin-top:6px;overflow:hidden}
.tb-fill{height:100%;border-radius:3px}
</style>
</head>
<body>

<!-- Toolbar -->
<div id="toolbar">
  <button class="tb-btn" id="btn-add">＋ เพิ่มช่อง</button>
  <button class="tb-btn" id="btn-clear">🗑 ล้างทั้งหมด</button>
  <div class="tb-sep"></div>
  <button class="view-btn" id="viso">3D</button>
  <button class="view-btn" id="vfront">หน้า</button>
  <button class="view-btn" id="vside">ข้าง</button>
  <button class="view-btn" id="vtop">บน</button>
  <button id="btn-autorot">▶ หมุน</button>
  <div class="tb-sep"></div>
  <div id="search-wrap">
    <span style="font-size:13px;color:#475569">🔍</span>
    <input id="search-inp" type="text" placeholder="บาร์โค้ด / ชื่อสินค้า ..."/>
    <button id="btn-sc">✕</button>
    <button id="btn-sg">ค้นหา</button>
  </div>
  <span id="search-label"></span>
  <div class="tb-right"><span id="box-count">ช่อง: 0</span></div>
</div>

<!-- Main 3D Canvas -->
<canvas id="c3d"></canvas>

<!-- Legend -->
<div id="legend-bar">
  <span style="color:#94a3b8;font-weight:600;font-size:11px">สถานะ:</span>
  <span class="leg-item"><span class="leg-dot" style="background:#10b981"></span>เพียงพอ</span>
  <span class="leg-item"><span class="leg-dot" style="background:#f97316"></span>ปานกลาง</span>
  <span class="leg-item"><span class="leg-dot" style="background:#ef4444"></span>ต่ำ</span>
  <span class="leg-item"><span class="leg-dot" style="background:#334155;border:1px solid #475569"></span>ว่าง</span>
  <span id="hint-text">🖱 ลากว่าง=หมุน · ลากกล่อง=ย้าย · คลิก=เปิด Shelf 3D · คลิกขวา=ตั้งค่า · เลื่อน=ซูม</span>
</div>

<!-- ════ Create/Settings Modal ════ -->
<div id="cm-ovl">
<div id="cm">
  <div class="cm-hd">
    <h3 id="cm-title">➕ เพิ่มช่องใหม่</h3>
    <div class="sub" id="cm-sub">ตั้งชื่อ, สี และ Grid ก่อนวางลงฉาก</div>
    <div class="tab-bar">
      <button class="t-btn active" data-tab="tg">🎨 ทั่วไป</button>
      <button class="t-btn" data-tab="tgr">🔲 Grid</button>
    </div>
  </div>
  <div class="t-pane active" id="tg">
    <div class="fgrp"><label>ชื่อช่อง</label><input type="text" id="inp-name" placeholder="เช่น ชั้น A-1"/></div>
    <div class="fgrp"><label>เลือกสี</label><div class="sw-row" id="sw-row"></div></div>
    <div class="fgrp">
      <label>สีกำหนดเอง</label>
      <div style="display:flex;gap:8px;align-items:center">
        <input type="color" id="inp-cc" value="#f97316" style="width:38px;height:34px;border:none;background:none;cursor:pointer;padding:0"/>
        <span style="font-size:11px;color:#64748b">เลือกสีที่ต้องการ</span>
      </div>
    </div>
  </div>
  <div class="t-pane" id="tgr">
    <div class="pre-row" id="pre-row"></div>
    <div class="g-ctrls">
      <div class="gc"><label>แถว (Rows)</label><input type="number" id="inp-r" min="1" max="12" value="3"/></div>
      <div class="gc"><label>คอลัมน์ (Cols)</label><input type="number" id="inp-c" min="1" max="12" value="4"/></div>
      <div class="gc"><label>ช่องว่าง (Gap)</label><input type="number" id="inp-g" min="0" max="40" value="6"/></div>
    </div>
    <div id="gp"></div>
  </div>
  <div class="m-act">
    <button class="m-btn m-sec" id="btn-cm-cancel">ยกเลิก</button>
    <button class="m-btn m-prim" id="btn-cm-ok">✔ วางช่อง</button>
  </div>
</div>
</div>

<!-- ════ Shelf 3D Modal ════ -->
<div id="im-ovl">
<div id="im">
  <div id="im-hd">
    <h3 id="im-title">📦 ชั้นวางสินค้า 3D</h3>
    <div class="im-acts">
      <button class="m-btn m-sec" id="btn-im-settings" style="padding:5px 12px;font-size:11px">⚙️ ตั้งค่าช่อง</button>
      <button class="cl-btn" id="btn-im-close">✕</button>
    </div>
  </div>
  <div id="shelf-wrap">
    <canvas id="shelf-c"></canvas>
  </div>
  <div id="shelf-controls">
    <span>🖱 ลาก=หมุน · เลื่อน=ซูม · คลิกสินค้า=แก้ไข</span>
    <button class="s-btn" id="s-reset">🔄 รีเซ็ตมุมมอง</button>
    <button class="s-btn" id="s-front">↔ ด้านหน้า</button>
    <button class="s-btn" id="s-iso">◈ 3D</button>
  </div>
</div>
</div>

<!-- ════ Item Edit Modal ════ -->
<div id="ei-ovl">
<div id="ei">
  <h4 id="ei-title">✏️ แก้ไขสินค้า</h4>
  <div class="ei-body">
    <label class="ei-toggle"><input type="checkbox" id="ei-empty"/> ช่องว่าง (ไม่มีสินค้า)</label>
    <div id="ei-fields">
      <div class="eg" style="margin-bottom:10px"><label>ชื่อสินค้า</label><input type="text" id="ei-name" placeholder="ชื่อสินค้า"/></div>
      <div class="ei-r">
        <div class="eg"><label>บาร์โค้ด</label><input type="text" id="ei-bc" placeholder="0000000000000"/></div>
      </div>
      <div class="ei-r">
        <div class="eg"><label>สต็อก (ชิ้น)</label><input type="number" id="ei-stock" min="0" value="0"/></div>
        <div class="eg"><label>สต็อกสูงสุด</label><input type="number" id="ei-max" min="1" value="100"/></div>
      </div>
      <div class="eg" style="margin-bottom:8px">
        <label style="margin-bottom:4px">เลือกรูปภาพสินค้าตัวอย่าง</label>
        <div class="img-preset-grid" id="img-preset-grid"></div>
      </div>
      <div class="eg"><label>URL รูปภาพสินค้า</label><input type="text" id="ei-image" placeholder="https://..."/></div>
    </div>
  </div>
  <div class="ei-act">
    <button class="m-btn m-sec" id="btn-ei-cancel">ยกเลิก</button>
    <button class="m-btn m-prim" id="btn-ei-save">✔ บันทึก</button>
  </div>
</div>
</div>

<!-- Tooltip -->
<div id="tt">
  <div class="tt-hd">
    <div class="tt-img-box" id="tt-img-box">
      <img id="tt-img" src="" alt="สินค้า"/>
    </div>
    <div class="tt-title-wrap">
      <h5 id="tt-name"></h5>
      <span class="tt-sub" id="tt-bc"></span>
    </div>
  </div>
  <div class="tr"><span class="tk">สต็อก</span><span class="tv" id="tt-sk"></span></div>
  <div class="tr"><span class="tk">สถานะ</span><span class="tv" id="tt-st"></span></div>
  <div class="tb-bar"><div class="tb-fill" id="tt-bar"></div></div>
</div>

<script>
/* ══════════════════════════════════════════════════════
   CONSTANTS & REAL PRODUCT CATALOG
══════════════════════════════════════════════════════ */
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

/* Image preloader cache for Canvas 2D */
const imgCache = {};
function getCachedImg(url){
  if(!url) return null;
  if(imgCache[url]) return imgCache[url];
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.src = url;
  img.onload = () => { if(sActiveBox) renderShelf(); };
  imgCache[url] = img;
  return img;
}
// Pre-warm product images
PRODUCTS.forEach(p => getCachedImg(p.image));

/* ══════════════════════════════════════════════════════
   SHARED HELPERS
══════════════════════════════════════════════════════ */
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
  if(item.empty || item.stock === 0) return {cell:'ce',badge:'be',ind:'ie',status:'ว่าง',color:'#334155'};
  const p = item.stock / item.maxStock;
  if(p > 0.5) return {cell:'cg',badge:'bg',ind:'ig',status:'เพียงพอ',color:'#10b981'};
  if(p > 0.2) return {cell:'co',badge:'bo',ind:'io',status:'ปานกลาง',color:'#f97316'};
  return {cell:'cr',badge:'br',ind:'ir',status:'⚠️ ต่ำ',color:'#ef4444'};
}

function stockColor(item){
  if(item.empty || item.stock === 0) return '#1e293b';
  const p = item.stock / item.maxStock;
  if(p > 0.5) return '#10b981';
  if(p > 0.2) return '#f97316';
  return '#ef4444';
}

function hexRgb(hex){
  const h = hex.replace('#', '');
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

function rgba(hex, br, a = 1){
  const [r, g, b] = hexRgb(hex);
  return `rgba(${Math.min(255, Math.round(r * br))},${Math.min(255, Math.round(g * br))},${Math.min(255, Math.round(b * br))},${a})`;
}

function pointInPoly(px, py, poly){
  let inside = false;
  for(let i = 0, j = poly.length - 1; i < poly.length; j = i++){
    const xi = poly[i][0], yi = poly[i][1], xj = poly[j][0], yj = poly[j][1];
    if(((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) inside = !inside;
  }
  return inside;
}

function boxAvgStockColor(box){
  const ne = box.items.filter(i => !i.empty);
  if(!ne.length) return '#334155';
  const avg = ne.reduce((s, i) => s + i.stock / i.maxStock, 0) / ne.length;
  if(avg > 0.5) return '#10b981';
  if(avg > 0.2) return '#f97316';
  return '#ef4444';
}

const tt = document.getElementById('tt');
function hideTT(){ tt.style.display = 'none'; }

/* ══════════════════════════════════════════════════════
   MAIN 3D SCENE
══════════════════════════════════════════════════════ */
const canvas = document.getElementById('c3d');
const ctx = canvas.getContext('2d');
let rotX = -0.42, rotY = 0.55, zoom = 1.0;
let autoRot = false, animId = null;
let boxes = [], nextId = 1, palIdx = 0;
let activeBox = null, editItemIdx = null;
let cmMode = 'create', cmColorIdx = 0;
let hoveredBox = null;

function resizeCanvas(){
  canvas.width  = document.documentElement.clientWidth || 800;
  canvas.height = Math.max(200, document.documentElement.clientHeight - 120);
}
resizeCanvas();
window.addEventListener('resize', () => { resizeCanvas(); render(); sizeShelfCanvas(); });

function project(x, y, z){
  const cY = Math.cos(rotY), sY = Math.sin(rotY);
  let rx = x * cY + z * sY, rz = -x * sY + z * cY;
  const cX = Math.cos(rotX), sX = Math.sin(rotX);
  let ry = y * cX - rz * sX, rz2 = y * sX + rz * cX;
  const fov = 380 * zoom, dist = fov + rz2 * 60, sc = fov / Math.max(1, dist);
  return {px: canvas.width / 2 + rx * sc * 180, py: canvas.height / 2 + ry * sc * 180, depth: rz2, sc};
}

function unproject_xz(dmx, dmy){
  const sc = 180 * zoom, cY = Math.cos(rotY), sY = Math.sin(rotY), sinX = Math.abs(Math.sin(rotX)) || 0.12;
  return {dx:(dmx * cY + dmy * sY / sinX) / sc, dz:(dmx * sY - dmy * cY / sinX) / sc};
}

function drawPoly(ctx2, pts3, fill, stroke = 'rgba(255,255,255,.1)', lw = 0.8, projFn){
  const ps = pts3.map(p => projFn(p[0], p[1], p[2]));
  ctx2.beginPath(); ctx2.moveTo(ps[0].px, ps[0].py);
  for(let i = 1; i < ps.length; i++) ctx2.lineTo(ps[i].px, ps[i].py);
  ctx2.closePath(); ctx2.fillStyle = fill; ctx2.fill();
  if(stroke){ ctx2.strokeStyle = stroke; ctx2.lineWidth = lw; ctx2.stroke(); }
  return ps.map(p => [p.px, p.py]);
}

let hitTargets = [];
function drawBox(box){
  const {x, z, hex, name, rows, cols, h:bh, w, d} = box;
  const x0 = x - w/2, x1 = x + w/2, z0 = z - d/2, z1 = z + d/2, y0 = 0, y1 = bh;
  const hi = box === hoveredBox, dim = box._dimmed;
  const alpha = dim ? 0.18 : 1;
  const stroke = hi ? '#f97316' : 'rgba(255,255,255,.12)';
  const lw = hi ? 2 : 0.7;
  const C = [[x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[x0,y0,z1],[x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1]];
  const faces = [
    {idx:[0,1,5,4], br:0.95, faceId:'front'},{idx:[3,2,6,7], br:0.50, faceId:'back'},
    {idx:[0,3,7,4], br:0.70, faceId:'left'},{idx:[1,2,6,5], br:0.80, faceId:'right'},
    {idx:[4,5,6,7], br:1.30, faceId:'top'},{idx:[0,1,2,3], br:0.25, faceId:'bottom'},
  ];
  faces.forEach(f => {
    const pts = f.idx.map(i => C[i]);
    const cx = pts.reduce((s, p) => s + p[0], 0) / pts.length;
    const cy = pts.reduce((s, p) => s + p[1], 0) / pts.length;
    const cz = pts.reduce((s, p) => s + p[2], 0) / pts.length;
    f.depth = project(cx, cy, cz).depth; f.pts = pts;
  });
  faces.sort((a, b) => b.depth - a.depth);
  let frontPoly = null;
  faces.forEach(f => {
    const fill = rgba(hex, f.br, alpha * 0.92);
    const poly = drawPoly(ctx, f.pts, fill, dim ? 'none' : stroke, lw, project);
    if(f.faceId === 'front') frontPoly = poly;
    if(f.faceId === 'top') box._topPoly = poly;
  });
  if(frontPoly) box._frontPoly = frontPoly;
  if(hi){
    ctx.save(); ctx.shadowColor = '#f97316'; ctx.shadowBlur = 16;
    ctx.strokeStyle = 'rgba(249,115,22,.4)'; ctx.lineWidth = 3;
    if(box._topPoly?.length){
      ctx.beginPath(); ctx.moveTo(box._topPoly[0][0], box._topPoly[0][1]);
      box._topPoly.forEach(p => ctx.lineTo(p[0], p[1])); ctx.closePath(); ctx.stroke();
    }
    ctx.restore();
  }
  // stock strip on front
  if(!dim && frontPoly?.length === 4){
    const sc2 = boxAvgStockColor(box);
    const [tl, tr, br2, bl] = frontPoly, frac = 0.18;
    const sl = [bl[0] + (tl[0] - bl[0]) * frac, bl[1] + (tl[1] - bl[1]) * frac];
    const sr = [br2[0] + (tr[0] - br2[0]) * frac, br2[1] + (tr[1] - br2[1]) * frac];
    ctx.beginPath(); ctx.moveTo(bl[0], bl[1]); ctx.lineTo(br2[0], br2[1]);
    ctx.lineTo(sr[0], sr[1]); ctx.lineTo(sl[0], sl[1]); ctx.closePath();
    ctx.fillStyle = sc2 + 'cc'; ctx.fill();
  }
  // labels
  if(!dim){
    const tc = project(x, y1 + 0.08, z);
    ctx.save(); ctx.fillStyle = 'rgba(255,255,255,.92)'; ctx.font = 'bold 11px Inter,sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(name.length > 14 ? name.slice(0, 13) + '…' : name, tc.px, tc.py); ctx.restore();
    const fc = project(x, y1 / 2, z0 - 0.01);
    ctx.save(); ctx.fillStyle = 'rgba(255,255,255,.6)'; ctx.font = '9px Inter,sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(`${rows}×${cols}`, fc.px, fc.py); ctx.restore();
  }
  hitTargets.push({box, poly:box._frontPoly || [], topPoly:box._topPoly || []});
}

function drawFloor(){
  for(let xi = -8; xi <= 8; xi++){
    for(let zi = -7; zi <= 7; zi++){
      const p1 = project(xi, 0, zi), p2 = project(xi + 1, 0, zi), p3 = project(xi + 1, 0, zi + 1), p4 = project(xi, 0, zi + 1);
      ctx.beginPath(); ctx.moveTo(p1.px, p1.py); ctx.lineTo(p2.px, p2.py); ctx.lineTo(p3.px, p3.py); ctx.lineTo(p4.px, p4.py); ctx.closePath();
      ctx.fillStyle = 'rgba(255,255,255,.012)'; ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,.025)'; ctx.lineWidth = 0.5; ctx.stroke();
    }
  }
}

function render(){
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const bg = ctx.createRadialGradient(canvas.width / 2, canvas.height / 2, 0, canvas.width / 2, canvas.height / 2, canvas.width * .7);
  bg.addColorStop(0, '#0f172a'); bg.addColorStop(1, '#050810');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, canvas.width, canvas.height);
  drawFloor();
  hitTargets = [];
  [...boxes].sort((a, b) => { const da = project(a.x, a.h / 2, a.z).depth, db = project(b.x, b.h / 2, b.z).depth; return db - da; })
    .forEach(b => drawBox(b));
}

/* ══════════════════════════════════════════════════════
   MAIN SCENE COLLISION
══════════════════════════════════════════════════════ */
function resolve3D(moved){
  const GAP = 0.12;
  for(const b of boxes){
    if(b.id === moved.id) continue;
    const ox = Math.abs(moved.x - b.x) - (moved.w + b.w) / 2 - GAP;
    const oz = Math.abs(moved.z - b.z) - (moved.d + b.d) / 2 - GAP;
    if(ox < 0 && oz < 0){
      if(ox > oz) moved.x += Math.sign(moved.x - b.x) * (-ox);
      else moved.z += Math.sign(moved.z - b.z) * (-oz);
    }
  }
  moved.x = Math.max(-7, Math.min(7, moved.x)); moved.z = Math.max(-6, Math.min(6, moved.z));
}

/* ══════════════════════════════════════════════════════
   MAIN SCENE INTERACTION
══════════════════════════════════════════════════════ */
let mouseBtn = -1, downX = 0, downY = 0, lastX = 0, lastY = 0;
let dragBox = null, rotDragging = false;

function pickBox(mx, my){
  for(let i = hitTargets.length - 1; i >= 0; i--){
    const ht = hitTargets[i];
    if(pointInPoly(mx, my, ht.poly) || pointInPoly(mx, my, ht.topPoly)) return ht.box;
  }
  return null;
}

canvas.addEventListener('mousedown', e => {
  if(document.getElementById('im-ovl').classList.contains('show')) return;
  mouseBtn = e.button; downX = e.offsetX; downY = e.offsetY; lastX = e.offsetX; lastY = e.offsetY;
  const picked = pickBox(e.offsetX, e.offsetY);
  if(e.button === 0){
    if(picked && !picked._dimmed){ dragBox = picked; canvas.classList.add('grabbing'); }
    else{ rotDragging = true; canvas.classList.add('grabbing'); }
  }
  if(e.button === 2 && picked && !picked._dimmed){ e.preventDefault(); openCM(picked); }
});

canvas.addEventListener('contextmenu', e => e.preventDefault());

document.addEventListener('mousemove', e => {
  if(sDragging && document.getElementById('im-ovl').classList.contains('show')){
    sRX += (e.clientY - sLY) * 0.007; sRY += (e.clientX - sLX) * 0.007;
    sRX = Math.max(-1.2, Math.min(0.1, sRX));
    sLX = e.clientX; sLY = e.clientY;
    renderShelf(); return;
  }
  if(document.getElementById('im-ovl').classList.contains('show')) return;
  const ph = pickBox(e.offsetX, e.offsetY);
  if(ph !== hoveredBox){ hoveredBox = ph; render(); }
  if(ph && !ph._dimmed) showBoxTooltip(e.clientX, e.clientY, ph);
  else hideTT();
  if(mouseBtn === 0){
    const dmx = e.offsetX - lastX, dmy = e.offsetY - lastY;
    if(dragBox){
      const {dx, dz} = unproject_xz(dmx, dmy); dragBox.x += dx; dragBox.z += dz; resolve3D(dragBox); render();
    } else if(rotDragging){
      rotY += dmx * 0.007; rotX += dmy * 0.007; rotX = Math.max(-1.3, Math.min(0.15, rotX)); render();
    }
  }
  lastX = e.offsetX; lastY = e.offsetY;
});

document.addEventListener('mouseup', e => {
  if(sDragging){ sDragging = false; return; }
  if(e.button === 0){
    const dist = Math.hypot(e.offsetX - downX, e.offsetY - downY);
    if(dist < 5){
      const picked = pickBox(downX, downY);
      if(picked && !picked._dimmed) openItemModal(picked);
    }
    dragBox = null; rotDragging = false; mouseBtn = -1; canvas.classList.remove('grabbing');
  }
});

canvas.addEventListener('wheel', e => {
  if(document.getElementById('im-ovl').classList.contains('show')) return;
  zoom *= e.deltaY < 0 ? 1.09 : 0.92; zoom = Math.max(0.3, Math.min(4, zoom)); render(); e.preventDefault();
}, {passive:false});

/* ══════════════════════════════════════════════════════
   MAIN SCENE BOX TOOLTIP
══════════════════════════════════════════════════════ */
function showBoxTooltip(cx, cy, box){
  const ne = box.items.filter(i => !i.empty);
  const avg = ne.length ? ne.reduce((s, i) => s + i.stock / i.maxStock, 0) / ne.length : 0;
  const sc = boxAvgStockColor(box);
  const pct = Math.round(avg * 100);
  const status = ne.length === 0 ? 'ว่าง' : avg > 0.5 ? 'เพียงพอ' : avg > 0.2 ? 'ปานกลาง' : '⚠️ ต่ำ';
  const sample = ne[0] || null;

  const imgBox = document.getElementById('tt-img-box');
  if(sample && sample.image){
    imgBox.innerHTML = `<img id="tt-img" src="${sample.image}" alt="${sample.name}"/>`;
  } else {
    imgBox.innerHTML = '<span style="font-size:22px;color:#64748b">📦</span>';
  }

  document.getElementById('tt-name').textContent = box.name;
  document.getElementById('tt-bc').textContent   = `${ne.length}/${box.items.length} รายการ`;
  document.getElementById('tt-sk').textContent   = `เฉลี่ย ${pct}%`;
  document.getElementById('tt-st').textContent   = status;
  document.getElementById('tt-st').style.color   = sc;
  const bar = document.getElementById('tt-bar'); bar.style.width = pct + '%'; bar.style.background = sc;
  let tx = cx + 14, ty = cy - 8;
  if(tx + 220 > window.innerWidth)  tx = cx - 230;
  if(ty + 150 > window.innerHeight) ty = cy - 155;
  tt.style.left = tx + 'px'; tt.style.top = ty + 'px'; tt.style.display = 'block';
}

/* ══════════════════════════════════════════════════════
   VIEW PRESETS & AUTO-ROTATE
══════════════════════════════════════════════════════ */
function setView(rx, ry){ rotX = rx; rotY = ry; zoom = 1; render(); }
document.getElementById('viso').addEventListener('click', () => setView(-0.42, 0.55));
document.getElementById('vfront').addEventListener('click', () => setView(-0.08, 0));
document.getElementById('vside').addEventListener('click', () => setView(-0.12, Math.PI / 2));
document.getElementById('vtop').addEventListener('click', () => setView(-1.1, 0.3));
const arBtn = document.getElementById('btn-autorot');
arBtn.addEventListener('click', () => {
  autoRot = !autoRot; arBtn.textContent = autoRot ? '⏸ หยุด' : '▶ หมุน'; arBtn.classList.toggle('on', autoRot);
  if(autoRot) loop();
});
function loop(){ if(!autoRot){ cancelAnimationFrame(animId); return; } rotY += 0.005; render(); animId = requestAnimationFrame(loop); }

/* ══════════════════════════════════════════════════════
   PLACE BOX IN MAIN SCENE
══════════════════════════════════════════════════════ */
function placeBox(cfg){
  const id = nextId++;
  const w = 0.5 + cfg.cols * 0.17, d = 0.5 + cfg.rows * 0.17, h = 1.1;
  let bx = 0, bz = 0;
  for(let attempt = 0; attempt < 40; attempt++){
    bx = (Math.random() - 0.5) * 6; bz = (Math.random() - 0.5) * 4;
    let ok = true;
    for(const b of boxes){ if(Math.abs(bx - b.x) < (w + b.w) / 2 + 0.2 && Math.abs(bz - b.z) < (d + b.d) / 2 + 0.2){ ok = false; break; } }
    if(ok) break;
  }
  const box = {
    id, x: bx, z: bz, w, d, h, name: cfg.name, hex: cfg.hex, grad: cfg.grad,
    rows: cfg.rows, cols: cfg.cols, gap: cfg.gap, items: generateItems(cfg.rows, cfg.cols),
    _dimmed: false, _frontPoly: [], _topPoly: []
  };
  boxes.push(box);
  document.getElementById('box-count').textContent = `ช่อง: ${boxes.length}`;
  render();
  return box;
}

/* ══════════════════════════════════════════════════════
   BUILD SWATCHES & PRESETS
══════════════════════════════════════════════════════ */
const swRow = document.getElementById('sw-row');
PALETTE.forEach((p, i) => { const s = document.createElement('div'); s.className = 'sw'; s.style.background = p.grad; s.dataset.idx = i; swRow.appendChild(s); });
const preRow = document.getElementById('pre-row');
PRESETS.forEach(p => {
  const b = document.createElement('button'); b.className = 'pre-btn'; b.textContent = p.label;
  b.addEventListener('click', () => { document.getElementById('inp-r').value = p.rows; document.getElementById('inp-c').value = p.cols; document.querySelectorAll('.pre-btn').forEach(x => x.classList.remove('active')); b.classList.add('active'); renderGP(); });
  preRow.appendChild(b);
});

/* ══════════════════════════════════════════════════════
   CREATE / SETTINGS MODAL
══════════════════════════════════════════════════════ */
const cmOvl = document.getElementById('cm-ovl');
const inpR = document.getElementById('inp-r'), inpC = document.getElementById('inp-c'), inpG = document.getElementById('inp-g');
function renderGP(){
  const r = Math.max(1, +inpR.value || 1), c = Math.max(1, +inpC.value || 1), g = Math.max(0, +inpG.value || 0);
  const pv = document.getElementById('gp'); pv.innerHTML = '';
  const grid = document.createElement('div'); grid.className = 'gp-grid';
  grid.style.cssText = `grid-template-columns:repeat(${c},36px);gap:${g}px`;
  const grad = PALETTE[cmColorIdx]?.grad || PALETTE[0].grad;
  for(let i = 0; i < r * c; i++){ const cell = document.createElement('div'); cell.className = 'gp-cell'; cell.style.background = grad; cell.style.opacity = '.75'; cell.textContent = i + 1; grid.appendChild(cell); }
  pv.appendChild(grid);
}
[inpR, inpC, inpG].forEach(el => el.addEventListener('input', () => { document.querySelectorAll('.pre-btn').forEach(x => x.classList.remove('active')); renderGP(); }));
document.querySelectorAll('.t-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.t-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.t-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active'); document.getElementById(btn.dataset.tab).classList.add('active');
  });
});
document.querySelectorAll('.sw').forEach(s => {
  s.addEventListener('click', () => {
    document.querySelectorAll('.sw').forEach(x => x.classList.remove('active'));
    s.classList.add('active'); cmColorIdx = +s.dataset.idx;
    document.getElementById('inp-cc').value = PALETTE[cmColorIdx].hex; renderGP();
  });
});
function openCM(box){
  cmMode = box ? 'edit' : 'create'; activeBox = box || null;
  document.getElementById('cm-title').textContent = box ? `⚙️ ตั้งค่า — ${box.name}` : '➕ เพิ่มช่องใหม่';
  document.getElementById('cm-sub').textContent   = box ? 'แก้ไขชื่อ, สี และ Grid' : 'ตั้งชื่อ, สี และ Grid ก่อนวางลงฉาก';
  document.getElementById('btn-cm-ok').textContent= box ? '✔ บันทึก' : '✔ วางช่อง';
  document.getElementById('inp-name').value       = box ? box.name : `ช่อง ${nextId}`;
  inpR.value = box ? box.rows : 3; inpC.value = box ? box.cols : 4; inpG.value = box ? box.gap : 6;
  const pi = box ? PALETTE.findIndex(p => p.hex === box.hex) : palIdx % PALETTE.length;
  cmColorIdx = pi >= 0 ? pi : 0;
  document.querySelectorAll('.sw').forEach((s, i) => s.classList.toggle('active', i === cmColorIdx));
  document.getElementById('inp-cc').value = PALETTE[cmColorIdx].hex;
  document.querySelectorAll('.t-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.t-pane').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-tab="tg"]').classList.add('active');
  document.getElementById('tg').classList.add('active');
  renderGP(); cmOvl.classList.add('show');
}
document.getElementById('btn-cm-cancel').addEventListener('click', () => cmOvl.classList.remove('show'));
cmOvl.addEventListener('click', e => { if(e.target === cmOvl) cmOvl.classList.remove('show'); });
document.getElementById('btn-cm-ok').addEventListener('click', () => {
  const name = document.getElementById('inp-name').value.trim() || `ช่อง ${nextId}`;
  const ccHex = document.getElementById('inp-cc').value;
  const palHex = PALETTE[cmColorIdx]?.hex || '#f97316';
  const fHex = ccHex && ccHex !== palHex ? ccHex : palHex;
  const fGrad = ccHex && ccHex !== palHex ? `linear-gradient(135deg,${fHex},${fHex}bb)` : PALETTE[cmColorIdx]?.grad || PALETTE[0].grad;
  const rows = Math.max(1, +inpR.value || 1), cols = Math.max(1, +inpC.value || 1), gap = Math.max(0, +inpG.value || 0);
  cmOvl.classList.remove('show');
  if(cmMode === 'create'){ palIdx++; placeBox({name, hex:fHex, grad:fGrad, rows, cols, gap}); }
  else {
    const gridChanged = rows !== activeBox.rows || cols !== activeBox.cols;
    activeBox.name = name; activeBox.hex = fHex; activeBox.grad = fGrad;
    activeBox.rows = rows; activeBox.cols = cols; activeBox.gap = gap;
    activeBox.w = 0.5 + cols * 0.17; activeBox.d = 0.5 + rows * 0.17;
    if(gridChanged) activeBox.items = generateItems(rows, cols);
    applySearch(); render();
  }
});

/* ══════════════════════════════════════════════════════
   ██████████  3D SHELF VIEWER (CANVAS 2D ENGINE)  ██████████
══════════════════════════════════════════════════════ */
const shelfC = document.getElementById('shelf-c');
const shelfCtx = shelfC.getContext('2d');
let sRX = -0.22, sRY = 0.40, sZm = 1.0;
let sActiveBox = null, sHovItem = null;
let sHits = [];
let sDragging = false, sDownX = 0, sDownY = 0, sLX = 0, sLY = 0;

// Shelf geometry constants
const PT = 0.07;
const SW = 0.80;
const SH = 0.68;
const SD = 0.55;
const PG = 0.045;

function sizeShelfCanvas(){
  const wrap = document.getElementById('shelf-wrap');
  if(!wrap) return;
  const rect = wrap.getBoundingClientRect();
  shelfC.width  = Math.max(300, rect.width || 800);
  shelfC.height = Math.max(250, rect.height || 440);
}

function sproj(x, y, z){
  const cY = Math.cos(sRY), sY2 = Math.sin(sRY);
  let rx = x * cY + z * sY2, rz = -x * sY2 + z * cY;
  const cX = Math.cos(sRX), sX2 = Math.sin(sRX);
  let ry = y * cX - rz * sX2, rz2 = y * sX2 + rz * cX;
  const fov = 320 * sZm, dist = fov + rz2 * 85, sc = fov / Math.max(1, dist);
  const S = sActiveBox ? Math.min(
    shelfC.width  * 0.42 / ((0.5 + sActiveBox.cols * 0.80 / 2) * 1.1),
    shelfC.height * 0.50 / ((0.5 + sActiveBox.rows * 0.68 / 2) * 1.1)
  ) : 115;
  return {px: shelfC.width / 2 + rx * sc * S, py: shelfC.height / 2 - ry * sc * S, depth: rz2};
}

function drawSFace(pts3, fill, stroke, lw = 0.7){
  const ps = pts3.map(p => sproj(p[0], p[1], p[2]));
  shelfCtx.beginPath(); shelfCtx.moveTo(ps[0].px, ps[0].py);
  for(let i = 1; i < ps.length; i++) shelfCtx.lineTo(ps[i].px, ps[i].py);
  shelfCtx.closePath(); shelfCtx.fillStyle = fill; shelfCtx.fill();
  if(stroke){ shelfCtx.strokeStyle = stroke; shelfCtx.lineWidth = lw; shelfCtx.stroke(); }
  return ps.map(p => [p.px, p.py]);
}

function faceDepth(pts3){ return pts3.reduce((s, p) => s + sproj(p[0], p[1], p[2]).depth, 0) / pts3.length; }

function renderShelf(){
  if(!sActiveBox) return;
  const box = sActiveBox;
  const rows = box.rows, cols = box.cols;

  const totalW = PT + cols * (SW + PT);
  const totalH = PT + rows * (SH + PT);
  const totalD = SD + PT * 1.6;
  const OX = -totalW / 2, OY = -totalH / 2, OZ = -totalD / 2;

  // Dark rich wood tones
  const WF = 'rgba(22,10,3,.98)';
  const WT = 'rgba(40,20,6,.98)';
  const WS = 'rgba(14,6,2,.99)';

  const BF = 'rgba(32,16,5,.97)';
  const BT = 'rgba(55,28,9,.97)';
  const BS = 'rgba(18,8,3,.98)';

  const faceList = [];
  function addFace(pts, fill, stroke = 'rgba(255,255,255,.055)', lw = 0.6, meta = null){
    faceList.push({pts, fill, stroke, lw, meta, d: faceDepth(pts)});
  }
  function addBox(x0, y0, z0, x1, y1, z1, cFront, cTop, cSide, str = 'rgba(255,255,255,.05)'){
    addFace([[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]], cFront, str);
    addFace([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]], 'rgba(0,0,0,.85)', str);
    addFace([[x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1]], cTop, str);
    addFace([[x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[x0,y0,z1]], 'rgba(0,0,0,.7)', str);
    addFace([[x0,y0,z0],[x0,y1,z0],[x0,y1,z1],[x0,y0,z1]], cSide, str);
    addFace([[x1,y0,z0],[x1,y1,z0],[x1,y1,z1],[x1,y0,z1]], cSide, str);
  }

  /* ── Shelf frame ── */
  addBox(OX, OY, OZ, OX + totalW, OY + totalH, OZ + PT, WF, WT, WS);
  addBox(OX, OY, OZ, OX + PT, OY + totalH, OZ + totalD, WF, WT, WS);
  addBox(OX + totalW - PT, OY, OZ, OX + totalW, OY + totalH, OZ + totalD, WF, WT, WS);
  for(let r = 0; r <= rows; r++){
    const yB = OY + r * (SH + PT), yT = yB + PT;
    addBox(OX, yB, OZ, OX + totalW, yT, OZ + totalD, BF, BT, BS, 'rgba(255,255,255,.04)');
  }

  /* ── Products ── */
  sHits = [];
  const textQueue = [];

  box.items.forEach((item, idx) => {
    const r = Math.floor(idx / cols), c = idx % cols;
    const px0 = OX + PT + c * (SW + PT) + PG;
    const px1 = OX + PT + c * (SW + PT) + SW - PG;
    const py0 = OY + PT + r * (SH + PT) + PG;
    const py1 = OY + PT + r * (SH + PT) + SH - PG;
    const pz0 = OZ + PT + PG;
    const pz1 = OZ + totalD - PG * 1.5;

    const isHov = item === sHovItem;
    const sClr = stockColor(item);
    const bright = isHov ? 1.35 : 1.0;
    const pFront = rgba(sClr, bright, 0.95);
    const pTop   = rgba(sClr, bright * 1.2, 0.88);
    const pSide  = rgba(sClr, bright * 0.65, 0.90);
    const pStr   = isHov ? '#f97316' : 'rgba(255,255,255,.12)';
    const pLw    = isHov ? 2.5 : 0.6;

    const frontPts = [[px0,py0,pz1],[px1,py0,pz1],[px1,py1,pz1],[px0,py1,pz1]];
    const fd = faceDepth(frontPts);

    faceList.push({pts:frontPts, fill:pFront, stroke:pStr, lw:pLw, meta:{isProductFront:true, item, idx}, d:fd});

    addFace([[px0,py0,pz0],[px1,py0,pz0],[px1,py1,pz0],[px0,py1,pz0]], 'rgba(0,0,0,.75)', 'none');
    addFace([[px0,py1,pz0],[px1,py1,pz0],[px1,py1,pz1],[px0,py1,pz1]], pTop, pStr, pLw);
    addFace([[px0,py0,pz0],[px0,py1,pz0],[px0,py1,pz1],[px0,py0,pz1]], pSide, pStr, pLw);
    addFace([[px1,py0,pz0],[px1,py1,pz0],[px1,py1,pz1],[px1,py0,pz1]], pSide, pStr, pLw);
    addFace([[px0,py0,pz0],[px1,py0,pz0],[px1,py0,pz1],[px0,py0,pz1]], 'rgba(0,0,0,.5)', 'none');

    if(isHov){
      addFace([[px0,py1,pz0],[px1,py1,pz0],[px1,py1,pz1],[px0,py1,pz1]], 'rgba(249,115,22,.35)', '#f97316', 2.5);
    }
  });

  faceList.sort((a, b) => b.d - a.d);

  shelfCtx.clearRect(0, 0, shelfC.width, shelfC.height);
  const bg = shelfCtx.createRadialGradient(shelfC.width / 2, shelfC.height / 2, 0, shelfC.width / 2, shelfC.height / 2, shelfC.width * .7);
  bg.addColorStop(0, '#0d1829'); bg.addColorStop(1, '#040810');
  shelfCtx.fillStyle = bg; shelfCtx.fillRect(0, 0, shelfC.width, shelfC.height);

  const vig = shelfCtx.createRadialGradient(shelfC.width / 2, shelfC.height / 2, shelfC.width * 0.3, shelfC.width / 2, shelfC.height / 2, shelfC.width * 0.8);
  vig.addColorStop(0, 'rgba(0,0,0,0)'); vig.addColorStop(1, 'rgba(0,0,0,.55)');
  shelfCtx.fillStyle = vig; shelfCtx.fillRect(0, 0, shelfC.width, shelfC.height);

  sHits = [];
  faceList.forEach(f => {
    const poly = drawSFace(f.pts, f.fill, f.stroke, f.lw);
    if(f.meta?.isProductFront){
      sHits.push({item:f.meta.item, idx:f.meta.idx, poly});
      const item = f.meta.item;
      if(poly.length >= 4){
        const cx = (poly[0][0] + poly[1][0] + poly[2][0] + poly[3][0]) / 4;
        const cy = (poly[0][1] + poly[1][1] + poly[2][1] + poly[3][1]) / 4;
        const faceH = Math.abs(poly[2][1] - poly[0][1]);
        const faceW = Math.abs(poly[1][0] - poly[0][0]);
        if(faceW > 18 && faceH > 16){
          textQueue.push({item, cx, cy, faceH, faceW});
        }
      }
    }
  });

  // Draw Real Product Images & stock labels on product front faces
  textQueue.forEach(({item, cx, cy, faceH, faceW}) => {
    shelfCtx.save();
    if(!item.empty && item.image){
      const img = getCachedImg(item.image);
      const imgSize = Math.min(faceW * 0.58, faceH * 0.52, 34);
      if(img && img.complete && img.naturalWidth > 0 && imgSize > 10){
        const ix = cx - imgSize / 2;
        const iy = cy - faceH * 0.12 - imgSize / 2;
        const r = 4;
        shelfCtx.save();
        shelfCtx.beginPath();
        if(shelfCtx.roundRect){ shelfCtx.roundRect(ix, iy, imgSize, imgSize, r); }
        else { shelfCtx.rect(ix, iy, imgSize, imgSize); }
        shelfCtx.clip();
        shelfCtx.drawImage(img, ix, iy, imgSize, imgSize);
        shelfCtx.restore();

        shelfCtx.save();
        shelfCtx.strokeStyle = 'rgba(255,255,255,0.45)';
        shelfCtx.lineWidth = 1;
        shelfCtx.beginPath();
        if(shelfCtx.roundRect){ shelfCtx.roundRect(ix, iy, imgSize, imgSize, r); }
        else { shelfCtx.rect(ix, iy, imgSize, imgSize); }
        shelfCtx.stroke();
        shelfCtx.restore();
      }

      // Stock quantity label
      shelfCtx.font = `bold ${Math.min(10, Math.max(7, faceH * 0.17))}px Inter,sans-serif`;
      shelfCtx.fillStyle = 'rgba(255,255,255,.9)';
      shelfCtx.textAlign = 'center';
      shelfCtx.textBaseline = 'middle';
      shelfCtx.fillText(`${item.stock} ชิ้น`, cx, cy + faceH * 0.28);
    } else {
      shelfCtx.font = `${Math.min(10, faceH * 0.22)}px Inter,sans-serif`;
      shelfCtx.fillStyle = 'rgba(100,116,139,.6)';
      shelfCtx.textAlign = 'center';
      shelfCtx.textBaseline = 'middle';
      shelfCtx.fillText('ว่าง', cx, cy);
    }
    shelfCtx.restore();
  });

  // Header banner inside Shelf Canvas
  shelfCtx.save();
  shelfCtx.fillStyle = 'rgba(249,115,22,.85)';
  shelfCtx.font = 'bold 12px Inter,sans-serif';
  shelfCtx.textAlign = 'center';
  shelfCtx.fillText(`${box.name}  —  ${rows}×${cols}  (${box.items.filter(i => !i.empty).length}/${box.items.length} รายการ)`, shelfC.width / 2, 20);
  shelfCtx.restore();
}

/* ── Shelf Canvas Events ── */
shelfC.addEventListener('mousedown', e => {
  sDragging = true; sDownX = e.offsetX; sDownY = e.offsetY; sLX = e.clientX; sLY = e.clientY;
  shelfC.classList.add('grabbing'); e.stopPropagation();
});

document.addEventListener('mouseup', e => {
  if(!sDragging) return;
  sDragging = false; shelfC.classList.remove('grabbing');
}, {passive:true});

shelfC.addEventListener('click', e => {
  if(Math.hypot(e.offsetX - sDownX, e.offsetY - sDownY) > 6) return;
  for(let i = sHits.length - 1; i >= 0; i--){
    if(pointInPoly(e.offsetX, e.offsetY, sHits[i].poly)){
      openItemEdit(sActiveBox, sHits[i].idx); break;
    }
  }
});

shelfC.addEventListener('mousemove', e => {
  if(sDragging) return;
  let found = null;
  for(let i = sHits.length - 1; i >= 0; i--){
    if(pointInPoly(e.offsetX, e.offsetY, sHits[i].poly)){ found = sHits[i]; break; }
  }
  const item = found ? found.item : null;
  if(item !== sHovItem){ sHovItem = item; renderShelf(); }
  if(found && !found.item.empty){ showSlotTip(e.clientX, e.clientY, found.item); }
  else hideTT();
});

shelfC.addEventListener('mouseleave', () => { sHovItem = null; hideTT(); renderShelf(); });
shelfC.addEventListener('wheel', e => {
  sZm *= e.deltaY < 0 ? 1.1 : 0.91; sZm = Math.max(0.4, Math.min(5, sZm));
  renderShelf(); e.preventDefault(); e.stopPropagation();
}, {passive:false});

function showSlotTip(cx, cy, item){
  const imgBox = document.getElementById('tt-img-box');
  if(item.empty){
    imgBox.innerHTML = '<span style="font-size:22px;color:#64748b">📦</span>';
  } else {
    imgBox.innerHTML = `<img id="tt-img" src="${item.image}" alt="${item.name}"/>`;
  }
  document.getElementById('tt-name').textContent = item.name;
  document.getElementById('tt-bc').textContent   = item.barcode;
  document.getElementById('tt-sk').textContent   = `${item.stock} / ${item.maxStock} ชิ้น`;
  const cls = stockClass(item);
  document.getElementById('tt-st').textContent   = cls.status;
  document.getElementById('tt-st').style.color   = cls.color;
  const bar = document.getElementById('tt-bar');
  bar.style.width = Math.round(item.stock / item.maxStock * 100) + '%'; bar.style.background = cls.color;
  let tx = cx + 14, ty = cy - 8;
  if(tx + 220 > window.innerWidth)  tx = cx - 230;
  if(ty + 150 > window.innerHeight) ty = cy - 155;
  tt.style.left = tx + 'px'; tt.style.top = ty + 'px'; tt.style.display = 'block';
}

document.getElementById('s-reset').addEventListener('click', () => { sRX = -0.22; sRY = 0.40; sZm = 1; renderShelf(); });
document.getElementById('s-front').addEventListener('click', () => { sRX = -0.04; sRY = 0; sZm = 1; renderShelf(); });
document.getElementById('s-iso').addEventListener('click',   () => { sRX = -0.30; sRY = 0.55; sZm = 1; renderShelf(); });

/* ══════════════════════════════════════════════════════
   ITEM MODAL (opens 3D shelf)
══════════════════════════════════════════════════════ */
const imOvl = document.getElementById('im-ovl');
document.getElementById('btn-im-close').addEventListener('click', () => { imOvl.classList.remove('show'); hideTT(); sHovItem = null; });
imOvl.addEventListener('click', e => { if(e.target === imOvl){ imOvl.classList.remove('show'); hideTT(); sHovItem = null; } });
document.getElementById('btn-im-settings').addEventListener('click', () => { imOvl.classList.remove('show'); openCM(activeBox); });

function openItemModal(box){
  activeBox = box; sActiveBox = box;
  sHovItem = null; sHits = [];
  document.getElementById('im-title').textContent = `📦 ${box.name} — Shelf 3D  (${box.rows}×${box.cols})`;
  imOvl.classList.add('show');
  setTimeout(() => {
    sizeShelfCanvas();
    sRX = -0.22; sRY = 0.40; sZm = 1.0;
    renderShelf();
  }, 30);
}

/* ══════════════════════════════════════════════════════
   ITEM EDIT MODAL (WITH REAL IMAGE PRESETS)
══════════════════════════════════════════════════════ */
const eiOvl = document.getElementById('ei-ovl');
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
    if(!document.getElementById('ei-name').value.trim()){
      document.getElementById('ei-name').value = p.name;
    }
  });
  imgPresetGrid.appendChild(b);
});

const eiEmp = document.getElementById('ei-empty');
eiEmp.addEventListener('change', () => {
  document.getElementById('ei-fields').querySelectorAll('input').forEach(el => {
    if(el === eiEmp) return;
    el.disabled = eiEmp.checked;
    el.style.opacity = eiEmp.checked ? .4 : 1;
  });
  imgPresetGrid.style.opacity = eiEmp.checked ? .3 : 1;
  imgPresetGrid.style.pointerEvents = eiEmp.checked ? 'none' : 'auto';
});

function openItemEdit(box, idx){
  activeBox = box; editItemIdx = idx;
  const item = box.items[idx];
  document.getElementById('ei-title').textContent = `✏️ แก้ไขสินค้า — ช่อง ${idx + 1}`;
  eiEmp.checked = item.empty;
  document.getElementById('ei-name').value  = item.empty ? '' : item.name;
  document.getElementById('ei-bc').value    = item.empty ? '' : item.barcode;
  document.getElementById('ei-stock').value = item.stock;
  document.getElementById('ei-max').value   = item.maxStock;
  document.getElementById('ei-image').value = item.image || '';

  document.getElementById('ei-fields').querySelectorAll('input').forEach(el => {
    el.disabled = item.empty; el.style.opacity = item.empty ? .4 : 1;
  });
  imgPresetGrid.style.opacity = item.empty ? .3 : 1;
  imgPresetGrid.style.pointerEvents = item.empty ? 'none' : 'auto';

  document.querySelectorAll('.img-preset-btn').forEach(b => {
    const imgEl = b.querySelector('img');
    b.classList.toggle('active', imgEl && imgEl.src === item.image);
  });
  eiOvl.classList.add('show');
}

document.getElementById('btn-ei-cancel').addEventListener('click', () => eiOvl.classList.remove('show'));
eiOvl.addEventListener('click', e => { if(e.target === eiOvl) eiOvl.classList.remove('show'); });

document.getElementById('btn-ei-save').addEventListener('click', () => {
  if(!activeBox || editItemIdx === null) return;
  const item = activeBox.items[editItemIdx];
  item.empty    = eiEmp.checked;
  item.name     = document.getElementById('ei-name').value.trim() || (item.empty ? '' : 'สินค้า');
  item.barcode  = document.getElementById('ei-bc').value.trim() || item.barcode;
  item.stock    = Math.max(0, +document.getElementById('ei-stock').value || 0);
  item.maxStock = Math.max(1, +document.getElementById('ei-max').value || 1);
  item.image    = document.getElementById('ei-image').value.trim() || PRODUCTS[0].image;
  if(item.empty) item.stock = 0;

  eiOvl.classList.remove('show');
  renderShelf();
  render();
  applySearch();
});

/* ══════════════════════════════════════════════════════
   SEARCH
══════════════════════════════════════════════════════ */
const sInp = document.getElementById('search-inp');
const sClear = document.getElementById('btn-sc');
const sLabel = document.getElementById('search-label');
function norm(s){ return s.toLowerCase().replace(/\s+/g, ''); }
function boxMatches(box, q){
  if(!q) return true;
  const nq = norm(q);
  if(norm(box.name).includes(nq)) return true;
  return box.items.some(it => !it.empty && (norm(it.name).includes(nq) || it.barcode.includes(q)));
}
function applySearch(){
  const q = sInp.value.trim();
  if(!q){ clearSearch(); return; }
  let cnt = 0;
  boxes.forEach(box => { const hit = boxMatches(box, q); box._dimmed = !hit; if(hit) cnt++; });
  sClear.style.display = 'block';
  sLabel.textContent = cnt === 0 ? '⚠️ ไม่พบสินค้า' : `พบ ${cnt} ช่อง`;
  sLabel.style.color = cnt === 0 ? '#f87171' : '#34d399';
  render();
}
function clearSearch(){
  sInp.value = ''; sClear.style.display = 'none'; sLabel.textContent = '';
  boxes.forEach(b => b._dimmed = false); render();
}
sInp.addEventListener('input', applySearch);
sInp.addEventListener('keydown', e => { if(e.key === 'Enter') applySearch(); });
document.getElementById('btn-sg').addEventListener('click', applySearch);
sClear.addEventListener('click', clearSearch);

/* ══════════════════════════════════════════════════════
   TOOLBAR
══════════════════════════════════════════════════════ */
document.getElementById('btn-add').addEventListener('click', () => openCM(null));
document.getElementById('btn-clear').addEventListener('click', () => {
  boxes = []; nextId = 1; palIdx = 0;
  document.getElementById('box-count').textContent = 'ช่อง: 0'; clearSearch(); render();
});

/* ══════════════════════════════════════════════════════
   SEED
══════════════════════════════════════════════════════ */
placeBox({name:'ชั้น A-1', hex:PALETTE[0].hex, grad:PALETTE[0].grad, rows:3, cols:4, gap:6});
placeBox({name:'ชั้น B-2', hex:PALETTE[1].hex, grad:PALETTE[1].grad, rows:2, cols:3, gap:6});
placeBox({name:'ชั้น C-3', hex:PALETTE[2].hex, grad:PALETTE[2].grad, rows:4, cols:4, gap:6});
render();
</script>
</body>
</html>
"""

components.html(CANVAS_3D, height=780, scrolling=False)
