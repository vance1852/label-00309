"""Alert models."""
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import hashlib


def get_encryption_key():
    """Generate encryption key from SECRET_KEY."""
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)


class AlertConfig(models.Model):
    """Alert configuration model."""
    smtp_server = models.CharField('SMTP服务器', max_length=200)
    smtp_port = models.PositiveIntegerField('SMTP端口', default=587)
    smtp_username = models.CharField('SMTP用户名', max_length=200)
    smtp_password_encrypted = models.TextField('SMTP密码(加密)')
    sender_email = models.EmailField('发件人邮箱')
    sender_name = models.CharField('发件人名称', max_length=100, default='巡检系统')
    use_tls = models.BooleanField('使用TLS', default=True)
    use_ssl = models.BooleanField('使用SSL', default=False)
    disk_threshold = models.PositiveIntegerField('磁盘告警阈值(%)', default=80)
    is_active = models.BooleanField('是否启用', default=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='更新人'
    )

    class Meta:
        db_table = 'alert_configs'
        verbose_name = '告警配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"告警配置 - {self.smtp_server}"

    def set_password(self, password):
        """Encrypt and store SMTP password."""
        fernet = Fernet(get_encryption_key())
        self.smtp_password_encrypted = fernet.encrypt(password.encode()).decode()

    def get_password(self):
        """Decrypt and return SMTP password."""
        fernet = Fernet(get_encryption_key())
        return fernet.decrypt(self.smtp_password_encrypted.encode()).decode()


class AlertRecipient(models.Model):
    """Alert recipient model."""
    config = models.ForeignKey(
        AlertConfig,
        on_delete=models.CASCADE,
        related_name='recipients',
        verbose_name='告警配置'
    )
    name = models.CharField('收件人名称', max_length=100)
    email = models.EmailField('收件人邮箱')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'alert_recipients'
        verbose_name = '告警收件人'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} <{self.email}>"
