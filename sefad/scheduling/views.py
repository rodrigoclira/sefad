from collections import defaultdict

from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from courses.models import Discipline
from professors.models import WorkloadNorm

from .forms import BulkImportForm, ClassAssignmentForm, CopyScheduleForm, ScheduledClassForm, SemesterScheduleForm
from .models import ClassAssignment, ScheduledClass, SemesterSchedule


# ---------------------------------------------------------------------------
# SemesterSchedule views
# ---------------------------------------------------------------------------


class SemesterScheduleListView(ListView):
    model = SemesterSchedule
    template_name = "scheduling/schedule_list.html"
    context_object_name = "schedules"

    def get_queryset(self):
        qs = SemesterSchedule.objects.all()
        semester = self.request.GET.get("semester", "").strip()
        if semester:
            qs = qs.filter(semester__icontains=semester)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_semester"] = self.request.GET.get("semester", "")
        return context


class SemesterScheduleCreateView(CreateView):
    model = SemesterSchedule
    form_class = SemesterScheduleForm
    template_name = "scheduling/schedule_form.html"
    success_url = reverse_lazy("scheduling:schedule_list")

    def form_valid(self, form):
        messages.success(self.request, "Grade semestral criada com sucesso!")
        return super().form_valid(form)


class SemesterScheduleUpdateView(UpdateView):
    model = SemesterSchedule
    form_class = SemesterScheduleForm
    template_name = "scheduling/schedule_form.html"

    def get_success_url(self):
        return reverse_lazy("scheduling:schedule_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Grade semestral atualizada com sucesso!")
        return super().form_valid(form)


class SemesterScheduleDeleteView(DeleteView):
    model = SemesterSchedule
    template_name = "scheduling/schedule_confirm_delete.html"
    success_url = reverse_lazy("scheduling:schedule_list")

    def form_valid(self, form):
        messages.success(self.request, "Grade semestral excluída com sucesso!")
        return super().form_valid(form)


class SemesterScheduleDetailView(DetailView):
    model = SemesterSchedule
    template_name = "scheduling/schedule_detail.html"
    context_object_name = "schedule"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schedule = self.object

        scheduled_classes = (
            schedule.scheduled_classes.select_related("discipline__course")
            .prefetch_related("assignments__professor")
        )

        # Group by course then by period
        grouped = defaultdict(lambda: defaultdict(list))
        for sc in scheduled_classes:
            course_name = sc.discipline.course.name
            period = sc.discipline.period
            grouped[course_name][period].append(sc)

        # Convert to sorted list for template iteration
        grouped_list = []
        for course_name in sorted(grouped.keys()):
            periods_list = []
            for period in sorted(grouped[course_name].keys(), key=lambda p: (int(p) if p.isdigit() else 0, p)):
                periods_list.append({
                    "period": period,
                    "classes": grouped[course_name][period],
                })
            grouped_list.append({
                "course_name": course_name,
                "periods": periods_list,
            })

        context["grouped_list"] = grouped_list
        context["total_classes"] = scheduled_classes.count()
        return context


# ---------------------------------------------------------------------------
# ScheduledClass views
# ---------------------------------------------------------------------------


class ScheduledClassCreateView(CreateView):
    model = ScheduledClass
    form_class = ScheduledClassForm
    template_name = "scheduling/scheduled_class_form.html"

    def get_schedule(self):
        return get_object_or_404(SemesterSchedule, pk=self.kwargs["schedule_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schedule"] = self.get_schedule()
        return context

    def form_valid(self, form):
        form.instance.schedule = self.get_schedule()
        messages.success(self.request, "Turma adicionada com sucesso!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("scheduling:schedule_detail", kwargs={"pk": self.kwargs["schedule_pk"]})


class ScheduledClassUpdateView(UpdateView):
    model = ScheduledClass
    form_class = ScheduledClassForm
    template_name = "scheduling/scheduled_class_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schedule"] = self.object.schedule
        return context

    def form_valid(self, form):
        messages.success(self.request, "Turma atualizada com sucesso!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("scheduling:schedule_detail", kwargs={"pk": self.object.schedule.pk})


class ScheduledClassDeleteView(DeleteView):
    model = ScheduledClass
    template_name = "scheduling/scheduled_class_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schedule"] = self.object.schedule
        return context

    def get_success_url(self):
        return reverse_lazy("scheduling:schedule_detail", kwargs={"pk": self.object.schedule.pk})

    def form_valid(self, form):
        messages.success(self.request, "Turma removida com sucesso!")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# ClassAssignment views
# ---------------------------------------------------------------------------


class ClassAssignmentCreateView(CreateView):
    model = ClassAssignment
    form_class = ClassAssignmentForm
    template_name = "scheduling/assignment_form.html"

    def get_scheduled_class(self):
        return get_object_or_404(ScheduledClass, pk=self.kwargs["scheduled_class_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sc = self.get_scheduled_class()
        context["scheduled_class"] = sc
        context["schedule"] = sc.schedule
        context["top_professors"] = (
            ClassAssignment.objects
            .filter(scheduled_class__discipline=sc.discipline)
            .exclude(scheduled_class__schedule=sc.schedule)
            .filter(professor__is_active=True)
            .values("professor__pk", "professor__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        return context

    def form_valid(self, form):
        form.instance.scheduled_class = self.get_scheduled_class()
        messages.success(self.request, "Professor atribuído com sucesso!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "scheduling:schedule_detail",
            kwargs={"pk": self.get_scheduled_class().schedule.pk},
        )


class ClassAssignmentDeleteView(DeleteView):
    model = ClassAssignment
    template_name = "scheduling/assignment_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schedule"] = self.object.scheduled_class.schedule
        return context

    def get_success_url(self):
        return reverse_lazy(
            "scheduling:schedule_detail",
            kwargs={"pk": self.object.scheduled_class.schedule.pk},
        )

    def form_valid(self, form):
        messages.success(self.request, "Atribuição removida com sucesso!")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Copy schedule
# ---------------------------------------------------------------------------


def copy_schedule_view(request, pk):
    source = get_object_or_404(SemesterSchedule, pk=pk)
    if request.method == "POST":
        form = CopyScheduleForm(request.POST)
        if form.is_valid():
            new = SemesterSchedule.objects.create(
                name=form.cleaned_data["name"],
                semester=form.cleaned_data["semester"],
                class_duration=source.class_duration,
                description=source.description,
            )
            copy_assignments = form.cleaned_data["copy_assignments"]
            for sc in source.scheduled_classes.prefetch_related("assignments").all():
                new_sc = ScheduledClass.objects.create(
                    schedule=new,
                    discipline=sc.discipline,
                    class_label=sc.class_label,
                    turno=sc.turno,
                    weekly_classes=sc.weekly_classes,
                    notes=sc.notes,
                )
                if copy_assignments:
                    for a in sc.assignments.all():
                        ClassAssignment.objects.create(
                            scheduled_class=new_sc,
                            professor=a.professor,
                        )
            messages.success(request, f"Grade copiada com sucesso para {new.semester}.")
            return redirect("scheduling:schedule_detail", pk=new.pk)
    else:
        form = CopyScheduleForm(initial={
            "name": f"Cópia de {source.name}",
            "semester": source.semester,
            "copy_assignments": False,
        })
    return render(request, "scheduling/schedule_copy.html", {"form": form, "source": source})


# ---------------------------------------------------------------------------
# Bulk delete
# ---------------------------------------------------------------------------


def bulk_delete_view(request, pk):
    schedule = get_object_or_404(SemesterSchedule, pk=pk)
    if request.method == "POST":
        ids = request.POST.getlist("selected_ids")
        if ids:
            deleted_count, _ = ScheduledClass.objects.filter(
                pk__in=ids, schedule=schedule
            ).delete()
            messages.success(request, f"{deleted_count} turma(s) removida(s).")
        else:
            messages.warning(request, "Nenhuma turma selecionada.")
    return redirect("scheduling:schedule_detail", pk=pk)


# ---------------------------------------------------------------------------
# Bulk import
# ---------------------------------------------------------------------------


def bulk_import_view(request, schedule_pk):
    schedule = get_object_or_404(SemesterSchedule, pk=schedule_pk)
    if request.method == "POST":
        form = BulkImportForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data["course"]
            turno = form.cleaned_data["turno"]
            skip = form.cleaned_data["skip_existing"]
            selected_periods = request.POST.getlist("periods")
            disciplines = Discipline.objects.filter(course=course)
            if selected_periods:
                disciplines = disciplines.filter(period__in=selected_periods)
            created = 0
            skipped = 0
            for discipline in disciplines:
                if skip and schedule.scheduled_classes.filter(
                    discipline=discipline, turno=turno
                ).exists():
                    skipped += 1
                    continue
                ScheduledClass.objects.create(
                    schedule=schedule,
                    discipline=discipline,
                    weekly_classes=discipline.credits,
                    turno=turno,
                )
                created += 1
            messages.success(
                request,
                f"{created} turma(s) adicionada(s). {skipped} ignorada(s) (já existiam).",
            )
            return redirect("scheduling:schedule_detail", pk=schedule_pk)
    else:
        form = BulkImportForm(initial={"skip_existing": True})
    return render(request, "scheduling/bulk_import.html", {"form": form, "schedule": schedule})


# ---------------------------------------------------------------------------
# Summary view
# ---------------------------------------------------------------------------


def summary_view(request, pk):
    schedule = get_object_or_404(SemesterSchedule, pk=pk)
    active_norm = WorkloadNorm.objects.filter(is_active=True).first()
    class_duration = schedule.class_duration

    scheduled_classes = (
        schedule.scheduled_classes.select_related("discipline__course")
        .prefetch_related("assignments__professor")
        .order_by("discipline__course__name", "discipline__period", "discipline__name")
    )

    # Build professor workload tally
    professor_tally = {}
    for sc in scheduled_classes:
        for assignment in sc.assignments.all():
            prof = assignment.professor
            if prof.pk not in professor_tally:
                mn, mx = prof.get_workload_limits(
                    class_duration=class_duration, norm=active_norm
                )
                professor_tally[prof.pk] = {
                    "professor": prof,
                    "total_weekly_classes": 0,
                    "min_classes": mn,
                    "max_classes": mx,
                    "status": None,
                    "classes": [],
                }
            professor_tally[prof.pk]["total_weekly_classes"] += sc.weekly_classes
            professor_tally[prof.pk]["classes"].append(sc)

    # Compute status and comparison metrics for each professor
    for row in professor_tally.values():
        if row["professor"].is_on_leave:
            row["status"] = "leave"
        elif row["min_classes"] is None:
            row["status"] = "unknown"
        elif row["total_weekly_classes"] < row["min_classes"]:
            row["status"] = "below"
        elif row["total_weekly_classes"] > row["max_classes"]:
            row["status"] = "above"
        else:
            row["status"] = "ok"

        if row["max_classes"]:
            row["margin"] = row["max_classes"] - row["total_weekly_classes"]
            row["utilization_pct"] = round(row["total_weekly_classes"] / row["max_classes"] * 100)
        else:
            row["margin"] = None
            row["utilization_pct"] = None

    professor_rows = sorted(professor_tally.values(), key=lambda r: r["professor"].name)

    context = {
        "schedule": schedule,
        "scheduled_classes": scheduled_classes,
        "professor_rows": professor_rows,
        "active_norm": active_norm,
        "class_duration": class_duration,
    }
    return render(request, "scheduling/summary.html", context)


# ---------------------------------------------------------------------------
# AJAX
# ---------------------------------------------------------------------------


def periods_by_course(request):
    """AJAX: return distinct periods for a given course."""
    course_id = request.GET.get("course_id")
    if not course_id:
        return JsonResponse({"periods": []})
    periods = (
        Discipline.objects.filter(course_id=course_id)
        .values_list("period", flat=True)
        .distinct()
        .order_by("period")
    )
    return JsonResponse({"periods": list(periods)})


def disciplines_by_course(request):
    """AJAX: return disciplines for a given course."""
    course_id = request.GET.get("course_id")
    if not course_id:
        return JsonResponse({"disciplines": []})
    disciplines = (
        Discipline.objects.filter(course_id=course_id)
        .order_by("period", "name")
        .values("id", "name", "period", "credits")
    )
    return JsonResponse({"disciplines": list(disciplines)})
