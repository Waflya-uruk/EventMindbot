import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    
    def __init__(self):
        from config import Config
        self.config = Config.get_config()
    
    def send_verification_email(self, email: str, code: str) -> bool:
        """
        Send verification code to email using SMTP
        """
        try:
            # Создаем письмо
            message = self._create_email_message(email, code)
            
            # Отправляем письмо
            self._send_smtp_email(message)
            
            logger.info(f"Verification code sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")
            return False
    
    def _create_email_message(self, to_email: str, code: str) -> MIMEMultipart:
        """Create email message"""
        message = MIMEMultipart('alternative')
        message['From'] = self.config['email_from']
        message['To'] = to_email
        message['Subject'] = 'Код подтверждения email'
        
        # HTML версия письма
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 10px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px;
                    text-align: center;
                    border-radius: 5px;
                }}
                .code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #4CAF50;
                    text-align: center;
                    padding: 20px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    font-size: 12px;
                    color: #777;
                    text-align: center;
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px solid #ddd;
                }}
                .warning {{
                    color: #ff6b6b;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Подтверждение email</h2>
                </div>
                
                <p>Здравствуйте!</p>
                
                <p>Вы запросили регистрацию в нашем сервисе. Для подтверждения email адреса используйте код:</p>
                
                <div class="code">
                    {code}
                </div>
                
                <p>Этот код действителен в течение <strong>5 минут</strong>.</p>
                
                <p class="warning">
                    ⚠️ Если вы не запрашивали регистрацию, просто проигнорируйте это письмо.
                </p>
                
                <div class="footer">
                    <p>С уважением,<br>Команда поддержки</p>
                    <p>Это автоматическое сообщение, пожалуйста, не отвечайте на него.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Текстовая версия письма (для почтовых клиентов без HTML)
        text_content = f"""
        Подтверждение email
        
        Здравствуйте!
        
        Вы запросили регистрацию в нашем сервисе. Для подтверждения email адреса используйте код:
        
        {code}
        
        Этот код действителен в течение 5 минут.
        
        Если вы не запрашивали регистрацию, просто проигнорируйте это письмо.
        
        ---
        С уважением,
        Команда поддержки
        """
        
        # Добавляем обе версии
        part_text = MIMEText(text_content, 'plain', 'utf-8')
        part_html = MIMEText(html_content, 'html', 'utf-8')
        
        message.attach(part_text)
        message.attach(part_html)
        
        return message
    
    def _send_smtp_email(self, message: MIMEMultipart) -> None:
        """Send email via SMTP"""
        try:
            # Создаем SSL контекст
            context = ssl.create_default_context()
            
            # Для Gmail и большинства серверов используем TLS
            if self.config['smtp_port'] == 587:
                with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                    server.starttls(context=context)
                    server.login(self.config['smtp_username'], self.config['smtp_password'])
                    server.send_message(message)
            # Для порта 465 используем SSL
            elif self.config['smtp_port'] == 465:
                with smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'], context=context) as server:
                    server.login(self.config['smtp_username'], self.config['smtp_password'])
                    server.send_message(message)
            else:
                raise ValueError(f"Unsupported SMTP port: {self.config['smtp_port']}")
                
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            raise