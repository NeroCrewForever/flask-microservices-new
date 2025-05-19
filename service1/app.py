import sqlite3
import bcrypt
import jwt
import datetime
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'M$4MMh4563vvv'  # Безопасный ключ
DATABASE = '/app/db/users.db'

def init_db():
    db_dir = os.path.dirname(DATABASE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        hashed = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT OR IGNORE INTO users (username, email, password) VALUES (?, ?, ?)',
                       ('testuser', 'test@example.com', hashed))
        conn.commit()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[len('Bearer '):]
                app.logger.info(f'Token from Authorization: {token[:10]}...')
        elif request.args.get('token'):
            token = request.args.get('token')
            app.logger.info(f'Token from query: {token[:10]}...')
        if not token:
            app.logger.warning('Token is missing in request')
            return jsonify({'error': 'Token is missing'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (data['user_id'],))
                user = cursor.fetchone()
            if not user:
                return jsonify({'error': 'Invalid token'}), 403
            kwargs['user_data'] = {'user_id': user[0], 'username': user[1], 'email': user[2]}
            kwargs['token'] = token
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token is expired'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    user_data = None
    token = (request.headers.get('Authorization') or '').replace('Bearer ', '') or request.args.get('token')
    if token:
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (data['user_id'],))
                user = cursor.fetchone()
            if user:
                user_data = {'user_id': user[0], 'username': user[1], 'email': user[2]}
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass
    return render_template('index.html', user_data=user_data, token=token, other_service_url='http://service2:5000')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                               (username, email, hashed_password))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return jsonify({'message': 'Email already exists'}), 400
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            return jsonify({'message': 'Missing email or password'}), 400
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, password FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            token = jwt.encode({
                'user_id': user[0],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            app.logger.info(f'User logged in: {email}')
            return redirect(url_for('user', token=token))
        return jsonify({'message': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/user')
@token_required
def user(user_data, token):
    return render_template('user.html', username=user_data['username'], email=user_data['email'], token=token)

@app.route('/verify-token', methods=['POST'])
def verify_token():
    token = request.json.get('token')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (data['user_id'],))
            user = cursor.fetchone()
        if not user:
            return jsonify({'message': 'Invalid token'}), 401
        return jsonify({'user_id': user[0], 'username': user[1], 'email': user[2]}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token is expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)