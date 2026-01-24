"""Schedule models."""
from django.db import models
from django.conf import settings


class InspectionSchedule(models.Model):
    """Inspection schedule model."""
    INTERVAL_CHOICES = [
        ('hourly', '每小时'),
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
    ]

    name = models.CharField('任务名称', max_length=100, default='定时巡检')
    interval_type = models.CharField('周期类型', max_length=20, choices=INTERVAL_CHOICES, default='daily')
    interval_value = models.PositiveIntegerField('周期值', default=1, help_text='每隔多少个周期执行')
    execute_time = models.TimeField('执行时间', default='02:00:00')
    execute_day = models.PositiveIntegerField('执行日', default=1, help_text='周几(1-7)或每月几号(1-31)')
    inspection_command = models.TextField('巡检命令', default='df -h')
    is_active = models.BooleanField('是否启用', default=True)
    last_run = models.DateTimeField('上次执行时间', null=True, blank=True)
    next_run = models.DateTimeField('下次执行时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='更新人'
    )

    class Meta:
        db_table = 'inspection_schedules'
        verbose_name = '巡检调度'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} - {self.get_interval_type_display()}"
