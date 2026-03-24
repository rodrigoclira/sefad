from django.db import models
from django.core.validators import RegexValidator

from courses.models import Discipline
from professors.models import Professor


semester_validator = RegexValidator(
    regex=r"^\d{4}\.[12]$",
    message="Formato inválido. Use AAAA.1 ou AAAA.2 (ex: 2025.1)",
)

TURNO_CHOICES = [
    ("M", "Manhã"),
    ("T", "Tarde"),
    ("N", "Noite"),
]

CLASS_DURATION_CHOICES = [
    (45, "45 min"),
    (50, "50 min"),
    (60, "60 min"),
]


class SemesterSchedule(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nome")
    semester = models.CharField(
        max_length=10,
        verbose_name="Semestre",
        validators=[semester_validator],
        help_text='Ex: "2025.1", "2025.2"',
    )
    class_duration = models.IntegerField(
        choices=CLASS_DURATION_CHOICES,
        default=45,
        verbose_name="Tempo de Aula (min)",
        help_text="Usado para calcular os limites de carga horária conforme norma vigente",
    )
    description = models.TextField(blank=True, verbose_name="Descrição")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-semester", "name"]
        verbose_name = "Grade Semestral"
        verbose_name_plural = "Grades Semestrais"

    def __str__(self):
        return f"{self.name} ({self.semester})"


class ScheduledClass(models.Model):
    schedule = models.ForeignKey(
        SemesterSchedule,
        on_delete=models.CASCADE,
        related_name="scheduled_classes",
        verbose_name="Grade",
    )
    discipline = models.ForeignKey(
        Discipline,
        on_delete=models.CASCADE,
        related_name="scheduled_classes",
        verbose_name="Disciplina",
    )
    class_label = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Rótulo da Turma",
        help_text='Ex: "Turma A", "T01"',
    )
    turno = models.CharField(
        max_length=1,
        choices=TURNO_CHOICES,
        blank=True,
        verbose_name="Turno",
    )
    weekly_classes = models.PositiveIntegerField(
        default=1,
        verbose_name="Aulas Semanais",
        help_text="Número de aulas por semana para esta turma",
    )
    notes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [
            "discipline__course__name",
            "discipline__period",
            "discipline__name",
            "turno",
            "class_label",
        ]
        verbose_name = "Turma Ofertada"
        verbose_name_plural = "Turmas Ofertadas"

    def __str__(self):
        parts = [self.discipline.name]
        if self.class_label:
            parts.append(self.class_label)
        if self.turno:
            parts.append(self.get_turno_display())
        return " — ".join(parts)


class ClassAssignment(models.Model):
    scheduled_class = models.ForeignKey(
        ScheduledClass,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Turma Ofertada",
    )
    professor = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        related_name="class_assignments",
        verbose_name="Professor",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["professor__name"]
        unique_together = ["scheduled_class", "professor"]
        verbose_name = "Atribuição de Professor"
        verbose_name_plural = "Atribuições de Professores"

    def __str__(self):
        return f"{self.professor.name} → {self.scheduled_class}"
