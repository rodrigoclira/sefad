from django.urls import path

from .views import (
    ClassAssignmentCreateView,
    ClassAssignmentDeleteView,
    ScheduledClassCreateView,
    ScheduledClassDeleteView,
    ScheduledClassUpdateView,
    SemesterScheduleCreateView,
    SemesterScheduleDeleteView,
    SemesterScheduleDetailView,
    SemesterScheduleListView,
    SemesterScheduleUpdateView,
    bulk_delete_view,
    bulk_import_view,
    copy_schedule_view,
    disciplines_by_course,
    periods_by_course,
    summary_view,
)

app_name = "scheduling"

urlpatterns = [
    # SemesterSchedule
    path("", SemesterScheduleListView.as_view(), name="schedule_list"),
    path("new/", SemesterScheduleCreateView.as_view(), name="schedule_create"),
    path("<int:pk>/", SemesterScheduleDetailView.as_view(), name="schedule_detail"),
    path("<int:pk>/edit/", SemesterScheduleUpdateView.as_view(), name="schedule_edit"),
    path("<int:pk>/delete/", SemesterScheduleDeleteView.as_view(), name="schedule_delete"),
    path("<int:pk>/summary/", summary_view, name="schedule_summary"),
    path("<int:pk>/copy/", copy_schedule_view, name="schedule_copy"),
    path("<int:pk>/bulk-delete/", bulk_delete_view, name="bulk_delete"),
    path("<int:schedule_pk>/import/", bulk_import_view, name="bulk_import"),
    # ScheduledClass
    path("<int:schedule_pk>/classes/new/", ScheduledClassCreateView.as_view(), name="class_create"),
    path("classes/<int:pk>/edit/", ScheduledClassUpdateView.as_view(), name="class_edit"),
    path("classes/<int:pk>/delete/", ScheduledClassDeleteView.as_view(), name="class_delete"),
    # ClassAssignment
    path(
        "classes/<int:scheduled_class_pk>/assign/",
        ClassAssignmentCreateView.as_view(),
        name="assign_create",
    ),
    path("assignments/<int:pk>/delete/", ClassAssignmentDeleteView.as_view(), name="assign_delete"),
    # AJAX
    path("api/disciplines/", disciplines_by_course, name="disciplines_by_course"),
    path("api/periods/", periods_by_course, name="periods_by_course"),
]
