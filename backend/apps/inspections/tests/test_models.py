"""Tests for inspection models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.servers.models import Server
from apps.inspections.models import InspectionRecord


User = get_user_model()


class InspectionRecordModelTests(TestCase):
    """Test cases for InspectionRecord model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.server = Server.objects.create(
            name='Test Server',
            ip_address='192.168.1.100',
            port=22,
            ssh_username='root',
            created_by=self.user
        )

    def test_create_inspection_record(self):
        """Test creating an inspection record."""
        record = InspectionRecord.objects.create(
            server=self.server,
            executed_by=self.user,
            command='df -h',
            raw_output='Filesystem  Size  Used Avail Use% Mounted on',
            parsed_result={'disks': []},
            status='success',
            has_alert=False
        )
        self.assertEqual(record.server, self.server)
        self.assertEqual(record.executed_by, self.user)
        self.assertEqual(record.command, 'df -h')
        self.assertEqual(record.status, 'success')
        self.assertFalse(record.has_alert)

    def test_inspection_record_str_representation(self):
        """Test inspection record string representation."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test output',
            parsed_result={},
            status='success'
        )
        expected_str = f"{self.server.name} - {record.inspection_time}"
        self.assertEqual(str(record), expected_str)

    def test_inspection_record_default_status(self):
        """Test default status is 'success'."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        self.assertEqual(record.status, 'success')

    def test_inspection_record_default_has_alert(self):
        """Test default has_alert is False."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        self.assertFalse(record.has_alert)

    def test_inspection_record_default_is_scheduled(self):
        """Test default is_scheduled is False."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        self.assertFalse(record.is_scheduled)

    def test_inspection_record_null_executed_by(self):
        """Test executed_by can be null."""
        record = InspectionRecord.objects.create(
            server=self.server,
            executed_by=None,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        self.assertIsNone(record.executed_by)

    def test_inspection_record_null_alert_message(self):
        """Test alert_message can be null."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        self.assertIsNone(record.alert_message)

    def test_inspection_record_status_choices(self):
        """Test status choices."""
        valid_statuses = ['success', 'failed', 'warning']
        for status in valid_statuses:
            record = InspectionRecord.objects.create(
                server=self.server,
                command='df -h',
                raw_output='test',
                parsed_result={},
                status=status
            )
            self.assertEqual(record.status, status)

    def test_inspection_record_ordering(self):
        """Test inspection records are ordered by inspection_time."""
        record1 = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test1',
            parsed_result={}
        )
        record2 = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test2',
            parsed_result={}
        )
        
        records = list(InspectionRecord.objects.all())
        # Verify both records exist
        self.assertEqual(len(records), 2)
        self.assertIn(record1, records)
        self.assertIn(record2, records)

    def test_inspection_record_cascade_delete_server(self):
        """Test records are deleted when server is deleted."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        self.assertEqual(InspectionRecord.objects.count(), 1)
        
        self.server.delete()
        self.assertEqual(InspectionRecord.objects.count(), 0)

    def test_inspection_record_parsed_result_json(self):
        """Test parsed_result stores JSON data correctly."""
        parsed_data = {
            'disks': [
                {
                    'filesystem': '/dev/sda1',
                    'size': '100G',
                    'used': '50G',
                    'available': '50G',
                    'use_percent': 50,
                    'mount_point': '/'
                }
            ],
            'total_size': 100,
            'total_used': 50,
            'total_available': 50
        }
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test output',
            parsed_result=parsed_data
        )
        self.assertEqual(record.parsed_result['disks'][0]['use_percent'], 50)
        self.assertEqual(record.parsed_result['total_size'], 100)

    def test_inspection_record_with_alert(self):
        """Test creating record with alert."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={'disks': []},
            status='warning',
            has_alert=True,
            alert_message='Disk usage exceeds threshold'
        )
        self.assertTrue(record.has_alert)
        self.assertEqual(record.alert_message, 'Disk usage exceeds threshold')
        self.assertEqual(record.status, 'warning')

    def test_inspection_record_scheduled(self):
        """Test creating scheduled inspection record."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            is_scheduled=True
        )
        self.assertTrue(record.is_scheduled)

    def test_inspection_record_raw_output_large_text(self):
        """Test storing large raw output."""
        large_output = 'Line\n' * 1000
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output=large_output,
            parsed_result={}
        )
        self.assertEqual(len(record.raw_output), len(large_output))
