"""Initialize default data."""
import os
from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.alerts.models import AlertConfig, AlertRecipient
from apps.schedules.models import InspectionSchedule
from apps.servers.models import Server


class Command(BaseCommand):
    help = 'Initialize default data'

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        else:
            admin = User.objects.get(username='admin')
            self.stdout.write('Admin user already exists')

        # Create default alert config
        if not AlertConfig.objects.exists():
            config = AlertConfig(
                smtp_server='smtp.163.com',
                smtp_port=465,
                smtp_username='z18203555732@163.com',
                sender_email='z18203555732@163.com',
                sender_name='巡检系统',
                use_tls=False,
                use_ssl=True,
                disk_threshold=80,
                is_active=True
            )
            config.set_password('WPptKqe2na7GtvsT')
            config.save()
            
            # Add default recipient
            AlertRecipient.objects.create(
                config=config,
                name='测试收件人',
                email='z18203555732@163.com',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Created default alert config'))
        else:
            self.stdout.write('Alert config already exists')

        # Create default schedule
        if not InspectionSchedule.objects.exists():
            InspectionSchedule.objects.create(
                name='每日巡检',
                interval_type='daily',
                interval_value=1,
                execute_time='02:00:00',
                inspection_command='df -h',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Created default schedule'))
        else:
            self.stdout.write('Schedule already exists')

        # Create test server
        # Docker 环境使用容器名，本地开发使用 127.0.0.1
        is_docker = os.environ.get('DB_HOST') == 'mysql'
        test_server_ip = 'test-server' if is_docker else '127.0.0.1'
        
        if not Server.objects.filter(name='测试服务器').exists():
            server = Server(
                name='测试服务器',
                ip_address=test_server_ip,
                port=2222 if not is_docker else 22,
                ssh_username='root',
                description='Docker 测试服务器，用于功能测试',
                is_active=True,
                created_by=admin
            )
            server.set_password('root123')
            server.save()
            self.stdout.write(self.style.SUCCESS(f'Created test server: {test_server_ip}'))
        else:
            # Update existing server IP based on environment
            server = Server.objects.get(name='测试服务器')
            server.ip_address = test_server_ip
            server.port = 2222 if not is_docker else 22
            server.save()
            self.stdout.write(f'Updated test server IP: {test_server_ip}')

        self.stdout.write(self.style.SUCCESS('Data initialization completed'))
