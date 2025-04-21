from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, flash
from helper_scripts.db_utils import DBManager
import helper_scripts.db_init as db_init
import pathlib as pl
import datetime
import os
import sys
import secrets
# from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(101432 ^ 10203)

DB_PATH = '/evanr/ece464.sqlite3'
ARTICLES_PATH = pl.Path('/evanr')
db = DBManager(DB_PATH, ARTICLES_PATH)

# @app.route('/api/create_user', methods=['POST'])
# def create_user_api():
#     data = request.json
#     success, message = db.create_user(data['username'], data['password'])
#     return jsonify({'success': success, 'message': message})

# @app.route('/api/login', methods=['POST'])
# def login_api():
#     data = request.json
#     success, token = db.log_in(data['username'], data['password'])
#     return jsonify({'success': success, 'token': token})

# @app.route('/api/logout', methods=['POST'])
# def logout_api():
#     data = request.json
#     success, message = db.log_out(token=data['token'])
#     return jsonify({'success': success, 'message': message})

# @app.route('/api/create_article', methods=['POST'])
# def create_article_api():
#     data = request.json
#     try:
#         pub_date = datetime.datetime.strptime(data['publish_date'], '%Y-%m-%d').date()
#     except ValueError:
#         return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'})
#     success, result = db.create_article(data['token'], data['content'], data['title'], pub_date, data['authors'])
#     return jsonify({'success': success, 'result': result})

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

@app.route('/home', methods=['GET', 'POST'])
def home():
    token = request.cookies.get('session_token')
    if not token:
        return redirect(url_for('login'))
    user_id = db.session_manager.validate_session(token)
    if user_id == -1:
        return redirect(url_for('login'))
    results = []
    error = None
    if request.method == 'POST':
        title = request.form.get('title', '')
        try:
            limit = int(request.form.get('limit', 5))
            limit = max(1, min(limit, 20))
        except ValueError:
            limit = 5
        success, result = db.search_articles_by_title(title, limit)
        if success:
            results = result
        else:
            error = result
    recent_articles = db.get_most_recent_articles(3)
    return render_template('home.html', results=results, recent_articles=recent_articles, error=error)

@app.route('/article/<int:article_id>', methods=['GET', 'POST'])
def view_article(article_id):
    token = request.cookies.get('session_token')
    if not token:
        return redirect(url_for('login'))
    user_id = db.session_manager.validate_session(token)
    if user_id == -1:
        return redirect(url_for('login'))
    summary = None
    show_summary = False
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'summarize':
            show_summary = True
            success, result = db.get_article_summary(token, article_id)
            if success:
                summary = result
            else:
                error = result
        elif action == 'hide_summary':
            show_summary = False
        elif action == 'recommend':
            success, result = db.get_recommended_article(article_id, user_id)
            if success:
                return redirect(url_for('view_article', article_id=result))
            else:
                error = result

    success, article_text = db.get_article_text(article_id)
    if not success:
        return f'Error: {article_text}', 404
    cursor = db.conn.execute('SELECT title, authors_str, publish_day, publish_month, publish_year FROM articles WHERE article_id = ?;', (article_id,))
    result = cursor.fetchone()
    if result:
        title, authors, day, month, year = result
        publish_date = f'{month:02}/{day:02}/{year}'
    else:
        title = f'Article #{article_id}'
        authors = 'Unknown Author'
        publish_date = 'Unknown Publication Date'
    user_id = db.session_manager.validate_session(token)
    if not db.log_article_read(user_id, article_id):
        error = 'Failed to log article read.'
    return render_template('article.html', article_id=article_id, article_text=article_text, title=title, authors=authors, publish_date=publish_date, summary=summary, show_summary=show_summary, error=error)


@app.route('/create', methods=['GET', 'POST'])
def create_article():
    token = request.cookies.get('session_token')
    if not token or db.session_manager.validate_session(token) == -1:
        return redirect(url_for('login'))

    error = None
    if request.method == 'POST':
        title = request.form['title']
        authors = request.form['authors']
        content = request.form['content']
        date = datetime.date.today()
        success, result = db.create_article(token, content, title, date, authors)
        if success:
            return redirect(url_for('view_article', article_id=result))
        else:
            error = result
    return render_template('create_article.html', error=error)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    token = request.cookies.get('session_token')
    if not token:
        return redirect(url_for('login'))
    user_id = db.session_manager.validate_session(token)
    if not token or user_id == -1:
        return redirect(url_for('login'))
    username = db.get_username_by_id(user_id)
    if request.method == 'POST':
        article_id = int(request.form.get('article_id'))
        success, message = db.delete_article(token, article_id)
        if not success:
            flash(message or 'Failed to delete article.', 'error')
        return redirect(url_for('profile'))
    cursor = db.conn.execute(
        'SELECT article_id, title FROM articles WHERE submitter_user_id = ? AND active = 1 ORDER BY submitted_timestamp DESC;',
        (user_id,)
    )
    articles = cursor.fetchall()
    return render_template('profile.html', username=username, articles=articles)

@app.route('/')
def catch_all():
    return redirect(url_for('home'))

if __name__ == '__main__':
    try:
        # if not os.path.exists(DB_PATH):
        if not db_init.db_init(DB_PATH, './WebApp/db_init.sql'):
            raise Exception('Unable to initialize database\n')
    except Exception as e:
        sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
    except KeyboardInterrupt as k:
        sys.stderr.write(f'KeyboardInterrupt: {str(k)}')
        sys.stderr.write('User Interrupt\n')
    else:
        print('Starting Flask app...', flush=True)
        app.run(host='0.0.0.0', port=5000, debug=True)