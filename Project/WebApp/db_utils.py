import sqlite3 as sq3
import secrets
import sys
import time
import datetime
import string

# Two Way Dict
class TokenDict:
    def __init__(self) -> None:
        self.token_to_user: dict[str, int] = dict()
        self.user_to_token: dict[str, int] = dict()
    
    # returns -1 if token is not in dict otherwise
    # returns the user_id associated with the token provided
    def get_user_id(self, token) -> int:
        if not self.contains(token=token):
            return -1
        return self.token_to_user[token]
    
    # returns True if successfully inserted otherwise False if 
    # user_id provided is invalid
    def insert(self, user_id: int, token: str) -> bool:
        if user_id < 0:
            return False
        self.token_to_user[token] = user_id
        self.user_to_token[user_id] = token
        return True
    
    # returns None if both or neither of user_id and token are provided otherwise 
    # returns True if provided arg was in dict before deletion and False if not
    def delete(self, *, user_id: int | None = None, token: str | None = None) -> bool | None:
        if (user_id is None) == (token is None):
            return None
        if user_id is not None:
            if not self.contains(user_id=user_id):
                return False
            token = self.user_to_token[user_id]
            del self.user_to_token[user_id]
            del self.token_to_user[token]
            return True
        if token is not None:
            if not self.contains(user_id=user_id):
                return False
            user_id = self.token_to_user[token]
            del self.token_to_user[token]
            del self.user_to_token[user_id]
            return True
        
    # returns None if both or neither of user_id and token are provided otherwise 
    # returns True if provided arg is in dict and False if not
    def contains(self, *, user_id: int | None = None, token: str | None = None) -> bool | None:
        if (user_id is None) == (token is None):
            return None
        if user_id is not None:
            return user_id in self.user_to_token
        if token is not None:
            return token in self.token_to_user

class SessionManager:
    def __init__(self) -> None:
        self.sessions: TokenDict = TokenDict()
        
    def generate_token(self, n: int = 32) -> str:
        return secrets.token_urlsafe(n)
    
    # returns True on success False on failure
    def register_session(self, user_id: str) -> tuple[bool, str]:
        token = self.generate_token()
        return (self.sessions.insert(user_id=user_id, token=token), token)
    
    # returns True on success False on failure
    def terminate_session(self, *, user_id: int | None = None, token: str | None = None) -> bool:
        if (user_id is None) and (token is None):
            return False
        if (token is not None) and (user_id is not None):
            return False
        if user_id is not None:
            return self.sessions.delete(user_id=user_id)
        if token is not None:
            return self.sessions.delete(token=token)
    
    # returns -1 if session is invalid otherwise returns user_id
    def validate_session(self, token: str) -> int:
        return self.sessions.get_user_id(token)

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
    
    def __del__(self):
        try:
            self.conn.commit()
            self.conn.close()
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}\n')
        
    def log_user_action(self, user_id: int, action_id: int) -> bool:
        try:
            self.conn.execute(
                f'INSERT INTO user_logs (user_id, log_action_id) VALUES ({user_id}, {action_id});'
            )
            self.conn.commit()
            return True
        except Exception as e:
            sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
            sys.stderr.write(f'Unable to log user action with {user_id=} and {action_id=} at {datetime.datetime.now()}.\n')
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