from django.contrib import admin

from .models import StudentWork, TeacherComment


class TeacherCommentInline(admin.TabularInline):
    model = TeacherComment
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(StudentWork)
class StudentWorkAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "student__username", "student__first_name")
    readonly_fields = ("created_at", "updated_at")
    inlines = [TeacherCommentInline]


@admin.register(TeacherComment)
class TeacherCommentAdmin(admin.ModelAdmin):
    list_display = ("work", "teacher", "created_at")
    list_filter = ("created_at",)
    search_fields = ("text", "work__title", "teacher__username")
    readonly_fields = ("created_at",)
