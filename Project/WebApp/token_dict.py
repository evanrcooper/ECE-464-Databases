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