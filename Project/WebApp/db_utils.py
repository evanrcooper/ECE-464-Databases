import sqlite3 as sq3
from session_manager import SessionManager
import sys
import time
import datetime
import string
import pickle
import numpy as np

class DBManager:
    # initializes a connection with the database
    # on failure will retry every retry_delay_seconds seconds 
    # and up to connection_retries times until success or raised error 
    def __init__(self, db_path: str, connection_retries: int = 4, retry_delay_seconds: float | int = 5.0) -> None:
        self.HEXCHARS = set(string.hexdigits)
        self.USERNAMECHARS = set(string.ascii_letters + string.digits + '_')
        self.session_manager: SessionManager = SessionManager()
        for i in range(connection_retries):
            if i != 0:
                sys.stderr.write('Retrying connection...\n')
            try:
                self.conn: sq3.Connection = sq3.connect(db_path)
            except Exception as e:
                sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
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
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
            sys.stderr.write(f'Unable to log user action with {user_id=} and {user_action_id=} at {datetime.datetime.now()}.\n')
        return False
    
    def create_user(self, username: str, encrypted_password: str) -> tuple[bool, str | None]:
        if not all(
            len(username) >= 4,
            len(username) <= 16,
            all([i in self.USERNAMECHARS for i in username]),
        ):
            return (False, 'Username Error') 
        if not all(
            len(encrypted_password) >= 8,
            len(encrypted_password) <= 32,
            all([i in self.HEXCHARS for i in encrypted_password]),
        ):
            return (False, 'Password Error')
        try:
            cursor: sq3.Cursor = self.conn.execute(
                f'SELECT COUNT(*) AS cnt FROM users WHERE username = \'{username}\' AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
            sys.stderr.write(f'Unable to check if username is unique.\n')
            return (False, 'User Creation Error')
        username_match_count_series: int | None = cursor.fetchone()
        if not username_match_count_series:
            return (False, 'User Creation Error')
        elif username_match_count_series[0] > 0:
            return (False, 'Username Already Exists')
        try:
            self.conn.execute(
                f'INSERT INTO users (username, encrypted_passkey) VALUES ({username}, {encrypted_password});'
            )
            self.conn.commit()
            cursor.execute(
                f'SELECT user_id FROM users WHERE username = \'{username}\' AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
            sys.stderr.write(f'Unable to create user.\n')
            return (False, 'User Creation Error')
        user_id: int | None = cursor.fetchone()
        if not user_id:
            return (False, 'User Creation Error')
        cursor.close()
        if not self.log_user_action(user_id[0], self.user_actions['CREATE']):
            return (False, 'User Creation Logging Error')
        return (True, '')
    
    def deactivate_user(self, token: str, encrypted_password: str) -> tuple[bool, str | None]:
        user_id: int = self.session_manager.validate_session(token)
        if user_id == -1:
            return (False, 'Invalid Session')
        cursor: sq3.Cursor = self.conn.cursor()
        try:
            cursor.execute(
                f'SELECT COUNT(*) AS cnt FROM users WHERE user_id = {user_id} AND encrypted_password = {encrypted_password} AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
            sys.stderr.write(f'Unable to validate password.\n')
            return (False, 'User Deactivation Error')
        user_exists_series: int | None = cursor.fetchone()
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
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
            sys.stderr.write(f'Unable to deactivate user.\n')
            return (False, 'User Deactivation Error')
        log_out_status = self.log_out(user_id)
        if not log_out_status[0]:
            return log_out_status
        if not self.log_user_action(user_id, self.user_actions['DEACTIVATE']):
            return (False, 'User Deactivation Logging Error')
        return (True, '')
            
    def log_in(self, username: str, encrypted_password: str) -> tuple[bool, str | None]:
        cursor: sq3.Cursor = self.conn.cursor()
        try:
            cursor.execute(
                f'SELECT user_id FROM users WHERE username = {username} AND encrypted_password = {encrypted_password} AND active = 1;'
            )
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
            sys.stderr.write(f'Unable to validate username or password.\n')
            return (False, 'User Log-In Error')
        user_id_series: int | None = cursor.fetchone()
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
        return (True, '')
    
    # ARTICLE FUNCTIONS

    def log_user_action(self, article_id: int, user_id: int, article_action_id: int) -> bool:
        try:
            self.conn.execute(
                f'INSERT INTO article_logs (article_id, user_id, log_action_id) VALUES ({article_id}, {user_id}, {article_action_id});'
            )
            self.conn.commit()
            return True
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
            sys.stderr.write(f'Unable to log article action with {article_id=}, {user_id=} and {article_action_id=} at {datetime.datetime.now()}.\n')
        return False