from django.db import models


class Course(models.Model):
    """
    Represents an academic course/program.
    Stores course information including name and calendar type.
    """

    CALENDAR_SEMESTRAL = "semestral"
    CALENDAR_YEARLY = "yearly"

    CALENDAR_CHOICES = [
        (CALENDAR_SEMESTRAL, "Semestral"),
        (CALENDAR_YEARLY, "Yearly"),
    ]

    name = models.CharField(max_length=200, verbose_name="Course Name")
    grade_year = models.CharField(
        max_length=20,
        default="2019.2",
        verbose_name="Grade Year",
        help_text="Academic year/period of the course curriculum (e.g., 2019.2)",
    )
    calendar_type = models.CharField(
        max_length=20,
        choices=CALENDAR_CHOICES,
        default=CALENDAR_SEMESTRAL,
        verbose_name="Calendar Type",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Course Description",
        help_text="Description of the course program to be used for effort calculation",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.name} ({self.get_calendar_type_display()})"


class Discipline(models.Model):
    """
    Represents a discipline/class within a course program.
    Each discipline has a period (semester or year) when it's offered
    and a main area to match with professors.
    """

    PERIOD_FIRST_SEMESTER = "1"
    PERIOD_SECOND_SEMESTER = "2"
    PERIOD_FIRST_YEAR = "year_1"
    PERIOD_SECOND_YEAR = "year_2"
    PERIOD_THIRD_YEAR = "year_3"
    PERIOD_FOURTH_YEAR = "year_4"
    PERIOD_FIFTH_YEAR = "year_5"

    SEMESTER_PERIODS = [
        (PERIOD_FIRST_SEMESTER, "1st Semester"),
        (PERIOD_SECOND_SEMESTER, "2nd Semester"),
    ]

    YEARLY_PERIODS = [
        (PERIOD_FIRST_YEAR, "1st Year"),
        (PERIOD_SECOND_YEAR, "2nd Year"),
        (PERIOD_THIRD_YEAR, "3rd Year"),
        (PERIOD_FOURTH_YEAR, "4th Year"),
        (PERIOD_FIFTH_YEAR, "5th Year"),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="disciplines",
        verbose_name="Course",
    )
    name = models.CharField(max_length=200, verbose_name="Discipline Name")
    period = models.CharField(
        max_length=20,
        verbose_name="Period",
        help_text="Semester or year when the discipline is offered",
    )
    main_area = models.CharField(
        max_length=200,
        verbose_name="Main Area",
        help_text="Main knowledge area to be matched with professors",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Discipline Description",
        help_text="Description of the discipline to be used for effort calculation",
    )
    credits = models.PositiveIntegerField(
        default=0, verbose_name="Credits", help_text="Number of credits"
    )
    ch_aula = models.PositiveIntegerField(
        default=0,
        verbose_name="CH Aula",
        help_text="Classroom hours (carga horária aula)",
    )
    ch_relogio = models.PositiveIntegerField(
        default=0,
        verbose_name="CH Relógio",
        help_text="Clock hours (carga horária relógio)",
    )
    pre_requisito = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Prerequisite",
        help_text="Prerequisite discipline(s)",
    )
    co_requisito = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Co-requisite",
        help_text="Co-requisite discipline(s)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "period", "name"]
        verbose_name = "Discipline"
        verbose_name_plural = "Disciplines"

    def __str__(self):
        return f"{self.name} - {self.course.name} ({self.period})"

    def get_period_display_options(self):
        """Return the appropriate period choices based on the course calendar type."""
        if self.course.calendar_type == Course.CALENDAR_SEMESTRAL:
            return self.SEMESTER_PERIODS
        else:
            return self.YEARLY_PERIODS
