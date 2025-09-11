# app/app.py
# Deliberately insecure Flask demo app focusing on:
# - A04: Insecure Design (weak logic)
# - A05: Security Misconfiguration (debug, hardcoded secrets)
# - A06: Vulnerable & Outdated Components (old deps in requirements.txt)

from flask import Flask, request, session, redirect, url_for, render_template_string

app = Flask(__name__)
app.secret_key = "12345"  # A05: Hardcoded secret (INSECURE)

# fake user store (purposefully minimal / insecure)
USERS = {
    "alice": {"account_id": "acct-alice", "balance": 1000},
    "bob":   {"account_id": "acct-bob",   "balance": 500},
}

# Home
@app.route('/')
def index():
    user = session.get("user")
    if user:
        return f"Hello {user}! <a href='/logout'>Logout</a><br><a href='/transfer_form'>Transfer</a>"
    return "Hello Guest! <a href='/login'>Login</a>"

# A04: Insecure Design - Weak Login (no password)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        # NO password verification - intentionally insecure
        if username in USERS:
            session['user'] = username
            return redirect(url_for('index'))
        return "Unknown user", 401
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            Username: <input type="text" name="username"><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# A04: Insecure Design - Broken Transfer Logic (no account ownership verification)
@app.route('/transfer_form')
def transfer_form():
    return render_template_string('''
        <h2>Transfer Money</h2>
        <form method="post" action="/transfer">
            To Account: <input type="text" name="to_account"><br>
            Amount: <input type="number" name="amount"><br>
            <input type="submit" value="Transfer">
        </form>
    ''')

@app.route('/transfer', methods=['POST'])
def transfer():
    user = session.get("user")
    to_account = request.form.get('to_account')
    amount = request.form.get('amount')

    # INTENTIONALLY INSECURE:
    # - no check that "user" owns the source account
    # - no validation of "to_account" (attacker could target internal accounts)
    # - no CSRF protection
    if user is None:
        return "Not logged in", 401

    # simulate "transfer"
    try:
        amount_val = float(amount)
    except Exception:
        return "Invalid amount", 400

    # Unchecked transfer - insecure business logic
    USERS[to_account]['balance'] += amount_val  # may raise KeyError
    return f"Transferred {amount_val} to {to_account} (initiated by {user})"

# Example admin endpoint (debug info leak risk)
@app.route('/admin')
def admin():
    # Reveals internal state (INSECURE)
    return {
        "debug": app.debug,
        "session": dict(session),
        "users": USERS  # intentionally returning internal user data
    }

if __name__ == '__main__':
    # A05: Debug mode enabled — will show stack traces and auto-reload (INSECURE)
    app.run(host='0.0.0.0', port=5000, debug=True)
