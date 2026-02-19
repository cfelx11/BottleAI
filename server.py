from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os

app = Flask(__name__)
app.secret_key = "bottle_ai_secret"
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = 'database.db'

# -------------------- Database --------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_user(username, password, role='user'):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = generate_password_hash(password)
    token = secrets.token_hex(16)
    cursor.execute("INSERT INTO users (username, password, role, token) VALUES (?,?,?,?)",
                   (username, hashed, role, token))
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, role, token FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return user
    return None

# -------------------- Routes --------------------
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        create_user(username, password)
        flash("User registered successfully!")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        flash("Invalid username or password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT prediction, created_at FROM logs WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    logs = cursor.fetchall()
    # Count GOOD/CRUMPLED
    cursor.execute("SELECT COUNT(*) FROM logs WHERE user_id=? AND prediction='GOOD'", (user_id,))
    good_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM logs WHERE user_id=? AND prediction='CRUMPLED'", (user_id,))
    crumpled_count = cursor.fetchone()[0]
    conn.close()
    return render_template('dashboard.html', user=user, logs=logs, good_count=good_count, crumpled_count=crumpled_count)

# -------------------- Admin --------------------
@app.route('/admin')
def admin():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('admin.html', users=users)

# -------------------- ESP32 API --------------------
@app.route('/api/classify', methods=['POST'])
def api_classify():
    data = request.json
    user_token = data.get('token')
    prediction = data.get('prediction')  # GOOD or CRUMPLED
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE token=?", (user_token,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"status":"error","message":"Invalid token"}), 401
    user_id = user['id']
    cursor.execute("INSERT INTO logs (user_id, prediction, created_at) VALUES (?,?,?)",
                   (user_id, prediction, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    # Emit SocketIO event for dashboard real-time update
    socketio.emit('update_dashboard', {'user_id': user_id, 'prediction': prediction})
    return jsonify({"status":"ok"})

# -------------------- Run --------------------
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
