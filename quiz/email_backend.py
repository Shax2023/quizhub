from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class DBEmailBackend(SMTPBackend):
    def open(self):
        try:
            from .models import SiteSettings
            s = SiteSettings.get_settings()
            if s.email_host_user and s.email_host_password:
                self.host = s.email_host
                self.port = s.email_port
                self.username = s.email_host_user
                self.password = s.email_host_password
                self.use_tls = s.email_use_tls
                self.use_ssl = s.email_use_ssl
        except Exception:
            pass
        return super().open()
