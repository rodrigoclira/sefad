# Courses App

This Django app manages courses and disciplines for the SEFAD system.

## Models

### Course
Represents an academic course/program.

**Fields:**
- `name`: Course name (CharField, max_length=200)
- `calendar_type`: Calendar type - semestral or yearly (CharField with choices)
- `description`: Course description for effort calculation (TextField, optional)
- `created_at`: Creation timestamp (auto)
- `updated_at`: Update timestamp (auto)

**Methods:**
- `__str__()`: Returns course name with calendar type

### Discipline
Represents a discipline/class within a course program.

**Fields:**
- `course`: Foreign key to Course
- `name`: Discipline name (CharField, max_length=200)
- `period`: Semester or year when offered (CharField)
- `main_area`: Main knowledge area for professor matching (CharField, max_length=200)
- `description`: Discipline description for effort calculation (TextField, optional)
- `workload_hours`: Total workload in hours (PositiveIntegerField, default=60)
- `created_at`: Creation timestamp (auto)
- `updated_at`: Update timestamp (auto)

**Methods:**
- `__str__()`: Returns discipline name with course and period
- `get_period_display_options()`: Returns appropriate period choices based on course calendar type

## URL Patterns

- `/courses/` - List all courses
- `/courses/course/<id>/` - Course detail with disciplines
- `/courses/disciplines/` - List all disciplines
- `/courses/discipline/<id>/` - Discipline detail

## Admin Interface

Both models are registered in the Django admin with:
- List display with relevant fields
- Filtering options
- Search functionality
- Organized fieldsets
- Timestamps (read-only)

The Discipline admin dynamically adjusts period choices based on the course's calendar type.

## Usage

### Creating a Course

```python
from courses.models import Course

course = Course.objects.create(
    name='Computer Science',
    calendar_type=Course.CALENDAR_SEMESTRAL,
    description='Bachelor degree in Computer Science'
)
```

### Creating a Discipline

```python
from courses.models import Discipline

discipline = Discipline.objects.create(
    course=course,
    name='Data Structures',
    period=Discipline.PERIOD_FIRST_SEMESTER,
    main_area='Computer Science',
    workload_hours=80,
    description='Introduction to data structures and algorithms'
)
```

### Accessing Disciplines of a Course

```python
# Get all disciplines of a course
disciplines = course.disciplines.all()

# Get disciplines by period
first_semester = course.disciplines.filter(period=Discipline.PERIOD_FIRST_SEMESTER)
```

## Testing

Run tests with:
```bash
python manage.py test courses
```

The test suite includes:
- Model creation tests
- String representation tests
- Relationship tests
- Default value tests
- Period display options tests
