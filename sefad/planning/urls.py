from django.urls import path
from .views import (
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
