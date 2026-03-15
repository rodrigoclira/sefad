from django.urls import path
from .views import (
    PlanListView,
    PlanDetailView,
    PlanCreateView,
    PlanUpdateView,
    PlanDeleteView,
    add_discipline_to_plan,
    add_period_to_plan,
    add_all_periods_to_plan,
    remove_discipline_from_plan,
    update_plan_item,
    # ClassEntry
    ClassEntryListView,
    ClassEntryCreateView,
    ClassEntryUpdateView,
    ClassEntryDeleteView,
    # ExtraClass
    ExtraClassListView,
    ExtraClassCreateView,
    ExtraClassDeleteView,
    disciplines_by_course,
    # Projection
    projection_view,
)

app_name = "planning"

urlpatterns = [
    # Existing semester plan CRUD
    path("", PlanListView.as_view(), name="plan_list"),
    path("create/", PlanCreateView.as_view(), name="plan_create"),
    path("<int:pk>/", PlanDetailView.as_view(), name="plan_detail"),
    path("<int:pk>/edit/", PlanUpdateView.as_view(), name="plan_edit"),
    path("<int:pk>/delete/", PlanDeleteView.as_view(), name="plan_delete"),
    path(
        "<int:plan_pk>/add-discipline/", add_discipline_to_plan, name="add_discipline"
    ),
    path("<int:plan_pk>/add-period/", add_period_to_plan, name="add_period"),
    path(
        "<int:plan_pk>/add-all-periods/",
        add_all_periods_to_plan,
        name="add_all_periods",
    ),
    path(
        "<int:plan_pk>/item/<int:item_pk>/remove/",
        remove_discipline_from_plan,
        name="remove_discipline",
    ),
    path(
        "<int:plan_pk>/item/<int:item_pk>/edit/", update_plan_item, name="update_item"
    ),
    # Projection
    path("projection/", projection_view, name="projection"),
    # Class entries (turmas)
    path("entries/", ClassEntryListView.as_view(), name="entry_list"),
    path("entries/new/", ClassEntryCreateView.as_view(), name="entry_create"),
    path("entries/<int:pk>/edit/", ClassEntryUpdateView.as_view(), name="entry_edit"),
    path("entries/<int:pk>/delete/", ClassEntryDeleteView.as_view(), name="entry_delete"),
    # Extra classes
    path("extra/", ExtraClassListView.as_view(), name="extra_list"),
    path("extra/new/", ExtraClassCreateView.as_view(), name="extra_create"),
    path("extra/<int:pk>/delete/", ExtraClassDeleteView.as_view(), name="extra_delete"),
    # AJAX
    path("api/disciplines/", disciplines_by_course, name="disciplines_by_course"),
]
