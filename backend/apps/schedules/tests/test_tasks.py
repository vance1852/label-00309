"""Tests for schedule Celery tasks."""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.schedules.models import InspectionSchedule
from apps.schedules.tasks import run_scheduled_inspection
from apps.servers.models import Server


User = get_user_model()


class RunScheduledInspectionTaskTests(TestCase):
    """Test cases for run_scheduled_inspection Celery task."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1,
            inspection_command='df -h',
            is_active=True
        )
        self.server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        self.server.set_password('test_password')
        self.server.save()

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_success(self, mock_service_class):
        """Test scheduled inspection runs successfully."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        result = run_scheduled_inspection()
        
        self.assertEqual(result['success'], 1)
        self.assertEqual(result['failed'], 0)

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_no_active_schedule(self, mock_service_class):
        """Test task returns early when no active schedule."""
        self.schedule.is_active = False
        self.schedule.save()
        
        result = run_scheduled_inspection()
        
        self.assertIsNone(result)
        mock_service_class.assert_not_called()

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_no_schedule(self, mock_service_class):
        """Test task returns early when no schedule exists."""
        InspectionSchedule.objects.all().delete()
        
        result = run_scheduled_inspection()
        
        self.assertIsNone(result)
        mock_service_class.assert_not_called()

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_no_servers(self, mock_service_class):
        """Test task returns early when no active servers."""
        Server.objects.all().delete()
        
        result = run_scheduled_inspection()
        
        self.assertIsNone(result)
        mock_service_class.assert_not_called()

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_no_active_servers(self, mock_service_class):
        """Test task returns early when no active servers."""
        self.server.is_active = False
        self.server.save()
        
        result = run_scheduled_inspection()
        
        self.assertIsNone(result)
        mock_service_class.assert_not_called()

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_uses_schedule_command(self, mock_service_class):
        """Test task uses command from schedule."""
        self.schedule.inspection_command = 'custom_command'
        self.schedule.save()
        
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        run_scheduled_inspection()
        
        # Verify the custom command was used
        call_args = mock_service.execute_inspection.call_args
        self.assertEqual(call_args[0][1], 'custom_command')

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_user_is_none(self, mock_service_class):
        """Test task passes None as user for scheduled inspections."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        run_scheduled_inspection()
        
        # Verify user is None
        call_args = mock_service.execute_inspection.call_args
        self.assertIsNone(call_args[0][2])

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_is_scheduled_flag(self, mock_service_class):
        """Test task passes is_scheduled=True."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        run_scheduled_inspection()
        
        # Verify is_scheduled=True was passed
        call_args = mock_service.execute_inspection.call_args
        self.assertEqual(call_args[1]['is_scheduled'], True)

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_updates_last_run(self, mock_service_class):
        """Test task updates schedule's last_run time."""
        from django.utils import timezone
        
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        self.assertIsNone(self.schedule.last_run)
        
        run_scheduled_inspection()
        
        self.schedule.refresh_from_db()
        self.assertIsNotNone(self.schedule.last_run)
        # last_run should be close to current time
        time_diff = timezone.now() - self.schedule.last_run
        self.assertLess(time_diff.total_seconds(), 5)

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_multiple_servers(self, mock_service_class):
        """Test task handles multiple servers."""
        server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.101',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        result = run_scheduled_inspection()
        
        self.assertEqual(result['success'], 2)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(mock_service.execute_inspection.call_count, 2)

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_partial_failure(self, mock_service_class):
        """Test task handles partial failure."""
        server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.101',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        
        mock_service = MagicMock()
        
        def side_effect(server, command, user, is_scheduled):
            mock_record = MagicMock()
            if server.name == 'Test Server':
                mock_record.status = 'success'
            else:
                mock_record.status = 'failed'
            return mock_record
        
        mock_service.execute_inspection.side_effect = side_effect
        mock_service_class.return_value = mock_service
        
        result = run_scheduled_inspection()
        
        self.assertEqual(result['success'], 1)
        self.assertEqual(result['failed'], 1)

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_all_failures(self, mock_service_class):
        """Test task handles all failures."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'failed'
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        result = run_scheduled_inspection()
        
        self.assertEqual(result['success'], 0)
        self.assertEqual(result['failed'], 1)

    @patch('apps.inspections.services.InspectionService')
    @patch('apps.schedules.tasks.logger')
    def test_run_scheduled_inspection_exception_handling(self, mock_logger, mock_service_class):
        """Test task handles exceptions."""
        mock_service = MagicMock()
        mock_service.execute_inspection.side_effect = Exception('SSH Error')
        mock_service_class.return_value = mock_service
        
        result = run_scheduled_inspection()
        
        self.assertEqual(result['success'], 0)
        self.assertEqual(result['failed'], 1)
        mock_logger.error.assert_called()

    @patch('apps.inspections.services.InspectionService')
    def test_run_scheduled_inspection_mixed_results(self, mock_service_class):
        """Test task with mixed results including warnings."""
        server2 = Server.objects.create(
            name='Server 2',
            ip_address='192.168.1.101',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        server3 = Server.objects.create(
            name='Server 3',
            ip_address='192.168.1.102',
            port=22,
            ssh_username='root',
            is_active=True,
            created_by=self.user
        )
        
        mock_service = MagicMock()
        
        statuses = ['success', 'warning', 'failed']
        call_count = [0]
        
        def side_effect(server, command, user, is_scheduled):
            mock_record = MagicMock()
            mock_record.status = statuses[call_count[0] % 3]
            call_count[0] += 1
            return mock_record
        
        mock_service.execute_inspection.side_effect = side_effect
        mock_service_class.return_value = mock_service
        
        result = run_scheduled_inspection()
        
        # success and warning are counted as success
        self.assertEqual(result['success'], 2)
        self.assertEqual(result['failed'], 1)

    @patch('apps.inspections.services.InspectionService')
    @patch('apps.schedules.tasks.logger')
    def test_run_scheduled_inspection_logs_completion(self, mock_logger, mock_service_class):
        """Test task logs completion message."""
        mock_service = MagicMock()
        mock_record = MagicMock()
        mock_record.status = 'success'
        mock_service.execute_inspection.return_value = mock_record
        mock_service_class.return_value = mock_service
        
        run_scheduled_inspection()
        
        mock_logger.info.assert_called()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('Scheduled inspection completed', log_message)
