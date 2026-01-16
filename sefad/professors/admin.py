from django.contrib import admin
from .models import Professor


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    """Admin interface for Professor model."""

    list_display = ["name", "created_at", "updated_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 50

    fieldsets = (
        ("Basic Information", {"fields": ("name",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
