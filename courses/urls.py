from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('disciplines/', views.DisciplineListView.as_view(), name='discipline_list'),
    path('discipline/<int:pk>/', views.DisciplineDetailView.as_view(), name='discipline_detail'),
]
