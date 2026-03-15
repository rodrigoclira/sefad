from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from .models import Professor, WorkloadNorm


class ProfessorListView(ListView):
    """List all professors."""

    model = Professor
    template_name = "professors/professor_list.html"
    context_object_name = "professors"
    paginate_by = 20


class ProfessorDetailView(DetailView):
    """Display details of a professor."""

    model = Professor
    template_name = "professors/professor_detail.html"
    context_object_name = "professor"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        professor = self.object
        active_norm = WorkloadNorm.objects.filter(is_active=True).first()
        limits = {}
        if active_norm:
            for duration in (45, 50, 60):
                mn, mx = professor.get_workload_limits(class_duration=duration, norm=active_norm)
                if mn is not None:
                    limits[duration] = {"min": mn, "max": mx}
        context["workload_limits"] = limits
        context["active_norm"] = active_norm
        return context


def professor_totals_api(request):
    """
    JSON endpoint: returns workload min/max for all professors and aggregated totals.
    Query param: duration (int, default 45) — class duration in minutes.
    """
    duration = int(request.GET.get("duration", 45))
    norm = WorkloadNorm.objects.filter(is_active=True).first()

    rows = []
    total_min = 0
    total_max = 0
    applicable_count = 0

    for prof in Professor.objects.all().order_by("name"):
        mn, mx = prof.get_workload_limits(class_duration=duration, norm=norm)
        rows.append({
            "id": prof.pk,
            "name": prof.name,
            "work_group": prof.work_group,
            "contract_type": prof.contract_type,
            "contract_type_display": prof.get_contract_type_display() if prof.contract_type else "—",
            "is_on_leave": prof.is_on_leave,
            "min_classes": mn,
            "max_classes": mx,
        })
        if mn is not None and not prof.is_on_leave:
            total_min += mn
            total_max += mx
            applicable_count += 1

    return JsonResponse({
        "rows": rows,
        "total_min": total_min,
        "total_max": total_max,
        "applicable_count": applicable_count,
        "total_professors": len(rows),
        "duration": duration,
        "norm_name": str(norm) if norm else None,
    })
