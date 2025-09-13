# app/app.py
# WARNING: This file is intentionally and massively insecure for demo purposes.
# DO NOT RUN ON A PUBLIC/PRODUCTION NETWORK. Use in an isolated VM/LAN only.

from flask import Flask, request, session, redirect, url_for, render_template_string, send_from_directory, jsonify, make_response
import sqlite3
import os
import subprocess
import pickle
import yaml  # intentionally old/unsafe usage in requirements
import secrets
from pathlib import Path

app = Flask(__name__)

# A05: Hardcoded, trivial secret and predictable session cookie settings
app.secret_key = "insecure-secret-12345"   # extremely weak; demo only
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False

# CORS: allow all origins (misconfiguration)
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Fake user store (in-memory)
USERS = {
    "alice": {"account_id": "acct-alice", "balance": 1000},
    "bob": {"account_id": "acct-bob", "balance": 500},
}

# Set up a blatantly insecure sqlite DB (SQL injection risk)
DB_FILE = "insecure.db"
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE users (username TEXT PRIMARY KEY, balance REAL)")
    c.execute("INSERT INTO users VALUES ('alice', 1000)")
    c.execute("INSERT INTO users VALUES ('bob', 500)")
    conn.commit()
    conn.close()

# Home
@app.route('/')
def index():
    user = session.get("user")
    if user:
        return f"Hello {user}! <a href='/logout'>Logout</a><br><a href='/transfer_form'>Transfer</a><br><a href='/admin_debug'>Admin Debug</a>"
    return "Hello Guest! <a href='/login'>Login</a>"

# A04: Insecure Design - Weak Login (no password) + session fixation possibility
@app.route('/login', methods=['GET', 'POST'])
def login():
    # optionally allow session fixation token via query param
    sid = request.args.get('sid')
    if sid:
        # insecure: accept any provided session id value
        session['session_id'] = sid

    if request.method == 'POST':
        username = request.form.get('username', '')
        # NO password verification - intentionally insecure
        if username in USERS:
            # insecure: set predictable session user and predictable csrf token
            session['user'] = username
            session['csrf'] = "csrf-"+username  # predictable CSRF token - insecure
            return redirect(url_for('index'))
        return "Unknown user", 401
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            Username: <input type="text" name="username"><br>
            <input type="submit" value="Login">
        </form>
        <p>Or set session id via ?sid=YOURID</p>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# A04: Broken Transfer Logic + SQL Injection (string concatenation)
@app.route('/transfer_form')
def transfer_form():
    return render_template_string('''
        <h2>Transfer Money</h2>
        <form method="post" action="/transfer">
            To Account(username): <input type="text" name="to_user"><br>
            Amount: <input type="number" name="amount"><br>
            <input type="submit" value="Transfer">
        </form>
        <p>Note: This demo uses insecure SQL & business logic.</p>
    ''')

@app.route('/transfer', methods=['POST'])
def transfer():
    user = session.get("user")
    to_user = request.form.get('to_user')
    amount = request.form.get('amount')

    if user is None:
        return "Not logged in", 401

    # INSECURE: no auth, no ownership check, no validation
    try:
        amount_val = float(amount)
    except Exception:
        return "Invalid amount", 400

    # Insecure SQL using string concat => SQL Injection
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Vulnerable query
    query = f"UPDATE users SET balance = balance + {amount_val} WHERE username = '{to_user}'"
    c.execute(query)   # SQL injection risk if to_user crafted
    conn.commit()
    # leak DB contents back (insecure)
    rows = c.execute("SELECT username, balance FROM users").fetchall()
    conn.close()
    return jsonify({"result": f"Transferred {amount_val} to {to_user} (initiated by {user})", "db": rows})

# A04: Insecure Deserialization endpoint (pickle.loads on user input)
@app.route('/deserialize', methods=['POST'])
def deserialize():
    # Expect raw binary pickled payload in body (dangerous)
    data = request.data
    try:
        obj = pickle.loads(data)   # INSECURE: arbitrary code execution possible
        return jsonify({"ok": True, "obj_type": str(type(obj)), "repr": repr(obj)})
    except Exception as e:
        return f"Deserialization failed: {e}", 400

# A04/A05: Unsafe YAML load (using full_load / unsafe loader)
@app.route('/yaml', methods=['POST'])
def yaml_endpoint():
    try:
        # uses unsafe loader which can instantiate objects
        content = request.data.decode('utf-8')
        obj = yaml.full_load(content)  # unsafe in older PyYAML versions
        return jsonify({"parsed": str(obj)})
    except Exception as e:
        return f"YAML parse error: {e}", 400

# A05: Debug/admin info endpoint that leaks env & secrets
@app.route('/admin_debug')
def admin_debug():
    # Return environment and session - huge info leak
    info = {
        "env": dict(os.environ),
        "session": dict(session),
        "secret_key": app.secret_key,
    }
    return jsonify(info)

# A05: Exec endpoint: command injection (uses shell=True)
@app.route('/exec', methods=['POST'])
def exec_cmd():
    cmd = request.form.get('cmd', '')
    # Danger: using shell=True with user input is command injection vector
    out = subprocess.getoutput(cmd)
    return f"Command output:\n<pre>{out}</pre>"

# A05: Upload path that does NOT sanitize filename => directory traversal
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        return "No file", 400
    # INSECURE: directly join filename (could be ../ etc)
    filepath = UPLOAD_DIR / f.filename
    f.save(str(filepath))
    return f"Saved to {filepath}"

# A06: Expose outdated package versions & sample hardcoded token
@app.route('/meta')
def meta():
    return jsonify({
        "flask_version": Flask.__version__,
        "hardcoded_api_token": "API_TOKEN_DEMO_1234567890"  # demo secret
    })

# A05: Serve any file from project root (insecure)
@app.route('/files/<path:filename>')
def files(filename):
    # Danger: reveals arbitrary files if accessible
    return send_from_directory('.', filename)

# Backdoor / secret admin action (hidden but hardcoded credential)
@app.route('/backdoor', methods=['POST'])
def backdoor():
    token = request.form.get('token')
    if token == "super-secret-admin-token":   # hardcoded token
        # perform dangerous action: drop DB (demo only)
        try:
            os.remove(DB_FILE)
            return "DB removed"
        except Exception as e:
            return f"Failed: {e}", 500
    return "Forbidden", 403

# Endpoint that demonstrates insecure eval usage
@app.route('/eval', methods=['POST'])
def insecure_eval():
    code = request.form.get('code', '')
    # INSECURE: eval on user-supplied code
    try:
        result = eval(code, {"__builtins__": None}, {})
        return jsonify({"result": str(result)})
    except Exception as e:
        return f"Eval error: {e}", 400

if __name__ == '__main__':
    # A05: Debug mode enabled — will show stack traces and auto-reload (INSECURE)
    app.run(host='0.0.0.0', port=5000, debug=True)
