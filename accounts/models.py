from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Студент"
        TEACHER = "teacher", "Преподаватель"
        ADMIN = "admin", "Администратор"

    email = models.EmailField("Email", unique=True)
    role = models.CharField(
        "Роль",
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_staff = True
        super().save(*args, **kwargs)

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    def get_post_login_url(self):
        if self.is_teacher:
            return "works:teacher_works"
        if self.is_admin_role:
            return "admin:index"
        return "works:dashboard"

    def __str__(self):
        full_name = self.get_full_name().strip()
        return full_name or self.username
