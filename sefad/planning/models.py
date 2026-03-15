from django.db import models
from courses.models import Course, Discipline
from django.core.validators import RegexValidator

semester_validator = RegexValidator(
    regex=r'^\d{4}\.[12]$',
    message='Formato inválido. Use AAAA.1 ou AAAA.2 (ex: 2026.1)',
)


class SemesterPlan(models.Model):
    """
    Represents a semester planning with disciplines to be offered.
    Used to calculate teaching effort and resource allocation.
    """

    name = models.CharField(
        max_length=200,
        verbose_name="Plan Name",
        help_text='Name to identify this semester plan (e.g., "2024.1 Planning")',
    )
    semester = models.CharField(
        max_length=20,
        verbose_name="Semester",
        help_text='Semester identifier (e.g., "2024.1", "2024.2")',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="semester_plans",
        verbose_name="Course",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Additional notes about this plan",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-semester", "-created_at"]
        verbose_name = "Semester Plan"
        verbose_name_plural = "Semester Plans"

    def __str__(self):
        return f"{self.name} - {self.course.name}"

    def get_total_credits(self):
        """Calculate total credits for all disciplines in this plan."""
        return sum(
            item.discipline.credits * item.classes_count
            for item in self.plan_items.all()
        )

    def get_total_ch_relogio(self):
        """Calculate total CH Relógio for all disciplines in this plan."""
        return sum(
            item.discipline.ch_relogio * item.classes_count
            for item in self.plan_items.all()
        )

    def get_disciplines_count(self):
        """Get total number of discipline instances (including extra classes)."""
        return sum(item.classes_count for item in self.plan_items.all())

    def get_unique_disciplines_count(self):
        """Get number of unique disciplines."""
        return self.plan_items.count()


class PlanDiscipline(models.Model):
    """
    Represents a discipline included in a semester plan.
    Allows for multiple classes of the same discipline (extra classes).
    """

    plan = models.ForeignKey(
        SemesterPlan,
        on_delete=models.CASCADE,
        related_name="plan_items",
        verbose_name="Plan",
    )
    discipline = models.ForeignKey(
        Discipline,
        on_delete=models.CASCADE,
        related_name="plan_items",
        verbose_name="Discipline",
    )
    classes_count = models.PositiveIntegerField(
        default=1,
        verbose_name="Number of Classes",
        help_text="Number of classes for this discipline (usually 1, but can be more for extra classes)",
    )
    assigned_period = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Assigned Period",
        help_text="Period where this elective discipline will be offered",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Additional notes about this discipline in the plan",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["discipline__period", "discipline__name"]
        verbose_name = "Plan Discipline"
        verbose_name_plural = "Plan Disciplines"
        unique_together = ["plan", "discipline"]

    def __str__(self):
        if self.classes_count > 1:
            return f"{self.discipline.name} ({self.classes_count}x)"
        return self.discipline.name

    def save(self, *args, **kwargs):
        """Override save to automatically set assigned_period for non-elective disciplines."""
        # If discipline is not elective (period != "0"), use discipline's period
        if self.discipline.period != "0":
            self.assigned_period = self.discipline.period
        super().save(*args, **kwargs)

    def get_period_display(self):
        """Get the actual period where this discipline is offered."""
        return self.assigned_period if self.assigned_period else self.discipline.period

    def get_total_credits(self):
        """Get total credits for this discipline considering class count."""
        return self.discipline.credits * self.classes_count

    def get_total_ch_relogio(self):
        """Get total CH Relógio for this discipline considering class count."""
        return self.discipline.ch_relogio * self.classes_count


class ClassEntry(models.Model):
    """
    Represents the start of a cohort (turma) for a course in a given semester.
    The system projects which disciplines will be offered in each future semester
    based on the course's periods.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="class_entries",
        verbose_name="Curso",
    )
    start_semester = models.CharField(
        max_length=10,
        verbose_name="Semestre de Início",
        help_text='Semestre em que a turma inicia (ex: "2026.1")',
        validators=[semester_validator],
    )
    label = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Rótulo",
        help_text='Nome opcional para identificar a turma (ex: "Turma A")',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Desmarque para excluir da projeção sem deletar",
    )
    notes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_semester", "course__name"]
        verbose_name = "Entrada de Turma"
        verbose_name_plural = "Entradas de Turma"

    def __str__(self):
        label = f" ({self.label})" if self.label else ""
        return f"{self.course.name} — {self.start_semester}{label}"

    def get_semester_for_period(self, period):
        """Return the target semester for the given course period number (1-based int)."""
        from .utils import add_semesters
        if self.course.calendar_type == Course.CALENDAR_SEMESTRAL:
            offset = period - 1
        else:
            # Yearly: each period lasts 2 semesters
            offset = (period - 1) * 2
        return add_semesters(self.start_semester, offset)


class ExtraClass(models.Model):
    """
    Represents extra turma(s) of a discipline offered in a specific semester,
    independent of any ClassEntry. Used to model additional classes beyond
    the regular projection.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="extra_classes",
        verbose_name="Curso",
    )
    discipline = models.ForeignKey(
        Discipline,
        on_delete=models.CASCADE,
        related_name="extra_classes",
        verbose_name="Disciplina",
    )
    semester = models.CharField(
        max_length=10,
        verbose_name="Semestre",
        help_text='Semestre em que a disciplina extra será ofertada (ex: "2026.1")',
        validators=[semester_validator],
    )
    extra_count = models.PositiveIntegerField(
        default=1,
        verbose_name="Número de Turmas Extras",
    )
    notes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["semester", "discipline__name"]
        verbose_name = "Disciplina Extra"
        verbose_name_plural = "Disciplinas Extras"
        unique_together = ["discipline", "semester"]

    def __str__(self):
        count = f" ({self.extra_count}x)" if self.extra_count > 1 else ""
        return f"{self.discipline.name}{count} — {self.semester}"
