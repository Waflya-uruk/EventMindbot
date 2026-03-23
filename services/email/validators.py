import re
from typing import Tuple, Optional

class Validators:
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        if not email:
            return False, "Email обязателен"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Неверный формат email"
        
        return True, None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Optional[str]]:
        """Validate password strength"""
        if not password:
            return False, "Пароль обязателен"
        
        if len(password) < 8:
            return False, "Пароль должен содержать минимум 8 символов"
        
        if not any(c.isupper() for c in password):
            return False, "Пароль должен содержать хотя бы одну заглавную букву"
        
        if not any(c.islower() for c in password):
            return False, "Пароль должен содержать хотя бы одну строчную букву"
        
        if not any(c.isdigit() for c in password):
            return False, "Пароль должен содержать хотя бы одну цифру"
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Пароль должен содержать хотя бы один специальный символ"
        
        return True, None
    
    @staticmethod
    def validate_verification_code(code: str) -> Tuple[bool, Optional[str]]:
        """Validate verification code format"""
        if not code:
            return False, "Код подтверждения обязателен"
        
        if len(code) != 6:
            return False, "Код подтверждения должен состоять из 6 цифр"
        
        if not code.isdigit():
            return False, "Код подтверждения должен содержать только цифры"
        
        return True, None