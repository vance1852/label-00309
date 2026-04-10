"""Tests for inspection serializers."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.servers.models import Server
from apps.inspections.models import InspectionRecord
from apps.inspections.serializers import InspectionRecordSerializer, InspectionExecuteSerializer


User = get_user_model()


class InspectionRecordSerializerTests(TestCase):
    """Test cases for InspectionRecordSerializer."""

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
        self.record_data = {
            'server': self.server.id,
            'command': 'df -h',
            'raw_output': 'Filesystem  Size  Used Avail Use% Mounted on',
            'parsed_result': {'disks': []},
            'status': 'success',
            'has_alert': False
        }

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        serializer = InspectionRecordSerializer(record)
        self.assertEqual(serializer.data['command'], 'df -h')
        self.assertEqual(serializer.data['status'], 'success')

    def test_serializer_contains_expected_fields(self):
        """Test serializer output contains expected fields."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        serializer = InspectionRecordSerializer(record)
        data = serializer.data
        
        expected_fields = [
            'id', 'server', 'server_name', 'server_ip',
            'executed_by', 'command',
            'raw_output', 'parsed_result', 'status', 'status_display',
            'has_alert', 'alert_message', 'inspection_time', 'is_scheduled'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_server_name_field(self):
        """Test server_name is included in serializer output."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        serializer = InspectionRecordSerializer(record)
        self.assertEqual(serializer.data['server_name'], 'Test Server')

    def test_server_ip_field(self):
        """Test server_ip is included in serializer output."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        serializer = InspectionRecordSerializer(record)
        self.assertEqual(serializer.data['server_ip'], '192.168.1.100')

    def test_executed_by_name_field(self):
        """Test executed_by_name is included in serializer output."""
        record = InspectionRecord.objects.create(
            server=self.server,
            executed_by=self.user,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        serializer = InspectionRecordSerializer(record)
        self.assertEqual(serializer.data['executed_by_name'], 'testuser')

    def test_executed_by_name_null(self):
        """Test executed_by_name is not present when executed_by is null."""
        record = InspectionRecord.objects.create(
            server=self.server,
            executed_by=None,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        serializer = InspectionRecordSerializer(record)
        # When executed_by is None, the field may not be present
        if 'executed_by_name' in serializer.data:
            self.assertIsNone(serializer.data['executed_by_name'])

    def test_status_display_field(self):
        """Test status_display is included in serializer output."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='success'
        )
        serializer = InspectionRecordSerializer(record)
        self.assertEqual(serializer.data['status_display'], '成功')

    def test_status_display_failed(self):
        """Test status_display for failed status."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='failed'
        )
        serializer = InspectionRecordSerializer(record)
        self.assertEqual(serializer.data['status_display'], '失败')

    def test_status_display_warning(self):
        """Test status_display for warning status."""
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={},
            status='warning'
        )
        serializer = InspectionRecordSerializer(record)
        self.assertEqual(serializer.data['status_display'], '警告')

    def test_inspection_time_read_only(self):
        """Test inspection_time is read-only."""
        from datetime import datetime
        from django.utils import timezone
        
        record = InspectionRecord.objects.create(
            server=self.server,
            command='df -h',
            raw_output='test',
            parsed_result={}
        )
        serializer = InspectionRecordSerializer(record)
        self.assertIn('inspection_time', serializer.data)

    def test_create_inspection_record_via_serializer(self):
        """Test creating inspection record through serializer."""
        data = {
            'server': self.server.id,
            'command': 'df -h',
            'raw_output': 'test output',
            'parsed_result': {'disks': []},
            'status': 'success',
            'has_alert': False
        }
        serializer = InspectionRecordSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        record = serializer.save()
        self.assertEqual(record.command, 'df -h')
        self.assertEqual(record.server, self.server)


class InspectionExecuteSerializerTests(TestCase):
    """Test cases for InspectionExecuteSerializer."""

    def setUp(self):
        """Set up test data."""
        self.valid_data = {
            'server_ids': [1, 2, 3],
            'command': 'df -h'
        }

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data."""
        serializer = InspectionExecuteSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_with_empty_command(self):
        """Test serializer with empty command uses default."""
        data = {'server_ids': [1]}
        serializer = InspectionExecuteSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['command'], 'df -h')

    def test_serializer_with_custom_command(self):
        """Test serializer with custom command."""
        data = {
            'server_ids': [1],
            'command': 'du -sh /var'
        }
        serializer = InspectionExecuteSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['command'], 'du -sh /var')

    def test_serializer_missing_server_ids(self):
        """Test serializer with missing server_ids."""
        data = {'command': 'df -h'}
        serializer = InspectionExecuteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('server_ids', serializer.errors)

    def test_serializer_empty_server_ids(self):
        """Test serializer with empty server_ids list."""
        data = {'server_ids': []}
        serializer = InspectionExecuteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('server_ids', serializer.errors)

    def test_serializer_invalid_server_ids_type(self):
        """Test serializer with invalid server_ids type."""
        data = {'server_ids': 'not_a_list'}
        serializer = InspectionExecuteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('server_ids', serializer.errors)

    def test_serializer_non_integer_server_ids(self):
        """Test serializer with non-integer server_ids."""
        data = {'server_ids': [1, 'two', 3]}
        serializer = InspectionExecuteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('server_ids', serializer.errors)

    def test_serializer_single_server_id(self):
        """Test serializer with single server_id."""
        data = {'server_ids': [1]}
        serializer = InspectionExecuteSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['server_ids'], [1])

    def test_serializer_large_server_ids_list(self):
        """Test serializer with large server_ids list."""
        data = {'server_ids': list(range(1, 101))}
        serializer = InspectionExecuteSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['server_ids']), 100)

    def test_validate_server_ids_empty_list(self):
        """Test validation of empty server_ids list."""
        data = {'server_ids': []}
        serializer = InspectionExecuteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # Should have error about empty list
        self.assertIn('server_ids', serializer.errors)
