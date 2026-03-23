from datetime import datetime, timedelta
import random
import logging
from typing import Optional, Tuple

from config import Config
from models import VerificationCode
from database.db_operations import save_verification_code, get_verification_code, delete_verification_code

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VerificationService:
    
    def __init__(self):
        self.config = Config.get_config()
    
    def generate_code(self) -> str:
        """Generate random verification code"""
        code = ''.join([str(random.randint(0, 9)) for _ in range(self.config['verification_length'])])
        return code
    
    def create_verification_code(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """Create and save verification code for email"""
        try:
            code = self.generate_code()
            expires_at = datetime.now() + timedelta(seconds=self.config['verification_expiry'])
            verification = VerificationCode(email, code, expires_at)
            save_verification_code(verification)
            
            logger.info(f"Verification code created for {email}")
            return code, None
            
        except Exception as e:
            logger.error(f"Failed to create verification code: {str(e)}")
            return None, f"Failed to create verification code: {str(e)}"
    
    def verify_code(self, email: str, code: str) -> Tuple[bool, Optional[str]]:
        """Verify the code for email"""
        try:
            stored_verification = get_verification_code(email)
            
            if not stored_verification:
                return False, "Код подтверждения не найден или истек"
            
            if stored_verification.code != code:
                return False, "Неверный код подтверждения"
            
            if stored_verification.is_expired():
                delete_verification_code(email)
                return False, "Срок действия кода подтверждения истек"
            
            delete_verification_code(email)
            logger.info(f"Email verified successfully for {email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return False, f"Verification failed: {str(e)}"
    
    def resend_verification(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """Resend verification code"""
        delete_verification_code(email)
        return self.create_verification_code(email)