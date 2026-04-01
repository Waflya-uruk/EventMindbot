import os
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY not found in environment variables!")

cipher = Fernet(ENCRYPTION_KEY.encode())


def encrypt_data(plain_text: str) -> str:
    """Шифрует строку (например, пароль приложения Яндекса)."""
    if not plain_text:
        return ""
    return cipher.encrypt(plain_text.encode()).decode()

def decrypt_data(encrypted_text: str) -> str:
    """Расшифровывает строку для использования в API."""
    if not encrypted_text:
        return ""
    return cipher.decrypt(encrypted_text.encode()).decode()



def hash_password(password: str) -> str:
    """Создает безопасный хеш пароля. Обратно расшифровать нельзя."""
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password: str, hashed_password: str) -> bool:
    """Проверяет соответствие введенного пароля сохраненному хешу."""
    return check_password_hash(hashed_password, password)