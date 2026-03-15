from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from .models import SemesterPlan, PlanDiscipline, ClassEntry, ExtraClass
from .forms import CreatePlanForm, AddDisciplineForm, UpdateItemForm, ClassEntryForm, ExtraClassForm, ProjectionFilterForm
from .utils import get_projection
from courses.models import Course, Discipline


class PlanListView(ListView):
    """List all semester plans."""

    model = SemesterPlan
    template_name = "planning/plan_list.html"
    context_object_name = "plans"
    paginate_by = 20


class PlanDetailView(DetailView):
    """Display details of a semester plan with summary."""

    model = SemesterPlan
    template_name = "planning/plan_detail.html"
    context_object_name = "plan"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.object
        context["plan_items"] = plan.plan_items.select_related("discipline").all()
        context["total_credits"] = plan.get_total_credits()
        context["total_ch_relogio"] = plan.get_total_ch_relogio()
        context["disciplines_count"] = plan.get_disciplines_count()
        context["unique_disciplines_count"] = plan.get_unique_disciplines_count()

        # Get available periods from the course
        periods = (
            Discipline.objects.filter(course=plan.course)
            .values_list("period", flat=True)
            .distinct()
            .order_by("period")
        )
        context["available_periods"] = list(periods)

        return context


class PlanCreateView(CreateView):
    """Create a new semester plan."""

    model = SemesterPlan
    template_name = "planning/plan_form.html"
    form_class = CreatePlanForm
    success_url = reverse_lazy("planning:plan_list")

    def form_valid(self, form):
        messages.success(
            self.request, f'Plano "{form.instance.name}" criado com sucesso!'
        )
        return super().form_valid(form)


class PlanUpdateView(UpdateView):
    """Update an existing semester plan."""

    model = SemesterPlan
    template_name = "planning/plan_form.html"
    form_class = CreatePlanForm

    def get_success_url(self):
        return reverse_lazy("planning:plan_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(
            self.request, f'Plano "{form.instance.name}" atualizado com sucesso!'
        )
        return super().form_valid(form)


class PlanDeleteView(DeleteView):
    """Delete a semester plan."""

    model = SemesterPlan
    template_name = "planning/plan_confirm_delete.html"
    success_url = reverse_lazy("planning:plan_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["disciplines_count"] = self.object.get_disciplines_count()
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f'Plano "{self.object.name}" excluído com sucesso!'
        )
        return super().form_valid(form)


def add_discipline_to_plan(request, plan_pk):
    """Add a single discipline to a plan."""
    plan = get_object_or_404(SemesterPlan, pk=plan_pk)

    if request.method == "POST":
        form = AddDisciplineForm(request.POST, plan=plan)
        if form.is_valid():
            discipline = form.cleaned_data["discipline"]
            classes_count = form.cleaned_data["classes_count"]
            assigned_period = form.cleaned_data.get("assigned_period", "")
            notes = form.cleaned_data["notes"]

            # Validate: if discipline is elective (period 0), assigned_period is required
            if discipline.period == "0" and not assigned_period:
                messages.error(
                    request,
                    "Para disciplinas optativas, você deve escolher o período de oferta!",
                )
                return render(
                    request,
                    "planning/add_discipline.html",
                    {"plan": plan, "form": form},
                )

            plan_item, created = PlanDiscipline.objects.get_or_create(
                plan=plan,
                discipline=discipline,
                defaults={
                    "classes_count": classes_count,
                    "assigned_period": assigned_period,
                    "notes": notes,
                },
            )

            if created:
                messages.success(
                    request, f'Disciplina "{discipline.name}" adicionada com sucesso!'
                )
            else:
                plan_item.classes_count = classes_count
                plan_item.assigned_period = assigned_period
                plan_item.notes = notes
                plan_item.save()
                messages.info(request, f'Disciplina "{discipline.name}" atualizada!')

            return redirect("planning:plan_detail", pk=plan_pk)
    else:
        form = AddDisciplineForm(plan=plan)

    # Get disciplines organized by period for reference
    # Exclude period 0 (electives)
    disciplines = (
        Discipline.objects.filter(course=plan.course)
        .exclude(period="0")
        .order_by("period", "name")
    )
    periods = disciplines.values_list("period", flat=True).distinct().order_by("period")

    context = {
        "plan": plan,
        "form": form,
        "disciplines": disciplines,
        "periods": list(periods),
    }
    return render(request, "planning/add_discipline.html", context)


def add_all_periods_to_plan(request, plan_pk):
    """Add all disciplines from all periods to a plan."""
    plan = get_object_or_404(SemesterPlan, pk=plan_pk)

    if request.method == "POST":
        classes_count = int(request.POST.get("classes_count", 1))

        # Exclude period 0 (electives) - they should be added manually
        disciplines = Discipline.objects.filter(course=plan.course).exclude(period="0")

        added_count = 0
        skipped_count = 0

        for discipline in disciplines:
            _, created = PlanDiscipline.objects.get_or_create(
                plan=plan,
                discipline=discipline,
                defaults={"classes_count": classes_count},
            )
            if created:
                added_count += 1
            else:
                skipped_count += 1

        if added_count > 0:
            messages.success(
                request,
                f"{added_count} disciplina(s) adicionada(s) de todos os períodos!",
            )
        if skipped_count > 0:
            messages.info(
                request, f"{skipped_count} disciplina(s) já existiam no plano."
            )

        return redirect("planning:plan_detail", pk=plan_pk)

    # GET request - show all disciplines organized by period
    # Exclude period 0 (electives)
    disciplines = (
        Discipline.objects.filter(course=plan.course)
        .exclude(period="0")
        .order_by("period", "name")
    )
    periods = disciplines.values_list("period", flat=True).distinct().order_by("period")

    # Organize disciplines by period
    disciplines_by_period = {}
    total_disciplines = 0
    for period in periods:
        period_disciplines = disciplines.filter(period=period)
        disciplines_by_period[period] = [
            {"name": d.name, "credits": d.credits, "period": d.period}
            for d in period_disciplines
        ]
        total_disciplines += len(period_disciplines)

    import json

    context = {
        "plan": plan,
        "disciplines_by_period": disciplines_by_period,
        "total_disciplines": total_disciplines,
    }
    return render(request, "planning/add_all_periods.html", context)


def add_period_to_plan(request, plan_pk):
    """Add all disciplines from a period to a plan."""
    plan = get_object_or_404(SemesterPlan, pk=plan_pk)

    if request.method == "POST":
        period = request.POST.get("period")
        classes_count = int(request.POST.get("classes_count", 1))

        disciplines = Discipline.objects.filter(course=plan.course, period=period)

        added_count = 0
        skipped_count = 0

        for discipline in disciplines:
            _, created = PlanDiscipline.objects.get_or_create(
                plan=plan,
                discipline=discipline,
                defaults={"classes_count": classes_count},
            )
            if created:
                added_count += 1
            else:
                skipped_count += 1

        if added_count > 0:
            messages.success(
                request,
                f"{added_count} disciplina(s) adicionada(s) do período {period}!",
            )
        if skipped_count > 0:
            messages.info(
                request, f"{skipped_count} disciplina(s) já existiam no plano."
            )

        return redirect("planning:plan_detail", pk=plan_pk)

    # GET request - show period selection with disciplines preview
    # Exclude period 0 (electives)
    disciplines = (
        Discipline.objects.filter(course=plan.course)
        .exclude(period="0")
        .order_by("period", "name")
    )
    periods = disciplines.values_list("period", flat=True).distinct().order_by("period")

    # Organize disciplines by period
    disciplines_by_period = {}
    for period in periods:
        period_disciplines = disciplines.filter(period=period)
        disciplines_by_period[period] = [
            {"name": d.name, "credits": d.credits, "period": d.period}
            for d in period_disciplines
        ]

    import json

    context = {
        "plan": plan,
        "available_periods": list(periods),
        "disciplines_by_period": disciplines_by_period,
    }
    return render(request, "planning/add_period.html", context)


def remove_discipline_from_plan(request, plan_pk, item_pk):
    """Remove a discipline from a plan."""
    plan = get_object_or_404(SemesterPlan, pk=plan_pk)
    item = get_object_or_404(PlanDiscipline, pk=item_pk, plan=plan)

    discipline_name = item.discipline.name
    item.delete()

    messages.success(request, f'Disciplina "{discipline_name}" removida do plano!')
    return redirect("planning:plan_detail", pk=plan_pk)


def update_plan_item(request, plan_pk, item_pk):
    """Update a plan item (classes count and notes)."""
    plan = get_object_or_404(SemesterPlan, pk=plan_pk)
    item = get_object_or_404(PlanDiscipline, pk=item_pk, plan=plan)

    if request.method == "POST":
        form = UpdateItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Disciplina "{item.discipline.name}" atualizada!'
            )
            return redirect("planning:plan_detail", pk=plan_pk)
    else:
        form = UpdateItemForm(instance=item)

    context = {
        "plan": plan,
        "item": item,
        "form": form,
    }
    return render(request, "planning/update_item.html", context)


# ---------------------------------------------------------------------------
# ClassEntry views
# ---------------------------------------------------------------------------

class ClassEntryListView(ListView):
    model = ClassEntry
    template_name = "planning/class_entry_list.html"
    context_object_name = "entries"

    def get_queryset(self):
        qs = ClassEntry.objects.select_related("course").order_by("start_semester", "course__name")
        course_id = self.request.GET.get("course")
        semester = self.request.GET.get("semester", "").strip()
        status = self.request.GET.get("status")
        if course_id:
            qs = qs.filter(course_id=course_id)
        if semester:
            qs = qs.filter(start_semester__icontains=semester)
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["courses"] = Course.objects.all().order_by("name")
        context["filter_course"] = self.request.GET.get("course", "")
        context["filter_semester"] = self.request.GET.get("semester", "")
        context["filter_status"] = self.request.GET.get("status", "")
        context["total_count"] = ClassEntry.objects.count()
        return context


class ClassEntryCreateView(CreateView):
    model = ClassEntry
    form_class = ClassEntryForm
    template_name = "planning/class_entry_form.html"
    success_url = reverse_lazy("planning:entry_list")

    def form_valid(self, form):
        messages.success(self.request, "Entrada de turma criada com sucesso!")
        return super().form_valid(form)


class ClassEntryUpdateView(UpdateView):
    model = ClassEntry
    form_class = ClassEntryForm
    template_name = "planning/class_entry_form.html"
    success_url = reverse_lazy("planning:entry_list")

    def form_valid(self, form):
        messages.success(self.request, "Entrada de turma atualizada com sucesso!")
        return super().form_valid(form)


class ClassEntryDeleteView(DeleteView):
    model = ClassEntry
    template_name = "planning/class_entry_confirm_delete.html"
    success_url = reverse_lazy("planning:entry_list")

    def form_valid(self, form):
        messages.success(self.request, "Entrada de turma excluída com sucesso!")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# ExtraClass views
# ---------------------------------------------------------------------------

class ExtraClassListView(ListView):
    model = ExtraClass
    template_name = "planning/extra_class_list.html"
    context_object_name = "extras"
    ordering = ["semester", "discipline__name"]


class ExtraClassCreateView(CreateView):
    model = ExtraClass
    form_class = ExtraClassForm
    template_name = "planning/extra_class_form.html"
    success_url = reverse_lazy("planning:extra_list")

    def form_valid(self, form):
        messages.success(self.request, "Disciplina extra adicionada com sucesso!")
        return super().form_valid(form)


class ExtraClassDeleteView(DeleteView):
    model = ExtraClass
    template_name = "planning/extra_class_confirm_delete.html"
    success_url = reverse_lazy("planning:extra_list")

    def form_valid(self, form):
        messages.success(self.request, "Disciplina extra removida com sucesso!")
        return super().form_valid(form)


def disciplines_by_course(request):
    """AJAX: return disciplines for a given course (used in ExtraClass form)."""
    course_id = request.GET.get("course_id")
    if not course_id:
        return JsonResponse({"disciplines": []})
    disciplines = (
        Discipline.objects.filter(course_id=course_id)
        .order_by("period", "name")
        .values("id", "name", "period")
    )
    return JsonResponse({"disciplines": list(disciplines)})


# ---------------------------------------------------------------------------
# Projection view
# ---------------------------------------------------------------------------

def projection_view(request):
    """Main workload projection view."""
    form = ProjectionFilterForm(request.GET or None)

    course_filter = None
    start_semester = None
    end_semester = None

    if form.is_valid():
        course_filter = form.cleaned_data.get("course")
        start_semester = form.cleaned_data.get("from_semester") or None
        end_semester = form.cleaned_data.get("to_semester") or None
        main_area = form.cleaned_data.get("main_area") or None
    else:
        main_area = None

    projection = get_projection(
        course_filter=course_filter,
        start_semester=start_semester,
        end_semester=end_semester,
        main_area=main_area,
    )

    # Merge regular disciplines and elective slots into a single sorted list per semester
    # Sort order: course name → period → is_elective
    for data in projection.values():
        rows = []
        for e in data["entries"]:
            rows.append({**e, "is_elective": False, "period": e["discipline"].period})
        for s in data["elective_slots"]:
            rows.append({**s, "is_elective": True})
        rows.sort(key=lambda r: (
            r["discipline"].course.name if not r["is_elective"] else r["slot"].course.name,
            int(r["period"]),
            r["is_elective"],
        ))
        data["all_rows"] = rows

    # Summary totals across all semesters
    grand_total_credits = sum(s["total_credits"] for s in projection.values())
    grand_total_ch = sum(s["total_ch"] for s in projection.values())
    grand_total_classes = sum(s["total_classes"] for s in projection.values())

    # Collect all period numbers present in the projection (for the legend)
    periods_in_use = sorted({
        e["discipline"].period
        for sem_data in projection.values()
        for e in sem_data["entries"]
    }, key=lambda p: int(p) if p.isdigit() else 0)

    context = {
        "form": form,
        "projection": projection,
        "grand_total_credits": grand_total_credits,
        "grand_total_ch": grand_total_ch,
        "grand_total_classes": grand_total_classes,
        "has_entries": ClassEntry.objects.filter(is_active=True).exists(),
        "periods_in_use": periods_in_use,
    }
    return render(request, "planning/projection.html", context)
