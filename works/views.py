from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from accounts.mixins import StudentRequiredMixin, TeacherRequiredMixin

from .forms import StatusFilterForm, WorkReviewForm, WorkUploadForm
from .models import StudentWork, TeacherComment


class HomeView(TemplateView):
    template_name = "home.html"


class StudentDashboardView(StudentRequiredMixin, ListView):
    model = StudentWork
    template_name = "works/dashboard.html"
    context_object_name = "works"

    def get_queryset(self):
        return StudentWork.objects.filter(student=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        works = context["works"]
        context["total_count"] = works.count()
        context["pending_count"] = works.filter(status=StudentWork.Status.PENDING).count()
        context["needs_fixes_count"] = works.filter(status=StudentWork.Status.NEEDS_FIXES).count()
        return context


class WorkUploadView(StudentRequiredMixin, FormView):
    template_name = "works/upload.html"
    form_class = WorkUploadForm

    def form_valid(self, form):
        work = form.save(commit=False)
        work.student = self.request.user
        work.status = StudentWork.Status.PENDING
        work.save()
        messages.success(self.request, "Работа успешно загружена и отправлена на проверку.")
        return redirect("works:detail", pk=work.pk)


class WorkDetailView(LoginRequiredMixin, DetailView):
    model = StudentWork
    template_name = "works/detail.html"
    context_object_name = "work"

    def get_object(self, queryset=None):
        work = super().get_object(queryset)
        if not work.can_be_viewed_by(self.request.user):
            raise PermissionDenied("Вы не можете просматривать эту работу.")
        return work

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.select_related("teacher")
        return context


class WorkDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        work = get_object_or_404(StudentWork, pk=pk)
        if not work.can_be_downloaded_by(request.user):
            raise PermissionDenied("Вы не можете скачать этот файл.")
        if not work.file:
            raise Http404("Файл не найден.")
        try:
            file_handle = work.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404("Файл не найден.") from exc
        return FileResponse(
            file_handle,
            as_attachment=True,
            filename=work.original_filename,
        )


class TeacherWorkListView(TeacherRequiredMixin, ListView):
    model = StudentWork
    template_name = "works/teacher_list.html"
    context_object_name = "works"

    def get_queryset(self):
        queryset = StudentWork.objects.select_related("student")
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = StatusFilterForm(self.request.GET)
        return context


class TeacherReviewView(TeacherRequiredMixin, View):
    template_name = "works/review.html"

    def get_work(self, pk):
        return get_object_or_404(StudentWork.objects.select_related("student"), pk=pk)

    def get(self, request, pk):
        work = self.get_work(pk)
        form = WorkReviewForm(initial={"status": work.status})
        return render(
            request,
            self.template_name,
            {
                "work": work,
                "form": form,
                "comments": work.comments.select_related("teacher"),
            },
        )

    def post(self, request, pk):
        work = self.get_work(pk)
        form = WorkReviewForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                work.status = form.cleaned_data["status"]
                work.save(update_fields=["status", "updated_at"])
                TeacherComment.objects.create(
                    work=work,
                    teacher=request.user,
                    text=form.cleaned_data["comment"],
                )
            messages.success(request, "Результат проверки сохранён.")
            return redirect("works:review", pk=work.pk)
        return render(
            request,
            self.template_name,
            {
                "work": work,
                "form": form,
                "comments": work.comments.select_related("teacher"),
            },
        )


def permission_denied_view(request, exception=None):
    message = str(exception) if exception else "Недостаточно прав для выполнения этого действия."
    return render(request, "403.html", {"message": message}, status=403)


def page_not_found_view(request, exception=None):
    return render(request, "404.html", status=404)
