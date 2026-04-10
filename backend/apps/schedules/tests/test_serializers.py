"""Tests for schedule serializers."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.schedules.models import InspectionSchedule
from apps.schedules.serializers import InspectionScheduleSerializer


User = get_user_model()


class InspectionScheduleSerializerTests(TestCase):
    """Test cases for InspectionScheduleSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.valid_data = {
            'name': 'Daily Inspection',
            'interval_type': 'daily',
            'interval_value': 1,
            'execute_time': '02:00:00',
            'execute_day': 1,
            'inspection_command': 'df -h',
            'is_active': True
        }

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data."""
        serializer = InspectionScheduleSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_output_fields(self):
        """Test serializer output contains expected fields."""
        schedule = InspectionSchedule.objects.create(**self.valid_data)
        serializer = InspectionScheduleSerializer(schedule)
        data = serializer.data
        
        expected_fields = [
            'id', 'name', 'interval_type', 'interval_type_display',
            'interval_value', 'execute_time', 'execute_day',
            'inspection_command', 'is_active', 'last_run', 'next_run',
            'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_interval_type_display_field(self):
        """Test interval_type_display is included in output."""
        schedule = InspectionSchedule.objects.create(
            name='Test',
            interval_type='hourly',
            interval_value=1
        )
        serializer = InspectionScheduleSerializer(schedule)
        self.assertEqual(serializer.data['interval_type_display'], '每小时')

    def test_updated_by_name_field(self):
        """Test updated_by_name is included in output."""
        schedule = InspectionSchedule.objects.create(
            name='Test',
            interval_type='daily',
            interval_value=1,
            updated_by=self.user
        )
        serializer = InspectionScheduleSerializer(schedule)
        self.assertEqual(serializer.data['updated_by_name'], 'testuser')

    def test_updated_by_name_null(self):
        """Test updated_by_name is not present when updated_by is null."""
        schedule = InspectionSchedule.objects.create(
            name='Test',
            interval_type='daily',
            interval_value=1,
            updated_by=None
        )
        serializer = InspectionScheduleSerializer(schedule)
        # When updated_by is None, the field may not be present
        if 'updated_by_name' in serializer.data:
            self.assertIsNone(serializer.data['updated_by_name'])

    def test_validate_interval_value_zero(self):
        """Test interval_value validation with zero."""
        data = self.valid_data.copy()
        data['interval_value'] = 0
        serializer = InspectionScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('interval_value', serializer.errors)

    def test_validate_interval_value_negative(self):
        """Test interval_value validation with negative value."""
        data = self.valid_data.copy()
        data['interval_value'] = -1
        serializer = InspectionScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('interval_value', serializer.errors)

    def test_validate_interval_value_positive(self):
        """Test interval_value validation with positive values."""
        for value in [1, 5, 10, 100]:
            data = self.valid_data.copy()
            data['interval_value'] = value
            serializer = InspectionScheduleSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Value {value} should be valid")

    def test_validate_execute_day_zero(self):
        """Test execute_day validation with zero."""
        data = self.valid_data.copy()
        data['execute_day'] = 0
        serializer = InspectionScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('execute_day', serializer.errors)

    def test_validate_execute_day_too_high(self):
        """Test execute_day validation with value too high."""
        data = self.valid_data.copy()
        data['execute_day'] = 32
        serializer = InspectionScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('execute_day', serializer.errors)

    def test_validate_execute_day_boundary_values(self):
        """Test execute_day validation with boundary values."""
        for day in [1, 7, 15, 31]:
            data = self.valid_data.copy()
            data['execute_day'] = day
            serializer = InspectionScheduleSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Day {day} should be valid")

    def test_create_schedule_via_serializer(self):
        """Test creating schedule through serializer."""
        serializer = InspectionScheduleSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        schedule = serializer.save(updated_by=self.user)
        
        self.assertEqual(schedule.name, 'Daily Inspection')
        self.assertEqual(schedule.interval_type, 'daily')
        self.assertEqual(schedule.interval_value, 1)
        self.assertEqual(schedule.updated_by, self.user)

    def test_update_schedule_via_serializer(self):
        """Test updating schedule through serializer."""
        schedule = InspectionSchedule.objects.create(
            name='Old Name',
            interval_type='daily',
            interval_value=1
        )
        
        update_data = {'name': 'New Name', 'interval_value': 2}
        serializer = InspectionScheduleSerializer(schedule, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        
        self.assertEqual(updated.name, 'New Name')
        self.assertEqual(updated.interval_value, 2)
        self.assertEqual(updated.interval_type, 'daily')  # Unchanged

    def test_read_only_fields(self):
        """Test that read-only fields cannot be set."""
        data = self.valid_data.copy()
        data['id'] = 999
        data['last_run'] = '2020-01-01T00:00:00Z'
        data['next_run'] = '2020-01-01T00:00:00Z'
        data['created_at'] = '2020-01-01T00:00:00Z'
        data['updated_at'] = '2020-01-01T00:00:00Z'
        
        serializer = InspectionScheduleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Read-only fields should not be in validated_data
        self.assertNotIn('id', serializer.validated_data)
        self.assertNotIn('last_run', serializer.validated_data)
        self.assertNotIn('next_run', serializer.validated_data)
        self.assertNotIn('created_at', serializer.validated_data)
        self.assertNotIn('updated_at', serializer.validated_data)

    def test_all_interval_types(self):
        """Test serializer with all interval types."""
        interval_types = ['hourly', 'daily', 'weekly', 'monthly']
        
        for interval_type in interval_types:
            data = self.valid_data.copy()
            data['interval_type'] = interval_type
            serializer = InspectionScheduleSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Interval type {interval_type} should be valid")

    def test_invalid_interval_type(self):
        """Test serializer with invalid interval type."""
        data = self.valid_data.copy()
        data['interval_type'] = 'yearly'  # Invalid choice
        serializer = InspectionScheduleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('interval_type', serializer.errors)

    def test_custom_inspection_command(self):
        """Test serializer with custom inspection command."""
        data = self.valid_data.copy()
        data['inspection_command'] = 'du -sh /var && df -h'
        serializer = InspectionScheduleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        schedule = serializer.save()
        self.assertEqual(schedule.inspection_command, 'du -sh /var && df -h')

    def test_time_format(self):
        """Test execute_time format."""
        times = ['00:00:00', '12:30:45', '23:59:59']
        
        for time_str in times:
            data = self.valid_data.copy()
            data['execute_time'] = time_str
            serializer = InspectionScheduleSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Time {time_str} should be valid")

    def test_partial_update(self):
        """Test partial update of schedule."""
        schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1,
            is_active=True
        )
        
        # Update only is_active
        update_data = {'is_active': False}
        serializer = InspectionScheduleSerializer(schedule, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        
        self.assertFalse(updated.is_active)
        self.assertEqual(updated.name, 'Test Schedule')  # Unchanged
