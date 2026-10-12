from django.conf import settings
from django.db import models

from .validators import validate_work_file


class StudentWork(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "На проверке"
        REVIEWED = "reviewed", "Проверена"
        NEEDS_FIXES = "needs_fixes", "Требуются исправления"
        REJECTED = "rejected", "Отклонена"

    title = models.CharField("Название работы", max_length=200)
    description = models.TextField("Описание", blank=True)
    file = models.FileField("Файл", upload_to="works/", validators=[validate_work_file])
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="works",
        verbose_name="Студент",
        limit_choices_to={"role": "student"},
    )
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField("Дата загрузки", auto_now_add=True)
    updated_at = models.DateTimeField("Дата изменения", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Студенческая работа"
        verbose_name_plural = "Студенческие работы"

    def __str__(self):
        return f"{self.title} ({self.student})"

    @property
    def original_filename(self):
        return self.file.name.rsplit("/", 1)[-1] if self.file else ""

    def can_be_viewed_by(self, user) -> bool:
        if not user.is_authenticated:
            return False
        if user.is_teacher or user.is_admin_role:
            return True
        return user.is_student and self.student_id == user.id

    def can_be_downloaded_by(self, user) -> bool:
        if not user.is_authenticated:
            return False
        if user.is_teacher:
            return True
        if user.is_admin_role:
            return True
        return user.is_student and self.student_id == user.id


class TeacherComment(models.Model):
    work = models.ForeignKey(
        StudentWork,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Работа",
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_comments",
        verbose_name="Преподаватель",
        limit_choices_to={"role": "teacher"},
    )
    text = models.TextField("Комментарий")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Комментарий преподавателя"
        verbose_name_plural = "Комментарии преподавателей"

    def __str__(self):
        return f"Комментарий к «{self.work.title}»"
