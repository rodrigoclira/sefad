from django.contrib import admin

from .models import ClassAssignment, ScheduledClass, SemesterSchedule


class ClassAssignmentInline(admin.TabularInline):
    model = ClassAssignment
    extra = 1
    raw_id_fields = ["professor"]


class ScheduledClassInline(admin.TabularInline):
    model = ScheduledClass
    extra = 0
    fields = ["discipline", "class_label", "weekly_classes", "notes"]
    show_change_link = True


@admin.register(SemesterSchedule)
class SemesterScheduleAdmin(admin.ModelAdmin):
    list_display = ["name", "semester", "class_duration", "get_classes_count", "created_at"]
    list_filter = ["semester", "class_duration"]
    search_fields = ["name", "semester"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ScheduledClassInline]

    def get_classes_count(self, obj):
        return obj.scheduled_classes.count()

    get_classes_count.short_description = "Turmas"


@admin.register(ScheduledClass)
class ScheduledClassAdmin(admin.ModelAdmin):
    list_display = [
        "discipline",
        "class_label",
        "schedule",
        "weekly_classes",
        "get_professors",
    ]
    list_filter = ["schedule", "discipline__course"]
    search_fields = ["discipline__name", "class_label", "schedule__name"]
    inlines = [ClassAssignmentInline]

    def get_professors(self, obj):
        names = [a.professor.name for a in obj.assignments.select_related("professor")]
        return ", ".join(names) if names else "—"

    get_professors.short_description = "Professores"


@admin.register(ClassAssignment)
class ClassAssignmentAdmin(admin.ModelAdmin):
    list_display = ["professor", "scheduled_class", "created_at"]
    list_filter = ["professor", "scheduled_class__schedule"]
    search_fields = ["professor__name", "scheduled_class__discipline__name"]
