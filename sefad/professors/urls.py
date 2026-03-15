from django.urls import path
from .views import ProfessorListView, ProfessorDetailView, professor_totals_api

app_name = "professors"

urlpatterns = [
    path("", ProfessorListView.as_view(), name="professor_list"),
    path("professor/<int:pk>/", ProfessorDetailView.as_view(), name="professor_detail"),
    path("api/totals/", professor_totals_api, name="professor_totals_api"),
]
