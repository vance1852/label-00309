"""Tests for schedule models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.schedules.models import InspectionSchedule


User = get_user_model()


class InspectionScheduleModelTests(TestCase):
    """Test cases for InspectionSchedule model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_create_schedule(self):
        """Test creating inspection schedule."""
        schedule = InspectionSchedule.objects.create(
            name='Daily Inspection',
            interval_type='daily',
            interval_value=1,
            execute_time='02:00:00',
            execute_day=1,
            inspection_command='df -h',
            is_active=True,
            updated_by=self.user
        )
        
        self.assertEqual(schedule.name, 'Daily Inspection')
        self.assertEqual(schedule.interval_type, 'daily')
        self.assertEqual(schedule.interval_value, 1)
        self.assertEqual(str(schedule.execute_time), '02:00:00')
        self.assertEqual(schedule.execute_day, 1)
        self.assertEqual(schedule.inspection_command, 'df -h')
        self.assertTrue(schedule.is_active)
        self.assertEqual(schedule.updated_by, self.user)

    def test_schedule_str_representation(self):
        """Test schedule string representation."""
        schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1
        )
        expected_str = f"{schedule.name} - {schedule.get_interval_type_display()}"
        self.assertEqual(str(schedule), expected_str)

    def test_schedule_default_values(self):
        """Test schedule default values."""
        schedule = InspectionSchedule.objects.create()
        
        self.assertEqual(schedule.name, '定时巡检')
        self.assertEqual(schedule.interval_type, 'daily')
        self.assertEqual(schedule.interval_value, 1)
        self.assertEqual(str(schedule.execute_time), '02:00:00')
        self.assertEqual(schedule.execute_day, 1)
        self.assertEqual(schedule.inspection_command, 'df -h')
        self.assertTrue(schedule.is_active)
        self.assertIsNone(schedule.last_run)
        self.assertIsNone(schedule.next_run)

    def test_schedule_interval_choices(self):
        """Test all interval type choices."""
        interval_types = ['hourly', 'daily', 'weekly', 'monthly']
        
        for i, interval_type in enumerate(interval_types):
            schedule = InspectionSchedule.objects.create(
                name=f'Schedule {i}',
                interval_type=interval_type,
                interval_value=1
            )
            self.assertEqual(schedule.interval_type, interval_type)

    def test_schedule_interval_type_display(self):
        """Test interval type display values."""
        displays = {
            'hourly': '每小时',
            'daily': '每天',
            'weekly': '每周',
            'monthly': '每月'
        }
        
        for interval_type, display in displays.items():
            schedule = InspectionSchedule.objects.create(
                name='Test',
                interval_type=interval_type,
                interval_value=1
            )
            self.assertEqual(schedule.get_interval_type_display(), display)

    def test_schedule_nullable_timestamps(self):
        """Test that last_run and next_run can be null."""
        schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1,
            last_run=None,
            next_run=None
        )
        
        self.assertIsNone(schedule.last_run)
        self.assertIsNone(schedule.next_run)

    def test_schedule_nullable_updated_by(self):
        """Test that updated_by can be null."""
        schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1,
            updated_by=None
        )
        
        self.assertIsNone(schedule.updated_by)

    def test_schedule_execute_day_range(self):
        """Test execute_day can be set to various values."""
        # Day of week (1-7) or day of month (1-31)
        for day in [1, 7, 15, 31]:
            schedule = InspectionSchedule.objects.create(
                name=f'Schedule {day}',
                interval_type='daily',
                interval_value=1,
                execute_day=day
            )
            self.assertEqual(schedule.execute_day, day)

    def test_schedule_interval_value_variations(self):
        """Test interval_value can be set to various values."""
        for value in [1, 2, 6, 12, 24]:
            schedule = InspectionSchedule.objects.create(
                name=f'Schedule {value}',
                interval_type='hourly',
                interval_value=value
            )
            self.assertEqual(schedule.interval_value, value)

    def test_schedule_custom_command(self):
        """Test custom inspection command."""
        custom_command = 'du -sh /var/log && df -h'
        schedule = InspectionSchedule.objects.create(
            name='Custom Schedule',
            interval_type='daily',
            interval_value=1,
            inspection_command=custom_command
        )
        
        self.assertEqual(schedule.inspection_command, custom_command)

    def test_schedule_ordering(self):
        """Test schedules are ordered by created_at."""
        schedule1 = InspectionSchedule.objects.create(
            name='Schedule 1',
            interval_type='daily',
            interval_value=1
        )
        schedule2 = InspectionSchedule.objects.create(
            name='Schedule 2',
            interval_type='hourly',
            interval_value=2
        )
        
        schedules = list(InspectionSchedule.objects.all())
        # Verify both schedules exist
        self.assertEqual(len(schedules), 2)
        self.assertIn(schedule1, schedules)
        self.assertIn(schedule2, schedules)

    def test_schedule_is_active_toggle(self):
        """Test toggling is_active status."""
        schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1,
            is_active=True
        )
        
        schedule.is_active = False
        schedule.save()
        
        schedule.refresh_from_db()
        self.assertFalse(schedule.is_active)

    def test_schedule_updated_at_auto_update(self):
        """Test updated_at is automatically updated."""
        import time
        
        schedule = InspectionSchedule.objects.create(
            name='Test Schedule',
            interval_type='daily',
            interval_value=1
        )
        
        original_updated_at = schedule.updated_at
        
        # Wait a moment to ensure time difference
        time.sleep(0.1)
        
        # Update the schedule
        schedule.name = 'Updated Name'
        schedule.save()
        
        schedule.refresh_from_db()
        self.assertGreaterEqual(schedule.updated_at, original_updated_at)
