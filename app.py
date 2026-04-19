"""
FF Tools - Flask Backend (Redesigned UI)
Chạy: python app.py
"""
import os, asyncio, aiohttp, threading, time
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY", "")
INFO_API_BASE = "http://raw.thug4ff.xyz"
LIKE_API_BASE = "https://free-fire-like1.p.rapidapi.com"

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return r

_rs = {}
def rate_limit(f):
    @wraps(f)
    def dec(*a, **kw):
        ip  = request.remote_addr
        now = time.time()
        hits = [t for t in _rs.get(ip,[]) if t > now-60]
        if len(hits) >= 20: return jsonify({"error":"Quá nhiều yêu cầu. Chờ 1 phút."}),429
        hits.append(now); _rs[ip]=hits
        return f(*a,**kw)
    return dec

def run_async(coro):
    res={}
    def _t():
        lp=asyncio.new_event_loop(); asyncio.set_event_loop(lp)
        try: res["v"]=lp.run_until_complete(coro)
        except Exception as e: res["e"]=e
        finally: lp.close()
    t=threading.Thread(target=_t); t.start(); t.join(timeout=15)
    if "e" in res: raise res["e"]
    if "v" not in res: raise TimeoutError("Timeout")
    return res["v"]

async def _fetch(url, headers=None):
    to=aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=to) as s:
        async with s.get(url,headers=headers or {}) as r:
            try: data=await r.json(content_type=None)
            except: data={"raw": await r.text()}
            return r.status, data

def val_uid(u): return bool(u) and u.isdigit() and len(u)>=6

@app.route("/api/info")
@rate_limit
def api_info():
    uid=request.args.get("uid","").strip()
    if not val_uid(uid): return jsonify({"error":"UID không hợp lệ"}),400
    try:
        s,d=run_async(_fetch(f"{INFO_API_BASE}/info?uid={uid}&key=great"))
        if s==404: return jsonify({"error":"Không tìm thấy người chơi"}),404
        if s!=200: return jsonify({"error":f"Lỗi API ({s})"}),502
        return jsonify(d)
    except TimeoutError: return jsonify({"error":"API timeout"}),504
    except Exception as e: return jsonify({"error":str(e)}),500

@app.route("/api/ban")
@rate_limit
def api_ban():
    uid=request.args.get("uid","").strip()
    if not val_uid(uid): return jsonify({"error":"UID không hợp lệ"}),400
    try:
        s,d=run_async(_fetch(f"{INFO_API_BASE}/check_ban/{uid}/great"))
        if s!=200: return jsonify({"error":f"Lỗi API ({s})"}),502
        if d.get("status")!=200 or not d.get("data"): return jsonify({"error":"Không tìm thấy dữ liệu"}),404
        return jsonify(d["data"])
    except TimeoutError: return jsonify({"error":"API timeout"}),504
    except Exception as e: return jsonify({"error":str(e)}),500

@app.route("/api/like")
@rate_limit
def api_like():
    uid=request.args.get("uid","").strip()
    if not val_uid(uid): return jsonify({"error":"UID không hợp lệ"}),400
    if not RAPIDAPI_KEY: return jsonify({"error":"RAPIDAPI_KEY chưa cấu hình"}),503
    hd={"x-rapidapi-key":RAPIDAPI_KEY,"x-rapidapi-host":"free-fire-like1.p.rapidapi.com"}
    try:
        s,d=run_async(_fetch(f"{LIKE_API_BASE}/like?uid={uid}",hd))
        if s==404: return jsonify({"error":"Không tìm thấy người chơi"}),404
        if s==429: return jsonify({"error":"Đã đạt giới hạn RapidAPI"}),429
        if s!=200: return jsonify({"error":f"Lỗi API ({s})"}),502
        return jsonify(d)
    except TimeoutError: return jsonify({"error":"API timeout"}),504
    except Exception as e: return jsonify({"error":str(e)}),500

@app.route("/api/outfit")
def api_outfit():
    uid=request.args.get("uid","").strip()
    if not val_uid(uid): return jsonify({"error":"UID không hợp lệ"}),400
    return jsonify({"url":f"http://profile.thug4ff.xyz/api/profile?uid={uid}"})

@app.route("/health")
def health():
    return jsonify({"status":"ok","time":datetime.utcnow().isoformat()+"Z","rapidapi":"ok" if RAPIDAPI_KEY else "missing"})

# ─── HTML ─────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FF Tools</title>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0d0f18;--bg2:#141720;--bg3:#1c1f2e;--bg4:#222638;
  --bdr:rgba(255,255,255,0.06);--bdr2:rgba(255,255,255,0.1);
  --acc:#4f8ef7;--acc2:rgba(79,142,247,0.15);--acc3:rgba(79,142,247,0.3);
  --ok:#4ade80;--ok2:rgba(74,222,128,0.12);
  --err:#f87171;--err2:rgba(248,113,113,0.12);
  --warn:#fb923c;--warn2:rgba(251,146,60,0.12);
  --gold:#f59e0b;--gold2:rgba(245,158,11,0.12);
  --t1:#f1f5f9;--t2:#94a3b8;--t3:#475569;
  --sans:'Be Vietnam Pro',sans-serif;--mono:'Space Mono',monospace;
  --r:10px;--rl:14px;--tr:.16s ease;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--sans);background:var(--bg);color:var(--t1);min-height:100vh}
body::before{content:'';position:fixed;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 60% 40% at 50% 0%,rgba(79,142,247,0.07),transparent);z-index:0}

/* ── Header ── */
header{position:relative;z-index:2;padding:2.5rem 1rem 2rem;text-align:center;border-bottom:1px solid var(--bdr)}
.logo-row{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:.4rem}
.logo-badge{
  font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;
  background:var(--acc2);color:var(--acc);border:1px solid rgba(79,142,247,.25);
  padding:3px 10px;border-radius:100px;
}
h1{font-size:clamp(1.7rem,4.5vw,2.6rem);font-weight:700;letter-spacing:-.04em}
h1 em{color:var(--acc);font-style:normal}
.sub{margin-top:.4rem;font-size:.82rem;color:var(--t3);font-weight:400;letter-spacing:.01em}

/* ── Layout ── */
main{position:relative;z-index:1;max-width:700px;margin:0 auto;padding:1.75rem 1rem 5rem}

/* ── Tabs ── */
.tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;
  background:var(--bg2);padding:4px;border-radius:var(--rl);border:1px solid var(--bdr);margin-bottom:1.5rem}
.tab{
  font-family:var(--sans);font-size:13px;font-weight:600;padding:9px 8px;
  border:1px solid transparent;border-radius:var(--r);
  background:transparent;color:var(--t3);cursor:pointer;
  transition:all var(--tr);display:flex;align-items:center;justify-content:center;gap:6px;
}
.tab svg{width:14px;height:14px;flex-shrink:0;opacity:.4;transition:opacity var(--tr)}
.tab:hover{color:var(--t1);background:var(--bg4)}
.tab.on{background:var(--bg3);color:var(--t1);border-color:var(--bdr2)}
.tab.on svg{opacity:1}

/* ── Panels ── */
.pnl{display:none}
.pnl.on{display:block;animation:fu .2s ease both}
@keyframes fu{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

.ph h2{font-size:1rem;font-weight:700;letter-spacing:-.02em}
.ph p{font-size:.8rem;color:var(--t3);margin-top:3px}
.ph{margin-bottom:1.2rem}

/* ── Form ── */
.fg{margin-bottom:.9rem}
.fg label{display:block;font-size:11px;font-weight:700;color:var(--t2);
  margin-bottom:6px;letter-spacing:.08em;text-transform:uppercase}
.iw{position:relative}
.iw svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);
  color:var(--t3);pointer-events:none;width:14px;height:14px}
input[type=text]{
  width:100%;padding:11px 14px 11px 37px;
  font-family:var(--mono);font-size:13px;letter-spacing:.04em;
  background:var(--bg2);border:1px solid var(--bdr);border-radius:var(--r);
  color:var(--t1);outline:none;transition:border-color var(--tr),box-shadow var(--tr);
}
input:focus{border-color:rgba(79,142,247,.5);box-shadow:0 0 0 3px var(--acc3)}
input::placeholder{color:var(--t3)}

/* ── Buttons ── */
.btn{
  width:100%;display:inline-flex;align-items:center;justify-content:center;gap:8px;
  padding:11px 20px;font-family:var(--sans);font-size:13.5px;font-weight:700;
  border:none;border-radius:var(--r);cursor:pointer;transition:all var(--tr);letter-spacing:.01em;
}
.btn:hover{filter:brightness(1.1)}.btn:active{transform:scale(.985)}
.btn:disabled{opacity:.45;cursor:not-allowed}.btn:disabled:active{transform:none}
.btn-a{background:var(--acc);color:#080c18}
.btn-b{background:var(--err);color:#080c18}
.btn-c{background:var(--ok);color:#080c18}
.sp{width:13px;height:13px;border:2px solid rgba(8,12,24,.3);border-top-color:#080c18;
  border-radius:50%;animation:spin .5s linear infinite;display:none;flex-shrink:0}
.loading .sp{display:block}.loading .bl{display:none}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── Error inline ── */
.ie{margin-top:1rem;padding:11px 14px;background:var(--err2);
  border:1px solid rgba(248,113,113,.2);border-radius:var(--r);
  font-size:13px;color:var(--err);display:flex;gap:8px;align-items:flex-start;animation:fu .18s ease both}
.ie svg{flex-shrink:0;width:14px;height:14px;margin-top:1px}

/* ═══════════════════════════════════════════════
   PLAYER CARD — FF split card style
═══════════════════════════════════════════════ */
.card{margin-top:1.1rem;border-radius:var(--rl);border:1px solid var(--bdr2);
  background:var(--bg2);overflow:hidden;animation:fu .22s ease both}

/* ── hero: split left/right ── */
.hero{
  position:relative;display:flex;align-items:stretch;
  border-bottom:1px solid var(--bdr);min-height:130px;
}

/* LEFT panel — dark game card */
.hero-left{
  position:relative;flex-shrink:0;width:38%;
  background:#070a14;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:16px 10px 20px;gap:6px;overflow:hidden;
  border-right:1px solid var(--bdr2);
}
/* grid texture overlay */
.hero-left::before{
  content:'';position:absolute;inset:0;pointer-events:none;
  background-image:
    linear-gradient(rgba(79,142,247,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(79,142,247,.04) 1px,transparent 1px);
  background-size:20px 20px;
}
/* top accent line */
.hero-left::after{
  content:'';position:absolute;top:0;left:10%;right:10%;height:1.5px;
  background:linear-gradient(90deg,transparent,rgba(79,142,247,.5),transparent);
}
/* neon border glow left edge */
.hero-left-glow{
  position:absolute;left:0;top:10%;bottom:10%;width:2px;
  background:linear-gradient(180deg,transparent,#4ade80,transparent);border-radius:2px;
}
/* green dot bottom center */
.hero-dot{
  position:absolute;bottom:10px;left:50%;transform:translateX(-50%);
  width:9px;height:9px;border-radius:50%;background:#4ade80;flex-shrink:0;
  box-shadow:0 0 0 3px rgba(74,222,128,.15),0 0 10px rgba(74,222,128,.3);
}
/* avatar box */
.avatar{
  width:62px;height:62px;border-radius:10px;flex-shrink:0;
  background:#0a0d1c;border:1.5px solid rgba(79,142,247,.3);
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;position:relative;z-index:1;
}
.avatar img{width:100%;height:100%;object-fit:cover;border-radius:8px}
.av-placeholder{width:100%;height:100%;display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,#0d1428,#111932)}
.hero-left-name{
  font-size:.78rem;font-weight:700;color:var(--t1);text-align:center;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  max-width:100%;position:relative;z-index:1;letter-spacing:.01em;
}
.hero-left-uid{
  font-family:var(--mono);font-size:.65rem;color:var(--t3);
  position:relative;z-index:1;
}

/* RIGHT panel — detail info */
.hero-right{
  flex:1;min-width:0;padding:14px 14px 14px 14px;
  display:flex;flex-direction:column;justify-content:center;gap:6px;
  background:linear-gradient(135deg,#0e1220 0%,#121828 100%);
  position:relative;overflow:hidden;
}
.hero-right::before{
  content:'';position:absolute;right:-30px;top:-30px;
  width:120px;height:120px;border-radius:50%;
  background:radial-gradient(circle,rgba(79,142,247,.06),transparent 70%);
  pointer-events:none;
}
.hr-name{
  font-size:clamp(.88rem,2.8vw,1rem);font-weight:700;letter-spacing:-.01em;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--t1);
}
.hr-badges{display:flex;align-items:center;gap:5px;flex-wrap:wrap}
.hr-uid{font-family:var(--mono);font-size:.7rem;color:var(--t3);margin-top:1px}
.hr-sig{font-size:.72rem;color:var(--t2);display:flex;align-items:center;gap:5px}
.hr-sig svg{width:11px;height:11px;flex-shrink:0;color:var(--t3)}
.hr-meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.hr-meta-item{display:flex;align-items:center;gap:4px;font-size:.69rem;color:var(--t3)}
.hr-meta-item svg{width:10px;height:10px;flex-shrink:0}
.hr-meta-sep{color:var(--bdr3);font-size:.65rem}

.level-tag{
  font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  background:rgba(139,92,246,.2);color:#a78bfa;border:1px solid rgba(139,92,246,.3);
  padding:2px 8px;border-radius:5px;
}
.pill{
  display:inline-flex;align-items:center;gap:4px;
  padding:2px 9px;border-radius:5px;font-size:10.5px;font-weight:600;letter-spacing:.03em;
  border:1px solid var(--bdr2);background:var(--bg3);color:var(--t2);
}
.pill.online{background:var(--ok2);color:var(--ok);border-color:rgba(74,222,128,.2)}
.pill svg{width:10px;height:10px}
.dot{width:5px;height:5px;border-radius:50%;background:var(--ok);flex-shrink:0}

/* outfit image */
.outfit-wrap{
  background:linear-gradient(180deg,#05080f 0%,#0a0e1a 100%);
  min-height:100px;display:flex;align-items:center;justify-content:center;
  border-top:1px solid var(--bdr);position:relative;overflow:hidden;
}
.outfit-wrap::before{
  content:'';position:absolute;inset:0;pointer-events:none;
  background-image:
    linear-gradient(rgba(79,142,247,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(79,142,247,.025) 1px,transparent 1px);
  background-size:24px 24px;
}
.outfit-wrap img{width:100%;display:block;max-height:300px;object-fit:contain;position:relative;z-index:1}
.outfit-loading{font-size:11px;color:var(--t3);padding:24px;text-align:center}

/* ── Sections ── */
.sec-head{
  padding:8px 16px 5px;font-size:10px;font-weight:800;letter-spacing:.12em;
  text-transform:uppercase;color:var(--t3);background:var(--bg3);
  border-top:1px solid var(--bdr);display:flex;align-items:center;gap:7px;
}
.sec-head svg{width:12px;height:12px;opacity:.6}

/* rows */
.rows{}
.row{
  display:flex;justify-content:space-between;align-items:center;
  padding:9px 16px;font-size:13px;border-bottom:1px solid var(--bdr);
}
.row:last-child{border-bottom:none}
.rk{font-size:11.5px;color:var(--t3);font-weight:500;letter-spacing:.02em;text-transform:uppercase;flex-shrink:0}
.rv{font-family:var(--mono);font-size:12px;color:var(--t1);text-align:right;max-width:64%;word-break:break-all}
.rv code{
  font-family:var(--mono);font-size:11.5px;
  background:var(--acc2);color:var(--acc);
  padding:1px 7px;border-radius:5px;border:1px solid rgba(79,142,247,.2);
}

/* rank badge */
.rank-badge{
  display:inline-flex;align-items:center;gap:5px;
  padding:2px 9px;border-radius:5px;font-size:11px;font-weight:700;
  letter-spacing:.02em;font-family:var(--sans);
}
.rank-stars{display:inline-flex;gap:1px;align-items:center;line-height:1}
.rank-bronze  {background:rgba(180,115,80,.18);color:#cd7f32;border:1px solid rgba(180,115,80,.35)}
.rank-silver  {background:rgba(180,180,180,.1); color:#b0b8c8;border:1px solid rgba(180,180,180,.25)}
.rank-gold    {background:var(--gold2);          color:var(--gold);border:1px solid rgba(245,158,11,.3)}
.rank-platinum{background:rgba(96,165,250,.1);   color:#60a5fa;border:1px solid rgba(96,165,250,.25)}
.rank-diamond {background:rgba(147,51,234,.12);  color:#c084fc;border:1px solid rgba(147,51,234,.28)}
.rank-heroic  {background:rgba(239,68,68,.12);   color:#f87171;border:1px solid rgba(239,68,68,.28)}
.rank-master  {background:rgba(251,146,60,.12);  color:#fb923c;border:1px solid rgba(251,146,60,.28)}
.rank-grand   {background:rgba(250,204,21,.12);  color:#facc15;border:1px solid rgba(250,204,21,.3)}
.rank-none    {background:var(--bg4);            color:var(--t3);border:1px solid var(--bdr)}

/* stat grid */
.stat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--bdr);border-top:1px solid var(--bdr)}
.sc{background:var(--bg2);padding:11px 15px}
.sc-l{font-size:10px;color:var(--t3);font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:2px}
.sc-v{font-family:var(--mono);font-size:16px;font-weight:700;color:var(--t1)}

/* ban result */
.ban-card{margin-top:1.1rem;border-radius:var(--rl);overflow:hidden;animation:fu .2s ease both;border:1px solid}
.ban-ok {border-color:rgba(74,222,128,.2);background:var(--bg2)}
.ban-err{border-color:rgba(248,113,113,.25);background:var(--bg2)}
.ban-h{padding:14px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--bdr)}
.ban-h svg{width:20px;height:20px;flex-shrink:0}
.ban-h.ok {background:var(--ok2);color:var(--ok)}
.ban-h.err{background:var(--err2);color:var(--err)}
.ban-title{font-size:14px;font-weight:700}
.ban-sub{font-size:11.5px;opacity:.7;margin-top:2px}

/* like result */
.like-card{margin-top:1.1rem;border-radius:var(--rl);overflow:hidden;border:1px solid var(--bdr2);animation:fu .2s ease both;background:var(--bg2)}
.like-h{padding:14px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--bdr)}
.like-h.ok {background:var(--ok2);color:var(--ok)}
.like-h.wrn{background:var(--warn2);color:var(--warn)}
.like-h svg{width:18px;height:18px;flex-shrink:0}
.like-numbers{display:grid;grid-template-columns:repeat(3,1fr);text-align:center;padding:14px 0;border-bottom:1px solid var(--bdr)}
.ln-cell{padding:4px 0}
.ln-num{font-family:var(--mono);font-size:20px;font-weight:700}
.ln-num.plus{color:var(--ok)}
.ln-lbl{font-size:10px;color:var(--t3);font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-top:2px}
.ln-sep{width:1px;background:var(--bdr)}

/* footer */
footer{position:relative;z-index:1;text-align:center;padding:1.2rem 1rem 2rem;font-size:11.5px;color:var(--t3);border-top:1px solid var(--bdr)}
footer a{color:var(--acc);text-decoration:none}

@media(max-width:440px){
  .tab span:not(.sp,.bl){display:none}
  .tab svg{opacity:.7}.tab.on svg{opacity:1}
}
</style>
</head>
<body>
<header>
  <div class="logo-row"><span class="logo-badge">Free Fire Utilities</span></div>
  <h1>FF <em>Tools</em></h1>
  <p class="sub">Tra cứu · Kiểm tra ban · Tăng likes</p>
</header>

<main>
  <div class="tabs">
    <button class="tab on" onclick="sw('info')">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M6 20v-1a6 6 0 0112 0v1"/></svg>
      <span>Player Info</span>
    </button>
    <button class="tab" onclick="sw('ban')">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
      <span>Check Ban</span>
    </button>
    <button class="tab" onclick="sw('like')">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
      <span>Send Likes</span>
    </button>
  </div>

  <!-- INFO -->
  <div id="p-info" class="pnl on">
    <div class="ph"><h2>Thông tin người chơi</h2><p>Nhập UID để xem chi tiết tài khoản Free Fire</p></div>
    <div class="fg">
      <label>Player UID</label>
      <div class="iw">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        <input type="text" id="uid-info" placeholder="Nhập UID (vd: 297885124)" maxlength="20" inputmode="numeric">
      </div>
    </div>
    <button class="btn btn-a" id="btn-info" onclick="doInfo()"><div class="sp"></div><span class="bl">Tra cứu ngay</span></button>
    <div id="out-info"></div>
  </div>

  <!-- BAN -->
  <div id="p-ban" class="pnl">
    <div class="ph"><h2>Kiểm tra trạng thái ban</h2><p>Xác minh tài khoản có bị Garena cấm không</p></div>
    <div class="fg">
      <label>Player UID</label>
      <div class="iw">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
        <input type="text" id="uid-ban" placeholder="Nhập UID (vd: 297885124)" maxlength="20" inputmode="numeric">
      </div>
    </div>
    <button class="btn btn-b" id="btn-ban" onclick="doBan()"><div class="sp"></div><span class="bl">Kiểm tra ngay</span></button>
    <div id="out-ban"></div>
  </div>

  <!-- LIKE -->
  <div id="p-like" class="pnl">
    <div class="ph"><h2>Tăng lượt thích</h2><p>Gửi likes đến tài khoản Free Fire qua RapidAPI</p></div>
    <div class="fg">
      <label>Player UID</label>
      <div class="iw">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
        <input type="text" id="uid-like" placeholder="Nhập UID (vd: 297885124)" maxlength="20" inputmode="numeric">
      </div>
    </div>
    <button class="btn btn-c" id="btn-like" onclick="doLike()"><div class="sp"></div><span class="bl">Gửi likes</span></button>
    <div id="out-like"></div>
  </div>
</main>

<footer>Flask + Python &nbsp;·&nbsp; <a href="/health" target="_blank">API Status</a> &nbsp;·&nbsp; by THUG</footer>

<script>
// ── TABS ─────────────────────────────────────────────────────────────────────
const TS=['info','ban','like'];
function sw(n){
  TS.forEach((t,i)=>{
    document.querySelectorAll('.tab')[i].classList.toggle('on',t===n);
    document.getElementById('p-'+t).classList.toggle('on',t===n);
  });
}

// ── HELPERS ───────────────────────────────────────────────────────────────────
const $=id=>document.getElementById(id);
function busy(id,on){const b=$(id);b.classList.toggle('loading',on);b.disabled=on}
function ok_uid(v){return v&&/^\d{6,}$/.test(v)}
function ts(t){return t?new Date(t*1000).toLocaleString('vi-VN'):'—'}
function fmt(n){return n!=null&&n!==''?Number(n).toLocaleString('vi-VN'):'—'}

function errHtml(msg){
  return`<div class="ie"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/></svg><span>${msg}</span></div>`;
}

function row(k,v){return`<div class="row"><span class="rk">${k}</span><span class="rv">${v}</span></div>`}
function code(v){return`<code>${v}</code>`}
function secHead(icon,title){
  return`<div class="sec-head">${icon}<span>${title}</span></div>`;
}

// ── RANK MAPPING ──────────────────────────────────────────────────────────────
// BR rank: sub-ranks dùng số La Mã (I, II, III, IV)
// CS rank: sub-ranks dùng số sao (1★ 2★ 3★ 4★)
const BR_TIERS = [
  {cls:'rank-bronze',   vi:'Đồng',       color:'#CD7F32', subs:['I','II','III'],      pts:[0,100,200]},
  {cls:'rank-silver',   vi:'Bạc',        color:'#A8B8C8', subs:['I','II','III'],      pts:[300,400,500]},
  {cls:'rank-gold',     vi:'Vàng',       color:'#E8A000', subs:['I','II','III','IV'], pts:[600,800,1000,1200]},
  {cls:'rank-platinum', vi:'Bạch Kim',   color:'#60A5FA', subs:['I','II','III','IV'], pts:[1400,1700,2000,2300]},
  {cls:'rank-diamond',  vi:'Kim Cương',  color:'#C084FC', subs:['I','II','III','IV'], pts:[2600,3000,3400,3800]},
  {cls:'rank-heroic',   vi:'Anh Hùng',  color:'#F87171', subs:[],                    pts:[4200]},
  {cls:'rank-master',   vi:'Cao Thủ',   color:'#FB923C', subs:[],                    pts:[5000]},
  {cls:'rank-grand',    vi:'Thách Đấu', color:'#FACC15', subs:[],                    pts:[6000]},
];
const CS_TIERS = [
  {cls:'rank-bronze',   vi:'Đồng',       color:'#CD7F32', stars:3, pts:[0,50,100]},
  {cls:'rank-silver',   vi:'Bạc',        color:'#A8B8C8', stars:3, pts:[150,200,250]},
  {cls:'rank-gold',     vi:'Vàng',       color:'#E8A000', stars:4, pts:[300,400,500,600]},
  {cls:'rank-platinum', vi:'Bạch Kim',   color:'#60A5FA', stars:4, pts:[700,850,1000,1150]},
  {cls:'rank-diamond',  vi:'Kim Cương',  color:'#C084FC', stars:4, pts:[1300,1500,1700,1900]},
  {cls:'rank-heroic',   vi:'Anh Hùng',  color:'#F87171', stars:0, pts:[2100]},
  {cls:'rank-master',   vi:'Cao Thủ',   color:'#FB923C', stars:0, pts:[2500]},
  {cls:'rank-grand',    vi:'Thách Đấu', color:'#FACC15', stars:0, pts:[3000]},
];

function getBRRank(pts){
  pts=parseInt(pts)||0;
  let tier=BR_TIERS[0],sub=0;
  for(const t of BR_TIERS){if(pts>=t.pts[0]){tier=t;sub=0;for(let i=0;i<t.pts.length;i++){if(pts>=t.pts[i])sub=i;}}}
  return{tier,sub};
}
function getCSRank(pts){
  pts=parseInt(pts)||0;
  let tier=CS_TIERS[0],sub=0;
  for(const t of CS_TIERS){if(pts>=t.pts[0]){tier=t;sub=0;for(let i=0;i<t.pts.length;i++){if(pts>=t.pts[i])sub=i;}}}
  return{tier,sub};
}

// BR badge: "Đồng I" / "Vàng III" / "Anh Hùng"
function rankBadge(pts, mode){
  if(mode==='cs') return csBadge(pts);
  return brBadge(pts);
}
function brBadge(pts){
  if(pts==null||pts==='') return`<span class="rank-badge rank-none">Chưa xếp hạng</span>`;
  const{tier,sub}=getBRRank(pts);
  const label=tier.subs.length>0?`${tier.vi} ${tier.subs[sub]||tier.subs[0]}`:tier.vi;
  return`<span class="rank-badge ${tier.cls}">${label}</span>`;
}

// CS badge: "Đồng" + filled/empty stars matching sub-rank count
function csBadge(pts){
  if(pts==null||pts==='') return`<span class="rank-badge rank-none">Chưa xếp hạng</span>`;
  const{tier,sub}=getCSRank(pts);
  let stars='';
  if(tier.stars>0){
    const filled=sub+1; // sub is 0-based index, so +1 = number of filled stars
    stars='<span class="rank-stars">'+
      Array.from({length:tier.stars},(_,i)=>
        `<svg width="13" height="13" viewBox="0 0 24 24" style="flex-shrink:0;fill:${i<filled?tier.color:'rgba(255,255,255,.15)'}"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`
      ).join('')+'</span>';
  }
  return`<span class="rank-badge ${tier.cls}">${tier.vi}${stars?' '+stars:''}</span>`;
}

const IC = {
  user:`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M6 20v-1a6 6 0 0112 0v1"/></svg>`,
  shield:`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  sword:`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14.5 17.5L3 6V3h3l11.5 11.5"/><path d="M13 19l6-6"/><path d="M2 2l20 20"/></svg>`,
  star:`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
  pet:`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="4" r="2"/><circle cx="18" cy="8" r="2"/><circle cx="20" cy="16" r="2"/><path d="M9 10a5 5 0 0 0 5 5 5 5 0 0 0 5-5 5 5 0 0 0-5-5 5 5 0 0 0-5 5"/><path d="M6 17v3"/><path d="M6 14c.5 2 1.5 3 3 3s3-1 4-3"/></svg>`,
  guild:`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  king:`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M2 20h20M5 20V8l7-6 7 6v12"/><path d="M9 20v-6h6v6"/></svg>`,
  outfit:`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20.38 3.46L16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.57a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.57a2 2 0 0 0-1.34-2.23z"/></svg>`,
};

// ── INFO ──────────────────────────────────────────────────────────────────────
async function doInfo(){
  const uid=$('uid-info').value.trim();
  const out=$('out-info');
  if(!ok_uid(uid)){out.innerHTML=errHtml('UID không hợp lệ — chỉ số, ít nhất 6 ký tự.');return}
  out.innerHTML='';busy('btn-info',true);
  try{
    const r=await fetch(`/api/info?uid=${uid}`);
    const d=await r.json();
    if(!r.ok){out.innerHTML=errHtml(d.error||'Lỗi không xác định.');return}

    const b=d.basicInfo||{}, cl=d.clanBasicInfo||{}, ca=d.captainBasicInfo||{},
          pt=d.petInfo||{},   cr=d.creditScoreInfo||{}, so=d.socialInfo||{};

    // Avatar: load real game icon from headPic ID
    const nick=b.nickname||uid;
    const headPicId=b.headPic||b.avatar||b.avatarId||null;
    const avatarId=headPicId;

    // region pill
    const region=b.region||'';

    let h=`<div class="card">
      <div class="hero">
        <!-- LEFT: game card panel -->
        <div class="hero-left">
          <div class="hero-left-glow"></div>
          <div class="avatar" id="av-${uid}">
            <div class="av-placeholder">
              <svg viewBox="0 0 40 40" fill="none" style="width:34px;height:34px;opacity:.5">
                <circle cx="20" cy="14" r="7" fill="#4f8ef7"/>
                <path d="M6 36c0-7.7 6.3-14 14-14s14 6.3 14 14" stroke="#4f8ef7" stroke-width="2.5" stroke-linecap="round"/>
              </svg>
            </div>
          </div>
          <div class="hero-left-name">${nick}</div>
          <div class="hero-left-uid">UID: ${uid}</div>
          <div class="hero-dot"></div>
        </div>
        <!-- RIGHT: detail info panel -->
        <div class="hero-right">
          <div class="hr-name">${nick}</div>
          <div class="hr-badges">
            ${brBadge(b.rankingPoints)}
            <span class="level-tag">LV.${b.level||'?'}</span>
          </div>
          <div class="hr-uid">UID: ${uid}</div>
          ${so.signature?`<div class="hr-sig"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>${so.signature}</div>`:''}
          <div class="hr-meta">
            ${region?`<span class="hr-meta-item"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>Khu vực: ${region}</span>`:''}
            ${region&&cl.clanName?`<span class="hr-meta-sep">|</span>`:''}
            <span class="hr-meta-item"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg># Guild: ${cl.clanName||'—'}</span>
          </div>
        </div>
      </div>

      <!-- outfit image below hero -->
      <div class="outfit-wrap" id="outfit-${uid}">
        <div class="outfit-loading">Đang tải trang phục...</div>
      </div>

      <div class="stat-grid">
        <div class="sc"><div class="sc-l">Exp</div><div class="sc-v">${fmt(b.exp)}</div></div>
        <div class="sc"><div class="sc-l">Honor Score</div><div class="sc-v">${cr.creditScore||'—'}</div></div>
      </div>

      ${secHead(IC.user,'Thông tin tài khoản')}
      <div class="rows">
        ${row('UID',code(uid))}
        ${row('Tiểu sử',so.signature||'<span style="color:var(--t3);font-family:var(--sans)">Không có</span>')}
        ${row('OB Version',b.releaseVersion||'—')}
        ${row('BP Badges',fmt(b.badgeCnt))}
        ${row('Tạo acc',ts(b.createAt))}
        ${row('Đăng nhập lần cuối',ts(b.lastLoginAt))}
      </div>

      ${secHead(IC.shield,'Sinh tồn — Xếp hạng')}
      <div class="rows">
        ${row('Hạng hiện tại',brBadge(b.rankingPoints))}
        ${row('Điểm BR',fmt(b.rankingPoints))}
      </div>

      ${secHead(IC.sword,'Tử chiến — Xếp hạng')}
      <div class="rows">
        ${row('Hạng hiện tại',csBadge(b.csRankingPoints))}
      </div>`;

    if(cl.clanName){
      h+=`${secHead(IC.guild,'Quân đoàn')}
      <div class="rows">
        ${row('Tên quân đoàn',cl.clanName)}
        ${row('ID',code(cl.clanId||'—'))}
        ${row('Cấp độ',cl.clanLevel||'—')}
        ${row('Thành viên',`${cl.memberNum||'?'}/${cl.capacity||'?'}`)}
      </div>`;

      if(ca.nickname){
        h+=`${secHead(IC.king,'Chủ quân đoàn')}
        <div class="rows">
          ${row('Nickname',ca.nickname)}
          ${row('UID',code(ca.accountId||'—'))}
          ${row('Cấp độ',`Lv. ${ca.level||'?'}`)}
          ${row('Sinh tồn',brBadge(ca.rankingPoints))}
          ${row('Tử chiến',csBadge(ca.csRankingPoints))}
          ${row('Đăng nhập cuối',ts(ca.lastLoginAt))}
        </div>`;
      }
    }

    if(pt.name){
      h+=`${secHead(IC.pet,'Pet')}
      <div class="rows">
        ${row('Tên pet',pt.name)}
        ${row('Cấp độ',`Lv. ${pt.level||'?'}`)}
        ${row('Exp',fmt(pt.exp))}
      </div>`;
    }

    h+=`</div>`;
    out.innerHTML=h;

    // Load images async
    loadAvatar(uid, avatarId);
    loadOutfit(uid);

  }catch(e){out.innerHTML=errHtml('Không kết nối được máy chủ.')}
  finally{busy('btn-info',false)}
}

// Try multiple CDN URLs for the game avatar icon
async function loadAvatar(uid, picId){
  const el=document.getElementById('av-'+uid);
  if(!el) return;
  if(!picId){return;} // keep placeholder

  // Free Fire CDN URL candidates for headPic
  const candidates=[
    `https://dl.dir.freefiremobile.com/common/web_event/official2.0/images/${picId}.png`,
    `https://dl.dir.freefiremobile.com/common/web_event/official2.0/images/${picId}.jpg`,
    `https://cdn.ff.garena.com/assets/item/icon/${picId}.png`,
    `https://www.assets.garena.com/free-fire/icon/${picId}.png`,
  ];

  for(const url of candidates){
    try{
      const ok=await new Promise(res=>{
        const img=new Image();
        img.onload=()=>res(true);
        img.onerror=()=>res(false);
        img.src=url;
      });
      if(ok){
        el.innerHTML='';
        const img=document.createElement('img');
        img.src=url;
        img.alt='avatar';
        img.style.cssText='width:100%;height:100%;object-fit:cover;border-radius:8px';
        el.appendChild(img);
        return;
      }
    }catch{}
  }
  // All failed — keep SVG placeholder, do nothing
}

async function loadOutfit(uid){
  const wrap=document.getElementById(`outfit-${uid}`);
  if(!wrap)return;
  try{
    const url=`http://profile.thug4ff.xyz/api/profile?uid=${uid}`;
    const img=new Image();
    img.onload=()=>{wrap.innerHTML='';wrap.appendChild(img)};
    img.onerror=()=>{wrap.style.display='none'};
    img.src=url;
    img.style.cssText='width:100%;display:block;max-height:320px;object-fit:contain';
  }catch{wrap.style.display='none'}
}

// ── BAN ───────────────────────────────────────────────────────────────────────
async function doBan(){
  const uid=$('uid-ban').value.trim();
  const out=$('out-ban');
  if(!ok_uid(uid)){out.innerHTML=errHtml('UID không hợp lệ — chỉ số, ít nhất 6 ký tự.');return}
  out.innerHTML='';busy('btn-ban',true);
  try{
    const r=await fetch(`/api/ban?uid=${uid}`);
    const d=await r.json();
    if(!r.ok){out.innerHTML=errHtml(d.error||'Lỗi không xác định.');return}
    const banned=d.is_banned==1;
    const okIcon=`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
    const banIcon=`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>`;
    let h=`<div class="ban-card ${banned?'ban-err':'ban-ok'}">
      <div class="ban-h ${banned?'err':'ok'}">
        ${banned?banIcon:okIcon}
        <div>
          <div class="ban-title">${banned?'Tài khoản bị cấm':'Tài khoản hợp lệ'}</div>
          <div class="ban-sub">${d.nickname||uid} · UID ${uid}</div>
        </div>
      </div>
      <div class="rows">
        ${row('Nickname',d.nickname||'—')}
        ${row('UID',code(uid))}
        ${row('Khu vực',d.region||'—')}
        ${row('Trạng thái',banned
          ?`<span style="color:var(--err);font-weight:700">⛔ Đã bị cấm</span>`
          :`<span style="color:var(--ok);font-weight:700">✓ Bình thường</span>`)}
        ${banned&&d.period?row('Thời hạn',`${d.period} ngày`):''}
      </div>
    </div>`;
    out.innerHTML=h;
  }catch{out.innerHTML=errHtml('Không kết nối được máy chủ.')}
  finally{busy('btn-ban',false)}
}

// ── LIKE ──────────────────────────────────────────────────────────────────────
async function doLike(){
  const uid=$('uid-like').value.trim();
  const out=$('out-like');
  if(!ok_uid(uid)){out.innerHTML=errHtml('UID không hợp lệ — chỉ số, ít nhất 6 ký tự.');return}
  out.innerHTML='';busy('btn-like',true);
  try{
    const r=await fetch(`/api/like?uid=${uid}`);
    const d=await r.json();
    if(!r.ok){out.innerHTML=errHtml(d.error||'Lỗi không xác định.');return}
    const ok=d.status===1;
    const hrtIc=`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>`;
    const wrnIc=`<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
    let h=`<div class="like-card">
      <div class="like-h ${ok?'ok':'wrn'}">${ok?hrtIc:wrnIc}
        <div style="font-size:13.5px;font-weight:700">${ok?'Gửi likes thành công':'Đã đạt giới hạn hôm nay'}</div>
      </div>`;
    if(ok){
      const before=parseInt(d.likes_before)||0;
      const added=parseInt(d.likes_added)||0;
      const after=parseInt(d.likes_after)||0;
      h+=`<div class="like-numbers">
        <div class="ln-cell"><div class="ln-num">${fmt(before)}</div><div class="ln-lbl">Trước</div></div>
        <div class="ln-sep"></div>
        <div class="ln-cell"><div class="ln-num plus">+${fmt(added)}</div><div class="ln-lbl">Đã thêm</div></div>
        <div class="ln-sep"></div>
        <div class="ln-cell"><div class="ln-num">${fmt(after)}</div><div class="ln-lbl">Sau</div></div>
      </div>
      <div class="rows">
        ${row('Nickname',d.player||'—')}
        ${row('UID',code(uid))}
      </div>`;
    }else{
      h+=`<div style="padding:14px 16px;font-size:13px;color:var(--t2)">UID này đã nhận đủ lượt thích tối đa trong ngày hôm nay.</div>`;
    }
    h+=`</div>`;
    out.innerHTML=h;
  }catch{out.innerHTML=errHtml('Không kết nối được máy chủ.')}
  finally{busy('btn-like',false)}
}

// ── Enter + digit-only ────────────────────────────────────────────────────────
[['uid-info',doInfo],['uid-ban',doBan],['uid-like',doLike]].forEach(([id,fn])=>{
  $(id).addEventListener('keydown',e=>{if(e.key==='Enter')fn()});
  $(id).addEventListener('input',function(){this.value=this.value.replace(/\D/g,'')});
});
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    debug=os.environ.get("FLASK_DEBUG","false").lower()=="true"
    print(f"\n✅  FF Tools → http://127.0.0.1:{port}")
    print(f"🔑  RAPIDAPI_KEY: {'✓ OK' if RAPIDAPI_KEY else '✗ chưa cấu hình (Like sẽ không hoạt động)'}\n")
    app.run(host="0.0.0.0",port=port,debug=debug)
