import sqlite3 as sq3
from .session_manager import SessionManager
from .text_summarizer import TextSummarizer
import sys
import time
import datetime
import string
import pickle
import numpy as np
import os
import pathlib as pl

class DBManager:
    # initializes a connection with the database
    # on failure will retry every retry_delay_seconds seconds 
    # and up to connection_retries times until success or raised error 
    def __init__(self, db_path: str, path_to_articles: pl.Path, connection_retries: int = 4, retry_delay_seconds: float | int = 5.0, remove_file_on_delete_article: bool = False, summary_num_senteces: int = 5) -> None:
        self.HEXCHARS = set(string.hexdigits)
        self.USERNAMECHARS = set(string.ascii_letters + string.digits + '_')
        self.session_manager: SessionManager = SessionManager()
        self.text_summarizer: TextSummarizer = TextSummarizer(summary_num_senteces)
        self.path_to_articles: pl.Path = path_to_articles
        self.remove_file_on_delete_article: bool = remove_file_on_delete_article
        self.AUTHORCHARS = set(string.ascii_letters + string.digits + string.punctuation + string.whitespace) - {'<', '>'}
        self.TITLECHARS = set(string.ascii_letters + string.digits + string.punctuation + string.whitespace) - {'<', '>'}
        self.ARTICLETEXTCHARS = set(string.ascii_letters + string.digits + string.punctuation + string.whitespace) - {'<', '>'}
        for i in range(connection_retries):
            if i != 0:
                sys.stderr.write('Retrying connection...\n')
            try:
                self.conn: sq3.Connection = sq3.connect(db_path)
            except Exception as e:
                sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
                sys.stderr.write(f'Database connection failed (attempt {i+1}/{connection_retries}), will retry connection in {retry_delay_seconds} seconds.\n')
            else:
                break # no error means successful connection
            time.sleep(retry_delay_seconds)
        else:
            raise sq3.DatabaseError('Could not connect to database.\n')
        self.user_actions: dict[str, int] = {
            'CREATE' : 1,
            'DEACTIVATE' : 2,
            'LOGIN' : 3,
            'LOGOUT' : 4,
        }
        self.article_actions: dict[str, int] = {
            'CREATE' : 1,
            'DELETE' : 2,
            'GENERATE_SUMMARY' : 3,
        }
    
    def __del__(self):
        try:
            self.conn.commit()
            self.conn.close()
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            
    def serialize_vector(vector: np.ndarray) -> bytes:
        return pickle.dumps(vector)

    def deserialize_vector(data: bytes) -> np.ndarray:
        return pickle.loads(data)
    
    # USER FUNCTIONS

    def log_user_action(self, user_id: int, user_action_id: int) -> bool:
        try:
            self.conn.execute(
                f'INSERT INTO user_logs (user_id, log_action_id) VALUES ({user_id}, {user_action_id});'
            )
            self.conn.commit()
            return True
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to log user action with {user_id=} and {user_action_id=} at {datetime.datetime.now()}.\n')
        return False
    
    def create_user(self, username: str, encrypted_password: str) -> tuple[bool, str | None]:
        if not all([
            len(username) >= 4,
            len(username) <= 16,
            all([i in self.USERNAMECHARS for i in username]),
        ]):
            return (False, 'Username Error') 
        if not all([
            len(encrypted_password) >= 8,
            len(encrypted_password) <= 32,
            all([i in self.HEXCHARS for i in encrypted_password]),
        ]):
            return (False, 'Password Error')
        try:
            cursor: sq3.Cursor = self.conn.execute(
                f'SELECT COUNT(*) AS cnt FROM users WHERE username = \'{username}\' AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to check if username is unique.\n')
            return (False, 'User Creation Error')
        username_match_count_series: tuple[int] | None = cursor.fetchone()
        if not username_match_count_series:
            return (False, 'User Creation Error')
        elif username_match_count_series[0] > 0:
            return (False, 'Username Already Exists')
        try:
            self.conn.execute(
                f'INSERT INTO users (username, encrypted_passkey) VALUES (\'{username}\', \'{encrypted_password}\');'
            )
            self.conn.commit()
            cursor.execute(
                f'SELECT user_id FROM users WHERE username = \'{username}\' AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to create user.\n')
            return (False, 'User Creation Error')
        user_id: int | None = cursor.fetchone()
        if not user_id:
            return (False, 'User Creation Error')
        cursor.close()
        if not self.log_user_action(user_id[0], self.user_actions['CREATE']):
            return (False, 'User Creation Logging Error')
        return (True, None)
    
    def deactivate_user(self, token: str, encrypted_password: str) -> tuple[bool, str | None]:
        user_id: int = self.session_manager.validate_session(token)
        if user_id == -1:
            return (False, 'Invalid Session')
        cursor: sq3.Cursor = self.conn.cursor()
        try:
            cursor.execute(
                f'SELECT COUNT(*) AS cnt FROM users WHERE user_id = {user_id} AND encrypted_password = \'{encrypted_password}\' AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to validate password.\n')
            return (False, 'User Deactivation Error')
        user_exists_series: tuple[int] | None = cursor.fetchone()
        cursor.close()
        if not user_exists_series:
            return (False, 'User Creation Error')
        if user_exists_series[0] <= 0:
            return (False, 'Password Error')
        try:
            self.conn.execute(
                f'UPDATE users SET active = 0 WHERE user_id = {user_id} AND active = 1;'
            )
            self.conn.commit()
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to deactivate user.\n')
            return (False, 'User Deactivation Error')
        log_out_status = self.log_out(user_id)
        if not log_out_status[0]:
            return log_out_status
        if not self.log_user_action(user_id, self.user_actions['DEACTIVATE']):
            return (False, 'User Deactivation Logging Error')
        return (True, None)
            
    def log_in(self, username: str, encrypted_password: str) -> tuple[bool, str | None]:
        cursor: sq3.Cursor = self.conn.cursor()
        try:
            cursor.execute(
                f'SELECT user_id FROM users WHERE username = \'{username}\' AND encrypted_passkey = \'{encrypted_password}\' AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to validate username or password.\n')
            return (False, 'User Log-In Error')
        user_id_series: tuple[int] | None = cursor.fetchone()
        cursor.close()
        if not user_id_series:
            return (False, 'Username or Password Error')
        user_id = user_id_series[0]
        session_creation_success, token = self.session_manager.register_session(user_id)
        if not session_creation_success:
            return (False, 'User Log-In Error')
        if not self.log_user_action(user_id, self.user_actions['LOGIN']):
            return (False, 'User Log-In Logging Error')
        return (True, token)
    
    def log_out(self, *, user_id: int | None = None, token: str | None = None) -> tuple[bool, str | None]:
        if not self.session_manager.terminate_session(user_id=user_id, token=token):
            return (False, 'User Log-Out Error')
        if not self.log_user_action(user_id, self.user_actions['LOGOUT']):
            return (False, 'User Log-Out Logging Error')
        return (True, None)
    
    # ARTICLE FUNCTIONS

    def log_article_action(self, article_id: int, user_id: int, article_action_id: int) -> bool:
        try:
            self.conn.execute(
                f'INSERT INTO article_logs (article_id, user_id, log_action_id) VALUES ({article_id}, {user_id}, {article_action_id});'
            )
            self.conn.commit()
            return True
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to log article action with {article_id=}, {user_id=} and {article_action_id=} at {datetime.datetime.now()}.\n')
        return False

    def delete_article(self, token: str, article_id: int) -> tuple[bool, str | None]:
        user_id: int = self.session_manager.validate_session(token)
        if user_id == -1:
            return (False, 'Invalid Session')
        cursor: sq3.Cursor = self.conn.cursor()
        try:
            cursor.execute(
                f'SELECT submitter_user_id FROM articles WHERE article_id = {article_id} AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to validate password.\n')
            return (False, 'Article Deletion Error')
        article_owner_id_series: tuple[int] | None = cursor.fetchone()
        cursor.close()
        if not article_owner_id_series:
            return (False, 'Article Not Found')
        if not int(article_owner_id_series[0]) != user_id:
            return (False, 'Article Not Owned By User')
        try:
            self.conn.execute(
                f'UPDATE articles SET active = 0 WHERE article_id = {article_id};'
            )
            self.conn.commit()
            if self.remove_file_on_delete_article:
                article_path: pl.Path = self.path_to_articles / 'articles' / f'{article_id}.txt'
                if os.path.exists(article_path):
                    os.remove('')
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to delete article.\n')
            return (False, 'Article Deletion Error')
        if not self.log_article_action(article_id, user_id, self.article_actions['DELETE']):
            return (False, 'Article Deletion Logging Error')
        return (True, None)
    
    def get_article_text(self, article_id: int) -> tuple[bool, str | None]:
        article_path: pl.Path = self.path_to_articles / 'articles' / f'{article_id}.txt'
        if os.path.exists(article_path):
            try:
                with open(article_path, 'r') as article_file:
                    return (True, article_file.read())
            except Exception as e:
                sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
                sys.stderr.write(f'Unable to fetch articlewith id: {article_id}.\n')
                return (False, 'Unable to get article.')
        else:
            return (False, 'Article does not exist.')
    
    def read_article_text(self, token: str, article_id: int) -> tuple[bool, str | None]:
        user_id: int = self.session_manager.validate_session(token)
        if user_id == -1:
            return (False, 'Invalid Session')
        get_article_text_succes, article_text = self.get_article_text(article_id)
        if not get_article_text_succes:
            return (False, article_text)
        cursor: sq3.Cursor = self.conn.cursor()
        try:
            cursor.execute(
                f'SELECT COUNT(*) AS cnt FROM article_interactions WHERE user_id = {user_id} AND article_id = {article_id};'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to validate read status.\n')
            return (False, 'Unable to fetch article.')
        article_user_interaction_series: tuple[int] | None = cursor.fetchone()
        cursor.close()
        if not article_user_interaction_series:
            return (False, 'Unable to fetch article.')
        if int(article_user_interaction_series[0]) == 0:
            query: str = f'INSERT INTO article_interactions (user_id, article_id, read) VALUES ({user_id}, {article_id}, {1});'
        else:
            query: str = f'UPDATE article_interactions SET read = 1, read_timestamp = CURRENT_TIMESTAMP WHERE user_id = {user_id} AND article_id = {article_id};'
        try:
            self.conn.execute(query)
            self.conn.commit()
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to set read status.\n')
            return (False, 'Unable to fetch article.')
        return (True, article_text)
    
    def get_article_summary(self, token: str, article_id: int) -> tuple[bool, str | None]:
        user_id: int = self.session_manager.validate_session(token)
        if user_id == -1:
            return (False, 'Invalid Session')
        
        summary_path: pl.Path = self.path_to_articles / 'summaries' / f'{article_id}.txt'
        if os.path.exists(summary_path):
            try:
                with open(summary_path, 'r') as summary_file:
                    return (True, summary_file.read())
            except Exception as e:
                sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
                sys.stderr.write(f'Unable to fetch article summary for article with id: {article_id}.\n')
                return (False, 'Unable to get article summary.')
        get_article_text_succes, article_text = self.get_article_text(article_id)
        if not get_article_text_succes:
            return (False, article_text)
        get_summary_succes, summary_text = self.text_summarizer.get_summary(article_text)
        if not get_summary_succes:
            return (False, summary_text)
        if not self.log_article_action(article_id, user_id, self.article_actions['GENERATE_SUMMARY']):
            return (False, 'Summary Generation Logging Error')
        return (True, summary_text)
    
    def create_article(self, token: str, article_text: str, title: str, publish_date: datetime.date, authors: str) -> tuple[bool, str | int | None]:
        # if not (all(
        #     [c in self.AUTHORCHARS for c in authors]
        # ) and all(
        #     [c in self.ARTICLETEXTCHARS for c in article_text]
        # ) and all(
        #     [c in self.TITLECHARS for c in title]
        # )):
        #     return (False, 'Invalid inputs.')
        user_id: int = self.session_manager.validate_session(token)
        if user_id == -1:
            return (False, 'Invalid Session')
        try:
            self.conn.execute(f'INSERT INTO articles (title, authors_str, publish_day, publish_month, publish_year, submitter_user_id) VALUES (\'{title}\', \'{authors}\', {publish_date.day}, {publish_date.month}, {publish_date.year}, {user_id});')
            self.conn.commit()
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to insert new article into database.\n')
            return (False, 'Unable to create article.')
        cursor: sq3.Cursor = self.conn.cursor()
        try:
            cursor.execute(
                f'SELECT article_id AS cnt FROM articles WHERE submitter_user_id = {user_id} ORDER BY submitted_timestamp DESC LIMIT 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to get new article_id.\n')
            return (False, 'Unable to find article_id.')
        article_id_series: tuple[int] | None = cursor.fetchone()
        cursor.close()
        if not article_id_series:
            return (False, 'Unable to find article_id.')
        article_id: int = int(article_id_series[0])
        try:
            article_path: pl.Path = self.path_to_articles / 'articles' / f'{article_id}.txt'
            with open(article_path, 'x') as article_file:
                article_file.write(article_text)
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
            sys.stderr.write(f'Unable to write to file.\n')
            return (False, 'Unable to create article.')
        if not self.log_article_action(article_id, user_id, self.article_actions['CREATE']):
            return (False, 'Article Creation Logging Error')
        return (True, article_id)