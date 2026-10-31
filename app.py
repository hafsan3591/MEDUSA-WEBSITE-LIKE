from flask import Flask, request, jsonify, session, redirect
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import aiohttp
import requests
import json
import os
import like_pb2
import uid_generator_pb2
import visit_count_pb2
from google.protobuf.message import DecodeError
from collections import OrderedDict

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "medusa-hacker-terminal-secret-2024-x9k")

# 🔐 Access Passwords
ACCESS_PASSWORD = "HK-385-HK"
ADMIN_PASSWORD  = "HK-385-HK"

VALID_API_KEYS = {"hkysxbhyws"}
ALLOWED_REGION = "BD"
BD_LIKE_URL = "https://clientbp.ggpolarbear.com/LikeProfile"
BD_INFO_URL = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"

daily_limit = 500
used_count = 0

# 🤖 Bot ON/OFF state
BOT_STATE_FILE = "/tmp/bot_state.json" if os.environ.get("VERCEL") else "bot_state.json"

def get_bot_state():
    try:
        with open(BOT_STATE_FILE, "r") as f:
            return bool(json.load(f).get("enabled", True))
    except Exception:
        return True

def set_bot_state(enabled):
    try:
        with open(BOT_STATE_FILE, "w") as f:
            json.dump({"enabled": bool(enabled)}, f)
    except Exception:
        pass


# ================= CORE HELPERS =================
def load_tokens():
    try:
        with open("token_bd.json", "r") as f:
            return json.load(f)
    except Exception as e:
        app.logger.error(f"Error loading BD tokens: {e}")
        return None

def encrypt_message(plaintext):
    try:
        key = b'Yg&tc%DEuh6%Zc^8'
        iv  = b'6oyZDr22E3ychjM%'
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded = pad(plaintext, AES.block_size)
        return binascii.hexlify(cipher.encrypt(padded)).decode('utf-8')
    except Exception as e:
        app.logger.error(f"Encrypt error: {e}")
        return None

def create_protobuf_message(user_id, region):
    try:
        message = like_pb2.like()
        message.uid = int(user_id)
        message.region = region
        return message.SerializeToString()
    except Exception as e:
        app.logger.error(f"Protobuf error: {e}")
        return None

async def send_request(encrypted_uid, token, url):
    try:
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Expect": "100-continue",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB55",
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(url, data=edata, headers=headers) as r:
                return await r.text()
    except Exception as e:
        app.logger.error(f"send_request: {e}")
        return None

async def send_multiple_requests(uid, region, url):
    try:
        pb = create_protobuf_message(uid, region)
        if pb is None: return None
        enc_uid = encrypt_message(pb)
        if enc_uid is None: return None
        tokens = load_tokens()
        if not tokens: return None
        tasks = [send_request(enc_uid, tokens[i % len(tokens)]["token"], url) for i in range(len(tokens))]
        return await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        app.logger.error(f"multi_request: {e}")
        return None

def create_protobuf(uid):
    try:
        m = uid_generator_pb2.uid_generator()
        m.saturn_ = int(uid)
        m.garena = 1
        return m.SerializeToString()
    except Exception as e:
        app.logger.error(f"uid proto: {e}")
        return None

def enc(uid):
    pb = create_protobuf(uid)
    if pb is None: return None
    return encrypt_message(pb)

def make_request(encrypted_uid, region, token):
    try:
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Expect": "100-continue",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB55",
        }
        r = requests.post(BD_INFO_URL, data=edata, headers=headers, verify=False, timeout=20)
        decoded = visit_count_pb2.Info()
        decoded.ParseFromString(r.content)
        return decoded
    except DecodeError as e:
        app.logger.error(f"DecodeError: {e}")
        return None
    except Exception as e:
        app.logger.error(f"make_request: {e}")
        return None


# ================= SHARED STYLES =================
BASE_CSS = """
<style>
* { margin:0; padding:0; box-sizing:border-box; }
:root{
  --g:#00ff41; --gd:#00b32c; --dd:#003b0f; --red:#ff0040;
  --bg:#000; --panel:#041a08;
}
html,body{
  min-height:100%;
  background:var(--bg);
  color:var(--g);
  font-family:'Courier New',Consolas,monospace;
  overflow-x:hidden;
}
body{
  min-height:100vh; position:relative; padding:24px 16px 60px;
}
/* scanlines + vignette */
body::before{
  content:''; position:fixed; inset:0; pointer-events:none; z-index:9998;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,
             rgba(0,255,65,.03) 2px,rgba(0,255,65,.03) 4px);
  animation:scan 10s linear infinite;
}
@keyframes scan{ from{background-position:0 0} to{background-position:0 200px} }
body::after{
  content:''; position:fixed; inset:0; pointer-events:none; z-index:9997;
  background:radial-gradient(ellipse at center,transparent 45%,rgba(0,0,0,.75) 100%);
}
.glow{ text-shadow:0 0 6px var(--g),0 0 14px var(--gd); }
.wrap{ max-width:760px; margin:0 auto; position:relative; z-index:2; }
.card{
  background:linear-gradient(180deg, rgba(0,30,10,.65), rgba(0,10,3,.9));
  border:1px solid rgba(0,255,65,.35);
  border-radius:14px;
  padding:28px 24px;
  box-shadow:0 0 24px rgba(0,255,65,.15), inset 0 0 24px rgba(0,255,65,.05);
  position:relative;
}
.card::before{
  content:'█ SYSTEM █ SECURE █ ENCRYPTED █';
  position:absolute; top:-10px; left:16px;
  background:#000; padding:0 8px; font-size:10px;
  color:var(--gd); letter-spacing:2px;
}
h1{
  font-size:26px; letter-spacing:3px; text-align:center;
  margin-bottom:6px; color:var(--g);
  text-shadow:0 0 8px var(--g),0 0 20px var(--gd);
}
.sub{ text-align:center; color:var(--gd); font-size:12px; letter-spacing:2px; margin-bottom:22px;}
.mono{ font-family:'Courier New',monospace; }
input{
  width:100%; background:#010d05; color:var(--g);
  border:1px solid rgba(0,255,65,.4);
  padding:14px 16px; font-family:'Courier New',monospace;
  font-size:16px; border-radius:8px; outline:none;
  transition:.2s; letter-spacing:2px;
}
input:focus{ border-color:var(--g); box-shadow:0 0 12px rgba(0,255,65,.35); }
input::placeholder{ color:rgba(0,255,65,.3); letter-spacing:2px; }
button{
  width:100%; margin-top:14px;
  background:linear-gradient(180deg, rgba(0,255,65,.18), rgba(0,255,65,.05));
  color:var(--g); border:1px solid var(--g);
  padding:14px 18px; font-family:'Courier New',monospace;
  font-size:14px; font-weight:bold; letter-spacing:3px;
  border-radius:8px; cursor:pointer; transition:.2s;
  text-shadow:0 0 8px var(--g);
}
button:hover:not(:disabled){
  background:linear-gradient(180deg, rgba(0,255,65,.35), rgba(0,255,65,.1));
  box-shadow:0 0 18px rgba(0,255,65,.55);
  transform:translateY(-1px);
}
button:disabled{ opacity:.5; cursor:not-allowed; }
.err{ color:var(--red); text-align:center; margin-top:12px; font-size:13px;
      text-shadow:0 0 8px rgba(255,0,64,.7); min-height:16px; }
.row{ display:grid; grid-template-columns: 1fr; gap:14px; }
@media(min-width:720px){ .row{ grid-template-columns:1fr 1fr; } }
.kv{ display:flex; justify-content:space-between; padding:10px 0;
     border-bottom:1px dashed rgba(0,255,65,.15); font-size:14px; }
.kv span:first-child{ color:var(--gd); letter-spacing:1px;}
.kv span:last-child{ color:var(--g); font-weight:bold; }
.status-bar{
  display:flex; justify-content:space-between; align-items:center;
  font-size:11px; color:var(--gd); margin-bottom:16px; letter-spacing:1px;
}
.dot{
  display:inline-block; width:8px; height:8px; border-radius:50%;
  background:var(--g); box-shadow:0 0 8px var(--g);
  animation:pulse 1.4s infinite; vertical-align:middle; margin-right:6px;
}
@keyframes pulse{ 0%,100%{opacity:1} 50%{opacity:.3} }
.blink{ animation:blink 1s steps(2) infinite; }
@keyframes blink{ 50%{opacity:0} }
.typing::after{ content:'_'; animation:blink 1s infinite; }
a{ color:var(--g); text-decoration:none; }
.badge{ display:inline-block; padding:2px 8px; border:1px solid var(--g);
        border-radius:4px; font-size:10px; letter-spacing:2px; }
.res{
  margin-top:18px; padding:16px; border:1px solid rgba(0,255,65,.3);
  border-radius:10px; background:rgba(0,255,65,.03); display:none;
}
.res.show{ display:block; animation:fade .35s ease; }
@keyframes fade{ from{opacity:0; transform:translateY(6px)} to{opacity:1; transform:none} }
.big{ font-size:30px; color:var(--g); text-shadow:0 0 12px var(--g); }
.center{ text-align:center; }
.toggle{
  display:flex; gap:10px; align-items:center; justify-content:space-between;
  padding:16px; border:1px solid rgba(0,255,65,.3); border-radius:10px;
  background:rgba(0,255,65,.03); margin:14px 0;
}
.pill{ padding:6px 14px; border-radius:20px; font-size:12px; letter-spacing:2px; font-weight:bold;}
.pill.on{ background:rgba(0,255,65,.2); color:var(--g); border:1px solid var(--g); }
.pill.off{ background:rgba(255,0,64,.15); color:var(--red); border:1px solid var(--red);}
.mini{ font-size:11px; color:var(--gd); letter-spacing:1px; }

/* Telegram Button Style */
.tg-btn {
  display: block;
  width: 100%;
  margin-top: 24px;
  padding: 16px;
  background: rgba(0,255,65,.05);
  color: var(--g);
  text-align: center;
  border: 1px solid var(--g);
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: bold;
  letter-spacing: 2px;
  text-decoration: none;
  text-shadow: 0 0 8px var(--g);
  box-shadow: 0 0 15px rgba(0,255,65,.15);
  transition: all 0.3s ease;
}
.tg-btn:hover {
  background: rgba(0,255,65,.2);
  box-shadow: 0 0 25px rgba(0,255,65,.5);
  transform: translateY(-2px);
}
</style>
"""


# ================= LOGIN PAGE =================
LOGIN_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEDUSA // ACCESS TERMINAL</title>
""" + BASE_CSS + """
</head><body>
<div class="wrap" style="max-width:460px; margin-top:10vh;">
  <div class="card">
    <div class="status-bar">
      <span><span class="dot"></span>TERMINAL ONLINE</span>
      <span>v3.8.5</span>
    </div>
    <h1 class="glow">◤ MEDUSA ACCESS ◢</h1>
    <p class="sub typing">RESTRICTED AREA · PASSKEY REQUIRED</p>
    <input type="password" id="pw" placeholder="ENTER PASSKEY" autofocus autocomplete="off">
    <button id="btn" onclick="login()">» AUTHENTICATE «</button>
    <p class="err" id="err"></p>
    <p class="mini center" style="margin-top:18px;">[ UNAUTHORIZED ACCESS IS MONITORED ]</p>
  </div>
</div>
<script>
async function login(){
  const pw = document.getElementById('pw').value;
  const err = document.getElementById('err');
  const btn = document.getElementById('btn');
  err.textContent=''; btn.disabled=true; btn.textContent='AUTHENTICATING...';
  try{
    const r = await fetch('/api/login',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({password:pw})
    });
    const d = await r.json();
    if(d.success){
      btn.textContent='ACCESS GRANTED ✓';
      setTimeout(()=>location.href='/dashboard', 500);
    } else {
      err.textContent='✗ ACCESS DENIED — INVALID PASSKEY';
      btn.disabled=false; btn.textContent='» AUTHENTICATE «';
      document.getElementById('pw').value='';
    }
  } catch(e){
    err.textContent='✗ CONNECTION ERROR'; btn.disabled=false;
    btn.textContent='» AUTHENTICATE «';
  }
}
document.getElementById('pw').addEventListener('keydown', e=>{
  if(e.key==='Enter') login();
});
</script></body></html>"""


# ================= DASHBOARD PAGE =================
DASHBOARD_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEDUSA // CONTROL PANEL</title>
""" + BASE_CSS + """
</head><body>
<div class="wrap">
  <div class="status-bar">
    <span><span class="dot"></span>LINK ESTABLISHED · BD SERVER</span>
    <span><a href="/logout">[ LOGOUT ]</a></span>
  </div>

  <div class="card">
    <h1 class="glow">⌁ MEDUSA LIKE WEBSITE ⌁</h1>
    <p class="sub">AUTHORIZED SESSION · REGION: BANGLADESH</p>

    <div class="toggle">
      <span><span class="mini">BOT STATUS</span></span>
      <span id="botPill" class="pill on">ONLINE</span>
    </div>

    <input type="text" id="uid" placeholder="ENTER FF UID" inputmode="numeric" autocomplete="off">
    <button id="go" onclick="run()">» INITIATE LIKE SEQUENCE «</button>
    <p class="err" id="err"></p>

    <div class="res" id="res">
      <div class="center" style="margin-bottom:14px;">
        <div class="mini">PLAYER NICKNAME</div>
        <div class="big" id="pname">—</div>
      </div>
      <div class="kv"><span>UID</span><span id="puid">—</span></div>
      <div class="kv"><span>LEVEL</span><span id="plevel">—</span></div>
      <div class="kv"><span>REGION</span><span id="pregion">—</span></div>
      <div class="kv"><span>LIKES BEFORE</span><span id="pbefore">—</span></div>
      <div class="kv"><span>LIKES AFTER</span><span id="pafter">—</span></div>
      <div class="kv" style="border-bottom:none;">
        <span>LIKES GIVEN</span>
        <span class="glow" id="pgiven" style="font-size:20px;">—</span>
      </div>
      <div class="kv" style="border-bottom:none;">
        <span>DAILY REMAINING</span><span id="premain">—</span>
      </div>
    </div>
  </div>

  <a href="https://t.me/MEDUSA_LIKE" target="_blank" class="tg-btn">
    ✈ JOIN TELEGRAM @MEDUSA_LIKE ✈
  </a>

  <p class="mini center" style="margin-top:14px;">
    UNAUTHORIZED REDISTRIBUTION WILL BE TRACED · v3.8.5
  </p>
</div>

<script>
async function refreshStatus(){
  try{
    const r = await fetch('/api/status');
    const d = await r.json();
    const pill = document.getElementById('botPill');
    if(d.bot_enabled){
      pill.className='pill on'; pill.textContent='ONLINE';
      document.getElementById('go').disabled=false;
    } else {
      pill.className='pill off'; pill.textContent='OFFLINE';
      document.getElementById('go').disabled=true;
    }
  }catch(e){}
}
refreshStatus();
setInterval(refreshStatus, 8000);

async function run(){
  const uid = document.getElementById('uid').value.trim();
  const err = document.getElementById('err');
  const btn = document.getElementById('go');
  const res = document.getElementById('res');
  err.textContent='';
  if(!/^\\d+$/.test(uid)){ err.textContent='✗ INVALID UID'; return; }
  btn.disabled=true; btn.textContent='TRANSMITTING PACKETS...';
  res.classList.remove('show');
  try{
    const r = await fetch('/api/like',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({uid})
    });
    const d = await r.json();
    if(!r.ok){
      err.textContent='✗ ' + (d.error || 'REQUEST FAILED');
      btn.disabled=false; btn.textContent='» INITIATE LIKE SEQUENCE «';
      return;
    }
    document.getElementById('pname').textContent   = d.player.nickname || '—';
    document.getElementById('puid').textContent    = d.player.uid;
    document.getElementById('plevel').textContent  = d.player.level;
    document.getElementById('pregion').textContent = d.player.region || 'BD';
    document.getElementById('pbefore').textContent = d.likes.before;
    document.getElementById('pafter').textContent  = d.likes.after;
    document.getElementById('pgiven').textContent  = '+' + d.likes.given;
    document.getElementById('premain').textContent = d.stats.remaining;
    res.classList.add('show');
    btn.textContent='✓ SEQUENCE COMPLETE';
    setTimeout(()=>{btn.disabled=false; btn.textContent='» INITIATE LIKE SEQUENCE «';}, 1800);
  }catch(e){
    err.textContent='✗ NETWORK ERROR';
    btn.disabled=false; btn.textContent='» INITIATE LIKE SEQUENCE «';
  }
}
document.getElementById('uid').addEventListener('keydown', e=>{
  if(e.key==='Enter') run();
});
</script></body></html>"""


# ================= ADMIN LOGIN =================
ADMIN_LOGIN_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEDUSA // ADMIN ROOT</title>
""" + BASE_CSS + """
</head><body>
<div class="wrap" style="max-width:460px; margin-top:10vh;">
  <div class="card">
    <div class="status-bar">
      <span><span class="dot"></span>ROOT TERMINAL</span>
      <span>ADMIN</span>
    </div>
    <h1 class="glow">⚡ ADMIN ROOT ⚡</h1>
    <p class="sub">PRIVILEGED ACCESS ONLY</p>
    <input type="password" id="pw" placeholder="ADMIN PASSKEY" autofocus autocomplete="off">
    <button onclick="login()">» UNLOCK ROOT «</button>
    <p class="err" id="err"></p>
  </div>
</div>
<script>
async function login(){
  const pw = document.getElementById('pw').value;
  const err = document.getElementById('err');
  err.textContent='';
  try{
    const r = await fetch('/api/admin/login',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({password:pw})
    });
    const d = await r.json();
    if(d.success){ location.reload(); }
    else { err.textContent='✗ INVALID ADMIN PASSKEY'; }
  }catch(e){ err.textContent='✗ CONNECTION ERROR'; }
}
document.getElementById('pw').addEventListener('keydown', e=>{
  if(e.key==='Enter') login();
});
</script></body></html>"""


# ================= ADMIN PANEL =================
ADMIN_PANEL = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEDUSA // ROOT CONTROL</title>
""" + BASE_CSS + """
</head><body>
<div class="wrap">
  <div class="status-bar">
    <span><span class="dot"></span>ROOT ACCESS GRANTED</span>
    <span><a href="/admin/logout">[ EXIT ROOT ]</a></span>
  </div>

  <div class="card">
    <h1 class="glow">⌬ ROOT CONTROL ⌬</h1>
    <p class="sub">GLOBAL BOT & SERVER MANAGEMENT</p>

    <div class="toggle" style="flex-direction:column; align-items:stretch; gap:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span class="mini">BOT STATUS</span>
        <span id="botPill" class="pill on">ONLINE</span>
      </div>
      <button id="tgl" onclick="toggle()">» TOGGLE BOT STATE «</button>
    </div>

    <div class="kv"><span>DAILY LIMIT</span><span id="lim">—</span></div>
    <div class="kv"><span>USED TODAY</span><span id="used">—</span></div>
    <div class="kv"><span>REMAINING</span><span id="rem">—</span></div>
    <div class="kv"><span>SERVER</span><span>BANGLADESH (BD)</span></div>
  </div>

  <p class="mini center" style="margin-top:14px;">
    ⚠ ROOT ACTIONS ARE LOGGED · v3.8.5
  </p>
</div>

<script>
async function refresh(){
  const r = await fetch('/api/admin/status');
  const d = await r.json();
  const pill = document.getElementById('botPill');
  if(d.enabled){ pill.className='pill on'; pill.textContent='ONLINE'; }
  else { pill.className='pill off'; pill.textContent='OFFLINE'; }
  document.getElementById('lim').textContent = d.daily_limit;
  document.getElementById('used').textContent = d.used;
  document.getElementById('rem').textContent = d.remaining;
}
async function toggle(){
  const btn = document.getElementById('tgl');
  btn.disabled=true; btn.textContent='SWITCHING...';
  await fetch('/api/admin/toggle', {method:'POST'});
  await refresh();
  btn.disabled=false; btn.textContent='» TOGGLE BOT STATE «';
}
refresh();
setInterval(refresh, 8000);
</script></body></html>"""


# ================= ROUTES =================
@app.route('/')
def home():
    if session.get('logged_in'):
        return redirect('/dashboard')
    return LOGIN_PAGE

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    return DASHBOARD_PAGE

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    if data.get('password') == ACCESS_PASSWORD:
        session['logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/api/status')
def api_status():
    return jsonify({
        "bot_enabled": get_bot_state(),
        "daily_limit": daily_limit,
        "used": used_count,
        "remaining": max(daily_limit - used_count, 0),
    })

@app.route('/api/like', methods=['POST'])
def api_like():
    global used_count
    if not session.get('logged_in'):
        return jsonify({"error": "UNAUTHORIZED"}), 401
    if not get_bot_state():
        return jsonify({"error": "BOT OFFLINE — CONTACT ADMIN"}), 503
    data = request.get_json(silent=True) or {}
    uid = str(data.get('uid', '')).strip()
    if not uid.isdigit():
        return jsonify({"error": "INVALID UID"}), 400
    if used_count >= daily_limit:
        return jsonify({"error": "DAILY LIMIT REACHED. RESET AT 4:00 AM IST."}), 429
    try:
        tokens = load_tokens()
        if not tokens:
            return jsonify({"error": "TOKEN LOAD FAILED"}), 500
        token = tokens[0]['token']
        enc_uid = enc(uid)
        if enc_uid is None:
            return jsonify({"error": "ENCRYPTION FAILED"}), 500
        before = make_request(enc_uid, ALLOWED_REGION, token)
        if before is None:
            return jsonify({"error": "PLAYER NOT FOUND OR API DOWN"}), 404
        before_like = before.AccountInfo.Likes

        asyncio.run(send_multiple_requests(uid, ALLOWED_REGION, BD_LIKE_URL))

        after = make_request(enc_uid, ALLOWED_REGION, token) or before
        after_like = after.AccountInfo.Likes
        like_given = max(after_like - before_like, 0)
        if like_given > 0:
            used_count += 1

        return jsonify({
            "success": True,
            "player": {
                "nickname": after.AccountInfo.PlayerNickname or "—",
                "level":    after.AccountInfo.Levels,
                "uid":      after.AccountInfo.UID,
                "region":   after.AccountInfo.PlayerRegion or "BD",
            },
            "likes": {
                "before": before_like,
                "after":  after_like,
                "given":  like_given,
            },
            "stats": {
                "daily_limit": daily_limit,
                "used": used_count,
                "remaining": max(daily_limit - used_count, 0),
            }
        })
    except Exception as e:
        app.logger.error(f"api_like: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin')
def admin_route():
    if not session.get('admin_logged_in'):
        return ADMIN_LOGIN_PAGE
    return ADMIN_PANEL

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin')

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.get_json(silent=True) or {}
    if data.get('password') == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/api/admin/status')
def api_admin_status():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "UNAUTHORIZED"}), 401
    return jsonify({
        "enabled": get_bot_state(),
        "daily_limit": daily_limit,
        "used": used_count,
        "remaining": max(daily_limit - used_count, 0),
    })

@app.route('/api/admin/toggle', methods=['POST'])
def api_admin_toggle():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "UNAUTHORIZED"}), 401
    new_state = not get_bot_state()
    set_bot_state(new_state)
    return jsonify({"success": True, "enabled": new_state})


# ================= LEGACY API (kept for API-key users) =================
@app.route('/like', methods=['GET'])
def handle_requests():
    global used_count
    api_key = request.args.get("key")
    if api_key not in VALID_API_KEYS:
        return jsonify({"error": "Invalid or missing API key", "status": 3}), 401
    if not get_bot_state():
        return jsonify({"error": "Bot offline", "status": 5}), 503
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "UID is required"}), 400
    if used_count >= daily_limit:
        return jsonify({"error": "Daily limit reached", "status": 4}), 429
    try:
        tokens = load_tokens()
        if not tokens:
            raise Exception("Failed to load BD tokens.")
        token = tokens[0]['token']
        enc_uid = enc(uid)
        before = make_request(enc_uid, ALLOWED_REGION, token)
        if before is None:
            raise Exception("Failed to get initial info.")
        before_like = before.AccountInfo.Likes
        asyncio.run(send_multiple_requests(uid, ALLOWED_REGION, BD_LIKE_URL))
        after = make_request(enc_uid, ALLOWED_REGION, token)
        after_like = after.AccountInfo.Likes
        like_given = after_like - before_like
        status = 1 if like_given > 0 else 2
        if status == 1:
            used_count += 1
        return jsonify(OrderedDict([
            ("LikesGivenByAPI", like_given),
            ("LikesafterCommand", after_like),
            ("LikesbeforeCommand", before_like),
            ("PlayerNickname", after.AccountInfo.PlayerNickname),
            ("Level", after.AccountInfo.Levels),
            ("Region", "BD"),
            ("UID", after.AccountInfo.UID),
            ("status", status),
            ("daily_limit", daily_limit),
            ("used", used_count),
            ("remaining", max(daily_limit - used_count, 0)),
        ]))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/remain', methods=['GET'])
def remain_info():
    return jsonify({
        "server": "BD",
        "daily_limit": daily_limit,
        "remaining": max(daily_limit - used_count, 0),
        "used": used_count,
        "reset_info": "4:00 AM IST",
    })


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
