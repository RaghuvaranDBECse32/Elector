import os
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import google.generativeai as genai

# ==============================
# CONFIG
# ==============================
PORT = 8080
DB = "chat.db"

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ==============================
# DATABASE
# ==============================
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chats(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    response TEXT
)
""")

conn.commit()

# ==============================
# FULL HTML (YOUR UI + CHAT ADDED)
# ==============================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CivicPath AI</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
body { font-family: Arial; margin:0; padding:20px; background:#f7f6f2; }
h1 { font-size:28px; }
.chat-box {
  margin-top:20px;
  border:1px solid #ccc;
  padding:15px;
  border-radius:10px;
  background:#fff;
}
textarea { width:100%; height:80px; }
button { padding:10px 15px; margin-top:10px; cursor:pointer; }
#output { white-space:pre-wrap; margin-top:10px; }
.login-box { margin-bottom:20px; }
</style>
</head>

<body>

<h1>🏛 CivicPath AI – Election Learning Assistant</h1>

<!-- LOGIN -->
<div class="login-box">
<input id="username" placeholder="Username">
<input id="password" type="password" placeholder="Password">
<button onclick="login()">Login</button>
</div>

<!-- INTRO -->
<p>
Understand election steps with interactive learning + AI assistant.
</p>

<!-- CHAT -->
<div class="chat-box">
<textarea id="prompt" placeholder="Ask about elections..."></textarea>
<button onclick="send()">Ask AI</button>
<pre id="output"></pre>
</div>

<script>
let user = "";

// LOGIN
function login(){
  fetch('/login',{
    method:'POST',
    body:JSON.stringify({
      username:document.getElementById('username').value,
      password:document.getElementById('password').value
    })
  })
  .then(res=>res.json())
  .then(data=>{
    if(data.status==="ok"){
      user = data.user;
      alert("Logged in as " + user);
    }
  });
}

// STREAM CHAT
function send(){
  if(!user){
    alert("Login first!");
    return;
  }

  const prompt = document.getElementById('prompt').value;
  const evtSource = new EventSource(`/chat?user=${user}&prompt=${encodeURIComponent(prompt)}`);

  let output = "";

  evtSource.onmessage = function(event){
    if(event.data === "[END]"){
      evtSource.close();
    } else {
      output += event.data;
      document.getElementById("output").textContent = output;
    }
  };
}
</script>

</body>
</html>
"""

# ==============================
# SERVER
# ==============================
class Handler(BaseHTTPRequestHandler):

    def _set_headers(self, content="text/html"):
        self.send_response(200)
        self.send_header("Content-type", content)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # HOME PAGE
        if parsed.path == "/":
            self._set_headers()
            self.wfile.write(HTML_PAGE.encode())

        # CHAT STREAM
        elif parsed.path == "/chat":
            params = urllib.parse.parse_qs(parsed.query)
            user = params.get("user", [""])[0]
            prompt = params.get("prompt", [""])[0]

            self.send_response(200)
            self.send_header("Content-type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()

            response = model.generate_content(prompt, stream=True)

            full_text = ""

            for chunk in response:
                if chunk.text:
                    text = chunk.text
                    full_text += text
                    self.wfile.write(f"data: {text}\n\n".encode())
                    self.wfile.flush()

            self.wfile.write(b"data: [END]\n\n")

            # SAVE CHAT
            cur.execute("INSERT INTO chats(username,message,response) VALUES(?,?,?)",
                        (user, prompt, full_text))
            conn.commit()

    def do_POST(self):

        if self.path == "/login":
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length))

            username = data["username"]
            password = data["password"]

            cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                        (username, password))
            user = cur.fetchone()

            if not user:
                cur.execute("INSERT OR IGNORE INTO users(username,password) VALUES(?,?)",
                            (username, password))
                conn.commit()

            self._set_headers("application/json")
            self.wfile.write(json.dumps({
                "status": "ok",
                "user": username
            }).encode())

# ==============================
# RUN
# ==============================
print(f"🚀 Running on http://localhost:{PORT}")
HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
