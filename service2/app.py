from flask import jsonify, request, render_template
from functools import wraps
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
SERVICE1_URL = 'http://service1:5000/verify-token'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[len('Bearer '):]
                app.logger.info(f'Token from Authorization: {token[:10]}...')
        elif request.form.get('token'):
            token = request.form.get('token')
            app.logger.info(f'Token from form: {token[:10]}...')
        if not token:
            app.logger.warning('Token is missing in request')
            return jsonify({'message': 'Token is missing'}), 401
        try:
            response = requests.post(SERVICE1_URL, json={'token': token}, timeout=5)
            if response.status_code != 200:
                app.logger.error(f'Verify-token failed: {response.json()}')
                return jsonify(response.json()), response.status_code
            kwargs['user_data'] = response.json()
            app.logger.info(f'User data received: {kwargs["user_data"]}')
        except requests.RequestException as e:
            app.logger.error(f'Failed to verify token: {str(e)}')
            return jsonify({'message': 'Failed to verify token'}), 500
        return f(*args, **kwargs)
    return decorated

@app.route('/', methods=['GET', 'POST'])
def home():
    user_data = None
    token = request.form.get('token') or (request.headers.get('Authorization') or '').replace('Bearer ', '')
    if token:
        app.logger.info(f'Token received in home: {token[:10]}...')
        try:
            response = requests.post(SERVICE1_URL, json={'token': token}, timeout=5)
            if response.status_code == 200:
                user_data = response.json()
                app.logger.info(f'User data in home: {user_data}')
        except requests.RequestException as e:
            app.logger.error(f'Failed to verify token in home: {str(e)}')
    else:
        app.logger.warning('No token in home request')
    return render_template('index.html', user_data=user_data, token=token)

@app.route('/protected', methods=['GET', 'POST'])
@token_required
def protected(user_data):
    return render_template('protected.html', username=user_data['username'], email=user_data['email'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)