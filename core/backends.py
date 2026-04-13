# core/backends.py
# Custom email backend for development that bypasses SSL certificate issues

import smtplib
import ssl
from django.core.mail.backends.smtp import EmailBackend


class DevelopmentSMTPBackend(EmailBackend):
    """
    Custom SMTP backend for development that handles SSL certificate verification issues.
    Uses verify_certs=False for Gmail SMTP on Windows development environments.
    """
    
    def open(self):
        """
        Ensure an SMTP connection is open. If one already exists, then this method does nothing.
        """
        if self.connection is not None:
            return False
        
        try:
            # Create SSL context that doesn't verify certificates (dev-only)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            self.connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            
            if self.use_tls:
                self.connection.starttls(context=context)
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
        except smtplib.SMTPException as err:
            if not self.fail_silently:
                raise
