import sqlite3 as sq3
import secrets
import sys
import time
import datetime

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
    # dict contained user_id or token before
    def insert(self, user_id: int, token: str) -> bool:
        if self.contains(user_id=user_id) or self.contains(token=token) or (user_id < 0):
            return False
        self.token_to_user[token] = user_id
        self.user_to_token[user_id] = token
        return True
    
    # returns None if both or neither of user_id and token are provided otherwise 
    # returns True if provided arg was in dict before deletion and False if not
    def delete(self, *, user_id: int | None = None, token: str | None = None) -> bool | None:
        if (user_id is None) and (token is None):
            return None
        if (token is not None) and (user_id is not None):
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
        if (user_id is None) and (token is None):
            return None
        if (token is not None) and (user_id is not None):
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
    def register_session(self, user_id: str) -> bool:
        return self.sessions.insert(user_id=user_id, token=self.generate_token())
    
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
        self.HEXCHARS = set('0123456789ABCDEFabcdef')
        for i in range(connection_retries):
            if i != 0:
                sys.stderr.write('Retrying connection...\n')
            try:
                self.conn: sq3.Connection = sq3.connect(db_path)
            except Exception as e:
                sys.stderr.write(e)
                sys.stderr.write(f'Database connection failed (attempt {i+1}/{connection_retries}), will retry connection in {retry_delay_seconds} seconds.\n')
            else:
                break # no error means successful connection
            time.sleep(retry_delay_seconds)
        else:
            raise sq3.DatabaseError('Could not connect to database.\n')
        self.user_actions: dict[int, str] = {
            1 : 'CREATE',
            2 : 'DEACTIVATE',
            3 : 'LOGIN',
            4 : 'LOGOFF',
        }
    
    def log_user_action(self, user_id: int, action_id: int) -> bool:
        try:
            self.conn.execute(
                f'INSERT INTO user_logs (uuid, log_action_id, timestamp) VALUES ({user_id}, {action_id}, datetime(\'now\'));'
            )
            return True
        except Exception as e:
            sys.stderr.write(e)
            sys.stderr.write(f'Unable to log user action with {user_id=} and {action_id=} at {datetime.datetime.now()}.\n')
        return False
    
    def create_user(self, username: str, encrypted_password: str) -> tuple[bool, str | None]:
        cursor = self.conn.cursor()
        cursor.execute(
            f'SELECT COUNT(*) AS cnt FROM users WHERE username = \'{username}\' AND active = 1;'
        )
        username_match_count: int | None = cursor.fetchone()
        if not username_match_count:
            return (False, 'User Creation Error')
        elif username_match_count > 0:
            return (False, 'Username Already Exists')
        if not all(
            len(encrypted_password) < 8,
            len(encrypted_password) > 32,
            all([i in self.HEXCHARS for i in encrypted_password]),
        ):
            return (False, 'Password Error')
        # insert new user into database
        # log user action
        # return true on success
        pass
    
    def deactivate_user(self, token: str, encrypted_password: str) -> tuple[bool, str | None]:
        pass
    
    def log_in(self, username: str, encrypted_password: str) -> tuple[bool, str | None]:
        pass
    
    def log_out(self, *, user_id: int | None = None, token: str | None = None) -> tuple[bool, str | None]:
        pass