from .token_dict import TokenDict
import secrets

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