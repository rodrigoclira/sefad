import json
from collections import defaultdict
from django.shortcuts import render
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from .models import ClassEntry, ExtraClass
from .forms import ClassEntryForm, ExtraClassForm, ProjectionFilterForm
from .utils import get_projection
from courses.models import Course, Discipline


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

    # --- Chart data ---
    chart_semesters = list(projection.keys())
    chart_ch = [data["total_ch"] for data in projection.values()]
    chart_credits = [data["total_credits"] for data in projection.values()]
    chart_classes = [data["total_classes"] for data in projection.values()]
    chart_regular = [
        sum(e["regular_count"] for e in data["entries"]) +
        sum(s["count"] for s in data["elective_slots"])
        for data in projection.values()
    ]
    chart_extra = [
        sum(e["extra_count"] for e in data["entries"])
        for data in projection.values()
    ]

    area_ch_map = defaultdict(int)
    period_ch_map = defaultdict(int)
    for data in projection.values():
        for entry in data["entries"]:
            area = entry["discipline"].main_area or "Sem área"
            area_ch_map[area] += entry["ch_total"]
            period_ch_map[entry["discipline"].period] += entry["ch_total"]
        for slot in data["elective_slots"]:
            period_ch_map[slot["period"]] += slot["ch_total"]

    sorted_periods = sorted(period_ch_map.keys(), key=lambda p: int(p) if p.isdigit() else 0)

    # Collect all courses present in the projection
    courses_in_proj = {}  # pk -> short_name or name
    for data in projection.values():
        for entry in data["entries"]:
            for src in entry["source_entries"]:
                courses_in_proj[src.course.pk] = src.course.short_name or src.course.name
        for slot in data["elective_slots"]:
            for src in slot["source_entries"]:
                courses_in_proj[src.course.pk] = src.course.short_name or src.course.name

    # Per semester, count unique ClassEntry PKs grouped by course
    active_entries_per_sem = []
    active_by_course = {pk: [] for pk in courses_in_proj}
    for data in projection.values():
        sem_course_entries = defaultdict(set)
        for entry in data["entries"]:
            for src in entry["source_entries"]:
                sem_course_entries[src.course.pk].add(src.pk)
        for slot in data["elective_slots"]:
            for src in slot["source_entries"]:
                sem_course_entries[src.course.pk].add(src.pk)
        total = sum(len(v) for v in sem_course_entries.values())
        active_entries_per_sem.append(total)
        for pk in courses_in_proj:
            active_by_course[pk].append(len(sem_course_entries.get(pk, set())))

    chart_data = json.dumps({
        "semesters": chart_semesters,
        "ch": chart_ch,
        "credits": chart_credits,
        "classes": chart_classes,
        "regular": chart_regular,
        "extra": chart_extra,
        "active_entries": active_entries_per_sem,
        "active_entries_by_course": [
            {"name": courses_in_proj[pk], "counts": counts}
            for pk, counts in active_by_course.items()
        ],
        "period_labels": [f"{p}º Período" for p in sorted_periods],
        "period_ch": [period_ch_map[p] for p in sorted_periods],
    })

    context = {
        "form": form,
        "projection": projection,
        "grand_total_credits": grand_total_credits,
        "grand_total_ch": grand_total_ch,
        "grand_total_classes": grand_total_classes,
        "has_entries": ClassEntry.objects.filter(is_active=True).exists(),
        "periods_in_use": periods_in_use,
        "chart_data": chart_data,
    }
    return render(request, "planning/projection.html", context)
