from django.contrib import admin
from .models import Course, Discipline


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course model."""
    list_display = ['name', 'calendar_type', 'created_at', 'updated_at']
    list_filter = ['calendar_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'calendar_type')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    """Admin interface for Discipline model."""
    list_display = ['name', 'course', 'period', 'main_area', 'workload_hours', 'created_at']
    list_filter = ['course', 'main_area', 'period', 'created_at']
    search_fields = ['name', 'description', 'main_area']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['course']
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'name', 'period', 'main_area', 'workload_hours')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form to show appropriate period choices based on course calendar type."""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.course:
            # Dynamically set period choices based on course calendar type
            if obj.course.calendar_type == Course.CALENDAR_SEMESTRAL:
                form.base_fields['period'].widget.choices = Discipline.SEMESTER_PERIODS
            else:
                form.base_fields['period'].widget.choices = Discipline.YEARLY_PERIODS
        return form
