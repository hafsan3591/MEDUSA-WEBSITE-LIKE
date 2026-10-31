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
app.secret_key = os.environ.get("SECRET_KEY", "medusa-premium-secret-2024-x9k")

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


# ================= PREMIUM STYLES =================
BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

* { margin:0; padding:0; box-sizing:border-box; font-family: 'Poppins', sans-serif; }

:root{
  --bg: #0b0f19;
  --card-bg: rgba(255, 255, 255, 0.03);
  --card-border: rgba(255, 255, 255, 0.08);
  --primary: #6366f1;
  --primary-hover: #4f46e5;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --accent: #8b5cf6;
}

html, body {
  min-height: 100vh;
  background-color: var(--bg);
  background-image: 
    radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.15) 0px, transparent 50%);
  color: var(--text-main);
  overflow-x: hidden;
}

body { padding: 24px 16px 60px; display: flex; flex-direction: column; align-items: center; }

.wrap { width: 100%; max-width: 500px; position: relative; z-index: 2; margin: 0 auto; }

.card {
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--card-border);
  border-radius: 20px;
  padding: 32px 24px;
  box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5);
  margin-bottom: 20px;
  transition: transform 0.3s ease;
}

h1 { font-size: 28px; font-weight: 700; text-align: center; margin-bottom: 8px; letter-spacing: 1px; }
.sub { text-align: center; color: var(--text-muted); font-size: 13px; margin-bottom: 28px; font-weight: 300; }

input {
  width: 100%; background: rgba(0,0,0,0.2); color: var(--text-main);
  border: 1px solid var(--card-border);
  padding: 16px 20px; font-size: 16px; border-radius: 12px; outline: none;
  transition: all 0.3s ease; margin-bottom: 16px;
}
input:focus { border-color: var(--primary); background: rgba(0,0,0,0.4); box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2); }
input::placeholder { color: var(--text-muted); }

button {
  width: 100%; background: linear-gradient(135deg, var(--primary), var(--accent));
  color: white; border: none; padding: 16px; font-size: 15px; font-weight: 600;
  border-radius: 12px; cursor: pointer; transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}
button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6); }
button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

.err { color: #ef4444; text-align: center; margin-top: 14px; font-size: 13px; min-height: 20px; font-weight: 500; }

/* Player Info Styles */
.res { display: none; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--card-border); }
.res.show { display: block; animation: slideUp 0.4s ease forwards; }
@keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

.player-header { text-align: center; margin-bottom: 24px; }
.player-name { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 4px; }

.kv { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }
.kv:last-child { border-bottom: none; }
.kv span:first-child { color: var(--text-muted); }
.kv span:last-child { font-weight: 600; color: var(--text-main); }

.highlight-val { font-size: 18px; color: #10b981 !important; text-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }

/* Social Buttons */
.social-container { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }

.btn-social {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 16px; border-radius: 12px; font-size: 15px; font-weight: 600;
  text-decoration: none; transition: all 0.3s ease; color: white;
}

.btn-telegram { background: #229ED9; box-shadow: 0 4px 15px rgba(34, 158, 217, 0.3); }
.btn-telegram:hover { background: #1e88be; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(34, 158, 217, 0.5); }

.btn-tiktok { background: #000000; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1); }
.btn-tiktok:hover { background: #111111; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(255, 255, 255, 0.2); border-color: rgba(255,255,255,0.4); }

.icon { width: 20px; height: 20px; fill: currentColor; }

/* Header Bar */
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; font-size: 13px; color: var(--text-muted); }
.top-bar a { color: #ef4444; text-decoration: none; font-weight: 500; }
.top-bar a:hover { text-decoration: underline; }

.pill { padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; }
.pill.on { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
.pill.off { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }

.toggle-box { display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); padding: 16px; border-radius: 12px; border: 1px solid var(--card-border); margin-bottom: 20px; }
</style>
"""

# ================= LOGIN PAGE =================
LOGIN_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEDUSA // LOGIN</title>
""" + BASE_CSS + """
</head><body>
<div class="wrap" style="margin-top:15vh;">
  <div class="card">
    <h1>MEDUSA</h1>
    <p class="sub">Premium Free Fire Likes</p>
    <input type="password" id="pw" placeholder="Enter Password" autofocus autocomplete="off">
    <button id="btn" onclick="login()">Access Dashboard</button>
    <p class="err" id="err"></p>
  </div>
</div>
<script>
async function login(){
  const pw = document.getElementById('pw').value;
  const err = document.getElementById('err');
  const btn = document.getElementById('btn');
  err.textContent=''; btn.disabled=true; btn.textContent='Authenticating...';
  try{
    const r = await fetch('/api/login',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({password:pw})
    });
    const d = await r.json();
    if(d.success){
      btn.textContent='Success ✓';
      setTimeout(()=>location.href='/dashboard', 500);
    } else {
      err.textContent='Invalid Password';
      btn.disabled=false; btn.textContent='Access Dashboard';
      document.getElementById('pw').value='';
    }
  } catch(e){
    err.textContent='Connection Error'; btn.disabled=false;
    btn.textContent='Access Dashboard';
  }
}
document.getElementById('pw').addEventListener('keydown', e=>{ if(e.key==='Enter') login(); });
</script></body></html>"""


# ================= DASHBOARD PAGE =================
DASHBOARD_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEDUSA // DASHBOARD</title>
""" + BASE_CSS + """
</head><body>
<div class="wrap">
  <div class="top-bar">
    <span>Welcome to Medusa</span>
    <a href="/logout">Logout</a>
  </div>

  <div class="card">
    <h1>MEDUSA LIKE</h1>
    <p class="sub">Boost your Free Fire Profile</p>

    <div class="toggle-box">
      <span style="font-size:14px; font-weight:500;">Server Status</span>
      <span id="botPill" class="pill on">ONLINE</span>
    </div>

    <input type="text" id="uid" placeholder="Enter Free Fire UID" inputmode="numeric" autocomplete="off">
    <button id="go" onclick="run()">Send Likes Now</button>
    <p class="err" id="err"></p>

    <div class="res" id="res">
      <div class="player-header">
        <div class="player-name" id="pname">Player Name</div>
      </div>
      <div class="kv"><span>UID</span><span id="puid">—</span></div>
      <div class="kv"><span>Level</span><span id="plevel">—</span></div>
      <div class="kv"><span>Region</span><span id="pregion">—</span></div>
      
      <div style="height: 10px;"></div>
      
      <div class="kv"><span>Likes Before</span><span id="pbefore">—</span></div>
      <div class="kv"><span>Likes After</span><span id="pafter">—</span></div>
      <div class="kv"><span>Likes Given</span><span class="highlight-val" id="pgiven">—</span></div>
      <div class="kv"><span>Daily Remaining</span><span id="premain">—</span></div>
    </div>
  </div>

  <div class="social-container">
    <a href="https://t.me/MEDUSA_LIKE" target="_blank" class="btn-social btn-telegram">
      <svg class="icon" viewBox="0 0 24 24"><path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.223-.54.223l.19-2.712 5.01-4.523c.218-.19-.05-.298-.338-.108l-6.19 3.89-2.673-.83c-.58-.182-.594-.58.122-.86l10.426-4.018c.485-.176.907.108.752.755z"/></svg>
      Join Telegram
    </a>
    <a href="https://www.tiktok.com/@hafsan_amv" target="_blank" class="btn-social btn-tiktok">
      <svg class="icon" viewBox="0 0 24 24"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.11-3.44-3.17-3.61-5.46-.02-.65-.02-1.3.05-1.95.4-2.82 2.59-5.25 5.39-5.87 1.09-.23 2.22-.19 3.3-.04v4.11c-.64-.19-1.33-.24-1.97-.12-1.31.22-2.45 1.18-2.86 2.43-.32.97-.22 2.05.26 2.95.61 1.18 1.91 1.88 3.24 1.8 1.16-.04 2.23-.68 2.82-1.69.25-.42.38-.9.38-1.38.02-3.35.01-6.71.01-10.07h4.65z"/></svg>
      Follow on TikTok
    </a>
  </div>
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
  
  if(!/^\\d+$/.test(uid)){ err.textContent='Please enter a valid numeric UID'; return; }
  
  btn.disabled=true; btn.textContent='Processing...';
  res.classList.remove('show');
  
  try{
    const r = await fetch('/api/like',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({uid})
    });
    const d = await r.json();
    
    if(!r.ok){
      err.textContent='✗ ' + (d.error || 'Request failed');
      btn.disabled=false; btn.textContent='Send Likes Now';
      return;
    }
    
    document.getElementById('pname').textContent   = d.player.nickname || 'Unknown';
    document.getElementById('puid').textContent    = d.player.uid;
    document.getElementById('plevel').textContent  = d.player.level;
    document.getElementById('pregion').textContent = d.player.region || 'BD';
    document.getElementById('pbefore').textContent = d.likes.before;
    document.getElementById('pafter').textContent  = d.likes.after;
    document.getElementById('pgiven').textContent  = '+' + d.likes.given;
    document.getElementById('premain').textContent = d.stats.remaining;
    
    res.classList.add('show');
    btn.textContent='Success! ✓';
    setTimeout(()=>{btn.disabled=false; btn.textContent='Send Likes Now';}, 2000);
  }catch(e){
    err.textContent='Network Error';
    btn.disabled=false; btn.textContent='Send Likes Now';
  }
}
document.getElementById('uid').addEventListener('keydown', e=>{ if(e.key==='Enter') run(); });
</script></body></html>"""


# ================= ADMIN LOGIN =================
ADMIN_LOGIN_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEDUSA // ADMIN</title>
""" + BASE_CSS + """
</head><body>
<div class="wrap" style="margin-top:15vh;">
  <div class="card">
    <h1 style="color:#ef4444;">ADMIN ROOT</h1>
    <p class="sub">Restricted Access Only</p>
    <input type="password" id="pw" placeholder="Admin Password" autofocus autocomplete="off">
    <button onclick="login()" style="background:#ef4444; box-shadow:0 4px 15px rgba(239,68,68,0.4);">Unlock Root</button>
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
    else { err.textContent='Invalid Admin Password'; }
  }catch(e){ err.textContent='Connection Error'; }
}
document.getElementById('pw').addEventListener('keydown', e=>{ if(e.key==='Enter') login(); });
</script></body></html>"""


# ================= ADMIN PANEL =================
ADMIN_PANEL = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEDUSA // ROOT</title>
""" + BASE_CSS + """
</head><body>
<div class="wrap">
  <div class="top-bar">
    <span style="color:#ef4444; font-weight:600;">ROOT ACCESS</span>
    <a href="/admin/logout">Exit Root</a>
  </div>

  <div class="card">
    <h1>Admin Panel</h1>
    <p class="sub">Global Bot Management</p>

    <div class="toggle-box" style="flex-direction:column; gap:16px;">
      <div style="display:flex; justify-content:space-between; width:100%;">
        <span style="font-weight:500;">Bot Status</span>
        <span id="botPill" class="pill on">ONLINE</span>
      </div>
      <button id="tgl" onclick="toggle()" style="background:rgba(255,255,255,0.1); box-shadow:none; border:1px solid rgba(255,255,255,0.2);">Toggle Bot State</button>
    </div>

    <div class="kv"><span>Daily Limit</span><span id="lim">—</span></div>
    <div class="kv"><span>Used Today</span><span id="used">—</span></div>
    <div class="kv"><span>Remaining</span><span id="rem" style="color:#10b981;">—</span></div>
    <div class="kv"><span>Server Region</span><span>Bangladesh (BD)</span></div>
  </div>
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
  btn.disabled=true; btn.textContent='Switching...';
  await fetch('/api/admin/toggle', {method:'POST'});
  await refresh();
  btn.disabled=false; btn.textContent='Toggle Bot State';
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
        return jsonify({"error": "DAILY LIMIT REACHED. TRY TOMORROW."}), 429
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


# ================= LEGACY API =================
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
    app.run(debug=True, use_reloader=False)16px;
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
