import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.database import SystemConfig

logger = logging.getLogger('db_monitor')

def send_email(to_addresses, subject, body):
    try:
        smtp_host = SystemConfig.query.filter_by(key='smtp_host').first()
        smtp_port = SystemConfig.query.filter_by(key='smtp_port').first()
        smtp_user = SystemConfig.query.filter_by(key='smtp_user').first()
        smtp_pass = SystemConfig.query.filter_by(key='smtp_pass').first()
        smtp_from = SystemConfig.query.filter_by(key='smtp_from').first()

        if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
            logger.warning("SMTP configuration missing")
            return False

        host = smtp_host.value
        port = int(smtp_port.value)
        user = smtp_user.value
        password = smtp_pass.value
        sender = smtp_from.value if smtp_from and smtp_from.value else user
        
        recipients = [addr.strip() for addr in to_addresses.split(',') if addr.strip()]
        if not recipients:
            return False

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if port == 465:
            server = smtplib.SMTP_SSL(host, port)
        else:
            server = smtplib.SMTP(host, port)
            server.ehlo()
            if server.has_extn('STARTTLS'):
                server.starttls()
                server.ehlo()

        try:
            server.login(user, password)
            server.sendmail(sender, recipients, msg.as_string())
            logger.info(f"Email sent to {recipients}")
            return True
        finally:
            server.quit()
            
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

