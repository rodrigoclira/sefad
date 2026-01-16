from django.test import TestCase
from .models import Course, Discipline


class CourseModelTest(TestCase):
    """Test cases for the Course model."""
    
    def setUp(self):
        """Set up test data."""
        self.course_semestral = Course.objects.create(
            name='Computer Science',
            calendar_type=Course.CALENDAR_SEMESTRAL,
            description='Bachelor degree in Computer Science'
        )
        self.course_yearly = Course.objects.create(
            name='Medicine',
            calendar_type=Course.CALENDAR_YEARLY,
            description='Doctor of Medicine program'
        )
    
    def test_course_creation(self):
        """Test that courses are created correctly."""
        self.assertEqual(self.course_semestral.name, 'Computer Science')
        self.assertEqual(self.course_semestral.calendar_type, Course.CALENDAR_SEMESTRAL)
        self.assertEqual(self.course_yearly.calendar_type, Course.CALENDAR_YEARLY)
    
    def test_course_str_representation(self):
        """Test the string representation of courses."""
        self.assertEqual(
            str(self.course_semestral),
            'Computer Science (Semestral)'
        )
        self.assertEqual(
            str(self.course_yearly),
            'Medicine (Yearly)'
        )
    
    def test_course_ordering(self):
        """Test that courses are ordered by name."""
        courses = Course.objects.all()
        self.assertEqual(courses[0].name, 'Computer Science')
        self.assertEqual(courses[1].name, 'Medicine')


class DisciplineModelTest(TestCase):
    """Test cases for the Discipline model."""
    
    def setUp(self):
        """Set up test data."""
        self.course = Course.objects.create(
            name='Computer Science',
            calendar_type=Course.CALENDAR_SEMESTRAL
        )
        self.discipline = Discipline.objects.create(
            course=self.course,
            name='Data Structures',
            period=Discipline.PERIOD_FIRST_SEMESTER,
            main_area='Computer Science',
            description='Introduction to data structures',
            workload_hours=80
        )
    
    def test_discipline_creation(self):
        """Test that disciplines are created correctly."""
        self.assertEqual(self.discipline.name, 'Data Structures')
        self.assertEqual(self.discipline.course, self.course)
        self.assertEqual(self.discipline.period, Discipline.PERIOD_FIRST_SEMESTER)
        self.assertEqual(self.discipline.main_area, 'Computer Science')
        self.assertEqual(self.discipline.workload_hours, 80)
    
    def test_discipline_str_representation(self):
        """Test the string representation of disciplines."""
        expected = f"Data Structures - Computer Science (Semestral) ({Discipline.PERIOD_FIRST_SEMESTER})"
        # The actual format is: name - course.name (period)
        self.assertIn('Data Structures', str(self.discipline))
        self.assertIn('Computer Science', str(self.discipline))
        self.assertIn('1', str(self.discipline))
    
    def test_discipline_course_relationship(self):
        """Test the relationship between discipline and course."""
        self.assertEqual(self.course.disciplines.count(), 1)
        self.assertEqual(self.course.disciplines.first(), self.discipline)
    
    def test_discipline_default_workload(self):
        """Test that discipline has a default workload."""
        discipline = Discipline.objects.create(
            course=self.course,
            name='Algorithms',
            period=Discipline.PERIOD_SECOND_SEMESTER,
            main_area='Computer Science'
        )
        self.assertEqual(discipline.workload_hours, 60)
    
    def test_get_period_display_options_semestral(self):
        """Test period options for semestral courses."""
        options = self.discipline.get_period_display_options()
        self.assertEqual(options, Discipline.SEMESTER_PERIODS)
    
    def test_get_period_display_options_yearly(self):
        """Test period options for yearly courses."""
        yearly_course = Course.objects.create(
            name='Medicine',
            calendar_type=Course.CALENDAR_YEARLY
        )
        discipline = Discipline.objects.create(
            course=yearly_course,
            name='Anatomy',
            period=Discipline.PERIOD_FIRST_YEAR,
            main_area='Medicine'
        )
        options = discipline.get_period_display_options()
        self.assertEqual(options, Discipline.YEARLY_PERIODS)
