from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Course, Discipline


class CourseListView(ListView):
    """List all courses."""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20


class CourseDetailView(DetailView):
    """Display details of a course and its disciplines."""
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = self.object.disciplines.all()
        return context


class DisciplineListView(ListView):
    """List all disciplines."""
    model = Discipline
    template_name = 'courses/discipline_list.html'
    context_object_name = 'disciplines'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        course_id = self.request.GET.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset


class DisciplineDetailView(DetailView):
    """Display details of a discipline."""
    model = Discipline
    template_name = 'courses/discipline_detail.html'
    context_object_name = 'discipline'
