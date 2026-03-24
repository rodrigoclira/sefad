from django.contrib import admin
from .models import Professor, WorkloadNorm, WorkloadNormEntry


class WorkloadNormEntryInline(admin.TabularInline):
    model = WorkloadNormEntry
    extra = 0
    fields = ["work_group", "contract_type", "class_duration", "min_classes", "max_classes"]
    ordering = ["class_duration", "work_group", "contract_type"]


@admin.register(WorkloadNorm)
class WorkloadNormAdmin(admin.ModelAdmin):
    list_display = ["name", "resolution_number", "effective_date", "is_active", "entry_count"]
    list_editable = ["is_active"]
    readonly_fields = ["created_at"]
    inlines = [WorkloadNormEntryInline]
    fieldsets = (
        ("Identificação", {"fields": ("name", "resolution_number", "effective_date", "is_active")}),
        ("Observações", {"fields": ("notes",)}),
        ("Registro", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def entry_count(self, obj):
        return obj.entries.count()
    entry_count.short_description = "Entradas"


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ["name", "work_group", "contract_type", "is_on_leave", "is_active", "get_limits_display", "created_at"]
    list_filter = ["work_group", "contract_type", "is_on_leave", "is_active"]
    list_editable = ["is_on_leave", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 50

    fieldsets = (
        ("Identificação", {"fields": ("name",)}),
        ("Vínculo", {"fields": ("work_group", "contract_type", "is_on_leave", "is_active")}),
        ("Registro", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_limits_display(self, obj):
        mn, mx = obj.get_workload_limits(class_duration=45)
        if mn is None:
            return "—"
        return f"{mn}–{mx} aulas/sem (45 min)"
    get_limits_display.short_description = "Limite CH (45 min)"
