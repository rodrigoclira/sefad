from django.contrib import admin
from django.db.models import Sum, Count
from .models import SemesterPlan, PlanDiscipline, ClassEntry, ExtraClass


class PlanDisciplineInline(admin.TabularInline):
    """Inline admin for disciplines within a plan."""

    model = PlanDiscipline
    extra = 1
    fields = ["discipline", "classes_count", "notes"]
    autocomplete_fields = ["discipline"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("discipline", "discipline__course")


@admin.register(SemesterPlan)
class SemesterPlanAdmin(admin.ModelAdmin):
    """Admin interface for Semester Plan model."""

    list_display = [
        "name",
        "course",
        "get_disciplines_summary",
        "get_effort_summary",
        "created_at",
    ]
    list_filter = ["course", "created_at"]
    search_fields = ["name", "description", "course__name"]
    readonly_fields = ["created_at", "updated_at", "get_summary_display"]
    autocomplete_fields = ["course"]
    inlines = [PlanDisciplineInline]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "course", "description")}),
        ("Summary", {"fields": ("get_summary_display",), "classes": ("wide",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_disciplines_summary(self, obj):
        """Display disciplines count summary."""
        unique = obj.get_unique_disciplines_count()
        total = obj.get_disciplines_count()
        if unique != total:
            return f"{unique} disciplinas ({total} turmas)"
        return f"{unique} disciplinas"

    get_disciplines_summary.short_description = "Disciplinas"

    def get_effort_summary(self, obj):
        """Display effort summary."""
        credits = obj.get_total_credits()
        ch = obj.get_total_ch_relogio()
        return f"{credits} créditos | {ch}h"

    get_effort_summary.short_description = "Esforço Total"

    def get_summary_display(self, obj):
        """Display detailed summary in the form."""
        if not obj.pk:
            return "Salve o plano para ver o resumo."

        summary = f"""
        <div style="background: #f0fdf4; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #16a34a;">
            <h3 style="margin-top: 0; color: #15803d;">Resumo do Planejamento</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #dcfce7;">
                    <td style="padding: 0.5rem; font-weight: 600;">Disciplinas Únicas:</td>
                    <td style="padding: 0.5rem;">{obj.get_unique_disciplines_count()}</td>
                </tr>
                <tr style="border-bottom: 1px solid #dcfce7;">
                    <td style="padding: 0.5rem; font-weight: 600;">Total de Turmas:</td>
                    <td style="padding: 0.5rem;">{obj.get_disciplines_count()}</td>
                </tr>
                <tr style="border-bottom: 1px solid #dcfce7;">
                    <td style="padding: 0.5rem; font-weight: 600;">Total de Créditos:</td>
                    <td style="padding: 0.5rem; color: #15803d; font-weight: 600;">{obj.get_total_credits()}</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem; font-weight: 600;">Total CH Relógio:</td>
                    <td style="padding: 0.5rem; color: #15803d; font-weight: 600;">{obj.get_total_ch_relogio()} horas</td>
                </tr>
            </table>
        </div>
        """
        return summary

    get_summary_display.short_description = "Resumo"
    get_summary_display.allow_tags = True

    actions = ["add_period_disciplines"]

    def add_period_disciplines(self, request, queryset):
        """Custom action to add all disciplines from a period to selected plans."""
        # This would open an intermediate page to select period
        # For now, we'll implement this later through a custom view
        self.message_user(request, "Esta funcionalidade será implementada em breve.")

    add_period_disciplines.short_description = "Adicionar disciplinas por período"


@admin.register(PlanDiscipline)
class PlanDisciplineAdmin(admin.ModelAdmin):
    """Admin interface for Plan Discipline model."""

    list_display = [
        "discipline",
        "plan",
        "classes_count",
        "get_credits_total",
        "get_ch_total",
    ]
    list_filter = ["plan", "discipline__course", "discipline__period"]
    search_fields = ["discipline__name", "plan__name", "notes"]
    autocomplete_fields = ["plan", "discipline"]

    fieldsets = (
        ("Basic Information", {"fields": ("plan", "discipline", "classes_count")}),
        ("Details", {"fields": ("notes",)}),
    )

    def get_credits_total(self, obj):
        """Display total credits for this item."""
        return f"{obj.get_total_credits()} créditos"

    get_credits_total.short_description = "Créditos Total"

    def get_ch_total(self, obj):
        """Display total CH for this item."""
        return f"{obj.get_total_ch_relogio()}h"

    get_ch_total.short_description = "CH Total"


@admin.register(ClassEntry)
class ClassEntryAdmin(admin.ModelAdmin):
    list_display = ["course", "start_semester", "label", "is_active", "created_at"]
    list_filter = ["course", "is_active"]
    search_fields = ["course__name", "label", "start_semester"]
    list_editable = ["is_active"]
    ordering = ["start_semester", "course__name"]


@admin.register(ExtraClass)
class ExtraClassAdmin(admin.ModelAdmin):
    list_display = ["discipline", "course", "semester", "extra_count", "created_at"]
    list_filter = ["course", "semester"]
    search_fields = ["discipline__name", "course__name", "semester"]
    ordering = ["semester", "discipline__name"]
