"""Alert services."""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .models import AlertConfig

logger = logging.getLogger(__name__)


class AlertService:
    """Service for sending alert emails."""

    def get_config(self):
        """Get active alert configuration."""
        return AlertConfig.objects.filter(is_active=True).first()

    def send_alert(self, server, record, message):
        """Send alert email for inspection result."""
        config = self.get_config()
        if not config:
            logger.warning("No active alert configuration found")
            return False

        recipients = config.recipients.filter(is_active=True)
        if not recipients.exists():
            logger.warning("No active recipients found")
            return False

        subject = f"[告警] 服务器 {server.name} 磁盘巡检告警"
        body = self._build_alert_body(server, record, message)

        recipient_emails = [r.email for r in recipients]
        return self.send_email(config, recipient_emails, subject, body)

    def send_test_email(self, recipient_email):
        """Send test email."""
        config = self.get_config()
        if not config:
            raise Exception("未配置告警邮箱")

        subject = "[测试] 巡检系统邮件测试"
        body = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #409EFF;">邮件测试成功</h2>
            <p>这是一封来自服务器硬盘巡检系统的测试邮件。</p>
            <p>如果您收到此邮件，说明邮件配置正确。</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
        </body>
        </html>
        """
        return self.send_email(config, [recipient_email], subject, body)

    def send_email(self, config, recipients, subject, body):
        """Send email using SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{config.sender_name} <{config.sender_email}>"
            msg['To'] = ', '.join(recipients)

            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)

            if config.use_ssl:
                server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port)
            else:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
                if config.use_tls:
                    server.starttls()

            server.login(config.smtp_username, config.get_password())
            server.sendmail(config.sender_email, recipients, msg.as_string())
            server.quit()

            logger.info(f"Alert email sent to: {', '.join(recipients)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise Exception(f"邮件发送失败: {str(e)}")

    def _build_alert_body(self, server, record, message):
        """Build alert email body."""
        disks_html = ""
        for disk in record.parsed_result.get('disks', []):
            color = '#F56C6C' if disk['use_percent'] >= 80 else '#67C23A'
            disks_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #eee;">{disk['mount_point']}</td>
                <td style="padding: 8px; border: 1px solid #eee;">{disk['filesystem']}</td>
                <td style="padding: 8px; border: 1px solid #eee;">{disk['size']}</td>
                <td style="padding: 8px; border: 1px solid #eee;">{disk['used']}</td>
                <td style="padding: 8px; border: 1px solid #eee;">{disk['available']}</td>
                <td style="padding: 8px; border: 1px solid #eee; color: {color}; font-weight: bold;">{disk['use_percent']}%</td>
            </tr>
            """

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f7fa;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);">
                <h2 style="color: #F56C6C; margin-bottom: 20px;">⚠️ 磁盘告警通知</h2>
                
                <div style="background: #fef0f0; border-left: 4px solid #F56C6C; padding: 12px; margin-bottom: 20px;">
                    <strong>告警信息：</strong>{message}
                </div>
                
                <h3 style="color: #303133;">服务器信息</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 8px; background: #f5f7fa; width: 100px;">服务器名称</td>
                        <td style="padding: 8px;">{server.name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; background: #f5f7fa;">IP地址</td>
                        <td style="padding: 8px;">{server.ip_address}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; background: #f5f7fa;">巡检时间</td>
                        <td style="padding: 8px;">{record.inspection_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
                
                <h3 style="color: #303133;">磁盘详情</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background: #f5f7fa;">
                            <th style="padding: 8px; border: 1px solid #eee; text-align: left;">挂载点</th>
                            <th style="padding: 8px; border: 1px solid #eee; text-align: left;">文件系统</th>
                            <th style="padding: 8px; border: 1px solid #eee; text-align: left;">总容量</th>
                            <th style="padding: 8px; border: 1px solid #eee; text-align: left;">已使用</th>
                            <th style="padding: 8px; border: 1px solid #eee; text-align: left;">可用</th>
                            <th style="padding: 8px; border: 1px solid #eee; text-align: left;">使用率</th>
                        </tr>
                    </thead>
                    <tbody>
                        {disks_html}
                    </tbody>
                </table>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">此邮件由服务器硬盘巡检系统自动发送，请勿回复。</p>
            </div>
        </body>
        </html>
        """
