import logging
from typing import Tuple, Optional

from models import User
from services.email.validators import Validators
from services.email_service import EmailService
from services.verification_service import VerificationService
from database import save_user, get_user_by_email, update_user_verification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthService:
    
    def __init__(self):
        self.validators = Validators()
        self.email_service = EmailService()
        self.verification_service = VerificationService()
    
    def register(self, email: str, password: str) -> Tuple[bool, Optional[str]]:
        """Register new user"""
        try:
            # Validate email
            is_valid, error = self.validators.validate_email(email)
            if not is_valid:
                return False, error
            
            # Validate password
            is_valid, error = self.validators.validate_password(password)
            if not is_valid:
                return False, error
            
            # Check if user already exists
            existing_user = get_user_by_email(email)
            if existing_user:
                return False, "Пользователь с таким email уже существует"
            
            # Create user
            user = User(email, password, is_verified=False)
            save_user(user)
            
            # Create verification code
            code, error = self.verification_service.create_verification_code(email)
            if error:
                return False, error
            
            # Send verification email
            print(f"\n📧 Отправка кода подтверждения на {email}...")
            if not self.email_service.send_verification_email(email, code):
                return False, "Не удалось отправить письмо с подтверждением. Проверьте настройки SMTP."
            
            logger.info(f"User registered successfully: {email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return False, f"Registration failed: {str(e)}"
    
    def verify_email(self, email: str, code: str) -> Tuple[bool, Optional[str]]:
        """Verify email with code"""
        try:
            # Validate code format
            is_valid, error = self.validators.validate_verification_code(code)
            if not is_valid:
                return False, error
            
            # Verify code
            is_valid, error = self.verification_service.verify_code(email, code)
            if not is_valid:
                return False, error
            
            # Update user verification status
            success, error = update_user_verification(email, True)
            if not success:
                return False, error
            
            logger.info(f"Email verified: {email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return False, f"Verification failed: {str(e)}"
    
    def resend_verification_code(self, email: str) -> Tuple[bool, Optional[str]]:
        """Resend verification code"""
        try:
            # Validate email
            is_valid, error = self.validators.validate_email(email)
            if not is_valid:
                return False, error
            
            # Check if user exists and not verified
            user = get_user_by_email(email)
            if not user:
                return False, "Пользователь не найден"
            
            if user.is_verified:
                return False, "Email уже подтвержден"
            
            # Resend verification code
            code, error = self.verification_service.resend_verification(email)
            if error:
                return False, error
            
            # Send verification email
            print(f"\n📧 Повторная отправка кода на {email}...")
            if not self.email_service.send_verification_email(email, code):
                return False, "Не удалось отправить письмо с подтверждением"
            
            logger.info(f"Verification code resent to: {email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Resend failed: {str(e)}")
            return False, f"Resend failed: {str(e)}"