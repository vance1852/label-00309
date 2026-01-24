"""Server models."""
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import hashlib


def get_encryption_key():
    """Generate encryption key from SECRET_KEY."""
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)


class Server(models.Model):
    """Server model for storing server information."""
    name = models.CharField('服务器名称', max_length=100)
    ip_address = models.GenericIPAddressField('IP地址')
    port = models.PositiveIntegerField('SSH端口', default=22)
    ssh_username = models.CharField('SSH用户名', max_length=100)
    ssh_password_encrypted = models.TextField('SSH密码(加密)')
    description = models.TextField('描述', blank=True, null=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'servers'
        verbose_name = '服务器'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    def set_password(self, password):
        """Encrypt and store password."""
        fernet = Fernet(get_encryption_key())
        self.ssh_password_encrypted = fernet.encrypt(password.encode()).decode()

    def get_password(self):
        """Decrypt and return password."""
        fernet = Fernet(get_encryption_key())
        return fernet.decrypt(self.ssh_password_encrypted.encode()).decode()
