from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Professor


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
