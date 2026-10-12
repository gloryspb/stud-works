from django.urls import path

from .views import (
    StudentDashboardView,
    TeacherReviewView,
    TeacherWorkListView,
    WorkDetailView,
    WorkDownloadView,
    WorkUploadView,
)

app_name = "works"

urlpatterns = [
    path("dashboard/", StudentDashboardView.as_view(), name="dashboard"),
    path("works/upload/", WorkUploadView.as_view(), name="upload"),
    path("works/<int:pk>/", WorkDetailView.as_view(), name="detail"),
    path("works/<int:pk>/download/", WorkDownloadView.as_view(), name="download"),
    path("teacher/works/", TeacherWorkListView.as_view(), name="teacher_works"),
    path("teacher/works/<int:pk>/review/", TeacherReviewView.as_view(), name="review"),
]
