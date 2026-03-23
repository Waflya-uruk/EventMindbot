from datetime import datetime
from typing import Optional, Dict, Any

class User:
    def __init__(self, email: str, password_hash: str, is_verified: bool = False):
        self.email = email
        self.password_hash = password_hash
        self.is_verified = is_verified
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'email': self.email,
            'password_hash': self.password_hash,
            'is_verified': self.is_verified,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        user = cls(
            email=data['email'],
            password_hash=data['password_hash'],
            is_verified=data.get('is_verified', False)
        )
        user.created_at = data.get('created_at', datetime.now())
        user.updated_at = data.get('updated_at', datetime.now())
        return user


class VerificationCode:
    def __init__(self, email: str, code: str, expires_at: datetime):
        self.email = email
        self.code = code
        self.expires_at = expires_at
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'email': self.email,
            'code': self.code,
            'expires_at': self.expires_at,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerificationCode':
        return cls(
            email=data['email'],
            code=data['code'],
            expires_at=data['expires_at']
        )
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at