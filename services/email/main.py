import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from services.auth_service import AuthService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    auth_service = AuthService()
    
    print("=== Система регистрации по email ===\n")
    
    while True:
        print("\nОпции:")
        print("1. Зарегистрировать нового пользователя")
        print("2. Подтвердить email")
        print("3. Отправить код подтверждения повторно")
        print("4. Выход")
        
        choice = input("\nВыберите опцию (1-4): ").strip()
        
        if choice == '1':
            email = input("Введите email: ").strip()
            password = input("Введите пароль: ").strip()
            
            print("\nРегистрация...")
            success, error = auth_service.register(email, password)
            
            if success:
                print(f"\n✓ Регистрация успешна!")
                print(f"Код подтверждения отправлен на {email}")
                print("Пожалуйста, проверьте вашу почту и подтвердите аккаунт.")
            else:
                print(f"\n✗ Ошибка регистрации: {error}")
        
        elif choice == '2':
            email = input("Введите email: ").strip()
            code = input("Введите код подтверждения: ").strip()
            
            print("\nПодтверждение...")
            success, error = auth_service.verify_email(email, code)
            
            if success:
                print(f"\n✓ Email успешно подтвержден!")
                print("Теперь вы можете войти в свой аккаунт.")
            else:
                print(f"\n✗ Ошибка подтверждения: {error}")
        
        elif choice == '3':
            email = input("Введите email: ").strip()
            
            print("\nОтправка кода подтверждения...")
            success, error = auth_service.resend_verification_code(email)
            
            if success:
                print(f"\n✓ Код подтверждения отправлен на {email}")
                print("Пожалуйста, проверьте вашу почту.")
            else:
                print(f"\n✗ Ошибка отправки кода: {error}")
        
        elif choice == '4':
            print("\nДо свидания!")
            break
        
        else:
            print("\nНеверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main()