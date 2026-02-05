import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_addr = settings.email_from

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str = None,
    ) -> bool:
        if not self.user or not self.password:
            logger.warning("SMTP credentials not configured, skipping email send")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.from_addr
            message["To"] = to
            message["Subject"] = subject

            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            raise


email_sender = EmailSender()
