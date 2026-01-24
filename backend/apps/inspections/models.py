"""Inspection models."""
from django.db import models
from django.conf import settings


class InspectionRecord(models.Model):
    """Inspection record model."""
    STATUS_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('warning', '警告'),
    ]

    server = models.ForeignKey(
        'servers.Server',
        on_delete=models.CASCADE,
        verbose_name='服务器'
    )
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='执行人'
    )
    command = models.TextField('执行命令')
    raw_output = models.TextField('原始输出')
    parsed_result = models.JSONField('解析结果', default=dict)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='success')
    has_alert = models.BooleanField('是否告警', default=False)
    alert_message = models.TextField('告警信息', blank=True, null=True)
    inspection_time = models.DateTimeField('巡检时间', auto_now_add=True)
    is_scheduled = models.BooleanField('是否定时任务', default=False)

    class Meta:
        db_table = 'inspection_records'
        verbose_name = '巡检记录'
        verbose_name_plural = verbose_name
        ordering = ['-inspection_time']

    def __str__(self):
        return f"{self.server.name} - {self.inspection_time}"
