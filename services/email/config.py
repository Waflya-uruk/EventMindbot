import os


class Config:
    SECRET_KEY = 'your-secret-key-here-change-in-production'
    
    SMTP_SERVER = 'smtp.yandex.ru'
    SMTP_PORT = 587
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")  # Ваш email
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")    # Пароль приложения
    EMAIL_FROM = 'Команда EventMind(3)'     # Email отправителя
    
    VERIFICATION_CODE_EXPIRY = 300
    VERIFICATION_CODE_LENGTH = 6
    
    # Session settings
    SESSION_EXPIRY = 3600
    
    @classmethod
    def get_config(cls):
        return {
            'secret_key': cls.SECRET_KEY,
            'smtp_server': cls.SMTP_SERVER,
            'smtp_port': cls.SMTP_PORT,
            'smtp_username': cls.SMTP_USERNAME,
            'smtp_password': cls.SMTP_PASSWORD,
            'email_from': cls.EMAIL_FROM,
            'verification_expiry': cls.VERIFICATION_CODE_EXPIRY,
            'verification_length': cls.VERIFICATION_CODE_LENGTH
        }