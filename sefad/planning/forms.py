from django import forms
from .models import SemesterPlan, PlanDiscipline, ClassEntry, ExtraClass
from courses.models import Course, Discipline


class AddDisciplineForm(forms.Form):
    """Form for adding a discipline to a plan."""

    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.none(),
        empty_label="-- Selecione uma disciplina --",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Disciplina",
    )
    classes_count = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-input"}),
        label="Número de Turmas",
        help_text="Quantas turmas desta disciplina serão oferecidas?",
    )
    assigned_period = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_assigned_period"}),
        label="Período de Oferta",
        help_text="Para disciplinas optativas, escolha em qual período será oferecida",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        label="Observações",
    )

    def __init__(self, *args, plan=None, **kwargs):
        super().__init__(*args, **kwargs)
        if plan:
            # Only show disciplines from the plan's course that aren't already in the plan
            self.fields["discipline"].queryset = (
                Discipline.objects.filter(course=plan.course)
                .exclude(pk__in=plan.plan_items.values_list("discipline_id", flat=True))
                .order_by("period", "name")
            )
            # Get available periods from the course (excluding period 0)
            periods = (
                Discipline.objects.filter(course=plan.course)
                .exclude(period="0")
                .values_list("period", flat=True)
                .distinct()
                .order_by("period")
            )
            period_choices = [(p, f"Período {p}") for p in periods]
            self.fields["assigned_period"].choices = [
                ("", "-- Selecione o período --")
            ] + period_choices


class CreatePlanForm(forms.ModelForm):
    """Form for creating a new semester plan."""

    class Meta:
        model = SemesterPlan
        fields = ["name", "semester", "course", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "semester": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "2024.1"}
            ),
            "course": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
        }
        labels = {
            "name": "Nome do Plano",
            "semester": "Semestre",
            "course": "Curso",
            "description": "Descrição",
        }
        help_texts = {
            "name": 'Name to identify this semester plan (e.g., "2024.1 Planning")',
            "semester": 'Semester identifier (e.g., "2024.1", "2024.2")',
            "description": "Additional notes about this plan",
        }


class UpdateItemForm(forms.ModelForm):
    """Form for updating a plan item."""

    class Meta:
        model = PlanDiscipline
        fields = ["classes_count", "notes"]
        widgets = {
            "classes_count": forms.NumberInput(attrs={"class": "form-input"}),
            "notes": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }
        labels = {
            "classes_count": "Número de Turmas",
            "notes": "Observações",
        }
        help_texts = {
            "classes_count": "Quantas turmas desta disciplina serão oferecidas?",
        }


class ClassEntryForm(forms.ModelForm):
    """Form for creating/editing a class entry (entrada de turma)."""

    class Meta:
        model = ClassEntry
        fields = ["course", "start_semester", "label", "is_active", "notes"]
        widgets = {
            "course": forms.Select(attrs={"class": "form-select"}),
            "start_semester": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "2026.1"}
            ),
            "label": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Turma A (opcional)"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "notes": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }
        labels = {
            "course": "Curso",
            "start_semester": "Semestre de Início",
            "label": "Rótulo",
            "is_active": "Ativa",
            "notes": "Observações",
        }


class ExtraClassForm(forms.ModelForm):
    """Form for creating an extra class (disciplina extra) in a semester."""

    class Meta:
        model = ExtraClass
        fields = ["course", "discipline", "semester", "extra_count", "notes"]
        widgets = {
            "course": forms.Select(attrs={"class": "form-select", "id": "id_course"}),
            "discipline": forms.Select(attrs={"class": "form-select", "id": "id_discipline"}),
            "semester": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "2026.1"}
            ),
            "extra_count": forms.NumberInput(attrs={"class": "form-input", "min": 1}),
            "notes": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }
        labels = {
            "course": "Curso",
            "discipline": "Disciplina",
            "semester": "Semestre",
            "extra_count": "Número de Turmas Extras",
            "notes": "Observações",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter discipline queryset by course if available
        if self.data.get("course"):
            try:
                course_id = int(self.data["course"])
                self.fields["discipline"].queryset = (
                    Discipline.objects.filter(course_id=course_id).order_by("period", "name")
                )
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk:
            self.fields["discipline"].queryset = (
                Discipline.objects.filter(course=self.instance.course).order_by("period", "name")
            )
        else:
            self.fields["discipline"].queryset = Discipline.objects.none()


class ProjectionFilterForm(forms.Form):
    """Form for filtering the projection view."""

    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by("name"),
        required=False,
        empty_label="Todos os cursos",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Curso",
    )
    from_semester = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "2026.1"}),
        label="De",
    )
    to_semester = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "2028.2"}),
        label="Até",
    )
    main_area = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Área",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        areas = (
            Discipline.objects.values_list("main_area", flat=True)
            .distinct()
            .order_by("main_area")
        )
        self.fields["main_area"].choices = [("", "Todas as áreas")] + [
            (a, a.capitalize()) for a in areas if a
        ]
