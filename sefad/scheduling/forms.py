from django import forms
from django.core.validators import RegexValidator

from courses.models import Course, Discipline
from professors.models import Professor

from .models import ClassAssignment, ScheduledClass, SemesterSchedule


class SemesterScheduleForm(forms.ModelForm):
    class Meta:
        model = SemesterSchedule
        fields = ["name", "semester", "class_duration", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Ex: Grade 2025.1"}
            ),
            "semester": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "2025.1"}
            ),
            "class_duration": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }
        labels = {
            "name": "Nome",
            "semester": "Semestre",
            "class_duration": "Tempo de Aula",
            "description": "Descrição",
        }


class ScheduledClassForm(forms.ModelForm):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by("name"),
        required=False,
        label="Curso",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_course"}),
    )

    class Meta:
        model = ScheduledClass
        fields = ["discipline", "class_label", "turno", "weekly_classes", "notes"]
        widgets = {
            "discipline": forms.Select(
                attrs={"class": "form-select", "id": "id_discipline"}
            ),
            "class_label": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Turma A (opcional)"}
            ),
            "turno": forms.Select(attrs={"class": "form-select"}),
            "weekly_classes": forms.NumberInput(attrs={"class": "form-input", "min": 1}),
            "notes": forms.Textarea(attrs={"class": "form-input", "rows": 2}),
        }
        labels = {
            "discipline": "Disciplina",
            "class_label": "Rótulo da Turma",
            "turno": "Turno",
            "weekly_classes": "Aulas Semanais",
            "notes": "Observações",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get("course"):
            try:
                course_id = int(self.data["course"])
                self.fields["discipline"].queryset = Discipline.objects.filter(
                    course_id=course_id
                ).order_by("period", "name")
            except (ValueError, TypeError):
                self.fields["discipline"].queryset = Discipline.objects.none()
        elif self.instance and self.instance.pk:
            self.fields["discipline"].queryset = Discipline.objects.filter(
                course=self.instance.discipline.course
            ).order_by("period", "name")
            self.initial["course"] = self.instance.discipline.course_id
        else:
            self.fields["discipline"].queryset = Discipline.objects.none()


class ClassAssignmentForm(forms.ModelForm):
    class Meta:
        model = ClassAssignment
        fields = ["professor"]
        widgets = {
            "professor": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "professor": "Professor",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["professor"].queryset = Professor.objects.filter(
            is_active=True
        ).order_by("name")


class CopyScheduleForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        label="Nome",
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    semester = forms.CharField(
        max_length=10,
        label="Semestre",
        validators=[RegexValidator(r"^\d{4}\.[12]$", "Formato inválido. Use AAAA.1 ou AAAA.2")],
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "2025.2"}),
        help_text='Ex: "2025.1", "2025.2"',
    )
    copy_assignments = forms.BooleanField(
        required=False,
        initial=False,
        label="Copiar atribuições de professores",
        widget=forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        help_text="Se marcado, os professores atribuídos às turmas também serão copiados.",
    )


class BulkImportForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by("name"),
        label="Curso",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    turno = forms.ChoiceField(
        choices=[("M", "Manhã"), ("T", "Tarde"), ("N", "Noite")],
        label="Turno",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    skip_existing = forms.BooleanField(
        required=False,
        initial=True,
        label="Ignorar disciplinas já adicionadas",
        widget=forms.CheckboxInput(attrs={"class": "form-checkbox"}),
    )
