from flask import Flask, request, jsonify, render_template_string, session
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import aiohttp
import requests
import json
import like_pb2
import uid_generator_pb2
import visit_count_pb2
from google.protobuf.message import DecodeError
from collections import OrderedDict
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
app.secret_key = "zexxy-change-this-to-a-random-string-please"

# ✅ Valid API keys
VALID_API_KEYS = {"ZEXXY"}
WEB_PASSWORD = "HM-385-MH"

daily_limit = 200
used_count = 0

# ---------------- HTML PAGE ----------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MEDUSA LIKE API</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);
    min-height:100vh; display:flex; align-items:center; justify-content:center;
    padding:20px; color:#fff;
  }
  .card {
    background:rgba(255,255,255,0.05); backdrop-filter:blur(10px);
    border:1px solid rgba(255,255,255,0.1); border-radius:20px;
    padding:40px; width:100%; max-width:420px;
    box-shadow:0 20px 60px rgba(0,0,0,0.5);
  }
  h1 { font-size:22px; margin-bottom:8px; text-align:center; }
  .subtitle { color:#8892b0; font-size:13px; text-align:center; margin-bottom:26px; }
  label { display:block; font-size:13px; color:#8892b0; margin-bottom:6px; }
  input, select {
    width:100%; padding:12px 14px; background:rgba(0,0,0,0.3);
    border:1px solid rgba(255,255,255,0.15); border-radius:10px;
    color:#fff; font-size:14px; margin-bottom:16px; outline:none;
  }
  input:focus, select:focus { border-color:#4f8cff; }
  button {
    width:100%; padding:13px; border:none; border-radius:10px;
    background:linear-gradient(135deg,#4f8cff,#3b6fd4); color:#fff;
    font-size:15px; font-weight:600; cursor:pointer;
  }
  button:disabled { opacity:0.5; cursor:not-allowed; }
  .result { margin-top:20px; padding:16px; border-radius:10px; font-size:13px; display:none; }
  .result.success { background:rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.35); display:block; }
  .result.error   { background:rgba(248,113,113,0.1); border:1px solid rgba(248,113,113,0.35); display:block; }
  .result .row { display:flex; justify-content:space-between; padding:4px 0; }
  .result .row span:first-child { color:#8892b0; }
  .hidden { display:none !important; }
</style>
</head>
<body>
<div class="card">
  <!-- Login -->
  <div id="loginScreen">
    <h1>MEDUSA LIKE API</h1>
    <p class="subtitle">Enter password to continue</p>
    <label>Password</label>
    <input type="password" id="password" placeholder="Enter password" onkeydown="if(event.key==='Enter')login()">
    <button onclick="login()">Login</button>
    <div id="loginError" class="result error" style="display:none;">Wrong password</div>
  </div>

  <!-- Main -->
  <div id="mainScreen" class="hidden">
    <h1>Send Likes</h1>
    <p class="subtitle">Send likes to a Free Fire account</p>
    <label>Region</label>
    <select id="region">
      <option value="BD">Bangladesh (BD)</option>
      <option value="IND">India (IND)</option>
      <option value="BR">Brazil (BR)</option>
      <option value="US">USA (US)</option>
      <option value="SAC">South America (SAC)</option>
      <option value="NA">North America (NA)</option>
    </select>
    <label>Free Fire UID</label>
    <input type="text" id="uid" placeholder="Enter UID" inputmode="numeric">
    <button id="confirmBtn" onclick="sendLike()">Confirm</button>
    <div id="result" class="result"></div>
  </div>
</div>

<script>
async function login() {
  const password = document.getElementById('password').value;
  const res = await fetch('/auth', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({password})
  });
  if (res.ok) {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('mainScreen').classList.remove('hidden');
  } else {
    document.getElementById('loginError').style.display = 'block';
  }
}

async function sendLike() {
  const uid = document.getElementById('uid').value.trim();
  const region = document.getElementById('region').value;
  const btn = document.getElementById('confirmBtn');
  const result = document.getElementById('result');
  if (!uid) { alert('Enter UID'); return; }
  btn.disabled = true; btn.textContent = 'Sending...';
  result.className = 'result'; result.innerHTML = '';
  try {
    const res = await fetch(`/web-like?uid=${encodeURIComponent(uid)}&region=${encodeURIComponent(region)}`);
    const data = await res.json();
    if (res.ok && data.status === 1) {
      result.className = 'result success';
      result.innerHTML = `
        <div class="row"><span>Likes Given</span><span>${data.LikesGivenByAPI}</span></div>
        <div class="row"><span>Before</span><span>${data.LikesbeforeCommand}</span></div>
        <div class="row"><span>After</span><span>${data.LikesafterCommand}</span></div>
        <div class="row"><span>Nickname</span><span>${data.PlayerNickname}</span></div>
        <div class="row"><span>Level</span><span>${data.Level}</span></div>
        <div class="row"><span>UID</span><span>${data.UID}</span></div>
        <div class="row"><span>Remaining</span><span>${data.remaining}</span></div>`;
    } else if (res.ok && data.status === 2) {
      result.className = 'result error';
      result.innerHTML = `<div class="row"><span>Status</span><span>No likes sent (already liked?)</span></div>`;
    } else {
      result.className = 'result error';
      result.innerHTML = `<div class="row"><span>Error</span><span>${data.error || 'Request failed'}</span></div>`;
    }
  } catch (e) {
    result.className = 'result error';
    result.innerHTML = `<div class="row"><span>Error</span><span>${e.message}</span></div>`;
  } finally {
    btn.disabled = false; btn.textContent = 'Confirm';
  }
}
</script>
</body>
</html>
"""


# ---------------- Helpers (unchanged) ----------------
def load_tokens(region):
    try:
        if region == "IND":
            with open("token_ind.json", "r") as f: tokens = json.load(f)
        elif region in {"BR", "US", "SAC", "NA"}:
            with open("token_br.json", "r") as f: tokens = json.load(f)
        else:
            with open("token_bd.json", "r") as f: tokens = json.load(f)
        return tokens
    except Exception as e:
        app.logger.error(f"Error loading tokens for region {region}: {e}")
        return None


def encrypt_message(plaintext):
    try:
        key = b'Yg&tc%DEuh6%Zc^8'
        iv  = b'6oyZDr22E3ychjM%'
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return binascii.hexlify(cipher.encrypt(pad(plaintext, AES.block_size))).decode('utf-8')
    except Exception as e:
        app.logger.error(f"Error encrypting message: {e}")
        return None


def create_protobuf_message(user_id, region):
    try:
        m = like_pb2.like(); m.uid = int(user_id); m.region = region
        return m.SerializeToString()
    except Exception as e:
        app.logger.error(f"Error creating protobuf message: {e}")
        return None


async def send_request(encrypted_uid, token, url):
    try:
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Expect": "100-continue", "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1", "ReleaseVersion": "OB55"
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(url, data=edata, headers=headers) as r:
                return await r.text()
    except Exception as e:
        app.logger.error(f"Exception in send_request: {e}")
        return None


async def send_multiple_requests(uid, region, url):
    try:
        pb = create_protobuf_message(uid, region)
        if pb is None: return None
        encrypted = encrypt_message(pb)
        if encrypted is None: return None
        tokens = load_tokens(region)
        if not tokens: return None
        tasks = [send_request(encrypted, tokens[i % len(tokens)]["token"], url) for i in range(100)]
        return await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        app.logger.error(f"Exception in send_multiple_requests: {e}")
        return None


def create_protobuf(uid):
    try:
        m = uid_generator_pb2.uid_generator(); m.saturn_ = int(uid); m.garena = 1
        return m.SerializeToString()
    except Exception as e:
        app.logger.error(f"Error creating uid protobuf: {e}")
        return None


def enc(uid):
    pb = create_protobuf(uid)
    if pb is None: return None
    return encrypt_message(pb)


BD_PERSONAL_SHOW_URL = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
BD_LIKE_URL = "https://clientbp.ggpolarbear.com/LikeProfile"


def make_request(encrypt, region, token):
    try:
        if region == "IND":
            url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        elif region in {"BR", "US", "SAC", "NA"}:
            url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
        else:
            url = BD_PERSONAL_SHOW_URL
        edata = bytes.fromhex(encrypt)
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Expect": "100-continue", "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1", "ReleaseVersion": "OB55"
        }
        r = requests.post(url, data=edata, headers=headers, verify=False, timeout=15)
        d = visit_count_pb2.Info(); d.ParseFromString(r.content)
        return d
    except DecodeError as e:
        app.logger.error(f"DecodeError: {e}"); return None
    except Exception as e:
        app.logger.error(f"Error in make_request: {e}"); return None


# ---------------- Shared like logic ----------------
def _process_like(uid, region):
    global used_count
    try:
        tokens = load_tokens(region)
        if not tokens: raise Exception("Failed to load tokens.")
        token = tokens[0]['token']
        encrypted_uid = enc(uid)
        if encrypted_uid is None: raise Exception("Encryption of UID failed.")
        before = make_request(encrypted_uid, region, token)
        if before is None: raise Exception("Failed to get initial info.")
        before_like = before.AccountInfo.Likes

        if region == "IND":
            url = "https://client.ind.freefiremobile.com/LikeProfile"
        elif region in {"BR", "US", "SAC", "NA"}:
            url = "https://client.us.freefiremobile.com/LikeProfile"
        else:
            url = BD_LIKE_URL

        asyncio.run(send_multiple_requests(uid, region, url))

        after = make_request(encrypted_uid, region, token)
        if after is None: raise Exception("Failed to get final info.")
        after_like = after.AccountInfo.Likes
        like_given = after_like - before_like
        status = 1 if like_given > 0 else 2
        if status == 1: used_count += 1
        remaining = max(daily_limit - used_count, 0)

        result = OrderedDict([
            ("LikesGivenByAPI", like_given),
            ("LikesafterCommand", after_like),
            ("LikesbeforeCommand", before_like),
            ("PlayerNickname", after.AccountInfo.PlayerNickname),
            ("Level", after.AccountInfo.Levels),
            ("Region", after.AccountInfo.PlayerRegion),
            ("UID", after.AccountInfo.UID),
            ("status", status),
            ("daily_limit", daily_limit),
            ("used", used_count),
            ("remaining", remaining),
        ])
        return app.response_class(
            response=json.dumps(result, separators=(',', ':')),
            status=200, mimetype='application/json'
        )
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------- Web routes ----------------
@app.route('/')
def home():
    return render_template_string(HTML_PAGE)


@app.route('/auth', methods=['POST'])
def auth():
    data = request.get_json(silent=True) or {}
    if data.get('password') == WEB_PASSWORD:
        session['authenticated'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Wrong password"}), 401


@app.route('/web-like', methods=['GET'])
def web_like():
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401
    uid = request.args.get("uid")
    region = request.args.get("region", "").upper()
    if not uid or not region:
        return jsonify({"error": "UID and region required"}), 400
    return _process_like(uid, region)


@app.route('/like', methods=['GET'])
def handle_requests():
    api_key = request.args.get("key")
    if api_key not in VALID_API_KEYS and not session.get('authenticated'):
        result = OrderedDict([("error", "Invalid or missing API key"), ("status", 3)])
        return app.response_class(
            response=json.dumps(result, separators=(',', ':')),
            status=401, mimetype='application/json'
        )
    uid = request.args.get("uid")
    region = request.args.get("region", "").upper()
    if not uid or not region:
        return {"error": "UID and region are required"}, 400
    return _process_like(uid, region)


@app.route('/remain', methods=['GET'])
def remain_info():
    global used_count
    remaining = max(daily_limit - used_count, 0)
    return jsonify({
        "daily_limit": daily_limit, "remaining": remaining,
        "used": used_count, "reset_info": "4:00 AM IST"
    })


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)