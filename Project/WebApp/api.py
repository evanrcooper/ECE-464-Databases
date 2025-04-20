from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
from helper_scripts.db_utils import DBManager
import helper_scripts.db_init as db_init
import pathlib as pl
import datetime
import os
import sys
from werkzeug.security import generate_password_hash

app = Flask(__name__)

DB_PATH = '/evanr/ece464.sqlite3'
ARTICLES_PATH = pl.Path('/evanr')
db = DBManager(DB_PATH, ARTICLES_PATH)

@app.route('/api/create_user', methods=['POST'])
def create_user():
    data = request.json
    success, message = db.create_user(data['username'], data['password'])
    return jsonify({'success': success, 'message': message})

# @app.route('/api/login', methods=['POST'])
# def login():
#     data = request.json
#     success, token = db.log_in(data['username'], data['password'])
#     return jsonify({'success': success, 'token': token})

# @app.route('/api/logout', methods=['POST'])
# def logout():
#     data = request.json
#     success, message = db.log_out(token=data['token'])
#     return jsonify({'success': success, 'message': message})

@app.route('/api/create_article', methods=['POST'])
def create_article():
    data = request.json
    try:
        pub_date = datetime.datetime.strptime(data['publish_date'], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'})
    success, result = db.create_article(data['token'], data['text'], data['title'], pub_date, data['authors'])
    return jsonify({'success': success, 'result': result})

@app.route('/api/get_article', methods=['GET'])
def get_article():
    token = request.args.get('token')
    article_id = request.args.get('article_id')

    if not token or not article_id:
        return jsonify({'success': False, 'message': 'Missing token or article_id'}), 400

    success, result = db.read_article_text(token, int(article_id))
    return jsonify({'success': success, 'result': result})

@app.route('/api/get_summary', methods=['GET'])
def get_summary():
    token = request.args.get('token')
    article_id = request.args.get('article_id')

    if not token or not article_id:
        return jsonify({'success': False, 'message': 'Missing token or article_id'}), 400

    success, result = db.get_article_summary(token, int(article_id))
    return jsonify({'success': success, 'result': result})

# ----------------------------------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_error = None
    signup_error = None
    token = request.cookies.get('session_token')
    if token and db.session_manager.validate_session(token) != -1:
        return redirect(url_for('home'))
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'login':
            username = request.form.get('username')
            password = request.form.get('password')
            success, token_or_msg = db.log_in(username, password)
            if success:
                response = make_response(redirect(url_for('home')))
                response.set_cookie('session_token', token_or_msg, httponly=True, samesite='Lax')
                return response
            else:
                login_error = token_or_msg
        elif form_type == 'signup':
            username = request.form.get('new_username')
            password = request.form.get('new_password')
            success, msg = db.create_user(username, password)
            if success:
                login_success, token = db.log_in(username, password)
                if login_success:
                    response = make_response(redirect(url_for('home')))
                    response.set_cookie('session_token', token, httponly=True, samesite='Lax')
                    return response
                else:
                    signup_error = token
            else:
                signup_error = msg
    return render_template('login.html', login_error=login_error, signup_error=signup_error)

@app.route('/home')
def home():
    token = request.cookies.get('session_token')
    if not token:
        return redirect(url_for('login'))
    user_id = db.session_manager.validate_session(token)
    if user_id == -1:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/logout', methods=['POST'])
def logout():
    token = request.cookies.get('session_token')
    if not token:
        return redirect(url_for('login'))
    user_id = db.session_manager.validate_session(token)
    if user_id == -1:
        return redirect(url_for('login'))
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session_token', '', expires=0)
    success, message = db.log_out(token=request.cookies.get('session_token'))
    if success:
        return response
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    try:
        if not os.path.exists(DB_PATH):
            if not db_init.db_init(DB_PATH, './WebApp/db_init.sql'):
                raise Exception('Unable to initialize database\n')
    except Exception as e:
        sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
    except KeyboardInterrupt as k:
        sys.stderr.write(f'KeyboardInterrupt: {str(k)}')
        sys.stderr.write('User Interrupt\n')
    app.run(host='0.0.0.0', port=5000, debug=True)
